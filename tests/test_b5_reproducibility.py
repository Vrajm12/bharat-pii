"""T14/B5: Indian-Adapted Multilingual Transformer baseline reproducibility and regression tests (PROJECT_SPEC.md §19 B5, §20.5, §21.2)."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from baselines.base import validate_predictions
from baselines.transformer_adapted import TransformerAdaptedBaselineAdapter
from benchmark.runner import load_canonical_benchmark_records, run_experiment

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize(
    ("seed", "expected_preds", "expected_tp_type", "expected_tp_exact"),
    [
        (42, 1638, 706, 456),
        (43, 1623, 705, 460),
        (44, 1646, 705, 450),
    ],
)
def test_b5_multi_seed_metrics_reproducibility(
    seed: int, expected_preds: int, expected_tp_type: int, expected_tp_exact: int
) -> None:
    checkpoint_dir = ROOT / "checkpoints" / f"b5_transformer_adapted_seed{seed}"
    if not checkpoint_dir.exists():
        pytest.skip(f"Checkpoint directory for seed {seed} not found")

    adapter = TransformerAdaptedBaselineAdapter(model_name_or_path=checkpoint_dir, seed=seed)
    adapter._system_version = f"5.16.1_xlm_roberta_base_indian_seed{seed}"

    report = run_experiment(adapter, save_artifacts=False)
    metrics = report["metrics_overall"]

    assert metrics["n_gold"] == 724
    assert metrics["n_predictions"] == expected_preds
    assert metrics["tp_type"] == expected_tp_type
    assert metrics["tp_exact"] == expected_tp_exact

    # High recall (>97%) invariant
    assert metrics["m2_recall"] > 0.97

    # Invariant partition
    assert (
        metrics["f1_missed"]
        + metrics["f2_wrong_span"]
        + metrics["f3_wrong_type"]
        + metrics["tp_exact"]
        == metrics["n_gold"]
    )
    assert report["n_predictions_rejected"] == 0


def test_b5_canonical_prediction_artifact_matches():
    """Verify stored canonical prediction artifact has exactly 1638 predictions with valid geometry."""
    pred_path = ROOT / "predictions" / "transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.jsonl"
    assert pred_path.exists()

    with open(pred_path, "r", encoding="utf-8") as f:
        stored_preds = [json.loads(line) for line in f if line.strip()]

    assert len(stored_preds) == 1638
    for p in stored_preds:
        assert p["start"] >= 0
        assert p["end"] > p["start"]
        assert len(p["text"]) == p["end"] - p["start"]
        assert p["type"] in TransformerAdaptedBaselineAdapter.TYPE_MAP or isinstance(p["type"], str)
