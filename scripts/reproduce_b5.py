#!/usr/bin/env python3
"""Reproduction Script for Baseline B5 (Indian-Adapted XLM-RoBERTa).

WARNING: Outputs are NON-CANONICAL REPRODUCTION ARTIFACTS.
This script executes inference on the canonical 964-record benchmark using
the trained B5 checkpoint and writes outputs exclusively to `reproduction/b5/`.
Canonical predictions and reports under `predictions/` and `reports/` are never overwritten.

Usage:
    python scripts/reproduce_b5.py [--seed 42] [--device -1]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from baselines.transformer_adapted import TransformerAdaptedBaselineAdapter
from benchmark.evaluator import Evaluator
from benchmark.runner import load_canonical_benchmark_records
from benchmark.schema import Prediction
from benchmark.stats import aggregate_results


def reproduce_b5(seed: int = 42, device: int | str = -1, output_dir: Path | None = None) -> dict[str, Any]:
    out_dir = output_dir or (ROOT / "reproduction" / "b5")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Normalize device for transformers pipeline
    dev_norm: int | str = -1
    if isinstance(device, str):
        if device in ["-1", "cpu"]:
            dev_norm = -1
        elif device.isdigit():
            dev_norm = int(device)
        else:
            dev_norm = device
    else:
        dev_norm = device

    print(f"[REPRODUCTION B5] Loading checkpoint for seed {seed} on device {dev_norm}...")
    adapter = TransformerAdaptedBaselineAdapter(seed=seed, device=dev_norm)

    print("[REPRODUCTION B5] Loading canonical 964-record benchmark...")
    records = load_canonical_benchmark_records()

    pred_file = out_dir / f"reproduction_b5_seed{seed}_predictions.jsonl"
    report_file = out_dir / f"reproduction_b5_seed{seed}_evaluation.json"

    print(f"[REPRODUCTION B5] Generating predictions -> {pred_file}...")
    preds_by_variant: dict[str, list[Prediction]] = {}
    all_preds = []

    with open(pred_file, "w", encoding="utf-8") as f_out:
        for rec in records:
            vid = rec["variant_id"]
            text = rec["text"]
            preds = adapter.predict(text)

            linked = []
            for p in preds:
                pred_dict = {
                    "variant_id": vid,
                    "type": p.type,
                    "start": p.start,
                    "end": p.end,
                    "text": p.text,
                    "confidence": p.confidence,
                    "status": p.status,
                    "rejection_reason": p.rejection_reason,
                    "reproduction_metadata": "NON-CANONICAL REPRODUCTION ARTIFACT",
                }
                f_out.write(json.dumps(pred_dict, ensure_ascii=False) + "\n")

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
                linked.append(linked_p)
                all_preds.append(linked_p)

            preds_by_variant[vid] = linked

    print("[REPRODUCTION B5] Evaluating predictions...")
    evaluator = Evaluator()
    eval_results = evaluator.evaluate_batch(records, preds_by_variant)
    metrics = aggregate_results(eval_results)
    metrics_dict = metrics.to_dict() if hasattr(metrics, "to_dict") else dict(metrics)

    report_payload = {
        "artifact_nature": "NON-CANONICAL REPRODUCTION ARTIFACT",
        "system": "B5_Adapted_XLM_R",
        "seed": seed,
        "n_records": len(records),
        "n_predictions": len(all_preds),
        "metrics_overall": metrics_dict,
    }

    with open(report_file, "w", encoding="utf-8") as f_rep:
        json.dump(report_payload, f_rep, indent=2)

    print("=" * 64)
    print("   B5 REPRODUCTION EVALUATION SUMMARY (NON-CANONICAL)")
    print("=" * 64)
    print(f"  Seed                     : {seed}")
    print(f"  Total Predictions        : {len(all_preds)}")
    print(f"  Exact Matches (TP_exact) : {metrics_dict['tp_exact']}")
    print(f"  Wrong Span (F2 Boundary) : {metrics_dict['f2_wrong_span']}")
    print(f"  False Positives (F4)     : {metrics_dict['f4_false_pos']}")
    print(f"  M1 Precision             : {metrics_dict['m1_precision']:.4f}")
    print(f"  M2 Recall                : {metrics_dict['m2_recall']:.4f}")
    print(f"  M3 Type F1               : {metrics_dict['m3_f1']:.4f}")
    print(f"  M4 Exact F1              : {metrics_dict['m4_exact_f1']:.4f}")
    print(f"  Artifact Location        : {report_file}")
    print("=" * 64)

    return report_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproduce B5 evaluation into reproduction/b5/.")
    parser.add_argument("--seed", type=int, default=42, choices=[42, 43, 44], help="Seed (42, 43, 44)")
    parser.add_argument("--device", default="-1", help="Device (-1 for CPU, 0 for GPU)")
    parser.add_argument("--output_dir", type=Path, default=None, help="Output directory")

    args = parser.parse_args()
    try:
        reproduce_b5(seed=args.seed, device=args.device, output_dir=args.output_dir)
        return 0
    except Exception as e:
        print(f"[ERROR] B5 reproduction failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
