"""
AI Integration Layer Service
============================
Bridge between the backend REST API layer and the Public AI Interface / Orchestrator.
Exposes production-ready integration methods, request/response validation,
structured logging (sanitized), timeout handling, and exponential backoff retry logic.
"""
import logging
import time
from typing import Dict, Any, List, Optional
from fastapi import UploadFile

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

logger = logging.getLogger(__name__)


class AIServiceAdapter:
    """
    Adapter interface wrapping the underlying Public AI Interface / Orchestrator.
    Contains explicit integration points (TODOs) for connecting Vandita's AI pipeline once merged.
    """

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def check_health(self) -> dict:
        # TODO: Replace with direct call to Vandita's Public AI Interface health check endpoint after branch merge.
        return {"status": "ok", "message": "AI Engine is ready."}

    def execute_investigation(self, request_data: dict) -> dict:
        # TODO: Replace with direct call to Vandita's Public AI Interface / Orchestrator after branch merge.
        return {
            "request_id": request_data.get("request_id"),
            "investigation_id": request_data.get("investigation_id"),
            "status": "PENDING",
            "message": "Waiting for Public AI Interface.",
        }

    def query_status(self, investigation_id: str, request_id: str) -> dict:
        # TODO: Replace with direct call to Vandita's Public AI Interface status query after branch merge.
        return {
            "request_id": request_id,
            "investigation_id": investigation_id,
            "status": "IN_PROGRESS",
            "progress_percentage": 100.0,
        }

    def abort_investigation(self, investigation_id: str, request_id: str) -> dict:
        # TODO: Replace with direct call to Vandita's Public AI Interface cancellation method after branch merge.
        return {
            "request_id": request_id,
            "investigation_id": investigation_id,
            "status": "CANCELLED",
            "message": "Investigation successfully cancelled.",
        }


