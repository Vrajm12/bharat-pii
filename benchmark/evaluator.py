"""T13: Benchmark evaluator orchestration layer (PROJECT_SPEC.md §20, §24).

Orchestrates the evaluation of detector predictions against benchmark dataset records:
1. Ingests dataset record and detector predictions.
2. Extracts ground-truth entities and text bounds.
3. Invokes benchmark.matching.match_predictions.
4. Invokes benchmark.metrics.compute_metrics.
5. Invokes benchmark.failure_analysis.analyze_failures.
6. Emits structured, immutable EvaluationResult.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .failure_analysis import FailureInstance, analyze_failures
from .matching import match_predictions
from .metrics import MetricScore, compute_metrics
from .schema import GoldEntity, MatchingResult, Prediction


@dataclass(frozen=True)
class EvaluationResult:
    """Structured evaluation outcome for a single dataset record."""

    variant_id: str
    record_metadata: dict[str, Any]
    matching_result: MatchingResult
    metrics: MetricScore
    failures: list[FailureInstance] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "metrics": self.metrics.to_dict(),
            "failures": [f.to_dict() for f in self.failures],
            "n_matches": len(self.matching_result.matches),
            "n_unmatched_gold": len(self.matching_result.unmatched_gold),
            "n_unmatched_predictions": len(self.matching_result.unmatched_predictions),
            "n_malformed_predictions": len(self.matching_result.malformed_predictions),
        }


class Evaluator:
    """Thin orchestration engine for benchmark evaluation (§20.2–20.10)."""

    def evaluate_record(
        self,
        record: dict[str, Any],
        predictions: list[Prediction],
    ) -> EvaluationResult:
        """Evaluate detector predictions against a single dataset record.

        Args:
            record: Dataset record dict (positive, hard-negative, or adversarial).
            predictions: List of Prediction objects.

        Returns:
            Structured EvaluationResult containing matches, metrics, and failures.
        """
        variant_id = record.get("variant_id", "UNKNOWN")
        text = record.get("text")
        base_kind = record.get("base_kind", "POSITIVE")

        # Extract gold entities (N=0 for hard negatives, entities[0..] for positives/adversarial)
        gold_entities: list[GoldEntity] = []
        if base_kind == "POSITIVE" and "entities" in record:
            gold_entities = [GoldEntity.from_dict(e) for e in record["entities"]]

        distractors = record.get("distractors", [])

        # 1. Matching (calls benchmark.matching)
        matching_res = match_predictions(
            gold_entities=gold_entities,
            predictions=predictions,
            original_text=text,
        )

        # 2. Metrics (calls benchmark.metrics)
        metrics = compute_metrics(matching_res)

        # 3. Failure Analysis (calls benchmark.failure_analysis)
        failures = analyze_failures(
            matching_result=matching_res,
            record_metadata=record,
            distractors=distractors,
        )

        return EvaluationResult(
            variant_id=variant_id,
            record_metadata=dict(record),
            matching_result=matching_res,
            metrics=metrics,
            failures=failures,
        )

    def evaluate_batch(
        self,
        records: list[dict[str, Any]],
        predictions_by_variant: dict[str, list[Prediction]],
    ) -> list[EvaluationResult]:
        """Evaluate a batch of records against their predictions.

        Deterministic ordering matching records list.
        """
        results: list[EvaluationResult] = []
        for rec in records:
            vid = rec.get("variant_id", "")
            preds = predictions_by_variant.get(vid, [])
            res = self.evaluate_record(rec, preds)
            results.append(res)
        return results
