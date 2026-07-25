"""
ML Engine
=========
Unsupervised anomaly detection using Isolation Forest.
"""
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.interfaces.base_engine import BaseDetectionEngine, EngineResult
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.utils.timer import timed

logger = get_logger(__name__)


class MLEngine(BaseDetectionEngine):
    """
    Scores transactions using an Isolation Forest.
    """
    def __init__(self) -> None:
        self.settings = get_settings().ml_engine
        self.model = None

    def _build_pipeline(self) -> Pipeline:
        """Builds the sklearn pipeline."""
        return Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler()),
            ('iforest', IsolationForest(
                n_estimators=self.settings.n_estimators,
                contamination=self.settings.contamination,
                random_state=self.settings.random_state,
                n_jobs=self.settings.n_jobs
            ))
        ])

    @timed("ML Engine")
    def run(self, features_df: pd.DataFrame) -> EngineResult:
        """
        Fits (if necessary) and predicts anomaly scores.
        """
        logger.info("Running ML Engine...")
        
        result = EngineResult()
        if features_df.empty:
            return result
            
        # Select numeric features only
        numeric_df = features_df.select_dtypes(include=['number'])
        
        if numeric_df.empty:
            logger.warning("No numeric features available for ML Engine.")
            result.scores = pd.Series(0.0, index=features_df.index)
            return result

        if self.model is None:
            logger.info("Training Isolation Forest on the fly (hackathon mode)...")
            self.model = self._build_pipeline()
            self.model.fit(numeric_df)
            
        # Decision function returns > 0 for normal, < 0 for anomalies
        # We invert and scale it to [0, 100] where 100 is highly anomalous
        scores = self.model.decision_function(numeric_df)
        
        # Invert scores: lower (more negative) is more anomalous
        anomaly_scores = -scores
        
        # Min-max scale to [0, 100] approximately based on typical decision function bounds (-0.5 to 0.5)
        # Custom scaling for better distribution
        scaled_scores = pd.Series(anomaly_scores).clip(-0.2, 0.2)
        scaled_scores = ((scaled_scores + 0.2) / 0.4) * 100.0
        
        result.scores = pd.Series(scaled_scores.values, index=features_df.index)
        result.flags = pd.DataFrame(index=features_df.index)
        
        # Flag transactions in the top `contamination` percentile
        preds = self.model.predict(numeric_df) # -1 for anomaly, 1 for normal
        result.flags["ml_anomaly"] = (preds == -1)
        
        logger.info("ML Engine complete.")
        return result
