"""T11 Phase 1: tests for generators/hard_negatives.py, written before the
generator itself (this project's established convention, see
generators/base_instances.py's own T04 turn).

Exercises the frozen architecture: guidelines.md §13.8 (four constructible
decoy-class rules), §13.9 (5/5/4/3/0/3 quota), §13.12 (hard_negative_decoy
persisted on the base). Does not generate derived records, does not modify
data/raw/base_instances.jsonl, does not touch validators/spans.py or
validators/semantic.py.
"""

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from validators.base_kind import (
    check_base_kind_hard_negative_decoy_invariant,
    check_base_kind_pii_invariant,
)

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "base_instance.schema.json"
EXISTING_BASES_PATH = ROOT / "data" / "raw" / "base_instances.jsonl"

SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)

FROZEN_QUOTA = {
    "NUMERIC_SHAPE": 5,
    "ALNUM_SHAPE": 5,
    "NAME_AS_PLACE": 4,
    "HANDLE_SHAPE": 3,
    "ORG_AS_PERSON": 0,
    "PARTIAL_PII": 3,
}

FROZEN_ROLE_AND_SURFACE = {
    # class -> (actual_role, allowed surface_types)
    "NUMERIC_SHAPE": ("ORDER_REFERENCE", {"PHONE", "AADHAAR", "BANK_ACCOUNT"}),
    "ALNUM_SHAPE": ("REFERENCE_CODE", {"PAN"}),
    "NAME_AS_PLACE": ("LOCALITY", {"LOCATION"}),
    "HANDLE_SHAPE": ("INTERNAL_HANDLE", {"EMAIL"}),
    "PARTIAL_PII": ("MASKED_IDENTIFIER", {"AADHAAR", "BANK_ACCOUNT"}),
}


def _generate():
    from generators.hard_negatives import generate_hard_negative_bases

    return generate_hard_negative_bases(seed=42)


def test_generates_exactly_twenty_bases():
    records = _generate()
    assert len(records) == 20


def test_quota_matches_the_frozen_13_9_table_exactly():
    records = _generate()
    counts = {}
    for r in records:
        cls = r["hard_negative_decoy"]["decoy_class"]
        counts[cls] = counts.get(cls, 0) + 1
    counts.setdefault("ORG_AS_PERSON", 0)
    assert counts == FROZEN_QUOTA


def test_org_as_person_and_handle_shape_are_not_invented_beyond_the_frozen_rule():
    records = _generate()
    classes_present = {r["hard_negative_decoy"]["decoy_class"] for r in records}
    assert "ORG_AS_PERSON" not in classes_present
    assert "HANDLE_SHAPE" in classes_present  # frozen, constructible -- must appear


def test_base_ids_are_unique_neg_prefixed_and_dont_collide_with_existing_bases():
    records = _generate()
    ids = [r["base_id"] for r in records]
    assert len(ids) == len(set(ids))
    assert all(i.startswith("NEG_") for i in ids)

    existing_ids = {
        json.loads(line)["base_id"]
        for line in EXISTING_BASES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    assert not (set(ids) & existing_ids)


def test_every_record_is_hard_negative_with_empty_pii():
    records = _generate()
    for r in records:
        assert r["base_kind"] == "HARD_NEGATIVE"
        assert r["pii"] == []


def test_every_record_has_no_entities_or_distractors_keys():
    records = _generate()
    for r in records:
        assert "entities" not in r
        assert "distractors" not in r


def test_every_record_has_a_populated_hard_negative_decoy_with_exactly_four_fields():
    records = _generate()
    for r in records:
        decoy = r["hard_negative_decoy"]
        assert decoy is not None
        assert set(decoy.keys()) == {"decoy_class", "value", "surface_type", "actual_role"}


def test_role_and_surface_type_match_the_frozen_section_13_8_table():
    records = _generate()
    for r in records:
        decoy = r["hard_negative_decoy"]
        expected_role, allowed_surfaces = FROZEN_ROLE_AND_SURFACE[decoy["decoy_class"]]
        assert decoy["actual_role"] == expected_role
        assert decoy["surface_type"] in allowed_surfaces


def test_canonical_text_contains_the_decoy_value_exactly_once():
    records = _generate()
    for r in records:
        value = r["hard_negative_decoy"]["value"]
        assert r["canonical_text"].count(value) == 1


def test_every_record_validates_against_base_instance_schema():
    records = _generate()
    for r in records:
        VALIDATOR.validate(r)


def test_every_record_passes_both_base_kind_invariants():
    records = _generate()
    for r in records:
        check_base_kind_pii_invariant(r)  # must not raise
        check_base_kind_hard_negative_decoy_invariant(r)  # must not raise


def test_every_record_has_populated_scenario_and_synthetic_true():
    records = _generate()
    for r in records:
        assert r["scenario"]["domain"]
        assert r["scenario"]["purpose"]
        assert r["synthetic"] is True
        assert r["generator_version"]


def test_decoy_values_are_unique_within_each_class():
    records = _generate()
    by_class = {}
    for r in records:
        decoy = r["hard_negative_decoy"]
        by_class.setdefault(decoy["decoy_class"], set())
        assert decoy["value"] not in by_class[decoy["decoy_class"]], "duplicate decoy value within class"
        by_class[decoy["decoy_class"]].add(decoy["value"])


def test_generation_is_deterministic_across_independent_runs():
    first = _generate()
    second = _generate()
    assert first == second


def test_existing_100_positive_bases_are_untouched_by_generation():
    """Generation must not read-then-write data/raw/base_instances.jsonl --
    calling the hard-negative generator must not change it at all."""
    before = EXISTING_BASES_PATH.read_text(encoding="utf-8")
    _generate()
    after = EXISTING_BASES_PATH.read_text(encoding="utf-8")
    assert before == after


def test_assert_dataset_valid_accepts_the_generated_set():
    from generators.hard_negatives import assert_hard_negative_dataset_valid

    records = _generate()
    assert_hard_negative_dataset_valid(records)  # must not raise


def test_assert_dataset_valid_rejects_wrong_count():
    from generators.hard_negatives import assert_hard_negative_dataset_valid

    records = _generate()[:19]
    with pytest.raises(AssertionError):
        assert_hard_negative_dataset_valid(records)


def test_assert_dataset_valid_rejects_wrong_quota():
    from generators.hard_negatives import assert_hard_negative_dataset_valid

    records = copy.deepcopy(_generate())
    records[0]["hard_negative_decoy"]["decoy_class"] = "PARTIAL_PII"
    with pytest.raises(AssertionError):
        assert_hard_negative_dataset_valid(records)


def test_write_refuses_to_overwrite_an_existing_file(tmp_path):
    from generators.hard_negatives import write_hard_negative_bases

    target = tmp_path / "hard_negative_bases.jsonl"
    target.write_text("existing content\n", encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_hard_negative_bases(_generate(), output_path=target)
