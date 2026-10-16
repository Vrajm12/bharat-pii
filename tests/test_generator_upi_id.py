import random
import re

from conftest import pii_item_validator
from generators.pii.upi_id import generate_upi_id

_UPI_RE = re.compile(r"^[6789][0-9]{9}@mail\.test$")


def test_value_matches_fixed_grammar():
    """<10-digit-synthetic-phone>@mail.test -- the one fixed grammar chosen
    for OQ-006 (Grammar 3). No other local-part or domain variant exists."""
    for seed in range(100):
        result = generate_upi_id(random.Random(seed))
        assert _UPI_RE.match(result.base_pii_value), result.base_pii_value


def test_domain_is_always_mail_test():
    for seed in range(100):
        result = generate_upi_id(random.Random(seed))
        assert result.base_pii_value.endswith("@mail.test")


def test_no_real_psp_handle_ever_used():
    """Rule 2: no real PSP handles/domains may be used."""
    real_psp_handles = (
        "@okaxis", "@ybl", "@paytm", "@oksbi", "@ibl", "@axl", "@upi",
        "@okhdfcbank", "@axisbank",
    )
    for seed in range(100):
        result = generate_upi_id(random.Random(seed))
        assert not any(result.base_pii_value.endswith(h) for h in real_psp_handles)


def test_local_part_is_ten_digits_starting_six_to_nine():
    for seed in range(100):
        result = generate_upi_id(random.Random(seed))
        local = result.base_pii_value.split("@", 1)[0]
        assert len(local) == 10
        assert local[0] in "6789"
        assert local.isdigit()


def test_shape_collides_with_email_grammar():
    """PROJECT_SPEC.md §7: UPI_ID must shape-collide with EMAIL. Confirm the
    UPI_ID value would also satisfy EMAIL's own local@label.tld regex."""
    email_shape_re = re.compile(r"^[a-z0-9]+@[a-z]+\.(test|invalid|example)$")
    result = generate_upi_id(random.Random(3))
    assert email_shape_re.match(result.base_pii_value)


def test_type_is_upi_id():
    result = generate_upi_id(random.Random(1))
    assert result.type == "UPI_ID"


def test_output_conforms_to_base_instance_pii_item_schema():
    result = generate_upi_id(random.Random(1))
    item = {
        "type": result.type,
        "base_pii_value": result.base_pii_value,
        "semantic_role": "PLACEHOLDER_ROLE",
    }
    pii_item_validator().validate(item)


def test_deterministic_sequence_over_many_seeds_is_reproducible():
    seq_a = [generate_upi_id(random.Random(s)).base_pii_value for s in range(20)]
    seq_b = [generate_upi_id(random.Random(s)).base_pii_value for s in range(20)]
    assert seq_a == seq_b
