import random

from conftest import pii_item_validator
from generators.pii.person import _FAMILY_NAMES, _GIVEN_NAMES, generate_person


def test_value_is_two_tokens_given_and_family():
    result = generate_person(random.Random(7))
    tokens = result.base_pii_value.split(" ")
    assert len(tokens) == 2
    given, family = tokens
    assert given in _GIVEN_NAMES
    assert family in _FAMILY_NAMES


def test_type_is_person():
    result = generate_person(random.Random(7))
    assert result.type == "PERSON"


def test_no_honorifics_or_titles_present():
    """guidelines.md §5.2 excludes honorifics from the PERSON span; this
    generator must never emit one in the first place."""
    excluded = {
        "Mr", "Mrs", "Ms", "Dr", "Shri", "Smt", "Sir", "Madam", "ji",
        "bhai", "bhaiya", "didi", "sahab", "saab", "bhaisaab", "jee",
    }
    for seed in range(50):
        result = generate_person(random.Random(seed))
        tokens = set(result.base_pii_value.split(" "))
        assert tokens.isdisjoint(excluded)


def test_output_conforms_to_base_instance_pii_item_schema():
    result = generate_person(random.Random(3))
    item = {
        "type": result.type,
        "base_pii_value": result.base_pii_value,
        "semantic_role": "PLACEHOLDER_ROLE",
    }
    pii_item_validator().validate(item)


def test_deterministic_sequence_over_many_seeds_is_reproducible():
    seq_a = [generate_person(random.Random(s)).base_pii_value for s in range(20)]
    seq_b = [generate_person(random.Random(s)).base_pii_value for s in range(20)]
    assert seq_a == seq_b
