"""
Profiling Package
=================
Builds per-customer and per-account behaviour baselines.

The Behaviour Profiler analyses historical transactions to establish
a customer's "normal" patterns: typical transaction amounts, preferred
channels, active hours, average frequency, etc.

The baseline is consumed by the Behaviour Engine to detect anomalous
deviations from the expected pattern.

Usage:
    from src.profiling.behaviour_profiler import BehaviourProfiler

    profiler = BehaviourProfiler(enriched_df)
    profiler.build_all_profiles()
    profile = profiler.get_profile("CUST-000001")
"""
from src.profiling.behaviour_profiler import BehaviourProfiler

__all__ = ["BehaviourProfiler"]
