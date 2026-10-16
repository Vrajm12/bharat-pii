"""T13: Benchmark metrics computation (PROJECT_SPEC.md §20.4, §20.5).

Implements the frozen M1-M6 metrics and the exact F1-F4 entity failure partition:
- M1: Entity Precision (|TP_type| / |predictions|)
- M2: Entity Recall (|TP_type| / N)
- M3: Entity F1 (harmonic mean of M1 and M2)
- M4: Exact-Span F1 (harmonic mean using |TP_exact|)
- M5: Type Accuracy (|TP_type| / |L|)
- M6: False Positive Rate (|unmatched_predictions| / |predictions|)

Invariants:
- 0.0 <= M_k <= 1.0 for all k in 1..6
- F1 (MISSED_PII) + F2 (WRONG_SPAN) + F3 (WRONG_TYPE) + TP_exact == N
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .schema import MatchingResult


@dataclass(frozen=True)
class MetricScore:
    """Evaluated metric scores and partition counts (PROJECT_SPEC.md §20.4)."""

    n_gold: int
    n_predictions: int
    tp_type: int
    tp_exact: int
    localized: int
    m1_precision: float
    m2_recall: float
    m3_f1: float
    m4_exact_f1: float
    m5_type_accuracy: float
    m6_fpr: float
    f1_missed: int
    f2_wrong_span: int
    f3_wrong_type: int
    f4_false_pos: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_gold": self.n_gold,
            "n_predictions": self.n_predictions,
            "tp_type": self.tp_type,
            "tp_exact": self.tp_exact,
            "localized": self.localized,
            "m1_precision": self.m1_precision,
            "m2_recall": self.m2_recall,
            "m3_f1": self.m3_f1,
            "m4_exact_f1": self.m4_exact_f1,
            "m5_type_accuracy": self.m5_type_accuracy,
            "m6_fpr": self.m6_fpr,
            "f1_missed": self.f1_missed,
            "f2_wrong_span": self.f2_wrong_span,
            "f3_wrong_type": self.f3_wrong_type,
            "f4_false_pos": self.f4_false_pos,
        }


def _harmonic_mean(p: float, r: float) -> float:
    """Compute harmonic mean of precision and recall with zero-handling."""
    if p + r <= 0.0:
        return 0.0
    return (2.0 * p * r) / (p + r)


def compute_metrics_from_counts(
    n_gold: int,
    n_predictions: int,
    tp_type: int,
    tp_exact: int,
    localized: int,
    unmatched_predictions: int,
) -> MetricScore:
    """Compute M1-M6 and error partition from aggregate counts.

    Handles zero-denominators deterministically without NaNs:
    - If n_gold == 0 and n_predictions == 0 (true negative): precision=1.0, recall=1.0, f1=1.0.
    - If n_predictions == 0 and n_gold > 0: precision=0.0, recall=0.0, f1=0.0.
    - If n_gold == 0 and n_predictions > 0: precision=0.0, recall=0.0, f1=0.0.
    """
    # M1: Entity Precision
    if n_predictions > 0:
        m1 = tp_type / n_predictions
    elif n_gold == 0:
        m1 = 1.0  # Clean true negative
    else:
        m1 = 0.0

    # M2: Entity Recall
    if n_gold > 0:
        m2 = tp_type / n_gold
    elif n_predictions == 0:
        m2 = 1.0  # Clean true negative
    else:
        m2 = 0.0

    # M3: Entity F1
    if n_gold == 0 and n_predictions == 0:
        m3 = 1.0
    else:
        m3 = _harmonic_mean(m1, m2)

    # M4: Exact-Span F1
    if n_predictions > 0:
        p_exact = tp_exact / n_predictions
    elif n_gold == 0:
        p_exact = 1.0
    else:
        p_exact = 0.0

    if n_gold > 0:
        r_exact = tp_exact / n_gold
    elif n_predictions == 0:
        r_exact = 1.0
    else:
        r_exact = 0.0

    if n_gold == 0 and n_predictions == 0:
        m4 = 1.0
    else:
        m4 = _harmonic_mean(p_exact, r_exact)

    # M5: Type Accuracy given localization
    if localized > 0:
        m5 = tp_type / localized
    else:
        m5 = 0.0

    # M6: False Positive Rate
    if n_predictions > 0:
        m6 = unmatched_predictions / n_predictions
    else:
        m6 = 0.0

    # Entity Failure Partition (§20.4)
    # F2: WRONG_SPAN (matched, right type, span not exact)
    f2 = tp_type - tp_exact
    # F3: WRONG_TYPE (matched, wrong type)
    f3 = localized - tp_type
    # F1: MISSED_PII (never matched)
    f1 = n_gold - localized
    # F4: FALSE_POS (predictions matched to nothing)
    f4 = unmatched_predictions

    return MetricScore(
        n_gold=n_gold,
        n_predictions=n_predictions,
        tp_type=tp_type,
        tp_exact=tp_exact,
        localized=localized,
        m1_precision=m1,
        m2_recall=m2,
        m3_f1=m3,
        m4_exact_f1=m4,
        m5_type_accuracy=m5,
        m6_fpr=m6,
        f1_missed=f1,
        f2_wrong_span=f2,
        f3_wrong_type=f3,
        f4_false_pos=f4,
    )


def compute_metrics(matching_result: MatchingResult) -> MetricScore:
    """Compute M1-M6 metrics for a single record's matching result."""
    n_gold = len(matching_result.matches) + len(matching_result.unmatched_gold)
    n_preds = len(matching_result.matches) + len(matching_result.unmatched_predictions)
    localized = len(matching_result.matches)
    tp_type = sum(1 for m in matching_result.matches if m.is_type_match)
    tp_exact = sum(1 for m in matching_result.matches if m.is_type_match and m.is_exact_span)
    unmatched_preds = len(matching_result.unmatched_predictions)

    return compute_metrics_from_counts(
        n_gold=n_gold,
        n_predictions=n_preds,
        tp_type=tp_type,
        tp_exact=tp_exact,
        localized=localized,
        unmatched_predictions=unmatched_preds,
    )


def aggregate_metrics(matching_results: list[MatchingResult]) -> MetricScore:
    """Micro-average metrics across a list of matching results."""
    total_gold = 0
    total_preds = 0
    total_localized = 0
    total_tp_type = 0
    total_tp_exact = 0
    total_unmatched_preds = 0

    for res in matching_results:
        total_gold += len(res.matches) + len(res.unmatched_gold)
        total_preds += len(res.matches) + len(res.unmatched_predictions)
        total_localized += len(res.matches)
        total_tp_type += sum(1 for m in res.matches if m.is_type_match)
        total_tp_exact += sum(1 for m in res.matches if m.is_type_match and m.is_exact_span)
        total_unmatched_preds += len(res.unmatched_predictions)

    return compute_metrics_from_counts(
        n_gold=total_gold,
        n_predictions=total_preds,
        tp_type=total_tp_type,
        tp_exact=total_tp_exact,
        localized=total_localized,
        unmatched_predictions=total_unmatched_preds,
    )
