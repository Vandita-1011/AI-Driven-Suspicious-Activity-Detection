"""
Base Explainer Interface
========================
Defines the contract for explanation generation.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class Explanation:
    """
    Evidence-based explanation for a transaction's risk score.
    """
    transaction_id: str
    risk_score: float
    narrative: str
    contributing_factors: list[dict[str, Any]] = field(default_factory=list)
    triggered_rules: list[str] = field(default_factory=list)
    matched_patterns: list[str] = field(default_factory=list)


class BaseExplainer(ABC):
    """
    Abstract base class for explainers.
    """

    @abstractmethod
    def explain(self, transaction_id: str, engine_results: dict[str, Any], features: pd.Series) -> Explanation:
        """
        Generates an explanation for a single transaction.

        Args:
            transaction_id: The ID of the transaction.
            engine_results: Combined results from all detection engines.
            features: The feature vector for this transaction.

        Returns:
            An Explanation object.
        """
        pass

    @abstractmethod
    def explain_batch(self, transaction_ids: list[str], engine_results: dict[str, Any], features_df: pd.DataFrame) -> list[Explanation]:
        """
        Generates explanations for a batch of transactions.
        """
        pass
