import random
import re

from conftest import pii_item_validator
from generators.pii.aadhaar import generate_aadhaar

_AADHAAR_RE = re.compile(r"^[0-9]{12}$")


def test_value_is_exactly_twelve_digits():
    for seed in range(100):
        result = generate_aadhaar(random.Random(seed))
        assert _AADHAAR_RE.match(result.base_pii_value), result.base_pii_value


def test_leading_zero_is_permitted():
    """BENCHMARK_SYNTHETIC per OQ-004: no leading-digit exclusion is applied
    -- unlike a real Aadhaar, a leading 0 or 1 is a reachable output here."""
    seen_leading_digits = {
        generate_aadhaar(random.Random(seed)).base_pii_value[0] for seed in range(300)
    }
    assert seen_leading_digits & {"0", "1"}, (
        "expected at least one generated value starting with 0 or 1 across "
        "300 seeds if leading digits are truly unconstrained"
    )


def test_type_is_aadhaar():
    result = generate_aadhaar(random.Random(1))
    assert result.type == "AADHAAR"


def test_output_conforms_to_base_instance_pii_item_schema():
    result = generate_aadhaar(random.Random(1))
    item = {
        "type": result.type,
        "base_pii_value": result.base_pii_value,
        "semantic_role": "PLACEHOLDER_ROLE",
    }
    pii_item_validator().validate(item)


def test_deterministic_sequence_over_many_seeds_is_reproducible():
    seq_a = [generate_aadhaar(random.Random(s)).base_pii_value for s in range(20)]
    seq_b = [generate_aadhaar(random.Random(s)).base_pii_value for s in range(20)]
    assert seq_a == seq_b
