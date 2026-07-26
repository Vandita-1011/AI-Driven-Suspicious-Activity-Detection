"""
AML Pattern Engine
==================
Detects specific AML scenarios matching the 15 patterns from the dataset.
"""
import pandas as pd

from src.constants.aml_scenarios import AMLScenario
from src.interfaces.base_engine import BaseDetectionEngine, EngineResult
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.utils.timer import timed

logger = get_logger(__name__)


class AMLPatternEngine(BaseDetectionEngine):
    """
    Pattern matching for known AML scenarios.
    """
    def __init__(self) -> None:
        self.settings = get_settings().aml_pattern_engine

    @timed("AML Pattern Engine")
    def run(self, features_df: pd.DataFrame) -> EngineResult:
        """
        Executes pattern matching logic.
        """
        logger.info("Running AML Pattern Engine...")
        
        result = EngineResult()
        if features_df.empty:
            return result
            
        result.scores = pd.Series(0.0, index=features_df.index)
        flags = pd.DataFrame(False, index=features_df.index, columns=AMLScenario.all_tags())

        # For the hackathon foundation, we rely on the pre-computed features 
        # or simplified proxies to detect patterns without complex group-bys here.

        # Example proxy for Round-Amount
        if "is_round_amount" in features_df.columns:
            mask = features_df["is_round_amount"] == 1
            flags.loc[mask, AMLScenario.ROUND_AMOUNT.value] = True
            result.scores[mask] += 50.0

        # Cap scores at 100
        result.scores = result.scores.clip(upper=100.0)
        result.flags = flags
        
        logger.info("AML Pattern Engine complete.")
        return result
