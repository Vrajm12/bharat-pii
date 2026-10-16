"""T13: Statistical aggregation across evaluation slices (PROJECT_SPEC.md §20, §22).

Aggregates already-computed per-record evaluation results across benchmark slices:
- Pooled M1-M6 calculation from pooled numerators and denominators (avoids percentage-of-percentages bias)
- Aggregation by language, PII type, semantic role, perturbation family, difficulty, base kind, and decoy class
- Failure counts aggregation (F1-F9)
- Deterministic, stably ordered outputs
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from .evaluator import EvaluationResult
from .metrics import MetricScore, aggregate_metrics


def aggregate_results(results: list[EvaluationResult]) -> MetricScore:
    """Compute pooled micro-average M1-M6 metrics across a collection of evaluation results.

    Pools exact numerators and denominators without percentage-of-percentages distortion.
    """
    matching_results = [r.matching_result for r in results]
    return aggregate_metrics(matching_results)


def group_and_aggregate(
    results: list[EvaluationResult],
    key_fn: Callable[[EvaluationResult], str | None],
) -> dict[str, MetricScore]:
    """Group evaluation results by a slice key and compute pooled metrics per slice.

    Returns a deterministically sorted dictionary by group key.
    """
    groups: dict[str, list[EvaluationResult]] = defaultdict(list)
    for r in results:
        key = key_fn(r)
        if key is not None:
            groups[key].append(r)

    aggregated: dict[str, MetricScore] = {}
    for key in sorted(groups.keys()):
        aggregated[key] = aggregate_results(groups[key])
    return aggregated


def aggregate_by_language(results: list[EvaluationResult]) -> dict[str, MetricScore]:
    """Aggregate results by language condition (EN, IN_EN, ROM_HI, HINGLISH, etc.)."""
    return group_and_aggregate(results, lambda r: r.record_metadata.get("language"))


def _extract_pii_type(r: EvaluationResult) -> str | None:
    if r.record_metadata.get("pii_type"):
        return r.record_metadata["pii_type"]
    entities = r.record_metadata.get("entities", [])
    if entities:
        return entities[0].get("type")
    pii = r.record_metadata.get("pii", [])
    if pii:
        return pii[0].get("type")
    if r.matching_result.matches:
        return r.matching_result.matches[0].gold.type
    if r.matching_result.unmatched_gold:
        return r.matching_result.unmatched_gold[0].type
    if r.record_metadata.get("base_kind") == "HARD_NEGATIVE":
        return "HARD_NEGATIVE"
    return None


def aggregate_by_pii_type(results: list[EvaluationResult]) -> dict[str, MetricScore]:
    """Aggregate results by declared primary PII type."""
    return group_and_aggregate(results, _extract_pii_type)


def aggregate_by_semantic_role(results: list[EvaluationResult]) -> dict[str, MetricScore]:
    """Aggregate results by declared semantic role."""
    return group_and_aggregate(results, lambda r: r.record_metadata.get("semantic_role"))


def aggregate_by_perturbation_family(results: list[EvaluationResult]) -> dict[str, MetricScore]:
    """Aggregate results by perturbation family (A1, A2, A3, A4, A5, NONE)."""
    return group_and_aggregate(
        results,
        lambda r: r.record_metadata.get("perturbation", {}).get("family", "NONE"),
    )


def aggregate_by_difficulty(results: list[EvaluationResult]) -> dict[str, MetricScore]:
    """Aggregate results by difficulty level (STANDARD, HARD_NEGATIVE, ADVERSARIAL)."""
    return group_and_aggregate(results, lambda r: r.record_metadata.get("difficulty"))


def aggregate_by_base_kind(results: list[EvaluationResult]) -> dict[str, MetricScore]:
    """Aggregate results by base kind (POSITIVE, HARD_NEGATIVE)."""
    return group_and_aggregate(results, lambda r: r.record_metadata.get("base_kind"))


def aggregate_by_decoy_class(results: list[EvaluationResult]) -> dict[str, MetricScore]:
    """Aggregate hard-negative results by distractor decoy class."""
    groups: dict[str, list[EvaluationResult]] = defaultdict(list)
    for r in results:
        distractors = r.record_metadata.get("distractors", [])
        for d in distractors:
            dc = d.get("decoy_class")
            if dc:
                groups[dc].append(r)

    aggregated: dict[str, MetricScore] = {}
    for key in sorted(groups.keys()):
        aggregated[key] = aggregate_results(groups[key])
    return aggregated


def count_failures_by_category(results: list[EvaluationResult]) -> dict[str, int]:
    """Count all primary and secondary failure occurrences across evaluation results.

    Returns a deterministically sorted dictionary of failure tag counts.
    """
    counts: dict[str, int] = defaultdict(int)
    for r in results:
        for f in r.failures:
            counts[f.failure_id] += 1
            counts[f.primary_category] += 1
            for tag in f.secondary_tags:
                counts[tag] += 1

    return {k: counts[k] for k in sorted(counts.keys())}
