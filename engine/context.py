from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Optional, Tuple
from pydantic import BaseModel, Field


class BREContext(BaseModel):
    date_of_birth: Optional[date] = Field(default=None, description="Applicant date of birth")
    monthly_income: Optional[Decimal] = Field(default=None, description="Monthly income")
    credit_score: Optional[int] = Field(default=None, description="Applicant credit bureau score")
    loan_amount: Optional[Decimal] = Field(default=None, description="Requested loan amount")
    property_value: Optional[Decimal] = Field(default=None, description="Estimated property value")
    employment_type: Optional[str] = Field(default=None, description="Salaried or Self Employed")
    loan_type: Optional[str] = Field(default=None, description="Home Loan or LAP")

    @property
    def age(self) -> Optional[int]:
        if not self.date_of_birth:
            return None
        today = date.today()
        # Accurate age calculation considering whether birthday has occurred this year
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def loan_ratio(self) -> Optional[Decimal]:
        if not self.loan_amount or not self.property_value or self.property_value <= Decimal("0"):
            return None
        return (self.loan_amount / self.property_value) * Decimal("100")

    def resolve_field(self, field_name: str) -> Tuple[bool, Any]:
        normalized = field_name.strip().lower()
        if normalized == "age":
            return True, self.age
        elif normalized == "monthly_income":
            return True, self.monthly_income
        elif normalized == "credit_score":
            return True, self.credit_score
        elif normalized == "loan_amount":
            return True, self.loan_amount
        elif normalized == "property_value":
            return True, self.property_value
        elif normalized == "loan_ratio":
            return True, self.loan_ratio
        elif normalized == "employment_type":
            return True, self.employment_type
        elif normalized == "loan_type":
            return True, self.loan_type
        return False, None
