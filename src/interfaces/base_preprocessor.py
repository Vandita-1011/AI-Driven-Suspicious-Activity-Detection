"""
Base Preprocessor Interface
===========================
Defines the contract for the data preprocessing stage.
"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from src.data.dataset_context import DatasetContext


class BasePreprocessor(ABC):
    """
    Abstract base class for data preprocessors.
    """

    def __init__(self, context: "DatasetContext") -> None:
        """
        Initializes the preprocessor with the raw dataset context.

        Args:
            context: The DatasetContext containing raw DataFrames.
        """
        self.context = context

    @abstractmethod
    def fit(self) -> "BasePreprocessor":
        """
        Fits the preprocessor (e.g., learns imputation values).
        
        Returns:
            Self.
        """
        pass

    @abstractmethod
    def transform(self) -> pd.DataFrame:
        """
        Transforms the data (cleans and enriches).
        
        Returns:
            A single enriched pandas DataFrame ready for profiling and feature extraction.
        """
        pass
        
    def fit_transform(self) -> pd.DataFrame:
        """
        Fits and transforms in a single step.
        
        Returns:
            The enriched pandas DataFrame.
        """
        return self.fit().transform()
