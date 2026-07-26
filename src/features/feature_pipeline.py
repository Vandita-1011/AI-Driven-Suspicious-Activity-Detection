"""
Feature Pipeline
================
Orchestrates the feature extraction process by combining domain-specific extractors.
"""
import pandas as pd

from src.data.dataset_context import DatasetContext
from src.features.transaction_features import TransactionFeatureExtractor
from src.features.customer_features import CustomerFeatureExtractor
from src.features.network_features import NetworkFeatureExtractor
from src.utils.logger import get_logger
from src.utils.timer import timed

logger = get_logger(__name__)


class FeaturePipeline:
    """
    Combines transaction, customer, and network feature extractors.
    """
    def __init__(self, enriched_df: pd.DataFrame, context: DatasetContext) -> None:
        self.df = enriched_df
        self.context = context
        self.txn_extractor = TransactionFeatureExtractor()
        self.cust_extractor = CustomerFeatureExtractor()
        self.net_extractor = NetworkFeatureExtractor(context)

    @timed("Feature Pipeline")
    def build(self) -> pd.DataFrame:
        """
        Runs all feature extractors sequentially.
        """
        logger.info("Starting feature pipeline...")
        
        if self.df.empty:
            logger.warning("Empty DataFrame provided to FeaturePipeline.")
            return self.df

        df = self.txn_extractor.extract(self.df)
        df = self.cust_extractor.extract(df)
        df = self.net_extractor.extract(df)
        
        logger.info("Feature extraction complete. Feature matrix shape: %s", df.shape)
        return df
