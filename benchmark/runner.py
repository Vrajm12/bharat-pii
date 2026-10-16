"""T13/E01: Benchmark experiment runner (PROJECT_SPEC.md §§20–24).

Orchestrates running baseline adapters across canonical benchmark records,
validating predictions, evaluating matching and metrics, and persisting
canonical prediction and evaluation report artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from baselines.base import BaselineAdapter

from benchmark.evaluator import EvaluationResult, Evaluator
from benchmark.schema import Prediction
from benchmark.stats import (
    aggregate_by_base_kind,
    aggregate_by_decoy_class,
    aggregate_by_difficulty,
    aggregate_by_language,
    aggregate_by_perturbation_family,
    aggregate_by_pii_type,
    aggregate_by_semantic_role,
    aggregate_results,
    count_failures_by_category,
)

ROOT = Path(__file__).resolve().parent.parent


def load_canonical_benchmark_records(data_dir: Path | None = None) -> list[dict[str, Any]]:
    """Load the complete 964-record canonical benchmark corpus in deterministic sequence."""
    base_dir = data_dir or (ROOT / "data")
    canonical_files = [
        base_dir / "raw" / "base_instances.jsonl",
        base_dir / "raw" / "hard_negative_bases.jsonl",
        base_dir / "generated" / "language_realizations.jsonl",
        base_dir / "generated" / "hard_negative_realizations.jsonl",
        base_dir / "generated" / "adversarial_realizations.jsonl",
    ]

    records: list[dict[str, Any]] = []
    for file_path in canonical_files:
        if not file_path.exists():
            raise FileNotFoundError(f"Canonical dataset file not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                # Normalize text and variant_id for base records
                if "canonical_text" in rec and "text" not in rec:
                    rec["text"] = rec["canonical_text"]
                if "variant_id" not in rec:
                    rec["variant_id"] = rec["base_id"]
                records.append(rec)

    if len(records) != 964:
        raise ValueError(f"Expected 964 canonical records, loaded {len(records)}")

    return records


def run_experiment(
    adapter: Any,
    records: list[dict[str, Any]] | None = None,
    dataset_version: str = "0.18",
    save_artifacts: bool = True,
    predictions_dir: Path | None = None,
    reports_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute a baseline adapter against the benchmark and produce evaluation metrics."""
    from baselines.base import validate_predictions

    corpus_records = records if records is not None else load_canonical_benchmark_records()

    predictions_by_variant: dict[str, list[Prediction]] = {}
    all_predictions_list: list[Prediction] = []
    total_rejected = 0

    for rec in corpus_records:
        vid = rec["variant_id"]
        text = rec.get("text", "")
        raw_preds = adapter.predict(text)

        valid_preds, rejected_preds = validate_predictions(raw_preds, original_text=text)
        total_rejected += len(rejected_preds)

        linked_preds: list[Prediction] = []
        for p in raw_preds:
            linked_p = Prediction(
                type=p.type,
                start=p.start,
                end=p.end,
                text=p.text,
                confidence=p.confidence,
                variant_id=vid,
                status=p.status,
                rejection_reason=p.rejection_reason,
            )
            linked_preds.append(linked_p)
            all_predictions_list.append(linked_p)

        predictions_by_variant[vid] = linked_preds

    # Evaluate batch
    evaluator = Evaluator()
    eval_results = evaluator.evaluate_batch(corpus_records, predictions_by_variant)

    # Compute aggregations
    overall_metrics = aggregate_results(eval_results)
    by_lang = aggregate_by_language(eval_results)
    by_type = aggregate_by_pii_type(eval_results)
    by_role = aggregate_by_semantic_role(eval_results)
    by_family = aggregate_by_perturbation_family(eval_results)
    by_diff = aggregate_by_difficulty(eval_results)
    by_kind = aggregate_by_base_kind(eval_results)
    by_decoy = aggregate_by_decoy_class(eval_results)
    failures_breakdown = count_failures_by_category(eval_results)

    report_data: dict[str, Any] = {
        "system_name": adapter.system_name,
        "system_version": adapter.system_version,
        "dataset_version": dataset_version,
        "n_records_evaluated": len(eval_results),
        "n_predictions_total": len(all_predictions_list),
        "n_predictions_rejected": total_rejected,
        "metrics_overall": overall_metrics.to_dict(),
        "metrics_by_language": {k: v.to_dict() for k, v in by_lang.items()},
        "metrics_by_pii_type": {k: v.to_dict() for k, v in by_type.items()},
        "metrics_by_semantic_role": {k: v.to_dict() for k, v in by_role.items()},
        "metrics_by_perturbation_family": {k: v.to_dict() for k, v in by_family.items()},
        "metrics_by_difficulty": {k: v.to_dict() for k, v in by_diff.items()},
        "metrics_by_base_kind": {k: v.to_dict() for k, v in by_kind.items()},
        "metrics_by_decoy_class": {k: v.to_dict() for k, v in by_decoy.items()},
        "failures_breakdown": failures_breakdown,
    }

    if save_artifacts:
        # 1. Save predictions JSONL
        p_dir = predictions_dir or (ROOT / "predictions")
        p_dir.mkdir(parents=True, exist_ok=True)
        pred_file = p_dir / f"{adapter.system_name}_{adapter.system_version}_v{dataset_version}.jsonl"
        with open(pred_file, "w", encoding="utf-8") as f:
            for p in all_predictions_list:
                f.write(json.dumps(p.to_dict(), ensure_ascii=False) + "\n")

        # 2. Save evaluation report JSON
        r_dir = reports_dir or (ROOT / "reports")
        r_dir.mkdir(parents=True, exist_ok=True)
        report_file = r_dir / f"evaluation_{adapter.system_name}_{adapter.system_version}_v{dataset_version}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

    return report_data
