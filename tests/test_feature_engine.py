# pyrefly: ignore [missing-import]
import pytest
import pandas as pd
# pyrefly: ignore [missing-import]
import numpy as np

from src.constants.column_names import TxnCols, ComputedCols
from src.features.feature_engine import FeatureEngine
from src.features.feature_models import FeatureVector
from src.profiling.profile_models import BehaviourProfile, BehaviourStatistics, CustomerMetadata, BehaviourFlags


@pytest.fixture
def empty_df():
    return pd.DataFrame()


@pytest.fixture
def single_txn_df():
    return pd.DataFrame({
        TxnCols.TRANSACTION_ID: ["TXN100"],
        TxnCols.CUSTOMER_ID: ["CUST100"],
        TxnCols.ACCOUNT_ID: ["ACC100"],
        TxnCols.TIMESTAMP: [pd.to_datetime("2024-01-01 10:00:00", utc=True)],
        TxnCols.AMOUNT: [500.0],
        ComputedCols.HOUR_OF_DAY: [10],
        ComputedCols.DAY_OF_WEEK: [0],
        'transaction_month': [1],
        'is_business_hours': [True]
    })


@pytest.fixture
def sample_profiles():
    meta = CustomerMetadata(
        customer_id="CUST100", account_age_days=100, customer_age_group="18-30",
        kyc_level="HIGH", pep_status=False, high_risk_country_history=False, previous_sar_count=0
    )
    stats = BehaviourStatistics(
        avg_amount=200.0, median_amount=150.0, max_amount=1000.0, min_amount=10.0, std_amount=50.0,
        avg_daily_txns=2.0, avg_weekly_txns=14.0, avg_monthly_txns=60.0, avg_txn_gap_days=0.5,
        preferred_hour=14, most_active_weekday=2, most_active_month=5, business_hours_ratio=0.8,
        weekend_ratio=0.2, cash_withdrawal_ratio=0.1, deposit_ratio=0.2, transfer_ratio=0.7,
        unique_beneficiaries=5, unique_accounts=1, unique_countries=1, unique_devices=1, unique_channels=1,
        most_common_beneficiary="BEN1", most_common_channel="MOBILE", most_common_txn_type="TRANSFER"
    )
    flags = BehaviourFlags(
        salary_account=False, business_account=False, frequent_transfer_user=True,
        cash_intensive_customer=False, dormant_customer=False, high_activity_customer=False,
        night_activity_customer=False, weekend_heavy_customer=False, international_customer=False,
        digital_first_customer=True
    )
    prof = BehaviourProfile(
        customer_id="CUST100", metadata=meta, statistics=stats, flags=flags,
        confidence_score=0.8, summary="Sample summary"
    )
    return {"CUST100": prof}


@pytest.fixture
def large_txn_df():
    n = 100
    dates = pd.date_range("2024-01-01", periods=n, freq="30min", tz="UTC")
    return pd.DataFrame({
        TxnCols.TRANSACTION_ID: [f"TXN{i:03d}" for i in range(n)],
        TxnCols.CUSTOMER_ID: ["CUST100"] * n,
        TxnCols.ACCOUNT_ID: ["ACC100"] * n,
        TxnCols.TIMESTAMP: dates,
        TxnCols.AMOUNT: np.linspace(100, 1000, n),
        ComputedCols.HOUR_OF_DAY: dates.hour,
        ComputedCols.DAY_OF_WEEK: dates.dayofweek,
        'transaction_month': dates.month,
        'is_business_hours': (dates.hour >= 9) & (dates.hour <= 17)
    })


def test_empty_dataset(empty_df):
    engine = FeatureEngine()
    result = engine.run(empty_df)
    assert result.empty


def test_single_transaction_features(single_txn_df, sample_profiles):
    engine = FeatureEngine()
    result = engine.run(single_txn_df, sample_profiles)

    assert not result.empty
    assert len(result) == 1

    # Check amount features
    assert result['transaction_amount'].iloc[0] == 500.0
    assert result['customer_average_amount'].iloc[0] == 200.0
    assert result['amount_difference'].iloc[0] == 300.0
    assert result['amount_z_score'].iloc[0] > 0

    # Check velocity features
    assert result['transactions_last_hour'].iloc[0] == 1
    assert result['transactions_last_day'].iloc[0] == 1

    # Check behaviour deviation features
    # preferred_hour=14, current=10 -> outside preferred hour
    assert result['outside_preferred_hour'].iloc[0] == True


def test_large_dataset_features(large_txn_df, sample_profiles):
    engine = FeatureEngine()
    result = engine.run(large_txn_df, sample_profiles)

    assert len(result) == 100

    # Velocity rollings should increase over time
    assert result['transactions_last_hour'].max() >= 2
    assert result['transactions_last_day'].max() > 10

    # Test conversion to FeatureVectors
    vectors = engine.run_to_vectors(large_txn_df, sample_profiles)
    assert len(vectors) == 100
    assert isinstance(vectors[0], FeatureVector)
    assert vectors[0].transaction_amount == 100.0


def test_advanced_feature_groups(sample_profiles):
    engine = FeatureEngine()
    df = pd.DataFrame({
        TxnCols.TRANSACTION_ID: ["T1", "T2"],
        TxnCols.CUSTOMER_ID: ["CUST100", "CUST100"],
        TxnCols.ACCOUNT_ID: ["ACC100", "ACC100"],
        TxnCols.TIMESTAMP: [
            pd.to_datetime("2024-01-01 10:00:00", utc=True),
            pd.to_datetime("2024-01-01 11:00:00", utc=True)
        ],
        TxnCols.AMOUNT: [100.0, 200.0],
        TxnCols.COUNTERPARTY_ACCOUNT_ID: ["BEN1", "BEN2"],
        TxnCols.DEVICE_ID: ["DEV1", "DEV2"],
        TxnCols.CHANNEL: ["MOBILE", "WEB"],
        TxnCols.COUNTERPARTY_COUNTRY: ["US", "IR"],
        'location_country': ["US", "US"],
        'account_age_days': [120, 120],
        'customer_age_group': ["18-30", "18-30"],
        'kyc_level': ["HIGH", "HIGH"],
        ComputedCols.IS_PEP: [False, False]
    })

    result = engine.run(df, sample_profiles)

    # 1. Relationship Features
    assert result['new_beneficiary'].iloc[0] == True
    assert result['new_beneficiary'].iloc[1] == True

    # 2. Device Features
    assert result['new_device'].iloc[0] == True
    assert result['device_switch_flag'].iloc[1] == True

    # 3. Channel Features
    assert result['preferred_channel'].iloc[0] == "MOBILE"
    assert result['outside_preferred_channel'].iloc[1] == True

    # 4. Geographic Features
    assert result['cross_border_transaction'].iloc[1] == True
    assert result['high_risk_country_flag'].iloc[1] == True  # IR is high risk
    assert result['geographic_change'].iloc[1] == True

    # 5. Historical Features
    assert result['account_age_days'].iloc[0] == 120
    assert result['customer_age_group'].iloc[0] == "18-30"

    # Test complete FeatureVector mapping
    vectors = engine.run_to_vectors(df, sample_profiles)
    assert len(vectors) == 2
    assert vectors[1].high_risk_country_flag == True
    assert vectors[1].device_switch_flag == True

