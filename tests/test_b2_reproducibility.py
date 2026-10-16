"""T13/B2: spaCy baseline reproducibility and regression tests (PROJECT_SPEC.md §19 B2, §20.4)."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from baselines.base import validate_predictions
from baselines.spacy import SpacyBaselineAdapter
from benchmark.runner import load_canonical_benchmark_records, run_experiment

ROOT = Path(__file__).resolve().parent.parent


def test_b2_prediction_generation_reproducibility():
    records = load_canonical_benchmark_records()
    adapter = SpacyBaselineAdapter()

    all_preds = []
    total_rejected = 0
    for r in records:
        text = r.get("text", "")
        preds = adapter.predict(text)
        valid, rejected = validate_predictions(preds, original_text=text)
        total_rejected += len(rejected)
        for p in preds:
            all_preds.append(p.to_dict())

    assert len(all_preds) == 1398
    assert total_rejected == 0

    pred_path = ROOT / "predictions" / "spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.jsonl"
    assert pred_path.exists()
    with open(pred_path, "r", encoding="utf-8") as f:
        stored_preds = [json.loads(line) for line in f if line.strip()]

    assert len(stored_preds) == 1398
    for p_gen, p_store in zip(all_preds, stored_preds):
        assert p_gen["type"] == p_store["type"]
        assert p_gen["start"] == p_store["start"]
        assert p_gen["end"] == p_store["end"]
        assert p_gen["text"] == p_store["text"]


def test_b2_evaluation_metrics_reproducibility():
    adapter = SpacyBaselineAdapter()
    report = run_experiment(adapter, save_artifacts=False)

    metrics = report["metrics_overall"]

    assert metrics["n_gold"] == 724
    assert metrics["n_predictions"] == 1398
    assert metrics["tp_type"] == 44
    assert metrics["tp_exact"] == 35
    assert metrics["localized"] == 515

    assert abs(metrics["m1_precision"] - 0.031473533619456366) < 1e-10
    assert abs(metrics["m2_recall"] - 0.06077348066298342) < 1e-10
    assert abs(metrics["m3_f1"] - 0.04147031102733271) < 1e-10
    assert abs(metrics["m4_exact_f1"] - 0.03298774740810557) < 1e-10
    assert abs(metrics["m5_type_accuracy"] - 0.0854368932038835) < 1e-10
    assert abs(metrics["m6_fpr"] - 0.6316165951359084) < 1e-10

    # Error partition
    assert metrics["f1_missed"] == 209
    assert metrics["f2_wrong_span"] == 9
    assert metrics["f3_wrong_type"] == 471
    assert metrics["f4_false_pos"] == 883
    assert (
        metrics["f1_missed"]
        + metrics["f2_wrong_span"]
        + metrics["f3_wrong_type"]
        + metrics["tp_exact"]
        == metrics["n_gold"]
    )
