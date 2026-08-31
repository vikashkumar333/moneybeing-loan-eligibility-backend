import pytest
import httpx
from unittest.mock import patch, AsyncMock
from integrations.credit_score.base import CreditScoreResult
from integrations.credit_score.mock_provider import MockCreditScoreProvider
from integrations.credit_score.cibil_provider import CibilCreditScoreProvider
from services.credit_score_service import CreditScoreService
from core.exceptions import ProviderException
from app.config import settings


@pytest.mark.asyncio
async def test_1_mock_provider_returns_valid_score():
    provider = MockCreditScoreProvider(default_score=750)
    result = await provider.get_credit_score(mobile="9876543210")
    assert result.success is True
    assert result.credit_score == 750
    assert result.provider == "mock"


@pytest.mark.asyncio
async def test_2_mock_provider_deterministic_scores():
    provider = MockCreditScoreProvider()
    
    # 7500 -> 750 (Approval case)
    res_approval = await provider.get_credit_score(mobile="987657500")
    assert res_approval.success is True
    assert res_approval.credit_score == 750

    # 6500 -> 650 (Rejection case)
    res_rejection = await provider.get_credit_score(mobile="987656500")
    assert res_rejection.success is True
    assert res_rejection.credit_score == 650

    # 0000 -> Outage simulation
    res_failure = await provider.get_credit_score(mobile="987650000")
    assert res_failure.success is False
    assert res_failure.credit_score is None
    assert res_failure.error_code == "CREDIT_SCORE_PROVIDER_UNAVAILABLE"


@pytest.mark.asyncio
async def test_3_provider_selection_works():
    with patch.object(settings, "CREDIT_SCORE_PROVIDER", "mock"):
        service_mock = CreditScoreService()
        assert service_mock.active_provider_name == "mock"

    with patch.object(settings, "CREDIT_SCORE_PROVIDER", "cibil"):
        service_cibil = CreditScoreService()
        assert service_cibil.active_provider_name == "cibil"


@pytest.mark.asyncio
async def test_4_invalid_provider_configuration():
    with patch.object(settings, "CREDIT_SCORE_PROVIDER", "invalid_provider_xyz"):
        with pytest.raises(ProviderException):
            CreditScoreService()


@pytest.mark.asyncio
async def test_5_cibil_missing_credentials_handled_gracefully():
    provider = CibilCreditScoreProvider(base_url="", api_key="")
    result = await provider.get_credit_score(mobile="9876543210")
    assert result.success is False
    assert result.error_code == "CREDIT_SCORE_CONFIG_ERROR"
    assert result.provider == "cibil"


@pytest.mark.asyncio
async def test_6_cibil_provider_timeout():
    provider = CibilCreditScoreProvider(base_url="https://api.cibil.test/score", api_key="secret-key")
    
    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Request timed out")):
        result = await provider.get_credit_score(mobile="9876543210")
        assert result.success is False
        assert result.error_code == "CREDIT_SCORE_TIMEOUT"


@pytest.mark.asyncio
async def test_7_cibil_provider_connection_failure():
    provider = CibilCreditScoreProvider(base_url="https://api.cibil.test/score", api_key="secret-key")
    
    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
        result = await provider.get_credit_score(mobile="9876543210")
        assert result.success is False
        assert result.error_code == "CREDIT_SCORE_CONNECTION_ERROR"


@pytest.mark.asyncio
async def test_8_cibil_provider_400_bad_request():
    provider = CibilCreditScoreProvider(base_url="https://api.cibil.test/score", api_key="secret-key")
    mock_resp = httpx.Response(status_code=400, json={"error": "Invalid mobile format"})
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await provider.get_credit_score(mobile="invalid")
        assert result.success is False
        assert result.error_code == "CREDIT_SCORE_CLIENT_ERROR_400"


@pytest.mark.asyncio
async def test_9_cibil_provider_401_unauthorized():
    provider = CibilCreditScoreProvider(base_url="https://api.cibil.test/score", api_key="invalid-key")
    mock_resp = httpx.Response(status_code=401, json={"error": "Unauthorized API key"})
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await provider.get_credit_score(mobile="9876543210")
        assert result.success is False
        assert result.error_code == "CREDIT_SCORE_CLIENT_ERROR_401"


@pytest.mark.asyncio
async def test_10_cibil_provider_403_forbidden():
    provider = CibilCreditScoreProvider(base_url="https://api.cibil.test/score", api_key="secret-key")
    mock_resp = httpx.Response(status_code=403, json={"error": "Forbidden"})
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await provider.get_credit_score(mobile="9876543210")
        assert result.success is False
        assert result.error_code == "CREDIT_SCORE_CLIENT_ERROR_403"


