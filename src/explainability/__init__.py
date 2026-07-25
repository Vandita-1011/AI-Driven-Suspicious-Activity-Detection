"""
Explainability Package
======================
Evidence-based explanation generation.

The Explainer does NOT use SHAP or LIME.  Instead, it assembles a
structured, human-readable narrative from the evidence already
collected by the five detection engines:

    Triggered AML rules          (from RuleEngine)
    Behaviour deviations         (from BehaviourEngine)
    Statistical anomalies        (from StatisticalEngine)
    ML anomaly scores            (from MLEngine)
    Matched AML patterns         (from AMLPatternEngine)

Output is an Explanation dataclass with a plain-English `narrative`
field suitable for direct display to an investigator.

Usage:
    from src.explainability.explainer import Explainer

    explainer = Explainer()
    explanation = explainer.explain(transaction_id, engine_results)
"""
from src.explainability.explainer import Explainer

__all__ = ["Explainer"]
