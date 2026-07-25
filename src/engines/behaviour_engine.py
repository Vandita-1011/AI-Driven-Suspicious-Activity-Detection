"""
Behaviour Engine
================
Detects anomalies by comparing transactions against customer behaviour baselines.
"""
import pandas as pd
import numpy as np

from src.constants.column_names import TxnCols
from src.interfaces.base_engine import BaseDetectionEngine, EngineResult
from src.interfaces.base_profiler import BaseBehaviourProfiler
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.utils.timer import timed

logger = get_logger(__name__)


class BehaviourEngine(BaseDetectionEngine):
    """
    Detects deviations from established behaviour profiles.
    """
    def __init__(self, profiler: BaseBehaviourProfiler) -> None:
        self.profiler = profiler
        self.settings = get_settings().behaviour_engine

    @timed("Behaviour Engine")
    def run(self, features_df: pd.DataFrame) -> EngineResult:
        """
        Executes behaviour deviation checks.
        """
        logger.info("Running Behaviour Engine...")
        
        result = EngineResult()
        if features_df.empty:
            return result
            
        result.scores = pd.Series(0.0, index=features_df.index)
        flags = pd.DataFrame(index=features_df.index)
        
        if TxnCols.CUSTOMER_ID in features_df.columns and TxnCols.AMOUNT in features_df.columns:
            # Example: Amount deviation from baseline
            def check_amount_deviation(row):
                cust_id = str(row[TxnCols.CUSTOMER_ID])
                profile = self.profiler.get_profile(cust_id)
                if profile and "avg_amount" in profile.features:
                    avg_amt = profile.features["avg_amount"]
                    if avg_amt > 0:
                        ratio = row[TxnCols.AMOUNT] / avg_amt
                        if ratio > self.settings.deviation_z_score_threshold:
                            return True, min(100.0, ratio * 10.0)
                return False, 0.0

            deviation_results = features_df.apply(check_amount_deviation, axis=1)
            flags["amount_deviation"] = deviation_results.apply(lambda x: x[0])
            result.scores = deviation_results.apply(lambda x: x[1])

        result.flags = flags
        logger.info("Behaviour Engine complete.")
        return result
