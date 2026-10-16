import random
import re

from conftest import pii_item_validator
from generators.pii.email import _RESERVED_TLDS, generate_email

_EMAIL_RE = re.compile(r"^[a-z0-9]+@[a-z]+\.(test|invalid|example)$")


def test_value_matches_local_at_label_dot_reserved_tld():
    for seed in range(100):
        result = generate_email(random.Random(seed))
        assert _EMAIL_RE.match(result.base_pii_value), result.base_pii_value


def test_tld_is_always_one_of_the_three_reserved_tlds():
    assert _RESERVED_TLDS == ("test", "invalid", "example")
    for seed in range(100):
        result = generate_email(random.Random(seed))
        tld = result.base_pii_value.rsplit(".", 1)[-1]
        assert tld in _RESERVED_TLDS


def test_no_real_resolvable_tld_ever_used():
    banned = (".com", ".net", ".org", ".in", ".co.in")
    for seed in range(100):
        result = generate_email(random.Random(seed))
        assert not any(result.base_pii_value.endswith(b) for b in banned)


def test_type_is_email():
    result = generate_email(random.Random(4))
    assert result.type == "EMAIL"


def test_output_conforms_to_base_instance_pii_item_schema():
    result = generate_email(random.Random(4))
    item = {
        "type": result.type,
        "base_pii_value": result.base_pii_value,
        "semantic_role": "PLACEHOLDER_ROLE",
    }
    pii_item_validator().validate(item)


def test_deterministic_sequence_over_many_seeds_is_reproducible():
    seq_a = [generate_email(random.Random(s)).base_pii_value for s in range(20)]
    seq_b = [generate_email(random.Random(s)).base_pii_value for s in range(20)]
    assert seq_a == seq_b
