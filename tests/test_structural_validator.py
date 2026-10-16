import json
from pathlib import Path
from unittest.mock import patch

import pytest

from validators.structural import (
    StructuralValidationError,
    check_structural_value,
    validate_base_instance_structural,
)

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "data" / "raw" / "base_instances.jsonl"

# ---------------------------------------------------------------------------
# 1. one valid example per type
# ---------------------------------------------------------------------------

VALID_EXAMPLES = {
    "PERSON": "Rahul Sharma",
    "ADDRESS": "Flat 302, ABC Apartments, Baner Road, Pune 411045",
    "PHONE": "9876543210",
    "EMAIL": "rahul123@example.test",
    "PAN": "ABCDE1234F",
    "AADHAAR": "083172788957",
    "UPI_ID": "9876543210@mail.test",
    "BANK_ACCOUNT": "324210249947",
}


@pytest.mark.parametrize("pii_type,value", VALID_EXAMPLES.items())
def test_valid_example_passes_for_every_type(pii_type, value):
    check_structural_value(pii_type, value)  # must not raise


# ---------------------------------------------------------------------------
# 2. >= 2 invalid examples per type with a meaningful structural rule
#    (PERSON/ADDRESS excluded here -- see the dedicated test below, #3)
# ---------------------------------------------------------------------------

INVALID_EXAMPLES = {
    "PHONE": ["12345", "5876543210", "98765432100", "987654321a"],
    "EMAIL": [
        "rahul123@example.com",
        "rahul123mail.test",
        "@mail.test",
        "rahul123@.test",
        "a@b@c.test",
    ],
    "PAN": ["ABCD1234F", "ABCDE12345", "abcde1234f", "ABCDE1234"],
    "AADHAAR": ["12345678901", "1234567890123", "12345678901A"],
    "UPI_ID": [
        "9876543210@paytm",
        "587654321@mail.test",
        "98765432100@mail.test",
        "9876543210@mail.example",
        "9876543210@MAIL.TEST",
    ],
    "BANK_ACCOUNT": ["12345678901", "1234567890123", "12345678901A"],
}


@pytest.mark.parametrize(
    "pii_type,value",
    [(t, v) for t, values in INVALID_EXAMPLES.items() for v in values],
)
def test_invalid_examples_are_rejected(pii_type, value):
    assert len(INVALID_EXAMPLES[pii_type]) >= 2
    with pytest.raises(StructuralValidationError):
        check_structural_value(pii_type, value)


# ---------------------------------------------------------------------------
# 3. PERSON/ADDRESS accept arbitrary non-empty synthetic text
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "pii_type,value",
    [
        ("PERSON", "Rahul Sharma"),
        ("PERSON", "R Sharma"),
        ("PERSON", "S. Raghavan"),
        ("PERSON", "A completely different-looking synthetic name, comma included"),
        ("ADDRESS", "Flat 302, ABC Apartments, Baner Road, Pune 411045"),
        ("ADDRESS", "near the old bus stand, opposite City Hospital, Nagpur"),
        ("ADDRESS", "1 Main St"),
    ],
)
def test_person_and_address_accept_arbitrary_nonempty_text(pii_type, value):
    check_structural_value(pii_type, value)  # must not raise


@pytest.mark.parametrize("pii_type", ["PERSON", "ADDRESS"])
def test_person_and_address_reject_empty_string(pii_type):
    with pytest.raises(StructuralValidationError):
        check_structural_value(pii_type, "")


# ---------------------------------------------------------------------------
# 4. AADHAAR leading-zero acceptance (guidelines.md Section 11.4, OQ-004)
# ---------------------------------------------------------------------------

def test_aadhaar_leading_zero_is_accepted():
    check_structural_value("AADHAAR", "012345678901")  # must not raise


def test_aadhaar_leading_one_is_accepted():
    check_structural_value("AADHAAR", "123456789012")  # must not raise


# ---------------------------------------------------------------------------
# 5. PAN lowercase rejection (guidelines.md Section 11.5, OQ-010)
# ---------------------------------------------------------------------------

def test_pan_lowercase_is_rejected():
    with pytest.raises(StructuralValidationError):
        check_structural_value("PAN", "abcde1234f")


def test_pan_mixed_case_is_rejected():
    with pytest.raises(StructuralValidationError):
        check_structural_value("PAN", "AbCdE1234F")


def test_pan_uppercase_is_accepted():
    check_structural_value("PAN", "ABCDE1234F")  # must not raise


# ---------------------------------------------------------------------------
# 6. EMAIL reserved-TLD enforcement (guidelines.md Section 9.1, OQ-009/OQ-011)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tld", ["test", "invalid", "example"])
def test_email_accepts_each_reserved_tld(tld):
    check_structural_value("EMAIL", f"rahul123@example.{tld}")  # must not raise


def test_email_rejects_non_reserved_tld():
    with pytest.raises(StructuralValidationError):
        check_structural_value("EMAIL", "rahul123@example.com")


def test_email_rejects_uppercase_tld():
    with pytest.raises(StructuralValidationError):
        check_structural_value("EMAIL", "rahul123@example.TEST")


# ---------------------------------------------------------------------------
# 7. UPI_ID exact @mail.test enforcement (guidelines.md Section 10.3/10.4)
# ---------------------------------------------------------------------------

def test_upi_id_accepts_the_one_frozen_grammar():
    check_structural_value("UPI_ID", "9876543210@mail.test")  # must not raise


def test_upi_id_rejects_real_shaped_psp_handle():
    with pytest.raises(StructuralValidationError):
        check_structural_value("UPI_ID", "9876543210@paytm")


def test_upi_id_rejects_wrong_domain():
    with pytest.raises(StructuralValidationError):
        check_structural_value("UPI_ID", "9876543210@mail.example")


