"""
Orchestrator
============
The master pipeline coordinator.
"""
from dataclasses import dataclass
from typing import Any

from src.data.loader import DatasetLoader
from src.preprocessing.preprocessor import Preprocessor
from src.profiling.behaviour_profiler import BehaviourProfiler
from src.features.feature_pipeline import FeaturePipeline
from src.engines.rule_engine import RuleEngine
from src.engines.behaviour_engine import BehaviourEngine
from src.engines.statistical_engine import StatisticalEngine
from src.engines.ml_engine import MLEngine
from src.engines.aml_pattern_engine import AMLPatternEngine
from src.engines.risk_fusion import SmartRiskFusion
from src.explainability.explainer import Explainer
from src.recommendation.recommender import Recommender
from src.alerts.alert_prioritizer import AlertPrioritizer
from src.api_interface.request_models import AnalysisRequest
from src.utils.logger import get_logger
from src.utils.timer import Timer

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    """Result of a full orchestrator run."""
    success: bool
    alerts: list[Any]
    elapsed_seconds: float
    error_message: str = ""


class Orchestrator:
    """
    Coordinates all pipeline components in sequence.
    """
    def __init__(self) -> None:
        self.loader = DatasetLoader()
        # Other components are initialized during the run after context is available

    def run(self, request: AnalysisRequest | None = None) -> PipelineResult:
        """
        Executes the full AI detection pipeline.
        """
        with Timer("Total Pipeline Execution") as t:
            try:
                logger.info("--- Starting AML AI Engine Pipeline ---")
                
                # 1. Load Data
                context = self.loader.load()
                
                # 2. Preprocess
                preprocessor = Preprocessor(context)
                enriched_df = preprocessor.fit_transform()
                
                # 3. Profiling
                profiler = BehaviourProfiler(enriched_df)
                profiler.build_all_profiles()
                
                # 4. Features
                feature_pipe = FeaturePipeline(enriched_df, context)
                features_df = feature_pipe.build()
                
                # 5-9. Detection Engines
                engines = {
                    "rule_engine": RuleEngine(),
                    "behaviour_engine": BehaviourEngine(profiler),
                    "statistical_engine": StatisticalEngine(),
                    "ml_engine": MLEngine(),
                    "aml_pattern_engine": AMLPatternEngine()
                }
                
                engine_results = {}
                for name, engine in engines.items():
                    engine_results[name] = engine.run(features_df)
                    
                # 10. Risk Fusion
                fusion = SmartRiskFusion()
                risk_df = fusion.fuse(engine_results)
                
                # 11-13. Explain, Recommend, Alert
                # For a full implementation, we'd filter risk_df first, then explain/recommend.
                explainer = Explainer()
                recommender = Recommender()
                prioritizer = AlertPrioritizer()
                
                # Dummy calls for foundation
                explanations = explainer.explain_batch([], engine_results, features_df)
                recs = recommender.recommend_batch(risk_df)
                alerts = prioritizer.prioritize(risk_df, explanations, recs)
                
                logger.info("--- Pipeline Completed Successfully ---")
                return PipelineResult(success=True, alerts=alerts, elapsed_seconds=t.elapsed_seconds)
                
            except Exception as e:
                logger.exception("Pipeline failed: %s", e)
                return PipelineResult(success=False, alerts=[], elapsed_seconds=t.elapsed_seconds, error_message=str(e))
