"""
Preprocessor
============
Orchestrates the cleaner and enricher into a single fit_transform pipeline.
"""
import pandas as pd

from src.data.dataset_context import DatasetContext
from src.interfaces.base_preprocessor import BasePreprocessor
from src.preprocessing.cleaner import DataCleaner
from src.preprocessing.enricher import DataEnricher
from src.utils.logger import get_logger
from src.utils.timer import timed

logger = get_logger(__name__)


class Preprocessor(BasePreprocessor):
    """
    Main preprocessing orchestrator.
    """

    def __init__(self, context: DatasetContext) -> None:
        super().__init__(context)
        self.cleaner = DataCleaner()
        self.enricher = DataEnricher(context)

    def fit(self) -> "Preprocessor":
        """No-op for this pipeline as imputation rules are static/config-driven."""
        return self

    @timed("Preprocessing Pipeline")
    def transform(self) -> pd.DataFrame:
        """
        Cleans individual tables and enriches the transactions.
        """
        logger.info("Starting preprocessing pipeline...")
        
        cleaned_txns = self.cleaner.clean_transactions(self.context.transactions)
        cleaned_customers = self.cleaner.clean_customers(self.context.customers)
        
        enriched_df = self.enricher.enrich(cleaned_txns, cleaned_customers)
        
        logger.info("Preprocessing complete.")
        return enriched_df
