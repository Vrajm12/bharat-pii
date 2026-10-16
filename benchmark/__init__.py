"""T13: Benchmark evaluation infrastructure, matching engine, metrics, failure analysis, and stats."""

from .evaluator import EvaluationResult, Evaluator
from .failure_analysis import FailureInstance, analyze_failures
from .matching import match_predictions
from .metrics import MetricScore, aggregate_metrics, compute_metrics
from .runner import load_canonical_benchmark_records, run_experiment
from .schema import GoldEntity, Match, MatchingResult, Prediction
from .stats import (
    aggregate_by_base_kind,
    aggregate_by_decoy_class,
    aggregate_by_difficulty,
    aggregate_by_language,
    aggregate_by_perturbation_family,
    aggregate_by_pii_type,
    aggregate_by_semantic_role,
    aggregate_results,
    count_failures_by_category,
    group_and_aggregate,
)

__all__ = [
    "Prediction",
    "GoldEntity",
    "Match",
    "MatchingResult",
    "match_predictions",
    "MetricScore",
    "compute_metrics",
    "aggregate_metrics",
    "FailureInstance",
    "analyze_failures",
    "EvaluationResult",
    "Evaluator",
    "aggregate_results",
    "group_and_aggregate",
    "aggregate_by_language",
    "aggregate_by_pii_type",
    "aggregate_by_semantic_role",
    "aggregate_by_perturbation_family",
    "aggregate_by_difficulty",
    "aggregate_by_base_kind",
    "aggregate_by_decoy_class",
    "count_failures_by_category",
    "load_canonical_benchmark_records",
    "run_experiment",
]
