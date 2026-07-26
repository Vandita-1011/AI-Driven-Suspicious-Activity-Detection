"""
Exceptions Package
==================
Custom exception hierarchy for the AI engine.

All exceptions extend AMLEngineError, making it possible to catch
any engine error with a single `except AMLEngineError` block.

Public hierarchy:
    AMLEngineError
    ├── DataLoadError
    ├── SchemaValidationError
    ├── PreprocessingError
    ├── FeatureEngineeringError
    ├── EngineExecutionError
    │   ├── RuleEngineError
    │   ├── BehaviourEngineError
    │   ├── StatisticalEngineError
    │   ├── MLEngineError
    │   └── PatternEngineError
    ├── RiskFusionError
    ├── ExplainerError
    ├── RecommenderError
    ├── AlertPrioritizationError
    ├── OrchestratorError
    └── ConfigurationError
"""
from src.exceptions.engine_exceptions import (
    AMLEngineError,
    DataLoadError,
    SchemaValidationError,
    PreprocessingError,
    FeatureEngineeringError,
    EngineExecutionError,
    RuleEngineError,
    BehaviourEngineError,
    StatisticalEngineError,
    MLEngineError,
    PatternEngineError,
    RiskFusionError,
    ExplainerError,
    RecommenderError,
    AlertPrioritizationError,
    OrchestratorError,
    ConfigurationError,
)

__all__ = [
    "AMLEngineError", "DataLoadError", "SchemaValidationError",
    "PreprocessingError", "FeatureEngineeringError", "EngineExecutionError",
    "RuleEngineError", "BehaviourEngineError", "StatisticalEngineError",
    "MLEngineError", "PatternEngineError", "RiskFusionError", "ExplainerError",
    "RecommenderError", "AlertPrioritizationError", "OrchestratorError",
    "ConfigurationError",
]
