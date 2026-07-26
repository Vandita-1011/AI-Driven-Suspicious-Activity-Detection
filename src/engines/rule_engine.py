import time
from typing import List, Dict, Optional, Any

from src.features.feature_models import FeatureVector
from src.profiling.profile_models import BehaviourProfile
from src.engines.rule_models import RuleHit
from src.engines.rule_builder import RuleBuilder
from src.utils.logger import get_logger
from src.utils.timer import timed
from src.exceptions.engine_exceptions import EngineExecutionError

logger = get_logger(__name__)


class RuleEngine:
    """
    Orchestrates the evaluation of transactions against AML rules.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.builder = RuleBuilder(config)

    @timed("Rule Engine")
    def run(self, features: List[FeatureVector], profiles: Dict[str, BehaviourProfile]) -> List[RuleHit]:
        """
        Evaluates a list of transaction feature vectors against all AML rules.

        Args:
            features: List of transaction feature vectors.
            profiles: Dictionary of customer behaviour profiles.

        Returns:
            A flat list of all RuleHits generated across all transactions.
        """
        if not features:
            logger.warning("Empty feature list provided to Rule Engine.")
            return []

        start_time = time.time()
        logger.info("Rule Engine Started. Processing %d transactions...", len(features))

        all_hits: List[RuleHit] = []

        try:
            for fv in features:
                cust_profile = profiles.get(fv.customer_id)
                # Evaluate the transaction
                txn_hits = self.builder.evaluate(fv, cust_profile)
                
                # Log triggered rules
                for hit in txn_hits:
                    logger.debug("Rule Triggered: [%s] %s for Txn %s (Severity: %s)", 
                                 hit.rule_id, hit.rule_name, hit.transaction_id, hit.severity.value)
                
                all_hits.extend(txn_hits)
                
        except Exception as e:
            logger.error("Error during rule evaluation: %s", e)
            raise EngineExecutionError(f"Rule Engine failed: {e}")

        execution_time = time.time() - start_time
        
        logger.info("Rule Engine execution completed in %.2fs.", execution_time)
        logger.info("Total rule hits generated: %d", len(all_hits))
        
        return all_hits
