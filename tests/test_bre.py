import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base
from models.user import User
from models.lead import Lead
from models.bre_rule import BRERule
from models.lead_bre_result import LeadBREResult
from engine.operator_registry import evaluate_operator, UnsupportedOperatorException
from engine.context import BREContext
from engine.rule_evaluator import evaluate_single_rule
from engine.bre_engine import BREEngine
from services.bre_service import BREService
from repositories.bre_rule_repository import BRERuleRepository
from repositories.lead_repository import LeadRepository
from core.constants import BREStatus


# ==============================================================================
# 1. OPERATOR TESTS (1-12)
# ==============================================================================

def test_1_operator_gte_pass():
    assert evaluate_operator(">=", 700, 700) is True
    assert evaluate_operator(">=", 750, 700) is True

def test_2_operator_gte_fail():
    assert evaluate_operator(">=", 699, 700) is False

def test_3_operator_lte_pass():
    assert evaluate_operator("<=", 60, 60) is True
    assert evaluate_operator("<=", 45, 60) is True

def test_4_operator_lte_fail():
    assert evaluate_operator("<=", 61, 60) is False

def test_5_operator_gt_pass():
    assert evaluate_operator(">", 100, 50) is True

def test_6_operator_gt_fail():
    assert evaluate_operator(">", 50, 50) is False
    assert evaluate_operator(">", 40, 50) is False

def test_7_operator_lt_pass():
    assert evaluate_operator("<", 50, 100) is True

def test_8_operator_lt_fail():
    assert evaluate_operator("<", 100, 100) is False
    assert evaluate_operator("<", 110, 100) is False

def test_9_operator_eq_pass():
    assert evaluate_operator("==", "Salaried", "Salaried") is True

def test_10_operator_eq_fail():
    assert evaluate_operator("==", "Self Employed", "Salaried") is False

def test_11_operator_neq_pass():
    assert evaluate_operator("!=", 100, 200) is True

def test_12_operator_neq_fail():
    assert evaluate_operator("!=", "Home Loan", "Home Loan") is False


# ==============================================================================
# 2. BUSINESS RULE LOGIC TESTS (13-22)
# ==============================================================================

def get_dob_for_age(target_age: int) -> date:
    today = date.today()
    return date(today.year - target_age, today.month, today.day)

def test_13_age_21_passes():
    ctx = BREContext(date_of_birth=get_dob_for_age(21))
    res = evaluate_single_rule(1, "Min Age", "age", ">=", "21", "Underage", ctx)
    assert res.is_passed is True

def test_14_age_20_fails():
    ctx = BREContext(date_of_birth=get_dob_for_age(20))
    res = evaluate_single_rule(1, "Min Age", "age", ">=", "21", "Underage", ctx)
    assert res.is_passed is False
    assert res.failure_message == "Underage"

def test_15_age_60_passes():
    ctx = BREContext(date_of_birth=get_dob_for_age(60))
    res = evaluate_single_rule(2, "Max Age", "age", "<=", "60", "Overage", ctx)
    assert res.is_passed is True

def test_16_age_61_fails():
    ctx = BREContext(date_of_birth=get_dob_for_age(61))
    res = evaluate_single_rule(2, "Max Age", "age", "<=", "60", "Overage", ctx)
    assert res.is_passed is False
    assert res.failure_message == "Overage"

def test_17_income_30000_passes():
    ctx = BREContext(monthly_income=Decimal("30000.00"))
    res = evaluate_single_rule(3, "Min Income", "monthly_income", ">=", "30000", "Low income", ctx)
    assert res.is_passed is True

def test_18_income_29999_fails():
    ctx = BREContext(monthly_income=Decimal("29999.99"))
    res = evaluate_single_rule(3, "Min Income", "monthly_income", ">=", "30000", "Low income", ctx)
    assert res.is_passed is False
    assert res.failure_message == "Low income"

