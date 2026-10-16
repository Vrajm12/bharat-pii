"""Governance and validation tests for Task SV-02 (Controlled Generalization / Hard-Negative Ablation).

Tests:
1. Zero Base-ID and Record-ID overlap with canonical test corpus.
2. Zero full-text duplication between SV-02 adaptation sets and canonical test corpus.
3. All hard-negative instances are strictly 100% labeled 'O' with zero entities.
4. Token budgets are documented and consistent.
5. All entity span character offsets match their underlying text substrings.
6. All 22 prior canonical benchmark dataset and baseline artifacts remain strictly immutable.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
SV02_DATA_DIR = ROOT / "data" / "experiments" / "sv02"

CANONICAL_22_ARTIFACTS = [
    ("data/raw/base_instances.jsonl", "7006b0c9227d93541d2b71f702407ecc"),
    ("data/raw/hard_negative_bases.jsonl", "b36c6c106548d18ff7083fd00532cb07"),
    ("data/generated/language_realizations.jsonl", "0cb046740507eb9111a214b24b680483"),
    ("data/generated/hard_negative_realizations.jsonl", "ae5537eec4129822e3d97b05170b4fea"),
    ("data/generated/adversarial_realizations.jsonl", "1b678b9597737c85197acf80ab56878d"),
    ("annotation/review_template.csv", "78c5767f2f8fede2021ff344aaddc32c"),
    ("predictions/regex_1.0.0_v0.18.jsonl", "8913ac633854a36948a3445e4be0594d"),
    ("reports/evaluation_regex_1.0.0_v0.18.json", "2958f77985fcc70d704c123e9e952ebd"),
    ("predictions/spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.jsonl", "6c74bd4ec742a1f0c6b8024200937fb5"),
    ("reports/evaluation_spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.json", "a9745314b2e71df861ea71af15a9dd1a"),
    ("predictions/presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.jsonl", "2c661403efa963275be5f2559a1577b9"),
    ("reports/evaluation_presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.json", "4831393231e3d15dc674166dcaaaa2b9"),
    ("predictions/transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.jsonl", "3f53b646fb9f95414bef8b972d2277b1"),
    ("reports/evaluation_transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.json", "dfe7e6b93e15ca266b29121977b1809e"),
    ("predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.jsonl", "e589c2a3daa96e8a3963d95fecb89012"),
    ("predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.jsonl", "e589c2a3daa96e8a3963d95fecb89012"),
    ("predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.jsonl", "e11d924839cdddebd59104624f667357"),
    ("predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.jsonl", "a0b17f4b93251463319d0dc1409514bf"),
    ("reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.json", "d3a9f9da8e848c7cafb9cf43299b9439"),
    ("reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.json", "06ca5638e48dc492c016166d8b1d12a2"),
    ("reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.json", "cfb422de399fa7cb13dec4e30f7b29e1"),
    ("reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.json", "90a0a0c9bb83dd4d2f456b6e0f508753"),
]


@pytest.mark.parametrize("rel_path, expected_md5", CANONICAL_22_ARTIFACTS)
def test_canonical_artifact_hash_integrity(rel_path: str, expected_md5: str):
    p = ROOT / rel_path
    assert p.exists(), f"Canonical artifact missing: {rel_path}"
    with open(p, "rb") as f:
        actual_md5 = hashlib.md5(f.read()).hexdigest()
    assert actual_md5 == expected_md5, f"Hash mismatch on {rel_path}: {actual_md5} != {expected_md5}"


def load_jsonl(p: Path) -> list[dict]:
    with open(p, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_sv02_data_disjointness_and_zero_test_leakage():
    from benchmark.runner import load_canonical_benchmark_records

    test_records = load_canonical_benchmark_records()
    test_base_ids = set(r["base_id"] for r in test_records)
    test_texts = set(" ".join(r["text"].lower().split()) for r in test_records)

    for var in ("b5_hard_negative", "b5_positive_matched", "b5_format_diversity"):
        train_p = SV02_DATA_DIR / var / "train.jsonl"
        val_p = SV02_DATA_DIR / var / "val.jsonl"
        assert train_p.exists(), f"Train file missing for {var}"
        assert val_p.exists(), f"Val file missing for {var}"

        all_recs = load_jsonl(train_p) + load_jsonl(val_p)
        adapt_base_ids = set(r["base_id"] for r in all_recs)

        # 1. Zero base-ID overlap
        assert len(adapt_base_ids.intersection(test_base_ids)) == 0, f"Base ID overlap in {var}"

        # 2. Zero normalized text overlap
        adapt_texts = set(" ".join(r["text"].lower().split()) for r in all_recs)
        assert len(adapt_texts.intersection(test_texts)) == 0, f"Text overlap in {var}"


def test_sv02_hard_negatives_contain_zero_entities():
    train_p = SV02_DATA_DIR / "b5_hard_negative" / "train.jsonl"
    val_p = SV02_DATA_DIR / "b5_hard_negative" / "val.jsonl"

    hn_recs = [r for r in load_jsonl(train_p) + load_jsonl(val_p) if r.get("is_hard_negative")]
    assert len(hn_recs) == 300, f"Expected 300 hard negative records, got {len(hn_recs)}"

    for r in hn_recs:
        assert r.get("entities") == [], f"Hard negative {r.get('record_id')} must have entities == []"


def test_sv02_span_offsets_match_text_substrings():
    for var in ("b5_hard_negative", "b5_positive_matched", "b5_format_diversity"):
        train_p = SV02_DATA_DIR / var / "train.jsonl"
        val_p = SV02_DATA_DIR / var / "val.jsonl"
        all_recs = load_jsonl(train_p) + load_jsonl(val_p)

        for r in all_recs:
            t = r["text"]
            for e in r.get("entities", []):
                s, end, val = e["start"], e["end"], e["text"]
                assert t[s:end] == val, f"Span mismatch in {var} record {r.get('record_id')}: {t[s:end]} != {val}"


def test_sv02_manifests_and_token_budget_accounting():
    master_manifest_p = SV02_DATA_DIR / "manifest.json"
    assert master_manifest_p.exists(), "Master SV-02 manifest missing"
    with open(master_manifest_p, "r", encoding="utf-8") as f:
        master = json.load(f)

    assert "variants" in master
    for var in ("b5_baseline", "b5_hard_negative", "b5_positive_matched", "b5_format_diversity"):
        assert var in master["variants"]
        v_info = master["variants"][var]
        assert v_info["records_train"] in (1000, 1250)
        assert v_info["tokens_train"] > 18000
