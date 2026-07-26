"""
Agent Package
=============
Autonomous AML Investigation Agent modules.

The Agent layer provides natural-language driven investigation capabilities
on top of the existing AI detection pipeline.

Submodules (implemented progressively):
    intent_models       — Intent enum and IntentResult dataclass.
    intent_catalog      — Keyword catalogue and per-intent max scores.
    intent_recognizer   — Classifies analyst queries into Intent objects.

Usage:
    from src.agent.intent_recognizer import IntentRecognizer
    from src.agent.intent_models import Intent, IntentResult
"""
from src.agent.intent_models import Intent, IntentResult
from src.agent.intent_recognizer import IntentRecognizer

__all__ = ["IntentRecognizer", "Intent", "IntentResult"]
