"""
Plan Models
===========
Data models for the Dynamic Plan Generation stage.
Defines logical tools and execution steps independently of physical routing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class LogicalTool(str, Enum):
    """
    Logical tool identifiers.
    Independent of actual Python functions or REST endpoints.
    """
    LOAD_CUSTOMER = "LOAD_CUSTOMER"
    LOAD_TRANSACTIONS = "LOAD_TRANSACTIONS"
    LOAD_ACCOUNTS = "LOAD_ACCOUNTS"
    LOAD_DATASET = "LOAD_DATASET"
    
    RUN_RULE_ENGINE = "RUN_RULE_ENGINE"
    RUN_BEHAVIOUR_ENGINE = "RUN_BEHAVIOUR_ENGINE"
    RUN_STATISTICAL_ENGINE = "RUN_STATISTICAL_ENGINE"
    RUN_ML_ENGINE = "RUN_ML_ENGINE"
    RUN_PATTERN_ENGINE = "RUN_PATTERN_ENGINE"
    
    RUN_RISK_FUSION = "RUN_RISK_FUSION"
    RUN_EXPLAINABILITY = "RUN_EXPLAINABILITY"
    RUN_RECOMMENDATION = "RUN_RECOMMENDATION"
    RUN_ALERT_PRIORITIZER = "RUN_ALERT_PRIORITIZER"
    
    MANUAL_REVIEW = "MANUAL_REVIEW"
    FORMAT_REPORT = "FORMAT_REPORT"


class StepPriority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class PlanStep:
    """
    A single logical step in an execution plan.
    """
    step_id: str
    description: str
    logical_tool: LogicalTool
    required_inputs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    priority: StepPriority = StepPriority.MEDIUM
    validation_constraints: List[str] = field(default_factory=list)
    early_stopping_possible: bool = False


@dataclass
class ExecutionPlan:
    """
    A full logical execution plan containing all steps required to
    fulfill the recognized pattern.
    """
    plan_id: str
    pattern_type: str
    steps: List[PlanStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
