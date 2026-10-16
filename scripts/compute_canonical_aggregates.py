"""Compute and return exact multi-seed (42, 43, 44) aggregated slices for B5 and B6."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def calc_stats(vals: list[float]) -> tuple[float, float]:
    n = len(vals)
    mean = sum(vals) / n
    variance = sum((x - mean) ** 2 for x in vals) / (n - 1)
    sd = math.sqrt(variance)
    return mean, sd


def get_slice_aggregates(slice_key: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Aggregate a breakdown slice across seeds 42, 43, 44 for B5 and B6.
    
    slice_key can be: 'metrics_by_pii_type', 'metrics_by_language', 'metrics_by_perturbation_family'.
    """
    b5_data = {}
    for s in (42, 43, 44):
        p = ROOT / f"reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed{s}_v0.18.json"
        with open(p, "r", encoding="utf-8") as f:
            b5_data[s] = json.load(f)[slice_key]

    b6_data = {}
    for s in (42, 43, 44):
        p = ROOT / f"reports/experiments/b6/evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed{s}_v0.18.json"
        with open(p, "r", encoding="utf-8") as f:
            b6_data[s] = json.load(f)[slice_key]

    categories = list(b5_data[42].keys())
    b5_agg = {}
    b6_agg = {}

    for cat in categories:
        if cat == "HARD_NEGATIVE":
            continue
        # B5
        b5_cat_metrics = {}
        for m_key in ["m1_precision", "m2_recall", "m3_f1", "m4_exact_f1", "m5_type_accuracy", "m6_fpr", "tp_exact", "tp_type", "f1_missed", "f2_wrong_span", "f3_wrong_type", "f4_false_pos", "n_predictions", "n_gold"]:
            vals = [b5_data[s][cat].get(m_key, 0.0) for s in (42, 43, 44)]
            mean, sd = calc_stats(vals)
            b5_cat_metrics[m_key] = {"mean": mean, "sd": sd, "values": vals}
        b5_agg[cat] = b5_cat_metrics

        # B6
        b6_cat_metrics = {}
        for m_key in ["m1_precision", "m2_recall", "m3_f1", "m4_exact_f1", "m5_type_accuracy", "m6_fpr", "tp_exact", "tp_type", "f1_missed", "f2_wrong_span", "f3_wrong_type", "f4_false_pos", "n_predictions", "n_gold"]:
            vals = [b6_data[s][cat].get(m_key, 0.0) for s in (42, 43, 44)]
            mean, sd = calc_stats(vals)
            b6_cat_metrics[m_key] = {"mean": mean, "sd": sd, "values": vals}
        b6_agg[cat] = b6_cat_metrics

    return b5_agg, b6_agg


if __name__ == "__main__":
    b5_type, b6_type = get_slice_aggregates("metrics_by_pii_type")
    print("Categories:", list(b5_type.keys()))
    for cat in b5_type:
        print(f"{cat:15s} | B5 Exact F1: {b5_type[cat]['m4_exact_f1']['mean']:.4f} | B6 Exact F1: {b6_type[cat]['m4_exact_f1']['mean']:.4f}")
