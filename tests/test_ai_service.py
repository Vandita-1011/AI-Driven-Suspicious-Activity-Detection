# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import MagicMock, patch

# Vandita's imports
from src.api_interface.ai_service import AIService as EngineAIService
from src.api_interface.request_models import AnalysisRequest
from src.api_interface.response_models import RiskReport, AlertResponse, PipelineStatusResponse
from src.orchestrator.orchestrator import PipelineResult
from src.alerts.alert_prioritizer import Alert
from src.constants.risk_levels import AlertPriority

# Harsh's imports
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
from backend.services.ai_service import AIService as BackendAIService, AIServiceAdapter

# ---------------------------------------------------------------------------
# Vandita's Helpers
# ---------------------------------------------------------------------------

def _make_request(run_id: str = "RUN001") -> AnalysisRequest:
    return AnalysisRequest(run_id=run_id)

def _make_alert(tid: str = "TXN001") -> Alert:
    return Alert(
        alert_id="ALT-AABBCC112233",
        transaction_id=tid,
        customer_id="CUST001",
        priority=AlertPriority.P1_CRITICAL,
        fused_risk_score=90.0,
        recommended_action="File Suspicious Activity Report (SAR)",
        narrative="Transaction flagged as CRITICAL risk.",
        timestamp="2026-07-26T00:00:00Z",
        risk_level="CRITICAL",
        confidence_score=0.92,
        alert_title="CRITICAL Risk | 2 Rules Triggered",
        alert_summary="Transaction TXN001 flagged as CRITICAL (score 90.0).",
        status="OPEN",
    )

def _successful_pipeline_result(alert: Alert) -> PipelineResult:
    return PipelineResult(
        success=True,
        alerts=[alert],
        elapsed_seconds=1.23,
    )

def _failed_pipeline_result() -> PipelineResult:
    return PipelineResult(
        success=False,
        alerts=[],
        elapsed_seconds=0.5,
        error_message="Data load error.",
    )

# ---------------------------------------------------------------------------
# Vandita's Tests — EngineAIService
# ---------------------------------------------------------------------------

class TestRunPipeline:

    def setup_method(self):
        self.service = EngineAIService()

    @patch("src.api_interface.ai_service.Orchestrator")
    def test_successful_run_returns_risk_report(self, MockOrchestrator):
        alert = _make_alert()
        MockOrchestrator.return_value.run.return_value = _successful_pipeline_result(alert)

        report = self.service.run_pipeline(_make_request())

        assert isinstance(report, RiskReport)
        assert report.run_id == "RUN001"
        assert report.alerts_generated == 1
        assert len(report.alerts) == 1

    @patch("src.api_interface.ai_service.Orchestrator")
    def test_alert_mapped_to_alert_response(self, MockOrchestrator):
        alert = _make_alert("TXN999")
        MockOrchestrator.return_value.run.return_value = _successful_pipeline_result(alert)

        report = self.service.run_pipeline(_make_request())
        resp = report.alerts[0]

        assert isinstance(resp, AlertResponse)
        assert resp.transaction_id == "TXN999"
        assert resp.alert_id == "ALT-AABBCC112233"
        assert resp.customer_id == "CUST001"
        assert resp.priority == "P1_CRITICAL"
        assert resp.score == 90.0
        assert resp.explanation == "Transaction flagged as CRITICAL risk."

    @patch("src.api_interface.ai_service.Orchestrator")
    def test_failed_pipeline_returns_empty_report(self, MockOrchestrator):
        MockOrchestrator.return_value.run.return_value = _failed_pipeline_result()

        report = self.service.run_pipeline(_make_request())

        assert isinstance(report, RiskReport)
        assert report.alerts_generated == 0
        assert report.alerts == []

    @patch("src.api_interface.ai_service.Orchestrator")
    def test_orchestrator_exception_returns_empty_report(self, MockOrchestrator):
        MockOrchestrator.return_value.run.side_effect = RuntimeError("Unexpected DB error")

        report = self.service.run_pipeline(_make_request())

        assert isinstance(report, RiskReport)
        assert report.alerts_generated == 0
        assert report.alerts == []

    def test_none_request_returns_empty_report(self):
        report = self.service.run_pipeline(None)

        assert isinstance(report, RiskReport)
        assert report.alerts_generated == 0
        assert report.alerts == []

    def test_empty_run_id_returns_empty_report(self):
        request = AnalysisRequest(run_id="   ")
        report = self.service.run_pipeline(request)

        assert isinstance(report, RiskReport)
        assert report.alerts_generated == 0

    @patch("src.api_interface.ai_service.Orchestrator")
    def test_empty_alerts_pipeline_returns_zero_count(self, MockOrchestrator):
        MockOrchestrator.return_value.run.return_value = PipelineResult(
            success=True, alerts=[], elapsed_seconds=0.5
        )
        report = self.service.run_pipeline(_make_request())

        assert report.alerts_generated == 0
        assert report.alerts == []


