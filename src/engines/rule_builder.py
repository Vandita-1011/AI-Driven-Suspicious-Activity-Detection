from typing import List, Optional, Dict, Any
from src.features.feature_models import FeatureVector
from src.profiling.profile_models import BehaviourProfile
from src.engines.rule_models import RuleHit, RuleSeverity


class RuleBuilder:
    """
    Executes individual AML rules against a transaction's feature vector.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initializes RuleBuilder with configurable thresholds.
        """
        self.config = config or {}
        
        # Rule Config Thresholds
        self.z_score_threshold = self.config.get("R002_z_score_threshold", 3.0)
        self.rapid_velocity_hour_threshold = self.config.get("R003_rapid_velocity_hour_threshold", 5)
        self.rapid_velocity_day_threshold = self.config.get("R003_rapid_velocity_day_threshold", 15)
        self.behaviour_deviation_threshold = self.config.get("R004_behaviour_deviation_threshold", 0.7)
        self.sar_history_threshold = self.config.get("R015_sar_history_threshold", 0)
        
        # Structuring thresholds (R017)
        self.structuring_reporting_threshold = self.config.get("R017_reporting_threshold", 10000.0)
        self.structuring_lower_bound = self.config.get("R017_lower_bound", 8000.0)
        self.structuring_velocity_threshold = self.config.get("R017_velocity_threshold", 3)
        
        # Cash intensive thresholds (R018)
        self.cash_ratio_threshold = self.config.get("R018_cash_ratio_threshold", 0.5)

    def evaluate(self, fv: FeatureVector, profile: Optional[BehaviourProfile]) -> List[RuleHit]:
        """
        Evaluates a single transaction against all AML rules.
        """
        hits = []
        
        # Evaluate individual rules
        self._check_large_transaction(fv, hits)
        self._check_large_z_score(fv, hits)
        self._check_rapid_velocity(fv, hits)
        self._check_behaviour_deviation(fv, hits)
        self._check_outside_business_hours(fv, hits)
        self._check_outside_preferred_hour(fv, hits)
        self._check_new_beneficiary(fv, hits)
        self._check_high_frequency_beneficiary(fv, hits)
        self._check_new_device(fv, hits)
        self._check_device_switch(fv, hits)
        self._check_new_country(fv, hits)
        self._check_cross_border_transaction(fv, hits)
        self._check_high_risk_country(fv, hits)
        self._check_pep_customer(fv, hits)
        self._check_previous_sar_history(fv, hits)
        self._check_dormant_reactivation(fv, profile, hits)
        self._check_structuring_indicator(fv, hits)
        self._check_cash_intensive_behaviour(fv, profile, hits)
        self._check_channel_anomaly(fv, hits)
        
        # Evaluate multi-signal composite rule
        self._check_multiple_high_risk_signals(fv, hits)
        
        return hits

    def _create_hit(
        self, fv: FeatureVector, rule_id: str, rule_name: str, 
        severity: RuleSeverity, score: float, reason: str, explanation: str, evidence: dict
    ) -> RuleHit:
        return RuleHit(
            rule_id=rule_id,
            rule_name=rule_name,
            severity=severity,
            score=score,
            triggered=True,
            reason=reason,
            explanation=explanation,
            evidence=evidence,
            customer_id=fv.customer_id,
            transaction_id=fv.transaction_id,
            timestamp=str(fv.timestamp)
        )

    def _check_large_transaction(self, fv: FeatureVector, hits: List[RuleHit]):
        if fv.large_transaction_flag:
            hits.append(self._create_hit(
                fv, "R001", "Large Transaction", RuleSeverity.HIGH, 80.0,
                "Transaction amount exceeds dynamic historical thresholds.",
                f"Transaction amount is significantly larger than historical average ({fv.customer_average_amount:,.2f}).",
                {"transaction_amount": fv.transaction_amount, "customer_average_amount": fv.customer_average_amount}
            ))

    def _check_large_z_score(self, fv: FeatureVector, hits: List[RuleHit]):
        if fv.amount_z_score > self.z_score_threshold:
            hits.append(self._create_hit(
                fv, "R002", "Large Z-Score", RuleSeverity.MEDIUM, 60.0,
                "Amount deviates significantly from established statistical distribution.",
                f"Transaction amount has a z-score of {fv.amount_z_score:.2f}, indicating it is an outlier.",
                {"amount_z_score": fv.amount_z_score, "threshold": self.z_score_threshold}
            ))

    def _check_rapid_velocity(self, fv: FeatureVector, hits: List[RuleHit]):
        if fv.transactions_last_hour >= self.rapid_velocity_hour_threshold or fv.transactions_last_day >= self.rapid_velocity_day_threshold:
            hits.append(self._create_hit(
                fv, "R003", "Rapid Transaction Velocity", RuleSeverity.HIGH, 75.0,
                "High frequency of transactions in a short time window.",
                f"Customer executed {fv.transactions_last_hour} txns in 1 hr and {fv.transactions_last_day} txns in 24 hrs.",
                {"txns_last_hour": fv.transactions_last_hour, "txns_last_day": fv.transactions_last_day}
            ))

    def _check_behaviour_deviation(self, fv: FeatureVector, hits: List[RuleHit]):
        if fv.behaviour_deviation_score > self.behaviour_deviation_threshold:
            hits.append(self._create_hit(
                fv, "R004", "Behaviour Deviation", RuleSeverity.MEDIUM, 65.0,
                "Transaction severely deviates from baseline behavioral profile.",
                f"Composite deviation score is {fv.behaviour_deviation_score:.2f}, indicating unusual temporal and frequency patterns.",
                {"deviation_score": fv.behaviour_deviation_score}
            ))

    def _check_outside_business_hours(self, fv: FeatureVector, hits: List[RuleHit]):
        if fv.outside_business_hours:
            hits.append(self._create_hit(
                fv, "R005", "Outside Business Hours", RuleSeverity.LOW, 20.0,
                "Transaction occurred outside standard business hours.",
                "Transaction occurred outside the standard 9AM - 5PM window.",
                {"outside_business_hours": True}
            ))

    def _check_outside_preferred_hour(self, fv: FeatureVector, hits: List[RuleHit]):
        if fv.outside_preferred_hour:
            hits.append(self._create_hit(
                fv, "R006", "Outside Preferred Hour", RuleSeverity.LOW, 20.0,
                "Transaction time deviates from customer's historical preference.",
                "Transaction hour is unusual compared to historical baseline.",
                {"outside_preferred_hour": True}
            ))

    def _check_new_beneficiary(self, fv: FeatureVector, hits: List[RuleHit]):
        if fv.new_beneficiary:
            hits.append(self._create_hit(
                fv, "R007", "New Beneficiary", RuleSeverity.LOW, 30.0,
                "First time transaction to this counterparty account.",
                "Customer has never transferred funds to this beneficiary before.",
                {"new_beneficiary": True}
            ))

    def _check_high_frequency_beneficiary(self, fv: FeatureVector, hits: List[RuleHit]):
        if fv.beneficiary_is_high_frequency:
            hits.append(self._create_hit(
                fv, "R008", "High Frequency Beneficiary", RuleSeverity.MEDIUM, 40.0,
                "Frequent transfers to the same beneficiary.",
                f"Customer has transferred to this beneficiary {fv.beneficiary_transaction_count} times.",
                {"beneficiary_transaction_count": fv.beneficiary_transaction_count}
            ))

    def _check_new_device(self, fv: FeatureVector, hits: List[RuleHit]):
        if fv.new_device:
            hits.append(self._create_hit(
                fv, "R009", "New Device", RuleSeverity.MEDIUM, 50.0,
                "Transaction initiated from a previously unseen device.",
                "Customer used a new device identifier for this transaction.",
                {"new_device": True}
            ))

    def _check_device_switch(self, fv: FeatureVector, hits: List[RuleHit]):
        if fv.device_switch_flag:
            hits.append(self._create_hit(
                fv, "R010", "Device Switch", RuleSeverity.MEDIUM, 45.0,
                "Transaction initiated from a different device than the immediate previous transaction.",
                "Customer switched devices between consecutive transactions.",
                {"device_switch_flag": True}
            ))

    def _check_new_country(self, fv: FeatureVector, hits: List[RuleHit]):
        if fv.new_country:
            hits.append(self._create_hit(
                fv, "R011", "New Country", RuleSeverity.HIGH, 70.0,
                "First time transaction involving this counterparty country.",
                "Customer has no prior history transacting with this geographical location.",
                {"new_country": True}
            ))

    def _check_cross_border_transaction(self, fv: FeatureVector, hits: List[RuleHit]):
        if fv.cross_border_transaction:
            hits.append(self._create_hit(
                fv, "R012", "Cross Border Transaction", RuleSeverity.MEDIUM, 55.0,
                "Transaction crosses international borders.",
                "Counterparty country differs from customer's home country.",
                {"cross_border": True}
            ))

    def _check_high_risk_country(self, fv: FeatureVector, hits: List[RuleHit]):
        if fv.high_risk_country_flag:
            hits.append(self._create_hit(
                fv, "R013", "High Risk Country", RuleSeverity.CRITICAL, 95.0,
                "Transaction involves a known FATF high-risk jurisdiction.",
                "Counterparty is located in a high-risk or sanctioned country.",
                {"high_risk_country": True}
            ))

    def _check_pep_customer(self, fv: FeatureVector, hits: List[RuleHit]):
        if fv.pep_flag:
            hits.append(self._create_hit(
                fv, "R014", "PEP Customer", RuleSeverity.HIGH, 85.0,
                "Customer is identified as a Politically Exposed Person.",
                "Enhanced due diligence is required due to PEP status.",
                {"pep_flag": True}
            ))

    def _check_previous_sar_history(self, fv: FeatureVector, hits: List[RuleHit]):
        if fv.previous_sar_count > self.sar_history_threshold:
            hits.append(self._create_hit(
                fv, "R015", "Previous SAR History", RuleSeverity.CRITICAL, 90.0,
                "Customer has previous Suspicious Activity Reports filed.",
                f"Customer was previously subject to {fv.previous_sar_count} SAR filings.",
                {"previous_sar_count": fv.previous_sar_count}
            ))

    def _check_dormant_reactivation(self, fv: FeatureVector, profile: Optional[BehaviourProfile], hits: List[RuleHit]):
        if profile and hasattr(profile, "flags") and profile.flags.dormant_customer:
            # Re-activating with sudden high velocity or large amount
            if fv.transactions_last_day >= 3 or fv.amount_z_score > 2.0:
                hits.append(self._create_hit(
                    fv, "R016", "Dormant Account Reactivation", RuleSeverity.HIGH, 80.0,
                    "Historically dormant account suddenly exhibiting high activity.",
                    "Account flagged as dormant in profile but shows rapid new activity.",
                    {"dormant_baseline": True, "recent_txns": fv.transactions_last_day}
                ))

    def _check_structuring_indicator(self, fv: FeatureVector, hits: List[RuleHit]):
        # Amount just below reporting threshold and multiple transactions recently
        if self.structuring_lower_bound <= fv.transaction_amount < self.structuring_reporting_threshold:
            if fv.transactions_last_day >= self.structuring_velocity_threshold:
                hits.append(self._create_hit(
                    fv, "R017", "Structuring Indicator", RuleSeverity.CRITICAL, 95.0,
                    "Multiple transactions executed just below mandatory reporting thresholds.",
                    f"Executed {fv.transactions_last_day} txns near reporting threshold within 24 hours.",
                    {"amount": fv.transaction_amount, "velocity": fv.transactions_last_day}
                ))

    def _check_cash_intensive_behaviour(self, fv: FeatureVector, profile: Optional[BehaviourProfile], hits: List[RuleHit]):
        if profile and hasattr(profile, "statistics"):
            if profile.statistics.cash_withdrawal_ratio + profile.statistics.deposit_ratio > self.cash_ratio_threshold:
                # If transaction itself is a high z-score for cash intensive customer
                if fv.amount_z_score > 2.0:
                    hits.append(self._create_hit(
                        fv, "R018", "Cash Intensive Behaviour", RuleSeverity.HIGH, 75.0,
                        "Unusually large transaction for a historically cash-intensive profile.",
                        f"Customer cash ratio is high and current txn is large.",
                        {"cash_ratio": profile.statistics.cash_withdrawal_ratio + profile.statistics.deposit_ratio}
                    ))

    def _check_channel_anomaly(self, fv: FeatureVector, hits: List[RuleHit]):
        if fv.outside_preferred_channel:
            hits.append(self._create_hit(
                fv, "R019", "Channel Anomaly", RuleSeverity.LOW, 25.0,
                "Transaction executed on a non-preferred channel.",
                f"Customer historically prefers another channel but used {fv.outside_preferred_channel} (anomaly flag).",
                {"outside_preferred_channel": True}
            ))

    def _check_multiple_high_risk_signals(self, fv: FeatureVector, hits: List[RuleHit]):
        # Count how many HIGH or CRITICAL rules triggered in current hits
        high_critical_count = sum(1 for h in hits if h.severity in (RuleSeverity.HIGH, RuleSeverity.CRITICAL))
        if high_critical_count >= 3:
            hits.append(self._create_hit(
                fv, "R020", "Multiple High Risk Signals", RuleSeverity.CRITICAL, 100.0,
                "Transaction triggered three or more high/critical severity AML rules simultaneously.",
                f"Compounded risk: {high_critical_count} major red flags identified on a single transaction.",
                {"high_critical_rule_count": high_critical_count}
            ))
