"""
API Response Models
===================
Typed plain Python dataclasses representing API responses.
"""
from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class AlertResponse:
    """Single alert response."""
    alert_id: str
    transaction_id: str
    customer_id: str
    priority: str
    score: float
    action: str
    explanation: str


@dataclass
class RiskReport:
    """Summary of a pipeline run."""
    run_id: str
    total_transactions_processed: int
    alerts_generated: int
    alerts: List[AlertResponse] = field(default_factory=list)


@dataclass
class CustomerRiskProfile:
    """Customer risk summary."""
    customer_id: str
    risk_level: str
    total_alerts: int
    profile_features: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineStatusResponse:
    """Status of the execution."""
    status: str
    message: str
    elapsed_seconds: float
