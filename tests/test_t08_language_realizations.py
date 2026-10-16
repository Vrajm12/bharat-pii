"""T08 tests -- written before data/generated/language_realizations.jsonl
exists. Exercises generators.language.records against the 100 frozen T04
bases entirely in memory; nothing here writes the canonical output file."""

import json
import re
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import pytest
from jsonschema import Draft202012Validator

from generators.language import metadata, realizations, templates
from generators.language.records import (
    GENERATOR_VERSION,
    generate_all_records,
    generate_records_for_base,
    load_base_instances,
)
from generators.language.spans import SpanResolutionError, find_occurrence
from generators.translit.table import TABLE as T07_TABLE
from generators.translit.table import transliterate_value

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads(
    (ROOT / "schemas" / "example.schema.json").read_text(encoding="utf-8")
)
VALIDATOR = Draft202012Validator(SCHEMA)

BASES = load_base_instances()
BASE_BY_ID = {b["base_id"]: b for b in BASES}


@pytest.fixture(scope="module")
def records():
    return generate_all_records(BASES)


@pytest.fixture(scope="module")
def by_base(records):
    grouped = {}
    for r in records:
        grouped.setdefault(r["base_id"], []).append(r)
    return grouped


TRANSLITERABLE_TYPES = ("PERSON", "ADDRESS")
NON_TRANSLITERABLE_TYPES = ("PHONE", "EMAIL", "PAN", "AADHAAR", "UPI_ID", "BANK_ACCOUNT")


def _pii_type_of(base_id):
    return BASE_BY_ID[base_id]["pii"][0]["type"]


# 1. Seven language conditions exactly ---------------------------------------

def test_exactly_seven_language_conditions_defined():
    assert templates.LANGUAGES == (
        "EN", "IN_EN", "HI_LATIN_PII", "HI_DEVA_PII", "ROM_HI", "HINGLISH",
        "INFORMAL_HINGLISH",
    )


# 2-6. Record counts ---------------------------------------------------------

def test_correct_variant_count_per_base(by_base):
    for base_id, recs in by_base.items():
        pii_type = _pii_type_of(base_id)
        expected = 7 if pii_type in TRANSLITERABLE_TYPES else 6
        assert len(recs) == expected, (base_id, pii_type, len(recs))


def test_exactly_624_records_total(records):
    assert len(records) == 624


def test_24_transliterable_bases_times_7(by_base):
    transliterable = [bid for bid in by_base if _pii_type_of(bid) in TRANSLITERABLE_TYPES]
    assert len(transliterable) == 24
    assert sum(len(by_base[bid]) for bid in transliterable) == 168


def test_76_nontransliterable_bases_times_6(by_base):
    non_transliterable = [
        bid for bid in by_base if _pii_type_of(bid) in NON_TRANSLITERABLE_TYPES
    ]
    assert len(non_transliterable) == 76
    assert sum(len(by_base[bid]) for bid in non_transliterable) == 456


def test_total_matches_168_plus_456(records):
    assert len(records) == 168 + 456 == 624


# 7-8. Base linkage -----------------------------------------------------------

def test_every_record_links_to_an_existing_base(records):
    valid_ids = set(BASE_BY_ID)
    for r in records:
        assert r["base_id"] in valid_ids


def test_no_orphan_base_ids_every_base_has_records(by_base):
    assert set(by_base) == set(BASE_BY_ID)


# 9. No unexpected languages --------------------------------------------------

def test_no_unexpected_languages(records):
    for r in records:
        assert r["language"] in templates.LANGUAGES


def test_non_transliterable_bases_never_get_hi_deva_pii(by_base):
    for base_id in by_base:
        if _pii_type_of(base_id) in NON_TRANSLITERABLE_TYPES:
            langs = {r["language"] for r in by_base[base_id]}
            assert "HI_DEVA_PII" not in langs


def test_transliterable_bases_get_both_hindi_conditions(by_base):
    for base_id in by_base:
        if _pii_type_of(base_id) in TRANSLITERABLE_TYPES:
            langs = {r["language"] for r in by_base[base_id]}
            assert {"HI_LATIN_PII", "HI_DEVA_PII"} <= langs


