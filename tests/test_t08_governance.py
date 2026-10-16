"""Governance/fixture tests proving the OQ-013, OQ-014, and OQ-027 decisions
(guidelines.md v0.11, decisions 36-38) before any T08 generator code exists.

These tests encode the FROZEN DECISIONS as constants and check them against
the schema and against guidelines.md's own §17 worked examples -- they do
not implement, and must not be mistaken for, the T08 language generator
itself (which does not exist yet).
"""

import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "example.schema.json"

SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)

LANGUAGES = (
    "EN",
    "IN_EN",
    "HI_LATIN_PII",
    "HI_DEVA_PII",
    "ROM_HI",
    "HINGLISH",
    "INFORMAL_HINGLISH",
)

# --- OQ-013 frozen mapping (guidelines.md §4.15, decision 36) --------------

NON_TRANSLITERABLE_PII_SCRIPT = {
    "PHONE": "NUMERIC",
    "AADHAAR": "NUMERIC",
    "BANK_ACCOUNT": "NUMERIC",
    "PAN": "LATIN",
    "EMAIL": "LATIN",
    "UPI_ID": "MIXED",
}

TRANSLITERABLE_PII_SCRIPT_BY_LANGUAGE = {
    language: ("DEVANAGARI" if language == "HI_DEVA_PII" else "LATIN")
    for language in LANGUAGES
}


def _entity(pii_type, pii_script, value="X"):
    return {
        "type": pii_type,
        "base_pii_value": value,
        "realized_pii_value": value,
        "pii_script": pii_script,
        "start": 0,
        "end": len(value),
        "occurrence_index": 0,
    }


def test_non_transliterable_pii_script_mapping_matches_frozen_decision():
    assert NON_TRANSLITERABLE_PII_SCRIPT == {
        "PHONE": "NUMERIC",
        "AADHAAR": "NUMERIC",
        "BANK_ACCOUNT": "NUMERIC",
        "PAN": "LATIN",
        "EMAIL": "LATIN",
        "UPI_ID": "MIXED",
    }


def test_transliterable_pii_script_is_devanagari_only_for_hi_deva_pii():
    for language, script in TRANSLITERABLE_PII_SCRIPT_BY_LANGUAGE.items():
        if language == "HI_DEVA_PII":
            assert script == "DEVANAGARI"
        else:
            assert script == "LATIN"


def test_schema_pii_script_enum_has_exactly_four_values_no_new_ones_added():
    assert set(SCHEMA["$defs"]["pii_script"]["enum"]) == {
        "LATIN",
        "DEVANAGARI",
        "MIXED",
        "NUMERIC",
    }


def test_each_frozen_non_transliterable_pii_script_is_schema_valid():
    for pii_type, script in NON_TRANSLITERABLE_PII_SCRIPT.items():
        VALIDATOR.validate(
            {**_MINIMAL_VALID_RECORD(), "entities": [_entity(pii_type, script)]}
        )


def test_each_frozen_transliterable_pii_script_is_schema_valid():
    for language, script in TRANSLITERABLE_PII_SCRIPT_BY_LANGUAGE.items():
        record = {**_MINIMAL_VALID_RECORD(), "language": language}
        record["entities"] = [_entity("PERSON", script)]
        VALIDATOR.validate(record)


def test_upi_id_is_mixed_not_numeric_or_latin_alone():
    """The specific worked example this decision hinged on: 9876543210@mail.test
    combines a numeric local part and a Latin domain."""
    assert NON_TRANSLITERABLE_PII_SCRIPT["UPI_ID"] == "MIXED"
    assert NON_TRANSLITERABLE_PII_SCRIPT["UPI_ID"] not in ("NUMERIC", "LATIN")


# --- OQ-014 frozen variant_id format (guidelines.md §4.16, decision 37) ----

_VARIANT_ID_PATTERN = re.compile(SCHEMA["properties"]["variant_id"]["pattern"])
_PERTURBATION_SUFFIX_RE = re.compile(r"_A[1-5]_[0-9]+$")


def clean_variant_id(base_id: str, language: str) -> str:
    """The frozen clean-record variant_id format: {base_id}_{language}."""
    return f"{base_id}_{language}"


def test_clean_variant_id_format_is_base_id_underscore_language():
    for language in LANGUAGES:
        vid = clean_variant_id("PERSON_001", language)
        assert vid == f"PERSON_001_{language}"


def test_clean_variant_ids_match_the_frozen_worked_examples():
    expected = [
        "PERSON_001_EN",
        "PERSON_001_IN_EN",
        "PERSON_001_HI_LATIN_PII",
        "PERSON_001_HI_DEVA_PII",
        "PERSON_001_ROM_HI",
        "PERSON_001_HINGLISH",
        "PERSON_001_INFORMAL_HINGLISH",
    ]
    actual = [clean_variant_id("PERSON_001", lang) for lang in LANGUAGES]
    assert actual == expected


