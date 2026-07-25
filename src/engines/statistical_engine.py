"""
Statistical Engine
==================
Detects anomalies using statistical methods (Z-score, IQR).
"""
import pandas as pd
import numpy as np
from scipy import stats

from src.interfaces.base_engine import BaseDetectionEngine, EngineResult
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.utils.timer import timed

logger = get_logger(__name__)


class StatisticalEngine(BaseDetectionEngine):
    """
    Applies Z-score and IQR-based anomaly detection.
    """
    def __init__(self) -> None:
        self.settings = get_settings().statistical_engine

    @timed("Statistical Engine")
    def run(self, features_df: pd.DataFrame) -> EngineResult:
        """
        Executes statistical anomaly checks.
        """
        logger.info("Running Statistical Engine...")
        
        result = EngineResult()
        if features_df.empty:
            return result
            
        result.scores = pd.Series(0.0, index=features_df.index)
        flags = pd.DataFrame(index=features_df.index)

        for col in self.settings.features_to_analyse:
            if col in features_df.columns:
                # Z-Score Anomaly
                # Note: nan_policy='omit' prevents propagation of NaNs
                z_scores = stats.zscore(features_df[col], nan_policy='omit')
                # Handle cases where all values are the same (z-score returns NaN)
                z_scores = np.nan_to_num(z_scores)
                
                flags[f"{col}_z_anomaly"] = np.abs(z_scores) > self.settings.z_score_threshold
                
                # Add to overall statistical score based on extreme z-scores
                result.scores += np.clip(np.abs(z_scores) * 10.0, 0, 30)

        # Cap scores at 100
        result.scores = result.scores.clip(upper=100.0)
        result.flags = flags
        
        logger.info("Statistical Engine complete.")
        return result