def test_19_credit_score_700_passes():
    ctx = BREContext(credit_score=700)
    res = evaluate_single_rule(4, "Min Credit Score", "credit_score", ">=", "700", "Low score", ctx)
    assert res.is_passed is True

def test_20_credit_score_699_fails():
    ctx = BREContext(credit_score=699)
    res = evaluate_single_rule(4, "Min Credit Score", "credit_score", ">=", "700", "Low score", ctx)
    assert res.is_passed is False
    assert res.failure_message == "Low score"

def test_21_loan_ratio_80_passes():
    # 800,000 / 1,000,000 = 80.0%
    ctx = BREContext(loan_amount=Decimal("800000"), property_value=Decimal("1000000"))
    res = evaluate_single_rule(5, "Loan Ratio", "loan_ratio", "<=", "80", "High ratio", ctx)
    assert res.is_passed is True

def test_22_loan_ratio_81_fails():
    # 810,000 / 1,000,000 = 81.0%
    ctx = BREContext(loan_amount=Decimal("810000"), property_value=Decimal("1000000"))
    res = evaluate_single_rule(5, "Loan Ratio", "loan_ratio", "<=", "80", "High ratio", ctx)
    assert res.is_passed is False
    assert res.failure_message == "High ratio"


# ==============================================================================
# 3. MULTIPLE RULE & DECISION TESTS (23-25)
# ==============================================================================

@pytest.fixture
def standard_rules():
    return [
        BRERule(id=1, rule_name="Min Age", field_name="age", operator=">=", rule_value="21", failure_message="Age below 21", priority=1, is_active=True),
        BRERule(id=2, rule_name="Max Age", field_name="age", operator="<=", rule_value="60", failure_message="Age above 60", priority=2, is_active=True),
        BRERule(id=3, rule_name="Min Income", field_name="monthly_income", operator=">=", rule_value="30000", failure_message="Income below 30k", priority=3, is_active=True),
        BRERule(id=4, rule_name="Min Credit Score", field_name="credit_score", operator=">=", rule_value="700", failure_message="Score below 700", priority=4, is_active=True),
        BRERule(id=5, rule_name="Loan Ratio", field_name="loan_ratio", operator="<=", rule_value="80", failure_message="Loan ratio exceeds 80%", priority=5, is_active=True),
    ]

def test_23_all_rules_pass_eligible(standard_rules):
    ctx = BREContext(
        date_of_birth=get_dob_for_age(30),
        monthly_income=Decimal("50000"),
        credit_score=750,
        loan_amount=Decimal("2000000"),
        property_value=Decimal("3000000"),
    )
    decision = BREEngine.evaluate(standard_rules, ctx)
    assert decision.status == "Eligible"
    assert decision.passed_rules == 5
    assert decision.failed_rules == 0
    assert len(decision.rejection_reasons) == 0

def test_24_single_rule_fails_not_eligible(standard_rules):
    ctx = BREContext(
        date_of_birth=get_dob_for_age(30),
        monthly_income=Decimal("50000"),
        credit_score=650,  # Fails credit score
        loan_amount=Decimal("2000000"),
        property_value=Decimal("3000000"),
    )
    decision = BREEngine.evaluate(standard_rules, ctx)
    assert decision.status == "Not Eligible"
    assert decision.passed_rules == 4
    assert decision.failed_rules == 1
    assert decision.rejection_reasons == ["Score below 700"]

def test_25_multiple_rules_fail_returns_all_reasons(standard_rules):
    ctx = BREContext(
        date_of_birth=get_dob_for_age(19),   # Fails Min Age
        monthly_income=Decimal("20000"),      # Fails Min Income
        credit_score=620,                     # Fails Credit Score
        loan_amount=Decimal("900000"),
        property_value=Decimal("1000000"),    # Fails 90% Loan Ratio
    )
    decision = BREEngine.evaluate(standard_rules, ctx)
    assert decision.status == "Not Eligible"
    assert decision.failed_rules == 4
    assert len(decision.rejection_reasons) == 4
    assert "Age below 21" in decision.rejection_reasons
    assert "Income below 30k" in decision.rejection_reasons
    assert "Score below 700" in decision.rejection_reasons
    assert "Loan ratio exceeds 80%" in decision.rejection_reasons


