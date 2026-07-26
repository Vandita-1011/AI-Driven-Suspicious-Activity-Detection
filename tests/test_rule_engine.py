# pyrefly: ignore [missing-import]
import pytest

from src.features.feature_models import FeatureVector
from src.profiling.profile_models import BehaviourProfile, CustomerMetadata, BehaviourStatistics, BehaviourFlags
from src.engines.rule_engine import RuleEngine
from src.engines.rule_models import RuleHit, RuleSeverity


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
        avg_daily_txns=1.0, avg_weekly_txns=5.0, avg_monthly_txns=20.0, avg_txn_gap_days=1.0,
        preferred_hour=10, most_active_weekday=1, most_active_month=1, business_hours_ratio=0.9,
        weekend_ratio=0.1, cash_withdrawal_ratio=0.1, deposit_ratio=0.1, transfer_ratio=0.8,
        unique_beneficiaries=2, unique_accounts=1, unique_countries=1, unique_devices=1, unique_channels=1,
        most_common_beneficiary="BEN1", most_common_channel="MOBILE", most_common_txn_type="TRANSFER"
    )
    flags = BehaviourFlags(
        salary_account=False, business_account=False, frequent_transfer_user=False,
        cash_intensive_customer=False, dormant_customer=True, high_activity_customer=False,
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
        
        transactions_last_hour=1, transactions_last_day=1, transactions_last_week=3, 
        amount_last_day=105.0, amount_last_week=305.0, rolling_transaction_count=1, 
        rolling_average_amount=105.0, rolling_std_amount=0.0, average_gap_between_transactions=1.0, 
        time_since_previous_transaction=24.0,
        
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
def high_risk_feature_vector():
    # A vector that triggers almost everything
    return FeatureVector(
        transaction_id="TXN2", customer_id="CUST1", account_id="ACC1", timestamp="2024-01-01T02:00:00",
        
        transaction_amount=9500.0, customer_average_amount=100.0, customer_median_amount=80.0, 
        customer_std_amount=20.0, amount_difference=9400.0, amount_ratio_to_average=95.0, 
        amount_z_score=470.0, amount_percentile=1.0, historical_max_amount=500.0, 
        historical_min_amount=10.0, large_transaction_flag=True,
        
        transactions_last_hour=6, transactions_last_day=20, transactions_last_week=25, 
        amount_last_day=9500.0, amount_last_week=9500.0, rolling_transaction_count=20, 
        rolling_average_amount=475.0, rolling_std_amount=50.0, average_gap_between_transactions=0.1, 
        time_since_previous_transaction=0.05,
        
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
    engine = RuleEngine()
    hits = engine.run(empty_features, {})
    assert len(hits) == 0


def test_normal_transaction(normal_feature_vector, sample_profile):
    engine = RuleEngine()
    hits = engine.run([normal_feature_vector], {"CUST1": sample_profile})
    # Shouldn't trigger any rules ideally, or maybe just a few low severity anomalies
    assert len(hits) == 0


def test_high_risk_transaction(high_risk_feature_vector, sample_profile):
    engine = RuleEngine()
    hits = engine.run([high_risk_feature_vector], {"CUST1": sample_profile})
    
    assert len(hits) > 10
    
    triggered_rules = {hit.rule_id for hit in hits}
    assert "R001" in triggered_rules  # Large Transaction
    assert "R002" in triggered_rules  # Large Z-Score
    assert "R003" in triggered_rules  # Rapid Velocity
    assert "R004" in triggered_rules  # Behaviour Deviation
    assert "R005" in triggered_rules  # Outside Business Hours
    assert "R009" in triggered_rules  # New Device
    assert "R013" in triggered_rules  # High Risk Country
    assert "R014" in triggered_rules  # PEP Customer
    assert "R015" in triggered_rules  # Previous SAR
    assert "R016" in triggered_rules  # Dormant Reactivation
    assert "R017" in triggered_rules  # Structuring Indicator (amount = 9500)
    assert "R020" in triggered_rules  # Multiple High Risk Signals

    # Ensure severity is mapped properly
    r013_hit = next(hit for hit in hits if hit.rule_id == "R013")
    assert r013_hit.severity == RuleSeverity.CRITICAL

    r020_hit = next(hit for hit in hits if hit.rule_id == "R020")
    assert r020_hit.severity == RuleSeverity.CRITICAL


def test_missing_profile(high_risk_feature_vector):
    engine = RuleEngine()
    # Missing profile shouldn't crash, but won't trigger profile-dependent rules
    hits = engine.run([high_risk_feature_vector], {})
    
    triggered_rules = {hit.rule_id for hit in hits}
    # It should still trigger rules that don't depend on the profile
    assert "R001" in triggered_rules
    assert "R013" in triggered_rules
    assert "R016" not in triggered_rules # Requires dormant profile flag
