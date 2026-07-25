from typing import List, Optional, Dict, Any
from src.features.feature_models import FeatureVector
from src.profiling.profile_models import BehaviourProfile
from src.engines.pattern_models import PatternFinding, PatternSeverity


class PatternBuilder:
    """
    Evaluates known AML typologies and patterns against transaction features.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Pattern Thresholds
        self.structuring_lower = self.config.get("P001_structuring_lower", 8000.0)
        self.structuring_upper = self.config.get("P001_structuring_upper", 10000.0)
        self.structuring_velocity = self.config.get("P001_structuring_velocity", 3)
        
        self.burst_hour_threshold = self.config.get("P013_burst_hour_threshold", 8)
        self.burst_gap_threshold = self.config.get("P013_burst_gap_threshold", 0.1) # hours
        
        self.escalating_ratio_threshold = self.config.get("P014_escalating_ratio_threshold", 3.0)

    def evaluate(self, fv: FeatureVector, profile: Optional[BehaviourProfile]) -> List[PatternFinding]:
        findings = []
        
        self._detect_structuring(fv, findings)
        self._detect_rapid_movement(fv, profile, findings)
        self._detect_layering(fv, profile, findings)
        self._detect_circular_transactions(fv, profile, findings)
        self._detect_fan_out(fv, profile, findings)
        self._detect_fan_in(fv, profile, findings)
        self._detect_dormant_reactivation(fv, profile, findings)
        self._detect_cross_border_layering(fv, findings)
        self._detect_high_risk_geography(fv, findings)
        self._detect_cash_intensive_behaviour(fv, profile, findings)
        self._detect_shared_device(fv, findings)
        self._detect_shared_beneficiary(fv, profile, findings)
        self._detect_burst_activity(fv, findings)
        self._detect_escalating_amounts(fv, findings)
        
        self._detect_composite_pattern(fv, findings)
        
        return findings

    def _create_finding(
        self, fv: FeatureVector, pattern_id: str, pattern_name: str, 
        severity: PatternSeverity, confidence: float, description: str, evidence: dict
    ) -> PatternFinding:
        return PatternFinding(
            pattern_id=pattern_id,
            pattern_name=pattern_name,
            severity=severity,
            confidence=confidence,
            description=description,
            evidence=evidence,
            customer_id=fv.customer_id,
            transaction_id=fv.transaction_id,
            timestamp=str(fv.timestamp)
        )

    def _detect_structuring(self, fv: FeatureVector, findings: List[PatternFinding]):
        if self.structuring_lower <= fv.transaction_amount < self.structuring_upper:
            if fv.transactions_last_day >= self.structuring_velocity:
                findings.append(self._create_finding(
                    fv, "P001", "Structuring / Smurfing", PatternSeverity.CRITICAL, 0.95,
                    "Multiple medium-sized transactions occurring just below mandatory reporting thresholds.",
                    {"amount": fv.transaction_amount, "daily_velocity": fv.transactions_last_day}
                ))

    def _detect_rapid_movement(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[PatternFinding]):
        # Proxy: Extremely short gap between transactions, especially if transfer ratio is high
        if fv.time_since_previous_transaction < 0.5 and fv.transactions_last_hour >= 2:
            is_transfer = profile.statistics.transfer_ratio > 0.5 if (profile and profile.statistics) else True
            if is_transfer:
                findings.append(self._create_finding(
                    fv, "P002", "Rapid Movement of Funds", PatternSeverity.HIGH, 0.85,
                    "Funds are being moved extremely quickly between accounts or entities.",
                    {"time_gap": fv.time_since_previous_transaction, "txns_last_hour": fv.transactions_last_hour}
                ))

    def _detect_layering(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[PatternFinding]):
        if profile and profile.statistics:
            # High velocity to multiple unique entities
            if fv.transactions_last_day > 5 and profile.statistics.unique_beneficiaries > 5:
                findings.append(self._create_finding(
                    fv, "P003", "Layering", PatternSeverity.CRITICAL, 0.90,
                    "Funds rapidly transferred through multiple beneficiaries or accounts to obscure origin.",
                    {"daily_velocity": fv.transactions_last_day, "unique_beneficiaries": profile.statistics.unique_beneficiaries}
                ))

    def _detect_circular_transactions(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[PatternFinding]):
        # Proxy: Very high frequency back and forth to same beneficiary
        if fv.beneficiary_is_high_frequency and fv.beneficiary_transaction_count > 10 and fv.time_since_previous_transaction < 1.0:
            findings.append(self._create_finding(
                fv, "P004", "Circular Transactions", PatternSeverity.HIGH, 0.80,
                "Repeated, high-velocity transactions cycling with a small network or returning to origin.",
                {"beneficiary_frequency": fv.beneficiary_transaction_count, "time_gap": fv.time_since_previous_transaction}
            ))

    def _detect_fan_out(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[PatternFinding]):
        if fv.transactions_last_hour >= 5 and fv.new_beneficiary:
            findings.append(self._create_finding(
                fv, "P005", "Fan-Out", PatternSeverity.HIGH, 0.85,
                "One account rapidly sending money to multiple distinct beneficiaries in a short period.",
                {"txns_last_hour": fv.transactions_last_hour, "new_beneficiary": True}
            ))

    def _detect_fan_in(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[PatternFinding]):
        # Assuming we can infer fan-in if receiving high volume from multiple sources. 
        # In this dataset context, we'll proxy it by high volume but low outbound amounts if possible.
        # Alternatively, use high transaction count + not new beneficiary (just rapid existing ties)
        # We will use rolling transaction count > 15 in a day with low amount deviation as a heuristic.
        if fv.transactions_last_day >= 15 and fv.amount_deviation_score < 0.2:
            findings.append(self._create_finding(
                fv, "P006", "Fan-In", PatternSeverity.HIGH, 0.75,
                "Pattern suggests many different accounts are sending funds to this single hub account.",
                {"daily_velocity": fv.transactions_last_day, "amount_deviation": fv.amount_deviation_score}
            ))

    def _detect_dormant_reactivation(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[PatternFinding]):
        if profile and hasattr(profile, "flags") and profile.flags.dormant_customer:
            if fv.transactions_last_day >= 2 or fv.amount_z_score > 1.5:
                findings.append(self._create_finding(
                    fv, "P007", "Dormant Account Reactivation", PatternSeverity.HIGH, 0.90,
                    "A historically dormant account has suddenly become highly active or executed a large transfer.",
                    {"dormant_flag": True, "recent_activity": fv.transactions_last_day, "amount_z_score": fv.amount_z_score}
                ))

    def _detect_cross_border_layering(self, fv: FeatureVector, findings: List[PatternFinding]):
        if fv.cross_border_transaction and fv.geographic_change and fv.transactions_last_day >= 3:
            findings.append(self._create_finding(
                fv, "P008", "Cross-Border Layering", PatternSeverity.CRITICAL, 0.95,
                "Rapid movement of funds across several different international borders.",
                {"cross_border": True, "geographic_change": True, "daily_velocity": fv.transactions_last_day}
            ))

    def _detect_high_risk_geography(self, fv: FeatureVector, findings: List[PatternFinding]):
        if fv.high_risk_country_flag:
            findings.append(self._create_finding(
                fv, "P009", "High-Risk Geography Pattern", PatternSeverity.CRITICAL, 0.98,
                "Repeated or significant activity involving known FATF high-risk or sanctioned jurisdictions.",
                {"high_risk_country": True}
            ))

    def _detect_cash_intensive_behaviour(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[PatternFinding]):
        if profile and hasattr(profile, "flags") and profile.flags.cash_intensive_customer:
            if fv.large_transaction_flag or fv.amount_z_score > 2.0:
                findings.append(self._create_finding(
                    fv, "P010", "Cash Intensive Behaviour", PatternSeverity.HIGH, 0.85,
                    "Large transfers immediately following or preceding significant cash deposits.",
                    {"cash_intensive_profile": True, "large_txn": fv.large_transaction_flag}
                ))

    def _detect_shared_device(self, fv: FeatureVector, findings: List[PatternFinding]):
        if fv.device_switch_flag and fv.unique_devices_last_30_days >= 3:
            findings.append(self._create_finding(
                fv, "P011", "Shared Device Pattern", PatternSeverity.MEDIUM, 0.80,
                "Multiple customers or accounts appear to be operated from the same physical device.",
                {"device_switch": True, "unique_devices": fv.unique_devices_last_30_days}
            ))

    def _detect_shared_beneficiary(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[PatternFinding]):
        if fv.beneficiary_is_high_frequency and fv.beneficiary_transaction_count > 15:
            findings.append(self._create_finding(
                fv, "P012", "Shared Beneficiary Pattern", PatternSeverity.HIGH, 0.85,
                "Unusually high volume of funds funneling to a single shared beneficiary from this and other accounts.",
                {"beneficiary_txns": fv.beneficiary_transaction_count}
            ))

    def _detect_burst_activity(self, fv: FeatureVector, findings: List[PatternFinding]):
        if fv.transactions_last_hour >= self.burst_hour_threshold and fv.time_since_previous_transaction < self.burst_gap_threshold:
            findings.append(self._create_finding(
                fv, "P013", "Burst Activity", PatternSeverity.CRITICAL, 0.95,
                "Extremely high transaction velocity concentrated in a very short, anomalous time window.",
                {"txns_last_hour": fv.transactions_last_hour, "time_gap": fv.time_since_previous_transaction}
            ))

    def _detect_escalating_amounts(self, fv: FeatureVector, findings: List[PatternFinding]):
        if fv.amount_ratio_to_average > self.escalating_ratio_threshold and fv.amount_percentile > 0.95:
            findings.append(self._create_finding(
                fv, "P014", "Escalating Transaction Amounts", PatternSeverity.HIGH, 0.90,
                "Transaction values are rapidly and systematically increasing compared to historical norms.",
                {"ratio_to_avg": fv.amount_ratio_to_average, "percentile": fv.amount_percentile}
            ))

    def _detect_composite_pattern(self, fv: FeatureVector, findings: List[PatternFinding]):
        high_critical_count = sum(1 for f in findings if f.severity in (PatternSeverity.HIGH, PatternSeverity.CRITICAL))
        if high_critical_count >= 3:
            findings.append(self._create_finding(
                fv, "P015", "Composite AML Pattern", PatternSeverity.CRITICAL, 1.0,
                "Transaction matches three or more HIGH or CRITICAL severity money laundering typologies simultaneously.",
                {"high_critical_pattern_count": high_critical_count}
            ))
