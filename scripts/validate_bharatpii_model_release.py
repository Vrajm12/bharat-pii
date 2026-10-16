"""Standalone Validation Script for BharatPII-CRF Model Release v1.0.

PROJECT_SPEC.md & Productization Step 1 Mandates:
1. Locate distributable model artifact in models/bharatpii-crf-v1.0/
2. Verify SHA256 hashes of all release files against SHA256SUMS.txt
3. Load tokenizer, config, and label map
4. Load weights from model.safetensors and verify tensor and parameter counts
5. Validate inference output contract and native Unicode slicing invariant
6. Run full benchmark inference across all 964 canonical records
7. Compare against canonical B6 predictions (assert 0 prediction mismatches)
8. Evaluate metric parity (TP_exact=601, F1=7, F2=76, F3=40, F4=356, M1-M6)
9. Print PASS / FAIL clearly.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
import torch
from safetensors.torch import load_file
from transformers import AutoTokenizer, XLMRobertaModel

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from baselines.transformer_b6 import TransformerB6CRFAdapter, TransformerB6CRFHead, LABEL_LIST, ID2LABEL
from benchmark.evaluator import Evaluator
from benchmark.runner import load_canonical_benchmark_records
from benchmark.schema import Prediction
from benchmark.stats import aggregate_results

MODEL_DIR = REPO_ROOT / "models" / "bharatpii-crf-v1.0"
CANONICAL_PRED_FILE = REPO_ROOT / "predictions" / "experiments" / "b6" / "transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.jsonl"
CANONICAL_REPORT_FILE = REPO_ROOT / "reports" / "experiments" / "b6" / "evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.json"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def validate_release() -> bool:
    print("=" * 70)
    print("BharatPII-CRF v1.0 Model Release Validation")
    print("=" * 70)

    # 1. Locate model directory
    print(f"\n[1/8] Locating model directory: {MODEL_DIR}")
    if not MODEL_DIR.exists():
        print(f"FAIL: Model directory not found at {MODEL_DIR}")
        return False
    print("  -> Directory found.")

    # 2. Verify SHA256SUMS.txt
    print("\n[2/8] Verifying file integrity against SHA256SUMS.txt...")
    sums_file = MODEL_DIR / "SHA256SUMS.txt"
    if not sums_file.exists():
        print("FAIL: SHA256SUMS.txt missing")
        return False

    expected_sums = {}
    with open(sums_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                sha, fname = line.strip().split(maxsplit=1)
                expected_sums[fname] = sha

    for fname, exp_sha in expected_sums.items():
        fpath = MODEL_DIR / fname
        if not fpath.exists():
            print(f"FAIL: Required file {fname} missing from release directory")
            return False
        act_sha = compute_sha256(fpath)
        if act_sha != exp_sha:
            print(f"FAIL: Checksum mismatch for {fname}: exp {exp_sha}, got {act_sha}")
            return False
        print(f"  [OK] {fname} ({fpath.stat().st_size:,} bytes) -> {act_sha[:16]}...")

    # 3. Verify Label Map & Metadata
    print("\n[3/8] Verifying label_map.json and model_metadata.json...")
    with open(MODEL_DIR / "label_map.json", "r", encoding="utf-8") as f:
        label_map = json.load(f)
    assert len(label_map) == 17, f"Expected 17 labels, got {len(label_map)}"
    for idx_str, tag in label_map.items():
        assert ID2LABEL[int(idx_str)] == tag, f"Label mismatch at {idx_str}: {tag} != {ID2LABEL[int(idx_str)]}"
    print("  [OK] label_map.json matches canonical 17 IOB2 labels perfectly.")

    with open(MODEL_DIR / "model_metadata.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["model_name"] == "BharatPII-CRF"
    assert meta["decoder"] == "linear-chain CRF"
    assert meta["parameters"]["total_parameters"] == 278057044
    assert meta["parameters"]["trainable_parameters_b6_adaptation"] == 13396
    print(f"  [OK] model_metadata.json verified (version: {meta['model_version']}).")

    # 4. Load weights and verify parameter counts
    print("\n[4/8] Loading model weights from model.safetensors...")
    state_dict = load_file(MODEL_DIR / "model.safetensors")
    assert len(state_dict) == 204, f"Expected 204 tensors, got {len(state_dict)}"

    roberta_tensors = {k: v for k, v in state_dict.items() if k.startswith("roberta.")}
    head_tensors = {k: v for k, v in state_dict.items() if not k.startswith("roberta.")}

    assert len(roberta_tensors) == 199, f"Expected 199 encoder tensors, got {len(roberta_tensors)}"
    assert len(head_tensors) == 5, f"Expected 5 head tensors, got {len(head_tensors)}"

    n_encoder = sum(t.numel() for t in roberta_tensors.values())
    n_head = sum(t.numel() for t in head_tensors.values())
    n_total = n_encoder + n_head

    print(f"  Total parameters:        {n_total:,}")
    print(f"  Encoder parameters:      {n_encoder:,} (Frozen base)")
    print(f"  CRF Head parameters:     {n_head:,} (Trainable)")
    assert n_total == 278057044, f"Total parameter mismatch: {n_total}"
    assert n_encoder == 278043648, f"Encoder parameter mismatch: {n_encoder}"
    assert n_head == 13396, f"Head parameter mismatch: {n_head}"
    print("  [OK] Parameter counts verified with exact bitwise precision.")

    # 5. Initialize Adapter from release artifact
    print("\n[5/8] Initializing TransformerB6CRFAdapter from release folder...")
    adapter = TransformerB6CRFAdapter(model_name_or_path=MODEL_DIR, seed=42)
    print("  [OK] Adapter initialized cleanly on device:", adapter.device)

    # 6. Validate output schema & Unicode slice contract on sample text
    print("\n[6/8] Verifying output schema and Unicode offset contract...")
    sample_text = "Call Rahul Sharma at 9876543210 regarding PAN ABCDE1234F."
    sample_preds = adapter.predict(sample_text)
    assert len(sample_preds) > 0, "No predictions on test sentence"
    for p in sample_preds:
        assert isinstance(p.text, str)
        assert isinstance(p.start, int)
        assert isinstance(p.end, int)
        assert isinstance(p.type, str)
        assert isinstance(p.confidence, float)
        assert 0.0 <= p.confidence <= 1.0
        assert sample_text[p.start:p.end] == p.text, f"Offset contract failed: '{sample_text[p.start:p.end]}' != '{p.text}'"
    print("  [OK] Output schema and native Unicode slicing verified.")

    # 7. Run Canonical Parity Test across all 964 benchmark records
    print("\n[7/8] Running Canonical Parity Test across 964 benchmark records...")
    records = load_canonical_benchmark_records()
    assert len(records) == 964, f"Expected 964 records, loaded {len(records)}"

    preds_by_variant: dict[str, list[Prediction]] = {}
    all_preds: list[Prediction] = []

    for i, rec in enumerate(records):
        vid = rec["variant_id"]
        txt = rec.get("text", "")
        preds = adapter.predict(txt)
        linked = []
        for p in preds:
            lp = Prediction(
                type=p.type,
                start=p.start,
                end=p.end,
                text=p.text,
                confidence=p.confidence,
                variant_id=vid,
                status=p.status,
            )
            linked.append(lp)
            all_preds.append(lp)
        preds_by_variant[vid] = linked
        if (i + 1) % 200 == 0 or (i + 1) == 964:
            print(f"  Processed {i + 1}/964 records ({len(all_preds)} entities detected)...")

    # Load canonical predictions
    print("\n  Comparing predictions against canonical B6 predictions...")
    canon_preds_by_variant: dict[str, list[dict]] = {}
    total_canon_count = 0
    with open(CANONICAL_PRED_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            vid = item["variant_id"]
            canon_preds_by_variant.setdefault(vid, []).append(item)
            total_canon_count += 1

    print(f"  Total released predictions:  {len(all_preds)}")
    print(f"  Total canonical predictions: {total_canon_count}")
    assert len(all_preds) == total_canon_count, f"Count mismatch: {len(all_preds)} != {total_canon_count}"

    mismatch_count = 0
    for vid, cand_list in preds_by_variant.items():
        c_list = canon_preds_by_variant.get(vid, [])
        if len(cand_list) != len(c_list):
            print(f"FAIL: Record {vid} entity count mismatch: {len(cand_list)} != {len(c_list)}")
            mismatch_count += abs(len(cand_list) - len(c_list))
            continue
        for cp, cand in zip(c_list, cand_list):
            if (
                cand.type != cp["type"]
                or cand.start != cp["start"]
                or cand.end != cp["end"]
                or cand.text != cp["text"]
                or abs(cand.confidence - cp["confidence"]) > 1e-4
            ):
                print(f"FAIL: Mismatch in {vid}: {cand} vs {cp}")
                mismatch_count += 1

    print(f"  Prediction Mismatches: {mismatch_count}")
    assert mismatch_count == 0, f"Expected 0 mismatches, found {mismatch_count}"
    print("  [OK] EXACT CANONICAL PARITY CONFIRMED: 0 prediction mismatches across all 964 records!")

    # 8. Metric Parity Evaluation
    print("\n[8/8] Evaluating metric parity against canonical report...")
    evaluator = Evaluator()
    eval_results = evaluator.evaluate_batch(records, preds_by_variant)
    score = aggregate_results(eval_results)
    metrics = score.to_dict()

    with open(CANONICAL_REPORT_FILE, "r", encoding="utf-8") as f:
        canon_rep = json.load(f)
    c_m = canon_rep["metrics_overall"]

    print("\nMetric Parity Comparison Table:")
    print("-" * 65)
    print(f"{'Metric':<25} | {'Released Model':<15} | {'Canonical B6':<15} | {'Diff':<8}")
    print("-" * 65)

    check_keys = [
        ("tp_exact", "TP_exact", True),
        ("tp_type", "TP_type", True),
        ("f1_missed", "F1 (Missed)", True),
        ("f2_wrong_span", "F2 (Wrong Span)", True),
        ("f3_wrong_type", "F3 (Wrong Type)", True),
        ("f4_false_pos", "F4 (False Pos)", True),
        ("m1_precision", "M1 (Precision)", False),
        ("m2_recall", "M2 (Recall)", False),
        ("m3_f1", "M3 (Type F1)", False),
        ("m4_exact_f1", "M4 (Exact F1)", False),
        ("m5_type_accuracy", "M5 (Accuracy)", False),
        ("m6_fpr", "M6 (FPR)", False),
    ]

    all_metrics_match = True
    for key, label, is_int in check_keys:
        act_val = metrics[key]
        exp_val = c_m[key]
        if is_int:
            diff = act_val - exp_val
            match = (diff == 0)
            print(f"{label:<25} | {act_val:<15} | {exp_val:<15} | {diff}")
        else:
            diff = abs(act_val - exp_val)
            match = (diff < 1e-5)
            print(f"{label:<25} | {act_val:<15.4f} | {exp_val:<15.4f} | {diff:.6f}")
        if not match:
            all_metrics_match = False

    print("-" * 65)

    # Invariant check
    inv = metrics["tp_exact"] + metrics["f1_missed"] + metrics["f2_wrong_span"] + metrics["f3_wrong_type"]
    print(f"Partition Invariant: TP_exact + F1 + F2 + F3 = {inv} (Expected: 724)")
    assert inv == 724, f"Partition invariant violation: {inv} != 724"
    assert all_metrics_match, "One or more metrics deviated from canonical values"

    print("\n" + "=" * 70)
    print("STATUS: PASS")
    print(f"MODEL: {MODEL_DIR}")
    print(f"TOTAL PARAMETERS: {n_total:,}")
    print(f"TRAINABLE PARAMETERS: {n_head:,}")
    print("CANONICAL PARITY: 0 mismatches across 964 records")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = validate_release()
    if not success:
        sys.exit(1)
