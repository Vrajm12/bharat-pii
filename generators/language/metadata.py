"""T08: record metadata construction.

Every function here implements a frozen decision from annotation/guidelines.md
v0.11 exactly -- no invented enum values, no new fields. Kept separate from
realizations.py (carrier-text construction) and spans.py (offset
computation) per the required architectural separation.
"""

from __future__ import annotations

from .templates import NON_TRANSLITERABLE_TYPES, TRANSLITERABLE_TYPES

CONTEXT = "EXPLICIT"  # guidelines.md Section 4.17, resolves OQ-027

NONE_PERTURBATION = {
    "family": "NONE",
    "type": "NONE",
    "severity": 0,
    "target": "NONE",
}  # guidelines.md Section 4.16, resolves OQ-014

# --- pii_script (guidelines.md Section 4.15, resolves OQ-013) --------------

_NON_TRANSLITERABLE_PII_SCRIPT = {
    "PHONE": "NUMERIC",
    "AADHAAR": "NUMERIC",
    "BANK_ACCOUNT": "NUMERIC",
    "PAN": "LATIN",
    "EMAIL": "LATIN",
    "UPI_ID": "MIXED",
}


def pii_script(pii_type: str, language: str) -> str:
    if pii_type in _NON_TRANSLITERABLE_PII_SCRIPT:
        return _NON_TRANSLITERABLE_PII_SCRIPT[pii_type]
    if pii_type in TRANSLITERABLE_TYPES:
        return "DEVANAGARI" if language == "HI_DEVA_PII" else "LATIN"
    raise ValueError(f"unsupported PII type: {pii_type!r}")


# --- carrier_script ----------------------------------------------------

_DEVANAGARI_CARRIER_LANGUAGES = ("HI_LATIN_PII", "HI_DEVA_PII")


def carrier_script(language: str) -> str:
    return "DEVANAGARI" if language in _DEVANAGARI_CARRIER_LANGUAGES else "LATIN"


# --- variant_id (guidelines.md Section 4.16, resolves OQ-014) --------------


def variant_id(base_id: str, language: str) -> str:
    return f"{base_id}_{language}"


# --- hi_variant_collapsed (guidelines.md Section 4.3/8.1) ------------------


def is_non_transliterable(pii_type: str) -> bool:
    return pii_type in NON_TRANSLITERABLE_TYPES


# --- difficulty (guidelines.md Section 13.1 -- derived, never hand-set) ----


def difficulty(language: str) -> str:
    """EASY: C1 + clean + EN/IN_EN. Everything else T08 produces is
    MEDIUM (code-mixed or non-English carrier) -- none of T08's clean
    records are multi-PII+distractor (HARD) or perturbed (ADVERSARIAL)."""
    return "EASY" if language in ("EN", "IN_EN") else "MEDIUM"


# --- domain casing (record-level domain is UPPER_SNAKE_CASE, matching
# guidelines.md Section 17's own worked example, "ACCOUNT_VERIFICATION";
# base-instance-level scenario.domain is lower_snake_case) ------------------


def record_domain(base_scenario_domain: str) -> str:
    return base_scenario_domain.upper()
