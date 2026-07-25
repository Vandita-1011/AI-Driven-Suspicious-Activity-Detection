from typing import List, Dict, Any, Optional
from collections import defaultdict

from src.engines.rule_models import RuleHit
from src.engines.behaviour_models import BehaviourFinding
from src.engines.statistical_models import StatisticalFinding
from src.engines.ml_models import MLFinding
from src.engines.pattern_models import PatternFinding
from src.fusion.risk_models import RiskAssessment, RiskLevel, EngineContribution


class RiskBuilder:
    """
    Fuses findings from all engines into a single unified Risk Assessment.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Base Engine Weights
        self.base_weights = {
            "Rule": self.config.get("weight_rule", 0.30),
            "Behaviour": self.config.get("weight_behaviour", 0.20),
            "Statistical": self.config.get("weight_statistical", 0.15),
            "ML": self.config.get("weight_ml", 0.15),
            "Pattern": self.config.get("weight_pattern", 0.20)
        }

    def fuse(
        self,
        transaction_id: str,
        customer_id: str,
        rule_hits: List[RuleHit],
        behaviour_findings: List[BehaviourFinding],
        stat_findings: List[StatisticalFinding],
        ml_findings: List[MLFinding],
        pattern_findings: List[PatternFinding]
    ) -> RiskAssessment:
        
        # 1. Calculate Individual Engine Scores (0-100)
        engine_scores = {
            "Rule": self._calculate_rule_score(rule_hits),
            "Behaviour": self._calculate_behaviour_score(behaviour_findings),
            "Statistical": self._calculate_stat_score(stat_findings),
            "ML": self._calculate_ml_score(ml_findings),
            "Pattern": self._calculate_pattern_score(pattern_findings)
        }
        
        finding_counts = {
            "Rule": len(rule_hits),
            "Behaviour": len(behaviour_findings),
            "Statistical": len(stat_findings),
            "ML": len(ml_findings),
            "Pattern": len(pattern_findings)
        }
        
        # 2. Adaptive Weighting
        active_weights = {}
        for engine, count in finding_counts.items():
            if count > 0:
                active_weights[engine] = self.base_weights[engine]
                
        total_active_weight = sum(active_weights.values())
        
        normalized_weights = {}
        if total_active_weight > 0:
            for engine in engine_scores.keys():
                normalized_weights[engine] = active_weights.get(engine, 0.0) / total_active_weight
        else:
            # No findings anywhere
            for engine in engine_scores.keys():
                normalized_weights[engine] = 0.0
                
        # 3. Overall Risk Score
        overall_score = 0.0
        for engine in engine_scores.keys():
            overall_score += engine_scores[engine] * normalized_weights[engine]
            
        overall_score = min(100.0, max(0.0, overall_score))
        
        # 4. Confidence Score
        confidence = self._calculate_confidence(
            finding_counts, 
            rule_hits, behaviour_findings, stat_findings, ml_findings, pattern_findings
        )
        
        # 5. Determine Risk Level
        risk_level = self._determine_risk_level(overall_score)
        
        # 6. Build Breakdown and Evidence
        risk_breakdown = {}
        for engine, weight in normalized_weights.items():
            risk_breakdown[engine] = f"{weight * 100:.1f}%"
            
        top_reasons = self._extract_top_reasons(
            rule_hits, behaviour_findings, stat_findings, ml_findings, pattern_findings
        )
        
        supporting_evidence = {
            "RuleFindings": [h.__dict__ for h in rule_hits],
            "BehaviourFindings": [f.__dict__ for f in behaviour_findings],
            "StatisticalFindings": [f.__dict__ for f in stat_findings],
            "MLFindings": [f.__dict__ for f in ml_findings],
            "PatternFindings": [f.__dict__ for f in pattern_findings]
        }
        
        triggered_rules = [h.rule_name for h in rule_hits]
        triggered_patterns = [p.pattern_name for p in pattern_findings]
        
        return RiskAssessment(
            transaction_id=transaction_id,
            customer_id=customer_id,
            overall_risk_score=round(overall_score, 2),
            confidence_score=round(confidence, 2),
            risk_level=risk_level,
            engine_scores={k: round(v, 2) for k, v in engine_scores.items()},
            engine_weights={k: round(v, 4) for k, v in normalized_weights.items()},
            supporting_evidence=supporting_evidence,
            triggered_rules=triggered_rules,
            triggered_patterns=triggered_patterns,
            top_reasons=top_reasons,
            risk_breakdown=risk_breakdown
        )

    def _calculate_rule_score(self, hits: List[RuleHit]) -> float:
        if not hits:
            return 0.0
        # Sum of scores clamped to 100
        score = sum(h.score for h in hits)
        return min(100.0, score)

    def _calculate_behaviour_score(self, findings: List[BehaviourFinding]) -> float:
        if not findings:
            return 0.0
        score = sum(f.score for f in findings)
        return min(100.0, score)

    def _calculate_stat_score(self, findings: List[StatisticalFinding]) -> float:
        if not findings:
            return 0.0
        score = sum(f.score for f in findings)
        return min(100.0, score)

    def _calculate_ml_score(self, findings: List[MLFinding]) -> float:
        if not findings:
            return 0.0
        # Take the max confidence among ML findings, scale to 100
        max_conf = max(f.confidence for f in findings)
        return max_conf * 100.0

    def _calculate_pattern_score(self, findings: List[PatternFinding]) -> float:
        if not findings:
            return 0.0
        # Assign base scores to severities if pattern model doesn't have raw float scores
        severity_map = {"LOW": 25.0, "MEDIUM": 50.0, "HIGH": 80.0, "CRITICAL": 100.0}
        score = sum(severity_map.get(f.severity.value, 0.0) for f in findings)
        return min(100.0, score)

    def _calculate_confidence(
        self, counts: Dict[str, int],
        rule_hits: List[RuleHit],
        behaviour_findings: List[BehaviourFinding],
        stat_findings: List[StatisticalFinding],
        ml_findings: List[MLFinding],
        pattern_findings: List[PatternFinding]
    ) -> float:
        active_engines = sum(1 for v in counts.values() if v > 0)
        if active_engines == 0:
            return 100.0  # 100% confident it's a 0-risk transaction
            
        # Base confidence from multi-engine agreement
        base_confidence = min(100.0, 40.0 + (active_engines * 15.0))
        
        # Adjust based on explicit ML/Pattern confidence if available
        confidences = []
        confidences.extend([f.confidence * 100.0 for f in ml_findings])
        confidences.extend([f.confidence * 100.0 for f in pattern_findings])
        
        if confidences:
            avg_explicit_conf = sum(confidences) / len(confidences)
            # Blend
            final_conf = (base_confidence * 0.6) + (avg_explicit_conf * 0.4)
        else:
            final_conf = base_confidence
            
        return min(100.0, max(0.0, final_conf))

    def _determine_risk_level(self, score: float) -> RiskLevel:
        if score <= 20.0:
            return RiskLevel.LOW
        elif score <= 40.0:
            return RiskLevel.MEDIUM
        elif score <= 60.0:
            return RiskLevel.HIGH
        elif score <= 80.0:
            return RiskLevel.VERY_HIGH
        else:
            return RiskLevel.CRITICAL

    def _extract_top_reasons(
        self,
        rule_hits: List[RuleHit],
        behaviour_findings: List[BehaviourFinding],
        stat_findings: List[StatisticalFinding],
        ml_findings: List[MLFinding],
        pattern_findings: List[PatternFinding]
    ) -> List[str]:
        reasons = []
        
        # Collect severe findings
        for r in rule_hits:
            if r.severity.value in ("HIGH", "CRITICAL"):
                reasons.append(r.rule_name)
                
        for p in pattern_findings:
            if p.severity.value in ("HIGH", "CRITICAL"):
                reasons.append(p.pattern_name)
                
        for b in behaviour_findings:
            if b.severity.value in ("HIGH", "CRITICAL"):
                reasons.append(b.finding_name)
                
        for s in stat_findings:
            if s.severity.value in ("HIGH", "CRITICAL"):
                reasons.append(s.finding_name)
                
        for m in ml_findings:
            if m.prediction == "Anomaly":
                reasons.append("ML Identified Anomaly")
                
        # Deduplicate and limit
        unique_reasons = list(dict.fromkeys(reasons))
        return unique_reasons[:5]