def test_clean_variant_ids_contain_no_perturbation_suffix():
    for language in LANGUAGES:
        vid = clean_variant_id("PAN_001", language)
        assert not _PERTURBATION_SUFFIX_RE.search(vid), vid


def test_clean_variant_ids_are_schema_valid():
    for language in LANGUAGES:
        vid = clean_variant_id("BANK_ACCOUNT_013", language)
        assert _VARIANT_ID_PATTERN.match(vid)


def test_clean_record_perturbation_block_is_all_none():
    clean_perturbation = {
        "family": "NONE",
        "type": "NONE",
        "severity": 0,
        "target": "NONE",
    }
    record = {**_MINIMAL_VALID_RECORD(), "perturbation": clean_perturbation}
    VALIDATOR.validate(record)


# --- OQ-027 frozen context decision (guidelines.md §4.17, decision 38) -----

T08_CONTEXT = "EXPLICIT"


def test_explicit_is_a_valid_schema_context_value():
    assert T08_CONTEXT in SCHEMA["$defs"]["context"]["enum"]


def test_t08_context_constant_is_explicit():
    assert T08_CONTEXT == "EXPLICIT"


def test_minimal_record_with_frozen_context_is_schema_valid():
    record = {**_MINIMAL_VALID_RECORD(), "context": T08_CONTEXT}
    VALIDATOR.validate(record)


# --- Helper: a minimal, otherwise-valid record to mutate per test ----------


def _MINIMAL_VALID_RECORD():
    return {
        "base_id": "PAN_001",
        "variant_id": "PAN_001_EN",
        "text": "My PAN number is ABCDE1234F.",
        "entities": [_entity("PAN", "LATIN", "ABCDE1234F")],
        "distractors": [],
        "language": "EN",
        "carrier_script": "LATIN",
        "context": "EXPLICIT",
        "domain": "ACCOUNT_VERIFICATION",
        "perturbation": {
            "family": "NONE",
            "type": "NONE",
            "severity": 0,
            "target": "NONE",
        },
        "difficulty": "EASY",
        "address_structure": None,
        "hi_variant_collapsed": False,
        "synthetic": True,
        "generator_version": "0.1.0",
        "guidelines_version": "0.11",
        "template_id": "EN_PAN_TEMPLATE",
        "seed": 42,
        "validation": {
            "structural": "PENDING",
            "span": "PENDING",
            "semantic": "PENDING",
            "language": "PENDING",
            "duplicate": "PENDING",
            "human": "PENDING",
        },
        "validation_status": "PENDING",
        "review_status": "PENDING",
        "split": None,
    }


def test_minimal_valid_record_itself_validates():
    VALIDATOR.validate(_MINIMAL_VALID_RECORD())


# --- guidelines.md §17's new clean-record worked example, reproduced exactly,
# proving the documentation example itself is schema-valid -----------------


def test_guidelines_section_17_clean_example_is_schema_valid():
    clean_example = {
        "base_id": "PAN_001",
        "variant_id": "PAN_001_EN",
        "text": "My PAN number is ABCDE1234F.",
        "entities": [
            {
                "type": "PAN",
                "base_pii_value": "ABCDE1234F",
                "realized_pii_value": "ABCDE1234F",
                "pii_script": "LATIN",
                "start": 17,
                "end": 27,
                "occurrence_index": 0,
            }
        ],
        "distractors": [],
        "language": "EN",
        "carrier_script": "LATIN",
        "context": "EXPLICIT",
        "domain": "ACCOUNT_VERIFICATION",
        "perturbation": {
            "family": "NONE",
            "type": "NONE",
            "severity": 0,
            "target": "NONE",
        },
        "difficulty": "EASY",
        "address_structure": None,
        "hi_variant_collapsed": False,
        "synthetic": True,
        "generator_version": "0.1.0",
        "guidelines_version": "0.11",
        "template_id": "EN_PAN_TEMPLATE",
        "seed": 42,
        "validation": {
            "structural": "PENDING",
            "span": "PENDING",
            "semantic": "PENDING",
            "language": "PENDING",
            "duplicate": "PENDING",
            "human": "PENDING",
        },
        "validation_status": "PENDING",
        "review_status": "PENDING",
        "split": None,
    }
    VALIDATOR.validate(clean_example)
    # and the span contract holds, exactly as guidelines.md §14.1 requires
    entity = clean_example["entities"][0]
    assert (
        clean_example["text"][entity["start"] : entity["end"]]
        == entity["realized_pii_value"]
    )
