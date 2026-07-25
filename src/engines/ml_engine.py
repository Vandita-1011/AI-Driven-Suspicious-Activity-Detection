import time
from typing import List, Dict, Optional, Any

from src.features.feature_models import FeatureVector
from src.engines.ml_models import MLFinding
from src.engines.ml_builder import MLBuilder
from src.utils.logger import get_logger
from src.utils.timer import timed
from src.exceptions.engine_exceptions import EngineExecutionError

logger = get_logger(__name__)


class MLEngine:
    """
    Orchestrates the evaluation of transactions against unsupervised Machine Learning models.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.builder = MLBuilder(config)
        self.is_initialized = False

    def _initialize_model(self, features: List[FeatureVector]) -> None:
        """Loads existing model or trains a new one if not found."""
        if self.builder.load_model():
            self.is_initialized = True
        else:
            logger.info("No pre-trained ML model found. Initiating automatic training...")
            if not features:
                raise EngineExecutionError("Cannot train ML model: No historical feature vectors provided.")
            
            self.builder.train(features)
            self.builder.save_model()
            self.is_initialized = True

    @timed("ML Engine")
    def run(self, features: List[FeatureVector]) -> List[MLFinding]:
        """
        Evaluates a list of transaction feature vectors using Machine Learning anomaly detection.

        Args:
            features: List of transaction feature vectors.

        Returns:
            A flat list of MLFindings for transactions predicted as anomalies.
        """
        if not features:
            logger.warning("Empty feature list provided to ML Engine.")
            return []

        start_time = time.time()
        logger.info("ML Engine Started. Processing %d transactions...", len(features))

        try:
            if not self.is_initialized:
                self._initialize_model(features)
                
            logger.info("Prediction Started.")
            
            all_findings: List[MLFinding] = []
            
            for fv in features:
                finding = self.builder.predict(fv)
                if finding:
                    all_findings.append(finding)
                    
            logger.info("Prediction Completed.")
                
        except Exception as e:
            logger.error("Error during ML evaluation: %s", e)
            raise EngineExecutionError(f"ML Engine failed: {e}")

        execution_time = time.time() - start_time
        
        logger.info("Execution Time: %.2fs.", execution_time)
        logger.info("Number of Anomalies: %d", len(all_findings))
        
        return all_findings
