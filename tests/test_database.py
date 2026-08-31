import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.database import Base
from models.user import User
from models.lead import Lead
from models.bre_rule import BRERule
from models.lead_bre_result import LeadBREResult
from models.audit_log import AuditLog
from repositories.user_repository import UserRepository
from repositories.lead_repository import LeadRepository
from repositories.bre_rule_repository import BRERuleRepository
from repositories.audit_log_repository import AuditLogRepository
from core.security import verify_password, get_password_hash


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    
    # Enable foreign key and check constraints in SQLite for testing
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_user_creation_and_uniqueness(db_session):
    repo = UserRepository(db_session)
    user1 = repo.create(username="admin_user", password="SecurePassword123")
    assert user1.id is not None
    assert user1.username == "admin_user"
    assert verify_password("SecurePassword123", user1.password_hash)

    # Duplicate username check
    with pytest.raises(IntegrityError):
        user_dup = User(username="admin_user", password_hash=get_password_hash("OtherPass"))
        db_session.add(user_dup)
        db_session.commit()
    db_session.rollback()


def test_lead_creation_and_numeric_precision(db_session):
    repo = LeadRepository(db_session)
    lead = repo.create_lead_with_bre_results(
        full_name="Rajesh Sharma",
        mobile="9876543210",
        email="rajesh@example.com",
        date_of_birth=date(1990, 5, 15),
        city="Mumbai",
        pincode="400001",
        loan_type="HOME_LOAN",
        employment_type="SALARIED",
        monthly_income=Decimal("75000.50"),
        loan_amount=Decimal("3500000.00"),
        property_value=Decimal("5000000.00"),
        credit_score=750,
        bre_status="ELIGIBLE",
    )
    assert lead.id is not None
    assert lead.monthly_income == Decimal("75000.50")
    assert lead.loan_amount == Decimal("3500000.00")
    assert lead.bre_status == "ELIGIBLE"


def test_duplicate_mobile_constraint(db_session):
    repo = LeadRepository(db_session)
    repo.create_lead_with_bre_results(
        full_name="User One",
        mobile="9999988888",
        date_of_birth=date(1992, 1, 1),
        city="Delhi",
        pincode="110001",
        loan_type="LAP",
        employment_type="SELF_EMPLOYED",
        monthly_income=Decimal("50000"),
        loan_amount=Decimal("1000000"),
        property_value=Decimal("2000000"),
    )

    with pytest.raises(IntegrityError):
        repo.create_lead_with_bre_results(
            full_name="User Two",
            mobile="9999988888",  # Same mobile
            date_of_birth=date(1995, 2, 2),
            city="Pune",
            pincode="411001",
            loan_type="HOME_LOAN",
            employment_type="SALARIED",
            monthly_income=Decimal("60000"),
            loan_amount=Decimal("1500000"),
            property_value=Decimal("2500000"),
        )
    db_session.rollback()


def test_check_constraints_negative_income(db_session):
    repo = LeadRepository(db_session)
    with pytest.raises(IntegrityError):
        repo.create_lead_with_bre_results(
            full_name="Negative Income User",
            mobile="9811122233",
            date_of_birth=date(1990, 1, 1),
            city="Delhi",
            pincode="110001",
            loan_type="HOME_LOAN",
            employment_type="SALARIED",
            monthly_income=Decimal("-5000"),  # Violates income >= 0
            loan_amount=Decimal("1000000"),
            property_value=Decimal("2000000"),
        )
    db_session.rollback()


def test_check_constraints_invalid_credit_score(db_session):
    repo = LeadRepository(db_session)
    with pytest.raises(IntegrityError):
        repo.create_lead_with_bre_results(
            full_name="Invalid Score User",
            mobile="9811122244",
            date_of_birth=date(1990, 1, 1),
            city="Delhi",
            pincode="110001",
            loan_type="HOME_LOAN",
            employment_type="SALARIED",
            monthly_income=Decimal("50000"),
            loan_amount=Decimal("1000000"),
            property_value=Decimal("2000000"),
            credit_score=950,  # Violates credit_score <= 900
        )
    db_session.rollback()


