"""
Features Package
================
Extracts and assembles the feature matrix consumed by all detection engines.

Three domain-specific extractors are combined by FeaturePipeline:
    TransactionFeatureExtractor  — amount, velocity, timing, channel features
    CustomerFeatureExtractor     — PEP, KYC, income deviation, risk score features
    NetworkFeatureExtractor      — graph-based features via NetworkX (ring membership,
                                   relationship count, transaction path analysis)

Usage:
    from src.features.feature_pipeline import FeaturePipeline

    pipeline = FeaturePipeline(enriched_df, context)
    feature_df = pipeline.build()     # returns enriched_df + all feature columns
"""
from src.features.transaction_features import TransactionFeatureExtractor
from src.features.customer_features import CustomerFeatureExtractor
from src.features.network_features import NetworkFeatureExtractor
from src.features.feature_pipeline import FeaturePipeline

__all__ = [
    "TransactionFeatureExtractor",
    "CustomerFeatureExtractor",
    "NetworkFeatureExtractor",
    "FeaturePipeline",
]
