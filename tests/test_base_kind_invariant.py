import copy
import json
from pathlib import Path

import pytest

from validators.base_kind import (
    BaseKindInvariantError,
    check_base_kind_hard_negative_decoy_invariant,
    check_base_kind_pii_invariant,
)

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def positive_base():
    return _load(FIXTURES / "base_instance.valid.json")


@pytest.fixture
def hard_negative_base():
    return _load(FIXTURES / "base_instance.hard_negative.valid.json")


def test_positive_with_nonempty_pii_is_valid(positive_base):
    assert positive_base["base_kind"] == "POSITIVE"
    assert len(positive_base["pii"]) >= 1
    check_base_kind_pii_invariant(positive_base)  # must not raise


def test_hard_negative_with_empty_pii_is_valid(hard_negative_base):
    assert hard_negative_base["base_kind"] == "HARD_NEGATIVE"
    assert hard_negative_base["pii"] == []
    check_base_kind_pii_invariant(hard_negative_base)  # must not raise


def test_positive_with_empty_pii_is_invalid(positive_base):
    broken = copy.deepcopy(positive_base)
    broken["pii"] = []
    with pytest.raises(BaseKindInvariantError):
        check_base_kind_pii_invariant(broken)


def test_hard_negative_with_nonempty_pii_is_invalid(hard_negative_base):
    broken = copy.deepcopy(hard_negative_base)
    broken["pii"] = [
        {"type": "PAN", "base_pii_value": "ABCDE1234F", "semantic_role": "TAX_IDENTIFIER"}
    ]
    with pytest.raises(BaseKindInvariantError):
        check_base_kind_pii_invariant(broken)


# --- hard_negative_decoy cross-field invariant (guidelines.md §13.12, OQ-046) --


def test_hard_negative_with_populated_decoy_is_valid(hard_negative_base):
    assert hard_negative_base["hard_negative_decoy"] is not None
    check_base_kind_hard_negative_decoy_invariant(hard_negative_base)  # must not raise


def test_positive_without_decoy_field_is_valid(positive_base):
    assert "hard_negative_decoy" not in positive_base
    check_base_kind_hard_negative_decoy_invariant(positive_base)  # must not raise


def test_positive_with_explicit_null_decoy_is_valid(positive_base):
    with_null = copy.deepcopy(positive_base)
    with_null["hard_negative_decoy"] = None
    check_base_kind_hard_negative_decoy_invariant(with_null)  # must not raise


def test_hard_negative_without_decoy_field_is_invalid(hard_negative_base):
    """Required check 3: HARD_NEGATIVE missing hard_negative_decoy entirely
    is rejected by the validator invariant -- the schema alone permits the
    field's absence (it is optional), so this must be caught here, not by
    schema validation."""
    broken = copy.deepcopy(hard_negative_base)
    del broken["hard_negative_decoy"]
    with pytest.raises(BaseKindInvariantError):
        check_base_kind_hard_negative_decoy_invariant(broken)


def test_hard_negative_with_null_decoy_is_invalid(hard_negative_base):
    broken = copy.deepcopy(hard_negative_base)
    broken["hard_negative_decoy"] = None
    with pytest.raises(BaseKindInvariantError):
        check_base_kind_hard_negative_decoy_invariant(broken)


def test_positive_with_populated_decoy_is_invalid(positive_base):
    broken = copy.deepcopy(positive_base)
    broken["hard_negative_decoy"] = {
        "decoy_class": "NUMERIC_SHAPE",
        "value": "9876543210",
        "surface_type": "PHONE",
        "actual_role": "ORDER_REFERENCE",
    }
    with pytest.raises(BaseKindInvariantError):
        check_base_kind_hard_negative_decoy_invariant(broken)
