"""Unit tests for annotation/export_review_csv.py and review CSV generation (guidelines.md §19)."""

from __future__ import annotations

import csv
from pathlib import Path
import pytest

from annotation.export_review_csv import (
    EXPECTED_COLUMNS,
    build_review_rows,
    export_pilot_review_csv,
)

ROOT = Path(__file__).resolve().parent.parent


def test_1_exact_964_data_rows():
    rows = build_review_rows(ROOT / "data")
    assert len(rows) == 964


def test_2_exact_required_column_names_and_order():
    expected = [
        "variant_id",
        "base_id",
        "base_kind",
        "difficulty",
        "language",
        "carrier_script",
        "context",
        "declared_pii_type",
        "marked_span_text",
        "start",
        "end",
        "perturbation_family",
        "perturbation_target",
        "decoy_class",
        "full_text",
        "reviewer_id",
        "span_correct",
        "type_correct",
        "language_correct",
        "script_correct",
        "meaning_preserved",
        "natural",
        "human_recoverable",
        "review_status",
        "notes",
    ]
    assert EXPECTED_COLUMNS == expected


def test_3_every_canonical_record_appears_once():
    rows = build_review_rows(ROOT / "data")
    vids = [r["variant_id"] for r in rows]
    assert len(vids) == 964
    assert len(set(vids)) == 964


def test_4_variant_id_fidelity():
    rows = build_review_rows(ROOT / "data")
    vids = {r["variant_id"] for r in rows}
    assert "PERSON_001" in vids  # base
    assert "NEG_001" in vids  # hard neg base
    assert "PERSON_001_EN" in vids  # derived
    assert "NEG_001_EN" in vids  # derived hard neg
    assert "PERSON_001_EN_A1_01" in vids  # adversarial


def test_5_base_id_fidelity():
    rows = build_review_rows(ROOT / "data")
    assert all(bool(r["base_id"]) for r in rows)


def test_6_base_kind_fidelity():
    rows = build_review_rows(ROOT / "data")
    positives = [r for r in rows if r["base_kind"] == "POSITIVE"]
    negatives = [r for r in rows if r["base_kind"] == "HARD_NEGATIVE"]
    # 100 positive bases + 624 language realizations + 100 adversarial = 824
    # 20 hard negative bases + 120 hard negative realizations = 140
    assert len(positives) == 824
    assert len(negatives) == 140


def test_7_difficulty_fidelity():
    rows = build_review_rows(ROOT / "data")
    diffs = {r["difficulty"] for r in rows}
    assert diffs == {"EASY", "MEDIUM", "ADVERSARIAL"}


def test_8_language_fidelity():
    rows = build_review_rows(ROOT / "data")
    langs = {r["language"] for r in rows}
    assert "EN" in langs
    assert "HINGLISH" in langs
    assert "HI_DEVA_PII" in langs


def test_9_carrier_script_fidelity():
    rows = build_review_rows(ROOT / "data")
    scripts = {r["carrier_script"] for r in rows}
    assert scripts == {"LATIN", "DEVANAGARI"}


def test_10_context_fidelity():
    rows = build_review_rows(ROOT / "data")
    contexts = {r["context"] for r in rows}
    assert "EXPLICIT" in contexts


def test_11_declared_pii_type_fidelity():
    rows = build_review_rows(ROOT / "data")
    types = {r["declared_pii_type"] for r in rows}
    assert "PAN" in types
    assert "AADHAAR" in types
    assert "NONE" in types


def test_12_marked_span_text_fidelity():
    rows = build_review_rows(ROOT / "data")
    for r in rows:
        if r["base_kind"] == "HARD_NEGATIVE":
            assert r["marked_span_text"] == ""
        else:
            if r["start"] != "":
                start, end = int(r["start"]), int(r["end"])
                assert r["full_text"][start:end] == r["marked_span_text"]


def test_13_start_end_fidelity():
    rows = build_review_rows(ROOT / "data")
    for r in rows:
        if r["base_kind"] == "HARD_NEGATIVE":
            assert r["start"] == ""
            assert r["end"] == ""
        else:
            assert int(r["start"]) >= 0
            assert int(r["end"]) > int(r["start"])


def test_14_perturbation_family_fidelity():
    rows = build_review_rows(ROOT / "data")
    fams = {r["perturbation_family"] for r in rows}
    assert fams == {"NONE", "A1", "A2", "A3", "A4", "A5"}


def test_15_perturbation_target_fidelity():
    rows = build_review_rows(ROOT / "data")
    targets = {r["perturbation_target"] for r in rows}
    assert targets == {"NONE", "VALUE", "LABEL"}


def test_16_decoy_class_fidelity():
    rows = build_review_rows(ROOT / "data")
    decoys = {r["decoy_class"] for r in rows if r["decoy_class"]}
    assert "NUMERIC_SHAPE" in decoys
    assert "ALNUM_SHAPE" in decoys
    assert "NAME_AS_PLACE" in decoys


def test_17_full_text_fidelity():
    rows = build_review_rows(ROOT / "data")
    assert all(len(r["full_text"].strip()) > 0 for r in rows)


def test_18_reviewer_fields_default_blank_or_pending():
    rows = build_review_rows(ROOT / "data")
    for r in rows:
        assert r["reviewer_id"] == ""
        assert r["span_correct"] == ""
        assert r["type_correct"] == ""
        assert r["language_correct"] == ""
        assert r["script_correct"] == ""
        assert r["meaning_preserved"] == ""
        assert r["natural"] == ""
        assert r["human_recoverable"] == ""
        assert r["review_status"] == "PENDING"
        assert r["notes"] == ""


def test_19_export_reproduces_identical_content(tmp_path: Path):
    out1 = tmp_path / "out1.csv"
    out2 = tmp_path / "out2.csv"

    export_pilot_review_csv(output_path=out1, data_dir=ROOT / "data", overwrite=True)
    export_pilot_review_csv(output_path=out2, data_dir=ROOT / "data", overwrite=True)

    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")


def test_20_csv_reload_reproduces_same_values(tmp_path: Path):
    out = tmp_path / "review.csv"
    export_pilot_review_csv(output_path=out, data_dir=ROOT / "data", overwrite=True)

    with open(out, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        reloaded_rows = list(reader)

    assert len(reloaded_rows) == 964
    assert list(reloaded_rows[0].keys()) == EXPECTED_COLUMNS
