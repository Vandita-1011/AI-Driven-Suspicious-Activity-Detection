import pytest

from src.features.feature_models import FeatureVector
from src.profiling.profile_models import BehaviourProfile, CustomerMetadata, BehaviourStatistics, BehaviourFlags
from src.engines.pattern_engine import PatternEngine
from src.engines.pattern_models import PatternFinding, PatternSeverity


@pytest.fixture
def empty_features():
    return []


@pytest.fixture
def sample_profile():
    meta = CustomerMetadata(
        customer_id="CUST1", account_age_days=100, customer_age_group="18-30",
        kyc_level="HIGH", pep_status=False, high_risk_country_history=False, previous_sar_count=0
    )
    stats = BehaviourStatistics(
        avg_amount=100.0, median_amount=80.0, max_amount=500.0, min_amount=10.0, std_amount=20.0,
        avg_daily_txns=2.0, avg_weekly_txns=10.0, avg_monthly_txns=40.0, avg_txn_gap_days=0.5,
        preferred_hour=14, most_active_weekday=1, most_active_month=1, business_hours_ratio=0.95,
        weekend_ratio=0.01, cash_withdrawal_ratio=0.1, deposit_ratio=0.1, transfer_ratio=0.8,
        unique_beneficiaries=10, unique_accounts=1, unique_countries=3, unique_devices=1, unique_channels=1,
        most_common_beneficiary="BEN1", most_common_channel="MOBILE", most_common_txn_type="TRANSFER"
    )
    flags = BehaviourFlags(
        salary_account=False, business_account=False, frequent_transfer_user=True,
        cash_intensive_customer=True, dormant_customer=True, high_activity_customer=False,
        night_activity_customer=False, weekend_heavy_customer=False, international_customer=False,
        digital_first_customer=True
    )
    return BehaviourProfile(
        customer_id="CUST1", metadata=meta, statistics=stats, flags=flags,
        confidence_score=0.9, summary=""
    )


@pytest.fixture
def normal_feature_vector():
    return FeatureVector(
        transaction_id="TXN1", customer_id="CUST1", account_id="ACC1", timestamp="2024-01-01T14:30:00",
        
        transaction_amount=105.0, customer_average_amount=100.0, customer_median_amount=80.0, 
        customer_std_amount=20.0, amount_difference=5.0, amount_ratio_to_average=1.05, 
        amount_z_score=0.25, amount_percentile=0.6, historical_max_amount=500.0, 
        historical_min_amount=10.0, large_transaction_flag=False,
        
        transactions_last_hour=1, transactions_last_day=2, transactions_last_week=10, 
        amount_last_day=105.0, amount_last_week=1005.0, rolling_transaction_count=2, 
        rolling_average_amount=100.0, rolling_std_amount=15.0, average_gap_between_transactions=12.0, 
        time_since_previous_transaction=12.0,
        
        outside_business_hours=False, outside_preferred_hour=False, unusual_weekday=False, 
        unusual_month=False, amount_deviation_score=0.05, frequency_deviation_score=0.1, 
        behaviour_deviation_score=0.1,
        
        new_beneficiary=False, beneficiary_frequency=5, beneficiary_amount_average=100.0, 
        beneficiary_amount_std=10.0, beneficiary_transaction_count=5, beneficiary_is_high_frequency=False,
        
        new_device=False, device_frequency=10, device_switch_flag=False, unique_devices_last_30_days=1,
        
        new_channel=False, channel_frequency=10, preferred_channel="MOBILE", outside_preferred_channel=False,
        
        new_country=False, country_frequency=10, cross_border_transaction=False, high_risk_country_flag=False, 
        geographic_change=False, distance_from_previous_country=0.0,
        
        account_age_days=100, customer_age_group="18-30", kyc_level="HIGH", pep_flag=False, 
        previous_sar_count=0, historical_average_amount=100.0
    )


