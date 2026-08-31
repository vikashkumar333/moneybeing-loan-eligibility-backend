import pytest
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from models.user import User
from models.lead import Lead
from models.bre_rule import BRERule
from models.audit_log import AuditLog
from repositories.lead_repository import LeadRepository

client = TestClient(app)


@pytest.fixture
def admin_token():
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "AdminPassword123"})
    return resp.json()["access_token"]


@pytest.fixture
def viewer_token():
    resp = client.post("/api/v1/auth/login", json={"username": "staff", "password": "StaffPassword123"})
    return resp.json()["access_token"]


# ==============================================================================
# PART A: LEAD MANAGEMENT TESTS (1-18)
# ==============================================================================

def test_1_admin_can_list_leads(admin_token, db):
    # Seed 2 leads
    lead_repo = LeadRepository(db)
    lead_repo.create_lead_with_bre_results(
        full_name="Rajesh Sharma",
        mobile="9811100001",
        date_of_birth=date(1990, 1, 1),
        city="Mumbai",
        pincode="400001",
        loan_type="Home Loan",
        employment_type="Salaried",
        monthly_income=Decimal("50000"),
        loan_amount=Decimal("1000000"),
        property_value=Decimal("2000000"),
        credit_score=750,
        bre_status="Eligible",
    )
    db.commit()

    resp = client.get("/api/v1/leads", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "data" in data
    assert "pagination" in data
    assert data["pagination"]["total"] >= 1


def test_2_unauthenticated_cannot_list_leads():
    resp = client.get("/api/v1/leads")
    assert resp.status_code == 401


def test_3_non_admin_cannot_list_leads(viewer_token):
    resp = client.get("/api/v1/leads", headers={"Authorization": f"Bearer {viewer_token}"})
    assert resp.status_code == 403


def test_4_pagination(admin_token):
    resp = client.get("/api/v1/leads?page=1&page_size=2", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 2


def test_5_page_size_limit(admin_token):
    resp = client.get("/api/v1/leads?page=1&page_size=500", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 422  # Exceeds max 100


def test_6_search_by_name(admin_token):
    resp = client.get("/api/v1/leads?search=Rajesh", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) >= 1
    assert "Rajesh" in data["data"][0]["full_name"]


def test_7_search_by_mobile(admin_token):
    resp = client.get("/api/v1/leads?search=9811100001", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) >= 1
    assert data["data"][0]["mobile"] == "9811100001"


def test_8_loan_type_filter(admin_token):
    resp = client.get("/api/v1/leads?loan_type=Home Loan", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert all(d["loan_type"] == "Home Loan" for d in data["data"])


def test_9_employment_type_filter(admin_token):
    resp = client.get("/api/v1/leads?employment_type=Salaried", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert all(d["employment_type"] == "Salaried" for d in data["data"])


def test_10_bre_status_filter(admin_token):
    resp = client.get("/api/v1/leads?bre_status=Eligible", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert all(d["bre_status"] == "Eligible" for d in data["data"])


def test_11_city_filter(admin_token):
    resp = client.get("/api/v1/leads?city=Mumbai", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert all("Mumbai" in d.get("city", "Mumbai") for d in data["data"])


def test_12_date_range_filter(admin_token):
    today = date.today()
    resp = client.get(f"/api/v1/leads?date_from={today}&date_to={today}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200


def test_13_sorting_ascending(admin_token):
    resp = client.get("/api/v1/leads?sort_by=created_at&sort_order=asc", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200


def test_14_sorting_descending(admin_token):
    resp = client.get("/api/v1/leads?sort_by=created_at&sort_order=desc", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200


def test_15_invalid_sort_order(admin_token):
    resp = client.get("/api/v1/leads?sort_by=created_at&sort_order=INVALID", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 422


def test_16_lead_detail(admin_token, db):
    lead = db.query(Lead).first()
    assert lead is not None
    resp = client.get(f"/api/v1/leads/{lead.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["data"]["id"] == lead.id
    assert "bre_results" in data["data"]


def test_17_lead_not_found(admin_token):
    resp = client.get("/api/v1/leads/999999", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 404
    assert "not found" in resp.json()["message"].lower()


def test_18_bre_history_included_in_detail(admin_token, db):
    lead = db.query(Lead).filter(Lead.bre_results.any()).first()
    if lead:
        resp = client.get(f"/api/v1/leads/{lead.id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert len(resp.json()["data"]["bre_results"]) >= 1


# ==============================================================================
# PART B: DASHBOARD TESTS (19-24)
# ==============================================================================

def test_19_dashboard_stats(admin_token):
    resp = client.get("/api/v1/dashboard/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "total_leads" in data
    assert "eligible_leads" in data
    assert "rejected_leads" in data
    assert "average_credit_score" in data
    assert data["total_leads"] == data["eligible_leads"] + data["rejected_leads"]


def test_20_dashboard_distribution(admin_token):
    resp = client.get("/api/v1/dashboard/lead-distribution", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "by_loan_type" in data
    assert "by_employment_type" in data


def test_21_non_admin_denied_dashboard(viewer_token):
    resp = client.get("/api/v1/dashboard/stats", headers={"Authorization": f"Bearer {viewer_token}"})
    assert resp.status_code == 403


# ==============================================================================
# PART C: BRE RULE CRUD & AUDIT TESTS (25-39)
# ==============================================================================

def test_25_list_bre_rules(admin_token):
    resp = client.get("/api/v1/bre-rules", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 5
    # Verify ordered by priority ASC
    priorities = [r["priority"] for r in data]
    assert priorities == sorted(priorities)


def test_26_create_bre_rule(admin_token, db):
    payload = {
        "rule_name": "Test Minimum Income High",
        "field_name": "monthly_income",
        "operator": ">=",
        "rule_value": "90000",
        "failure_message": "Income below 90k threshold",
        "is_active": True,
        "priority": 10,
    }
    resp = client.post("/api/v1/bre-rules", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["rule_name"] == "Test Minimum Income High"
    assert data["rule_value"] == "90000"

    # Verify Audit Log
    audit = db.query(AuditLog).filter(AuditLog.entity_id == data["id"], AuditLog.action == "CREATE").first()
    assert audit is not None
    assert audit.entity == "BRE_RULE"
    assert audit.new_value["rule_name"] == "Test Minimum Income High"


def test_27_update_bre_rule(admin_token, db):
    # Find the created rule
    rule = db.query(BRERule).filter(BRERule.rule_name == "Test Minimum Income High").first()
    assert rule is not None

    update_payload = {
        "rule_value": "95000",
        "failure_message": "Income below 95k threshold",
    }
    resp = client.put(f"/api/v1/bre-rules/{rule.id}", json=update_payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["rule_value"] == "95000"

    # Verify Audit Log
    audit = db.query(AuditLog).filter(AuditLog.entity_id == rule.id, AuditLog.action == "UPDATE").first()
    assert audit is not None
    assert audit.old_value["rule_value"] == "90000"
    assert audit.new_value["rule_value"] == "95000"


def test_28_deactivate_bre_rule(admin_token, db):
    rule = db.query(BRERule).filter(BRERule.rule_name == "Test Minimum Income High").first()
    assert rule is not None

    resp = client.delete(f"/api/v1/bre-rules/{rule.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200

    db.refresh(rule)
    assert rule.is_active is False


def test_29_activate_bre_rule(admin_token, db):
    rule = db.query(BRERule).filter(BRERule.rule_name == "Test Minimum Income High").first()
    assert rule is not None

    resp = client.patch(f"/api/v1/bre-rules/{rule.id}/status", json={"is_active": True}, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is True

    db.refresh(rule)
    assert rule.is_active is True


def test_30_invalid_field_rejected(admin_token):
    payload = {
        "rule_name": "Bad Field",
        "field_name": "invalid_field_xyz",
        "operator": ">=",
        "rule_value": "100",
        "failure_message": "Fail",
    }
    resp = client.post("/api/v1/bre-rules", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 422


def test_31_invalid_operator_rejected(admin_token):
    payload = {
        "rule_name": "Bad Op",
        "field_name": "credit_score",
        "operator": "INVALID_OP",
        "rule_value": "700",
        "failure_message": "Fail",
    }
    resp = client.post("/api/v1/bre-rules", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 422


def test_32_invalid_rule_value_rejected(admin_token):
    payload = {
        "rule_name": "Bad Val",
        "field_name": "credit_score",
        "operator": ">=",
        "rule_value": "NOT_A_NUMBER",
        "failure_message": "Fail",
    }
    resp = client.post("/api/v1/bre-rules", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 422


def test_33_invalid_priority_rejected(admin_token):
    payload = {
        "rule_name": "Bad Priority",
        "field_name": "credit_score",
        "operator": ">=",
        "rule_value": "700",
        "failure_message": "Fail",
        "priority": 0,  # ge=1 required
    }
    resp = client.post("/api/v1/bre-rules", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 422


def test_34_rule_not_found(admin_token):
    resp = client.get("/api/v1/bre-rules/999999", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 404


def test_35_non_admin_denied_bre_rules(viewer_token):
    resp = client.get("/api/v1/bre-rules", headers={"Authorization": f"Bearer {viewer_token}"})
    assert resp.status_code == 403


# ==============================================================================
# CRITICAL BUSINESS VERIFICATION: DYNAMIC BRE RULE EVALUATION
# ==============================================================================

def test_40_dynamic_bre_rule_change_verification(admin_token, db):
    """
    Verifies that changing a rule threshold in the database immediately alters
    the outcome of the Lead Creation API without code modifications.
    """
    # 1. Update Credit Score threshold rule from 700 to 750
    score_rule = db.query(BRERule).filter(BRERule.field_name == "credit_score", BRERule.is_active == True).first()
    assert score_rule is not None
    original_val = score_rule.rule_value

    update_resp = client.put(
        f"/api/v1/bre-rules/{score_rule.id}",
        json={"rule_value": "750", "failure_message": "Credit score must be at least 750"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert update_resp.status_code == 200

    # 2. Deactivate the 95k test rule so it doesn't affect this test
    extra_rule = db.query(BRERule).filter(BRERule.rule_name == "Test Minimum Income High").first()
    if extra_rule:
        client.delete(f"/api/v1/bre-rules/{extra_rule.id}", headers={"Authorization": f"Bearer {admin_token}"})

    # 3. Create lead with credit score 742 (default mock score for unique mobile)
    payload = {
        "full_name": "Dynamic BRE Test Applicant",
        "mobile": "9812999742",
        "email": "dynamic@test.com",
        "date_of_birth": "1990-01-01",
        "city": "Bengaluru",
        "pincode": "560001",
        "loan_type": "Home Loan",
        "employment_type": "Salaried",
        "monthly_income": 80000,
        "loan_amount": 1000000,
        "property_value": 3000000,
        "consent": True,
    }
    lead_resp = client.post("/api/v1/leads", json=payload)
    assert lead_resp.status_code == 201
    data = lead_resp.json()

    # With score 742 < 750, the lead MUST be NOT ELIGIBLE
    assert data["bre_status"] == "Not Eligible"
    assert "Credit score must be at least 750" in data["reasons"]

    # 4. Restore original rule threshold
    client.put(
        f"/api/v1/bre-rules/{score_rule.id}",
        json={"rule_value": original_val, "failure_message": "Credit score below minimum requirement of 700"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
