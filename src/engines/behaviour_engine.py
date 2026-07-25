import time
from typing import List, Dict, Optional, Any

from src.features.feature_models import FeatureVector
from src.profiling.profile_models import BehaviourProfile
from src.engines.behaviour_models import BehaviourFinding
from src.engines.behaviour_builder import BehaviourBuilder
from src.utils.logger import get_logger
from src.utils.timer import timed
from src.exceptions.engine_exceptions import EngineExecutionError

logger = get_logger(__name__)


class BehaviourEngine:
    """
    Orchestrates the evaluation of transactions against historical customer behaviour anomaly detectors.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.builder = BehaviourBuilder(config)

    @timed("Behaviour Engine")
    def run(self, features: List[FeatureVector], profiles: Dict[str, BehaviourProfile]) -> List[BehaviourFinding]:
        """
        Evaluates a list of transaction feature vectors against behavioural anomaly detectors.

        Args:
            features: List of transaction feature vectors.
            profiles: Dictionary of customer behaviour profiles.

        Returns:
            A flat list of all BehaviourFindings generated across all transactions.
        """
        if not features:
            logger.warning("Empty feature list provided to Behaviour Engine.")
            return []

        start_time = time.time()
        logger.info("Behaviour Engine Started. Processing %d transactions...", len(features))

        all_findings: List[BehaviourFinding] = []

        try:
            for fv in features:
                cust_profile = profiles.get(fv.customer_id)
                # Evaluate the transaction for behavioural anomalies
                txn_findings = self.builder.evaluate(fv, cust_profile)
                
                # Log triggered findings
                for finding in txn_findings:
                    logger.debug("Behaviour Finding: [%s] %s for Txn %s (Severity: %s)", 
                                 finding.finding_id, finding.finding_name, finding.transaction_id, finding.severity.value)
                
                all_findings.extend(txn_findings)
                
        except Exception as e:
            logger.error("Error during behavioural evaluation: %s", e)
            raise EngineExecutionError(f"Behaviour Engine failed: {e}")

        execution_time = time.time() - start_time
        
        logger.info("Behaviour Engine execution completed in %.2fs.", execution_time)
        logger.info("Total behaviour findings generated: %d", len(all_findings))
        
        return all_findings
