"""Comprehensive Canonical Parity Verification across all 964 Benchmark Records."""

import json
from pathlib import Path
import pytest
from bharatpii import BharatPII
from benchmark.evaluator import Evaluator
from benchmark.runner import load_canonical_benchmark_records
from benchmark.schema import Prediction
from benchmark.stats import aggregate_results

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = REPO_ROOT / "models" / "bharatpii-crf-v1.0"
CANONICAL_PRED_FILE = (
    REPO_ROOT / "predictions" / "experiments" / "b6" / "transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.jsonl"
)
CANONICAL_REP_FILE = (
    REPO_ROOT / "reports" / "experiments" / "b6" / "evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.json"
)


def test_canonical_prediction_and_metric_parity():
    """Verify that BharatPII produces EXACTLY 0 mismatches across 964 benchmark records."""
    model = BharatPII.from_pretrained(MODEL_DIR)
    records = load_canonical_benchmark_records()
    assert len(records) == 964

    # 1. Run predictions across all 964 records
    preds_by_variant: dict[str, list[Prediction]] = {}
    total_package_preds = 0

    for rec in records:
        vid = rec["variant_id"]
        txt = rec.get("text", "")
        res = model.predict(txt)
        linked = []
        for ent in res.entities:
            p = Prediction(
                type=ent.label,
                start=ent.start,
                end=ent.end,
                text=ent.text,
                confidence=ent.score or 1.0,
                variant_id=vid,
                status="VALID",
            )
            linked.append(p)
            total_package_preds += 1
        preds_by_variant[vid] = linked

    # 2. Compare against canonical predictions
    canonical_preds_by_variant: dict[str, list[dict]] = {}
    total_canonical_preds = 0
    with open(CANONICAL_PRED_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                canonical_preds_by_variant.setdefault(item["variant_id"], []).append(item)
                total_canonical_preds += 1

    assert total_package_preds == 1073, f"Expected 1,073 predictions, got {total_package_preds}"
    assert total_canonical_preds == 1073
    assert total_package_preds == total_canonical_preds

    mismatches = 0
    for vid, cand_list in preds_by_variant.items():
        canon_list = canonical_preds_by_variant.get(vid, [])
        assert len(cand_list) == len(canon_list), f"Entity count mismatch in {vid}"
        for cand, canon in zip(cand_list, canon_list):
            if (
                cand.type != canon["type"]
                or cand.start != canon["start"]
                or cand.end != canon["end"]
                or cand.text != canon["text"]
                or abs(cand.confidence - canon["confidence"]) > 1e-4
            ):
                mismatches += 1

    assert mismatches == 0, f"Expected 0 prediction mismatches, found {mismatches}"

    # 3. Metric Parity
    evaluator = Evaluator()
    eval_results = evaluator.evaluate_batch(records, preds_by_variant)
    metrics = aggregate_results(eval_results).to_dict()

    with open(CANONICAL_REP_FILE, "r", encoding="utf-8") as f:
        canon_rep = json.load(f)
    cm = canon_rep["metrics_overall"]

    assert metrics["tp_exact"] == 601
    assert metrics["tp_type"] == 677
    assert metrics["f1_missed"] == 7
    assert metrics["f2_wrong_span"] == 76
    assert metrics["f3_wrong_type"] == 40
    assert metrics["f4_false_pos"] == 356

    # Partition invariant
    inv = metrics["tp_exact"] + metrics["f1_missed"] + metrics["f2_wrong_span"] + metrics["f3_wrong_type"]
    assert inv == 724
    assert metrics["tp_type"] == metrics["tp_exact"] + metrics["f2_wrong_span"]

    # Metric rates
    assert abs(metrics["m1_precision"] - cm["m1_precision"]) < 1e-5
    assert abs(metrics["m2_recall"] - cm["m2_recall"]) < 1e-5
    assert abs(metrics["m3_f1"] - cm["m3_f1"]) < 1e-5
    assert abs(metrics["m4_exact_f1"] - cm["m4_exact_f1"]) < 1e-5
    assert abs(metrics["m5_type_accuracy"] - cm["m5_type_accuracy"]) < 1e-5
    assert abs(metrics["m6_fpr"] - cm["m6_fpr"]) < 1e-5
