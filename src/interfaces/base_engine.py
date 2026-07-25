"""
Base Engine Interface
=====================
Defines the contract for all detection engines.

All engines (Rule, Behaviour, Statistical, ML, AMLPattern) must inherit
from `BaseDetectionEngine` and implement the `run` method.

The `EngineResult` dataclass standardizes the output of every engine,
ensuring the Smart Risk Fusion stage can consume them uniformly.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class EngineResult:
    """
    Standardized output from any detection engine.

    Attributes:
        scores: A pandas Series containing numeric risk/anomaly scores,
                indexed by transaction_id.
        flags: A pandas DataFrame containing boolean flags or categorical
               findings (e.g., matched pattern names, triggered rules),
               indexed by transaction_id.
        metadata: Engine-specific metadata for debugging or explainability
                  (e.g., model version, thresholds used).
    """
    scores: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    flags: pd.DataFrame = field(default_factory=lambda: pd.DataFrame())
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseDetectionEngine(ABC):
    """
    Abstract base class for all detection engines.
    """

    @abstractmethod
    def run(self, features_df: pd.DataFrame) -> EngineResult:
        """
        Executes the detection logic on the provided feature matrix.

        Args:
            features_df: A pandas DataFrame containing all necessary features
                         for the transactions being analyzed. The index should
                         be the transaction_id.

        Returns:
            An EngineResult containing scores, flags, and metadata.
        """
        pass
