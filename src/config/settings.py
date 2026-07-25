"""
Configuration Settings
=======================
Loads and exposes the AI engine configuration from ``engine_config.yaml``.

Design:
  - One ``Settings`` object composed of domain-specific dataclass sections.
  - ``get_settings()`` returns a singleton — the file is read only once.
  - ``reset_settings()`` clears the cache (unit tests only).
  - ``load_settings()`` always re-reads the file (useful for hot-reload testing).

Usage:
    from src.config.settings import get_settings

    cfg = get_settings()
    threshold = cfg.rule_engine.structuring_threshold
    level      = cfg.logging.level
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

# Avoid circular import: logger not yet configured when settings module loads.
# We import it lazily inside functions that run after setup_logging().
import logging

_CONFIG_PATH = Path(__file__).parent / "engine_config.yaml"
_settings_instance: Optional["Settings"] = None


# ══════════════════════════════════════════════════════════════════════════════
# Section dataclasses  (one per top-level YAML key)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class DatasetConfig:
    """Paths to all 12 CSV tables."""
    path: str = "dataset"
    files: dict[str, str] = field(default_factory=lambda: {
        "transactions": "transaction.csv",
        "customers": "customer.csv",
        "accounts": "account.csv",
        "devices": "device.csv",
        "beneficiaries": "beneficiary.csv",
        "merchants": "merchant.csv",
        "locations": "location.csv",
        "branches": "branch.csv",
        "country_risk": "country_risk.csv",
        "customer_relationships": "customer_relationship.csv",
        "fraud_rings": "fraud_ring.csv",
        "fraud_ring_memberships": "customer_fraud_ring_membership.csv",
    })


@dataclass
class LoggingConfig:
    """Logging handler configuration."""
    level: str = "INFO"
    log_dir: str = "logs"
    log_file: str = "ai_engine.log"
    max_bytes: int = 10_485_760
    backup_count: int = 5
    console_enabled: bool = True
    file_enabled: bool = True
    format: str = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


@dataclass
class OutputsConfig:
    """Output file paths."""
    dir: str = "outputs"
    alerts_file: str = "alerts.json"
    risk_report_file: str = "risk_report.json"
    eda_report_file: str = "eda_report.json"


@dataclass
class ModelsConfig:
    """Trained model artifact paths."""
    dir: str = "models"
    isolation_forest_file: str = "isolation_forest.pkl"


@dataclass
class PreprocessingConfig:
    """Preprocessing parameters."""
    timestamp_format: str = "%Y-%m-%d %H:%M:%S"
    date_columns: list[str] = field(default_factory=lambda: ["timestamp"])
    bool_columns: list[str] = field(default_factory=lambda: [
        "is_pep", "sanctions_hit", "is_shared_device",
        "is_high_risk", "is_high_risk_branch", "is_symmetric",
    ])
    null_strategy: dict[str, str] = field(default_factory=lambda: {
        "numeric": "median",
        "categorical": "unknown",
    })


@dataclass
class FeaturesConfig:
    """Feature engineering parameters."""
    velocity_window_hours: int = 24
    burst_window_minutes: int = 60
    round_amount_tolerance: float = 0.01
    high_amount_multiplier: float = 3.0
    min_transactions_for_profile: int = 3


@dataclass
class RuleEngineConfig:
    """Rule engine thresholds.

    Note: ``structuring_threshold`` matches the generator's
    ``reporting_threshold: 1000000`` in generator/config.yaml.
    """
    structuring_threshold: float = 1_000_000.0
    structuring_window_days: int = 5
    structuring_sub_threshold_ratio: float = 0.98
    large_cash_threshold: float = 500_000.0
    high_risk_transfer_threshold: float = 100_000.0
    dormant_reactivation_lookback_days: int = 90
    velocity_max_txns_per_day: int = 10
    velocity_max_txns_per_hour: int = 5


@dataclass
class BehaviourEngineConfig:
    """Behaviour engine parameters."""
    deviation_z_score_threshold: float = 2.5
    min_history_transactions: int = 5


@dataclass
class StatisticalEngineConfig:
    """Statistical engine parameters."""
    z_score_threshold: float = 3.0
    iqr_multiplier: float = 1.5
    features_to_analyse: list[str] = field(default_factory=lambda: [
        "amount", "balance_after", "txn_count_24h",
    ])


@dataclass
class MLEngineConfig:
    """Isolation Forest hyperparameters."""
    n_estimators: int = 100
    contamination: float = 0.05
    random_state: int = 42
    max_samples: Any = "auto"
    n_jobs: int = -1


@dataclass
class AMLPatternEngineConfig:
    """AML pattern engine detection thresholds."""
    structuring_n_txns: int = 3
    smurfing_n_senders: int = 4
    layering_min_hops: int = 3
    circular_min_nodes: int = 3
    mule_passthrough_hours: int = 24
    mule_passthrough_ratio: float = 0.85
    dormant_lookback_days: int = 90
    velocity_max_per_day: int = 8
    burst_max_per_hour: int = 5
    round_amount_values: list[float] = field(default_factory=lambda: [
        10_000, 25_000, 50_000, 100_000, 200_000, 500_000,
    ])


@dataclass
class RiskFusionConfig:
    """Smart Risk Fusion weights and tier thresholds.

    ``weights`` must sum to 1.0.
    """
    weights: dict[str, float] = field(default_factory=lambda: {
        "rule_engine": 0.30,
        "behaviour_engine": 0.20,
        "statistical_engine": 0.15,
        "ml_engine": 0.20,
        "aml_pattern_engine": 0.15,
    })
    risk_thresholds: dict[str, int] = field(default_factory=lambda: {
        "critical": 90, "high": 75, "medium": 50, "low": 0,
    })


@dataclass
class AlertsConfig:
    """Alert prioritization configuration."""
    max_alerts: int = 1000
    priority_thresholds: dict[str, int] = field(default_factory=lambda: {
        "critical": 90, "high": 75, "medium": 50, "low": 0,
    })
    deduplication_window_hours: int = 24


# ══════════════════════════════════════════════════════════════════════════════
# Root Settings dataclass
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Settings:
    """Central configuration object for the AI engine.

    Composed of domain-specific section dataclasses, each mapping
    to a top-level key in ``engine_config.yaml``.

    Do not instantiate directly — use ``get_settings()``.
    """
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    outputs: OutputsConfig = field(default_factory=OutputsConfig)
    models: ModelsConfig = field(default_factory=ModelsConfig)
    preprocessing: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    features: FeaturesConfig = field(default_factory=FeaturesConfig)
    rule_engine: RuleEngineConfig = field(default_factory=RuleEngineConfig)
    behaviour_engine: BehaviourEngineConfig = field(default_factory=BehaviourEngineConfig)
    statistical_engine: StatisticalEngineConfig = field(default_factory=StatisticalEngineConfig)
    ml_engine: MLEngineConfig = field(default_factory=MLEngineConfig)
    aml_pattern_engine: AMLPatternEngineConfig = field(default_factory=AMLPatternEngineConfig)
    risk_fusion: RiskFusionConfig = field(default_factory=RiskFusionConfig)
    alerts: AlertsConfig = field(default_factory=AlertsConfig)

    def validate_fusion_weights(self) -> None:
        """Asserts that risk fusion weights sum to 1.0 (within floating-point tolerance).

        Raises:
            ValueError: If the weights do not sum to 1.0.
        """
        total = sum(self.risk_fusion.weights.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"risk_fusion.weights must sum to 1.0, got {total:.6f}. "
                f"Weights: {self.risk_fusion.weights}"
            )


# ══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ══════════════════════════════════════════════════════════════════════════════

def _populate_section(raw: dict, dataclass_type: type, key: str) -> Any:
    """Safely populates a dataclass from a YAML section, ignoring unknown keys.

    Args:
        raw:            Full parsed YAML dict.
        dataclass_type: Target dataclass type to instantiate.
        key:            Top-level YAML key for this section.

    Returns:
        Populated dataclass instance (defaults used for any missing fields).
    """
    section = raw.get(key, {}) or {}
    known = {f for f in dataclass_type.__dataclass_fields__}
    filtered = {k: v for k, v in section.items() if k in known}
    return dataclass_type(**filtered)


# ══════════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════════

def load_settings(config_path: Optional[Path] = None) -> Settings:
    """Reads ``engine_config.yaml`` and returns a populated ``Settings`` instance.

    Always re-reads the file. For the singleton version, use ``get_settings()``.

    Args:
        config_path: Optional override path.  Defaults to the bundled
                     ``engine_config.yaml`` in ``src/config/``.

    Returns:
        Fully populated ``Settings`` instance.

    Raises:
        ConfigurationError: If the YAML file is missing or malformed.
    """
    # Lazy import to avoid circular dependency at module load time
    from src.exceptions.engine_exceptions import ConfigurationError
    from src.utils.logger import setup_logging

    path = config_path or _CONFIG_PATH

    if not path.exists():
        raise ConfigurationError(
            message=f"Configuration file not found: {path}",
            key="config_path",
        )

    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw: dict = yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:
        raise ConfigurationError(
            message=f"Failed to parse engine_config.yaml: {exc}",
        ) from exc

    settings = Settings(
        dataset=_populate_section(raw, DatasetConfig, "dataset"),
        logging=_populate_section(raw, LoggingConfig, "logging"),
        outputs=_populate_section(raw, OutputsConfig, "outputs"),
        models=_populate_section(raw, ModelsConfig, "models"),
        preprocessing=_populate_section(raw, PreprocessingConfig, "preprocessing"),
        features=_populate_section(raw, FeaturesConfig, "features"),
        rule_engine=_populate_section(raw, RuleEngineConfig, "rule_engine"),
        behaviour_engine=_populate_section(raw, BehaviourEngineConfig, "behaviour_engine"),
        statistical_engine=_populate_section(raw, StatisticalEngineConfig, "statistical_engine"),
        ml_engine=_populate_section(raw, MLEngineConfig, "ml_engine"),
        aml_pattern_engine=_populate_section(raw, AMLPatternEngineConfig, "aml_pattern_engine"),
        risk_fusion=_populate_section(raw, RiskFusionConfig, "risk_fusion"),
        alerts=_populate_section(raw, AlertsConfig, "alerts"),
    )

    # Validate constraints
    settings.validate_fusion_weights()

    # Boot logging as early as possible
    setup_logging(
        log_dir=settings.logging.log_dir,
        log_file=settings.logging.log_file,
        level=settings.logging.level,
        log_format=settings.logging.format,
        date_format=settings.logging.date_format,
        max_bytes=settings.logging.max_bytes,
        backup_count=settings.logging.backup_count,
        console_enabled=settings.logging.console_enabled,
        file_enabled=settings.logging.file_enabled,
    )

    logging.getLogger(__name__).info("Settings loaded from: %s", path)
    return settings


def get_settings() -> Settings:
    """Returns the cached ``Settings`` singleton.

    Loads the configuration on first call; all subsequent calls return
    the same instance without re-reading the file.

    Returns:
        Singleton ``Settings`` instance.
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = load_settings()
    return _settings_instance


def reset_settings() -> None:
    """Clears the cached ``Settings`` singleton.

    After calling this, ``get_settings()`` will reload from disk.
    Use this ONLY in unit tests to ensure a clean state.
    """
    global _settings_instance
    _settings_instance = None