# 10-11. variant_id ------------------------------------------------------------

def test_variant_id_uniqueness(records):
    ids = [r["variant_id"] for r in records]
    assert len(ids) == len(set(ids))


def test_variant_id_exact_clean_format(records):
    for r in records:
        assert r["variant_id"] == f"{r['base_id']}_{r['language']}"
        assert not re.search(r"_A[1-5]_[0-9]+$", r["variant_id"])


# 12-13. perturbation / context -----------------------------------------------

def test_perturbation_always_none(records):
    for r in records:
        assert r["perturbation"] == {
            "family": "NONE", "type": "NONE", "severity": 0, "target": "NONE",
        }


def test_context_always_explicit(records):
    for r in records:
        assert r["context"] == "EXPLICIT"


# 14-18. PII/base-field preservation ------------------------------------------

def test_base_pii_value_preserved(records):
    for r in records:
        base = BASE_BY_ID[r["base_id"]]
        assert r["entities"][0]["base_pii_value"] == base["pii"][0]["base_pii_value"]


def test_realized_pii_value_correct_per_condition(records):
    for r in records:
        base = BASE_BY_ID[r["base_id"]]
        base_value = base["pii"][0]["base_pii_value"]
        pii_type = base["pii"][0]["type"]
        realized = r["entities"][0]["realized_pii_value"]
        if pii_type in TRANSLITERABLE_TYPES and r["language"] == "HI_DEVA_PII":
            assert realized == transliterate_value(base_value)
        else:
            assert realized == base_value


def test_base_instances_file_untouched_by_generation(records):
    """Proves semantic_role/scenario/synthetic on the base were never
    mutated -- T08 only reads base_instances.jsonl, never writes it."""
    reloaded = load_base_instances()
    assert reloaded == BASES


def test_pii_type_preserved(records):
    for r in records:
        base = BASE_BY_ID[r["base_id"]]
        assert r["entities"][0]["type"] == base["pii"][0]["type"]


def test_synthetic_remains_true(records):
    assert all(r["synthetic"] is True for r in records)


# 19-21. Hindi-pair correctness -----------------------------------------------

def test_person_address_hi_deva_pii_equals_t07_output(by_base):
    for base_id, recs in by_base.items():
        if _pii_type_of(base_id) not in TRANSLITERABLE_TYPES:
            continue
        base_value = BASE_BY_ID[base_id]["pii"][0]["base_pii_value"]
        deva_record = next(r for r in recs if r["language"] == "HI_DEVA_PII")
        assert deva_record["entities"][0]["realized_pii_value"] == transliterate_value(
            base_value
        )


def test_person_address_hi_latin_pii_preserves_latin_value(by_base):
    for base_id, recs in by_base.items():
        if _pii_type_of(base_id) not in TRANSLITERABLE_TYPES:
            continue
        base_value = BASE_BY_ID[base_id]["pii"][0]["base_pii_value"]
        latin_record = next(r for r in recs if r["language"] == "HI_LATIN_PII")
        assert latin_record["entities"][0]["realized_pii_value"] == base_value


def test_non_transliterable_collapsed_record_matches_what_hi_deva_pii_would_be(
    by_base,
):
    """HI_LATIN_PII and HI_DEVA_PII are collapsed into one record for the six
    non-transliterable types (guidelines.md Section 8.1). Prove the single
    generated record is what BOTH labels would have produced identically."""
    for base_id, recs in by_base.items():
        pii_type = _pii_type_of(base_id)
        if pii_type not in NON_TRANSLITERABLE_TYPES:
            continue
        collapsed = next(r for r in recs if r["language"] == "HI_LATIN_PII")
        assert collapsed["hi_variant_collapsed"] is True
        base_value = BASE_BY_ID[base_id]["pii"][0]["base_pii_value"]
        would_be_deva_text, would_be_deva_value = realizations.realize_hindi_carrier(
            pii_type, base_value
        )
        assert collapsed["text"] == would_be_deva_text
        assert collapsed["entities"][0]["realized_pii_value"] == would_be_deva_value
        assert would_be_deva_value == base_value  # non-transliterable: unchanged


