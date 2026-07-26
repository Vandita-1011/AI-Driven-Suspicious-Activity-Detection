import os
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
import numpy as np

from src.features.feature_models import FeatureVector
from src.engines.ml_engine import MLEngine
from src.engines.ml_builder import MLBuilder
from src.engines.ml_models import MLFinding


@pytest.fixture
def empty_features():
    return []


@pytest.fixture
def training_features():
    # Generate 50 normal-looking feature vectors
    features = []
    for i in range(50):
        features.append(FeatureVector(
            transaction_id=f"TXN_{i}", customer_id="CUST1", account_id="ACC1", timestamp="2024-01-01T10:00:00",
            
            amount_z_score=np.random.normal(0, 0.5), 
            amount_ratio_to_average=np.random.normal(1.0, 0.1),
            transactions_last_hour=np.random.randint(1, 3), 
            transactions_last_day=np.random.randint(1, 5),
            rolling_average_amount=100.0, 
            rolling_std_amount=10.0,
            behaviour_deviation_score=np.random.uniform(0.0, 0.2), 
            frequency_deviation_score=np.random.uniform(0.0, 0.2),
            time_since_previous_transaction=np.random.uniform(10.0, 48.0),
            beneficiary_frequency=5, device_frequency=10, channel_frequency=10, country_frequency=10,
            historical_average_amount=100.0, historical_max_amount=500.0, historical_min_amount=10.0,
            
            transaction_amount=100.0, customer_average_amount=100.0, customer_median_amount=80.0, 
            customer_std_amount=20.0, amount_difference=0.0, amount_percentile=0.5, large_transaction_flag=False,
            transactions_last_week=10, amount_last_day=100.0, amount_last_week=1000.0, rolling_transaction_count=2, 
            average_gap_between_transactions=24.0, outside_business_hours=False, outside_preferred_hour=False, 
            unusual_weekday=False, unusual_month=False, amount_deviation_score=0.1, new_beneficiary=False, 
            beneficiary_amount_average=100.0, beneficiary_amount_std=10.0, beneficiary_transaction_count=5, 
            beneficiary_is_high_frequency=False, new_device=False, device_switch_flag=False, 
            unique_devices_last_30_days=1, new_channel=False, preferred_channel="MOBILE", 
            outside_preferred_channel=False, new_country=False, cross_border_transaction=False, 
            high_risk_country_flag=False, geographic_change=False, distance_from_previous_country=0.0,
            account_age_days=100, customer_age_group="18-30", kyc_level="HIGH", pep_flag=False, 
            previous_sar_count=0
        ))
    return features


@pytest.fixture
def anomalous_feature_vector():
    # A vector that looks completely different
    return FeatureVector(
        transaction_id="TXN_ANOMALY", customer_id="CUST1", account_id="ACC1", timestamp="2024-01-01T10:00:00",
        
        amount_z_score=15.0, 
        amount_ratio_to_average=50.0,
        transactions_last_hour=50, 
        transactions_last_day=200,
        rolling_average_amount=100.0, 
        rolling_std_amount=10.0,
        behaviour_deviation_score=1.0, 
        frequency_deviation_score=1.0,
        time_since_previous_transaction=0.01,
        beneficiary_frequency=1, device_frequency=1, channel_frequency=1, country_frequency=1,
        historical_average_amount=100.0, historical_max_amount=500.0, historical_min_amount=10.0,
        
        transaction_amount=5000.0, customer_average_amount=100.0, customer_median_amount=80.0, 
        customer_std_amount=20.0, amount_difference=4900.0, amount_percentile=1.0, large_transaction_flag=True,
        transactions_last_week=250, amount_last_day=5000.0, amount_last_week=5000.0, rolling_transaction_count=20, 
        average_gap_between_transactions=24.0, outside_business_hours=True, outside_preferred_hour=True, 
        unusual_weekday=True, unusual_month=True, amount_deviation_score=1.0, new_beneficiary=True, 
        beneficiary_amount_average=5000.0, beneficiary_amount_std=0.0, beneficiary_transaction_count=1, 
        beneficiary_is_high_frequency=False, new_device=True, device_switch_flag=True, 
        unique_devices_last_30_days=5, new_channel=True, preferred_channel="MOBILE", 
        outside_preferred_channel=True, new_country=True, cross_border_transaction=True, 
        high_risk_country_flag=True, geographic_change=True, distance_from_previous_country=5000.0,
        account_age_days=100, customer_age_group="18-30", kyc_level="HIGH", pep_flag=True, 
        previous_sar_count=0
    )


@pytest.fixture
def tmp_config(tmp_path):
    model_path = os.path.join(tmp_path, "isolation_forest.joblib")
    scaler_path = os.path.join(tmp_path, "scaler.joblib")
    return {
        "ml_contamination": 0.05,
        "ml_model_path": model_path,
        "ml_scaler_path": scaler_path
    }


def test_empty_dataset():
    engine = MLEngine()
    findings = engine.run([])
    assert len(findings) == 0


def test_ml_training_and_prediction(training_features, anomalous_feature_vector, tmp_config):
    # 1. Train and save model implicitly via run()
    engine = MLEngine(config=tmp_config)
    
    # Should train on the 50 normal features, maybe 2-3 get flagged due to 0.05 contamination
    initial_findings = engine.run(training_features)
    assert engine.is_initialized is True
    
    # Check that model files were created
    assert os.path.exists(tmp_config["ml_model_path"])
    assert os.path.exists(tmp_config["ml_scaler_path"])
    
    # 2. Test model loading
    new_engine = MLEngine(config=tmp_config)
    
    # 3. Predict on a normal transaction (from the training set)
    # Shouldn't be an anomaly (usually, since it's normal)
    normal_tx = training_features[0]
    normal_findings = new_engine.run([normal_tx])
    
    # 4. Predict on an anomalous transaction
    anomalous_findings = new_engine.run([anomalous_feature_vector])
    
    assert len(anomalous_findings) == 1
    anomaly = anomalous_findings[0]
    
    assert anomaly.prediction == "Anomaly"
    assert anomaly.anomaly_score > 0
    assert anomaly.confidence >= 0.0
    assert anomaly.confidence <= 1.0
    assert "Isolation Forest" in anomaly.explanation
