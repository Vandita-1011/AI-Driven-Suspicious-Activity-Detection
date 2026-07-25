"""
Preprocessing Package
=====================
Transforms raw DataFrames into a clean, enriched, analysis-ready DataFrame.

Pipeline:
    DataCleaner  →  null handling, type coercion, date parsing
    DataEnricher →  multi-table joins: transactions ← accounts ← customers
                    ← branches ← country_risk ← merchants ← locations
    Preprocessor →  orchestrates cleaner + enricher into one enriched output

Usage:
    from src.preprocessing.preprocessor import Preprocessor

    preprocessor = Preprocessor(context)
    enriched_df = preprocessor.fit_transform()
"""
from src.preprocessing.cleaner import DataCleaner
from src.preprocessing.enricher import DataEnricher
from src.preprocessing.preprocessor import Preprocessor

__all__ = ["DataCleaner", "DataEnricher", "Preprocessor"]
