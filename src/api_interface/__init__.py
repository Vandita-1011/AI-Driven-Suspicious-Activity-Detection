"""
API Interface Package
=====================
Typed request and response models for the API boundary.

These are plain Python dataclasses — no FastAPI imports.
The FastAPI developer imports these models and wraps them in route handlers.

Request models  (src/api_interface/request_models.py):
    AnalysisRequest     Full pipeline run with optional filters
    CustomerQueryRequest Single customer investigation
    AlertQueryRequest   Paginated alert retrieval with filters

Response models (src/api_interface/response_models.py):
    AlertResponse       Single alert with explanation and recommendation
    RiskReport          Full pipeline run summary
    CustomerRiskProfile Per-customer risk summary
    PipelineStatusResponse Pipeline execution metadata

Usage (by the FastAPI developer):
    from src.api_interface.request_models import AnalysisRequest
    from src.api_interface.response_models import RiskReport
"""
from src.api_interface.request_models import (
    AnalysisRequest,
    CustomerQueryRequest,
    AlertQueryRequest,
)
from src.api_interface.response_models import (
    AlertResponse,
    RiskReport,
    CustomerRiskProfile,
    PipelineStatusResponse,
)

__all__ = [
    "AnalysisRequest", "CustomerQueryRequest", "AlertQueryRequest",
    "AlertResponse", "RiskReport", "CustomerRiskProfile", "PipelineStatusResponse",
]
