"""
Recommendation Package
======================
Maps risk scores and scenario evidence to concrete investigator actions.

The Recommender takes a transaction's fused risk score, matched AML
patterns, triggered rules, and customer flags to produce a
RecommendedAction from the defined action catalogue.

Actions range from "No Action Required" (low-risk normal transactions)
to "File SAR" and "Freeze Account" for critical findings.

Usage:
    from src.recommendation.recommender import Recommender

    recommender = Recommender()
    action = recommender.recommend(risk_score, patterns, rules, customer_flags)
"""
from src.recommendation.recommender import Recommender

__all__ = ["Recommender"]
