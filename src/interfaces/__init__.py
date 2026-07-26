"""
Interfaces Package
==================
Abstract base classes defining the contracts between all engine modules.

The Orchestrator depends only on these interfaces — never on concrete
implementations — enabling engines to be swapped without touching the
pipeline coordinator (Dependency Inversion Principle).

Public exports:
    EngineResult        Dataclass: output of any detection engine
    BehaviourProfile    Dataclass: customer behaviour baseline
    Explanation         Dataclass: evidence-based transaction explanation
    BaseDataLoader      ABC: load() → DatasetContext
    BasePreprocessor    ABC: fit(), transform(), fit_transform()
    BaseDetectionEngine ABC: run() → EngineResult
    BaseBehaviourProfiler ABC: build_profile(), get_profile()
    BaseExplainer       ABC: explain(), explain_batch()
"""
from src.interfaces.base_engine import EngineResult, BaseDetectionEngine
from src.interfaces.base_loader import BaseDataLoader
from src.interfaces.base_preprocessor import BasePreprocessor
from src.interfaces.base_profiler import BehaviourProfile, BaseBehaviourProfiler
from src.interfaces.base_explainer import Explanation, BaseExplainer

__all__ = [
    "EngineResult", "BaseDetectionEngine",
    "BaseDataLoader",
    "BasePreprocessor",
    "BehaviourProfile", "BaseBehaviourProfiler",
    "Explanation", "BaseExplainer",
]
