"""
Custom Exception Hierarchy
===========================
All custom exceptions for the AI engine.

Design rules:
  - Every exception extends ``AMLEngineError`` (the base).
  - Each exception carries a ``module`` field for easy log filtering.
  - Exceptions are domain-specific, not generic Python exceptions.
  - Use these instead of ValueError / RuntimeError / IOError.

Catching all engine errors:
    try:
        orchestrator.run()
    except AMLEngineError as e:
        logger.error("Engine failed in %s: %s", e.module, e.message)
"""


class AMLEngineError(Exception):
    """
    Base exception for all AI engine errors.

    Every custom exception in this project extends this class,
    making it possible to catch any engine error with a single handler.

    Attributes:
        message: Human-readable description of the error.
        module: Name of the module where the error originated.
    """

    def __init__(self, message: str, module: str = "AMLEngine") -> None:
        self.module = module
        self.message = message
        super().__init__(f"[{module}] {message}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(module={self.module!r}, message={self.message!r})"


# ──────────────────────────────────────────────────────────────────────────────
# Data Layer Exceptions
# ──────────────────────────────────────────────────────────────────────────────

class DataLoadError(AMLEngineError):
    """Raised when the DatasetLoader fails to read one or more CSV files.

    Attributes:
        file_path: Path of the file that caused the error.
    """

    def __init__(self, message: str, file_path: str = "") -> None:
        self.file_path = file_path
        detail = f" (file: {file_path})" if file_path else ""
        super().__init__(message + detail, module="DataLoader")


class SchemaValidationError(AMLEngineError):
    """Raised when a DataFrame does not match the expected schema.

    Examples:
        - A required column is missing from a CSV.
        - A primary key column contains duplicate values.
        - A foreign key reference is broken.

    Attributes:
        table_name: Name of the table that failed validation.
        missing_cols: List of missing column names (if applicable).
    """

    def __init__(
        self,
        message: str,
        table_name: str = "",
        missing_cols: list[str] | None = None,
    ) -> None:
        self.table_name = table_name
        self.missing_cols: list[str] = missing_cols or []
        detail = f" Missing columns: {self.missing_cols}" if self.missing_cols else ""
        super().__init__(message + detail, module=f"Schema:{table_name}" if table_name else "Schema")


# ──────────────────────────────────────────────────────────────────────────────
# Preprocessing Exceptions
# ──────────────────────────────────────────────────────────────────────────────

class PreprocessingError(AMLEngineError):
    """Raised when the preprocessing pipeline encounters an unrecoverable error.

    Attributes:
        stage: Which preprocessing stage failed (e.g. "cleaning", "enrichment").
    """

    def __init__(self, message: str, stage: str = "") -> None:
        self.stage = stage
        super().__init__(
            message,
            module=f"Preprocessing:{stage}" if stage else "Preprocessing",
        )


# ──────────────────────────────────────────────────────────────────────────────
# Feature Engineering Exceptions
# ──────────────────────────────────────────────────────────────────────────────

class FeatureEngineeringError(AMLEngineError):
    """Raised when feature extraction or the feature pipeline fails.

    Attributes:
        feature_set: Which extractor failed (e.g. "transaction", "network").
    """

    def __init__(self, message: str, feature_set: str = "") -> None:
        self.feature_set = feature_set
        super().__init__(
            message,
            module=f"Features:{feature_set}" if feature_set else "Features",
        )


# ──────────────────────────────────────────────────────────────────────────────
# Detection Engine Exceptions
# ──────────────────────────────────────────────────────────────────────────────

class EngineExecutionError(AMLEngineError):
    """Base class for all detection engine runtime errors.

    Attributes:
        engine_name: Name of the engine that raised the error.
    """

    def __init__(self, message: str, engine_name: str = "DetectionEngine") -> None:
        self.engine_name = engine_name
        super().__init__(message, module=engine_name)


class RuleEngineError(EngineExecutionError):
    """Raised when the Rule Engine encounters an error."""

    def __init__(self, message: str) -> None:
        super().__init__(message, engine_name="RuleEngine")


class BehaviourEngineError(EngineExecutionError):
    """Raised when the Behaviour Engine encounters an error."""

    def __init__(self, message: str) -> None:
        super().__init__(message, engine_name="BehaviourEngine")


class StatisticalEngineError(EngineExecutionError):
    """Raised when the Statistical Engine encounters an error."""

    def __init__(self, message: str) -> None:
        super().__init__(message, engine_name="StatisticalEngine")


class MLEngineError(EngineExecutionError):
    """Raised when the ML Engine fails during training or inference."""

    def __init__(self, message: str) -> None:
        super().__init__(message, engine_name="MLEngine")


class PatternEngineError(EngineExecutionError):
    """Raised when the AML Pattern Engine encounters an error."""

    def __init__(self, message: str) -> None:
        super().__init__(message, engine_name="AMLPatternEngine")


# ──────────────────────────────────────────────────────────────────────────────
# Post-Engine Exceptions
# ──────────────────────────────────────────────────────────────────────────────

class RiskFusionError(AMLEngineError):
    """Raised when the Smart Risk Fusion stage fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, module="RiskFusion")


class ExplainerError(AMLEngineError):
    """Raised when explanation generation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, module="Explainer")


class RecommenderError(AMLEngineError):
    """Raised when the Recommender module fails to generate an action."""

    def __init__(self, message: str) -> None:
        super().__init__(message, module="Recommender")


class AlertPrioritizationError(AMLEngineError):
    """Raised when the AlertPrioritizer encounters an error."""

    def __init__(self, message: str) -> None:
        super().__init__(message, module="AlertPrioritizer")


class OrchestratorError(AMLEngineError):
    """Raised when the Orchestrator fails to coordinate the pipeline.

    Attributes:
        stage: Pipeline stage name where the failure occurred.
    """

    def __init__(self, message: str, stage: str = "") -> None:
        self.stage = stage
        super().__init__(
            message,
            module=f"Orchestrator:{stage}" if stage else "Orchestrator",
        )


class ConfigurationError(AMLEngineError):
    """Raised when the configuration file is missing, malformed, or has invalid values.

    Attributes:
        key: The offending configuration key, if known.
    """

    def __init__(self, message: str, key: str = "") -> None:
        self.key = key
        detail = f" (config key: '{key}')" if key else ""
        super().__init__(message + detail, module="Configuration")
