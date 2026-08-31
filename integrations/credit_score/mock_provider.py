import logging
from typing import Optional
from integrations.credit_score.base import CreditScoreProvider, CreditScoreResult
from app.config import settings

logger = logging.getLogger("moneybeing.credit_score.mock")


class MockCreditScoreProvider(CreditScoreProvider):
    def __init__(self, default_score: Optional[int] = None):
        self.default_score = default_score if default_score is not None else settings.MOCK_CREDIT_SCORE

    @property
    def provider_name(self) -> str:
        return "mock"

    async def get_credit_score(
        self,
        mobile: str,
        pan: Optional[str] = None,
        name: Optional[str] = None,
    ) -> CreditScoreResult:
        masked = f"...{mobile[-4:]}" if len(mobile) >= 4 else mobile
        logger.info(f"MockCreditScoreProvider generating score for mobile {masked}")

        # 1. Mobile ending in 0000 -> Simulates provider failure
        if mobile.endswith("0000"):
            return CreditScoreResult(
                success=False,
                credit_score=None,
                provider=self.provider_name,
                error_code="CREDIT_SCORE_PROVIDER_UNAVAILABLE",
                message="Mock provider simulated provider outage.",
            )

        # 2. Mobile ending in 6500 -> Returns fixed score of 650 (rejection test case)
        if mobile.endswith("6500"):
            return CreditScoreResult(
                success=True,
                credit_score=650,
                provider=self.provider_name,
                message="Mock credit score generated.",
            )

        # 3. Mobile ending in 7500 -> Returns fixed score of 750 (approval test case)
        if mobile.endswith("7500"):
            return CreditScoreResult(
                success=True,
                credit_score=750,
                provider=self.provider_name,
                message="Mock credit score generated.",
            )

        # 4. Generate dynamic realistic credit score (620 to 830 range)
        if self.default_score is not None and self.default_score != settings.MOCK_CREDIT_SCORE:
            score = self.default_score
        else:
            # Deterministic realistic score based on applicant mobile digits
            seed_val = sum(ord(c) * (idx + 1) for idx, c in enumerate(mobile))
            score = 620 + (seed_val % 210)  # Generates realistic score between 620 and 829

        return CreditScoreResult(
            success=True,
            credit_score=score,
            provider=self.provider_name,
            message="Mock credit score fetched successfully (Demo/Dynamic environment).",
        )
