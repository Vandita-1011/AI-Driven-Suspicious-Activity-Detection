"""
Orchestrator Package
====================
Master pipeline coordinator — the single entry point to the AI engine.

The Orchestrator accepts a query from the API Interface layer, runs
every pipeline stage in the correct order, handles failures gracefully,
and returns a structured PipelineResult.

Calling order:
    1. DatasetLoader.load()
    2. Preprocessor.fit_transform()
    3. BehaviourProfiler.build_all_profiles()
    4. FeaturePipeline.build()
    5. RuleEngine.run()
    6. BehaviourEngine.run()
    7. StatisticalEngine.run()
    8. MLEngine.run()
    9. AMLPatternEngine.run()
    10. SmartRiskFusion.fuse()
    11. Explainer.explain_batch()
    12. Recommender.recommend_batch()
    13. AlertPrioritizer.prioritize()

Usage:
    from src.orchestrator.orchestrator import Orchestrator

    orchestrator = Orchestrator()
    result = orchestrator.run()
"""
from src.orchestrator.orchestrator import Orchestrator, PipelineResult

__all__ = ["Orchestrator", "PipelineResult"]
