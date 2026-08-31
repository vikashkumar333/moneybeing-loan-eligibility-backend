import re
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CreateLeadRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="Full legal name of the applicant")
    mobile: str = Field(..., description="10-digit Indian mobile number")
    email: Optional[EmailStr] = Field(default=None, description="Applicant contact email address")
    date_of_birth: date = Field(..., description="Date of birth (YYYY-MM-DD)")
    city: str = Field(..., min_length=2, max_length=100, description="City of residence")
    pincode: str = Field(..., description="6-digit postal pincode")
    loan_type: str = Field(..., description="Loan type: HOME_LOAN, LAP, Home Loan, Loan Against Property")
    employment_type: str = Field(..., description="Employment type: SALARIED, SELF_EMPLOYED, Salaried, Self Employed")
    monthly_income: Decimal = Field(..., gt=0, description="Monthly net income in INR")
    loan_amount: Decimal = Field(..., gt=0, description="Requested loan amount in INR")
    property_value: Decimal = Field(..., gt=0, description="Estimated property value in INR")
    consent: bool = Field(..., description="Mandatory consent checkbox")

    @field_validator("full_name", "city")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        cleaned = re.sub(r"\D", "", v.strip())
        if len(cleaned) != 10:
            raise ValueError("Mobile number must be exactly 10 digits")
        return cleaned

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        cleaned = re.sub(r"\D", "", v.strip())
        if len(cleaned) != 6:
            raise ValueError("Pincode must be exactly 6 digits")
        return cleaned

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: date) -> date:
        today = date.today()
        if v >= today:
            raise ValueError("Date of birth must be in the past")
        approx_age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if approx_age < 21:
            raise ValueError("Applicant must be at least 21 years old to apply for a loan")
        if approx_age > 100:
            raise ValueError("Applicant age cannot exceed 100 years")
        return v

    @field_validator("consent")
    @classmethod
    def validate_consent(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Applicant consent is mandatory to proceed with loan evaluation")
        return v


class LeadResponse(BaseModel):
    status: str = Field(default="success")
    lead_id: int = Field(..., description="Created lead ID")
    credit_score: Optional[int] = Field(default=None, description="Retrieved credit score")
    bre_status: str = Field(..., description="Eligible or Not Eligible")
    reasons: Optional[List[str]] = Field(default=None, description="Rejection reasons if Not Eligible")


class LeadListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    mobile: str
    email: Optional[str] = None
    loan_type: str
    employment_type: str
    monthly_income: Decimal
    loan_amount: Decimal
    property_value: Decimal
    credit_score: Optional[int] = None
    bre_status: str
    created_at: datetime


class LeadBREResultItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_id: Optional[int] = None
    is_passed: bool
    failure_message: Optional[str] = None
    evaluated_at: datetime


class LeadDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    mobile: str
    email: Optional[str] = None
    date_of_birth: date
    city: str
    pincode: str
    loan_type: str
    employment_type: str
    monthly_income: Decimal
    loan_amount: Decimal
    property_value: Decimal
    credit_score: Optional[int] = None
    bre_status: str
    rejection_reasons: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    bre_results: List[LeadBREResultItem] = []
