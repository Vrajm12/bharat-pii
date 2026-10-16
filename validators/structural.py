"""T05: structural (PROJECT_SPEC.md Section 15, Layer 1) validation.

"Value conforms to its synthetic format schema." Nothing else. This module
validates `base_pii_value` on an arbitrary base instance -- it never calls
any `generators/pii/*.py` generator, so a hand-crafted or externally-sourced
record is checked exactly the same way as generator output.

Explicitly out of scope (later tasks, other modules):
  base_kind      -> validators/base_kind.py (frozen, unrelated to this module)
  semantic_role  -> not a value-format concern
  scenario       -> not a value-format concern
  canonical_text -> not inspected here at all
  span positions -> Layer 2 (T09)
  semantic role  -> Layer 3 (T10)
  language/script -> Layer 4 (T10)
  duplicates     -> Layer 5
  human review   -> Layer 6
No real-world issuance/registry/checksum validation is performed for any
type -- this benchmark never claims to validate whether an identifier was
actually issued (guidelines.md Section 11.3 / Section 11.4).

Per-type rules, each traceable to a frozen guidelines.md decision:

  PERSON        no format -- free text (guidelines.md Section 5; no value-format
                rule exists anywhere). Only non-emptiness is checked, which
                schemas/base_instance.schema.json already enforces
                (minLength: 1) -- this module adds nothing beyond that.
  ADDRESS       no format -- free text (guidelines.md Section 7; same as PERSON).
  PHONE         ^[6789][0-9]{9}$ -- guidelines.md Section 8.1 (v0.7, OQ-008).
                Base representation only; +91/spacing/hyphens are a realized-
                span concern (Section 8), not checked here.
  EMAIL         exactly one '@', non-empty local part, domain ending in an
                exact-lowercase .test/.invalid/.example -- guidelines.md
                Section 9.1 (v0.7, OQ-009, OQ-011). Not full RFC 5321/5322
                validation; no invented local-part character restrictions.
  PAN           ^[A-Z]{5}[0-9]{4}[A-Z]$ -- guidelines.md Section 11.5 (v0.7,
                OQ-010). Uppercase-only; lowercase is structurally invalid.
                No checksum/issuance/category-code validation.
  AADHAAR       ^[0-9]{12}$ -- guidelines.md Section 11.4 (v0.4, OQ-004).
                No leading-digit exclusion, no checksum.
  UPI_ID        ^[6789][0-9]{9}@mail\\.test$ -- guidelines.md Section 10.3/10.4
                (v0.5/v0.7, OQ-006/OQ-011). One fixed grammar, no variants.
                A value failing this (e.g. "...@paytm") is invalid because it
                does not match the frozen grammar -- never described as
                invalid for resembling a real PSP handle (OQ-011).
  BANK_ACCOUNT  ^[0-9]{12}$ -- guidelines.md Section 11.4 (v0.4, OQ-005).
                Not claimed as the universal real-world length/format.
"""

from __future__ import annotations

import re

_PHONE_RE = re.compile(r"^[6789][0-9]{9}$")
_EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.(test|invalid|example)$")
_PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
_AADHAAR_RE = re.compile(r"^[0-9]{12}$")
_UPI_ID_RE = re.compile(r"^[6789][0-9]{9}@mail\.test$")
_BANK_ACCOUNT_RE = re.compile(r"^[0-9]{12}$")

# Types with no value-format rule -- only non-emptiness applies, and that is
# already schema-enforced (schemas/base_instance.schema.json, minLength: 1).
_FREE_TEXT_TYPES = frozenset({"PERSON", "ADDRESS"})

_REGEX_RULES = {
    "PHONE": _PHONE_RE,
    "PAN": _PAN_RE,
    "AADHAAR": _AADHAAR_RE,
    "UPI_ID": _UPI_ID_RE,
    "BANK_ACCOUNT": _BANK_ACCOUNT_RE,
}

KNOWN_PII_TYPES = frozenset(_FREE_TEXT_TYPES | set(_REGEX_RULES) | {"EMAIL"})


class StructuralValidationError(ValueError):
    """Raised when a PII value fails its type's frozen structural rule, or
    when the type itself is not one of the 8 pilot categories."""


def check_structural_value(pii_type: str, value: str) -> None:
    """Raise StructuralValidationError if `value` does not conform to
    `pii_type`'s frozen structural rule. Does not call any generator."""
    if pii_type not in KNOWN_PII_TYPES:
        raise StructuralValidationError(
            f"unsupported PII type: {pii_type!r} (expected one of "
            f"{sorted(KNOWN_PII_TYPES)})"
        )

    if not isinstance(value, str) or not value:
        raise StructuralValidationError(
            f"{pii_type}: value must be a non-empty string, got {value!r}"
        )

    if pii_type in _FREE_TEXT_TYPES:
        return  # non-emptiness (already checked above) is the entire rule

    if pii_type == "EMAIL":
        if not _EMAIL_RE.match(value):
            raise StructuralValidationError(
                f"EMAIL: {value!r} does not match local@domain.<reserved TLD> "
                f"(guidelines.md Section 9.1)"
            )
        return

    pattern = _REGEX_RULES[pii_type]
    if not pattern.match(value):
        raise StructuralValidationError(
            f"{pii_type}: {value!r} does not match the frozen structural "
            f"rule {pattern.pattern!r}"
        )


def validate_base_instance_structural(base_instance: dict) -> None:
    """Run check_structural_value over every pii[] entry of a base instance.
    Validates the base instance as given -- does not call any generator."""
    for entry in base_instance["pii"]:
        check_structural_value(entry["type"], entry["base_pii_value"])
