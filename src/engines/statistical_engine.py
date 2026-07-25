import time
from typing import List, Dict, Optional, Any

from src.features.feature_models import FeatureVector
from src.profiling.profile_models import BehaviourProfile
from src.engines.statistical_models import StatisticalFinding
from src.engines.statistical_builder import StatisticalBuilder
from src.utils.logger import get_logger
from src.utils.timer import timed
from src.exceptions.engine_exceptions import EngineExecutionError

logger = get_logger(__name__)


class StatisticalEngine:
    """
    Orchestrates the evaluation of transactions against statistical anomaly detectors.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.builder = StatisticalBuilder(config)

    @timed("Statistical Engine")
    def run(self, features: List[FeatureVector], profiles: Dict[str, BehaviourProfile]) -> List[StatisticalFinding]:
        """
        Evaluates a list of transaction feature vectors against all statistical anomaly detectors.

        Args:
            features: List of transaction feature vectors.
            profiles: Dictionary of customer behaviour profiles.

        Returns:
            A flat list of all StatisticalFindings generated across all transactions.
        """
        if not features:
            logger.warning("Empty feature list provided to Statistical Engine.")
            return []

        start_time = time.time()
        logger.info("Statistical Engine Started. Processing %d transactions...", len(features))

        all_findings: List[StatisticalFinding] = []

        try:
            for fv in features:
                cust_profile = profiles.get(fv.customer_id)
                # Evaluate the transaction for statistical anomalies
                txn_findings = self.builder.evaluate(fv, cust_profile)
                
                # Log triggered findings
                for finding in txn_findings:
                    logger.debug("Statistical Finding: [%s] %s for Txn %s (Severity: %s)", 
                                 finding.finding_id, finding.finding_name, finding.transaction_id, finding.severity.value)
                
                all_findings.extend(txn_findings)
                
        except Exception as e:
            logger.error("Error during statistical evaluation: %s", e)
            raise EngineExecutionError(f"Statistical Engine failed: {e}")

        execution_time = time.time() - start_time
        
        logger.info("Statistical Engine execution completed in %.2fs.", execution_time)
        logger.info("Total statistical findings generated: %d", len(all_findings))
        
        return all_findings
