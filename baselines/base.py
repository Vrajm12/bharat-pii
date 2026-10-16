"""T13: Baseline adapter abstract interface and prediction validation (PROJECT_SPEC.md §20.6, §20.7, §20.8).

Defines the minimal interface contract for all baseline PII detectors:
- system_name: str
- system_version: str
- predict(text: str) -> list[Prediction]
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from benchmark.schema import Prediction


def validate_predictions(
    predictions: list[Prediction],
    original_text: str,
) -> tuple[list[Prediction], list[Prediction]]:
    """Validate detector predictions against the original text bounds and character content (§20.6).

    Args:
        predictions: List of predictions from an adapter.
        original_text: Exact unmodified input text.

    Returns:
        tuple of (valid_predictions, rejected_predictions)
    """
    text_len = len(original_text)
    valid: list[Prediction] = []
    rejected: list[Prediction] = []

    for p in predictions:
        # Check structural bounds: 0 <= start < end <= text_len
        if (
            not isinstance(p.start, int)
            or not isinstance(p.end, int)
            or p.start < 0
            or p.end <= p.start
            or p.end > text_len
        ):
            rej_p = Prediction(
                type=p.type,
                start=p.start,
                end=p.end,
                text=p.text,
                confidence=p.confidence,
                variant_id=p.variant_id,
                status="REJECTED",
                rejection_reason="INVALID_SPAN_OFFSETS",
            )
            rejected.append(rej_p)
            continue

        # If prediction text is supplied, check exact substring identity
        if p.text is not None and original_text[p.start : p.end] != p.text:
            rej_p = Prediction(
                type=p.type,
                start=p.start,
                end=p.end,
                text=p.text,
                confidence=p.confidence,
                variant_id=p.variant_id,
                status="REJECTED",
                rejection_reason="TEXT_SPAN_MISMATCH",
            )
            rejected.append(rej_p)
            continue

        valid.append(p)

    return valid, rejected


class BaselineAdapter(ABC):
    """Abstract interface for all baseline PII detectors (PROJECT_SPEC.md §20.7).

    One call, one raw text input, one list of Prediction objects out.
    """

    @property
    @abstractmethod
    def system_name(self) -> str:
        """Exact system identifier (e.g. 'regex', 'spacy', 'presidio')."""
        ...

    @property
    @abstractmethod
    def system_version(self) -> str:
        """Exact system/model/configuration version (e.g. '2.2.355_india_enabled')."""
        ...

    @abstractmethod
    def predict(self, text: str) -> list[Prediction]:
        """Run detection on a single raw text string.

        Must return Python Unicode code-point offsets into the exact original text (§20.6).
        """
        ...
