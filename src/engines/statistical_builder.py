from typing import List, Optional, Dict, Any
from src.features.feature_models import FeatureVector
from src.profiling.profile_models import BehaviourProfile
from src.engines.statistical_models import StatisticalFinding, StatisticalSeverity


class StatisticalBuilder:
    """
    Executes individual statistical anomaly detectors against a transaction's feature vector.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initializes StatisticalBuilder with configurable thresholds.
        """
        self.config = config or {}
        
        # Detector Config Thresholds
        self.z_score_threshold = self.config.get("S001_z_score_threshold", 3.0)
        self.percentile_threshold = self.config.get("S002_percentile_threshold", 0.95)
        self.rolling_mean_deviation_threshold = self.config.get("S003_rolling_mean_deviation_threshold", 2.0) # multiple of rolling mean
        self.rolling_std_deviation_threshold = self.config.get("S004_rolling_std_deviation_threshold", 2.5) # number of rolling stds
        
        self.freq_spike_hour_multiplier = self.config.get("S005_freq_spike_hour_multiplier", 3.0)
        self.freq_spike_day_multiplier = self.config.get("S005_freq_spike_day_multiplier", 3.0)
        
        self.velocity_spike_threshold = self.config.get("S006_velocity_spike_threshold", 5.0) # transactions per hour vs normal
        
        self.time_gap_outlier_threshold = self.config.get("S007_time_gap_outlier_threshold", 0.1) # e.g. 10% of normal gap
        self.behaviour_deviation_threshold = self.config.get("S008_behaviour_deviation_threshold", 0.75)
        
        self.composite_trigger_threshold = self.config.get("S010_composite_trigger_threshold", 3)

    def evaluate(self, fv: FeatureVector, profile: Optional[BehaviourProfile]) -> List[StatisticalFinding]:
        """
        Evaluates a single transaction against all statistical anomaly detectors.
        """
        findings = []
        
        # Evaluate individual detectors
        self._detect_amount_zscore(fv, findings)
        self._detect_amount_percentile(fv, findings)
        self._detect_rolling_mean_deviation(fv, findings)
        self._detect_rolling_std_deviation(fv, findings)
        self._detect_frequency_spike(fv, profile, findings)
        self._detect_velocity_spike(fv, profile, findings)
        self._detect_gap_outlier(fv, profile, findings)
        self._detect_behaviour_deviation(fv, findings)
        self._detect_historical_range_violation(fv, findings)
        
        # Evaluate composite outlier
        self._detect_composite_outlier(fv, findings)
        
        return findings

    def _create_finding(
        self, fv: FeatureVector, finding_id: str, finding_name: str, 
        severity: StatisticalSeverity, score: float, metric_name: str,
        metric_value: float, expected_value: float, deviation: float,
        explanation: str
    ) -> StatisticalFinding:
        # Simple confidence scaling based on deviation, capped at 1.0
        confidence = min(1.0, 0.5 + (deviation * 0.05)) if deviation > 0 else 0.8
        
        return StatisticalFinding(
            finding_id=finding_id,
            finding_name=finding_name,
            severity=severity,
            score=score,
            triggered=True,
            customer_id=fv.customer_id,
            transaction_id=fv.transaction_id,
            metric_name=metric_name,
            metric_value=metric_value,
            expected_value=expected_value,
            deviation=deviation,
            confidence=round(confidence, 2),
            explanation=explanation,
            timestamp=str(fv.timestamp)
        )

    def _detect_amount_zscore(self, fv: FeatureVector, findings: List[StatisticalFinding]):
        if abs(fv.amount_z_score) > self.z_score_threshold:
            severity = StatisticalSeverity.HIGH if abs(fv.amount_z_score) > self.z_score_threshold * 1.5 else StatisticalSeverity.MEDIUM
            score = 75.0 if severity == StatisticalSeverity.HIGH else 50.0
            findings.append(self._create_finding(
                fv, "S001", "Amount Z-Score", severity, score,
                "amount_z_score", fv.amount_z_score, 0.0, fv.amount_z_score,
                f"Transaction amount is {fv.amount_z_score:.2f} standard deviations from the customer's historical mean."
            ))

    def _detect_amount_percentile(self, fv: FeatureVector, findings: List[StatisticalFinding]):
        if fv.amount_percentile > self.percentile_threshold:
            findings.append(self._create_finding(
                fv, "S002", "Amount Percentile", StatisticalSeverity.MEDIUM, 60.0,
                "amount_percentile", fv.amount_percentile, self.percentile_threshold, 
                fv.amount_percentile - self.percentile_threshold,
                f"Transaction amount is in the {(fv.amount_percentile*100):.1f}th percentile of the customer's historical amounts."
            ))

    def _detect_rolling_mean_deviation(self, fv: FeatureVector, findings: List[StatisticalFinding]):
        if fv.rolling_average_amount > 0:
            ratio = fv.transaction_amount / fv.rolling_average_amount
            if ratio > self.rolling_mean_deviation_threshold:
                findings.append(self._create_finding(
                    fv, "S003", "Rolling Mean Deviation", StatisticalSeverity.MEDIUM, 65.0,
                    "rolling_mean_ratio", ratio, 1.0, ratio - 1.0,
                    f"Transaction amount is {ratio:.1f}x the recent rolling average amount."
                ))

    def _detect_rolling_std_deviation(self, fv: FeatureVector, findings: List[StatisticalFinding]):
        if fv.rolling_std_amount > 0 and fv.rolling_average_amount > 0:
            diff = fv.transaction_amount - fv.rolling_average_amount
            std_diff = diff / fv.rolling_std_amount
            if std_diff > self.rolling_std_deviation_threshold:
                findings.append(self._create_finding(
                    fv, "S004", "Rolling Standard Deviation", StatisticalSeverity.HIGH, 70.0,
                    "rolling_std_diff", std_diff, 0.0, std_diff,
                    f"Transaction amount deviates by {std_diff:.2f} recent rolling standard deviations."
                ))

    def _detect_frequency_spike(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[StatisticalFinding]):
        if profile and profile.statistics:
            expected_daily = profile.statistics.avg_daily_txns
            if expected_daily > 0:
                day_ratio = fv.transactions_last_day / expected_daily
                if day_ratio > self.freq_spike_day_multiplier:
                    findings.append(self._create_finding(
                        fv, "S005", "Transaction Frequency Spike", StatisticalSeverity.HIGH, 80.0,
                        "transactions_last_day", float(fv.transactions_last_day), expected_daily, day_ratio,
                        f"Customer executed {fv.transactions_last_day} transactions today, which is {day_ratio:.1f}x their daily average."
                    ))

    def _detect_velocity_spike(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[StatisticalFinding]):
        if profile and profile.statistics:
            # Expected hourly velocity based on daily avg
            expected_hourly = profile.statistics.avg_daily_txns / 24.0
            if expected_hourly > 0:
                hour_ratio = fv.transactions_last_hour / expected_hourly
                if hour_ratio > self.velocity_spike_threshold and fv.transactions_last_hour >= 3:
                    findings.append(self._create_finding(
                        fv, "S006", "Velocity Spike", StatisticalSeverity.CRITICAL, 90.0,
                        "transactions_last_hour", float(fv.transactions_last_hour), expected_hourly, hour_ratio,
                        f"Detected rapid acceleration: {fv.transactions_last_hour} transactions in the last hour vs expected {expected_hourly:.2f}."
                    ))

    def _detect_gap_outlier(self, fv: FeatureVector, profile: Optional[BehaviourProfile], findings: List[StatisticalFinding]):
        if fv.time_since_previous_transaction > 0 and fv.average_gap_between_transactions > 0:
            # We are looking for unusually short gaps (e.g. burst activity)
            gap_ratio = fv.time_since_previous_transaction / fv.average_gap_between_transactions
            if gap_ratio < self.time_gap_outlier_threshold:
                findings.append(self._create_finding(
                    fv, "S007", "Time Gap Outlier", StatisticalSeverity.MEDIUM, 60.0,
                    "time_since_previous_transaction", fv.time_since_previous_transaction, 
                    fv.average_gap_between_transactions, 1.0 / gap_ratio if gap_ratio > 0 else 0,
                    f"Time gap since last transaction ({fv.time_since_previous_transaction:.2f} hrs) is unusually short compared to average ({fv.average_gap_between_transactions:.2f} hrs)."
                ))

    def _detect_behaviour_deviation(self, fv: FeatureVector, findings: List[StatisticalFinding]):
        if fv.behaviour_deviation_score > self.behaviour_deviation_threshold:
            findings.append(self._create_finding(
                fv, "S008", "Behaviour Deviation", StatisticalSeverity.HIGH, 75.0,
                "behaviour_deviation_score", fv.behaviour_deviation_score, 0.0, fv.behaviour_deviation_score,
                f"Composite statistical behaviour deviation score of {fv.behaviour_deviation_score:.2f} indicates abnormal activity."
            ))

    def _detect_historical_range_violation(self, fv: FeatureVector, findings: List[StatisticalFinding]):
        if fv.historical_max_amount > 0 and fv.transaction_amount > fv.historical_max_amount:
            diff = fv.transaction_amount - fv.historical_max_amount
            findings.append(self._create_finding(
                fv, "S009", "Historical Range Violation", StatisticalSeverity.HIGH, 85.0,
                "transaction_amount", fv.transaction_amount, fv.historical_max_amount, diff,
                f"Transaction amount ({fv.transaction_amount:.2f}) exceeds historical maximum ({fv.historical_max_amount:.2f})."
            ))
        elif fv.historical_min_amount > 0 and fv.transaction_amount < fv.historical_min_amount:
            # We only really care if they usually transact large amounts, but let's log the violation
            # Maybe LOW severity for minimum violations unless it's a micro-deposit structuring pattern
            diff = fv.historical_min_amount - fv.transaction_amount
            findings.append(self._create_finding(
                fv, "S009", "Historical Range Violation", StatisticalSeverity.LOW, 30.0,
                "transaction_amount", fv.transaction_amount, fv.historical_min_amount, diff,
                f"Transaction amount ({fv.transaction_amount:.2f}) is below historical minimum ({fv.historical_min_amount:.2f})."
            ))

    def _detect_composite_outlier(self, fv: FeatureVector, findings: List[StatisticalFinding]):
        high_critical_count = sum(1 for f in findings if f.severity in (StatisticalSeverity.HIGH, StatisticalSeverity.CRITICAL))
        if high_critical_count >= self.composite_trigger_threshold:
            findings.append(self._create_finding(
                fv, "S010", "Composite Statistical Outlier", StatisticalSeverity.CRITICAL, 95.0,
                "high_severity_findings", float(high_critical_count), 0.0, float(high_critical_count),
                f"Transaction triggered {high_critical_count} simultaneous HIGH/CRITICAL statistical anomalies."
            ))
