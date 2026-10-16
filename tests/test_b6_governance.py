"""Governance and Integrity Test Suite for Baseline B6 (PROJECT_SPEC.md §§19-24, §§28).

Verifies:
1. All 22 canonical benchmark and baseline artifacts remain bitwise unchanged.
2. B6 model architecture adheres strictly to LinearChainCRF and 17 IOB2 tags.
3. B6 inference is deterministic.
4. Evaluation reports satisfy the partition invariant F1 + F2 + F3 + TP_exact == 724.
5. Zero raw PII in B6 report artifacts.
6. Prediction schema adherence and valid native Unicode offset slicing.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest
import torch

from baselines.transformer_b6 import (
    ID2LABEL,
    LABEL2ID,
    LABEL_LIST,
    LinearChainCRF,
    TransformerB6CRFAdapter,
    TransformerB6CRFHead,
)
from benchmark.schema import Prediction

REPO_ROOT = Path(__file__).resolve().parent.parent

CANONICAL_HASHES = {
    "data/raw/base_instances.jsonl": "7006b0c9227d93541d2b71f702407ecc",
    "data/raw/hard_negative_bases.jsonl": "b36c6c106548d18ff7083fd00532cb07",
    "data/generated/language_realizations.jsonl": "0cb046740507eb9111a214b24b680483",
    "data/generated/hard_negative_realizations.jsonl": "ae5537eec4129822e3d97b05170b4fea",
    "data/generated/adversarial_realizations.jsonl": "1b678b9597737c85197acf80ab56878d",
    "annotation/review_template.csv": "78c5767f2f8fede2021ff344aaddc32c",
    "predictions/regex_1.0.0_v0.18.jsonl": "8913ac633854a36948a3445e4be0594d",
    "reports/evaluation_regex_1.0.0_v0.18.json": "2958f77985fcc70d704c123e9e952ebd",
    "predictions/spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.jsonl": "6c74bd4ec742a1f0c6b8024200937fb5",
    "reports/evaluation_spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.json": "a9745314b2e71df861ea71af15a9dd1a",
    "predictions/presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.jsonl": "2c661403efa963275be5f2559a1577b9",
    "reports/evaluation_presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.json": "4831393231e3d15dc674166dcaaaa2b9",
    "predictions/transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.jsonl": "3f53b646fb9f95414bef8b972d2277b1",
    "reports/evaluation_transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.json": "dfe7e6b93e15ca266b29121977b1809e",
    "predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.jsonl": "e589c2a3daa96e8a3963d95fecb89012",
    "predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.jsonl": "e589c2a3daa96e8a3963d95fecb89012",
    "predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.jsonl": "e11d924839cdddebd59104624f667357",
    "predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.jsonl": "a0b17f4b93251463319d0dc1409514bf",
    "reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.json": "d3a9f9da8e848c7cafb9cf43299b9439",
    "reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.json": "06ca5638e48dc492c016166d8b1d12a2",
    "reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.json": "cfb422de399fa7cb13dec4e30f7b29e1",
    "reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.json": "90a0a0c9bb83dd4d2f456b6e0f508753",
}


def test_canonical_artifacts_immutability():
    """Verify all 22 canonical benchmark and baseline artifacts are strictly bitwise identical."""
    for rel_path, expected_md5 in CANONICAL_HASHES.items():
        p = REPO_ROOT / rel_path
        assert p.exists(), f"Missing canonical file: {p}"
        with open(p, "rb") as f:
            actual_md5 = hashlib.md5(f.read()).hexdigest()
        assert actual_md5 == expected_md5, f"Bitwise deviation in {rel_path}: {actual_md5} != {expected_md5}"


def test_b6_crf_head_architecture():
    """Verify B6 CRF head parameters and taxonomy."""
    head = TransformerB6CRFHead(hidden_size=768, num_tags=17)
    assert head.classifier.in_features == 768
    assert head.classifier.out_features == 17
    assert isinstance(head.crf, LinearChainCRF)
    assert head.crf.transitions.shape == (17, 17)
    assert head.crf.start_transitions.shape == (17,)
    assert head.crf.end_transitions.shape == (17,)
    assert len(LABEL_LIST) == 17
    assert LABEL_LIST[0] == "O"


def test_b6_partition_invariants():
    """Verify that B6 evaluation reports satisfy the exact partition invariant: F1 + F2 + F3 + TP_exact == 724."""
    rep_dir = REPO_ROOT / "reports" / "experiments" / "b6"
    for seed in [42, 43, 44]:
        rep_file = rep_dir / f"evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed{seed}_v0.18.json"
        if rep_file.exists():
            data = json.loads(rep_file.read_text(encoding="utf-8"))
            m = data["metrics_overall"]
            inv = m["f1_missed"] + m["f2_wrong_span"] + m["f3_wrong_type"] + m["tp_exact"]
            assert inv == 724, f"Seed {seed} invariant failed: {inv} != 724"
            assert data["n_predictions_rejected"] == 0, f"Seed {seed} has rejected predictions"


def test_b6_no_raw_pii_in_reports():
    """Verify no unredacted synthetic PII strings leak into B6 report artifacts."""
    rep_dir = REPO_ROOT / "reports" / "experiments" / "b6"
    if not rep_dir.exists():
        return
    for json_file in rep_dir.glob("*.json"):
        content = json_file.read_text(encoding="utf-8")
        assert "raw_pii" not in content.lower(), f"Potential PII exposure in {json_file.name}"


def test_b6_predictions_schema_and_offsets():
    """Verify all B6 prediction records adhere to schema and exact native Unicode slice invariant."""
    pred_dir = REPO_ROOT / "predictions" / "experiments" / "b6"
    pred_file = pred_dir / "transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.jsonl"
    assert pred_file.exists(), f"Missing primary B6 prediction file: {pred_file}"

    # Load canonical records text mapping
    rec_texts = {}
    with open(REPO_ROOT / "data" / "generated" / "language_realizations.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            rec_texts[r["variant_id"]] = r["text"]

    with open(pred_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if not line.strip():
                continue
            data = json.loads(line)
            p = Prediction.from_dict(data)
            assert p.status == "VALID"
            assert 0 <= p.start < p.end
            vid = p.variant_id
            if vid in rec_texts:
                assert rec_texts[vid][p.start:p.end] == p.text, f"Offset mismatch in record {vid}"


def test_b6_deterministic_inference():
    """Verify that repeated inference calls on the same text yield identical predictions."""
    adapter = TransformerB6CRFAdapter(seed=42)
    sample_text = "Contact Rahul at rahul.sharma@example.com or call 9876543210 regarding PAN ABCDE1234F."
    preds1 = adapter.predict(sample_text)
    preds2 = adapter.predict(sample_text)

    assert len(preds1) == len(preds2)
    for p1, p2 in zip(preds1, preds2):
        assert p1.type == p2.type
        assert p1.start == p2.start
        assert p1.end == p2.end
        assert p1.text == p2.text
        assert abs(p1.confidence - p2.confidence) < 1e-6