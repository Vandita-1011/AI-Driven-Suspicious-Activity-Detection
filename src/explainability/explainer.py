"""
Explainer
=========
Generates plain-English evidence-based explanations for a transaction's risk score.
Does not use SHAP or LIME; relies purely on triggered rules, patterns, and anomalies.
"""
from typing import Any

import pandas as pd

from src.interfaces.base_explainer import BaseExplainer, Explanation
from src.utils.logger import get_logger
from src.utils.timer import timed

logger = get_logger(__name__)


class Explainer(BaseExplainer):
    """
    Evidence-based explanation generator.
    """
    def explain(self, transaction_id: str, engine_results: dict[str, Any], features: pd.Series) -> Explanation:
        """
        Creates a single explanation.
        """
        # For the hackathon foundation, we provide a basic structural implementation.
        explanation = Explanation(
            transaction_id=transaction_id,
            risk_score=0.0,
            narrative="Transaction analyzed successfully. Risk score is pending fusion.",
        )
        return explanation

    @timed("Explainer Batch")
    def explain_batch(self, transaction_ids: list[str], engine_results: dict[str, Any], features_df: pd.DataFrame) -> list[Explanation]:
        """
        Creates explanations for a list of transactions.
        """
        logger.info("Generating explanations for %d transactions...", len(transaction_ids))
        explanations = []
        for tid in transaction_ids:
            # We pass empty series/dict for foundation. Implementation will lookup by ID.
            explanations.append(self.explain(tid, {}, pd.Series(dtype=float)))
        return explanations
