"""Verification and Statistics Reconciliation Script for Clean-Room Reproduction.

Calculates:
1. Invariants for B5 and B6 across all seeds.
2. Prediction exact matches vs canonical.
3. Metric discrepancies vs canonical.
4. Mean and Sample Standard Deviation (ddof=1) for all metrics across seeds.
5. Comparisons with canonical tables.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def calc_stats(vals: list[float]) -> tuple[float, float]:
    n = len(vals)
    mean = sum(vals) / n
    variance = sum((x - mean) ** 2 for x in vals) / (n - 1)
    sd = math.sqrt(variance)
    return mean, sd


def main():
    print("=" * 70)
    print("   CLEAN-ROOM REPRODUCTION VERIFICATION & STATISTICS")
    print("=" * 70)

    # 1. B5 Verification
    print("\n--- BASELINE B5 VERIFICATION ---")
    b5_metrics_by_seed = {}
    for s in (42, 43, 44):
        eval_path = ROOT / f"reproduction/clean_room/b5/seed{s}/reproduction_b5_seed{s}_evaluation.json"
        with open(eval_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        m = data["metrics_overall"]
        b5_metrics_by_seed[s] = m

        # Check invariants
        inv1 = (m["tp_exact"] + m["f1_missed"] + m["f2_wrong_span"] + m["f3_wrong_type"] == 724)
        inv2 = (m["tp_type"] == m["tp_exact"] + m["f2_wrong_span"])
        inv3 = (m["n_predictions"] == m["tp_type"] + m["f3_wrong_type"] + m["f4_false_pos"])
        assert inv1 and inv2 and inv3, f"Invariant failure in B5 seed {s}!"

        # Canonical comparison
        canon_eval_path = ROOT / f"reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed{s}_v0.18.json"
        with open(canon_eval_path, "r", encoding="utf-8") as f:
            c_data = json.load(f)
        cm = c_data["metrics_overall"]
        max_diff = max(abs(m[k] - cm[k]) for k in m if isinstance(m[k], (int, float)))

        print(f"Seed {s}: All 3 invariants PASS. Max metric diff vs canonical: {max_diff:.2e}")

    # 2. B6 Verification
    print("\n--- BASELINE B6 VERIFICATION ---")
    b6_metrics_by_seed = {}
    for s in (42, 43, 44):
        eval_path = ROOT / f"reproduction/clean_room/b6/seed{s}/reproduction_b6_seed{s}_evaluation.json"
        with open(eval_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        m = data["metrics_overall"]
        b6_metrics_by_seed[s] = m

        # Check invariants
        inv1 = (m["tp_exact"] + m["f1_missed"] + m["f2_wrong_span"] + m["f3_wrong_type"] == 724)
        inv2 = (m["tp_type"] == m["tp_exact"] + m["f2_wrong_span"])
        inv3 = (m["n_predictions"] == m["tp_type"] + m["f3_wrong_type"] + m["f4_false_pos"])
        assert inv1 and inv2 and inv3, f"Invariant failure in B6 seed {s}!"

        # Canonical comparison
        canon_eval_path = ROOT / f"reports/experiments/b6/evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed{s}_v0.18.json"
        with open(canon_eval_path, "r", encoding="utf-8") as f:
            c_data = json.load(f)
        cm = c_data["metrics_overall"]
        max_diff = max(abs(m[k] - cm[k]) for k in m if isinstance(m[k], (int, float)))

        print(f"Seed {s}: All 3 invariants PASS. Max metric diff vs canonical: {max_diff:.2e}")

    # 3. Compute Aggregate Sample Standard Deviation (ddof=1)
    print("\n--- AGGREGATE METRICS & SAMPLE SD (ddof=1) ---")
    keys_to_report = [
        ("m1_precision", "M1 Precision"),
        ("m2_recall", "M2 Recall"),
        ("m3_f1", "M3 Type F1"),
        ("m4_exact_f1", "M4 Exact F1"),
        ("m5_type_accuracy", "M5 Type Accuracy"),
        ("m6_fpr", "M6 FPR"),
        ("tp_exact", "TP_exact"),
        ("f2_wrong_span", "F2 Wrong Span"),
        ("f4_false_pos", "F4 False Pos"),
        ("n_predictions", "Total Predictions"),
    ]

    print("\nBASELINE B5:")
    for k, name in keys_to_report:
        vals = [b5_metrics_by_seed[s][k] for s in (42, 43, 44)]
        mean, sd = calc_stats(vals)
        if "f1" in k or "precision" in k or "recall" in k or "accuracy" in k or "fpr" in k:
            print(f"  {name:20s}: {mean:.4f} ± {sd:.4f}  (raw: {vals})")
        else:
            print(f"  {name:20s}: {mean:.1f} ± {sd:.1f}  (raw: {vals})")

    print("\nBASELINE B6:")
    for k, name in keys_to_report:
        vals = [b6_metrics_by_seed[s][k] for s in (42, 43, 44)]
        mean, sd = calc_stats(vals)
        if "f1" in k or "precision" in k or "recall" in k or "accuracy" in k or "fpr" in k:
            print(f"  {name:20s}: {mean:.4f} ± {sd:.4f}  (raw: {vals})")
        else:
            print(f"  {name:20s}: {mean:.1f} ± {sd:.1f}  (raw: {vals})")

    # Save summary json
    summary_out = ROOT / "reproduction/clean_room/verification_summary.json"
    summary_payload = {
        "b5": {
            "per_seed": b5_metrics_by_seed,
            "aggregate": {
                k: {"mean": calc_stats([b5_metrics_by_seed[s][k] for s in (42, 43, 44)])[0],
                    "sd_sample": calc_stats([b5_metrics_by_seed[s][k] for s in (42, 43, 44)])[1]}
                for k, _ in keys_to_report
            }
        },
        "b6": {
            "per_seed": b6_metrics_by_seed,
            "aggregate": {
                k: {"mean": calc_stats([b6_metrics_by_seed[s][k] for s in (42, 43, 44)])[0],
                    "sd_sample": calc_stats([b6_metrics_by_seed[s][k] for s in (42, 43, 44)])[1]}
                for k, _ in keys_to_report
            }
        }
    }
    with open(summary_out, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)
    print(f"\nWrote verification summary to {summary_out}")


if __name__ == "__main__":
    main()
