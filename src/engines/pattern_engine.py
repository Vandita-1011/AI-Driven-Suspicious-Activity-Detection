import time
from typing import List, Dict, Optional, Any

from src.features.feature_models import FeatureVector
from src.profiling.profile_models import BehaviourProfile
from src.engines.pattern_models import PatternFinding
from src.engines.pattern_builder import PatternBuilder
from src.utils.logger import get_logger
from src.utils.timer import timed
from src.exceptions.engine_exceptions import EngineExecutionError

logger = get_logger(__name__)


class PatternEngine:
    """
    Orchestrates the evaluation of transactions against known money laundering typologies.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.builder = PatternBuilder(config)

    @timed("Pattern Engine")
    def run(self, features: List[FeatureVector], profiles: Dict[str, BehaviourProfile]) -> List[PatternFinding]:
        """
        Evaluates a list of transaction feature vectors against AML pattern typologies.

        Args:
            features: List of transaction feature vectors.
            profiles: Dictionary of customer behaviour profiles.

        Returns:
            A flat list of all PatternFindings generated across all transactions.
        """
        if not features:
            logger.warning("Empty feature list provided to Pattern Engine.")
            return []

        start_time = time.time()
        logger.info("Pattern Engine Started. Processing %d transactions...", len(features))

        all_findings: List[PatternFinding] = []

        try:
            for fv in features:
                cust_profile = profiles.get(fv.customer_id)
                # Evaluate the transaction against AML typologies
                txn_findings = self.builder.evaluate(fv, cust_profile)
                
                # Log triggered findings
                for finding in txn_findings:
                    logger.debug("Pattern Finding: [%s] %s for Txn %s (Severity: %s)", 
                                 finding.pattern_id, finding.pattern_name, finding.transaction_id, finding.severity.value)
                
                all_findings.extend(txn_findings)
                
        except Exception as e:
            logger.error("Error during AML pattern evaluation: %s", e)
            raise EngineExecutionError(f"Pattern Engine failed: {e}")

        execution_time = time.time() - start_time
        
        logger.info("Pattern Engine execution completed in %.2fs.", execution_time)
        logger.info("Total AML patterns generated: %d", len(all_findings))
        
        return all_findings
