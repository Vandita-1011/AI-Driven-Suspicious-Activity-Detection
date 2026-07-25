"""
Transaction Feature Extractor
=============================
Extracts temporal, velocity, and amount-based features from transactions.
"""
import pandas as pd

from src.constants.column_names import TxnCols, ComputedCols
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TransactionFeatureExtractor:
    """
    Extracts features specific to individual transactions and temporal windows.
    """
    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Appends transaction features to the DataFrame.
        """
        logger.debug("Extracting transaction features...")
        df = df.copy()

        if TxnCols.TIMESTAMP in df.columns:
            # Time-based features
            df[ComputedCols.HOUR_OF_DAY] = df[TxnCols.TIMESTAMP].dt.hour
            df[ComputedCols.DAY_OF_WEEK] = df[TxnCols.TIMESTAMP].dt.dayofweek
            df[ComputedCols.IS_WEEKEND] = df[ComputedCols.DAY_OF_WEEK].isin([5, 6]).astype(int)

        if TxnCols.AMOUNT in df.columns:
            # Simple round amount logic (e.g., divisible by 1000)
            df[ComputedCols.IS_ROUND_AMOUNT] = (df[TxnCols.AMOUNT] % 1000 == 0).astype(int)

        # Basic window features could be added here (velocity), but usually require sorting by account.
        # For prototype foundation, we just instantiate the columns if needed or leave them for implementation phase.
        
        return df
