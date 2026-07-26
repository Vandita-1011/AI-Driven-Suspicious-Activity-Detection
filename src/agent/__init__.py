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
    entity_models       — EntityExtractionResult and related dataclasses.
    entity_extractor    — Extracts entities and filters from analyst queries.

Usage:
    from src.agent.intent_recognizer import IntentRecognizer
    from src.agent.entity_extractor import EntityExtractor
"""
from src.agent.intent_models import Intent, IntentResult
from src.agent.intent_recognizer import IntentRecognizer
from src.agent.entity_models import (
    AmountFilter,
    AmountOperator,
    DateFilter,
    EntityExtractionResult,
    RiskLevelFilter,
)
from src.agent.entity_extractor import EntityExtractor

__all__ = [
    "IntentRecognizer", "Intent", "IntentResult",
    "EntityExtractor", "EntityExtractionResult",
    "AmountFilter", "AmountOperator", "DateFilter", "RiskLevelFilter",
]
