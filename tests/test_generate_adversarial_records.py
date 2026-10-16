"""Tests for T12 adversarial record generation (Phase 2 test-first suite).

Tests the perturbation transforms and the adversarial record assembler
against all requirements in guidelines.md v0.18 Section 14 and schemas/example.schema.json.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator

from generators.language.adversarial_records import (
    SELECTED_BASE_IDS,
    generate_adversarial_records_for_base,
    generate_all_adversarial_records,
    load_selected_bases,
)
from generators.perturbations import (
    A3_LABEL_MAP,
    A4_ABBREVIATION_MAP,
    OCR_HOMOGLYPH_MAP,
    apply_char_variation,
    apply_punctuation,
    apply_spacing,
    realize_abbreviation,
    realize_char_variation,
    realize_label_obfuscation,
    realize_punctuation,
    realize_spacing,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_INSTANCES_PATH = REPO_ROOT / "data" / "raw" / "base_instances.jsonl"
HARD_NEG_BASES_PATH = REPO_ROOT / "data" / "raw" / "hard_negative_bases.jsonl"
LANG_REALIZATIONS_PATH = REPO_ROOT / "data" / "generated" / "language_realizations.jsonl"
HARD_NEG_REALIZATIONS_PATH = REPO_ROOT / "data" / "generated" / "hard_negative_realizations.jsonl"
EXAMPLE_SCHEMA_PATH = REPO_ROOT / "schemas" / "example.schema.json"

EXPECTED_BASE_MD5 = "7006b0c9227d93541d2b71f702407ecc"
EXPECTED_HARD_NEG_BASE_MD5 = "b36c6c106548d18ff7083fd00532cb07"
EXPECTED_LANG_REALIZATIONS_MD5 = "0cb046740507eb9111a214b24b680483"
EXPECTED_HARD_NEG_REALIZATIONS_MD5 = "ae5537eec4129822e3d97b05170b4fea"


@pytest.fixture(scope="module")
def example_schema_validator():
    schema = json.loads(EXAMPLE_SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


@pytest.fixture(scope="module")
def selected_bases():
    return load_selected_bases()


@pytest.fixture(scope="module")
def generated_records(selected_bases):
    return generate_all_adversarial_records(selected_bases)


# --- 1. Selection & Cardinality ---


def test_selected_base_count_and_ids(selected_bases):
    assert len(selected_bases) == 20
    base_ids = [b["base_id"] for b in selected_bases]
    assert base_ids == SELECTED_BASE_IDS


def test_total_record_cardinality(generated_records):
    assert len(generated_records) == 100


def test_records_per_family_distribution(generated_records):
    family_counts = {}
    for r in generated_records:
        fam = r["perturbation"]["family"]
        family_counts[fam] = family_counts.get(fam, 0) + 1
    assert family_counts == {"A1": 20, "A2": 20, "A3": 20, "A4": 20, "A5": 20}


def test_records_per_type_distribution(generated_records):
    type_counts = {}
    for r in generated_records:
        ptype = r["entities"][0]["type"]
        type_counts[ptype] = type_counts.get(ptype, 0) + 1
    # 2 bases * 5 = 10; 3 bases * 5 = 15
    assert type_counts == {
        "PERSON": 10,
        "ADDRESS": 10,
        "PHONE": 10,
        "EMAIL": 10,
        "PAN": 15,
        "AADHAAR": 15,
        "UPI_ID": 15,
        "BANK_ACCOUNT": 15,
    }


def test_base_linkage(generated_records, selected_bases):
    base_map = {b["base_id"]: b for b in selected_bases}
    for r in generated_records:
        bid = r["base_id"]
        assert bid in base_map
        base = base_map[bid]
        assert r["entities"][0]["base_pii_value"] == base["pii"][0]["base_pii_value"]
        assert r["domain"] == base["scenario"]["domain"].upper()


# --- 2. Invariants & Span Verification ---


def test_span_integrity_on_all_records(generated_records):
    for r in generated_records:
        text = r["text"]
        entity = r["entities"][0]
        start, end = entity["start"], entity["end"]
        realized = entity["realized_pii_value"]
        assert text[start:end] == realized
        assert entity["occurrence_index"] == 0
        assert r["distractors"] == []
        assert r["language"] == "EN"
        assert r["carrier_script"] == "LATIN"
        assert r["context"] == "EXPLICIT"
        assert r["difficulty"] == "ADVERSARIAL"
        assert r["synthetic"] is True
        assert r["guidelines_version"] == "0.18"


def test_variant_id_uniqueness_and_format(generated_records):
    seen_ids = set()
    for r in generated_records:
        vid = r["variant_id"]
        assert vid not in seen_ids
        seen_ids.add(vid)
        fam = r["perturbation"]["family"]
        bid = r["base_id"]
        assert vid == f"{bid}_EN_{fam}_01"


def test_schema_validity(generated_records, example_schema_validator):
    for r in generated_records:
        example_schema_validator.validate(r)


# --- 3. Perturbation Transforms ---


def test_a1_spacing_transform(generated_records):
    a1_records = [r for r in generated_records if r["perturbation"]["family"] == "A1"]
    assert len(a1_records) == 20
    for r in a1_records:
        assert r["perturbation"]["type"] == "SPACING"
        assert r["perturbation"]["target"] == "VALUE"
        assert r["perturbation"]["severity"] == 1
        base_val = r["entities"][0]["base_pii_value"]
        realized_val = r["entities"][0]["realized_pii_value"]
        assert realized_val == apply_spacing(base_val)
        assert realized_val != base_val


def test_a2_punctuation_transform(generated_records):
    a2_records = [r for r in generated_records if r["perturbation"]["family"] == "A2"]
    assert len(a2_records) == 20
    for r in a2_records:
        assert r["perturbation"]["type"] == "PUNCTUATION"
        assert r["perturbation"]["target"] == "VALUE"
        assert r["perturbation"]["severity"] == 1
        ptype = r["entities"][0]["type"]
        base_val = r["entities"][0]["base_pii_value"]
        realized_val = r["entities"][0]["realized_pii_value"]
        assert realized_val == apply_punctuation(ptype, base_val)
        assert realized_val != base_val


def test_a3_label_obfuscation_transform(generated_records):
    a3_records = [r for r in generated_records if r["perturbation"]["family"] == "A3"]
    assert len(a3_records) == 20
    for r in a3_records:
        assert r["perturbation"]["type"] == "LABEL_OBFUSCATION"
        assert r["perturbation"]["target"] == "LABEL"
        assert r["perturbation"]["severity"] == 1
        base_val = r["entities"][0]["base_pii_value"]
        realized_val = r["entities"][0]["realized_pii_value"]
        # Value remains byte-identical
        assert realized_val == base_val


def test_a4_informal_abbreviation_transform(generated_records):
    a4_records = [r for r in generated_records if r["perturbation"]["family"] == "A4"]
    assert len(a4_records) == 20
    for r in a4_records:
        assert r["perturbation"]["type"] == "INFORMAL_ABBREVIATION"
        assert r["perturbation"]["target"] == "LABEL"
        assert r["perturbation"]["severity"] == 1
        base_val = r["entities"][0]["base_pii_value"]
        realized_val = r["entities"][0]["realized_pii_value"]
        # Value remains byte-identical
        assert realized_val == base_val


def test_a5_character_variation_transform(generated_records):
    a5_records = [r for r in generated_records if r["perturbation"]["family"] == "A5"]
    assert len(a5_records) == 20
    for r in a5_records:
        assert r["perturbation"]["type"] == "CHARACTER_VARIATION"
        assert r["perturbation"]["target"] == "VALUE"
        assert r["perturbation"]["severity"] == 1
        ptype = r["entities"][0]["type"]
        base_val = r["entities"][0]["base_pii_value"]
        realized_val = r["entities"][0]["realized_pii_value"]
        assert realized_val == apply_char_variation(ptype, base_val)
        assert realized_val != base_val
        if ptype in ("PHONE", "AADHAAR", "BANK_ACCOUNT"):
            diffs = sum(1 for c1, c2 in zip(base_val, realized_val) if c1 != c2)
            assert diffs == 1


# --- 4. Dataset Integrity & Determinism ---


def test_source_datasets_unmutated():
    def md5(p):
        return hashlib.md5(p.read_bytes()).hexdigest()

    assert md5(BASE_INSTANCES_PATH) == EXPECTED_BASE_MD5
    assert md5(HARD_NEG_BASES_PATH) == EXPECTED_HARD_NEG_BASE_MD5
    assert md5(LANG_REALIZATIONS_PATH) == EXPECTED_LANG_REALIZATIONS_MD5
    assert md5(HARD_NEG_REALIZATIONS_PATH) == EXPECTED_HARD_NEG_REALIZATIONS_MD5


def test_determinism_across_runs(selected_bases):
    run1 = generate_all_adversarial_records(selected_bases)
    run2 = generate_all_adversarial_records(selected_bases)
    assert run1 == run2
    assert json.dumps(run1, sort_keys=True) == json.dumps(run2, sort_keys=True)
