"""T13: Evaluation data models and prediction schemas (PROJECT_SPEC.md §20.2, §20.8, §20.9).

Defines the minimum typed structures required by the frozen evaluation contract:
- Prediction: Detector output entity (§20.2)
- GoldEntity: Ground-truth entity representation (§13)
- Match: Pairwise match result (§20.3)
- MatchingResult: Output of the bipartite matching algorithm (§20.3, §20.4)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Prediction:
    """A single predicted entity produced by a detector adapter (PROJECT_SPEC.md §20.2).

    Attributes:
        type: One of the eight taxonomy types, or an out-of-taxonomy label.
        start: Python Unicode code-point offset into the original input text.
        end: Python Unicode code-point offset into the original input text.
        text: The predicted substring (optional, redundant with text[start:end]).
        confidence: Prediction confidence / probability score (optional).
        variant_id: Linkage to the ground-truth record (optional at adapter level,
                    attached by the harness for batch evaluation).
        status: Validation status ('VALID' or 'REJECTED').
        rejection_reason: Reason code if status is 'REJECTED' (§20.9).
    """

    type: str
    start: int
    end: int
    text: str | None = None
    confidence: float | None = None
    variant_id: str | None = None
    status: str = "VALID"
    rejection_reason: str | None = None

    def is_structurally_valid(self, text_length: int | None = None) -> bool:
        """Check the strict structural boundary contract (§20.2, §20.6).

        0 <= start < end <= len(original_text)
        """
        if not isinstance(self.start, int) or not isinstance(self.end, int):
            return False
        if self.start < 0 or self.end <= self.start:
            return False
        if text_length is not None and self.end > text_length:
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary (§20.8)."""
        d: dict[str, Any] = {
            "type": self.type,
            "start": self.start,
            "end": self.end,
        }
        if self.text is not None:
            d["text"] = self.text
        if self.confidence is not None:
            d["confidence"] = self.confidence
        if self.variant_id is not None:
            d["variant_id"] = self.variant_id
        if self.status != "VALID":
            d["status"] = self.status
            if self.rejection_reason is not None:
                d["rejection_reason"] = self.rejection_reason
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Prediction:
        """Construct from a dictionary."""
        return cls(
            type=data["type"],
            start=data["start"],
            end=data["end"],
            text=data.get("text"),
            confidence=data.get("confidence"),
            variant_id=data.get("variant_id"),
            status=data.get("status", "VALID"),
            rejection_reason=data.get("rejection_reason"),
        )


@dataclass(frozen=True)
class GoldEntity:
    """A ground-truth entity from a benchmark dataset record (guidelines.md §4.4, §13).

    Attributes:
        type: The taxonomy PII type.
        start: Python Unicode code-point start offset.
        end: Python Unicode code-point end offset.
        base_pii_value: Original unperturbed PII string.
        realized_pii_value: Realized PII string in the text.
        occurrence_index: Bookkeeping index (ignored during prediction matching, §20.3).
    """

    type: str
    start: int
    end: int
    base_pii_value: str | None = None
    realized_pii_value: str | None = None
    occurrence_index: int = 0

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "type": self.type,
            "start": self.start,
            "end": self.end,
            "occurrence_index": self.occurrence_index,
        }
        if self.base_pii_value is not None:
            d["base_pii_value"] = self.base_pii_value
        if self.realized_pii_value is not None:
            d["realized_pii_value"] = self.realized_pii_value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GoldEntity:
        return cls(
            type=data["type"],
            start=data["start"],
            end=data["end"],
            base_pii_value=data.get("base_pii_value"),
            realized_pii_value=data.get("realized_pii_value"),
            occurrence_index=data.get("occurrence_index", 0),
        )


@dataclass(frozen=True)
class Match:
    """A matched gold entity and prediction pair (PROJECT_SPEC.md §20.3)."""

    gold: GoldEntity
    prediction: Prediction
    weight: float
    iou: float
    is_type_match: bool
    is_exact_span: bool


@dataclass
class MatchingResult:
    """Result of maximum-weight bipartite matching on a single record (§20.3, §20.4)."""

    matches: list[Match] = field(default_factory=list)
    unmatched_gold: list[GoldEntity] = field(default_factory=list)
    unmatched_predictions: list[Prediction] = field(default_factory=list)
    malformed_predictions: list[Prediction] = field(default_factory=list)
