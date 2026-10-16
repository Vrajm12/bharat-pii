"""T12: A3 LABEL_OBFUSCATION perturbation transform (guidelines.md Section 14.7.3)."""

from __future__ import annotations

A3_LABEL_MAP: dict[str, tuple[str, str]] = {
    "PERSON": ("My name is ", "My N.A.M.E: "),
    "ADDRESS": ("My address is ", "My A.D.D.R.E.S.S: "),
    "PHONE": ("My phone number is ", "My P.H.O.N.E. No.: "),
    "EMAIL": ("Email me at ", "E.M.A.I.L: "),
    "PAN": ("My PAN number is ", "My P.A.N. No.: "),
    "AADHAAR": ("My Aadhaar number is ", "My A.A.D.H.A.A.R. No.: "),
    "UPI_ID": ("My UPI ID is ", "My U.P.I. I.D.: "),
    "BANK_ACCOUNT": ("My bank account number is ", "My B.A.N.K. A/C No.: "),
}


def realize_label_obfuscation(
    pii_type: str, canonical_text: str, base_pii_value: str
) -> tuple[str, str]:
    """A3 LABEL_OBFUSCATION (Severity 1, Target: LABEL).

    Replaces the exact carrier prefix in canonical_text.
    PII value remains byte-identical: realized_pii_value == base_pii_value.
    Returns (text, realized_pii_value).
    """
    if pii_type not in A3_LABEL_MAP:
        raise ValueError(f"unsupported PII type for label obfuscation: {pii_type!r}")
    old_prefix, new_prefix = A3_LABEL_MAP[pii_type]
    if not canonical_text.startswith(old_prefix):
        raise ValueError(
            f"canonical_text {canonical_text!r} does not start with expected prefix {old_prefix!r}"
        )
    text = canonical_text.replace(old_prefix, new_prefix, 1)
    return text, base_pii_value
