import random
import re

from conftest import pii_item_validator
from generators.pii.address import generate_address

_PIN_RE = re.compile(r"\b([1-8][0-9]{5})\b")


def test_value_contains_all_expected_components():
    result = generate_address(random.Random(11))
    value = result.base_pii_value
    assert value.startswith("Flat ")
    assert value.count(",") == 3  # flat, building, road, "city PIN" -> 3 commas


def test_pin_code_is_six_digits_first_digit_one_to_eight():
    for seed in range(50):
        result = generate_address(random.Random(seed))
        match = _PIN_RE.search(result.base_pii_value)
        assert match is not None, result.base_pii_value


def test_type_is_address():
    result = generate_address(random.Random(11))
    assert result.type == "ADDRESS"


def test_output_conforms_to_base_instance_pii_item_schema():
    result = generate_address(random.Random(5))
    item = {
        "type": result.type,
        "base_pii_value": result.base_pii_value,
        "semantic_role": "PLACEHOLDER_ROLE",
    }
    pii_item_validator().validate(item)


def test_deterministic_sequence_over_many_seeds_is_reproducible():
    seq_a = [generate_address(random.Random(s)).base_pii_value for s in range(20)]
    seq_b = [generate_address(random.Random(s)).base_pii_value for s in range(20)]
    assert seq_a == seq_b
