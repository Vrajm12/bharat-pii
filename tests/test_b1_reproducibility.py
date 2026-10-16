"""T13/E01: B1 Regex baseline reproducibility and regression tests (PROJECT_SPEC.md §19 B1, §20.4)."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from baselines.base import validate_predictions
from baselines.regex import RegexBaselineAdapter
from benchmark.runner import load_canonical_benchmark_records, run_experiment

ROOT = Path(__file__).resolve().parent.parent


def test_e01_corpus_record_count():
    records = load_canonical_benchmark_records()
    assert len(records) == 964


def test_e01_prediction_generation_reproducibility():
    records = load_canonical_benchmark_records()
    adapter = RegexBaselineAdapter()

    all_preds = []
    total_rejected = 0
    for r in records:
        text = r.get("text", "")
        preds = adapter.predict(text)
        valid, rejected = validate_predictions(preds, original_text=text)
        total_rejected += len(rejected)
        for p in preds:
            all_preds.append(p.to_dict())

    assert len(all_preds) == 582
    assert total_rejected == 0

    # Compare with stored canonical prediction artifact
    pred_path = ROOT / "predictions" / "regex_1.0.0_v0.18.jsonl"
    assert pred_path.exists()
    with open(pred_path, "r", encoding="utf-8") as f:
        stored_preds = [json.loads(line) for line in f if line.strip()]

    assert len(stored_preds) == 582
    for p_gen, p_store in zip(all_preds, stored_preds):
        assert p_gen["type"] == p_store["type"]
        assert p_gen["start"] == p_store["start"]
        assert p_gen["end"] == p_store["end"]
        assert p_gen["text"] == p_store["text"]


def test_e01_evaluation_metrics_reproducibility():
    adapter = RegexBaselineAdapter()
    report = run_experiment(adapter, save_artifacts=False)

    metrics = report["metrics_overall"]

    # Exact headline numbers
    assert metrics["n_gold"] == 724
    assert metrics["n_predictions"] == 582
    assert metrics["tp_type"] == 377
    assert metrics["tp_exact"] == 377
    assert metrics["localized"] == 444

    assert abs(metrics["m1_precision"] - 0.647766323024055) < 1e-10
    assert abs(metrics["m2_recall"] - 0.5207182320441989) < 1e-10
    assert abs(metrics["m3_f1"] - 0.5773353751914242) < 1e-10
    assert abs(metrics["m4_exact_f1"] - 0.5773353751914242) < 1e-10
    assert abs(metrics["m5_type_accuracy"] - 0.8490990990990991) < 1e-10
    assert abs(metrics["m6_fpr"] - 0.23711340206185566) < 1e-10

    # Error partition
    assert metrics["f1_missed"] == 280
    assert metrics["f2_wrong_span"] == 0
    assert metrics["f3_wrong_type"] == 67
    assert metrics["f4_false_pos"] == 138
    assert (
        metrics["f1_missed"]
        + metrics["f2_wrong_span"]
        + metrics["f3_wrong_type"]
        + metrics["tp_exact"]
        == metrics["n_gold"]
    )
