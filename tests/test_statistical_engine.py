import pytest

from src.features.feature_models import FeatureVector
from src.profiling.profile_models import BehaviourProfile, CustomerMetadata, BehaviourStatistics, BehaviourFlags
from src.engines.statistical_engine import StatisticalEngine
from src.engines.statistical_models import StatisticalFinding, StatisticalSeverity


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
        preferred_hour=10, most_active_weekday=1, most_active_month=1, business_hours_ratio=0.9,
        weekend_ratio=0.1, cash_withdrawal_ratio=0.1, deposit_ratio=0.1, transfer_ratio=0.8,
        unique_beneficiaries=2, unique_accounts=1, unique_countries=1, unique_devices=1, unique_channels=1,
        most_common_beneficiary="BEN1", most_common_channel="MOBILE", most_common_txn_type="TRANSFER"
    )
    flags = BehaviourFlags(
        salary_account=False, business_account=False, frequent_transfer_user=False,
        cash_intensive_customer=False, dormant_customer=False, high_activity_customer=False,
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
        transaction_id="TXN1", customer_id="CUST1", account_id="ACC1", timestamp="2024-01-01T10:00:00",
        
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
def high_outlier_feature_vector():
    # A vector that triggers statistical anomalies
    return FeatureVector(
        transaction_id="TXN2", customer_id="CUST1", account_id="ACC1", timestamp="2024-01-01T02:00:00",
        
        transaction_amount=9500.0, customer_average_amount=100.0, customer_median_amount=80.0, 
        customer_std_amount=20.0, amount_difference=9400.0, amount_ratio_to_average=95.0, 
        amount_z_score=470.0, amount_percentile=1.0, historical_max_amount=500.0, 
        historical_min_amount=10.0, large_transaction_flag=True,
        
        transactions_last_hour=10, transactions_last_day=20, transactions_last_week=25, 
        amount_last_day=9500.0, amount_last_week=9500.0, rolling_transaction_count=20, 
        rolling_average_amount=100.0, rolling_std_amount=20.0, average_gap_between_transactions=12.0, 
        time_since_previous_transaction=0.01, # extremely short gap
        
        outside_business_hours=True, outside_preferred_hour=True, unusual_weekday=True, 
        unusual_month=True, amount_deviation_score=1.0, frequency_deviation_score=1.0, 
        behaviour_deviation_score=0.9,
        
        new_beneficiary=True, beneficiary_frequency=1, beneficiary_amount_average=9500.0, 
        beneficiary_amount_std=0.0, beneficiary_transaction_count=1, beneficiary_is_high_frequency=False,
        
        new_device=True, device_frequency=1, device_switch_flag=True, unique_devices_last_30_days=3,
        
        new_channel=True, channel_frequency=1, preferred_channel="MOBILE", outside_preferred_channel=True,
        
        new_country=True, country_frequency=1, cross_border_transaction=True, high_risk_country_flag=True, 
        geographic_change=True, distance_from_previous_country=500.0,
        
        account_age_days=100, customer_age_group="18-30", kyc_level="HIGH", pep_flag=True, 
        previous_sar_count=2, historical_average_amount=100.0
    )


def test_empty_dataset(empty_features):
    engine = StatisticalEngine()
    findings = engine.run(empty_features, {})
    assert len(findings) == 0


def test_normal_transaction(normal_feature_vector, sample_profile):
    engine = StatisticalEngine()
    findings = engine.run([normal_feature_vector], {"CUST1": sample_profile})
    # Should not trigger any statistical anomalies
    assert len(findings) == 0


def test_high_outlier_transaction(high_outlier_feature_vector, sample_profile):
    engine = StatisticalEngine()
    findings = engine.run([high_outlier_feature_vector], {"CUST1": sample_profile})
    
    assert len(findings) > 5
    
    triggered_findings = {f.finding_id for f in findings}
    assert "S001" in triggered_findings  # Amount Z-Score
    assert "S002" in triggered_findings  # Amount Percentile
    assert "S003" in triggered_findings  # Rolling Mean Deviation
    assert "S004" in triggered_findings  # Rolling Std Deviation
    assert "S005" in triggered_findings  # Transaction Frequency Spike
    assert "S006" in triggered_findings  # Velocity Spike
    assert "S007" in triggered_findings  # Time Gap Outlier
    assert "S008" in triggered_findings  # Behaviour Deviation
    assert "S009" in triggered_findings  # Historical Range Violation
    assert "S010" in triggered_findings  # Composite Statistical Outlier

    # Ensure severity is mapped properly
    s010_finding = next(f for f in findings if f.finding_id == "S010")
    assert s010_finding.severity == StatisticalSeverity.CRITICAL

    s001_finding = next(f for f in findings if f.finding_id == "S001")
    assert s001_finding.severity == StatisticalSeverity.HIGH # z-score 470 is massive


def test_missing_profile_handling(high_outlier_feature_vector):
    engine = StatisticalEngine()
    findings = engine.run([high_outlier_feature_vector], {})
    
    triggered_findings = {f.finding_id for f in findings}
    # It should still trigger findings that don't depend on the profile
    assert "S001" in triggered_findings
    assert "S002" in triggered_findings
    
    # Velocity spike relies on profile.statistics, so it shouldn't trigger
    assert "S006" not in triggered_findings
