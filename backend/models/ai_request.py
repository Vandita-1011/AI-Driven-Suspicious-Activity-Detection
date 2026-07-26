"""
AI Request Models
=================
Typed Pydantic request models for the AI Integration Layer.
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class InvestigationRequest(BaseModel):
    request_id: str = Field(..., min_length=1, description="Unique request identifier")
    investigation_id: str = Field(..., min_length=1, description="Unique investigation identifier")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    transaction_ids: Optional[List[str]] = Field(default_factory=list)


class HealthCheckRequest(BaseModel):
    request_id: str = Field(..., min_length=1, description="Unique request identifier")
