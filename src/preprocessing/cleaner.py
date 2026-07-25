"""
Data Cleaner
============
Handles null imputation, data type coercion, and datetime parsing
for the raw DataFrames before they are joined.
"""
import pandas as pd

from src.config.settings import get_settings
from src.constants.column_names import TxnCols, CustomerCols
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataCleaner:
    """
    Cleans individual DataFrames (types, nulls, dates).
    """

    def __init__(self) -> None:
        self.settings = get_settings().preprocessing

    def clean_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans the transactions DataFrame."""
        logger.debug("Cleaning transactions data...")
        df = df.copy()
        
        # Parse dates
        if TxnCols.TIMESTAMP in df.columns:
            df[TxnCols.TIMESTAMP] = pd.to_datetime(
                df[TxnCols.TIMESTAMP], 
                format=self.settings.timestamp_format, 
                errors="coerce"
            )
            
        # Handle nulls
        if TxnCols.MERCHANT_ID in df.columns:
            df[TxnCols.MERCHANT_ID] = df[TxnCols.MERCHANT_ID].fillna(self.settings.null_strategy["categorical"])
            
        return df

    def clean_customers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans the customers DataFrame."""
        logger.debug("Cleaning customers data...")
        df = df.copy()
        
        # Parse dates
        if CustomerCols.DOB in df.columns:
            df[CustomerCols.DOB] = pd.to_datetime(df[CustomerCols.DOB], errors="coerce")
        if CustomerCols.ONBOARDING_DATE in df.columns:
            df[CustomerCols.ONBOARDING_DATE] = pd.to_datetime(df[CustomerCols.ONBOARDING_DATE], errors="coerce")
            
        # Convert booleans
        for col in self.settings.bool_columns:
            if col in df.columns:
                df[col] = df[col].astype(bool)
                
        return df
