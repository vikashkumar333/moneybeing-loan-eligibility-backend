from typing import Optional, Dict
from decimal import Decimal
from pydantic import BaseModel, Field


class DashboardStatsResponse(BaseModel):
    total_leads: int = Field(..., description="Total number of submitted leads")
    eligible_leads: int = Field(..., description="Number of eligible leads")
    rejected_leads: int = Field(..., description="Number of rejected leads")
    average_credit_score: Optional[float] = Field(default=None, description="Average credit score across leads with scores")


class LeadDistributionResponse(BaseModel):
    eligible_count: int
    not_eligible_count: int
    by_loan_type: Dict[str, int]
    by_employment_type: Dict[str, int]