@pytest.fixture
def high_risk_pattern_vector():
    # A vector that triggers almost every pattern
    return FeatureVector(
        transaction_id="TXN2", customer_id="CUST1", account_id="ACC1", timestamp="2024-01-01T02:00:00",
        
        transaction_amount=9500.0, customer_average_amount=100.0, customer_median_amount=80.0, 
        customer_std_amount=20.0, amount_difference=9400.0, amount_ratio_to_average=50.0, 
        amount_z_score=42.5, amount_percentile=0.99, historical_max_amount=500.0, 
        historical_min_amount=10.0, large_transaction_flag=True,
        
        transactions_last_hour=15, transactions_last_day=20, transactions_last_week=10, 
        amount_last_day=95000.0, amount_last_week=95000.0, rolling_transaction_count=20, 
        rolling_average_amount=100.0, rolling_std_amount=20.0, average_gap_between_transactions=12.0, 
        time_since_previous_transaction=0.05,
        
        outside_business_hours=True, outside_preferred_hour=True, unusual_weekday=True, 
        unusual_month=False, amount_deviation_score=0.9, frequency_deviation_score=0.8, 
        behaviour_deviation_score=0.9,
        
        new_beneficiary=True, beneficiary_frequency=1, beneficiary_amount_average=950.0, 
        beneficiary_amount_std=0.0, beneficiary_transaction_count=20, beneficiary_is_high_frequency=True,
        
        new_device=True, device_frequency=1, device_switch_flag=True, unique_devices_last_30_days=5,
        
        new_channel=True, channel_frequency=1, preferred_channel="MOBILE", outside_preferred_channel=True,
        
        new_country=True, country_frequency=1, cross_border_transaction=True, high_risk_country_flag=True, 
        geographic_change=True, distance_from_previous_country=500.0,
        
        account_age_days=100, customer_age_group="18-30", kyc_level="HIGH", pep_flag=False, 
        previous_sar_count=0, historical_average_amount=100.0
    )


def test_empty_dataset(empty_features):
    engine = PatternEngine()
    findings = engine.run(empty_features, {})
    assert len(findings) == 0


def test_normal_transaction(normal_feature_vector, sample_profile):
    engine = PatternEngine()
    findings = engine.run([normal_feature_vector], {"CUST1": sample_profile})
    # Should not trigger any AML patterns
    assert len(findings) == 0


def test_high_risk_patterns(high_risk_pattern_vector, sample_profile):
    engine = PatternEngine()
    findings = engine.run([high_risk_pattern_vector], {"CUST1": sample_profile})
    
    triggered_patterns = {f.pattern_id for f in findings}
    
    assert "P001" in triggered_patterns  # Structuring (amount 9500)
    assert "P002" in triggered_patterns  # Rapid movement (gap 0.05, hr 15)
    assert "P003" in triggered_patterns  # Layering (txns 20, unique ben > 5)
    assert "P004" in triggered_patterns  # Circular (ben_freq high, count > 10, gap < 1.0)
    assert "P005" in triggered_patterns  # Fan-Out (hr >= 5, new ben)
    assert "P006" in triggered_patterns  # Fan-In (Not explicitly triggered by this vector due to amount deviation score)
    assert "P007" in triggered_patterns  # Dormant (dormant flag + high velocity)
    assert "P008" in triggered_patterns  # Cross-Border Layering (cross border, geo change, high vel)
    assert "P009" in triggered_patterns  # High-Risk Geo (high risk flag)
    assert "P010" in triggered_patterns  # Cash Intensive (cash intensive flag + large txn)
    assert "P011" in triggered_patterns  # Shared Device (device switch + > 3 unique)
    assert "P012" in triggered_patterns  # Shared Beneficiary (high freq + count > 15)
    assert "P013" in triggered_patterns  # Burst Activity (hr > 8, gap < 0.1)
    assert "P014" in triggered_patterns  # Escalating Amounts (ratio 50, pct 0.99)
    assert "P015" in triggered_patterns  # Composite AML Pattern (3+ High/Crit)

    # Verify severity
    p015_finding = next(f for f in findings if f.pattern_id == "P015")
    assert p015_finding.severity == PatternSeverity.CRITICAL

def test_missing_profile_handling(high_risk_pattern_vector):
    engine = PatternEngine()
    findings = engine.run([high_risk_pattern_vector], {})
    
    triggered_patterns = {f.pattern_id for f in findings}
    
    # Needs profile statistics or flags, so shouldn't trigger
    assert "P003" not in triggered_patterns  # Needs profile for unique beneficiaries
    assert "P007" not in triggered_patterns  # Needs dormant flag
    assert "P010" not in triggered_patterns  # Needs cash intensive flag
    
    # Doesn't need profile, should still trigger
    assert "P001" in triggered_patterns
    assert "P005" in triggered_patterns
    assert "P009" in triggered_patterns
    assert "P011" in triggered_patterns
    assert "P013" in triggered_patterns
    assert "P014" in triggered_patterns
