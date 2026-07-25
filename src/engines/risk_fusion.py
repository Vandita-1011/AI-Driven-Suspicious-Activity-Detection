"""
Smart Risk Fusion
=================
Combines scores from all five detection engines into a single fused risk score.
"""
from typing import Any

import pandas as pd
import numpy as np

from src.interfaces.base_engine import EngineResult
from src.constants.risk_levels import RiskLevel
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.utils.timer import timed

logger = get_logger(__name__)


class SmartRiskFusion:
    """
    Fuses multiple engine scores into a unified 0-100 risk score and categorises it.
    """
    def __init__(self) -> None:
        self.settings = get_settings().risk_fusion

    @timed("Risk Fusion")
    def fuse(self, engine_results: dict[str, EngineResult]) -> pd.DataFrame:
        """
        Calculates the weighted average score from all engines.

        Args:
            engine_results: Dict mapping engine name to its EngineResult.

        Returns:
            A DataFrame with fused scores and risk levels, indexed by transaction_id.
        """
        logger.info("Fusing risk scores...")
        
        # Get index from the first available non-empty result
        idx = None
        for res in engine_results.values():
            if not res.scores.empty:
                idx = res.scores.index
                break
                
        if idx is None:
            return pd.DataFrame()

        fused_scores = pd.Series(0.0, index=idx)
        
        # Apply weighted sum
        weights = self.settings.weights
        for engine_name, weight in weights.items():
            if engine_name in engine_results:
                scores = engine_results[engine_name].scores
                # Align on index and fill missing with 0
                scores = scores.reindex(idx).fillna(0.0)
                fused_scores += scores * weight

        # Cap at 100
        fused_scores = fused_scores.clip(upper=100.0)

        # Categorise into RiskLevel
        def assign_level(score: float) -> str:
            return RiskLevel.from_score(score, self.settings.risk_thresholds).value

        result_df = pd.DataFrame({
            "fused_risk_score": fused_scores,
            "risk_level": fused_scores.apply(assign_level)
        }, index=idx)

        logger.info("Risk fusion complete.")
        return result_df