@pytest.mark.asyncio
async def test_11_cibil_provider_429_rate_limited():
    provider = CibilCreditScoreProvider(base_url="https://api.cibil.test/score", api_key="secret-key")
    mock_resp = httpx.Response(status_code=429, json={"error": "Rate limit exceeded"})
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await provider.get_credit_score(mobile="9876543210")
        assert result.success is False
        assert result.error_code == "CREDIT_SCORE_RATE_LIMITED"


@pytest.mark.asyncio
async def test_12_cibil_provider_500_server_error():
    provider = CibilCreditScoreProvider(base_url="https://api.cibil.test/score", api_key="secret-key")
    mock_resp = httpx.Response(status_code=500, text="Internal Server Error")
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await provider.get_credit_score(mobile="9876543210")
        assert result.success is False
        assert result.error_code == "CREDIT_SCORE_SERVER_ERROR_500"


@pytest.mark.asyncio
async def test_13_cibil_provider_503_service_unavailable():
    provider = CibilCreditScoreProvider(base_url="https://api.cibil.test/score", api_key="secret-key")
    mock_resp = httpx.Response(status_code=503, text="Service Unavailable")
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await provider.get_credit_score(mobile="9876543210")
        assert result.success is False
        assert result.error_code == "CREDIT_SCORE_SERVER_ERROR_503"


@pytest.mark.asyncio
async def test_14_cibil_malformed_json_response():
    provider = CibilCreditScoreProvider(base_url="https://api.cibil.test/score", api_key="secret-key")
    mock_resp = httpx.Response(status_code=200, content=b"INVALID NON JSON STRING")
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await provider.get_credit_score(mobile="9876543210")
        assert result.success is False
        assert result.error_code == "CREDIT_SCORE_MALFORMED_RESPONSE"


@pytest.mark.asyncio
async def test_15_cibil_missing_credit_score_field():
    provider = CibilCreditScoreProvider(base_url="https://api.cibil.test/score", api_key="secret-key")
    mock_resp = httpx.Response(status_code=200, json={"status": "OK"})  # missing credit_score
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await provider.get_credit_score(mobile="9876543210")
        assert result.success is False
        assert result.error_code == "CREDIT_SCORE_MISSING"


@pytest.mark.asyncio
async def test_16_cibil_invalid_credit_score_type():
    provider = CibilCreditScoreProvider(base_url="https://api.cibil.test/score", api_key="secret-key")
    mock_resp = httpx.Response(status_code=200, json={"credit_score": "NOT_A_NUMBER"})
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await provider.get_credit_score(mobile="9876543210")
        assert result.success is False
        assert result.error_code == "CREDIT_SCORE_INVALID_TYPE"


@pytest.mark.asyncio
async def test_17_cibil_valid_boundary_300_score():
    provider = CibilCreditScoreProvider(base_url="https://api.cibil.test/score", api_key="secret-key")
    mock_resp = httpx.Response(status_code=200, json={"credit_score": 300})
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await provider.get_credit_score(mobile="9876543210")
        assert result.success is True
        assert result.credit_score == 300


@pytest.mark.asyncio
async def test_18_cibil_valid_boundary_900_score():
    provider = CibilCreditScoreProvider(base_url="https://api.cibil.test/score", api_key="secret-key")
    mock_resp = httpx.Response(status_code=200, json={"credit_score": 900})
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await provider.get_credit_score(mobile="9876543210")
        assert result.success is True
        assert result.credit_score == 900


@pytest.mark.asyncio
async def test_19_cibil_score_below_300_rejected():
    provider = CibilCreditScoreProvider(base_url="https://api.cibil.test/score", api_key="secret-key")
    mock_resp = httpx.Response(status_code=200, json={"credit_score": 250})
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await provider.get_credit_score(mobile="9876543210")
        assert result.success is False
        assert result.error_code == "CREDIT_SCORE_OUT_OF_RANGE"


@pytest.mark.asyncio
async def test_20_cibil_score_above_900_rejected():
    provider = CibilCreditScoreProvider(base_url="https://api.cibil.test/score", api_key="secret-key")
    mock_resp = httpx.Response(status_code=200, json={"credit_score": 950})
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await provider.get_credit_score(mobile="9876543210")
        assert result.success is False
        assert result.error_code == "CREDIT_SCORE_OUT_OF_RANGE"
