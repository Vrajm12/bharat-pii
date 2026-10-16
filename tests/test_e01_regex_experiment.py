"""Tests for E01 Regex experiment runner and artifact pipeline (PROJECT_SPEC.md §§20–24)."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import pytest

from baselines.regex import RegexBaselineAdapter
from benchmark.runner import load_canonical_benchmark_records, run_experiment

ROOT = Path(__file__).resolve().parent.parent


def test_e01_load_canonical_records():
    records = load_canonical_benchmark_records()
    assert len(records) == 964

    # Verify key fields present
    for r in records:
        assert "variant_id" in r
        assert "text" in r
        assert len(r["text"]) > 0


def test_e01_experiment_runner_structure():
    adapter = RegexBaselineAdapter()
    report = run_experiment(adapter, save_artifacts=False)

    assert report["system_name"] == "regex"
    assert report["system_version"] == "1.0.0"
    assert report["dataset_version"] == "0.18"
    assert report["n_records_evaluated"] == 964
    assert report["n_predictions_rejected"] == 0
    assert report["n_predictions_total"] > 0

    # Required metric keys
    overall = report["metrics_overall"]
    for k in [
        "m1_precision",
        "m2_recall",
        "m3_f1",
        "m4_exact_f1",
        "m5_type_accuracy",
        "m6_fpr",
        "tp_type",
        "tp_exact",
        "f1_missed",
        "f2_wrong_span",
        "f3_wrong_type",
        "f4_false_pos",
    ]:
        assert k in overall

    # Slice keys present
    assert "metrics_by_language" in report
    assert "metrics_by_pii_type" in report
    assert "metrics_by_semantic_role" in report
    assert "metrics_by_perturbation_family" in report
    assert "metrics_by_difficulty" in report
    assert "metrics_by_base_kind" in report
    assert "metrics_by_decoy_class" in report
    assert "failures_breakdown" in report


def test_e01_experiment_runner_determinism():
    adapter = RegexBaselineAdapter()
    report_1 = run_experiment(adapter, save_artifacts=False)
    report_2 = run_experiment(adapter, save_artifacts=False)

    assert report_1 == report_2


def test_e01_experiment_artifact_saving(tmp_path: Path):
    adapter = RegexBaselineAdapter()
    pred_dir = tmp_path / "preds"
    rep_dir = tmp_path / "reps"

    report = run_experiment(
        adapter,
        save_artifacts=True,
        predictions_dir=pred_dir,
        reports_dir=rep_dir,
        dataset_version="0.18",
    )

    pred_file = pred_dir / "regex_1.0.0_v0.18.jsonl"
    rep_file = rep_dir / "evaluation_regex_1.0.0_v0.18.json"

    assert pred_file.exists()
    assert rep_file.exists()

    with open(pred_file, "r", encoding="utf-8") as f:
        preds = [json.loads(line) for line in f if line.strip()]
    assert len(preds) == report["n_predictions_total"]

    with open(rep_file, "r", encoding="utf-8") as f:
        loaded_rep = json.load(f)
    assert loaded_rep == report
