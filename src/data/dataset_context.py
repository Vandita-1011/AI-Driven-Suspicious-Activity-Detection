"""
Dataset Context
===============
A container for all raw datasets loaded from the CSV files.
Passed through the pipeline to allow different engines access to
reference data without redundant loading.
"""
from dataclasses import dataclass, field
import pandas as pd


@dataclass
class DatasetContext:
    """
    Holds all raw DataFrames loaded from the dataset directory.
    """
    transactions: pd.DataFrame = field(default_factory=pd.DataFrame)
    customers: pd.DataFrame = field(default_factory=pd.DataFrame)
    accounts: pd.DataFrame = field(default_factory=pd.DataFrame)
    devices: pd.DataFrame = field(default_factory=pd.DataFrame)
    beneficiaries: pd.DataFrame = field(default_factory=pd.DataFrame)
    merchants: pd.DataFrame = field(default_factory=pd.DataFrame)
    locations: pd.DataFrame = field(default_factory=pd.DataFrame)
    branches: pd.DataFrame = field(default_factory=pd.DataFrame)
    country_risk: pd.DataFrame = field(default_factory=pd.DataFrame)
    relationships: pd.DataFrame = field(default_factory=pd.DataFrame)
    fraud_rings: pd.DataFrame = field(default_factory=pd.DataFrame)
    fraud_ring_memberships: pd.DataFrame = field(default_factory=pd.DataFrame)

    def is_empty(self) -> bool:
        """Checks if the primary transactions table is empty."""
        return self.transactions.empty
