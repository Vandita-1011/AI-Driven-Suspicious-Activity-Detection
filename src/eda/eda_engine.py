"""
EDA Engine
==========
Exploratory Data Analysis module for the dataset.
"""
from typing import Any

import pandas as pd

from src.data.dataset_context import DatasetContext
from src.utils.io_helpers import save_json
from src.utils.logger import get_logger
from src.utils.timer import timed
from src.config.settings import get_settings

logger = get_logger(__name__)


class EDAEngine:
    """
    Generates an EDA report on demand.
    """

    def __init__(self, context: DatasetContext, enriched_df: pd.DataFrame) -> None:
        self.context = context
        self.df = enriched_df
        self.settings = get_settings().outputs

    @timed("EDA Engine")
    def run(self) -> dict[str, Any]:
        """
        Executes the EDA routines.
        """
        logger.info("Generating EDA Report...")
        
        report: dict[str, Any] = {
            "dataset_shape": {
                "transactions": len(self.df),
                "customers": len(self.context.customers),
                "accounts": len(self.context.accounts),
            }
        }
        
        if self.df.empty:
            logger.warning("Enriched DataFrame is empty, skipping detailed EDA.")
            return report

        # Basic stats
        if "flag_label" in self.df.columns:
            report["flag_distribution"] = self.df["flag_label"].value_counts(dropna=False).to_dict()
            
        if "aml_scenario_tag" in self.df.columns:
            report["scenario_distribution"] = self.df["aml_scenario_tag"].value_counts(dropna=False).to_dict()
            
        if "amount" in self.df.columns:
            desc = self.df["amount"].describe().to_dict()
            report["amount_statistics"] = desc

        return report

    def save_report(self, report: dict[str, Any]) -> None:
        """Saves the EDA report to disk."""
        save_json(report, f"{self.settings.dir}/{self.settings.eda_report_file}")
