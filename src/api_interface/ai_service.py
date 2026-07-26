"""
AI Service
==========
Public API layer for the AML AI Detection pipeline.

Serves as the single entry point into the AI engine for all external callers
(backend services, FastAPI routes, CLI tools).

Responsibilities:
  - Validate incoming AnalysisRequest.
  - Initialise and invoke the Orchestrator.
  - Map PipelineResult → structured response models.
  - Catch and log all exceptions without exposing stack traces.
  - Return consistently typed responses.

Usage:
    from src.api_interface.ai_service import AIService

    service = AIService()
    report = service.run_pipeline(request)
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, List

from src.api_interface.request_models import AnalysisRequest
from src.api_interface.response_models import (
    AlertResponse,
    PipelineStatusResponse,
    RiskReport,
)
from src.orchestrator.orchestrator import Orchestrator, PipelineResult
from src.utils.logger import get_logger
from src.utils.timer import timed

logger = get_logger(__name__)


class AIService:
    """
    Public interface to the AML AI Detection pipeline.

    Validates requests, invokes the Orchestrator, and returns structured
    responses without leaking internal implementation details.
    """

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_request(request: AnalysisRequest) -> str | None:
        """
        Validates an AnalysisRequest.

        Returns:
            None if valid; a human-readable error string if invalid.
        """
        if not request:
            return "Request must not be None."
        if not request.run_id or not request.run_id.strip():
            return "AnalysisRequest.run_id must be a non-empty string."
        return None

    @staticmethod
    def _alert_to_response(alert: Any) -> AlertResponse:
        """
        Maps a single Alert object to an AlertResponse.

        Handles both the extended Alert (from alert_prioritizer) and any
        legacy-shaped dict gracefully.
        """
        if isinstance(alert, dict):
            return AlertResponse(
                alert_id=str(alert.get("alert_id", "")),
                transaction_id=str(alert.get("transaction_id", "")),
                customer_id=str(alert.get("customer_id", "")),
                priority=str(alert.get("priority", "")),
                score=float(alert.get("fused_risk_score", 0.0)),
                action=str(alert.get("recommended_action", "")),
                explanation=str(alert.get("narrative", "")),
            )

        return AlertResponse(
            alert_id=getattr(alert, "alert_id", ""),
            transaction_id=getattr(alert, "transaction_id", ""),
            customer_id=getattr(alert, "customer_id", ""),
            priority=(
                alert.priority.value
                if hasattr(alert.priority, "value")
                else str(getattr(alert, "priority", ""))
            ),
            score=float(getattr(alert, "fused_risk_score", 0.0)),
            action=str(getattr(alert, "recommended_action", "")),
            explanation=str(getattr(alert, "narrative", "")),
        )

    def _build_report(
        self,
        run_id: str,
        pipeline_result: PipelineResult,
        total_transactions: int,
    ) -> RiskReport:
        """Converts a PipelineResult into a RiskReport."""
        alert_responses: List[AlertResponse] = [
            self._alert_to_response(alert)
            for alert in (pipeline_result.alerts or [])
        ]
        return RiskReport(
            run_id=run_id,
            total_transactions_processed=total_transactions,
            alerts_generated=len(alert_responses),
            alerts=alert_responses,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @timed("AIService.run_pipeline")
    def run_pipeline(self, request: AnalysisRequest) -> RiskReport:
        """
        Validates the request, runs the full AML detection pipeline, and
        returns a RiskReport summarising the results.

        Args:
            request: AnalysisRequest with run_id and optional date filters.

        Returns:
            RiskReport with success status, alert list, and execution metadata.

        Raises:
            Never raises — all exceptions are caught, logged, and reflected
            in the returned RiskReport (zero alerts, error context in run_id).
        """
        # 1. Validate
        validation_error = self._validate_request(request)
        if validation_error:
            logger.error("Invalid AnalysisRequest: %s", validation_error)
            return RiskReport(
                run_id=getattr(request, "run_id", "unknown"),
                total_transactions_processed=0,
                alerts_generated=0,
                alerts=[],
            )

        logger.info("AIService: starting pipeline run [run_id=%s]", request.run_id)

        # 2. Invoke Orchestrator
        try:
            orchestrator = Orchestrator()
            result: PipelineResult = orchestrator.run(request)
        except Exception as exc:
            logger.exception(
                "AIService: orchestrator raised an unexpected exception [run_id=%s]: %s",
                request.run_id, exc,
            )
            return RiskReport(
                run_id=request.run_id,
                total_transactions_processed=0,
                alerts_generated=0,
                alerts=[],
            )

        # 3. Handle pipeline-level failure
        if not result.success:
            logger.error(
                "AIService: pipeline failed [run_id=%s]: %s",
                request.run_id, result.error_message,
            )
            return RiskReport(
                run_id=request.run_id,
                total_transactions_processed=0,
                alerts_generated=0,
                alerts=[],
            )

        # 4. Build and return structured report
        report = self._build_report(
            run_id=request.run_id,
            pipeline_result=result,
            total_transactions=len(result.alerts),
        )

        logger.info(
            "AIService: pipeline completed [run_id=%s] — %d alert(s) in %.2fs",
            request.run_id, report.alerts_generated, result.elapsed_seconds,
        )
        return report

    def get_pipeline_status(self, elapsed_seconds: float, success: bool) -> PipelineStatusResponse:
        """
        Returns a lightweight status response summarising a pipeline execution.

        Args:
            elapsed_seconds: Wall-clock time of the pipeline run.
            success:         Whether the pipeline completed without error.

        Returns:
            PipelineStatusResponse.
        """
        return PipelineStatusResponse(
            status="SUCCESS" if success else "FAILED",
            message=(
                "Pipeline executed successfully."
                if success
                else "Pipeline encountered an error. Check logs for details."
            ),
            elapsed_seconds=elapsed_seconds,
        )
