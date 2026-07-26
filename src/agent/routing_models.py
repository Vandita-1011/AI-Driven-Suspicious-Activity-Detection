"""
Routing Models
==============
Data models for the Tool Selection & Routing stage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from src.agent.plan_models import PlanStep


class StepStatus(str, Enum):
    BLOCKED = "BLOCKED"
    READY = "READY"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class RoutedStep:
    """
    Extends PlanStep with routing metadata and readiness status.
    """
    plan_step: PlanStep
    status: StepStatus = StepStatus.BLOCKED
    retry_count: int = 0
    max_retries: int = 3
    routing_metadata: Dict[str, str] = field(default_factory=dict)
    
    @property
    def step_id(self) -> str:
        return self.plan_step.step_id


@dataclass
class ExecutionStage:
    """
    A group of steps that can be executed in parallel.
    All steps in this stage depend only on steps from previous stages.
    """
    stage_number: int
    tools: List[RoutedStep] = field(default_factory=list)


@dataclass
class RoutedPlan:
    """
    A fully routed execution plan structured into sequential stages.
    """
    plan_id: str
    stages: List[ExecutionStage] = field(default_factory=list)
