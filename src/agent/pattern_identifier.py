"""
Pattern Identifier
==================
Evaluates intent and extracted entities to determine the specific
investigation pattern required.
"""
from __future__ import annotations

from typing import List, Tuple

from src.agent.intent_models import Intent, IntentResult
from src.agent.entity_models import EntityExtractionResult
from src.agent.pattern_models import (
    ConfidenceLevel,
    InvestigationPatternType,
    PatternIdentificationResult,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

AML_PATTERN_MAP = {
    "structuring": InvestigationPatternType.STRUCTURING_INVESTIGATION,
    "smurfing": InvestigationPatternType.SMURFING_INVESTIGATION,
    "layering": InvestigationPatternType.LAYERING_INVESTIGATION,
    "rapid_fund_movement": InvestigationPatternType.RAPID_MOVEMENT_INVESTIGATION,
}

ENTITY_WEIGHTS = {
    "customer_ids": 0.30,
    "transaction_ids": 0.30,
    "countries": 0.15,
    "limit": 0.05
}

class PatternIdentifier:
    """
    Determines the specific InvestigationPatternType based on the
    recognized intent and extracted entities.
    """

    def identify(
        self, intent_result: IntentResult, entity_result: EntityExtractionResult
    ) -> PatternIdentificationResult:
        """
        Evaluates the parsed intent and entities to identify the pattern.
        """
        logger.debug("Identifying pattern for intent: %s", intent_result.intent.value)

        # 1. Determine base pattern and required entities
        pattern, required, reason = self._map_pattern(intent_result, entity_result)

        # 2. Check for missing entities
        missing = self._find_missing_entities(required, entity_result)
        
        # 3. Determine confidence
        confidence_score = self._calculate_confidence(intent_result.confidence, missing)
        confidence_level = self._get_confidence_level(confidence_score)

        # 4. Generate validation messages
        messages: List[str] = []
        if missing:
            messages.append(f"Missing required entities: {', '.join(missing)}")
        if confidence_level == ConfidenceLevel.LOW:
            messages.append("Low confidence in pattern identification; manual review recommended.")

        return PatternIdentificationResult(
            investigation_pattern=pattern,
            confidence_score=round(confidence_score, 4),
            confidence_level=confidence_level,
            reasoning=reason,
            matched_intent=intent_result,
            matched_entities=entity_result,
            required_entities=required,
            missing_entities=missing,
            validation_messages=messages
        )

    def _map_pattern(
        self, intent: IntentResult, entities: EntityExtractionResult
    ) -> Tuple[InvestigationPatternType, List[str], str]:
        """
        Maps intent to a pattern type and determines required entities.
        """
        if intent.intent == Intent.CUSTOMER_INVESTIGATION:
            if "dormant_account" in entities.aml_patterns:
                return (
                    InvestigationPatternType.DORMANT_ACCOUNT_INVESTIGATION,
                    ["customer_ids"],
                    "Customer investigation for dormant accounts."
                )
            return (
                InvestigationPatternType.CUSTOMER_INVESTIGATION,
                ["customer_ids"],
                "Direct customer investigation requested."
            )

        if intent.intent == Intent.TRANSACTION_INVESTIGATION:
            if "suspicious" in intent.raw_query.lower():
                return (
                    InvestigationPatternType.SUSPICIOUS_TRANSACTION_ANALYSIS,
                    ["transaction_ids"],
                    "Suspicious transaction investigation."
                )
            return (
                InvestigationPatternType.TRANSACTION_INVESTIGATION,
                ["transaction_ids"],
                "Direct transaction investigation requested."
            )

        if intent.intent == Intent.HIGH_RISK_CUSTOMER:
            return (
                InvestigationPatternType.HIGH_RISK_CUSTOMER_REVIEW,
                [],
                "Reviewing high risk customers."
            )

        if intent.intent == Intent.AML_PATTERN_SEARCH:
            for pattern in entities.aml_patterns:
                if pattern in AML_PATTERN_MAP:
                    return (
                        AML_PATTERN_MAP[pattern],
                        [],
                        f"{pattern.replace('_', ' ').capitalize()} AML pattern identified."
                    )
            return (
                InvestigationPatternType.GENERAL_SEARCH,
                [],
                "General AML pattern search."
            )

        if intent.intent == Intent.DASHBOARD_SUMMARY:
            return (
                InvestigationPatternType.RISK_SUMMARY,
                [],
                "Dashboard summary requested."
            )

        if intent.intent == Intent.DATASET_ANALYSIS:
            if entities.limit is not None:
                return (
                    InvestigationPatternType.TOP_N_INVESTIGATION,
                    ["limit"],
                    "Top-N dataset analysis."
                )
            if entities.countries:
                return (
                    InvestigationPatternType.COUNTRY_RISK_INVESTIGATION,
                    ["countries"],
                    "Country risk analysis requested."
                )
            return (
                InvestigationPatternType.GENERAL_SEARCH,
                [],
                "General dataset analysis."
            )

        return (
            InvestigationPatternType.CUSTOM_INVESTIGATION,
            [],
            "Fallback to custom investigation for unknown or complex intents."
        )

    def _find_missing_entities(
        self, required: List[str], entities: EntityExtractionResult
    ) -> List[str]:
        missing: List[str] = []
        if "customer_ids" in required and not entities.customer_ids:
            missing.append("customer_ids")
        if "transaction_ids" in required and not entities.transaction_ids:
            missing.append("transaction_ids")
        if "limit" in required and not entities.limit:
            missing.append("limit")
        if "countries" in required and not entities.countries:
            missing.append("countries")
        return missing

    def _calculate_confidence(self, base_confidence: float, missing_entities: List[str]) -> float:
        """Penalizes confidence for missing required entities using weighted penalties."""
        penalty = 0.0
        for entity in missing_entities:
            penalty += ENTITY_WEIGHTS.get(entity, 0.10)  # Default penalty of 0.10 for unknown entity types
        
        return max(0.0, min(1.0, base_confidence - penalty))

    def _get_confidence_level(self, score: float) -> ConfidenceLevel:
        if score >= 0.90:
            return ConfidenceLevel.HIGH
        if score >= 0.75:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW
