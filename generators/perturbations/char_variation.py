"""T12: A5 CHARACTER_VARIATION perturbation transform (guidelines.md Section 14.7.5)."""

from __future__ import annotations

OCR_HOMOGLYPH_MAP: dict[str, str] = {"0": "O", "1": "l", "5": "S", "8": "B"}


def apply_char_variation(pii_type: str, base_pii_value: str) -> str:
    """A5 CHARACTER_VARIATION (Severity 1, Target: VALUE).

    - PAN, PERSON, ADDRESS: base_pii_value.lower()
    - EMAIL, UPI_ID: base_pii_value.upper()
    - PHONE, AADHAAR, BANK_ACCOUNT (M2 Single-Character OCR Substitution):
      Scan left-to-right. Replace ONLY the first occurrence of a digit matching
      {'0': 'O', '1': 'l', '5': 'S', '8': 'B'} with its visual letter.
      Leave all remaining digits unchanged.
    """
    v = base_pii_value
    if pii_type in ("PAN", "PERSON", "ADDRESS"):
        return v.lower()
    elif pii_type in ("EMAIL", "UPI_ID"):
        return v.upper()
    elif pii_type in ("PHONE", "AADHAAR", "BANK_ACCOUNT"):
        for i, c in enumerate(v):
            if c in OCR_HOMOGLYPH_MAP:
                return v[:i] + OCR_HOMOGLYPH_MAP[c] + v[i + 1 :]
        raise ValueError(f"no OCR homoglyph match found in numeric PII {v!r}")
    raise ValueError(f"unsupported PII type for character variation: {pii_type!r}")


def realize_char_variation(
    pii_type: str, canonical_text: str, base_pii_value: str
) -> tuple[str, str]:
    """Return (text, realized_pii_value) for A5 CHARACTER_VARIATION."""
    realized_val = apply_char_variation(pii_type, base_pii_value)
    if base_pii_value not in canonical_text:
        raise ValueError(
            f"base_pii_value {base_pii_value!r} not found in canonical_text {canonical_text!r}"
        )
    text = canonical_text.replace(base_pii_value, realized_val, 1)
    return text, realized_val
