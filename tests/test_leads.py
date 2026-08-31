import pytest
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from models.lead import Lead
from models.lead_bre_result import LeadBREResult

client = TestClient(app)


def test_1_create_eligible_lead(db):
    payload = {
        "full_name": "Rohan Verma",
        "mobile": "9812347500",
        "email": "rohan.verma@example.com",
        "date_of_birth": "1992-05-15",
        "city": "Mumbai",
        "pincode": "400001",
        "loan_type": "Home Loan",
        "employment_type": "Salaried",
        "monthly_income": 85000,
        "loan_amount": 2500000,
        "property_value": 4000000,
        "consent": True,
    }
    response = client.post("/api/v1/leads", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["bre_status"] == "Eligible"
    assert data["credit_score"] == 750
    assert data["lead_id"] > 0
    assert data["reasons"] is None

    lead = db.query(Lead).filter(Lead.id == data["lead_id"]).first()
    assert lead is not None
    assert lead.full_name == "Rohan Verma"
    assert lead.bre_status == "Eligible"
    assert len(lead.bre_results) == 5


def test_2_create_rejected_lead_with_reasons(db):
    payload = {
        "full_name": "Amit Shah",
        "mobile": "9812346500",
        "email": "amit@example.com",
        "date_of_birth": "1990-01-01",
        "city": "Delhi",
        "pincode": "110001",
        "loan_type": "Home Loan",
        "employment_type": "Salaried",
        "monthly_income": 50000,
        "loan_amount": 900000,
        "property_value": 1000000,  # 90% loan ratio > 80%
        "consent": True,
    }
    response = client.post("/api/v1/leads", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["bre_status"] == "Not Eligible"
    assert data["credit_score"] == 650
    assert len(data["reasons"]) == 2
    assert "Credit score below minimum requirement of 700" in data["reasons"]
    assert "Loan amount cannot exceed 80% of property value" in data["reasons"]


def test_3_duplicate_mobile_rejected():
    payload = {
        "full_name": "Duplicate Rohan",
        "mobile": "9812347500",
        "email": "dup@example.com",
        "date_of_birth": "1992-05-15",
        "city": "Mumbai",
        "pincode": "400001",
        "loan_type": "Home Loan",
        "employment_type": "Salaried",
        "monthly_income": 85000,
        "loan_amount": 2500000,
        "property_value": 4000000,
        "consent": True,
    }
    response = client.post("/api/v1/leads", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["status"] == "error"
    assert data["message"] == "Lead already exists"


def test_4_validation_error_invalid_mobile():
    payload = {
        "full_name": "Invalid Mobile",
        "mobile": "12345",
        "date_of_birth": "1990-01-01",
        "city": "Pune",
        "pincode": "411001",
        "loan_type": "Home Loan",
        "employment_type": "Salaried",
        "monthly_income": 50000,
        "loan_amount": 1000000,
        "property_value": 2000000,
        "consent": True,
    }
    response = client.post("/api/v1/leads", json=payload)
    assert response.status_code == 422


def test_5_validation_error_missing_consent():
    payload = {
        "full_name": "No Consent",
        "mobile": "9899999999",
        "date_of_birth": "1990-01-01",
        "city": "Pune",
        "pincode": "411001",
        "loan_type": "Home Loan",
        "employment_type": "Salaried",
        "monthly_income": 50000,
        "loan_amount": 1000000,
        "property_value": 2000000,
        "consent": False,
    }
    response = client.post("/api/v1/leads", json=payload)
    assert response.status_code == 422


def test_6_credit_score_provider_outage_fails_safely(db):
    payload = {
        "full_name": "Outage Test",
        "mobile": "9812340000",
        "date_of_birth": "1990-01-01",
        "city": "Pune",
        "pincode": "411001",
        "loan_type": "Home Loan",
        "employment_type": "Salaried",
        "monthly_income": 50000,
        "loan_amount": 1000000,
        "property_value": 2000000,
        "consent": True,
    }
    response = client.post("/api/v1/leads", json=payload)
    assert response.status_code == 502
    data = response.json()
    assert data["status"] == "error"
    assert "credit score" in data["message"].lower()

    lead = db.query(Lead).filter(Lead.mobile == "9812340000").first()
    assert lead is None


def test_7_individual_bre_results_persisted(db):
    lead = db.query(Lead).filter(Lead.mobile == "9812346500").first()
    assert lead is not None
    eval_results = db.query(LeadBREResult).filter(LeadBREResult.lead_id == lead.id).all()
    assert len(eval_results) == 5
    failed_results = [r for r in eval_results if not r.is_passed]
    assert len(failed_results) == 2
