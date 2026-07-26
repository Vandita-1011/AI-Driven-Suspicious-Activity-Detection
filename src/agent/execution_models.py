"""
Execution Models
================
Data models for the Execution Controller stage.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class ExecutionStatus(str, Enum):
    """Status states for an execution run or individual step."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    CANCELLED = "CANCELLED"


@dataclass
class ExecutionLogEntry:
    """Chronological execution log entry."""
    step_id: str
    tool_name: str
    status: ExecutionStatus
    message: str
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.utcnow)


@dataclass
class ExecutionResult:
    """Final result of an execution run."""
    execution_id: str
    session_id: str
    plan_id: str
    status: ExecutionStatus
    started_at: datetime.datetime
    finished_at: Optional[datetime.datetime] = None
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    execution_log: List[ExecutionLogEntry] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
