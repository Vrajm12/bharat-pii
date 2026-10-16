"""T12: A1 SPACING perturbation transform (guidelines.md Section 14.7.1)."""

from __future__ import annotations


def apply_spacing(base_pii_value: str) -> str:
    """A1 SPACING (Severity 1, Target: VALUE).

    - Single-token values: " ".join(c for c in base_pii_value)
    - Multi-word values (PERSON, ADDRESS):
      "  ".join(" ".join(c for c in token) for token in base_pii_value.split(" "))
      (Single space intra-word, double space inter-word).
    """
    if " " in base_pii_value:
        return "  ".join(" ".join(t) for t in base_pii_value.split(" "))
    return " ".join(base_pii_value)


def realize_spacing(canonical_text: str, base_pii_value: str) -> tuple[str, str]:
    """Return (text, realized_pii_value) for A1 SPACING."""
    realized_val = apply_spacing(base_pii_value)
    if base_pii_value not in canonical_text:
        raise ValueError(
            f"base_pii_value {base_pii_value!r} not found in canonical_text {canonical_text!r}"
        )
    text = canonical_text.replace(base_pii_value, realized_val, 1)
    return text, realized_val
