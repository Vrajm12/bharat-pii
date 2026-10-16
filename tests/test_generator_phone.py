import random
import re

from conftest import pii_item_validator
from generators.pii.phone import generate_phone

_PHONE_RE = re.compile(r"^[6789][0-9]{9}$")


def test_value_is_ten_digits_starting_six_to_nine():
    for seed in range(100):
        result = generate_phone(random.Random(seed))
        assert _PHONE_RE.match(result.base_pii_value), result.base_pii_value


def test_value_has_no_intrinsic_formatting():
    """Formatting variants (+91, hyphens, spacing) are a later
    language-realization/perturbation concern, not a base-value concern."""
    result = generate_phone(random.Random(2))
    assert "+" not in result.base_pii_value
    assert "-" not in result.base_pii_value
    assert " " not in result.base_pii_value


def test_type_is_phone():
    result = generate_phone(random.Random(2))
    assert result.type == "PHONE"


def test_output_conforms_to_base_instance_pii_item_schema():
    result = generate_phone(random.Random(9))
    item = {
        "type": result.type,
        "base_pii_value": result.base_pii_value,
        "semantic_role": "PLACEHOLDER_ROLE",
    }
    pii_item_validator().validate(item)


def test_deterministic_sequence_over_many_seeds_is_reproducible():
    seq_a = [generate_phone(random.Random(s)).base_pii_value for s in range(20)]
    seq_b = [generate_phone(random.Random(s)).base_pii_value for s in range(20)]
    assert seq_a == seq_b
