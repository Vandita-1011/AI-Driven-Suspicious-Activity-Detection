"""
Unit tests for Module 1: AI Integration Layer (AIService)
"""
import pytest
from unittest.mock import MagicMock

from backend.exceptions.ai_exceptions import (
    AIServiceException,
    AIValidationError,
    AIConnectionError,
    AITimeoutError,
    AIUnavailableError,
)
from backend.models.ai_request import InvestigationRequest, HealthCheckRequest
from backend.models.ai_response import (
    HealthCheckResponse,
    InvestigationResponse,
    StatusResponse,
    CancelResponse,
)
from backend.services.ai_service import AIService, AIServiceAdapter


def test_health_check_success():
    service = AIService()
    response = service.health_check()
    assert isinstance(response, HealthCheckResponse)
    assert response.status == "ok"
    assert "ready" in response.message.lower()


def test_submit_investigation_success():
    service = AIService()
    req = InvestigationRequest(
        request_id="req-123",
        investigation_id="inv-456",
        transaction_ids=["tx-1", "tx-2"],
    )
    resp = service.submit_investigation(req)
    assert isinstance(resp, InvestigationResponse)
    assert resp.request_id == "req-123"
    assert resp.investigation_id == "inv-456"
    assert resp.status == "COMPLETED"


def test_submit_investigation_validation_error_empty_id():
    service = AIService()
    with pytest.raises(AIValidationError):
        service.submit_investigation(
            InvestigationRequest(request_id="   ", investigation_id="inv-1")
        )

    with pytest.raises(AIValidationError):
        service.submit_investigation(
            InvestigationRequest(request_id="req-1", investigation_id="")
        )


def test_get_investigation_status_success():
    service = AIService()
    resp = service.get_investigation_status("inv-789", request_id="req-789")
    assert isinstance(resp, StatusResponse)
    assert resp.investigation_id == "inv-789"
    assert resp.status == "IN_PROGRESS"


def test_get_investigation_status_invalid_id():
    service = AIService()
    with pytest.raises(AIValidationError):
        service.get_investigation_status("")


def test_cancel_investigation_success():
    service = AIService()
    resp = service.cancel_investigation("inv border-999")
    assert isinstance(resp, CancelResponse)
    assert resp.investigation_id == "inv border-999"
    assert resp.status == "CANCELLED"


def test_adapter_response_validation_failure():
    mock_adapter = MagicMock()
    mock_adapter.execute_investigation.return_value = "invalid response (not a dict)"
    service = AIService(max_retries=1, adapter=mock_adapter)

    req = InvestigationRequest(request_id="req-1", investigation_id="inv-1")
    with pytest.raises(AIValidationError):
        service.submit_investigation(req)


def test_retry_mechanism_exhausted():
    mock_adapter = MagicMock()
    mock_adapter.execute_investigation.side_effect = TimeoutError("Connection timed out")
    service = AIService(max_retries=3, backoff_factor=0.01, adapter=mock_adapter)

    req = InvestigationRequest(request_id="req-1", investigation_id="inv-1")
    with pytest.raises(AITimeoutError):
        service.submit_investigation(req)

    assert mock_adapter.execute_investigation.call_count == 3


def test_retry_mechanism_recovers():
    mock_adapter = MagicMock()
    mock_adapter.execute_investigation.side_effect = [
        ConnectionError("Transient failure"),
        {
            "request_id": "req-1",
            "investigation_id": "inv-1",
            "status": "COMPLETED",
            "message": "Recovered",
        },
    ]
    service = AIService(max_retries=3, backoff_factor=0.01, adapter=mock_adapter)

    req = InvestigationRequest(request_id="req-1", investigation_id="inv-1")
    resp = service.submit_investigation(req)

    assert resp.status == "COMPLETED"
    assert mock_adapter.execute_investigation.call_count == 2
