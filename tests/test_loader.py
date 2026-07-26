import pytest
from pathlib import Path
import pandas as pd

from src.data.loader import DatasetLoader
from src.data.dataset_context import DatasetContext
from src.exceptions.engine_exceptions import SchemaValidationError, DataLoadError


def test_loader_initializes_with_default_path():
    loader = DatasetLoader()
    assert loader.data_dir.name == "dataset"


def test_loader_loads_all_datasets():
    loader = DatasetLoader()
    try:
        context = loader.load()
    except (DataLoadError, SchemaValidationError) as e:
        pytest.fail(f"Loader failed on valid dataset with: {e}")
        
    assert isinstance(context, DatasetContext)
    
    # Verify all DataFrames are loaded
    assert not context.transactions.empty
    assert not context.customers.empty
    assert not context.accounts.empty
    assert not context.devices.empty
    assert not context.beneficiaries.empty
    assert not context.merchants.empty
    assert not context.locations.empty
    assert not context.branches.empty
    assert not context.country_risk.empty
    
    # Verify relations
    assert not context.relationships.empty
    assert not context.fraud_rings.empty
    assert not context.fraud_ring_memberships.empty


def test_loader_validates_columns(mocker):
    loader = DatasetLoader()
    # Mock _load_csv to return a missing-column dataframe
    mocker.patch.object(
        loader, 
        '_load_csv', 
        return_value=pd.DataFrame({"invalid_col": [1, 2, 3]})
    )
    
    with pytest.raises(SchemaValidationError) as exc:
        loader.load()
        
    assert "missing required columns" in str(exc.value)

