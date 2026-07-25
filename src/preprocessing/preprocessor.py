"""
Preprocessor
============
Orchestrates the cleaner, type normalizer, timestamp processor, and enricher into a single fit_transform pipeline.
"""
import pandas as pd
import pprint

from src.data.dataset_context import DatasetContext
from src.interfaces.base_preprocessor import BasePreprocessor
from src.preprocessing.cleaner import DataCleaner, DataTypeNormalizer, TimestampProcessor, DataQualityReport
from src.preprocessing.enricher import DataEnricher
from src.utils.logger import get_logger
from src.utils.timer import timed
from src.exceptions.engine_exceptions import PreprocessingError

logger = get_logger(__name__)


class Preprocessor(BasePreprocessor):
    """
    Main preprocessing orchestrator.
    """

    def __init__(self, context: DatasetContext) -> None:
        super().__init__(context)
        self.report = DataQualityReport()
        self.cleaner = DataCleaner(self.report)
        self.normalizer = DataTypeNormalizer(self.report)
        self.timestamp_proc = TimestampProcessor(self.report)
        self.enricher = DataEnricher(context)

    def fit(self) -> "Preprocessor":
        """No-op for this pipeline as imputation rules are static/config-driven."""
        return self

    @timed("Preprocessing Pipeline")
    def transform(self) -> pd.DataFrame:
        """
        Orchestrates cleaning, normalisation, and enrichment.
        """
        logger.info("--- START PREPROCESSING ---")
        
        # We clean and normalize the core tables used in enrichment
        # 1. Cleaner
        logger.info("Stage 1: Cleaning Data")
        clean_txns = self.cleaner.clean(self.context.transactions, "Transactions")
        clean_custs = self.cleaner.clean(self.context.customers, "Customers")
        clean_accs = self.cleaner.clean(self.context.accounts, "Accounts")
        
        # 2. Type Normalizer
        logger.info("Stage 2: Type Normalization")
        norm_txns = self.normalizer.normalize(clean_txns, "Transactions")
        norm_custs = self.normalizer.normalize(clean_custs, "Customers")
        norm_accs = self.normalizer.normalize(clean_accs, "Accounts")
        
        # 3. Timestamp Processor
        logger.info("Stage 3: Timestamp Processing")
        ts_txns = self.timestamp_proc.process(norm_txns, "Transactions")
        ts_custs = self.timestamp_proc.process(norm_custs, "Customers")
        ts_accs = self.timestamp_proc.process(norm_accs, "Accounts")
        
        # Update context (Clean DatasetContext)
        self.context.transactions = ts_txns
        self.context.customers = ts_custs
        self.context.accounts = ts_accs
        
        # 4. Enricher
        logger.info("Stage 4: Data Enrichment")
        enriched_df = self.enricher.enrich(ts_txns, ts_custs, ts_accs)
        
        # 5. Validation (Sanity check)
        if enriched_df.empty:
            raise PreprocessingError("Preprocessing resulted in an empty DataFrame.")
            
        # 6. Generate Data Quality Report
        self.report.complete()
        self._print_quality_report()
        
        logger.info("--- PREPROCESSING COMPLETE ---")
        return enriched_df

    def _print_quality_report(self) -> None:
        """Logs the final preprocessing metrics."""
        report_str = f"""
        ========================================
        DATA QUALITY REPORT
        ========================================
        Processing Duration: {self.report.processing_duration:.2f}s
        Rows Processed:      {self.report.rows_processed}
        Rows Removed:        {self.report.rows_removed}
        Duplicates Removed:  {self.report.duplicates_removed}
        Missing Values Fixed:{self.report.missing_values_fixed}
        Invalid Vals Detected:{self.report.invalid_values_detected}
        ========================================
        """
        logger.info(report_str)

