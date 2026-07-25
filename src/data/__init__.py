"""
Data Package
============
Responsible for loading all 12 CSV tables, validating their schemas,
and providing a unified DatasetContext object to the pipeline.

Sub-modules:
    schema          TypedDict schema definitions per table (documentation only)
    dataset_context DatasetContext — a bag-of-tables passed through the pipeline
    loader          DatasetLoader — reads CSVs from dataset/, validates, returns context

Usage:
    from src.data.loader import DatasetLoader

    loader = DatasetLoader()
    context = loader.load()           # loads all 12 tables
    txn_df = context.transactions     # pd.DataFrame
"""
from src.data.dataset_context import DatasetContext
from src.data.loader import DatasetLoader

__all__ = ["DatasetContext", "DatasetLoader"]
