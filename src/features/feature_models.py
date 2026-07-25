from dataclasses import dataclass, asdict
from typing import Any, Dict


@dataclass
class FeatureVector:
    """
    Core feature vector for a single transaction.
    """
    transaction_id: str
    customer_id: str
    account_id: str
    timestamp: Any

    # 1. Amount Features
    transaction_amount: float
    customer_average_amount: float
    customer_median_amount: float
    customer_std_amount: float
    amount_difference: float
    amount_ratio_to_average: float
    amount_z_score: float
    amount_percentile: float
    historical_max_amount: float
    historical_min_amount: float
    large_transaction_flag: bool

    # 2. Velocity Features
    transactions_last_hour: int
    transactions_last_day: int
    transactions_last_week: int
    amount_last_day: float
    amount_last_week: float
    rolling_transaction_count: int
    rolling_average_amount: float
    rolling_std_amount: float
    average_gap_between_transactions: float
    time_since_previous_transaction: float

    # 3. Behaviour Deviation Features
    outside_business_hours: bool
    outside_preferred_hour: bool
    unusual_weekday: bool
    unusual_month: bool
    amount_deviation_score: float
    frequency_deviation_score: float
    behaviour_deviation_score: float

    # 4. Relationship Features
    new_beneficiary: bool
    beneficiary_frequency: int
    beneficiary_amount_average: float
    beneficiary_amount_std: float
    beneficiary_transaction_count: int
    beneficiary_is_high_frequency: bool

    # 5. Device Features
    new_device: bool
    device_frequency: int
    device_switch_flag: bool
    unique_devices_last_30_days: int

    # 6. Channel Features
    new_channel: bool
    channel_frequency: int
    preferred_channel: str
    outside_preferred_channel: bool

    # 7. Geographic Features
    new_country: bool
    country_frequency: int
    cross_border_transaction: bool
    high_risk_country_flag: bool
    geographic_change: bool
    distance_from_previous_country: float

    # 8. Historical Customer Features
    account_age_days: int
    customer_age_group: str
    kyc_level: str
    pep_flag: bool
    previous_sar_count: int
    historical_average_amount: float

    def to_dict(self) -> Dict[str, Any]:
        """Converts FeatureVector into a dictionary."""
        return asdict(self)

