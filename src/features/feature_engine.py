import time
import pandas as pd
from typing import Dict, Optional, List

from src.data.dataset_context import DatasetContext
from src.profiling.profile_models import BehaviourProfile
from src.features.feature_builder import FeatureBuilder
from src.features.feature_models import FeatureVector
from src.utils.logger import get_logger
from src.utils.timer import timed
from src.exceptions.engine_exceptions import PreprocessingError

logger = get_logger(__name__)


class FeatureEngine:
    """
    Main engine orchestrating Core Feature Engineering (Part A).
    """

    def __init__(self) -> None:
        self.builder = FeatureBuilder()

    @timed("Feature Engine")
    def run(
        self, 
        enriched_df: pd.DataFrame, 
        profiles: Optional[Dict[str, BehaviourProfile]] = None
    ) -> pd.DataFrame:
        """
        Runs the feature engineering pipeline on the enriched transaction DataFrame.

        Args:
            enriched_df: Output DataFrame from Smart Preprocessor.
            profiles: Map of customer profiles from Behaviour Profiling Engine.

        Returns:
            DataFrame containing all core feature vectors for each transaction.
        """
        if enriched_df.empty:
            logger.warning("Empty DataFrame passed to FeatureEngine.")
            return pd.DataFrame()

        start_time = time.time()
        txns_count = len(enriched_df)
        logger.info("Advanced Feature Generation Started for %d transactions.", txns_count)

        try:
            feature_df = self.builder.build_features(enriched_df, profiles)
        except Exception as e:
            logger.error("Error during feature generation: %s", e)
            raise PreprocessingError(f"Feature Engineering failed: {e}")

        execution_time = time.time() - start_time
        logger.info(
            "Advanced Feature Generation Completed. Processed %d transactions in %.2fs. Execution Time: %.2fs", 
            txns_count, execution_time, execution_time
        )
        return feature_df

    def run_to_vectors(
        self, 
        enriched_df: pd.DataFrame, 
        profiles: Optional[Dict[str, BehaviourProfile]] = None
    ) -> List[FeatureVector]:
        """Runs the feature engineering pipeline and converts results into FeatureVector models."""
        df = self.run(enriched_df, profiles)
        return self.builder.to_feature_vectors(df)
