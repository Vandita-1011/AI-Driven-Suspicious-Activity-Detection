from typing import List, Optional, Dict, Any
from datetime import datetime

from src.features.feature_models import FeatureVector
from src.profiling.profile_models import BehaviourProfile
from src.engines.behaviour_models import BehaviourFinding, BehaviourSeverity


class BehaviourBuilder:
    """
    Executes individual behaviour anomaly detectors against a transaction's feature vector.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initializes BehaviourBuilder with configurable thresholds.
        """
        self.config = config or {}
        
        self.freq_deviation_threshold = self.config.get("B004_freq_deviation_threshold", 0.5)
        self.amount_deviation_threshold = self.config.get("B005_amount_deviation_threshold", 0.6)
        
        self.composite_trigger_threshold = self.config.get("B010_composite_trigger_threshold", 3)

    def evaluate(self, fv: FeatureVector, profile: Optional[BehaviourProfile]) -> List[BehaviourFinding]:
        """
        Evaluates a single transaction against all behaviour anomaly detectors.
        """
        findings = []
        
        # We need a profile to compare against. If none exists, we can only evaluate basic feature flags.
        
        self._detect_hour_change(fv, profile, findings)
        self._detect_business_hour_change(fv, profile, findings)
        self._detect_weekend_change(fv, profile, findings)
        self._detect_frequency_change(fv, profile, findings)
        self._detect_amount_change(fv, profile, findings)
        self._detect_beneficiary_change(fv, profile, findings)
        self._detect_device_change(fv, profile, findings)
        self._detect_channel_change(fv, profile, findings)
        self._detect_country_change(fv, profile, findings)
        
        self._detect_composite_anomaly(fv, findings)
        
        return findings

    def _create_finding(
        self, fv: FeatureVector, finding_id: str, finding_name: str, 
        severity: BehaviourSeverity, score: float, behaviour_type: str,
        expected_behaviour: str, observed_behaviour: str, deviation: float,
        explanation: str
    ) -> BehaviourFinding:
        
        # Base confidence calculation
        confidence = min(1.0, 0.7 + (deviation * 0.1)) if deviation > 0 else 0.8
        
        return BehaviourFinding(
            finding_id=finding_id,
            finding_name=finding_name,
            severity=severity,
            score=score,
            triggered=True,
            customer_id=fv.customer_id,
            transaction_id=fv.transaction_id,
            behaviour_type=behaviour_type,
            expected_behaviour=expected_behaviour,
            observed_behaviour=observed_behaviour,
            deviation=deviation,
            confidence=round(confidence, 2),
            explanation=explanation,
            timestamp=str(fv.timestamp)
        )

    def _extract_hour(self, timestamp_str: str) -> int:
        try:
            return datetime.fromisoformat(timestamp_str).hour
        except (ValueError, TypeError):
            return -1

    def _detect_hour_change(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[BehaviourFinding]):
        if fv.outside_preferred_hour and profile and profile.statistics:
            txn_hour = self._extract_hour(fv.timestamp)
            expected_hour = profile.statistics.preferred_hour
            
            # Calculate absolute shortest hour difference (0-12)
            diff = abs(txn_hour - expected_hour)
            diff = min(diff, 24 - diff)
            
            findings.append(self._create_finding(
                fv, "B001", "Preferred Hour Deviation", BehaviourSeverity.LOW, 25.0,
                "temporal", f"Preferred hour: {expected_hour}:00", f"Observed hour: {txn_hour}:00", float(diff),
                f"Customer normally transacts around {expected_hour}:00 but current transaction occurred at {txn_hour}:00."
            ))

    def _detect_business_hour_change(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[BehaviourFinding]):
        if profile and profile.statistics:
            # If the customer almost exclusively transacts during business hours (> 90%)
            if profile.statistics.business_hours_ratio > 0.9 and fv.outside_business_hours:
                findings.append(self._create_finding(
                    fv, "B002", "Business Hour Deviation", BehaviourSeverity.MEDIUM, 40.0,
                    "temporal", "During business hours", "Outside business hours", 1.0,
                    "Customer historically transacts almost exclusively during business hours, but this transaction is outside that window."
                ))

    def _detect_weekend_change(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[BehaviourFinding]):
        if fv.unusual_weekday and profile and profile.statistics:
            if profile.statistics.weekend_ratio < 0.05: # Usually doesn't transact on weekends
                findings.append(self._create_finding(
                    fv, "B003", "Weekend Behaviour Change", BehaviourSeverity.MEDIUM, 45.0,
                    "temporal", "Weekday transactions", "Weekend transaction", 1.0,
                    "Customer rarely transacts on weekends, but this transaction occurred on an unusual weekday/weekend for them."
                ))

    def _detect_frequency_change(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[BehaviourFinding]):
        if fv.frequency_deviation_score > self.freq_deviation_threshold:
            findings.append(self._create_finding(
                fv, "B004", "Frequency Behaviour Change", BehaviourSeverity.HIGH, 75.0,
                "frequency", "Normal transaction rate", "Abnormal transaction rate", fv.frequency_deviation_score,
                f"Customer frequency behaviour deviates significantly from historical baseline (Deviation Score: {fv.frequency_deviation_score:.2f})."
            ))

    def _detect_amount_change(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[BehaviourFinding]):
        if fv.amount_deviation_score > self.amount_deviation_threshold:
            findings.append(self._create_finding(
                fv, "B005", "Amount Behaviour Change", BehaviourSeverity.HIGH, 70.0,
                "amount", "Expected transaction amount range", "Highly unusual amount", fv.amount_deviation_score,
                f"Transaction amount pattern deviates significantly from historical baseline (Deviation Score: {fv.amount_deviation_score:.2f})."
            ))

    def _detect_beneficiary_change(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[BehaviourFinding]):
        if fv.new_beneficiary:
            # If the customer usually transacts with the same few beneficiaries
            if profile and profile.statistics and profile.statistics.unique_beneficiaries < 3 and profile.statistics.avg_monthly_txns > 10:
                findings.append(self._create_finding(
                    fv, "B006", "Beneficiary Behaviour Change", BehaviourSeverity.MEDIUM, 60.0,
                    "counterparty", "Established beneficiaries", "Completely new beneficiary", 1.0,
                    "Customer with highly repetitive counterparty history is transacting with a completely new beneficiary."
                ))
            else:
                findings.append(self._create_finding(
                    fv, "B006", "Beneficiary Behaviour Change", BehaviourSeverity.LOW, 30.0,
                    "counterparty", "Known beneficiary", "New beneficiary", 0.5,
                    "Customer is transacting with a new beneficiary."
                ))

    def _detect_device_change(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[BehaviourFinding]):
        if fv.device_switch_flag or fv.new_device:
            severity = BehaviourSeverity.HIGH if fv.device_switch_flag else BehaviourSeverity.MEDIUM
            score = 70.0 if fv.device_switch_flag else 50.0
            desc = "Customer switched devices between consecutive transactions." if fv.device_switch_flag else "Customer is using a new device."
            
            findings.append(self._create_finding(
                fv, "B007", "Device Behaviour Change", severity, score,
                "channel_device", "Established device", "New or switched device", 1.0,
                desc
            ))

    def _detect_channel_change(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[BehaviourFinding]):
        if fv.outside_preferred_channel and profile and profile.statistics:
            findings.append(self._create_finding(
                fv, "B008", "Channel Behaviour Change", BehaviourSeverity.MEDIUM, 50.0,
                "channel_device", f"Preferred channel: {profile.statistics.most_common_channel}", "Alternative channel used", 1.0,
                f"Customer normally prefers {profile.statistics.most_common_channel} but used an alternative channel for this transaction."
            ))

    def _detect_country_change(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[BehaviourFinding]):
        if fv.new_country:
            findings.append(self._create_finding(
                fv, "B009", "Country Behaviour Change", BehaviourSeverity.HIGH, 80.0,
                "geographic", "Domestic/Known countries", "New geographic location", 1.0,
                "Transaction involves a completely new geographical country that the customer has never interacted with before."
            ))

    def _detect_composite_anomaly(self, fv: FeatureVector, findings: List[BehaviourFinding]):
        high_critical_count = sum(1 for f in findings if f.severity in (BehaviourSeverity.HIGH, BehaviourSeverity.CRITICAL))
        if high_critical_count >= self.composite_trigger_threshold:
            findings.append(self._create_finding(
                fv, "B010", "Composite Behaviour Anomaly", BehaviourSeverity.CRITICAL, 95.0,
                "composite", "Normal baseline behaviour", f"{high_critical_count} major behavioural shifts", float(high_critical_count),
                f"Transaction triggered {high_critical_count} simultaneous HIGH/CRITICAL behavioural shifts, indicating fundamentally altered activity."
            ))
