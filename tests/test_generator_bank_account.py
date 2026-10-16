import random
import re

from conftest import pii_item_validator
from generators.pii.bank_account import generate_bank_account

_BANK_ACCOUNT_RE = re.compile(r"^[0-9]{12}$")


def test_value_is_exactly_twelve_digits():
    for seed in range(100):
        result = generate_bank_account(random.Random(seed))
        assert _BANK_ACCOUNT_RE.match(result.base_pii_value), result.base_pii_value


def test_type_is_bank_account():
    result = generate_bank_account(random.Random(1))
    assert result.type == "BANK_ACCOUNT"


def test_output_conforms_to_base_instance_pii_item_schema():
    result = generate_bank_account(random.Random(1))
    item = {
        "type": result.type,
        "base_pii_value": result.base_pii_value,
        "semantic_role": "PLACEHOLDER_ROLE",
    }
    pii_item_validator().validate(item)


def test_deterministic_sequence_over_many_seeds_is_reproducible():
    seq_a = [generate_bank_account(random.Random(s)).base_pii_value for s in range(20)]
    seq_b = [generate_bank_account(random.Random(s)).base_pii_value for s in range(20)]
    assert seq_a == seq_b
