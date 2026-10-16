"""T13: Failure analysis and error taxonomy attribution (PROJECT_SPEC.md §23, §20.4, §20.5).

Implements the frozen F1-F9 failure taxonomy:
- F1: MISSED_PII (entity not detected)
- F2: WRONG_SPAN (partial or over-extended boundary)
- F3: WRONG_TYPE (localized entity, wrong category)
- F4: FALSE_POSITIVE (non-PII predicted as PII; tagged with decoy_class on hard negatives)
- F5: CONTEXT_FAILURE (attributable to implicit/ambiguous context or A3/A4 label noise)
- F6: LINGUISTIC_FAILURE (attributable to Hindi / Romanized / code-mixed form)
- F7: FORMATTING_FAILURE (attributable to spacing / punctuation A1/A2)
- F8: ADVERSARIAL_FAILURE (under deliberate perturbation A1-A5)
- F9: SCRIPT_FAILURE (attributable specifically to Devanagari realization HI_DEVA_PII)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schema import GoldEntity, Match, MatchingResult, Prediction


@dataclass(frozen=True)
class FailureInstance:
    """A classified failure instance produced during evaluation."""

    failure_id: str  # 'F1', 'F2', 'F3', 'F4'
    primary_category: str  # 'MISSED_PII', 'WRONG_SPAN', 'WRONG_TYPE', 'FALSE_POSITIVE'
    secondary_tags: list[str] = field(default_factory=list)  # F5..F9 secondary attributions
    gold_entity: GoldEntity | None = None
    prediction: Prediction | None = None
    decoy_class: str | None = None  # Populated only on designed hard-negative distractor hit (§20.5)
    variant_id: str | None = None
    details: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "failure_id": self.failure_id,
            "primary_category": self.primary_category,
            "secondary_tags": list(self.secondary_tags),
            "details": self.details,
        }
        if self.gold_entity is not None:
            d["gold_entity"] = self.gold_entity.to_dict()
        if self.prediction is not None:
            d["prediction"] = self.prediction.to_dict()
        if self.decoy_class is not None:
            d["decoy_class"] = self.decoy_class
        if self.variant_id is not None:
            d["variant_id"] = self.variant_id
        return d


def _derive_secondary_tags(metadata: dict[str, Any] | None) -> list[str]:
    """Derive secondary failure attribution tags (F5-F9) from record metadata (§23)."""
    if not metadata:
        return []

    tags = []
    perturbation = metadata.get("perturbation", {})
    fam = perturbation.get("family", "NONE")
    lang = metadata.get("language", "EN")
    context = metadata.get("context", "EXPLICIT")

    # F8: ADVERSARIAL_FAILURE (under deliberate perturbation A1-A5)
    if fam in ("A1", "A2", "A3", "A4", "A5") or metadata.get("difficulty") == "ADVERSARIAL":
        tags.append("F8_ADVERSARIAL_FAILURE")
        tags.append(f"FAMILY_{fam}")

    # F7: FORMATTING_FAILURE (attributable to spacing/punctuation A1, A2)
    if fam in ("A1", "A2"):
        tags.append("F7_FORMATTING_FAILURE")

    # F5: CONTEXT_FAILURE (attributable to A3/A4 label noise or implicit context)
    if fam in ("A3", "A4") or context in ("SEMI_EXPLICIT", "IMPLICIT", "UNLABELLED"):
        tags.append("F5_CONTEXT_FAILURE")

    # F6: LINGUISTIC_FAILURE (attributable to Hindi / Romanized / code-mixed form)
    if lang in ("ROM_HI", "HINGLISH", "INFORMAL_HINGLISH", "IN_EN", "HI_LATIN_PII"):
        tags.append("F6_LINGUISTIC_FAILURE")

    # F9: SCRIPT_FAILURE (attributable specifically to Devanagari script)
    if lang == "HI_DEVA_PII" or metadata.get("carrier_script") == "DEVANAGARI":
        tags.append("F9_SCRIPT_FAILURE")

    return tags


def _find_overlapping_distractor(
    pred: Prediction, distractors: list[dict[str, Any]] | None
) -> str | None:
    """Check if a false positive prediction overlaps a designed hard-negative distractor (§20.5)."""
    if not distractors:
        return None

    for d in distractors:
        d_start = d.get("start")
        d_end = d.get("end")
        if d_start is not None and d_end is not None:
            # Overlap check
            if max(d_start, pred.start) < min(d_end, pred.end):
                return d.get("decoy_class")
    return None


def analyze_failures(
    matching_result: MatchingResult,
    record_metadata: dict[str, Any] | None = None,
    distractors: list[dict[str, Any]] | None = None,
) -> list[FailureInstance]:
    """Analyze matching results and produce structured failure instances (§20.4, §23).

    Deterministic and sorted by position.
    """
    failures: list[FailureInstance] = []
    secondary_tags = _derive_secondary_tags(record_metadata)
    variant_id = record_metadata.get("variant_id") if record_metadata else None

    # 1. F1: MISSED_PII (unmatched gold entities)
    for g in matching_result.unmatched_gold:
        failures.append(
            FailureInstance(
                failure_id="F1",
                primary_category="MISSED_PII",
                secondary_tags=list(secondary_tags),
                gold_entity=g,
                prediction=None,
                variant_id=variant_id,
                details=f"Gold entity {g.type} at [{g.start}:{g.end}] not detected",
            )
        )

    # 2. Matches with errors (F2 WRONG_SPAN, F3 WRONG_TYPE)
    for m in matching_result.matches:
        if not m.is_type_match:
            # F3: WRONG_TYPE (localized, wrong category)
            failures.append(
                FailureInstance(
                    failure_id="F3",
                    primary_category="WRONG_TYPE",
                    secondary_tags=list(secondary_tags),
                    gold_entity=m.gold,
                    prediction=m.prediction,
                    variant_id=variant_id,
                    details=(
                        f"Gold entity {m.gold.type} at [{m.gold.start}:{m.gold.end}] "
                        f"predicted as wrong type {m.prediction.type} at [{m.prediction.start}:{m.prediction.end}]"
                    ),
                )
            )
        elif not m.is_exact_span:
            # F2: WRONG_SPAN (correct type, boundary not exact)
            failures.append(
                FailureInstance(
                    failure_id="F2",
                    primary_category="WRONG_SPAN",
                    secondary_tags=list(secondary_tags),
                    gold_entity=m.gold,
                    prediction=m.prediction,
                    variant_id=variant_id,
                    details=(
                        f"Gold entity {m.gold.type} at [{m.gold.start}:{m.gold.end}] "
                        f"predicted with inexact span [{m.prediction.start}:{m.prediction.end}] (IoU={m.iou:.3f})"
                    ),
                )
            )

    # 3. F4: FALSE_POSITIVE (unmatched predictions)
    for p in matching_result.unmatched_predictions:
        decoy_class = _find_overlapping_distractor(p, distractors)
        tags = list(secondary_tags)
        if decoy_class:
            tags.append(f"DECOY_{decoy_class}")

        failures.append(
            FailureInstance(
                failure_id="F4",
                primary_category="FALSE_POSITIVE",
                secondary_tags=tags,
                gold_entity=None,
                prediction=p,
                decoy_class=decoy_class,
                variant_id=variant_id,
                details=(
                    f"False positive prediction {p.type} at [{p.start}:{p.end}]"
                    + (f" (decoy: {decoy_class})" if decoy_class else "")
                ),
            )
        )

    # Deterministic sorting
    def sort_key(f: FailureInstance):
        start = (
            f.gold_entity.start
            if f.gold_entity
            else (f.prediction.start if f.prediction else 0)
        )
        return (f.failure_id, start, f.details)

    failures.sort(key=sort_key)
    return failures