# ==============================================================================
# 4. CONFIGURATION & ERROR TESTS (26-30)
# ==============================================================================

def test_26_inactive_rules_are_ignored():
    rules = [
        BRERule(id=1, rule_name="Active Rule", field_name="credit_score", operator=">=", rule_value="700", failure_message="Score below 700", priority=1, is_active=True),
        BRERule(id=2, rule_name="Inactive Rule", field_name="monthly_income", operator=">=", rule_value="100000", failure_message="Income below 100k", priority=2, is_active=False),
    ]
    ctx = BREContext(credit_score=750, monthly_income=Decimal("50000"))
    decision = BREEngine.evaluate(rules, ctx)
    assert decision.status == "Eligible"
    assert len(decision.evaluations) == 1

def test_27_unsupported_field_rejected():
    ctx = BREContext(credit_score=750)
    res = evaluate_single_rule(1, "Bad Field", "non_existent_field", "==", "val", "Fail", ctx)
    assert res.is_passed is False
    assert "unsupported rule field" in res.failure_message.lower()

def test_28_unsupported_operator_rejected():
    with pytest.raises(UnsupportedOperatorException):
        evaluate_operator("INVALID_OP", 10, 20)

def test_29_invalid_rule_value_handled():
    ctx = BREContext(credit_score=750)
    res = evaluate_single_rule(1, "Bad Val", "credit_score", ">=", "NOT_A_NUMBER", "Fail", ctx)
    assert res.is_passed is False
    assert "invalid configured rule threshold" in res.failure_message.lower()

def test_30_missing_context_field_handled():
    ctx = BREContext()  # Empty context
    res = evaluate_single_rule(1, "Check Score", "credit_score", ">=", "700", "Score below 700", ctx)
    assert res.is_passed is False
    assert "Score below 700" in res.failure_message


# ==============================================================================
# 5. EDGE CASES (31-36)
# ==============================================================================

def test_31_property_value_zero_safely_handled():
    ctx = BREContext(loan_amount=Decimal("500000"), property_value=Decimal("0"))
    assert ctx.loan_ratio is None
    res = evaluate_single_rule(1, "Loan Ratio", "loan_ratio", "<=", "80", "Invalid ratio", ctx)
    assert res.is_passed is False

def test_32_property_value_negative_safely_handled():
    ctx = BREContext(loan_amount=Decimal("500000"), property_value=Decimal("-100000"))
    assert ctx.loan_ratio is None
    res = evaluate_single_rule(1, "Loan Ratio", "loan_ratio", "<=", "80", "Invalid ratio", ctx)
    assert res.is_passed is False

def test_33_missing_credit_score():
    ctx = BREContext(date_of_birth=get_dob_for_age(30), monthly_income=Decimal("50000"))
    res = evaluate_single_rule(1, "Credit Check", "credit_score", ">=", "700", "Missing score", ctx)
    assert res.is_passed is False

def test_34_missing_income():
    ctx = BREContext(credit_score=750)
    res = evaluate_single_rule(1, "Income Check", "monthly_income", ">=", "30000", "Income missing", ctx)
    assert res.is_passed is False

def test_35_boundary_values():
    ctx = BREContext(date_of_birth=get_dob_for_age(21), monthly_income=Decimal("30000"), credit_score=700)
    assert evaluate_single_rule(1, "Min Age", "age", ">=", "21", "Fail", ctx).is_passed is True
    assert evaluate_single_rule(2, "Min Income", "monthly_income", ">=", "30000", "Fail", ctx).is_passed is True
    assert evaluate_single_rule(3, "Min Score", "credit_score", ">=", "700", "Fail", ctx).is_passed is True