def test_upi_id_structural_failure_reason_does_not_mention_psp():
    """OQ-011: the validator must never describe real-PSP avoidance as the
    structural *reasoning* for failure -- only grammar non-conformance. The
    invalid value itself may still be echoed back (e.g. "'...@paytm' does
    not match ...") for debuggability -- that's data, not a claim about PSPs."""
    with pytest.raises(StructuralValidationError) as excinfo:
        check_structural_value("UPI_ID", "9876543210@paytm")
    message = str(excinfo.value).lower()
    assert "psp" not in message
    assert "resembl" not in message
    assert "real-world" not in message
    assert "match" in message or "grammar" in message


# ---------------------------------------------------------------------------
# 8. PHONE leading-digit / length rejection (guidelines.md Section 8.1, OQ-008)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("leading_digit", ["0", "1", "2", "3", "4", "5"])
def test_phone_rejects_disallowed_leading_digit(leading_digit):
    with pytest.raises(StructuralValidationError):
        check_structural_value("PHONE", leading_digit + "876543210")


@pytest.mark.parametrize("leading_digit", ["6", "7", "8", "9"])
def test_phone_accepts_allowed_leading_digit(leading_digit):
    check_structural_value("PHONE", leading_digit + "876543210")  # must not raise


def test_phone_rejects_wrong_length():
    with pytest.raises(StructuralValidationError):
        check_structural_value("PHONE", "987654321")  # 9 digits


def test_phone_rejects_formatted_variant():
    """+91 / spaces / hyphens are a realized-span concern (guidelines.md
    Section 8), not part of the frozen base representation (Section 8.1)."""
    for formatted in ("+91 9876543210", "+91-9876543210", "98765 43210"):
        with pytest.raises(StructuralValidationError):
            check_structural_value("PHONE", formatted)


# ---------------------------------------------------------------------------
# 9. BANK_ACCOUNT exact 12-digit rule (guidelines.md Section 11.4, OQ-005)
# ---------------------------------------------------------------------------

def test_bank_account_accepts_twelve_digits():
    check_structural_value("BANK_ACCOUNT", "123456789012")  # must not raise


def test_bank_account_rejects_eleven_digits():
    with pytest.raises(StructuralValidationError):
        check_structural_value("BANK_ACCOUNT", "12345678901")


def test_bank_account_rejects_thirteen_digits():
    with pytest.raises(StructuralValidationError):
        check_structural_value("BANK_ACCOUNT", "1234567890123")


# ---------------------------------------------------------------------------
# 10. proof the validator does not call any generator
# ---------------------------------------------------------------------------

def test_structural_module_does_not_import_generators():
    """Static check: the module source never imports from the generators
    package at all."""
    source = Path(ROOT / "validators" / "structural.py").read_text(encoding="utf-8")
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("import generators") or stripped.startswith(
            "from generators"
        ):
            pytest.fail(f"validators/structural.py imports a generator: {stripped!r}")


def test_validator_never_calls_any_generator_at_runtime():
    """Behavioral proof: patch every one of the 8 frozen generators to raise
    if called, then exercise the validator (valid and invalid inputs, every
    type) and assert none of the mocks were ever invoked."""
    targets = [
        "generators.pii.person.generate_person",
        "generators.pii.address.generate_address",
        "generators.pii.phone.generate_phone",
        "generators.pii.email.generate_email",
        "generators.pii.pan.generate_pan",
        "generators.pii.aadhaar.generate_aadhaar",
        "generators.pii.upi_id.generate_upi_id",
        "generators.pii.bank_account.generate_bank_account",
    ]
    patchers = [patch(t, side_effect=AssertionError(f"{t} was called")) for t in targets]
    mocks = [p.start() for p in patchers]
    try:
        for pii_type, value in VALID_EXAMPLES.items():
            check_structural_value(pii_type, value)
        for pii_type, values in INVALID_EXAMPLES.items():
            for value in values:
                with pytest.raises(StructuralValidationError):
                    check_structural_value(pii_type, value)
    finally:
        for p in patchers:
            p.stop()
    for mock in mocks:
        mock.assert_not_called()


# ---------------------------------------------------------------------------
# 11. malformed / unsupported PII type handling
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "bad_type", ["NOT_A_TYPE", "person", "", "LOCATION", "PASSPORT", None]
)
def test_unsupported_pii_type_is_rejected(bad_type):
    with pytest.raises(StructuralValidationError):
        check_structural_value(bad_type, "some value")


def test_non_string_value_is_rejected():
    with pytest.raises(StructuralValidationError):
        check_structural_value("PAN", None)
    with pytest.raises(StructuralValidationError):
        check_structural_value("PAN", 12345)


# ---------------------------------------------------------------------------
# 12. integration test against the 100 frozen T04 bases
# ---------------------------------------------------------------------------

def test_all_100_frozen_base_instances_pass_structural_validation():
    records = [
        json.loads(line) for line in DATASET_PATH.read_text(encoding="utf-8").splitlines()
    ]
    assert len(records) == 100
    for record in records:
        validate_base_instance_structural(record)  # must not raise for any of the 100


def test_validate_base_instance_structural_rejects_a_corrupted_copy():
    records = [
        json.loads(line) for line in DATASET_PATH.read_text(encoding="utf-8").splitlines()
    ]
    pan_record = next(r for r in records if r["base_id"].startswith("PAN_"))
    corrupted = json.loads(json.dumps(pan_record))  # deep copy
    corrupted["pii"][0]["base_pii_value"] = corrupted["pii"][0]["base_pii_value"].lower()
    with pytest.raises(StructuralValidationError):
        validate_base_instance_structural(corrupted)
