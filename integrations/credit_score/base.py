from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel, Field


class CreditScoreResult(BaseModel):
    success: bool = Field(..., description="Whether the credit score fetch succeeded")
    credit_score: Optional[int] = Field(default=None, description="Credit score in range 300-900")
    provider: str = Field(..., description="Provider identifier, e.g. 'mock' or 'cibil'")
    error_code: Optional[str] = Field(default=None, description="Standardized error code if failed")
    message: Optional[str] = Field(default=None, description="Human-readable status or error message")


class CreditScoreProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def get_credit_score(
        self,
        mobile: str,
        pan: Optional[str] = None,
        name: Optional[str] = None,
    ) -> CreditScoreResult:
        pass