def test_36_decimal_monetary_precision():
    ctx = BREContext(monthly_income=Decimal("30000.000001"))
    res = evaluate_single_rule(1, "Precision", "monthly_income", ">=", "30000", "Fail", ctx)
    assert res.is_passed is True


# ==============================================================================
# 6. DATABASE INTEGRATION & AUDIT HISTORY TESTS (37-40)
# ==============================================================================

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    
    # Seed default rules
    rule_repo = BRERuleRepository(session)
    rule_repo.create(rule_name="Min Age", field_name="age", operator=">=", rule_value="21", failure_message="Age below 21", priority=1)
    rule_repo.create(rule_name="Max Age", field_name="age", operator="<=", rule_value="60", failure_message="Age above 60", priority=2)
    rule_repo.create(rule_name="Min Income", field_name="monthly_income", operator=">=", rule_value="30000", failure_message="Income below 30k", priority=3)
    rule_repo.create(rule_name="Min Score", field_name="credit_score", operator=">=", rule_value="700", failure_message="Score below 700", priority=4)
    rule_repo.create(rule_name="Loan Ratio", field_name="loan_ratio", operator="<=", rule_value="80", failure_message="Ratio above 80%", priority=5)

    lead_repo = LeadRepository(session)
    lead = lead_repo.create_lead_with_bre_results(
        full_name="Anil Kumar",
        mobile="9876500011",
        date_of_birth=date(1995, 1, 1),
        city="Mumbai",
        pincode="400001",
        loan_type="Home Loan",
        employment_type="Salaried",
        monthly_income=Decimal("50000"),
        loan_amount=Decimal("2000000"),
        property_value=Decimal("3000000"),
        credit_score=750,
    )
    yield session, lead
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_37_individual_rule_results_stored(db_session):
    session, lead = db_session
    bre_service = BREService(session)
    
    ctx = BREContext(
        date_of_birth=lead.date_of_birth,
        monthly_income=lead.monthly_income,
        credit_score=lead.credit_score,
        loan_amount=lead.loan_amount,
        property_value=lead.property_value,
    )
    decision, results = bre_service.evaluate_and_persist(lead.id, ctx)
    session.commit()

    assert decision.status == "Eligible"
    assert len(results) == 5
    assert all(r.is_passed is True for r in results)

def test_38_multiple_evaluations_do_not_overwrite_history(db_session):
    session, lead = db_session
    bre_service = BREService(session)
    
    ctx = BREContext(
        date_of_birth=lead.date_of_birth,
        monthly_income=lead.monthly_income,
        credit_score=lead.credit_score,
        loan_amount=lead.loan_amount,
        property_value=lead.property_value,
    )
    # First run
    bre_service.evaluate_and_persist(lead.id, ctx)
    session.commit()

    # Second run with different context
    ctx2 = BREContext(
        date_of_birth=lead.date_of_birth,
        monthly_income=Decimal("15000"),  # Fails income
        credit_score=600,                # Fails credit score
        loan_amount=lead.loan_amount,
        property_value=lead.property_value,
    )
    bre_service.evaluate_and_persist(lead.id, ctx2)
    session.commit()

    all_history = session.query(LeadBREResult).filter(LeadBREResult.lead_id == lead.id).all()
    # 5 results from run 1 + 5 results from run 2 = 10 total historical records
    assert len(all_history) == 10

def test_39_rule_result_references_correct_lead(db_session):
    session, lead = db_session
    bre_service = BREService(session)
    ctx = BREContext(
        date_of_birth=lead.date_of_birth,
        monthly_income=lead.monthly_income,
        credit_score=lead.credit_score,
        loan_amount=lead.loan_amount,
        property_value=lead.property_value,
    )
    _, results = bre_service.evaluate_and_persist(lead.id, ctx)
    session.commit()
    for r in results:
        assert r.lead_id == lead.id

