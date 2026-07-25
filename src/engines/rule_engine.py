"""
Rule Engine
===========
Applies hard business rules and thresholds to flag suspicious activity.
"""
import pandas as pd

from src.constants.column_names import ComputedCols, TxnCols
from src.interfaces.base_engine import BaseDetectionEngine, EngineResult
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.utils.timer import timed

logger = get_logger(__name__)


class RuleEngine(BaseDetectionEngine):
    """
    Evaluates hard rules (e.g., structuring thresholds, high-risk geography).
    """
    def __init__(self) -> None:
        self.settings = get_settings().rule_engine

    @timed("Rule Engine")
    def run(self, features_df: pd.DataFrame) -> EngineResult:
        """
        Executes rule-based checks.
        """
        logger.info("Running Rule Engine...")
        
        result = EngineResult()
        if features_df.empty:
            return result
            
        result.scores = pd.Series(0.0, index=features_df.index)
        flags = pd.DataFrame(index=features_df.index)
        
        # Example Rule: Large Cash Transaction
        if TxnCols.AMOUNT in features_df.columns:
            flags["large_cash"] = features_df[TxnCols.AMOUNT] >= self.settings.large_cash_threshold
            # Boost score for flagged items
            result.scores += flags["large_cash"].astype(float) * 20.0
            
        # Example Rule: High Risk Counterparty Country (FATF Black/Grey)
        if ComputedCols.FATF_STATUS in features_df.columns:
            flags["high_risk_country"] = features_df[ComputedCols.FATF_STATUS].isin(["Black", "Grey"])
            result.scores += flags["high_risk_country"].astype(float) * 30.0

        # Cap scores at 100
        result.scores = result.scores.clip(upper=100.0)
        result.flags = flags
        
        logger.info("Rule Engine complete.")
        return result