class TestGetPipelineStatus:

    def setup_method(self):
        self.service = EngineAIService()

    def test_success_status(self):
        status = self.service.get_pipeline_status(elapsed_seconds=2.5, success=True)

        assert isinstance(status, PipelineStatusResponse)
        assert status.status == "SUCCESS"
        assert status.elapsed_seconds == 2.5
        assert "successfully" in status.message.lower()

    def test_failed_status(self):
        status = self.service.get_pipeline_status(elapsed_seconds=0.3, success=False)

        assert status.status == "FAILED"
        assert "error" in status.message.lower()


class TestAlertToResponse:

    def setup_method(self):
        self.service = EngineAIService()

    def test_dict_alert_mapped_correctly(self):
        alert_dict = {
            "alert_id": "ALT-DICT001",
            "transaction_id": "TXN002",
            "customer_id": "CUST002",
            "priority": "P2_HIGH",
            "fused_risk_score": 77.5,
            "recommended_action": "Escalate",
            "narrative": "HIGH risk detected.",
        }
        resp = self.service._alert_to_response(alert_dict)

        assert resp.alert_id == "ALT-DICT001"
        assert resp.transaction_id == "TXN002"
        assert resp.score == 77.5
        assert resp.explanation == "HIGH risk detected."


# ---------------------------------------------------------------------------
# Harsh's Tests — BackendAIService
# ---------------------------------------------------------------------------

def test_health_check_success():
    service = BackendAIService()
    response = service.health_check()
    assert isinstance(response, HealthCheckResponse)
    assert response.status == "ok"
    assert "ready" in response.message.lower()


def test_submit_investigation_success():
    service = BackendAIService()
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
    service = BackendAIService()
    with pytest.raises(AIValidationError):
        service.submit_investigation(
            InvestigationRequest(request_id="   ", investigation_id="inv-1")
        )

    with pytest.raises(AIValidationError):
        service.submit_investigation(
            InvestigationRequest(request_id="req-1", investigation_id="")
        )


def test_get_investigation_status_success():
    service = BackendAIService()
    resp = service.get_investigation_status("inv-789", request_id="req-789")
    assert isinstance(resp, StatusResponse)
    assert resp.investigation_id == "inv-789"
    assert resp.status == "IN_PROGRESS"


def test_get_investigation_status_invalid_id():
    service = BackendAIService()
    with pytest.raises(AIValidationError):
        service.get_investigation_status("")


def test_cancel_investigation_success():
    service = BackendAIService()
    resp = service.cancel_investigation("inv border-999")
    assert isinstance(resp, CancelResponse)
    assert resp.investigation_id == "inv border-999"
    assert resp.status == "CANCELLED"


def test_adapter_response_validation_failure():
    mock_adapter = MagicMock()
    mock_adapter.execute_investigation.return_value = "invalid response (not a dict)"
    service = BackendAIService(max_retries=1, adapter=mock_adapter)

    req = InvestigationRequest(request_id="req-1", investigation_id="inv-1")
    with pytest.raises(AIValidationError):
        service.submit_investigation(req)


def test_retry_mechanism_exhausted():
    mock_adapter = MagicMock()
    mock_adapter.execute_investigation.side_effect = TimeoutError("Connection timed out")
    service = BackendAIService(max_retries=3, backoff_factor=0.01, adapter=mock_adapter)

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
    service = BackendAIService(max_retries=3, backoff_factor=0.01, adapter=mock_adapter)

    req = InvestigationRequest(request_id="req-1", investigation_id="inv-1")
    resp = service.submit_investigation(req)

    assert resp.status == "COMPLETED"
    assert mock_adapter.execute_investigation.call_count == 2
