from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_FIELDS = {"age", "monthly_income", "credit_score", "loan_amount", "property_value", "loan_ratio"}
ALLOWED_OPERATORS = {">=", "<=", ">", "<", "==", "!="}


class CreateBRERuleRequest(BaseModel):
    rule_name: str = Field(..., min_length=2, max_length=100, description="Display name of the rule")
    field_name: str = Field(..., description="Supported field: age, monthly_income, credit_score, loan_amount, property_value, loan_ratio")
    operator: str = Field(..., description="Comparison operator: >=, <=, >, <, ==, !=")
    rule_value: str = Field(..., description="String threshold value, e.g. '700', '30000'")
    failure_message: str = Field(..., min_length=2, max_length=255, description="Message returned when rule fails")
    is_active: bool = Field(default=True, description="Whether rule is active")
    priority: int = Field(default=1, ge=1, description="Evaluation priority order (lower number evaluated first)")

    @field_validator("field_name")
    @classmethod
    def validate_field_name(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ALLOWED_FIELDS:
            raise ValueError(f"Invalid field_name '{v}'. Allowed: {', '.join(sorted(ALLOWED_FIELDS))}")
        return clean

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: str) -> str:
        clean = v.strip()
        if clean not in ALLOWED_OPERATORS:
            raise ValueError(f"Invalid operator '{v}'. Allowed: {', '.join(sorted(ALLOWED_OPERATORS))}")
        return clean

    @field_validator("rule_value")
    @classmethod
    def validate_rule_value(cls, v: str) -> str:
        clean = v.strip()
        try:
            Decimal(clean)
        except InvalidOperation:
            raise ValueError(f"rule_value '{v}' must be a valid numeric threshold")
        return clean


class UpdateBRERuleRequest(BaseModel):
    rule_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    field_name: Optional[str] = None
    operator: Optional[str] = None
    rule_value: Optional[str] = None
    failure_message: Optional[str] = Field(default=None, min_length=2, max_length=255)
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(default=None, ge=1)

    @field_validator("field_name")
    @classmethod
    def validate_field_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        clean = v.strip().lower()
        if clean not in ALLOWED_FIELDS:
            raise ValueError(f"Invalid field_name '{v}'. Allowed: {', '.join(sorted(ALLOWED_FIELDS))}")
        return clean

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        clean = v.strip()
        if clean not in ALLOWED_OPERATORS:
            raise ValueError(f"Invalid operator '{v}'. Allowed: {', '.join(sorted(ALLOWED_OPERATORS))}")
        return clean

    @field_validator("rule_value")
    @classmethod
    def validate_rule_value(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        clean = v.strip()
        try:
            Decimal(clean)
        except InvalidOperation:
            raise ValueError(f"rule_value '{v}' must be a valid numeric threshold")
        return clean


class ToggleStatusRequest(BaseModel):
    is_active: bool = Field(..., description="Target active state")


class BRERuleDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_name: str
    field_name: str
    operator: str
    rule_value: str
    failure_message: str
    is_active: bool
    priority: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