def test_transliterable_hi_variant_collapsed_is_false(by_base):
    for base_id, recs in by_base.items():
        if _pii_type_of(base_id) not in TRANSLITERABLE_TYPES:
            continue
        for r in recs:
            if r["language"] in ("HI_LATIN_PII", "HI_DEVA_PII"):
                assert r["hi_variant_collapsed"] is False


# 24, 42. Matched-carrier invariant -------------------------------------------

def test_matched_hindi_carrier_invariant_for_every_transliterable_base(by_base):
    for base_id, recs in by_base.items():
        if _pii_type_of(base_id) not in TRANSLITERABLE_TYPES:
            continue
        latin = next(r for r in recs if r["language"] == "HI_LATIN_PII")
        deva = next(r for r in recs if r["language"] == "HI_DEVA_PII")

        l_entity, d_entity = latin["entities"][0], deva["entities"][0]
        l_prefix = latin["text"][: l_entity["start"]]
        l_suffix = latin["text"][l_entity["end"] :]
        d_prefix = deva["text"][: d_entity["start"]]
        d_suffix = deva["text"][d_entity["end"] :]

        assert l_prefix == d_prefix, base_id
        assert l_suffix == d_suffix, base_id


# 25. Informal-Hinglish never mutates PII -------------------------------------

def test_informal_hinglish_never_mutates_pii(records):
    for r in records:
        if r["language"] != "INFORMAL_HINGLISH":
            continue
        base = BASE_BY_ID[r["base_id"]]
        assert r["entities"][0]["realized_pii_value"] == base["pii"][0]["base_pii_value"]


def test_informal_hinglish_pii_substring_present_unmutated_in_text(records):
    for r in records:
        if r["language"] != "INFORMAL_HINGLISH":
            continue
        value = r["entities"][0]["realized_pii_value"]
        assert value in r["text"]


# 26-31. Per-type value integrity ---------------------------------------------

@pytest.mark.parametrize("pii_type", ["PAN"])
def test_pan_remains_uppercase_in_every_condition(records, pii_type):
    for r in records:
        if r["entities"][0]["type"] != pii_type:
            continue
        value = r["entities"][0]["realized_pii_value"]
        assert value == value.upper()
        assert re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", value)


def test_aadhaar_unchanged_leading_zero_preserved_if_present(records):
    for r in records:
        if r["entities"][0]["type"] != "AADHAAR":
            continue
        base = BASE_BY_ID[r["base_id"]]
        assert r["entities"][0]["realized_pii_value"] == base["pii"][0]["base_pii_value"]


@pytest.mark.parametrize(
    "pii_type", ["EMAIL", "UPI_ID", "BANK_ACCOUNT", "PHONE"]
)
def test_non_transliterable_value_unchanged_across_all_conditions(records, pii_type):
    for r in records:
        if r["entities"][0]["type"] != pii_type:
            continue
        base = BASE_BY_ID[r["base_id"]]
        assert r["entities"][0]["realized_pii_value"] == base["pii"][0]["base_pii_value"]


# 22. pii_script for all eight types ------------------------------------------

def test_pii_script_correct_for_all_eight_types(records):
    for r in records:
        entity = r["entities"][0]
        pii_type = entity["type"]
        language = r["language"]
        expected = metadata.pii_script(pii_type, language)
        assert entity["pii_script"] == expected


def test_pii_script_matches_frozen_oq013_table(records):
    non_transliterable_expected = {
        "PHONE": "NUMERIC", "AADHAAR": "NUMERIC", "BANK_ACCOUNT": "NUMERIC",
        "PAN": "LATIN", "EMAIL": "LATIN", "UPI_ID": "MIXED",
    }
    for r in records:
        entity = r["entities"][0]
        if entity["type"] in non_transliterable_expected:
            assert entity["pii_script"] == non_transliterable_expected[entity["type"]]
        else:  # PERSON / ADDRESS
            expected = "DEVANAGARI" if r["language"] == "HI_DEVA_PII" else "LATIN"
            assert entity["pii_script"] == expected


