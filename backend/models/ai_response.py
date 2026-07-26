"""
AI Response Models
==================
Typed Pydantic response models for the AI Integration Layer.
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    status: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class InvestigationResponse(BaseModel):
    request_id: str = Field(..., min_length=1)
    investigation_id: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    message: Optional[str] = None
    results: Optional[Dict[str, Any]] = None


class StatusResponse(BaseModel):
    request_id: str = Field(..., min_length=1)
    investigation_id: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    progress_percentage: Optional[float] = 0.0


class CancelResponse(BaseModel):
    request_id: str = Field(..., min_length=1)
    investigation_id: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    message: Optional[str] = None
