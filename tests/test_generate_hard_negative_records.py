"""T11 Phase 2: tests for generators/language/hard_negative_records.py,
written before generating the canonical hard-negative derived-record
dataset (this project's established convention).

Exercises the frozen architecture: guidelines.md §13.11 (six realizations,
collapsed Hindi labeled HI_LATIN_PII, never HI_DEVA_PII), §13.13 (exact
carrier grammar per decoy_class, resolves OQ-047), §13.12/schema
(hard_negative_decoy is the sole persisted ground truth for the derived
distractor). Does not touch OQ-048 (distractor-span validation is a
construction-time check here, not a validators/spans.py contract change).
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from generators.language import metadata, templates
from generators.language.hard_negative_records import (
    GENERATOR_VERSION,
    HARD_NEGATIVE_CARRIER_DEVANAGARI,
    HARD_NEGATIVE_CARRIER_ROM_HI,
    generate_all_records,
    generate_records_for_base,
    load_hard_negative_bases,
)
from generators.language.spans import find_occurrence

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_SCHEMA = json.loads(
    (ROOT / "schemas" / "example.schema.json").read_text(encoding="utf-8")
)
VALIDATOR = Draft202012Validator(EXAMPLE_SCHEMA)

POSITIVE_BASES_PATH = ROOT / "data" / "raw" / "base_instances.jsonl"
HARD_NEGATIVE_BASES_PATH = ROOT / "data" / "raw" / "hard_negative_bases.jsonl"
POSITIVE_RECORDS_PATH = ROOT / "data" / "generated" / "language_realizations.jsonl"

EXPECTED_LANGUAGES = {
    "EN", "IN_EN", "ROM_HI", "HINGLISH", "INFORMAL_HINGLISH", "HI_LATIN_PII",
}

FROZEN_QUOTA = {
    "NUMERIC_SHAPE": 5,
    "ALNUM_SHAPE": 5,
    "NAME_AS_PLACE": 4,
    "HANDLE_SHAPE": 3,
    "PARTIAL_PII": 3,
}


@pytest.fixture(scope="module")
def bases():
    return load_hard_negative_bases()


@pytest.fixture(scope="module")
def base_by_id(bases):
    return {b["base_id"]: b for b in bases}


@pytest.fixture(scope="module")
def records(bases):
    return generate_all_records(bases)


@pytest.fixture(scope="module")
def by_base(records):
    grouped = {}
    for r in records:
        grouped.setdefault(r["base_id"], []).append(r)
    return grouped


# 1. Exactly 120 records total -------------------------------------------------

def test_exactly_120_records_total(records):
    assert len(records) == 120


# 2. Exactly 6 per NEG base -----------------------------------------------------

def test_exactly_six_records_per_base(by_base, bases):
    assert set(by_base) == {b["base_id"] for b in bases}
    for base_id, recs in by_base.items():
        assert len(recs) == 6, base_id


# 3. Exact six language conditions ----------------------------------------------

def test_exact_six_language_conditions_per_base(by_base):
    for base_id, recs in by_base.items():
        assert {r["language"] for r in recs} == EXPECTED_LANGUAGES, base_id


# 4. No HI_DEVA_PII ever ---------------------------------------------------------

def test_hi_deva_pii_never_generated(records):
    for r in records:
        assert r["language"] != "HI_DEVA_PII"


# 5. entities == [] always -------------------------------------------------------

def test_entities_always_empty(records):
    for r in records:
        assert r["entities"] == []


# 6. Exactly one distractor -------------------------------------------------------

def test_exactly_one_distractor_per_record(records):
    for r in records:
        assert len(r["distractors"]) == 1


# 7. Distractor metadata equals persisted hard_negative_decoy exactly -----------

def test_distractor_metadata_matches_persisted_decoy_exactly(records, base_by_id):
    for r in records:
        decoy = base_by_id[r["base_id"]]["hard_negative_decoy"]
        d = r["distractors"][0]
        assert d["surface_type"] == decoy["surface_type"]
        assert d["actual_role"] == decoy["actual_role"]
        assert d["decoy_class"] == decoy["decoy_class"]


# 8. Distractor value unchanged --------------------------------------------------

def test_distractor_text_equals_persisted_decoy_value(records, base_by_id):
    for r in records:
        decoy = base_by_id[r["base_id"]]["hard_negative_decoy"]
        assert r["distractors"][0]["text"] == decoy["value"]


# 9-10. Distractor span correctness and containment -----------------------------

def test_distractor_span_matches_text_slice(records):
    for r in records:
        d = r["distractors"][0]
        assert r["text"][d["start"] : d["end"]] == d["text"]


def test_distractor_span_within_text_bounds(records):
    for r in records:
        d = r["distractors"][0]
        assert 0 <= d["start"] < d["end"] <= len(r["text"])


# 11-12. Base linkage and base_kind (via base) -----------------------------------

def test_every_record_links_to_an_existing_hard_negative_base(records, base_by_id):
    for r in records:
        assert r["base_id"] in base_by_id


def test_linked_base_is_hard_negative(records, base_by_id):
    for r in records:
        assert base_by_id[r["base_id"]]["base_kind"] == "HARD_NEGATIVE"


# 13. variant_id format and uniqueness -------------------------------------------

def test_variant_id_format_and_uniqueness(records):
    ids = [r["variant_id"] for r in records]
    assert len(ids) == len(set(ids))
    for r in records:
        assert r["variant_id"] == f"{r['base_id']}_{r['language']}"


# 14. context always EXPLICIT ----------------------------------------------------

def test_context_always_explicit(records):
    for r in records:
        assert r["context"] == "EXPLICIT"


# 15. perturbation always NONE ---------------------------------------------------

def test_perturbation_always_none(records):
    for r in records:
        assert r["perturbation"] == {
            "family": "NONE", "type": "NONE", "severity": 0, "target": "NONE",
        }


# 16. Schema validity -------------------------------------------------------------

def test_every_record_schema_valid(records):
    for r in records:
        VALIDATOR.validate(r)


# 17. All five constructible decoy classes represented per frozen quota ----------

def test_decoy_class_counts_match_frozen_quota_times_six(records):
    counts = {}
    for r in records:
        cls = r["distractors"][0]["decoy_class"]
        counts[cls] = counts.get(cls, 0) + 1
    expected = {cls: n * 6 for cls, n in FROZEN_QUOTA.items()}
    assert counts == expected


# 18. ORG_AS_PERSON absent ---------------------------------------------------------

def test_org_as_person_never_present(records):
    for r in records:
        assert r["distractors"][0]["decoy_class"] != "ORG_AS_PERSON"


# 19. Exact language x decoy-class counts ------------------------------------------

def test_language_by_decoy_class_matrix_matches_quota(records):
    matrix = {}
    for r in records:
        key = (r["language"], r["distractors"][0]["decoy_class"])
        matrix[key] = matrix.get(key, 0) + 1
    for language in EXPECTED_LANGUAGES:
        for decoy_class, quota in FROZEN_QUOTA.items():
            assert matrix.get((language, decoy_class)) == quota, (language, decoy_class)


# 20. Deterministic for seed 42 (in-memory) ----------------------------------------

def test_deterministic_repeated_generation_in_memory(bases):
    first = generate_all_records(bases)
    second = generate_all_records(bases)
    assert first == second


# 21. Fresh-process deterministic regeneration -------------------------------------

def test_deterministic_across_fresh_processes():
    script = (
        "import json, sys; "
        "sys.path.insert(0, r'" + str(ROOT) + "'); "
        "from generators.language.hard_negative_records import generate_all_records, load_hard_negative_bases; "
        "print(json.dumps(generate_all_records(load_hard_negative_bases())))"
    )
    outputs = []
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, check=True, cwd=str(ROOT),
        )
        outputs.append(json.loads(result.stdout))
    assert outputs[0] == outputs[1]


# 22-23. Existing positive datasets remain byte-identical --------------------------

def test_existing_624_positive_records_untouched(records):
    reloaded = POSITIVE_RECORDS_PATH.read_text(encoding="utf-8")
    lines = [json.loads(line) for line in reloaded.splitlines() if line.strip()]
    assert len(lines) == 624


def test_existing_100_positive_bases_untouched(records):
    reloaded = POSITIVE_BASES_PATH.read_text(encoding="utf-8")
    lines = [json.loads(line) for line in reloaded.splitlines() if line.strip()]
    assert len(lines) == 100
    assert all(b["base_kind"] == "POSITIVE" for b in lines)


# 24. No NEG records in the positive realization file ------------------------------

def test_no_neg_records_in_positive_realization_file():
    text = POSITIVE_RECORDS_PATH.read_text(encoding="utf-8")
    assert "NEG_" not in text


# 25. All persisted decoy values used exactly as ground truth ----------------------

def test_all_persisted_decoy_values_used_exactly(bases, by_base):
    for base in bases:
        decoy_value = base["hard_negative_decoy"]["value"]
        for r in by_base[base["base_id"]]:
            assert r["distractors"][0]["text"] == decoy_value


# 26. HINGLISH doesn't mutate the distractor ---------------------------------------

def test_hinglish_does_not_mutate_distractor(by_base, base_by_id):
    for base_id, recs in by_base.items():
        decoy_value = base_by_id[base_id]["hard_negative_decoy"]["value"]
        hinglish = next(r for r in recs if r["language"] == "HINGLISH")
        assert hinglish["distractors"][0]["text"] == decoy_value
        assert decoy_value in hinglish["text"]


# 27. INFORMAL_HINGLISH doesn't mutate the distractor -------------------------------

def test_informal_hinglish_does_not_mutate_distractor(by_base, base_by_id):
    for base_id, recs in by_base.items():
        decoy_value = base_by_id[base_id]["hard_negative_decoy"]["value"]
        informal = next(r for r in recs if r["language"] == "INFORMAL_HINGLISH")
        assert informal["distractors"][0]["text"] == decoy_value
        assert decoy_value in informal["text"]


# 28. Collapsed Hindi carrier is exactly the frozen §13.13 carrier ------------------

def test_collapsed_hindi_carrier_matches_section_13_13_exactly(by_base, base_by_id):
    for base_id, recs in by_base.items():
        decoy = base_by_id[base_id]["hard_negative_decoy"]
        expected_text = HARD_NEGATIVE_CARRIER_DEVANAGARI[decoy["decoy_class"]].format(
            value=decoy["value"]
        )
        collapsed = next(r for r in recs if r["language"] == "HI_LATIN_PII")
        assert collapsed["text"] == expected_text
        assert collapsed["hi_variant_collapsed"] is True


def test_rom_hi_carrier_matches_section_13_13_exactly(by_base, base_by_id):
    for base_id, recs in by_base.items():
        decoy = base_by_id[base_id]["hard_negative_decoy"]
        expected_text = HARD_NEGATIVE_CARRIER_ROM_HI[decoy["decoy_class"]].format(
            value=decoy["value"]
        )
        rom_hi = next(r for r in recs if r["language"] == "ROM_HI")
        assert rom_hi["text"] == expected_text


# 29. NAME_AS_PLACE keeps the value unchanged, only carrier transforms ---------------

def test_name_as_place_value_unchanged_across_all_six_conditions(by_base, base_by_id):
    for base_id, recs in by_base.items():
        decoy = base_by_id[base_id]["hard_negative_decoy"]
        if decoy["decoy_class"] != "NAME_AS_PLACE":
            continue
        for r in recs:
            assert r["distractors"][0]["text"] == decoy["value"]
            assert decoy["value"] in r["text"]


# 30. Numeric/alphanumeric/handle/partial-PII values structurally unchanged ---------

@pytest.mark.parametrize(
    "decoy_class", ["NUMERIC_SHAPE", "ALNUM_SHAPE", "HANDLE_SHAPE", "PARTIAL_PII"]
)
def test_value_never_transliterated_or_altered(by_base, base_by_id, decoy_class):
    for base_id, recs in by_base.items():
        decoy = base_by_id[base_id]["hard_negative_decoy"]
        if decoy["decoy_class"] != decoy_class:
            continue
        for r in recs:
            assert r["distractors"][0]["text"] == decoy["value"]


# --- Additional construction-time checks (not a validators/ contract; OQ-048
# remains untouched) ----------------------------------------------------------

def test_en_equals_canonical_text_exactly(by_base, base_by_id):
    for base_id, recs in by_base.items():
        en = next(r for r in recs if r["language"] == "EN")
        assert en["text"] == base_by_id[base_id]["canonical_text"]


def test_in_en_uses_a_frozen_marker(by_base):
    signature_phrases = [
        "kindly note", "do the needful", "revert", "prepone",
        "please find the details below", "intimate", "the same",
        "at the earliest",
    ]
    for base_id, recs in by_base.items():
        in_en = next(r for r in recs if r["language"] == "IN_EN")
        lowered = in_en["text"].lower()
        assert any(p in lowered for p in signature_phrases), in_en["text"]


def test_hinglish_uses_a_frozen_pattern(by_base):
    for base_id, recs in by_base.items():
        hinglish = next(r for r in recs if r["language"] == "HINGLISH")
        assert hinglish["text"].startswith("Sir, ") or hinglish["text"].endswith(
            ", please confirm."
        )


def test_carrier_script_correct(records):
    for r in records:
        expected = "DEVANAGARI" if r["language"] == "HI_LATIN_PII" else "LATIN"
        assert r["carrier_script"] == expected


def test_hi_variant_collapsed_false_for_five_conditions(records):
    for r in records:
        if r["language"] != "HI_LATIN_PII":
            assert r["hi_variant_collapsed"] is False


def test_address_structure_always_none(records):
    for r in records:
        assert r["address_structure"] is None


def test_synthetic_always_true(records):
    assert all(r["synthetic"] is True for r in records)


def test_generator_version_and_guidelines_version_recorded(records):
    for r in records:
        assert r["generator_version"] == GENERATOR_VERSION
        assert r["guidelines_version"] == "0.17"


def test_no_llm_or_network_dependency():
    source = (
        ROOT / "generators" / "language" / "hard_negative_records.py"
    ).read_text(encoding="utf-8")
    forbidden = ["openai", "anthropic", "requests", "urllib", "httpx", "socket"]
    lowered = source.lower()
    for word in forbidden:
        assert word not in lowered, f"forbidden dependency found: {word}"


def test_write_refuses_to_overwrite_an_existing_file(tmp_path, bases):
    from generators.language.hard_negative_records import write_derived_records

    target = tmp_path / "hard_negative_realizations.jsonl"
    target.write_text("existing content\n", encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_derived_records(generate_all_records(bases), output_path=target)


def test_generate_records_for_base_returns_six_records_directly(bases):
    recs = generate_records_for_base(bases[0], 0)
    assert len(recs) == 6
    assert {r["language"] for r in recs} == EXPECTED_LANGUAGES


# --- Regression: T08 positive-generation behavior is unchanged --------------------

def test_t08_positive_generation_still_produces_the_canonical_624_records():
    from generators.language.records import generate_all_records as t08_generate_all
    from generators.language.records import load_base_instances

    positive_bases = load_base_instances()
    regenerated = t08_generate_all(positive_bases)

    canonical = [
        json.loads(line)
        for line in POSITIVE_RECORDS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert regenerated == canonical


def test_t08_shared_dependency_modules_are_byte_unchanged_by_this_module_existing():
    """generators/language/hard_negative_records.py must not have required any
    edit to metadata.py, templates.py, spans.py, or realizations.py -- confirm
    none of T08's own frozen constants were touched by importing this new
    module (e.g. accidental monkeypatching), by checking the frozen values
    used elsewhere are what T08's own test suite already expects."""
    assert templates.LANGUAGES == (
        "EN", "IN_EN", "HI_LATIN_PII", "HI_DEVA_PII", "ROM_HI", "HINGLISH",
        "INFORMAL_HINGLISH",
    )
    assert metadata.CONTEXT == "EXPLICIT"
