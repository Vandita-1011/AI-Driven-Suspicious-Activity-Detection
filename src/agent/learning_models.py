"""
Learning Models
===============
Data models for the Continuous Learning & Feedback module.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from src.agent.execution_models import ExecutionStatus


class FeedbackType(str, Enum):
    """Categorized feedback types from investigators."""
    TRUE_POSITIVE = "TRUE_POSITIVE"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    TRUE_NEGATIVE = "TRUE_NEGATIVE"
    FALSE_NEGATIVE = "FALSE_NEGATIVE"
    INVESTIGATOR_NOTE = "INVESTIGATOR_NOTE"


@dataclass
class LearningRecord:
    """Historical learning record capturing execution outcome and investigator feedback."""
    record_id: str
    session_id: str
    execution_id: str
    plan_id: str
    timestamp: datetime.datetime
    execution_status: ExecutionStatus
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    execution_duration: float = 0.0
    feedback_type: Optional[FeedbackType] = None
    investigator_notes: Optional[str] = None
    risk_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningSummary:
    """Aggregated summary of recorded executions and feedback."""
    total_records: int
    successful_executions: int
    failed_executions: int
    partial_executions: int
    cancelled_executions: int
    feedback_distribution: Dict[str, int] = field(default_factory=dict)
    total_investigator_notes: int = 0
    average_execution_time: float = 0.0
    generated_at: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
