"""T12: A2 PUNCTUATION perturbation transform (guidelines.md Section 14.7.2)."""

from __future__ import annotations


def apply_punctuation(pii_type: str, base_pii_value: str) -> str:
    """A2 PUNCTUATION (Severity 1, Target: VALUE).

    Inserts internal punctuation delimiters at fixed structural boundaries:
    - PAN: 5-4-1 hyphenation
    - AADHAAR / BANK_ACCOUNT: 4-4-4 hyphenation
    - PHONE: 5-5 hyphenation
    - PERSON: word boundary hyphenation
    - EMAIL: local-part hyphenation before numeric run
    - UPI_ID: 5-5 local phone VPA hyphenation
    - ADDRESS: slash-delimited segments
    """
    v = base_pii_value
    if pii_type == "PAN":
        return v[:5] + "-" + v[5:9] + "-" + v[9:]
    elif pii_type in ("AADHAAR", "BANK_ACCOUNT"):
        return v[:4] + "-" + v[4:8] + "-" + v[8:]
    elif pii_type == "PHONE":
        return v[:5] + "-" + v[5:]
    elif pii_type == "PERSON":
        return v.replace(" ", "-")
    elif pii_type == "EMAIL":
        local, domain = v.split("@")
        return local[:-4] + "-" + local[-4:] + "@" + domain
    elif pii_type == "UPI_ID":
        local, domain = v.split("@")
        return local[:5] + "-" + local[5:] + "@" + domain
    elif pii_type == "ADDRESS":
        return v.replace(", ", " / ")
    raise ValueError(f"unsupported PII type for punctuation: {pii_type!r}")


def realize_punctuation(
    pii_type: str, canonical_text: str, base_pii_value: str
) -> tuple[str, str]:
    """Return (text, realized_pii_value) for A2 PUNCTUATION."""
    realized_val = apply_punctuation(pii_type, base_pii_value)
    if base_pii_value not in canonical_text:
        raise ValueError(
            f"base_pii_value {base_pii_value!r} not found in canonical_text {canonical_text!r}"
        )
    text = canonical_text.replace(base_pii_value, realized_val, 1)
    return text, realized_val
