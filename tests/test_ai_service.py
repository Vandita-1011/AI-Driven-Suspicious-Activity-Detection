# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import MagicMock, patch

from src.api_interface.ai_service import AIService
from src.api_interface.request_models import AnalysisRequest
from src.api_interface.response_models import RiskReport, AlertResponse, PipelineStatusResponse
from src.orchestrator.orchestrator import PipelineResult
from src.alerts.alert_prioritizer import Alert
from src.constants.risk_levels import AlertPriority


# ---------------------------------------------------------------------------
# Helpers
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
# Tests — run_pipeline()
# ---------------------------------------------------------------------------

class TestRunPipeline:

    def setup_method(self):
        self.service = AIService()

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


# ---------------------------------------------------------------------------
# Tests — get_pipeline_status()
# ---------------------------------------------------------------------------

class TestGetPipelineStatus:

    def setup_method(self):
        self.service = AIService()

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


# ---------------------------------------------------------------------------
# Tests — _alert_to_response() with dict input
# ---------------------------------------------------------------------------

class TestAlertToResponse:

    def setup_method(self):
        self.service = AIService()

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
