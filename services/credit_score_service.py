import logging
from typing import Optional
from integrations.credit_score.base import CreditScoreProvider, CreditScoreResult
from integrations.credit_score.cibil_provider import CibilCreditScoreProvider
from integrations.credit_score.mock_provider import MockCreditScoreProvider
from core.exceptions import ProviderException
from app.config import settings

logger = logging.getLogger("moneybeing.credit_score.service")


class CreditScoreService:
    def __init__(self, provider: Optional[CreditScoreProvider] = None):
        self._provider = provider or self._resolve_provider()

    @staticmethod
    def _resolve_provider() -> CreditScoreProvider:
        provider_name = settings.CREDIT_SCORE_PROVIDER.lower().strip()
        if provider_name in ["mock", "demo", "test"]:
            return MockCreditScoreProvider()
        elif provider_name in ["cibil", "real", "sandbox"]:
            return CibilCreditScoreProvider()
        else:
            logger.error(f"Unknown CREDIT_SCORE_PROVIDER configured: '{provider_name}'")
            raise ProviderException(f"Unsupported credit score provider: '{provider_name}'")

    @property
    def active_provider_name(self) -> str:
        return self._provider.provider_name

    async def fetch_credit_score(
        self,
        mobile: str,
        pan: Optional[str] = None,
        name: Optional[str] = None,
    ) -> CreditScoreResult:
        logger.info(f"Fetching credit score via [{self._provider.provider_name}] provider...")
        result = await self._provider.get_credit_score(mobile=mobile, pan=pan, name=name)

        if result.success and result.credit_score is not None:
            if result.credit_score < 300 or result.credit_score > 900:
                logger.error(f"Provider returned invalid score: {result.credit_score}")
                return CreditScoreResult(
                    success=False,
                    credit_score=None,
                    provider=result.provider,
                    error_code="CREDIT_SCORE_OUT_OF_RANGE",
                    message="Credit score returned by provider is outside valid range (300-900).",
                )

        return result