# 23. carrier_script -----------------------------------------------------------

def test_carrier_script_correct(records):
    for r in records:
        expected = (
            "DEVANAGARI" if r["language"] in ("HI_LATIN_PII", "HI_DEVA_PII") else "LATIN"
        )
        assert r["carrier_script"] == expected


# 32-34. Span correctness ------------------------------------------------------

def test_span_offsets_correct_for_every_record(records):
    for r in records:
        e = r["entities"][0]
        assert r["text"][e["start"] : e["end"]] == e["realized_pii_value"]


def test_occurrence_index_is_zero_for_all_t08_records(records):
    """None of T08's templates repeat the PII value within one sentence."""
    for r in records:
        assert r["entities"][0]["occurrence_index"] == 0


def test_span_utility_walks_occurrences_not_a_bare_find():
    """Prove find_occurrence resolves repeats correctly, not just the first
    match -- the exact failure mode a bare str.find() has."""
    text = "X is X, and X again."
    first_start, first_end = find_occurrence(text, "X", occurrence_index=0)
    second_start, second_end = find_occurrence(text, "X", occurrence_index=1)
    third_start, third_end = find_occurrence(text, "X", occurrence_index=2)
    assert (first_start, first_end) == (0, 1)
    assert (second_start, second_end) == (5, 6)
    assert (third_start, third_end) == (12, 13)
    assert first_start != second_start != third_start


def test_span_utility_fails_closed_on_unresolvable_occurrence():
    with pytest.raises(SpanResolutionError):
        find_occurrence("no target here", "MISSING", occurrence_index=0)
    with pytest.raises(SpanResolutionError):
        find_occurrence("only one X here", "X", occurrence_index=1)


# 35-37. No LLM / no external service / T07 untouched -------------------------

def test_records_module_does_not_import_llm_or_network_libraries():
    source = (
        (ROOT / "generators" / "language" / "records.py").read_text(encoding="utf-8")
        + (ROOT / "generators" / "language" / "realizations.py").read_text(
            encoding="utf-8"
        )
        + (ROOT / "generators" / "language" / "templates.py").read_text(
            encoding="utf-8"
        )
    )
    forbidden = ["openai", "anthropic", "requests", "urllib", "httpx", "socket"]
    lowered = source.lower()
    for word in forbidden:
        assert word not in lowered, f"forbidden dependency found: {word}"


def test_t07_table_is_used_but_never_mutated(records):
    before = dict(T07_TABLE)
    generate_all_records(BASES)  # regenerate again
    assert T07_TABLE == before


def test_t07_transliterate_value_is_called_not_reimplemented():
    """Behavioral proof the language package calls T07's real function,
    rather than reimplementing transliteration itself."""
    with patch(
        "generators.language.records.transliterate_value",
        wraps=transliterate_value,
    ) as spy:
        person_base = next(
            b for b in BASES if b["pii"][0]["type"] == "PERSON"
        )
        generate_records_for_base(person_base, 0)
        spy.assert_called()


# 38. Determinism ---------------------------------------------------------------

def test_deterministic_repeated_generation_in_memory():
    first = generate_all_records(BASES)
    second = generate_all_records(BASES)
    assert first == second


# 39. Schema validation ---------------------------------------------------------

def test_every_generated_record_is_schema_valid(records):
    for r in records:
        VALIDATOR.validate(r)


# 40. Corrupted realization fails validation -------------------------------------

def test_corrupted_realization_fails_span_contract():
    text, value = realizations.realize_en("My PAN number is ABCDE1234F.", "ABCDE1234F")
    start, end = find_occurrence(text, value)
    corrupted_text = text[:start] + "WRONGVALUE" + text[end:]
    with pytest.raises(SpanResolutionError):
        find_occurrence(corrupted_text, value)


