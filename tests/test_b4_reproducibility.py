"""T13/B4: Multilingual Transformer baseline reproducibility and regression tests (PROJECT_SPEC.md §19 B4, §20.4)."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from baselines.base import validate_predictions
from baselines.transformer import TransformerBaselineAdapter
from benchmark.runner import load_canonical_benchmark_records, run_experiment

ROOT = Path(__file__).resolve().parent.parent


def test_b4_prediction_generation_reproducibility():
    records = load_canonical_benchmark_records()
    adapter = TransformerBaselineAdapter()

    all_preds = []
    total_rejected = 0
    for r in records:
        text = r.get("text", "")
        preds = adapter.predict(text)
        valid, rejected = validate_predictions(preds, original_text=text)
        total_rejected += len(rejected)
        for p in preds:
            all_preds.append(p.to_dict())

    assert len(all_preds) == 467
    assert total_rejected == 0

    pred_path = ROOT / "predictions" / "transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.jsonl"
    assert pred_path.exists()
    with open(pred_path, "r", encoding="utf-8") as f:
        stored_preds = [json.loads(line) for line in f if line.strip()]

    assert len(stored_preds) == 467
    for p_gen, p_store in zip(all_preds, stored_preds):
        assert p_gen["type"] == p_store["type"]
        assert p_gen["start"] == p_store["start"]
        assert p_gen["end"] == p_store["end"]
        assert p_gen["text"] == p_store["text"]


def test_b4_evaluation_metrics_reproducibility():
    adapter = TransformerBaselineAdapter()
    report = run_experiment(adapter, save_artifacts=False)

    metrics = report["metrics_overall"]

    assert metrics["n_gold"] == 724
    assert metrics["n_predictions"] == 467
    assert metrics["tp_type"] == 94
    assert metrics["tp_exact"] == 86
    assert metrics["localized"] == 185

    assert abs(metrics["m1_precision"] - 0.2012847965738758) < 1e-10
    assert abs(metrics["m2_recall"] - 0.1298342541436464) < 1e-10
    assert abs(metrics["m3_f1"] - 0.15785054575986562) < 1e-10
    assert abs(metrics["m4_exact_f1"] - 0.144416456759026) < 1e-10
    assert abs(metrics["m5_type_accuracy"] - 0.5081081081081081) < 1e-10
    assert abs(metrics["m6_fpr"] - 0.6038543897216274) < 1e-10

    # Error partition
    assert metrics["f1_missed"] == 539
    assert metrics["f2_wrong_span"] == 8
    assert metrics["f3_wrong_type"] == 91
    assert metrics["f4_false_pos"] == 282
    assert (
        metrics["f1_missed"]
        + metrics["f2_wrong_span"]
        + metrics["f3_wrong_type"]
        + metrics["tp_exact"]
        == metrics["n_gold"]
    )
