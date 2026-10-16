import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "schemas"
FIXTURES = ROOT / "tests" / "fixtures"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_base_instance_fixture_validates():
    schema = _load(SCHEMAS / "base_instance.schema.json")
    instance = _load(FIXTURES / "base_instance.valid.json")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(instance)


def test_example_fixture_validates():
    schema = _load(SCHEMAS / "example.schema.json")
    instance = _load(FIXTURES / "example.valid.json")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(instance)


def test_hard_negative_base_instance_fixture_validates():
    """base_kind == HARD_NEGATIVE with pii == [] is structurally valid (OQ-003)."""
    schema = _load(SCHEMAS / "base_instance.schema.json")
    instance = _load(FIXTURES / "base_instance.hard_negative.valid.json")
    Draft202012Validator(schema).validate(instance)


def test_invalid_base_kind_is_rejected_by_schema():
    """base_kind enum membership is structural, so this fails at the schema layer,
    not the validators/base_kind.py cross-field check (guidelines.md §13.4)."""
    schema = _load(SCHEMAS / "base_instance.schema.json")
    instance = copy.deepcopy(_load(FIXTURES / "base_instance.valid.json"))
    instance["base_kind"] = "NEUTRAL"
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(instance)


# --- hard_negative_decoy (guidelines.md §13.12, resolves OQ-046) -------------


def test_positive_base_without_hard_negative_decoy_field_is_valid():
    """Required check 1: the field is optional -- an existing POSITIVE base
    that simply lacks the key entirely (as all 100 real bases do) must
    remain valid, with no fixture edit needed to accommodate it."""
    schema = _load(SCHEMAS / "base_instance.schema.json")
    instance = _load(FIXTURES / "base_instance.valid.json")
    assert "hard_negative_decoy" not in instance
    Draft202012Validator(schema).validate(instance)


def test_positive_base_with_explicit_null_hard_negative_decoy_is_valid():
    schema = _load(SCHEMAS / "base_instance.schema.json")
    instance = copy.deepcopy(_load(FIXTURES / "base_instance.valid.json"))
    instance["hard_negative_decoy"] = None
    Draft202012Validator(schema).validate(instance)


def test_hard_negative_base_with_populated_decoy_is_valid():
    """Required check 2."""
    schema = _load(SCHEMAS / "base_instance.schema.json")
    instance = _load(FIXTURES / "base_instance.hard_negative.valid.json")
    assert instance["hard_negative_decoy"]["decoy_class"] == "NUMERIC_SHAPE"
    Draft202012Validator(schema).validate(instance)


def _hard_negative_with_decoy(**overrides):
    base = copy.deepcopy(_load(FIXTURES / "base_instance.hard_negative.valid.json"))
    base["hard_negative_decoy"].update(overrides)
    return base


def test_hard_negative_decoy_invalid_decoy_class_is_rejected():
    """Required check 4."""
    schema = _load(SCHEMAS / "base_instance.schema.json")
    instance = _hard_negative_with_decoy(decoy_class="NOT_A_REAL_CLASS")
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(instance)


def test_hard_negative_decoy_missing_value_is_rejected():
    """Required check 5."""
    schema = _load(SCHEMAS / "base_instance.schema.json")
    instance = _hard_negative_with_decoy()
    del instance["hard_negative_decoy"]["value"]
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(instance)


def test_hard_negative_decoy_missing_surface_type_is_rejected():
    """Required check 6."""
    schema = _load(SCHEMAS / "base_instance.schema.json")
    instance = _hard_negative_with_decoy()
    del instance["hard_negative_decoy"]["surface_type"]
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(instance)


def test_hard_negative_decoy_missing_actual_role_is_rejected():
    """Required check 7."""
    schema = _load(SCHEMAS / "base_instance.schema.json")
    instance = _hard_negative_with_decoy()
    del instance["hard_negative_decoy"]["actual_role"]
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(instance)


def test_hard_negative_decoy_extra_field_is_rejected():
    """Required check 8."""
    schema = _load(SCHEMAS / "base_instance.schema.json")
    instance = _hard_negative_with_decoy(extra_field="not allowed")
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(instance)


def test_hard_negative_decoy_enum_matches_example_schema_exactly():
    """The two schemas duplicate this enum (no cross-file $ref, same
    convention as generator_version) -- they must never drift apart."""
    base_schema = _load(SCHEMAS / "base_instance.schema.json")
    example_schema = _load(SCHEMAS / "example.schema.json")
    assert (
        set(base_schema["$defs"]["decoy_class"]["enum"])
        == set(example_schema["$defs"]["decoy_class"]["enum"])
    )


def test_pii_empty_list_remains_mandatory_for_hard_negative_at_schema_level():
    """Required check 9 (schema half -- pii itself is still schema-legal as
    an empty array; the cross-field requirement that it must be empty for
    HARD_NEGATIVE is validators/base_kind.py's job, exercised in
    tests/test_base_kind_invariant.py)."""
    schema = _load(SCHEMAS / "base_instance.schema.json")
    instance = _load(FIXTURES / "base_instance.hard_negative.valid.json")
    assert instance["pii"] == []
    Draft202012Validator(schema).validate(instance)


def test_entities_field_is_rejected_on_base_instance():
    """Required check 10: entities[] is exclusively a derived-record field
    (schemas/example.schema.json) -- additionalProperties: false on the base
    schema must reject it outright, for POSITIVE and HARD_NEGATIVE alike."""
    schema = _load(SCHEMAS / "base_instance.schema.json")
    instance = copy.deepcopy(_load(FIXTURES / "base_instance.hard_negative.valid.json"))
    instance["entities"] = []
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(instance)


def test_distractors_field_is_rejected_on_base_instance():
    """Required check 11: distractors[] stays derived-record-only per
    guidelines.md §13.4's explicit "must not gain a distractors property" --
    unaffected by hard_negative_decoy's addition."""
    schema = _load(SCHEMAS / "base_instance.schema.json")
    instance = copy.deepcopy(_load(FIXTURES / "base_instance.hard_negative.valid.json"))
    instance["distractors"] = [
        {
            "text": "9876543210",
            "start": 20,
            "end": 30,
            "surface_type": "PHONE",
            "actual_role": "ORDER_REFERENCE",
            "decoy_class": "NUMERIC_SHAPE",
        }
    ]
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(instance)
