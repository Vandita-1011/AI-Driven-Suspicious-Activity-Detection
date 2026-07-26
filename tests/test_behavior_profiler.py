# pyrefly: ignore [missing-import]
import pytest
import pandas as pd
# pyrefly: ignore [missing-import]
import numpy as np

from src.constants.column_names import TxnCols, CustomerCols, AccountCols, ComputedCols
from src.profiling.behaviour_profiler import BehaviourProfiler
from src.profiling.profile_models import BehaviourProfile, BehaviourFlags, BehaviourStatistics, CustomerMetadata


@pytest.fixture
def empty_df():
    return pd.DataFrame()


@pytest.fixture
def single_txn_df():
    return pd.DataFrame({
        TxnCols.CUSTOMER_ID: ["CUST001"],
        TxnCols.ACCOUNT_ID: ["ACC001"],
        TxnCols.TRANSACTION_ID: ["TXN001"],
        TxnCols.AMOUNT: [500.0],
        TxnCols.TIMESTAMP: [pd.to_datetime("2024-01-01 10:00:00", utc=True)],
        TxnCols.TRANSACTION_TYPE: ["TRANSFER"],
        TxnCols.CHANNEL: ["MOBILE"],
        TxnCols.COUNTERPARTY_ACCOUNT_ID: ["BENEF001"],
        TxnCols.COUNTERPARTY_COUNTRY: ["US"],
        TxnCols.DEVICE_ID: ["DEV001"],
        ComputedCols.HOUR_OF_DAY: [10],
        ComputedCols.DAY_OF_WEEK: [0],
        'transaction_month': [1],
        'transaction_day': [1],
        'transaction_year': [2024],
        'is_business_hours': [True],
        ComputedCols.IS_WEEKEND: [False],
        'transaction_date': [pd.to_datetime("2024-01-01").date()],
        'account_age_days': [30],
        'customer_age_group': ["31-50"],
        CustomerCols.KYC_LEVEL: ["VERIFIED"],
        ComputedCols.IS_PEP: [False],
        'is_high_risk_country_history': [False]
    })


@pytest.fixture
def many_txns_df():
    n = 60
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=n, freq="12h", tz="UTC")
    return pd.DataFrame({
        TxnCols.CUSTOMER_ID: ["CUST002"] * n,
        TxnCols.ACCOUNT_ID: ["ACC002"] * n,
        TxnCols.TRANSACTION_ID: [f"TXN{i:03d}" for i in range(n)],
        TxnCols.AMOUNT: np.random.uniform(50, 500, size=n),
        TxnCols.TIMESTAMP: dates,
        TxnCols.TRANSACTION_TYPE: np.random.choice(["TRANSFER", "CASH_WITHDRAWAL", "DEPOSIT"], size=n),
        TxnCols.CHANNEL: np.random.choice(["MOBILE", "WEB"], size=n),
        TxnCols.COUNTERPARTY_ACCOUNT_ID: [f"BENEF{i%5:03d}" for i in range(n)],
        TxnCols.COUNTERPARTY_COUNTRY: np.random.choice(["US", "UK", "CA"], size=n),
        TxnCols.DEVICE_ID: ["DEV002"] * n,
        ComputedCols.HOUR_OF_DAY: dates.hour,
        ComputedCols.DAY_OF_WEEK: dates.dayofweek,
        'transaction_month': dates.month,
        'transaction_day': dates.day,
        'transaction_year': dates.year,
        'is_business_hours': (dates.hour >= 9) & (dates.hour <= 17),
        ComputedCols.IS_WEEKEND: dates.dayofweek >= 5,
        'transaction_date': dates.date,
        'account_age_days': [200] * n,
        'customer_age_group': ["31-50"] * n,
        CustomerCols.KYC_LEVEL: ["HIGH"] * n,
        ComputedCols.IS_PEP: [False] * n,
        'is_high_risk_country_history': [False] * n
    })


def test_empty_dataframe(empty_df):
    profiler = BehaviourProfiler(empty_df)
    profiler.build_all_profiles()
    assert profiler.get_profile("CUST001") is None


def test_single_transaction_profile(single_txn_df):
    profiler = BehaviourProfiler(single_txn_df)
    profiler.build_all_profiles()
    
    profile = profiler.get_profile("CUST001")
    assert profile is not None
    assert profile.customer_id == "CUST001"
    assert profile.statistics.avg_amount == 500.0
    assert profile.statistics.min_amount == 500.0
    assert profile.statistics.max_amount == 500.0
    assert profile.statistics.std_amount == 0.0
    assert profile.statistics.unique_beneficiaries == 1
    # Confidence score for 1 txn should be low (< 0.5)
    assert 0.0 <= profile.confidence_score <= 0.5


def test_many_transactions_profile(many_txns_df):
    profiler = BehaviourProfiler(many_txns_df)
    profiler.build_all_profiles()
    
    profile = profiler.get_profile("CUST002")
    assert profile is not None
    assert profile.customer_id == "CUST002"
    assert profile.statistics.avg_daily_txns > 0
    assert profile.statistics.unique_countries == 3
    # Confidence score for 60 txns and 200 days account age should be high (> 0.7)
    assert profile.confidence_score >= 0.7


def test_behaviour_flags(many_txns_df):
    profiler = BehaviourProfiler(many_txns_df)
    profiler.build_all_profiles()
    
    profile = profiler.get_profile("CUST002")
    assert isinstance(profile.flags, BehaviourFlags)
    # 3 countries used -> international customer
    assert profile.flags.international_customer is True
    # Mobile/Web -> digital first customer
    assert profile.flags.digital_first_customer is True


def test_deterministic_summary(single_txn_df):
    profiler = BehaviourProfiler(single_txn_df)
    profiler.build_all_profiles()
    
    profile = profiler.get_profile("CUST001")
    assert isinstance(profile.summary, str)
    assert len(profile.summary) > 0
    assert "Customer" in profile.summary
    assert "500.00" in profile.summary
