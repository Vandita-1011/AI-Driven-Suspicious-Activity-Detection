"""
Base Data Loader Interface
==========================
Defines the contract for data loading.
"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.data.dataset_context import DatasetContext


class BaseDataLoader(ABC):
    """
    Abstract base class for data loaders.
    """

    @abstractmethod
    def load(self) -> "DatasetContext":
        """
        Loads all required datasets and returns a unified context.

        Returns:
            A DatasetContext object containing all loaded DataFrames.
            
        Raises:
            DataLoadError: If data loading fails.
            SchemaValidationError: If loaded data fails schema validation.
        """
        pass
