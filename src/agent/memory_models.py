"""
Memory Models
=============
Data models for the in-memory Context & Memory module.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import List, Optional

from src.agent.entity_models import EntityExtractionResult
from src.agent.intent_models import IntentResult
from src.agent.pattern_models import PatternIdentificationResult
from src.agent.plan_models import ExecutionPlan
from src.agent.routing_models import RoutedPlan


@dataclass
class InvestigationSession:
    """Metadata about the current investigation session."""
    session_id: str
    investigation_id: Optional[str] = None
    created_at: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = field(default_factory=datetime.datetime.utcnow)

    def touch(self) -> None:
        """Updates the updated_at timestamp."""
        self.updated_at = datetime.datetime.utcnow()


@dataclass
class ConversationState:
    """Stores natural language context."""
    latest_query: Optional[str] = None
    query_history: List[str] = field(default_factory=list)

    def add_query(self, query: str) -> None:
        self.latest_query = query
        self.query_history.append(query)


@dataclass
class PlanningState:
    """Stores the outputs of the intelligence and planning layers."""
    intent_result: Optional[IntentResult] = None
    entity_result: Optional[EntityExtractionResult] = None
    pattern_result: Optional[PatternIdentificationResult] = None
    execution_plan: Optional[ExecutionPlan] = None
    routed_plan: Optional[RoutedPlan] = None


@dataclass
class ExecutionState:
    """Tracks the progress of tool execution."""
    current_stage: int = 0
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    pending_steps: List[str] = field(default_factory=list)


@dataclass
class ContextMemory:
    """
    Top-level object containing all state for a single session.
    """
    session: InvestigationSession
    conversation_state: ConversationState = field(default_factory=ConversationState)
    planning_state: PlanningState = field(default_factory=PlanningState)
    execution_state: ExecutionState = field(default_factory=ExecutionState)

    def touch(self) -> None:
        """Touches the underlying session to update the timestamp."""
        self.session.touch()
