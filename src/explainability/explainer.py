"""
Explainer
=========
Generates plain-English evidence-based explanations for a transaction's risk score.
Does not use SHAP or LIME; relies purely on triggered rules, patterns, and anomalies.
"""
from typing import List
from collections import defaultdict

from src.interfaces.base_explainer import BaseExplainer, Explanation
from src.fusion.risk_models import RiskAssessment
from src.engines.rule_models import RuleHit
from src.engines.behaviour_models import BehaviourFinding
from src.engines.statistical_models import StatisticalFinding
from src.engines.ml_models import MLFinding
from src.engines.pattern_models import PatternFinding
from src.utils.logger import get_logger
from src.utils.timer import timed

logger = get_logger(__name__)


class Explainer(BaseExplainer):
    """
    Evidence-based explanation generator.
    """
    def explain(
        self,
        risk_assessment: RiskAssessment,
        rule_hits: List[RuleHit],
        behaviour_findings: List[BehaviourFinding],
        stat_findings: List[StatisticalFinding],
        ml_findings: List[MLFinding],
        pattern_findings: List[PatternFinding]
    ) -> Explanation:
        """
        Creates a single explanation based on existing fused risk results.
        """
        tid = risk_assessment.transaction_id
        score = risk_assessment.overall_risk_score
        risk_level = risk_assessment.risk_level.value
        confidence = risk_assessment.confidence_score

        # 1. Overall Risk Summary
        summary = f"This transaction has been classified as {risk_level} RISK with an overall confidence of {confidence:.2f}."

        # 2. Why the score is high (engines that contributed)
        contributions = []
        if rule_hits:
            contributions.append("- Rule Engine detected rule violations.")
        if behaviour_findings:
            contributions.append("- Behaviour Engine detected deviation from historical profile.")
        if stat_findings:
            contributions.append("- Statistical Engine detected statistical anomalies.")
        if ml_findings:
            contributions.append("- ML Engine predicted fraud probability.")
        if pattern_findings:
            contributions.append("- Pattern Engine detected known laundering patterns.")

        why_str = "Contributing factors:\n" + "\n".join(contributions) if contributions else "No significant contributing engines found."

        # 3. Triggered Indicators
        indicators = []
        triggered_rules_names = []
        matched_patterns_names = []

        for r in rule_hits:
            indicators.append(r.rule_name)
            triggered_rules_names.append(r.rule_name)
        for b in behaviour_findings:
            indicators.append(b.finding_name)
        for s in stat_findings:
            indicators.append(s.finding_name)
        for m in ml_findings:
            indicators.append(f"ML Anomaly: {m.model_name}")
        for p in pattern_findings:
            indicators.append(p.pattern_name)
            matched_patterns_names.append(p.pattern_name)

        # Deduplicate indicators preserving order
        seen = set()
        dedup_indicators = []
        for ind in indicators:
            if ind not in seen:
                seen.add(ind)
                dedup_indicators.append(ind)

        indicators_str = "Triggered Indicators:\n- " + "\n- ".join(dedup_indicators) if dedup_indicators else "No specific indicators."

        # 4. Confidence Explanation
        num_engines = sum([len(rule_hits) > 0, len(behaviour_findings) > 0, len(stat_findings) > 0, len(ml_findings) > 0, len(pattern_findings) > 0])

        if num_engines >= 3:
            conf_str = f"High confidence because {num_engines} independent engines produced consistent suspicious indicators."
        elif num_engines == 2:
            conf_str = f"Moderate confidence based on signals from 2 independent engines."
        elif num_engines == 1:
            conf_str = f"Lower confidence as indicators were detected by only 1 engine."
        else:
            conf_str = f"Low confidence with no primary detection engines triggering."

        narrative = f"{summary}\n\n{why_str}\n\n{indicators_str}\n\n{conf_str}"

        # Contributing factors for structured output
        factors = []
        factors.extend([{"type": "rule", "name": r.rule_name, "score": r.score} for r in rule_hits])
        factors.extend([{"type": "behaviour", "name": b.finding_name, "score": b.score} for b in behaviour_findings])
        factors.extend([{"type": "statistical", "name": s.finding_name, "score": s.score} for s in stat_findings])
        factors.extend([{"type": "ml", "name": m.model_name, "score": m.anomaly_score} for m in ml_findings])
        factors.extend([{"type": "pattern", "name": p.pattern_name, "score": p.confidence} for p in pattern_findings])

        return Explanation(
            transaction_id=tid,
            risk_score=score,
            narrative=narrative,
            contributing_factors=factors,
            triggered_rules=triggered_rules_names,
            matched_patterns=matched_patterns_names
        )

    @timed("Explainer Batch")
    def explain_batch(
        self,
        risk_assessments: List[RiskAssessment],
        rule_hits: List[RuleHit],
        behaviour_findings: List[BehaviourFinding],
        stat_findings: List[StatisticalFinding],
        ml_findings: List[MLFinding],
        pattern_findings: List[PatternFinding]
    ) -> List[Explanation]:
        """
        Creates explanations for a list of transactions based on provided results and features.
        """
        logger.info("Generating explanations for %d transactions...", len(risk_assessments))

        # Group findings by transaction_id
        rules_by_tx = defaultdict(list)
        for r in rule_hits:
            if r.triggered:
                rules_by_tx[r.transaction_id].append(r)

        behav_by_tx = defaultdict(list)
        for b in behaviour_findings:
            if b.triggered:
                behav_by_tx[b.transaction_id].append(b)

        stat_by_tx = defaultdict(list)
        for s in stat_findings:
            if s.triggered:
                stat_by_tx[s.transaction_id].append(s)

        ml_by_tx = defaultdict(list)
        for m in ml_findings:
            if m.prediction == 'Anomaly':
                ml_by_tx[m.transaction_id].append(m)

        pattern_by_tx = defaultdict(list)
        for p in pattern_findings:
            pattern_by_tx[p.transaction_id].append(p)

        explanations = []
        for risk in risk_assessments:
            tid = risk.transaction_id
            explanation = self.explain(
                risk_assessment=risk,
                rule_hits=rules_by_tx.get(tid, []),
                behaviour_findings=behav_by_tx.get(tid, []),
                stat_findings=stat_by_tx.get(tid, []),
                ml_findings=ml_by_tx.get(tid, []),
                pattern_findings=pattern_by_tx.get(tid, [])
            )
            explanations.append(explanation)

        return explanations
