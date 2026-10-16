"""Public Evaluation CLI for the Indian PII Robustness Benchmark.

Usage:
    python -m benchmark.evaluate --gold <gold.jsonl> --predictions <predictions.jsonl> [--output <metrics.json>]

This tool wraps the canonical benchmark evaluator and metrics engine to score
predictions against gold standard records.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from benchmark.evaluator import Evaluator
from benchmark.schema import Prediction
from benchmark.stats import aggregate_results


def load_gold_records(gold_path: Path) -> list[dict[str, Any]]:
    """Load gold records from a jsonl file or canonical corpus."""
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold record file not found: {gold_path}")

    records = []
    with open(gold_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as err:
                raise ValueError(f"Malformed JSON on line {line_num} of {gold_path}: {err}") from err

            # Normalize variant_id and text
            if "variant_id" not in rec and "record_id" in rec:
                rec["variant_id"] = rec["record_id"]
            elif "variant_id" not in rec and "base_id" in rec:
                rec["variant_id"] = rec["base_id"]

            if "text" not in rec and "canonical_text" in rec:
                rec["text"] = rec["canonical_text"]

            records.append(rec)
    return records


def load_predictions_by_variant(pred_path: Path) -> tuple[dict[str, list[Prediction]], int]:
    """Load predictions from a jsonl file and group by variant_id.
    
    Returns:
        tuple of (predictions_by_variant_id, total_prediction_count)
    """
    if not pred_path.exists():
        raise FileNotFoundError(f"Prediction file not found: {pred_path}")

    preds_by_variant: dict[str, list[Prediction]] = {}
    total_count = 0

    with open(pred_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as err:
                raise ValueError(f"Malformed JSON on line {line_num} of {pred_path}: {err}") from err

            vid = item.get("variant_id") or item.get("record_id")
            if not vid:
                raise ValueError(f"Missing variant_id/record_id on line {line_num} of {pred_path}")

            pred = Prediction(
                type=item["type"],
                start=int(item["start"]),
                end=int(item["end"]),
                text=item.get("text", ""),
                confidence=float(item.get("confidence", 1.0)),
                variant_id=vid,
                status=item.get("status", "VALID"),
                rejection_reason=item.get("rejection_reason"),
            )

            if vid not in preds_by_variant:
                preds_by_variant[vid] = []
            preds_by_variant[vid].append(pred)
            total_count += 1

    return preds_by_variant, total_count


def format_summary_table(metrics: dict[str, Any]) -> str:
    """Format evaluation metrics as an ASCII summary table."""
    lines = [
        "=" * 64,
        "   INDIAN PII ROBUSTNESS BENCHMARK — EVALUATION RESULTS",
        "=" * 64,
        f"  Total Gold Entities (N_gold)      : {metrics.get('n_gold', 0):>8}",
        f"  Total Predictions Emitted (N_pred): {metrics.get('n_predictions', 0):>8}",
        f"  Exact Matches (TP_exact)          : {metrics.get('tp_exact', 0):>8}",
        f"  Type Matches (TP_type)            : {metrics.get('tp_type', 0):>8}",
        "-" * 64,
        "  Error Partitions (Invariant: TP_exact + F1 + F2 + F3 == N_gold):",
        f"    F1 Missed Entities              : {metrics.get('f1_missed', 0):>8}",
        f"    F2 Boundary Errors (Wrong Span) : {metrics.get('f2_wrong_span', 0):>8}",
        f"    F3 Classification (Wrong Type)  : {metrics.get('f3_wrong_type', 0):>8}",
        f"    F4 False Positives (Spurious)   : {metrics.get('f4_false_pos', 0):>8}",
        "-" * 64,
        "  Primary Performance Metrics:",
        f"    M1 Precision (Type-Strict)      : {metrics.get('m1_precision', 0.0):>8.4f}",
        f"    M2 Recall (Type-Strict)         : {metrics.get('m2_recall', 0.0):>8.4f}",
        f"    M3 F1 Score (Type-Strict)       : {metrics.get('m3_f1', 0.0):>8.4f}",
        f"    M4 Exact F1 Score (Exact Bounds): {metrics.get('m4_exact_f1', 0.0):>8.4f}",
        f"    M5 Type Accuracy                : {metrics.get('m5_type_accuracy', 0.0):>8.4f}",
        f"    M6 False Positive Rate (FPR)    : {metrics.get('m6_fpr', 0.0):>8.4f}",
        "=" * 64,
    ]
    return "\n".join(lines)


def run_evaluation(gold_path: Path, pred_path: Path, output_path: Path | None = None) -> dict[str, Any]:
    """Execute evaluation and return metrics dictionary."""
    records = load_gold_records(gold_path)
    preds_by_variant, total_preds = load_predictions_by_variant(pred_path)

    evaluator = Evaluator()
    eval_results = evaluator.evaluate_batch(records, preds_by_variant)
    overall_metrics = aggregate_results(eval_results)
    metrics_dict = overall_metrics.to_dict() if hasattr(overall_metrics, "to_dict") else dict(overall_metrics)

    result_payload = {
        "n_records_evaluated": len(records),
        "n_predictions_total": total_preds,
        "metrics_overall": metrics_dict,
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, indent=2)

    return result_payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate PII detector predictions against Indian PII Robustness Benchmark gold records."
    )
    parser.add_argument(
        "--gold",
        type=Path,
        required=True,
        help="Path to gold records JSONL file.",
    )
    parser.add_argument(
        "--predictions",
        type=Path,
        required=True,
        help="Path to predictions JSONL file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to output evaluation results as JSON.",
    )

    args = parser.parse_args(argv)

    try:
        results = run_evaluation(args.gold, args.predictions, args.output)
        summary = format_summary_table(results["metrics_overall"])
        print(summary)
        if args.output:
            print(f"\n[INFO] Machine-readable metrics written to: {args.output}")
        return 0
    except Exception as e:
        print(f"[ERROR] Evaluation failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