def test_40_rule_result_references_correct_rule(db_session):
    session, lead = db_session
    bre_service = BREService(session)
    ctx = BREContext(
        date_of_birth=lead.date_of_birth,
        monthly_income=lead.monthly_income,
        credit_score=lead.credit_score,
        loan_amount=lead.loan_amount,
        property_value=lead.property_value,
    )
    _, results = bre_service.evaluate_and_persist(lead.id, ctx)
    session.commit()
    rule_ids = {r.rule_id for r in results}
    assert len(rule_ids) == 5


# ==============================================================================
# 7. SPECIFIC CREDIT SCORE & MULTI-RULE CONSISTENCY TESTS (41-46)
# ==============================================================================

def test_41_credit_score_742_with_threshold_700_passes():
    ctx = BREContext(credit_score=742)
    res = evaluate_single_rule(4, "Min Score", "credit_score", ">=", "700", "Credit score below minimum requirement of 700", ctx)
    assert res.is_passed is True
    assert res.failure_message is None

def test_42_credit_score_700_with_threshold_700_passes():
    ctx = BREContext(credit_score=700)
    res = evaluate_single_rule(4, "Min Score", "credit_score", ">=", "700", "Credit score below minimum requirement of 700", ctx)
    assert res.is_passed is True
    assert res.failure_message is None

def test_43_credit_score_699_with_threshold_700_fails():
    ctx = BREContext(credit_score=699)
    res = evaluate_single_rule(4, "Min Score", "credit_score", ">=", "700", "Credit score below minimum requirement of 700", ctx)
    assert res.is_passed is False
    assert res.failure_message == "Credit score below minimum requirement of 700"

def test_44_credit_score_742_income_fails_overall_not_eligible_with_actual_reason():
    rules = [
        BRERule(id=1, rule_name="Min Income", field_name="monthly_income", operator=">=", rule_value="30000", failure_message="Monthly income must be at least ₹30,000", priority=1, is_active=True),
        BRERule(id=2, rule_name="Min Score", field_name="credit_score", operator=">=", rule_value="700", failure_message="Credit score below minimum requirement of 700", priority=2, is_active=True),
    ]
    # Applicant has 742 credit score (PASS), but income is 20000 (FAIL)
    ctx = BREContext(credit_score=742, monthly_income=Decimal("20000"))
    decision = BREEngine.evaluate(rules, ctx)
    
    assert decision.status == "Not Eligible"
    assert decision.passed_rules == 1
    assert decision.failed_rules == 1
    assert "Monthly income must be at least ₹30,000" in decision.rejection_reasons
    assert "Credit score below minimum requirement of 700" not in decision.rejection_reasons

def test_45_all_rules_pass_eligible_reasons_empty():
    rules = [
        BRERule(id=1, rule_name="Min Income", field_name="monthly_income", operator=">=", rule_value="30000", failure_message="Monthly income must be at least ₹30,000", priority=1, is_active=True),
        BRERule(id=2, rule_name="Min Score", field_name="credit_score", operator=">=", rule_value="700", failure_message="Credit score below minimum requirement of 700", priority=2, is_active=True),
    ]
    ctx = BREContext(credit_score=742, monthly_income=Decimal("60000"))
    decision = BREEngine.evaluate(rules, ctx)
    
    assert decision.status == "Eligible"
    assert decision.passed_rules == 2
    assert decision.failed_rules == 0
    assert len(decision.rejection_reasons) == 0

def test_46_dynamic_template_failure_message_formatting():
    ctx = BREContext(credit_score=650)
    res = evaluate_single_rule(
        rule_id=4,
        rule_name="Min Score",
        field_name="credit_score",
        operator=">=",
        rule_value="750",
        failure_message="Credit score {actual} is below required threshold of {threshold}",
        context=ctx,
    )
    assert res.is_passed is False
    assert res.failure_message == "Credit score 650 is below required threshold of 750"
