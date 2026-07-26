import time
from typing import List, Dict, Optional, Any
from collections import defaultdict

from src.engines.rule_models import RuleHit
from src.engines.behaviour_models import BehaviourFinding
from src.engines.statistical_models import StatisticalFinding
from src.engines.ml_models import MLFinding
from src.engines.pattern_models import PatternFinding
from src.fusion.risk_models import RiskAssessment
from src.fusion.risk_builder import RiskBuilder
from src.utils.logger import get_logger
from src.utils.timer import timed
from src.exceptions.engine_exceptions import EngineExecutionError

logger = get_logger(__name__)


class RiskEngine:
    """
    Orchestrates the fusion of all detection engine findings into unified risk assessments.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.builder = RiskBuilder(config)

    @timed("Risk Fusion Engine")
    def run(
        self,
        rule_hits: List[RuleHit],
        behaviour_findings: List[BehaviourFinding],
        stat_findings: List[StatisticalFinding],
        ml_findings: List[MLFinding],
        pattern_findings: List[PatternFinding]
    ) -> List[RiskAssessment]:
        """
        Consumes outputs from all five detection engines and fuses them into unified RiskAssessments.

        Args:
            rule_hits: List of all RuleHits generated.
            behaviour_findings: List of all BehaviourFindings generated.
            stat_findings: List of all StatisticalFindings generated.
            ml_findings: List of all MLFindings generated.
            pattern_findings: List of all PatternFindings generated.

        Returns:
            A list of RiskAssessment objects, one per unique transaction.
        """
        start_time = time.time()
        logger.info("Smart Risk Fusion Engine Started.")

        assessments: List[RiskAssessment] = []

        try:
            # Group all findings by transaction ID
            grouped_rules = defaultdict(list)
            for h in rule_hits:
                grouped_rules[h.transaction_id].append(h)
                
            grouped_behaviours = defaultdict(list)
            for f in behaviour_findings:
                grouped_behaviours[f.transaction_id].append(f)
                
            grouped_stats = defaultdict(list)
            for f in stat_findings:
                grouped_stats[f.transaction_id].append(f)
                
            grouped_ml = defaultdict(list)
            for f in ml_findings:
                grouped_ml[f.transaction_id].append(f)
                
            grouped_patterns = defaultdict(list)
            for f in pattern_findings:
                grouped_patterns[f.transaction_id].append(f)
                
            # Collect all unique transaction IDs that have AT LEAST ONE finding
            all_txn_ids = set()
            all_txn_ids.update(grouped_rules.keys())
            all_txn_ids.update(grouped_behaviours.keys())
            all_txn_ids.update(grouped_stats.keys())
            all_txn_ids.update(grouped_ml.keys())
            all_txn_ids.update(grouped_patterns.keys())
            
            logger.info("Fusing findings for %d unique anomalous transactions...", len(all_txn_ids))
            
            for txn_id in all_txn_ids:
                # We need customer_id. We can extract it from any finding that exists for this txn.
                customer_id = "UNKNOWN"
                if grouped_rules[txn_id]: customer_id = grouped_rules[txn_id][0].customer_id
                elif grouped_behaviours[txn_id]: customer_id = grouped_behaviours[txn_id][0].customer_id
                elif grouped_stats[txn_id]: customer_id = grouped_stats[txn_id][0].customer_id
                elif grouped_ml[txn_id]: customer_id = grouped_ml[txn_id][0].customer_id
                elif grouped_patterns[txn_id]: customer_id = grouped_patterns[txn_id][0].customer_id
                
                assessment = self.builder.fuse(
                    transaction_id=txn_id,
                    customer_id=customer_id,
                    rule_hits=grouped_rules[txn_id],
                    behaviour_findings=grouped_behaviours[txn_id],
                    stat_findings=grouped_stats[txn_id],
                    ml_findings=grouped_ml[txn_id],
                    pattern_findings=grouped_patterns[txn_id]
                )
                
                logger.debug("Risk Assessment Generated: Txn %s | Score: %.2f | Level: %s", 
                             txn_id, assessment.overall_risk_score, assessment.risk_level.value)
                
                assessments.append(assessment)
                
        except Exception as e:
            logger.error("Error during risk fusion: %s", e)
            raise EngineExecutionError(f"Risk Fusion Engine failed: {e}")

        execution_time = time.time() - start_time
        
        logger.info("Smart Risk Fusion Engine execution completed in %.2fs.", execution_time)
        logger.info("Total Risk Assessments generated: %d", len(assessments))
        
        return assessments
