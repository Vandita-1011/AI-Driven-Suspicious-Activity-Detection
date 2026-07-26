"""
Intent Recognizer
=================
Classifies a natural-language analyst query into a structured Intent.

Design
------
Recognition is performed in two stages:

1. **Normalization** — lowercases, strips punctuation, and collapses
   whitespace so that surface variations ("Investigate!", "investigate…")
   are treated identically.

2. **Keyword Matching** — each supported Intent is associated with an
   ordered list of keyword-groups (tuples) defined in ``intent_catalog``.
   A keyword-group matches when **all** of its tokens are present in the
   normalised query.  Matched group weights are summed per intent, then
   normalised against that intent's *own* maximum possible score so that
   intents with fewer rules are not unfairly penalised.

The recognizer is intentionally rule-based (no ML dependency) and can be
extended by adding entries to ``intent_catalog.KEYWORD_CATALOGUE``.

Usage
-----
    from src.agent.intent_recognizer import IntentRecognizer

    recognizer = IntentRecognizer()
    result = recognizer.recognize("Investigate customer 4521")
    print(result.intent.value, result.confidence)
"""
from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Tuple

from src.agent.intent_catalog import KEYWORD_CATALOGUE, MAX_SCORE_PER_INTENT
from src.agent.intent_models import Intent, IntentResult
from src.utils.logger import get_logger
from src.utils.timer import timed

logger = get_logger(__name__)


class IntentRecognizer:
    """
    Classifies natural-language analyst queries into structured Intent objects.

    The recognizer is stateless and thread-safe.

    Examples::

        recognizer = IntentRecognizer()

        r = recognizer.recognize("Analyze this dataset for suspicious activity")
        assert r.intent == Intent.DATASET_ANALYSIS

        r = recognizer.recognize("Find structuring patterns")
        assert r.intent == Intent.AML_PATTERN_SEARCH

        r = recognizer.recognize("Investigate customer 4521")
        assert r.intent == Intent.CUSTOMER_INVESTIGATION
    """

    # Confidence floor below which UNKNOWN is returned even for a matched intent
    _CONFIDENCE_THRESHOLD: float = 0.10

    def __init__(self) -> None:
        logger.debug(
            "IntentRecognizer initialised with %d catalogue entries across %d intents.",
            len(KEYWORD_CATALOGUE),
            len(MAX_SCORE_PER_INTENT),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @timed("Intent Recognition")
    def recognize(self, query: str) -> IntentResult:
        """
        Classifies *query* into the most appropriate Intent.

        Confidence is normalised per-intent: a query that matches half of
        DATASET_ANALYSIS's rules receives the same confidence (0.5) as one
        that matches half of CUSTOMER_INVESTIGATION's rules, regardless of
        how many total rules each intent has.

        Args:
            query: Raw natural-language input from the analyst.
                   Empty or whitespace-only strings return UNKNOWN.

        Returns:
            IntentResult with intent, confidence ∈ [0, 1], and
            the matched keyword phrases that drove the decision.
        """
        if not query or not query.strip():
            logger.warning("IntentRecognizer received an empty query.")
            return self._unknown_result(query or "", "")

        normalized = self._normalize(query)
        logger.debug(
            "Recognizing intent for query: '%s' → normalized: '%s'", query, normalized
        )

        raw_scores, matched_per_intent = self._score_all(normalized)

        if not raw_scores:
            return self._unknown_result(query, normalized)

        # Per-intent normalised confidence
        confidences: Dict[Intent, float] = {
            intent: min(raw / MAX_SCORE_PER_INTENT.get(intent, 1.0), 1.0)
            for intent, raw in raw_scores.items()
        }

        best_intent = max(confidences, key=lambda i: confidences[i])
        confidence = confidences[best_intent]

        if confidence < self._CONFIDENCE_THRESHOLD:
            logger.info(
                "No intent matched with sufficient confidence "
                "(best=%s confidence=%.3f < threshold=%.3f). Returning UNKNOWN.",
                best_intent.value, confidence, self._CONFIDENCE_THRESHOLD,
            )
            return self._unknown_result(query, normalized)

        phrases = matched_per_intent.get(best_intent, [])
        logger.info(
            "Intent recognized: %s (confidence=%.2f, phrases=%s)",
            best_intent.value, confidence, phrases,
        )

        return IntentResult(
            intent=best_intent,
            confidence=round(confidence, 4),
            matched_phrases=phrases,
            raw_query=query,
            normalized_query=normalized,
        )

    def supported_intents(self) -> List[Intent]:
        """Returns all supported Intent values (excluding UNKNOWN)."""
        return [i for i in Intent if i != Intent.UNKNOWN]

    # ------------------------------------------------------------------
    # Internal methods
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(text: str) -> str:
        """
        Normalises a query string for reliable keyword matching.

        Steps:
          1. Unicode NFC normalisation.
          2. Lowercase.
          3. Replace punctuation / non-alphanumeric characters with spaces.
          4. Collapse multiple spaces into one and strip.
        """
        text = unicodedata.normalize("NFC", text)
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _score_all(
        normalized: str,
    ) -> Tuple[Dict[Intent, float], Dict[Intent, List[str]]]:
        """
        Evaluates every catalogue entry against *normalized* and aggregates
        raw scores and matched phrases per intent.

        Returns:
            raw_scores:        Dict[Intent → sum of matched weights].
            matched_per_intent: Dict[Intent → list of matched phrase strings].
        """
        raw_scores: Dict[Intent, float] = {}
        matched: Dict[Intent, List[str]] = {}
        tokens: set = set(normalized.split())

        for intent, (weight, group) in KEYWORD_CATALOGUE:
            if all(token in tokens for token in group):
                raw_scores[intent] = raw_scores.get(intent, 0.0) + weight
                phrase = " ".join(group)
                matched.setdefault(intent, []).append(phrase)

        return raw_scores, matched

    @staticmethod
    def _unknown_result(raw_query: str, normalized: str) -> IntentResult:
        return IntentResult(
            intent=Intent.UNKNOWN,
            confidence=0.0,
            matched_phrases=[],
            raw_query=raw_query,
            normalized_query=normalized,
        )
