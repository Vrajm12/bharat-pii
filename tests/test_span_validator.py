"""T09 tests -- written before any validation artifact is produced. Exercises
validators.spans against the 624 real T08 records and a set of synthetic/
corrupted cases built by copying real records and mutating one field at a
time (never hand-authoring a full record from scratch, so every test stays
anchored to what the frozen schema/dataset actually looks like)."""

import copy
import json
from pathlib import Path

import pytest

from generators.language.spans import find_all_occurrences
from generators.translit.table import transliterate_value
from validators.spans import (
    OCCURRENCE_MISMATCH,
    PII_NOT_FOUND,
    SPAN_MISMATCH,
    expected_realized_value,
    validate_dataset,
    validate_hindi_collapse_representation,
    validate_record_span,
)

ROOT = Path(__file__).resolve().parent.parent
BASES = [
    json.loads(line)
    for line in (ROOT / "data" / "raw" / "base_instances.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()
]
RECORDS = [
    json.loads(line)
    for line in (ROOT / "data" / "generated" / "language_realizations.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()
]
BASE_BY_ID = {b["base_id"]: b for b in BASES}
RECORD_BY_VARIANT_ID = {r["variant_id"]: r for r in RECORDS}


def _real(variant_id):
    return copy.deepcopy(RECORD_BY_VARIANT_ID[variant_id])


# ---------------------------------------------------------------------------
# 1. Single-PII exact span (real record)
# ---------------------------------------------------------------------------

def test_single_pii_exact_span_valid():
    record = _real("PAN_001_EN")
    assert validate_record_span(record, BASE_BY_ID) == []


# ---------------------------------------------------------------------------
# 2-4, plus >=3 occurrences: repeated identical PII, occurrence_index 0/1/2
# ---------------------------------------------------------------------------

def _repeated_value_base_and_record():
    base = {
        "base_id": "PAN_999",
        "base_kind": "POSITIVE",
        "pii": [{"type": "PAN", "base_pii_value": "ABCDE1234F", "semantic_role": "TAX_IDENTIFIER"}],
        "person_context": {"name": "Test Person", "name_deva": None},
        "scenario": {"domain": "account_verification", "purpose": "identity_verification"},
        "address_structure": None,
        "canonical_text": "x",
        "synthetic": True,
        "generator_version": "0.1.0",
    }
    text = "PAN ABCDE1234F. Again ABCDE1234F. Once more ABCDE1234F."
    matches = find_all_occurrences(text, "ABCDE1234F")
    assert len(matches) == 3  # sanity: this fixture genuinely has 3 occurrences
    return base, text, matches


def _record_for_occurrence(base, text, matches, occurrence_index):
    start = matches[occurrence_index]
    end = start + len("ABCDE1234F")
    return {
        "base_id": base["base_id"],
        "variant_id": f"PAN_999_EN_occ{occurrence_index}",
        "text": text,
        "entities": [{
            "type": "PAN", "base_pii_value": "ABCDE1234F",
            "realized_pii_value": "ABCDE1234F", "pii_script": "LATIN",
            "start": start, "end": end, "occurrence_index": occurrence_index,
        }],
        "language": "EN",
    }


@pytest.mark.parametrize("occurrence_index", [0, 1, 2])
def test_repeated_identical_pii_each_occurrence_valid(occurrence_index):
    base, text, matches = _repeated_value_base_and_record()
    record = _record_for_occurrence(base, text, matches, occurrence_index)
    base_by_id = {**BASE_BY_ID, base["base_id"]: base}
    assert validate_record_span(record, base_by_id) == []


def test_three_or_more_occurrences_all_independently_resolved():
    base, text, matches = _repeated_value_base_and_record()
    base_by_id = {**BASE_BY_ID, base["base_id"]: base}
    for occ in range(3):
        record = _record_for_occurrence(base, text, matches, occ)
        issues = validate_record_span(record, base_by_id)
        assert issues == [], (occ, issues)


# ---------------------------------------------------------------------------
# 5. Wrong occurrence_index
# ---------------------------------------------------------------------------

def test_wrong_occurrence_index_rejected():
    base, text, matches = _repeated_value_base_and_record()
    base_by_id = {**BASE_BY_ID, base["base_id"]: base}
    # occurrence_index says 1 but span is actually occurrence 0's position
    record = _record_for_occurrence(base, text, matches, 0)
    record["entities"][0]["occurrence_index"] = 1
    issues = validate_record_span(record, base_by_id)
    assert any(i.reason == OCCURRENCE_MISMATCH for i in issues)


# ---------------------------------------------------------------------------
# 6. Missing occurrence
# ---------------------------------------------------------------------------

def test_missing_occurrence_rejected():
    record = _real("PAN_001_EN")
    record["text"] = "This sentence no longer contains the PAN value at all."
    issues = validate_record_span(record, BASE_BY_ID)
    assert any(i.reason == PII_NOT_FOUND for i in issues)


# ---------------------------------------------------------------------------
# 7. Wrong realized value
# ---------------------------------------------------------------------------

def test_wrong_realized_value_rejected():
    record = _real("PAN_001_EN")
    record["entities"][0]["realized_pii_value"] = "ZZZZZ9999Z"
    issues = validate_record_span(record, BASE_BY_ID)
    assert any(i.reason == SPAN_MISMATCH for i in issues)


# ---------------------------------------------------------------------------
# 8. Wrong type
# ---------------------------------------------------------------------------

def test_wrong_type_rejected():
    record = _real("PAN_001_EN")
    record["entities"][0]["type"] = "AADHAAR"
    issues = validate_record_span(record, BASE_BY_ID)
    assert any(i.reason == SPAN_MISMATCH for i in issues)


# ---------------------------------------------------------------------------
# 9-10. Wrong start / wrong end
# ---------------------------------------------------------------------------

def test_wrong_start_rejected():
    record = _real("PAN_001_EN")
    record["entities"][0]["start"] += 1
    issues = validate_record_span(record, BASE_BY_ID)
    assert any(i.reason == SPAN_MISMATCH for i in issues)


def test_wrong_end_rejected():
    record = _real("PAN_001_EN")
    record["entities"][0]["end"] -= 1
    issues = validate_record_span(record, BASE_BY_ID)
    assert any(i.reason == SPAN_MISMATCH for i in issues)


# ---------------------------------------------------------------------------
# 11. Trailing punctuation excluded (real record, structural property)
# ---------------------------------------------------------------------------

def test_trailing_punctuation_excluded_from_span():
    record = _real("PAN_001_EN")
    entity = record["entities"][0]
    assert record["text"][entity["end"] : entity["end"] + 1] == "."
    assert entity["realized_pii_value"][-1] != "."
    assert validate_record_span(record, BASE_BY_ID) == []


# ---------------------------------------------------------------------------
# 12-13, 17: Devanagari span, mixed-script span, code-point correctness
# ---------------------------------------------------------------------------

def _first(language, pii_type=None):
    for r in RECORDS:
        if r["language"] == language and (pii_type is None or r["entities"][0]["type"] == pii_type):
            return r
    raise AssertionError(f"no record found for language={language} type={pii_type}")


def test_devanagari_span_valid_for_person():
    record = copy.deepcopy(_first("HI_DEVA_PII", "PERSON"))
    assert validate_record_span(record, BASE_BY_ID) == []
    entity = record["entities"][0]
    assert entity["pii_script"] == "DEVANAGARI"
    assert record["text"][entity["start"] : entity["end"]] == entity["realized_pii_value"]


def test_mixed_script_span_valid_hi_latin_pii_pan():
    """PAN's collapsed HI_LATIN_PII record: Devanagari carrier, Latin/ASCII PII."""
    record = copy.deepcopy(_first("HI_LATIN_PII", "PAN"))
    assert validate_record_span(record, BASE_BY_ID) == []
    assert record["carrier_script"] == "DEVANAGARI"
    assert record["entities"][0]["pii_script"] == "LATIN"


def test_unicode_code_point_offsets_not_bytes_or_utf16():
    """The classic guidelines.md §4.6 trip-wire: len("राहुल") == 5 code points,
    not the UTF-8 byte count (11) or the UTF-16 code-unit count."""
    record = copy.deepcopy(_first("HI_DEVA_PII", "PERSON"))
    entity = record["entities"][0]
    deva_value = entity["realized_pii_value"]
    assert entity["end"] - entity["start"] == len(deva_value)  # code points, not bytes
    assert len(deva_value.encode("utf-8")) >= len(deva_value)  # byte count would differ


def test_devanagari_combining_marks_matras_exercised():
    """Explicit combining-mark/matra example -- guidelines.md §4.6: "Devanagari
    matras and the virama occupy their own index positions."""
    text = "मेरा नाम राहुल शर्मा है।"
    value = "राहुल शर्मा"
    # राहुल: र + ा(matra) + ह + ु(matra) + ल = 5 code points
    assert len("राहुल") == 5
    matches = find_all_occurrences(text, value)
    assert len(matches) == 1
    start = matches[0]
    end = start + len(value)
    assert text[start:end] == value
    assert transliterate_value("Rahul Sharma") == "राहुल शर्मा"


# ---------------------------------------------------------------------------
# 14. Collapsed Hindi record
# ---------------------------------------------------------------------------

def test_collapsed_hindi_record_valid():
    non_translit_base_id = "PAN_001"
    base = BASE_BY_ID[non_translit_base_id]
    records_for_base = [r for r in RECORDS if r["base_id"] == non_translit_base_id]
    issues = validate_hindi_collapse_representation(records_for_base, base)
    assert issues == []
    hi_latin = next(r for r in records_for_base if r["language"] == "HI_LATIN_PII")
    assert hi_latin["hi_variant_collapsed"] is True
    assert not any(r["language"] == "HI_DEVA_PII" for r in records_for_base)


def test_transliterable_base_not_collapsed():
    translit_base_id = "PERSON_001"
    base = BASE_BY_ID[translit_base_id]
    records_for_base = [r for r in RECORDS if r["base_id"] == translit_base_id]
    issues = validate_hindi_collapse_representation(records_for_base, base)
    assert issues == []


def test_collapse_violation_detected():
    non_translit_base_id = "PAN_001"
    base = BASE_BY_ID[non_translit_base_id]
    records_for_base = copy.deepcopy(
        [r for r in RECORDS if r["base_id"] == non_translit_base_id]
    )
    for r in records_for_base:
        if r["language"] == "HI_LATIN_PII":
            r["hi_variant_collapsed"] = False  # corrupt the flag
    issues = validate_hindi_collapse_representation(records_for_base, base)
    assert any(i.reason == SPAN_MISMATCH for i in issues)


# ---------------------------------------------------------------------------
# 15-16. PERSON / ADDRESS transliterated value == T07 output
# ---------------------------------------------------------------------------

def test_person_transliterated_value_matches_t07():
    record = _first("HI_DEVA_PII", "PERSON")
    base = BASE_BY_ID[record["base_id"]]
    base_value = base["pii"][0]["base_pii_value"]
    expected = expected_realized_value("HI_DEVA_PII", "PERSON", base_value)
    assert expected == transliterate_value(base_value)
    assert record["entities"][0]["realized_pii_value"] == expected


def test_address_transliterated_value_matches_t07():
    record = _first("HI_DEVA_PII", "ADDRESS")
    base = BASE_BY_ID[record["base_id"]]
    base_value = base["pii"][0]["base_pii_value"]
    expected = expected_realized_value("HI_DEVA_PII", "ADDRESS", base_value)
    assert expected == transliterate_value(base_value)
    assert record["entities"][0]["realized_pii_value"] == expected


# ---------------------------------------------------------------------------
# 18. Text mutation causes rejection
# ---------------------------------------------------------------------------

def test_text_mutation_causes_stale_span_rejection():
    record = _real("PAN_001_EN")
    # insert a character before the PII span -- offsets are now stale
    entity = record["entities"][0]
    record["text"] = record["text"][: entity["start"]] + "X" + record["text"][entity["start"] :]
    issues = validate_record_span(record, BASE_BY_ID)
    assert any(i.reason == SPAN_MISMATCH for i in issues)


# ---------------------------------------------------------------------------
# 19. Deterministic repeated execution
# ---------------------------------------------------------------------------

def test_validate_dataset_is_deterministic():
    report1 = validate_dataset(RECORDS, BASES)
    report2 = validate_dataset(RECORDS, BASES)
    assert report1["total_records"] == report2["total_records"]
    assert report1["valid_records"] == report2["valid_records"]
    assert [(i.variant_id, i.reason, i.detail) for i in report1["issues"]] == [
        (i.variant_id, i.reason, i.detail) for i in report2["issues"]
    ]


# ---------------------------------------------------------------------------
# 20. All 624 T08 records pass
# ---------------------------------------------------------------------------

def test_all_624_records_pass_validation():
    report = validate_dataset(RECORDS, BASES)
    assert report["total_records"] == 624
    assert report["issues"] == []
    assert report["valid_records"] == 624


# --- Fail-closed / no-repair discipline -------------------------------------

def test_validator_never_mutates_input_records():
    before = copy.deepcopy(RECORDS)
    validate_dataset(RECORDS, BASES)
    assert RECORDS == before


def test_validator_never_mutates_base_instances():
    before = copy.deepcopy(BASES)
    validate_dataset(RECORDS, BASES)
    assert BASES == before


def test_generated_dataset_file_untouched_by_validation():
    path = ROOT / "data" / "generated" / "language_realizations.jsonl"
    reloaded = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert reloaded == RECORDS


# --- HARD_NEGATIVE compatibility (T11 Phase 2 pre-audit, guidelines.md §13.3) -
#
# A hard negative has an empty entities array by definition -- that has been
# true since guidelines.md v0.1, long before this validator existed. These
# tests prove the fix and, just as importantly, prove the original
# POSITIVE-base behavior (entities=[] is PII_NOT_FOUND) is unchanged.


HARD_NEGATIVE_BASE = {
    "base_id": "NEG_001",
    "base_kind": "HARD_NEGATIVE",
    "pii": [],
    "person_context": None,
    "scenario": {"domain": "customer_support", "purpose": "hard_negative_context"},
    "address_structure": None,
    "canonical_text": "The order number is 9876543210.",
    "synthetic": True,
    "generator_version": "0.1.0",
    "hard_negative_decoy": {
        "decoy_class": "NUMERIC_SHAPE",
        "value": "9876543210",
        "surface_type": "PHONE",
        "actual_role": "ORDER_REFERENCE",
    },
}


def _hard_negative_record(**overrides):
    record = {
        "base_id": "NEG_001",
        "variant_id": "NEG_001_EN",
        "text": "The order number is 9876543210.",
        "entities": [],
        "distractors": [
            {
                "text": "9876543210",
                "start": 20,
                "end": 30,
                "surface_type": "PHONE",
                "actual_role": "ORDER_REFERENCE",
                "decoy_class": "NUMERIC_SHAPE",
            }
        ],
        "language": "EN",
    }
    record.update(overrides)
    return record


def test_hard_negative_record_with_empty_entities_passes():
    record = _hard_negative_record()
    base_by_id = {"NEG_001": HARD_NEGATIVE_BASE}
    assert validate_record_span(record, base_by_id) == []


def test_hard_negative_record_with_an_unexpected_entity_is_rejected():
    record = _hard_negative_record(
        entities=[
            {
                "type": "PHONE",
                "base_pii_value": "9876543210",
                "realized_pii_value": "9876543210",
                "pii_script": "NUMERIC",
                "start": 20,
                "end": 30,
                "occurrence_index": 0,
            }
        ]
    )
    base_by_id = {"NEG_001": HARD_NEGATIVE_BASE}
    issues = validate_record_span(record, base_by_id)
    assert len(issues) == 1
    assert issues[0].reason == SPAN_MISMATCH


def test_positive_base_with_empty_entities_still_reports_pii_not_found():
    """Regression guard: the fix must not weaken T09 for the case it was
    always meant to catch -- a POSITIVE record that is missing its entity."""
    base = BASES[0]
    assert base["base_kind"] == "POSITIVE"
    record = {
        "base_id": base["base_id"],
        "variant_id": f"{base['base_id']}_EN",
        "text": base["canonical_text"],
        "entities": [],
        "language": "EN",
    }
    issues = validate_record_span(record, {base["base_id"]: base})
    assert len(issues) == 1
    assert issues[0].reason == PII_NOT_FOUND
