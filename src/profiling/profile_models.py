from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


@dataclass
class CustomerMetadata:
    customer_id: str
    account_age_days: int
    customer_age_group: str
    kyc_level: str
    pep_status: bool
    high_risk_country_history: bool
    previous_sar_count: int


@dataclass
class BehaviourStatistics:
    # Amount stats
    avg_amount: float
    median_amount: float
    max_amount: float
    min_amount: float
    std_amount: float

    # Frequency stats
    avg_daily_txns: float
    avg_weekly_txns: float
    avg_monthly_txns: float
    avg_txn_gap_days: float

    # Temporal preferences
    preferred_hour: int
    most_active_weekday: int
    most_active_month: int
    business_hours_ratio: float
    weekend_ratio: float

    # Type ratios
    cash_withdrawal_ratio: float
    deposit_ratio: float
    transfer_ratio: float

    # Diversity metrics
    unique_beneficiaries: int
    unique_accounts: int
    unique_countries: int
    unique_devices: int
    unique_channels: int

    # Baseline contextual
    most_common_beneficiary: str
    most_common_channel: str
    most_common_txn_type: str


@dataclass
class BehaviourFlags:
    salary_account: bool
    business_account: bool
    frequent_transfer_user: bool
    cash_intensive_customer: bool
    dormant_customer: bool
    high_activity_customer: bool
    night_activity_customer: bool
    weekend_heavy_customer: bool
    international_customer: bool
    digital_first_customer: bool


@dataclass
class BehaviourProfile:
    """
    Comprehensive behavioural profile for a customer.
    """
    customer_id: str
    metadata: CustomerMetadata
    statistics: BehaviourStatistics
    flags: BehaviourFlags
    confidence_score: float
    summary: str
    timestamp_generated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def features(self) -> dict[str, Any]:
        """Backward compatibility for BehaviourEngine which expects profile.features"""
        return {
            "avg_amount": self.statistics.avg_amount,
            "total_transactions": self.statistics.avg_daily_txns * 30  # approx
        }

