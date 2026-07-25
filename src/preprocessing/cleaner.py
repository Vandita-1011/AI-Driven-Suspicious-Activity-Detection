"""
Data Cleaner and Normalizer
===========================
Handles missing values, duplicate rows, data type coercion, and timestamp normalization.
"""
import re
from typing import Any, get_type_hints
import time

import pandas as pd
import numpy as np

from src.constants.column_names import TxnCols, CustomerCols, AccountCols, ComputedCols
from src.utils.logger import get_logger
from src.exceptions.engine_exceptions import PreprocessingError
from src.data.dataset_context import DatasetContext
from src.data import schema

logger = get_logger(__name__)


class DataQualityReport:
    """Collects statistics during preprocessing."""
    def __init__(self) -> None:
        self.rows_processed: int = 0
        self.rows_removed: int = 0
        self.duplicates_removed: int = 0
        self.missing_values_fixed: int = 0
        self.invalid_values_detected: int = 0
        self.processing_duration: float = 0.0
        self.column_statistics: dict[str, dict[str, Any]] = {}
        self._start_time: float = time.time()

    def complete(self) -> None:
        self.processing_duration = time.time() - self._start_time


class DataCleaner:
    """
    Removes duplicates, handles missing values, and cleans strings.
    """
    def __init__(self, report: DataQualityReport) -> None:
        self.report = report
        # Threshold for excessive missing values
        self.missing_threshold = 0.5 

    def clean(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Executes all cleaning steps on a DataFrame."""
        if df.empty:
            return df
            
        initial_rows = len(df)
        self.report.rows_processed += initial_rows
        logger.info("Cleaning table: %s (%d rows)", table_name, initial_rows)

        df = self._remove_duplicates(df, table_name)
        df = self._remove_empty_rows(df, table_name)
        df = self._clean_strings(df, table_name)
        df = self._handle_missing_values(df, table_name)
        
        final_rows = len(df)
        removed = initial_rows - final_rows
        self.report.rows_removed += removed
        logger.info("Cleaned %s. Rows removed: %d. Final rows: %d", table_name, removed, final_rows)
        return df

    def _remove_duplicates(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        initial = len(df)
        df = df.drop_duplicates()
        dupes = initial - len(df)
        if dupes > 0:
            self.report.duplicates_removed += dupes
            logger.debug("%s: Removed %d duplicate rows.", table_name, dupes)
        return df

    def _remove_empty_rows(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        initial = len(df)
        df = df.dropna(how='all')
        empty = initial - len(df)
        if empty > 0:
            logger.debug("%s: Removed %d completely empty rows.", table_name, empty)
        return df

    def _clean_strings(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        # Select object/string columns
        str_cols = df.select_dtypes(include=['object', 'string']).columns
        
        for col in str_cols:
            # Strip spaces
            df[col] = df[col].str.strip()
            # Remove invisible characters and duplicate whitespace
            df[col] = df[col].str.replace(r'[\x00-\x1F\x7F-\x9F]', '', regex=True)
            df[col] = df[col].str.replace(r'\s+', ' ', regex=True)
            # Normalize casing for non-ID columns (IDs usually need precise casing)
            if not col.endswith('_id') and col != 'transaction_id':
                # Convert to title case for generic strings, or lower for things like channel
                # We'll just stick to standardizing to a clean string without forcing case on everything
                pass
                
        return df

    def _handle_missing_values(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        total_rows = len(df)
        
        # Detect excessive missing values
        missing_ratios = df.isna().mean()
        drop_cols = missing_ratios[missing_ratios > self.missing_threshold].index.tolist()
        if drop_cols:
            logger.warning("%s: Dropping columns with >50%% missing values: %s", table_name, drop_cols)
            df = df.drop(columns=drop_cols)
            
        # Fill missing values
        for col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count == 0:
                continue
                
            self.report.missing_values_fixed += int(missing_count)
            
            # Numeric: Median
            if pd.api.types.is_numeric_dtype(df[col]):
                median_val = df[col].median()
                if pd.isna(median_val):
                    median_val = 0
                df[col] = df[col].fillna(median_val)
                logger.debug("%s: Filled %d missing in numeric '%s' with median %s", table_name, missing_count, col, median_val)
                
            # Boolean: False
            elif pd.api.types.is_bool_dtype(df[col]) or (df[col].dropna().isin([True, False, 'True', 'False', 0, 1]).all()):
                df[col] = df[col].fillna(False)
                logger.debug("%s: Filled %d missing in boolean '%s' with False", table_name, missing_count, col)
                
            # Categorical/Object: Mode
            elif pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]):
                mode_series = df[col].mode()
                if not mode_series.empty:
                    mode_val = mode_series.iloc[0]
                else:
                    mode_val = "UNKNOWN"
                df[col] = df[col].fillna(mode_val)
                logger.debug("%s: Filled %d missing in categorical '%s' with mode '%s'", table_name, missing_count, col, mode_val)
                
            # Datetime: Leave unchanged (already logged)
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                logger.debug("%s: Ignored %d missing values in datetime '%s'", table_name, missing_count, col)
                
        return df


class DataTypeNormalizer:
    """
    Coerces column datatypes based on the schema definitions.
    """
    def __init__(self, report: DataQualityReport) -> None:
        self.report = report
        
        # Map TypedDict schema names to actual schema objects
        self.schema_map = {
            "Transactions": schema.TransactionSchema,
            "Customers": schema.CustomerSchema,
            "Accounts": schema.AccountSchema,
            "Devices": schema.DeviceSchema,
            "Beneficiaries": schema.BeneficiarySchema,
            "Merchants": schema.MerchantSchema,
            "Locations": schema.LocationSchema,
            "Branches": schema.BranchSchema,
            "Country Risk": schema.CountryRiskSchema,
            "Relationships": schema.RelationshipSchema,
            "Fraud Rings": schema.FraudRingSchema,
            "Fraud Ring Memberships": schema.FraudRingMembershipSchema,
        }

    def normalize(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Converts columns to their explicitly defined types."""
        if df.empty or table_name not in self.schema_map:
            return df
            
        logger.info("Normalizing data types for: %s", table_name)
        schema_def = self.schema_map[table_name]
        type_hints = get_type_hints(schema_def)
        
        df = df.copy()
        
        for col, target_type in type_hints.items():
            if col not in df.columns:
                continue
                
            try:
                if target_type == int:
                    # Int64 allows for NaN safely if needed
                    df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
                elif target_type == float:
                    df[col] = pd.to_numeric(df[col], errors='coerce').astype('float64')
                elif target_type == bool:
                    df[col] = df[col].astype(str).str.lower().map({'true': True, '1': True, 'false': False, '0': False})
                    df[col] = df[col].fillna(False).astype(bool)
                elif target_type == str:
                    df[col] = df[col].astype(str)
                    
                # Datetimes are handled by TimestampProcessor natively. The typed dict uses `str` for datetimes,
                # but we will parse known datetime columns explicitly in TimestampProcessor.
                
                # Check for NaNs introduced by coercion (invalid values)
                if target_type in [int, float]:
                    invalid_mask = df[col].isna() & (df[col].astype(str) != '<NA>') # Ignore intended nulls
                    # The missing values were handled in cleaner, so any new NaNs are coercion failures
                    # But if we did coerce, we should track invalid values detected.
            except Exception as e:
                logger.error("Failed to convert %s.%s to %s: %s", table_name, col, target_type, e)
                raise PreprocessingError(f"Type conversion failed for {table_name}.{col}: {e}")
                
        return df


class TimestampProcessor:
    """
    Normalizes timestamps and extracts temporal metadata components.
    """
    def __init__(self, report: DataQualityReport) -> None:
        self.report = report

    def process(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Parses and normalizes datetimes, and adds derived temporal columns if applicable."""
        if df.empty:
            return df
            
        df = df.copy()
        logger.info("Processing timestamps for: %s", table_name)
        
        # Define known timestamp columns
        datetime_cols = {
            "Transactions": [TxnCols.TIMESTAMP],
            "Customers": [CustomerCols.DOB, CustomerCols.ONBOARDING_DATE],
            "Accounts": [AccountCols.OPEN_DATE],
            "Devices": ["first_seen_date"],
            "Beneficiaries": ["added_date"],
            "Fraud Rings": ["formation_date"],
        }
        
        cols_to_process = datetime_cols.get(table_name, [])
        
        for col in cols_to_process:
            if col in df.columns:
                try:
                    # Convert to datetime with UTC timezone
                    df[col] = pd.to_datetime(df[col], errors='coerce', utc=True)
                except Exception as e:
                    raise PreprocessingError(f"Failed to parse timestamp for {table_name}.{col}: {e}")
                    
        # Extract metadata specifically for Transactions
        if table_name == "Transactions" and TxnCols.TIMESTAMP in df.columns:
            ts_col = df[TxnCols.TIMESTAMP]
            df[ComputedCols.HOUR_OF_DAY] = ts_col.dt.hour
            df['transaction_day'] = ts_col.dt.day
            df[ComputedCols.DAY_OF_WEEK] = ts_col.dt.dayofweek
            df['transaction_month'] = ts_col.dt.month
            df['transaction_year'] = ts_col.dt.year
            df[ComputedCols.IS_WEEKEND] = df[ComputedCols.DAY_OF_WEEK].isin([5, 6]).astype(bool)
            
        return df

