import logging
from typing import Optional
import httpx
from integrations.credit_score.base import CreditScoreProvider, CreditScoreResult
from app.config import settings

logger = logging.getLogger("moneybeing.credit_score.cibil")


class CibilCreditScoreProvider(CreditScoreProvider):
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.CREDIT_SCORE_API_BASE_URL or settings.CIBIL_API_URL or "").strip()
        self.api_key = (api_key or settings.CREDIT_SCORE_API_KEY or settings.CIBIL_API_KEY or "").strip()
        self.timeout = timeout or settings.CREDIT_SCORE_API_TIMEOUT or settings.CIBIL_TIMEOUT_SECONDS

    @property
    def provider_name(self) -> str:
        return "cibil"

    async def get_credit_score(
        self,
        mobile: str,
        pan: Optional[str] = None,
        name: Optional[str] = None,
    ) -> CreditScoreResult:
        if not self.base_url or not self.api_key:
            logger.error("CIBIL API configuration is missing (base_url or api_key is empty).")
            return CreditScoreResult(
                success=False,
                credit_score=None,
                provider=self.provider_name,
                error_code="CREDIT_SCORE_CONFIG_ERROR",
                message="CIBIL provider is not properly configured with valid credentials.",
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {"mobile": mobile}
        if pan:
            payload["pan"] = pan
        if name:
            payload["name"] = name

        max_retries = 2
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Initiating CIBIL credit score request (attempt {attempt}/{max_retries})...")
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(self.base_url, json=payload, headers=headers)

                if response.status_code == 200:
                    try:
                        data = response.json()
                    except Exception:
                        return CreditScoreResult(
                            success=False,
                            provider=self.provider_name,
                            error_code="CREDIT_SCORE_MALFORMED_RESPONSE",
                            message="Malformed JSON response from credit bureau provider.",
                        )

                    raw_score = data.get("credit_score")
                    if raw_score is None:
                        return CreditScoreResult(
                            success=False,
                            provider=self.provider_name,
                            error_code="CREDIT_SCORE_MISSING",
                            message="Credit score was not found in provider response.",
                        )

                    try:
                        score_int = int(raw_score)
                    except (ValueError, TypeError):
                        return CreditScoreResult(
                            success=False,
                            provider=self.provider_name,
                            error_code="CREDIT_SCORE_INVALID_TYPE",
                            message="Provider returned a non-integer credit score.",
                        )

                    if score_int < 300 or score_int > 900:
                        return CreditScoreResult(
                            success=False,
                            provider=self.provider_name,
                            error_code="CREDIT_SCORE_OUT_OF_RANGE",
                            message=f"Credit score {score_int} is outside valid range (300-900).",
                        )

                    return CreditScoreResult(
                        success=True,
                        credit_score=score_int,
                        provider=self.provider_name,
                        message="Credit score fetched successfully.",
                    )

                elif response.status_code in [400, 401, 403, 404]:
                    logger.warning(f"CIBIL provider returned client error status {response.status_code}")
                    return CreditScoreResult(
                        success=False,
                        provider=self.provider_name,
                        error_code=f"CREDIT_SCORE_CLIENT_ERROR_{response.status_code}",
                        message=f"Credit score request failed with status code {response.status_code}.",
                    )

                elif response.status_code == 429:
                    logger.warning("CIBIL provider rate limit reached (HTTP 429).")
                    return CreditScoreResult(
                        success=False,
                        provider=self.provider_name,
                        error_code="CREDIT_SCORE_RATE_LIMITED",
                        message="Credit score provider rate limit exceeded. Please retry later.",
                    )

                elif response.status_code in [500, 502, 503, 504]:
                    logger.warning(f"CIBIL provider server error {response.status_code} on attempt {attempt}")
                    if attempt == max_retries:
                        return CreditScoreResult(
                            success=False,
                            provider=self.provider_name,
                            error_code=f"CREDIT_SCORE_SERVER_ERROR_{response.status_code}",
                            message="Credit score provider server is temporarily unavailable.",
                        )
                    continue

                else:
                    return CreditScoreResult(
                        success=False,
                        provider=self.provider_name,
                        error_code=f"CREDIT_SCORE_UNEXPECTED_STATUS_{response.status_code}",
                        message=f"Unexpected response status {response.status_code} from provider.",
                    )

            except httpx.TimeoutException:
                logger.warning(f"Timeout connecting to CIBIL provider on attempt {attempt}")
                if attempt == max_retries:
                    return CreditScoreResult(
                        success=False,
                        provider=self.provider_name,
                        error_code="CREDIT_SCORE_TIMEOUT",
                        message="Credit score provider request timed out.",
                    )
            except (httpx.ConnectError, httpx.NetworkError) as e:
                logger.warning(f"Network connection error to CIBIL provider on attempt {attempt}: {str(e)}")
                if attempt == max_retries:
                    return CreditScoreResult(
                        success=False,
                        provider=self.provider_name,
                        error_code="CREDIT_SCORE_CONNECTION_ERROR",
                        message="Unable to connect to credit score provider network.",
                    )
            except Exception as e:
                logger.error(f"Unexpected exception during CIBIL credit score request: {str(e)}")
                return CreditScoreResult(
                    success=False,
                    provider=self.provider_name,
                    error_code="CREDIT_SCORE_UNEXPECTED_ERROR",
                    message="An unexpected error occurred while communicating with credit bureau.",
                )

        return CreditScoreResult(
            success=False,
            provider=self.provider_name,
            error_code="CREDIT_SCORE_MAX_RETRIES_EXCEEDED",
            message="Credit score service is temporarily unavailable after multiple attempts.",
        )
