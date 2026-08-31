import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, get_db
from models.user import User
from models.bre_rule import BRERule
from repositories.user_repository import UserRepository
from repositories.bre_rule_repository import BRERuleRepository

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    
    # 1. Seed users
    user_repo = UserRepository(db)
    user_repo.create(username="admin", password="AdminPassword123", role="Admin", is_active=True)
    user_repo.create(username="staff", password="StaffPassword123", role="Viewer", is_active=True)
    user_repo.create(username="disabled_user", password="DisabledPass123", role="Admin", is_active=False)

    # 2. Seed default BRE rules
    rule_repo = BRERuleRepository(db)
    rule_repo.create(rule_name="Min Age", field_name="age", operator=">=", rule_value="21", failure_message="Applicant age must be at least 21 years old", priority=1)
    rule_repo.create(rule_name="Max Age", field_name="age", operator="<=", rule_value="60", failure_message="Applicant age must not exceed 60 years old", priority=2)
    rule_repo.create(rule_name="Min Income", field_name="monthly_income", operator=">=", rule_value="30000", failure_message="Monthly income must be at least ₹30,000", priority=3)
    rule_repo.create(rule_name="Min Score", field_name="credit_score", operator=">=", rule_value="700", failure_message="Credit score below minimum requirement of 700", priority=4)
    rule_repo.create(rule_name="Loan Ratio", field_name="loan_ratio", operator="<=", rule_value="80", failure_message="Loan amount cannot exceed 80% of property value", priority=5)
    db.close()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app)
