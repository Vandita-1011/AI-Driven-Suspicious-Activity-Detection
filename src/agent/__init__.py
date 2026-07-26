"""
Agent Package
=============
Autonomous AML Investigation Agent modules.

The Agent layer provides natural-language driven investigation capabilities
on top of the existing AI detection pipeline.

Submodules (implemented progressively):
    intent_models       — Intent enum and IntentResult dataclass.
    intent_catalog      — Keyword catalogue and per-intent max scores.
    intent_recognizer   — Classifies analyst queries into Intent objects.
    entity_models       — EntityExtractionResult and related dataclasses.
    entity_extractor    — Extracts entities and filters from analyst queries.
    pattern_models      — InvestigationPatternType and PatternIdentificationResult.
    pattern_identifier  — Maps intents and entities to patterns.
    plan_models         — Logical tools and ExecutionPlan.
    dynamic_planner     — Generates logical execution plans from patterns.
    routing_models      — RoutedStep, ExecutionStage, RoutedPlan.
    tool_router         — Determines parallel execution stages via dependencies.

Usage:
    from src.agent.intent_recognizer import IntentRecognizer
    from src.agent.entity_extractor import EntityExtractor
    from src.agent.pattern_identifier import PatternIdentifier
    from src.agent.dynamic_planner import DynamicPlanner
    from src.agent.tool_router import ToolRouter
"""
from src.agent.intent_models import Intent, IntentResult
from src.agent.intent_recognizer import IntentRecognizer
from src.agent.entity_models import (
    AmountFilter,
    AmountOperator,
    DateFilter,
    EntityExtractionResult,
    RiskLevelFilter,
)
from src.agent.entity_extractor import EntityExtractor
from src.agent.pattern_models import ConfidenceLevel, InvestigationPatternType, PatternIdentificationResult
from src.agent.pattern_identifier import PatternIdentifier
from src.agent.plan_models import ExecutionPlan, LogicalTool, PlanStep, StepPriority
from src.agent.dynamic_planner import DynamicPlanner
from src.agent.routing_models import ExecutionStage, RoutedPlan, RoutedStep, StepStatus
from src.agent.tool_router import ToolRouter
from src.agent.memory_models import (
    ContextMemory,
    ConversationState,
    ExecutionState,
    InvestigationSession,
    PlanningState,
)
from src.agent.context_memory import ContextMemoryManager, SessionNotFoundError
from src.agent.execution_models import ExecutionLogEntry, ExecutionResult, ExecutionStatus
from src.agent.execution_controller import ExecutionController, ToolExecutor

__all__ = [
    "IntentRecognizer", "Intent", "IntentResult",
    "EntityExtractor", "EntityExtractionResult",
    "AmountFilter", "AmountOperator", "DateFilter", "RiskLevelFilter",
    "PatternIdentifier", "InvestigationPatternType", "ConfidenceLevel", "PatternIdentificationResult",
    "DynamicPlanner", "ExecutionPlan", "LogicalTool", "PlanStep", "StepPriority",
    "ToolRouter", "ExecutionStage", "RoutedPlan", "RoutedStep", "StepStatus",
    "ContextMemoryManager", "SessionNotFoundError", "ContextMemory", "InvestigationSession",
    "ConversationState", "PlanningState", "ExecutionState",
    "ExecutionController", "ToolExecutor",
    "ExecutionStatus", "ExecutionLogEntry", "ExecutionResult",
]
