"""
Recommender
===========
Maps risk scores and scenario evidence to concrete investigator actions.
"""
from typing import Any

from src.constants.risk_levels import RecommendedAction, RiskLevel
from src.utils.logger import get_logger
from src.utils.timer import timed

logger = get_logger(__name__)


class Recommender:
    """
    Determines the next best action for an investigator.
    """
    
    def recommend(self, risk_score: float, risk_level: str, patterns: list[str], rules: list[str]) -> RecommendedAction:
        """
        Returns a RecommendedAction based on risk severity and evidence.
        """
        if risk_level == RiskLevel.CRITICAL.value:
            return RecommendedAction.FILE_SAR
        elif risk_level == RiskLevel.HIGH.value:
            return RecommendedAction.ESCALATE_TO_COMPLIANCE
        elif risk_level == RiskLevel.MEDIUM.value:
            return RecommendedAction.REQUEST_DOCUMENTS
        else:
            return RecommendedAction.NO_ACTION

    @timed("Recommender Batch")
    def recommend_batch(self, risk_df: Any) -> dict[str, RecommendedAction]:
        """
        Generates recommendations for a batch of transactions.
        """
        logger.info("Generating recommendations...")
        # For the foundation, we just return a stub mapping.
        # Implementation will iterate over risk_df and call `recommend`
        return {}
