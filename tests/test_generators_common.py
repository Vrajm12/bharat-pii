"""Shared tests: GeneratedPII contract, and the base_kind/base_id independence
requirement that applies identically to every T03 generator."""

import inspect
import json
import random
from pathlib import Path

import pytest

from generators.pii._common import PII_TYPES, GeneratedPII
from generators.pii.aadhaar import generate_aadhaar
from generators.pii.address import generate_address
from generators.pii.bank_account import generate_bank_account
from generators.pii.email import generate_email
from generators.pii.pan import generate_pan
from generators.pii.person import generate_person
from generators.pii.phone import generate_phone
from generators.pii.upi_id import generate_upi_id

ROOT = Path(__file__).resolve().parent.parent

ALL_GENERATORS = (
    generate_person,
    generate_address,
    generate_phone,
    generate_email,
    generate_pan,
    generate_aadhaar,
    generate_bank_account,
    generate_upi_id,
)


def test_pii_types_loaded_from_schema_not_redeclared():
    schema = json.loads(
        (ROOT / "schemas" / "base_instance.schema.json").read_text(encoding="utf-8")
    )
    assert PII_TYPES == tuple(schema["$defs"]["pii_type"]["enum"])


def test_generated_pii_rejects_unknown_type():
    with pytest.raises(ValueError):
        GeneratedPII(type="NOT_A_TYPE", base_pii_value="x")


def test_generated_pii_rejects_empty_value():
    with pytest.raises(ValueError):
        GeneratedPII(type="PAN", base_pii_value="")


@pytest.mark.parametrize("generator", ALL_GENERATORS, ids=lambda g: g.__name__)
def test_generator_does_not_accept_base_kind_or_base_id(generator):
    """No T03 generator may accept, and therefore cannot depend on or infer
    anything from, base_kind or base_id (validators/base_kind.py's frozen
    contract; guidelines.md §13.4)."""
    params = inspect.signature(generator).parameters
    assert "base_kind" not in params
    assert "base_id" not in params


@pytest.mark.parametrize("generator", ALL_GENERATORS, ids=lambda g: g.__name__)
def test_generator_only_accepts_rng(generator):
    """Every generator's sole parameter is the caller-owned random.Random
    instance -- a clear, uniform callable interface across all eight."""
    params = list(inspect.signature(generator).parameters)
    assert params == ["rng"]


@pytest.mark.parametrize("generator", ALL_GENERATORS, ids=lambda g: g.__name__)
def test_generator_is_deterministic_under_shared_seed(generator):
    first = generator(random.Random(42))
    second = generator(random.Random(42))
    assert first == second


@pytest.mark.parametrize("generator", ALL_GENERATORS, ids=lambda g: g.__name__)
def test_generator_returns_generated_pii(generator):
    result = generator(random.Random(1))
    assert isinstance(result, GeneratedPII)
    assert result.type in PII_TYPES
    assert isinstance(result.base_pii_value, str)
    assert result.base_pii_value