class AIService:
    """
    Production-ready AI Integration Layer.
    Handles validation, typed models, retry with exponential backoff, logging, and error handling.
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        adapter: Optional[AIServiceAdapter] = None,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.adapter = adapter or AIServiceAdapter(timeout=timeout)

    def _log_structured(
        self,
        request_id: Optional[str],
        investigation_id: Optional[str],
        execution_time: float,
        retry_count: int,
        status: str,
    ) -> None:
        """
        Structured logger that logs ONLY non-sensitive operational telemetry.
        """
        logger.info(
            "AI_SERVICE_TELEMETRY - request_id=%s investigation_id=%s execution_time=%.4fs retry_count=%d status=%s",
            request_id or "N/A",
            investigation_id or "N/A",
            execution_time,
            retry_count,
            status,
        )

    def _execute_with_retry(
        self,
        operation_name: str,
        func,
        request_id: Optional[str] = None,
        investigation_id: Optional[str] = None,
    ) -> dict:
        """
        Executes a function with retry logic (up to 3 retries with exponential backoff)
        and logs execution metrics upon completion or failure.
        """
        start_time = time.time()
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                # Execution attempt
                result = func()
                execution_time = time.time() - start_time
                self._log_structured(
                    request_id=request_id,
                    investigation_id=investigation_id,
                    execution_time=execution_time,
                    retry_count=attempt - 1,
                    status="SUCCESS",
                )
                return result
            except (AIValidationError, AITimeoutError, AIConnectionError, AIUnavailableError) as exc:
                last_exception = exc
            except TimeoutError as exc:
                last_exception = AITimeoutError(f"Operation '{operation_name}' timed out after {self.timeout}s.")
            except ConnectionError as exc:
                last_exception = AIConnectionError(f"Connection failed during '{operation_name}': {str(exc)}")
            except Exception as exc:
                last_exception = AIUnavailableError(f"Unexpected engine failure during '{operation_name}': {str(exc)}")

            # Exponential backoff sleep
            if attempt < self.max_retries:
                sleep_duration = self.backoff_factor * (2 ** (attempt - 1))
                logger.warning(
                    "AI_SERVICE_RETRY - attempt=%d operation=%s request_id=%s retrying in %.2fs due to: %s",
                    attempt,
                    operation_name,
                    request_id or "N/A",
                    sleep_duration,
                    str(last_exception),
                )
                time.sleep(sleep_duration)

        execution_time = time.time() - start_time
        self._log_structured(
            request_id=request_id,
            investigation_id=investigation_id,
            execution_time=execution_time,
            retry_count=self.max_retries - 1,
            status="FAILED",
        )
        if last_exception:
            raise last_exception
        raise AIUnavailableError(f"Operation '{operation_name}' failed after maximum retries.")

    # ----------------------------------------------------------------
    # Production-Ready Integration API
    # ----------------------------------------------------------------

    def health_check(self) -> HealthCheckResponse:
        """
        Exposes system health check. Validates health response structure.
        """
        request_id = "health_check_req"
        
        def _call():
            raw = self.adapter.check_health()
            if not isinstance(raw, dict) or "status" not in raw or "message" not in raw:
                raise AIValidationError("Malformed response received from AI engine health check.")
            return raw

        raw_response = self._execute_with_retry(
            operation_name="health_check",
            func=_call,
            request_id=request_id,
        )

        try:
            return HealthCheckResponse(**raw_response)
        except Exception as e:
            raise AIValidationError(f"Response validation failed for health check: {str(e)}")

    def submit_investigation(self, request: InvestigationRequest) -> InvestigationResponse:
        """
        Validates request, submits an investigation payload, retries with backoff,
        validates response structure, and returns typed response.
        """
        if not isinstance(request, InvestigationRequest):
            raise AIValidationError("Request must be an instance of InvestigationRequest.")
        if not request.request_id or not request.request_id.strip():
            raise AIValidationError("Validation failed: request_id cannot be empty.")
        if not request.investigation_id or not request.investigation_id.strip():
            raise AIValidationError("Validation failed: investigation_id cannot be empty.")

        payload = request.model_dump()

        def _call():
            raw = self.adapter.execute_investigation(payload)
            if not isinstance(raw, dict):
                raise AIValidationError("Malformed response from AI engine (expected dict).")
            if raw.get("request_id") != request.request_id:
                raise AIValidationError("Response request_id does not match request_id.")
            if raw.get("investigation_id") != request.investigation_id:
                raise AIValidationError("Response investigation_id does not match investigation_id.")
            return raw

        raw_response = self._execute_with_retry(
            operation_name="submit_investigation",
            func=_call,
            request_id=request.request_id,
            investigation_id=request.investigation_id,
        )

        try:
            return InvestigationResponse(**raw_response)
        except Exception as e:
            raise AIValidationError(f"Response validation failed for submit_investigation: {str(e)}")

    def get_investigation_status(self, investigation_id: str, request_id: Optional[str] = None) -> StatusResponse:
        """
        Queries current execution status of an investigation.
        """
        req_id = request_id or f"req_status_{investigation_id}"
        if not investigation_id or not investigation_id.strip():
            raise AIValidationError("Validation failed: investigation_id cannot be empty.")

        def _call():
            raw = self.adapter.query_status(investigation_id=investigation_id, request_id=req_id)
            if not isinstance(raw, dict) or "status" not in raw:
                raise AIValidationError("Malformed response from AI engine status query.")
            return raw

        raw_response = self._execute_with_retry(
            operation_name="get_investigation_status",
            func=_call,
            request_id=req_id,
            investigation_id=investigation_id,
        )

        try:
            return StatusResponse(**raw_response)
        except Exception as e:
            raise AIValidationError(f"Response validation failed for get_investigation_status: {str(e)}")

    def cancel_investigation(self, investigation_id: str, request_id: Optional[str] = None) -> CancelResponse:
        """
        Requests cancellation of an ongoing investigation.
        """
        req_id = request_id or f"req_cancel_{investigation_id}"
        if not investigation_id or not investigation_id.strip():
            raise AIValidationError("Validation failed: investigation_id cannot be empty.")

        def _call():
            raw = self.adapter.abort_investigation(investigation_id=investigation_id, request_id=req_id)
            if not isinstance(raw, dict) or "status" not in raw:
                raise AIValidationError("Malformed response from AI engine cancellation.")
            return raw

        raw_response = self._execute_with_retry(
            operation_name="cancel_investigation",
            func=_call,
            request_id=req_id,
            investigation_id=investigation_id,
        )

        try:
            return CancelResponse(**raw_response)
        except Exception as e:
            raise AIValidationError(f"Response validation failed for cancel_investigation: {str(e)}")

    # ----------------------------------------------------------------
    # Backwards-Compatibility Layer for FastAPI Routers
    # ----------------------------------------------------------------

    def process_uploaded_file(self, file: UploadFile) -> Dict[str, Any]:
        """Temporary stub for upload route. TODO: Replace with real backend storage service after merging Vandita's Public AI Interface."""
        return self.upload_transactions(file)

    def upload_transactions(self, file: UploadFile) -> Dict[str, Any]:
        """Temporary stub for upload route. TODO: Replace with real backend storage service after merging Vandita's Public AI Interface."""
        if not file or not file.filename:
            raise AIValidationError("Uploaded file or file name is missing.")
        return {"status": "success", "file_name": file.filename}

    def run_analysis(self) -> Dict[str, Any]:
        """Temporary stub for triggering analysis. TODO: Replace with real pipeline orchestrator call after merging Vandita's Public AI Interface."""
        req = InvestigationRequest(request_id="auto_trigger_req", investigation_id="auto_trigger_inv")
        resp = self.submit_investigation(req)
        return {"status": resp.status, "message": resp.message or "Analysis completed successfully."}

    def get_dashboard_data(self) -> Dict[str, int]:
        """Temporary stub for dashboard metrics. TODO: Replace with real analytics service call after merging Vandita's Public AI Interface."""
        return {
            "total_alerts": 120,
            "high_risk": 15,
            "medium_risk": 45,
            "low_risk": 60,
        }

    def get_alerts(self) -> List[Dict[str, Any]]:
        """Temporary stub for alert listing. TODO: Replace with real database query after merging Vandita's Public AI Interface."""
        return [
            {"alert_id": "ALT-001", "severity": "HIGH", "description": "Suspicious large transfer"},
            {"alert_id": "ALT-002", "severity": "MEDIUM", "description": "Unusual login location"},
        ]

    def get_alert(self, alert_id: str) -> Dict[str, Any]:
        """Temporary stub for alert details. TODO: Replace with real database query after merging Vandita's Public AI Interface."""
        if not alert_id or not alert_id.strip():
            raise AIValidationError("Alert ID cannot be empty.")
        return {
            "alert_id": alert_id,
            "severity": "HIGH",
            "description": "Suspicious large transfer",
            "details": {"transaction_amount": 50000, "currency": "USD"},
        }

    def get_investigation(self, alert_id: str) -> Dict[str, Any]:
        """Temporary stub for investigation details. TODO: Replace with real investigation service call after merging Vandita's Public AI Interface."""
        if not alert_id or not alert_id.strip():
            raise AIValidationError("Alert ID cannot be empty.")
        return {
            "alert_id": alert_id,
            "status": "In Progress",
            "notes": ["Reviewed transaction history.", "Pending customer call."],
        }

    def update_investigation(self, alert_id: str, payload: Any) -> Dict[str, Any]:
        """Temporary stub for investigation updates. TODO: Replace with real investigation service call after merging Vandita's Public AI Interface."""
        if not alert_id or not alert_id.strip():
            raise AIValidationError("Alert ID cannot be empty.")
        status_val = getattr(payload, "status", "Updated")
        return {
            "alert_id": alert_id,
            "updated_status": status_val,
            "message": "Investigation updated successfully.",
        }

    def get_reports(self) -> List[Dict[str, str]]:
        """Temporary stub for reports listing. TODO: Replace with real report generation service call after merging Vandita's Public AI Interface."""
        return [
            {"report_id": "REP-001", "name": "Monthly AML Summary"},
            {"report_id": "REP-002", "name": "High Risk Entities"},
        ]