def test_corrupted_pii_script_fails_schema_validation():
    good = {
        "type": "PAN", "base_pii_value": "ABCDE1234F",
        "realized_pii_value": "ABCDE1234F", "pii_script": "LATIN",
        "start": 0, "end": 10, "occurrence_index": 0,
    }
    bad = {**good, "pii_script": "NOT_A_REAL_SCRIPT"}
    record = {
        "base_id": "PAN_001", "variant_id": "PAN_001_EN", "text": "ABCDE1234F",
        "entities": [bad], "distractors": [], "language": "EN",
        "carrier_script": "LATIN", "context": "EXPLICIT", "domain": "X",
        "perturbation": {"family": "NONE", "type": "NONE", "severity": 0, "target": "NONE"},
        "difficulty": "EASY", "address_structure": None, "hi_variant_collapsed": False,
        "synthetic": True, "generator_version": "0.1.0", "guidelines_version": "0.11",
        "template_id": "X", "seed": 42,
        "validation": {"structural": "PENDING", "span": "PENDING", "semantic": "PENDING",
                        "language": "PENDING", "duplicate": "PENDING", "human": "PENDING"},
        "validation_status": "PENDING", "review_status": "PENDING", "split": None,
    }
    with pytest.raises(Exception):
        VALIDATOR.validate(record)


# 41. EN == canonical_text -----------------------------------------------------

def test_en_equals_canonical_text_exactly(records):
    for r in records:
        if r["language"] != "EN":
            continue
        base = BASE_BY_ID[r["base_id"]]
        assert r["text"] == base["canonical_text"]


# --- Guidelines-frozen inventory tests (no invented markers) -----------------

_IN_EN_MARKER_SIGNATURE_PHRASES = {
    "kindly": "kindly note",
    "do the needful": "do the needful",
    "revert": "revert",
    "prepone": "prepone",
    "please find below/attached": "please find the details below",
    "intimate": "intimate",
    "the same": "the same",
    "at the earliest": "at the earliest",
}


def test_in_en_realization_uses_only_frozen_markers(records):
    """Each IN_EN record must contain the signature phrase of the one
    frozen marker (guidelines.md Section 4.12) it was deterministically
    assigned -- not an invented marker."""
    assert set(_IN_EN_MARKER_SIGNATURE_PHRASES) == {
        name for name, _ in templates.IN_EN_MARKERS
    }
    for r in records:
        if r["language"] != "IN_EN":
            continue
        lowered = r["text"].lower()
        assert any(
            phrase in lowered for phrase in _IN_EN_MARKER_SIGNATURE_PHRASES.values()
        ), r["text"]


def test_hinglish_realization_contains_a_frozen_insertion_word(records):
    for r in records:
        if r["language"] != "HINGLISH":
            continue
        lowered = r["text"].lower()
        assert any(word in lowered for word in templates.HINGLISH_INSERTION_WORDS)


def test_rom_hi_does_not_contain_hinglish_insertion_markers(records):
    """ROM_HI must not contain deliberate HINGLISH insertion markers --
    a closed-set membership test on the frozen HINGLISH inventory only
    (not a claim that all English-origin tokens must be enumerated)."""
    for r in records:
        if r["language"] != "ROM_HI":
            continue
        lowered = r["text"].lower()
        for word in templates.HINGLISH_INSERTION_WORDS:
            assert word not in lowered, (r["variant_id"], word)


def test_informal_hinglish_contains_a_frozen_informal_marker(records):
    for r in records:
        if r["language"] != "INFORMAL_HINGLISH":
            continue
        lowered = r["text"].lower()
        has_abbrev = any(a in lowered for a in templates.INFORMAL_ABBREVIATIONS)
        has_particle = any(p in lowered for p in templates.INFORMAL_CASUAL_PARTICLES)
        has_contraction = any(
            short in lowered for short in templates.INFORMAL_COPULA_CONTRACTIONS.values()
        )
        assert has_abbrev or has_particle or has_contraction, r["text"]
