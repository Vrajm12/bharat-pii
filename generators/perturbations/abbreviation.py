"""T12: A4 INFORMAL_ABBREVIATION perturbation transform (guidelines.md Section 14.7.4)."""

from __future__ import annotations

A4_ABBREVIATION_MAP: dict[str, tuple[str, str]] = {
    "PERSON": ("My name is ", "name: "),
    "ADDRESS": ("My address is ", "addr: "),
    "PHONE": ("My phone number is ", "ph no: "),
    "EMAIL": ("Email me at ", "mail: "),
    "PAN": ("My PAN number is ", "pan no: "),
    "AADHAAR": ("My Aadhaar number is ", "aadhaar no: "),
    "UPI_ID": ("My UPI ID is ", "upi: "),
    "BANK_ACCOUNT": ("My bank account number is ", "acct no: "),
}


def realize_abbreviation(
    pii_type: str, canonical_text: str, base_pii_value: str
) -> tuple[str, str]:
    """A4 INFORMAL_ABBREVIATION (Severity 1, Target: LABEL).

    Replaces the exact carrier prefix in canonical_text.
    PII value remains byte-identical: realized_pii_value == base_pii_value.
    Returns (text, realized_pii_value).
    """
    if pii_type not in A4_ABBREVIATION_MAP:
        raise ValueError(f"unsupported PII type for abbreviation: {pii_type!r}")
    old_prefix, new_prefix = A4_ABBREVIATION_MAP[pii_type]
    if not canonical_text.startswith(old_prefix):
        raise ValueError(
            f"canonical_text {canonical_text!r} does not start with expected prefix {old_prefix!r}"
        )
    text = canonical_text.replace(old_prefix, new_prefix, 1)
    return text, base_pii_value
