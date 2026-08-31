from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from engine.rule_evaluator import RuleEvaluationResult


class BREEvaluateRequest(BaseModel):
    date_of_birth: date = Field(..., description="Applicant date of birth")
    monthly_income: Decimal = Field(..., ge=0, description="Monthly income in INR")
    credit_score: Optional[int] = Field(default=None, ge=300, le=900, description="Credit score")
    loan_amount: Decimal = Field(..., gt=0, description="Requested loan amount in INR")
    property_value: Decimal = Field(..., gt=0, description="Estimated property value in INR")
    employment_type: Optional[str] = Field(default="Salaried")
    loan_type: Optional[str] = Field(default="Home Loan")


class BREDecisionResponse(BaseModel):
    status: str = Field(..., description="Eligible or Not Eligible")
    passed_rules: int
    failed_rules: int
    rejection_reasons: List[str]
    evaluations: List[RuleEvaluationResult]


class BRERuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_name: str
    field_name: str
    operator: str
    rule_value: str
    failure_message: str
    is_active: bool
    priority: int
