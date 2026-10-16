"""T07 tests. Coverage tests import the frozen T03 vocabularies directly
from generators/pii/person.py and generators/pii/address.py rather than
retyping them here, per instruction."""

import random

import pytest

from generators.pii.address import (
    _BUILDING_NAMES,
    _CITIES,
    _ROAD_NAMES,
    generate_address,
)
from generators.pii.person import _FAMILY_NAMES, _GIVEN_NAMES, generate_person
from generators.translit.table import (
    TABLE,
    TransliterationError,
    transliterate_token,
    transliterate_value,
)

# ---------------------------------------------------------------------------
# The one explicitly required test (guidelines.md Section 4.6 / PROJECT_SPEC.md
# Section 28)
# ---------------------------------------------------------------------------

def test_len_rahul_deva_equals_5():
    assert len(transliterate_value("Rahul")) == 5


# ---------------------------------------------------------------------------
# Complete vocabulary coverage -- mechanically derived from the frozen T03
# generators, never retyped
# ---------------------------------------------------------------------------

def _address_lexical_tokens():
    """Every lexical word reachable from generators/pii/address.py's frozen
    vocabulary, split from its actual tuples. "Flat" is the one literal word
    inline in the generator's f-string (not stored in a data structure), so
    it can't be derived mechanically -- it's the sole hardcoded addition."""
    tokens = {"Flat"}
    for phrase in (*_BUILDING_NAMES, *_ROAD_NAMES):
        tokens.update(phrase.split())
    tokens.update(_CITIES)
    return tokens


@pytest.mark.parametrize("token", sorted(_GIVEN_NAMES))
def test_every_frozen_given_name_has_a_table_entry(token):
    assert token in TABLE, f"{token!r} (PERSON given name) missing from TABLE"


@pytest.mark.parametrize("token", sorted(_FAMILY_NAMES))
def test_every_frozen_family_name_has_a_table_entry(token):
    assert token in TABLE, f"{token!r} (PERSON family name) missing from TABLE"


@pytest.mark.parametrize("token", sorted(_address_lexical_tokens()))
def test_every_frozen_address_lexical_token_has_a_table_entry(token):
    assert token in TABLE, f"{token!r} (ADDRESS lexical token) missing from TABLE"


def test_table_has_no_extra_person_entries_beyond_the_frozen_vocabulary():
    person_keys = set(_GIVEN_NAMES) | set(_FAMILY_NAMES)
    address_keys = _address_lexical_tokens()
    assert set(TABLE) == person_keys | address_keys, (
        "TABLE contains keys outside the frozen T03 PERSON/ADDRESS vocabularies, "
        "or is missing some -- table and generators have drifted out of sync"
    )


def test_table_size_matches_expected_vocabulary_count():
    person_count = len(set(_GIVEN_NAMES) | set(_FAMILY_NAMES))
    address_count = len(_address_lexical_tokens())
    assert len(TABLE) == person_count + address_count == 79


# ---------------------------------------------------------------------------
# Exact expected mappings
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "latin,deva",
    [
        ("Rahul", "राहुल"),
        ("Sharma", "शर्मा"),
        ("Pune", "पुणे"),
        ("Mumbai", "मुंबई"),
        ("Flat", "फ्लैट"),
        ("Road", "रोड"),
        ("ABC", "एबीसी"),  # OQ-022: benchmark-specific convention
        ("MG", "एमजी"),  # OQ-022: benchmark-specific convention
    ],
)
def test_exact_expected_mapping(latin, deva):
    assert transliterate_token(latin) == deva


# ---------------------------------------------------------------------------
# Lookup-miss rejection (fail closed, guidelines.md Section 4.9 / OQ-018)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "token", ["Nonexistent", "Zzzznotaname", "xyz", "Bangalore", "Delhi"]
)
def test_lookup_miss_raises_and_never_guesses(token):
    assert token not in TABLE  # sanity: these are genuinely absent
    with pytest.raises(TransliterationError):
        transliterate_token(token)


def test_lookup_miss_error_message_names_the_token():
    with pytest.raises(TransliterationError, match="Nonexistent"):
        transliterate_token("Nonexistent")


# ---------------------------------------------------------------------------
# Numeric preservation (Section 4.8 / OQ-017: numerals stay ASCII, unconverted)
# ---------------------------------------------------------------------------

def test_house_number_and_pin_pass_through_unchanged():
    value = "Flat 302, Silver Oak Heights, Baner Road, Bengaluru 754235"
    result = transliterate_value(value)
    assert "302" in result
    assert "754235" in result


@pytest.mark.parametrize("digits", ["0", "302", "754235", "9999999999"])
def test_bare_digit_run_passes_through_unchanged(digits):
    assert transliterate_value(digits) == digits


# ---------------------------------------------------------------------------
# Punctuation / spacing preservation
# ---------------------------------------------------------------------------

def test_comma_and_spacing_preserved_exactly_in_address():
    value = "Flat 1, ABC Apartments, MG Road, Pune 411001"
    result = transliterate_value(value)
    # every comma-space separator from the input survives untouched
    assert result.count(", ") == value.count(", ")
    # only the lexical/numeric content changed; separators are identical
    assert result.split(", ")[0].startswith("फ्लैट")


def test_person_value_join_space_preserved():
    result = transliterate_value("Rahul Sharma")
    assert result == "राहुल शर्मा"
    assert " " in result


# ---------------------------------------------------------------------------
# Deterministic repeatability
# ---------------------------------------------------------------------------

def test_transliterate_value_is_deterministic_across_repeated_calls():
    value = "Flat 302, Silver Oak Heights, Baner Road, Bengaluru 754235"
    assert transliterate_value(value) == transliterate_value(value)


def test_transliterate_token_is_deterministic_across_repeated_calls():
    for _ in range(50):
        assert transliterate_token("Rahul") == "राहुल"


def test_full_generator_output_transliterates_deterministically_and_identically():
    """Every value the frozen generators can actually produce transliterates
    identically on repeat calls, over many seeds."""
    for seed in range(50):
        rng = random.Random(seed)
        person_value = generate_person(rng).base_pii_value
        first = transliterate_value(person_value)
        second = transliterate_value(person_value)
        assert first == second

    for seed in range(50):
        rng = random.Random(seed)
        address_value = generate_address(rng).base_pii_value
        first = transliterate_value(address_value)
        second = transliterate_value(address_value)
        assert first == second


def test_full_generator_output_never_hits_a_lookup_miss():
    """Every value the frozen generators can actually produce transliterates
    successfully -- the table is complete for the reachable vocabulary."""
    for seed in range(200):
        rng = random.Random(seed)
        transliterate_value(generate_person(rng).base_pii_value)  # must not raise
    for seed in range(200):
        rng = random.Random(seed)
        transliterate_value(generate_address(rng).base_pii_value)  # must not raise