def test_bre_rule_creation_and_deactivation(db_session):
    user_repo = UserRepository(db_session)
    admin = user_repo.create(username="rule_admin", password="Password123")

    bre_repo = BRERuleRepository(db_session)
    rule = bre_repo.create(
        rule_name="Minimum Age",
        field_name="age",
        operator=">=",
        rule_value="21",
        failure_message="Applicant age must be at least 21 years",
        priority=1,
        created_by=admin.id,
    )
    assert rule.id is not None
    assert rule.is_active is True

    # Check active rules
    active_rules = bre_repo.get_active_rules()
    assert len(active_rules) == 1
    assert active_rules[0].rule_name == "Minimum Age"

    # Soft deactivate rule
    bre_repo.set_active_status(rule.id, is_active=False)
    assert len(bre_repo.get_active_rules()) == 0
    assert len(bre_repo.list_all()) == 1


def test_bre_rule_invalid_operator(db_session):
    bre_repo = BRERuleRepository(db_session)
    with pytest.raises(IntegrityError):
        bre_repo.create(
            rule_name="Invalid Op Rule",
            field_name="age",
            operator="INVALID_OP",  # Violates operator check
            rule_value="21",
            failure_message="Invalid",
            priority=1,
        )
    db_session.rollback()


def test_lead_bre_results_cascade(db_session):
    lead_repo = LeadRepository(db_session)
    bre_repo = BRERuleRepository(db_session)

    rule = bre_repo.create(
        rule_name="Credit Score Check",
        field_name="credit_score",
        operator=">=",
        rule_value="700",
        failure_message="Credit score below 700",
        priority=1,
    )

    lead = lead_repo.create_lead_with_bre_results(
        full_name="Priya Patel",
        mobile="9123456780",
        date_of_birth=date(1988, 10, 20),
        city="Bengaluru",
        pincode="560001",
        loan_type="HOME_LOAN",
        employment_type="SALARIED",
        monthly_income=Decimal("120000"),
        loan_amount=Decimal("4000000"),
        property_value=Decimal("6000000"),
        credit_score=680,
        bre_status="NOT_ELIGIBLE",
        rejection_reasons=["Credit score below 700"],
        bre_evaluations=[
            {
                "rule_id": rule.id,
                "is_passed": False,
                "failure_message": "Credit score below 700",
            }
        ],
    )

    assert len(lead.bre_results) == 1
    assert lead.bre_results[0].is_passed is False
    assert lead.bre_results[0].failure_message == "Credit score below 700"


def test_lead_repository_pagination_and_filter(db_session):
    lead_repo = LeadRepository(db_session)
    for i in range(15):
        lead_repo.create_lead_with_bre_results(
            full_name=f"Applicant {i}",
            mobile=f"98000000{i:02d}",
            date_of_birth=date(1990, 1, 1),
            city="Delhi" if i % 2 == 0 else "Mumbai",
            pincode="110001",
            loan_type="HOME_LOAN" if i % 2 == 0 else "LAP",
            employment_type="SALARIED" if i % 2 == 0 else "SELF_EMPLOYED",
            monthly_income=Decimal("50000"),
            loan_amount=Decimal("1000000"),
            property_value=Decimal("2000000"),
            bre_status="ELIGIBLE" if i % 2 == 0 else "NOT_ELIGIBLE",
        )

    # Test pagination page 1
    items, total = lead_repo.list_leads(page=1, page_size=10)
    assert total == 15
    assert len(items) == 10

    # Test pagination page 2
    items_p2, total_p2 = lead_repo.list_leads(page=2, page_size=10)
    assert total_p2 == 15
    assert len(items_p2) == 5

    # Test filter by loan_type
    home_loans, total_hl = lead_repo.list_leads(loan_type="HOME_LOAN")
    assert total_hl == 8


def test_audit_logging(db_session):
    user_repo = UserRepository(db_session)
    admin = user_repo.create(username="auditor", password="Password123")

    audit_repo = AuditLogRepository(db_session)
    log = audit_repo.log_action(
        action="UPDATE",
        entity="BRE_RULE",
        user_id=admin.id,
        entity_id=1,
        old_value={"rule_value": "700"},
        new_value={"rule_value": "720"},
        ip_address="192.168.1.100",
    )
    assert log.id is not None
    assert log.old_value == {"rule_value": "700"}
    assert log.new_value == {"rule_value": "720"}
    assert log.user_id == admin.id
