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

    def to_dict(self) -> Dict[str, Any]:
        """Converts FeatureVector into a dictionary."""
        return asdict(self)
