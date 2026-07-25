import pytest
import pandas as pd
import numpy as np

from src.data.dataset_context import DatasetContext
from src.preprocessing.cleaner import DataCleaner, DataTypeNormalizer, TimestampProcessor, DataQualityReport
from src.preprocessing.preprocessor import Preprocessor
from src.exceptions.engine_exceptions import PreprocessingError
from src.constants.column_names import TxnCols, CustomerCols, AccountCols

@pytest.fixture
def base_context():
    ctx = DatasetContext()
    
    # Valid Transactions
    ctx.transactions = pd.DataFrame({
        TxnCols.TRANSACTION_ID: ["t1", "t2", "t2"], # t2 is duplicate
        TxnCols.ACCOUNT_ID: ["a1", "a1", "a1"],
        TxnCols.CUSTOMER_ID: ["c1", "c1", "c1"],
        TxnCols.TIMESTAMP: ["2024-01-01 10:00:00", "2024-01-01 15:00:00", "2024-01-01 15:00:00"],
        TxnCols.AMOUNT: [100.50, np.nan, np.nan], # missing amount
        TxnCols.MERCHANT_ID: ["m1", "m2", "m2"],
        TxnCols.COUNTERPARTY_COUNTRY: ["US", "UK", "UK"]
    })
    
    # Valid Customers
    ctx.customers = pd.DataFrame({
        CustomerCols.CUSTOMER_ID: ["c1"],
        CustomerCols.DOB: ["1980-05-15"],
        CustomerCols.AGE: [43],
        CustomerCols.IS_PEP: ["true"], # Needs conversion to bool
        CustomerCols.PROFILE_SEGMENT: ["VIP"]
    })
    
    # Valid Accounts
    ctx.accounts = pd.DataFrame({
        AccountCols.ACCOUNT_ID: ["a1"],
        AccountCols.OPEN_DATE: ["2020-01-01"],
        AccountCols.STATUS: ["ACTIVE"],
        AccountCols.AVG_MONTHLY_BALANCE: [5000.0]
    })
    
    return ctx

def test_cleaner_removes_duplicates(base_context):
    report = DataQualityReport()
    cleaner = DataCleaner(report)
    
    assert len(base_context.transactions) == 3
    cleaned = cleaner.clean(base_context.transactions, "Transactions")
    
    assert len(cleaned) == 2
    assert report.duplicates_removed == 1

def test_cleaner_fills_missing_numeric(base_context):
    report = DataQualityReport()
    cleaner = DataCleaner(report)
    
    cleaned = cleaner.clean(base_context.transactions, "Transactions")
    # Median of [100.50] is 100.50
    assert cleaned[TxnCols.AMOUNT].iloc[1] == 100.50
    assert report.missing_values_fixed == 1

def test_datatype_normalizer(base_context):
    report = DataQualityReport()
    normalizer = DataTypeNormalizer(report)
    
    norm = normalizer.normalize(base_context.customers, "Customers")
    assert norm[CustomerCols.IS_PEP].dtype == bool
    assert norm[CustomerCols.IS_PEP].iloc[0] is True
    assert pd.api.types.is_integer_dtype(norm[CustomerCols.AGE])

def test_timestamp_processor_invalid_timestamps():
    report = DataQualityReport()
    tp = TimestampProcessor(report)
    
    df = pd.DataFrame({
        TxnCols.TIMESTAMP: ["2024-01-01", "invalid_date"]
    })
    
    processed = tp.process(df, "Transactions")
    assert pd.isna(processed[TxnCols.TIMESTAMP].iloc[1])
    assert not pd.isna(processed[TxnCols.TIMESTAMP].iloc[0])

def test_preprocessor_orchestration(base_context):
    preprocessor = Preprocessor(base_context)
    enriched = preprocessor.fit_transform()
    
    # Check that duplicates were removed
    assert len(enriched) == 2
    
    # Check that metadata was added
    assert 'customer_age_group' in enriched.columns
    assert 'account_age_days' in enriched.columns
    assert 'transaction_date' in enriched.columns
    assert 'is_business_hours' in enriched.columns
    
    # Check business hours logic (10:00 is True, 15:00 is True)
    assert enriched['is_business_hours'].all()

def test_preprocessor_empty_dataset():
    ctx = DatasetContext()
    preprocessor = Preprocessor(ctx)
    
    with pytest.raises(PreprocessingError) as exc:
        preprocessor.fit_transform()
        
    assert "empty DataFrame" in str(exc.value)
