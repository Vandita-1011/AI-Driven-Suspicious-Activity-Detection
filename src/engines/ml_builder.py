import os
import uuid
import numpy as np
import joblib
from typing import List, Optional, Dict, Any, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from src.features.feature_models import FeatureVector
from src.engines.ml_models import MLFinding
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MLBuilder:
    """
    Handles Isolation Forest model training, prediction, and feature extraction.
    """
    
    # Selected numerical features for anomaly detection
    NUMERICAL_FEATURES = [
        "amount_z_score",
        "amount_ratio_to_average",
        "transactions_last_hour",
        "transactions_last_day",
        "rolling_average_amount",
        "rolling_std_amount",
        "behaviour_deviation_score",
        "frequency_deviation_score",
        "time_since_previous_transaction",
        "beneficiary_frequency",
        "device_frequency",
        "channel_frequency",
        "country_frequency",
        "historical_average_amount",
        "historical_max_amount",
        "historical_min_amount"
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # ML Config
        self.contamination = self.config.get("ml_contamination", 0.01) # 1% expected anomalies
        self.random_state = self.config.get("ml_random_state", 42)
        self.n_estimators = self.config.get("ml_n_estimators", 100)
        self.max_samples = self.config.get("ml_max_samples", "auto")
        
        self.model_path = self.config.get("ml_model_path", "models/isolation_forest.joblib")
        self.scaler_path = self.config.get("ml_scaler_path", "models/scaler.joblib")
        
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        
        self.model_name = "IsolationForest_v1"

    def _extract_features(self, fv: FeatureVector) -> List[float]:
        """Extracts strictly numerical features, safely handling None/NaN values."""
        features = []
        for feature_name in self.NUMERICAL_FEATURES:
            val = getattr(fv, feature_name, 0.0)
            if val is None or np.isnan(val) or np.isinf(val):
                val = 0.0
            features.append(float(val))
        return features

    def train(self, features_list: List[FeatureVector]) -> None:
        """Trains the Isolation Forest model on historical feature vectors."""
        logger.info("Extracting features for ML training...")
        
        if not features_list:
            logger.warning("No features provided for ML training.")
            return
            
        X_raw = [self._extract_features(fv) for fv in features_list]
        X = np.array(X_raw)
        
        logger.info("Fitting StandardScaler...")
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Replace any remaining NaNs after scaling (rare, but possible if variance is 0)
        X_scaled = np.nan_to_num(X_scaled, nan=0.0, posinf=0.0, neginf=0.0)
        
        logger.info(f"Training {self.model_name} with contamination={self.contamination}, n_estimators={self.n_estimators}...")
        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            max_samples=self.max_samples,
            contamination=self.contamination,
            random_state=self.random_state
        )
        
        self.model.fit(X_scaled)
        logger.info("Model Trained successfully.")

    def save_model(self) -> None:
        """Saves the trained model and scaler to disk."""
        if self.model and self.scaler:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            os.makedirs(os.path.dirname(self.scaler_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            logger.info(f"Model and scaler saved to {self.model_path} and {self.scaler_path}.")
        else:
            logger.warning("Attempted to save model, but model or scaler is not trained.")

    def load_model(self) -> bool:
        """Loads the model and scaler from disk. Returns True if successful."""
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            try:
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                logger.info(f"Model Loaded from {self.model_path}.")
                return True
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                return False
        return False

    def predict(self, fv: FeatureVector) -> Optional[MLFinding]:
        """Predicts whether a single transaction is an anomaly."""
        if not self.model or not self.scaler:
            raise RuntimeError("Model is not initialized. Call train() or load_model() first.")
            
        x_raw = self._extract_features(fv)
        X = np.array([x_raw])
        X_scaled = self.scaler.transform(X)
        X_scaled = np.nan_to_num(X_scaled, nan=0.0, posinf=0.0, neginf=0.0)
        
        # -1 for anomaly, 1 for normal
        pred = self.model.predict(X_scaled)[0]
        # anomaly score is typically negative for anomalies, positive for normal
        # We invert it so higher score = more anomalous
        raw_score = self.model.decision_function(X_scaled)[0]
        anomaly_score = -float(raw_score) 
        
        is_anomaly = pred == -1
        prediction_str = "Anomaly" if is_anomaly else "Normal"
        
        # If it's not an anomaly, we don't necessarily need to return a finding, 
        # but the prompt requires returning findings based on prediction.
        if not is_anomaly:
            return None
            
        # Confidence calculation (heuristic based on Isolation Forest score distribution)
        # Assuming anomaly_score ranges roughly between -0.2 to 0.3 depending on contamination.
        # We'll normalize it to 0-1.
        confidence = float(min(1.0, max(0.0, 0.5 + (anomaly_score * 2.0))))
        
        explanation = (
            f"Isolation Forest assigned an anomaly score of {anomaly_score:.3f}, "
            f"indicating this transaction significantly differs from normal customer behaviour."
        )
        
        finding_id = f"ML-{uuid.uuid4().hex[:8].upper()}"
        
        return MLFinding(
            finding_id=finding_id,
            model_name=self.model_name,
            prediction=prediction_str,
            anomaly_score=anomaly_score,
            confidence=round(confidence, 2),
            customer_id=fv.customer_id,
            transaction_id=fv.transaction_id,
            explanation=explanation,
            timestamp=fv.timestamp
        )
