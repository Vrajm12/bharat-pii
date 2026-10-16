import random
import re

from conftest import pii_item_validator
from generators.pii.pan import generate_pan

_PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


def test_value_matches_pan_shape():
    """5 letters + 4 digits + 1 letter -- guidelines.md's own repeated
    worked example ("ABCDE1234F") establishes this shape."""
    for seed in range(100):
        result = generate_pan(random.Random(seed))
        assert _PAN_RE.match(result.base_pii_value), result.base_pii_value


def test_value_is_ten_characters():
    result = generate_pan(random.Random(6))
    assert len(result.base_pii_value) == 10


def test_type_is_pan():
    result = generate_pan(random.Random(6))
    assert result.type == "PAN"


def test_output_conforms_to_base_instance_pii_item_schema():
    result = generate_pan(random.Random(6))
    item = {
        "type": result.type,
        "base_pii_value": result.base_pii_value,
        "semantic_role": "PLACEHOLDER_ROLE",
    }
    pii_item_validator().validate(item)


def test_deterministic_sequence_over_many_seeds_is_reproducible():
    seq_a = [generate_pan(random.Random(s)).base_pii_value for s in range(20)]
    seq_b = [generate_pan(random.Random(s)).base_pii_value for s in range(20)]
    assert seq_a == seq_b
