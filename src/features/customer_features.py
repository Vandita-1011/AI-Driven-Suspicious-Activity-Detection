"""
Customer Feature Extractor
==========================
Extracts risk features based on customer profiles.
"""
import pandas as pd

from src.constants.column_names import ComputedCols, CustomerCols
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CustomerFeatureExtractor:
    """
    Extracts features related to the customer's risk profile (PEP, KYC, Segments).
    """
    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Appends customer features to the DataFrame.
        """
        logger.debug("Extracting customer features...")
        df = df.copy()

        # Translate booleans to numeric for ML models if present
        if ComputedCols.IS_PEP in df.columns:
            df[ComputedCols.PEP_RISK_FLAG] = df[ComputedCols.IS_PEP].astype(int)
            
        if ComputedCols.SANCTIONS_HIT in df.columns:
            df[ComputedCols.SANCTIONS_RISK_FLAG] = df[ComputedCols.SANCTIONS_HIT].astype(int)

        # Map KYC levels to ordinal/numeric risk weights
        if ComputedCols.KYC_LEVEL in df.columns:
            kyc_mapping = {"Low": 1, "Medium": 2, "High": 3}
            df[ComputedCols.KYC_RISK_SCORE] = df[ComputedCols.KYC_LEVEL].map(kyc_mapping).fillna(0)

        return df
