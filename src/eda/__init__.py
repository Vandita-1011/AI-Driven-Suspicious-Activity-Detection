"""
EDA Package
===========
Exploratory Data Analysis — triggered only when explicitly requested
by the Orchestrator (not part of the default detection pipeline).

Produces:
  - Dataset shape and missing value summary
  - Suspicious vs Normal transaction distribution
  - Per-scenario transaction counts
  - Customer segment distributions
  - Amount distribution statistics
  - Correlation matrix of numeric features

Usage:
    from src.eda.eda_engine import EDAEngine

    eda = EDAEngine(context, enriched_df)
    report = eda.run()          # returns EDAReport dict
    eda.save_report(report)     # writes to outputs/eda_report.json
"""
from src.eda.eda_engine import EDAEngine

__all__ = ["EDAEngine"]
