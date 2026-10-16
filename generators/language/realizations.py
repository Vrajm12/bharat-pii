"""T08: per-condition carrier-text realization functions.

Pure functions: given a base's canonical text / PII value / PII type and a
small deterministic index (used only to cycle through frozen inventories,
never as randomness), return the realized (text, realized_pii_value) pair
for one language condition. No LLM, no external service, no randomness.

Determinism note: `index` is always the base's 0-based position in the
fixed CATEGORY_ORDER-then-file-order sequence (generators/base_instances.py)
-- the same ordering principle T04 already uses for domain assignment.
"""

from __future__ import annotations

from . import templates
from .spans import SpanResolutionError, find_occurrence


def realize_en(canonical_text: str, base_pii_value: str):
    """EN: text == canonical_text byte-for-byte. No rewriting."""
    return canonical_text, base_pii_value


def realize_in_en(canonical_text: str, base_pii_value: str, index: int):
    """IN_EN: canonical_text wrapped with one frozen marker (guidelines.md
    Section 4.12), cycled deterministically by base index."""
    _, wrap_fn = templates.IN_EN_MARKERS[index % len(templates.IN_EN_MARKERS)]
    return wrap_fn(canonical_text), base_pii_value


def realize_hindi_carrier(pii_type: str, pii_value_for_slot: str):
    """Shared Devanagari carrier construction for HI_LATIN_PII / HI_DEVA_PII
    (guidelines.md Section 4.11's matched-variant invariant: identical
    template, only the {value} slot's content/script differs by caller)."""
    template = templates.CARRIER_TEMPLATE_DEVANAGARI[pii_type]
    text = template.format(value=pii_value_for_slot)
    return text, pii_value_for_slot


def realize_rom_hi(pii_type: str, base_pii_value: str):
    """ROM_HI: frozen Latin-script Hindi carrier template. PII unchanged."""
    template = templates.CARRIER_TEMPLATE_ROM_HI[pii_type]
    text = template.format(value=base_pii_value)
    return text, base_pii_value


def realize_hinglish(rom_hi_text: str, base_pii_value: str, index: int):
    """HINGLISH: built from the ROM_HI realization, one frozen insertion
    pattern applied (guidelines.md Section 4.13), cycled deterministically."""
    pattern_fn = templates.HINGLISH_PATTERNS[index % len(templates.HINGLISH_PATTERNS)]
    text = pattern_fn(rom_hi_text)
    return text, base_pii_value


def _lowercase_and_contract(carrier_fragment: str) -> str:
    out = carrier_fragment.lower()
    for full, short in templates.INFORMAL_COPULA_CONTRACTIONS.items():
        out = out.replace(f" {full}", f" {short}")
    return out


def realize_informal_hinglish(hinglish_text: str, base_pii_value: str, index: int):
    """INFORMAL_HINGLISH: built from HINGLISH. The PII substring is located
    and carved out BEFORE any transformation; only the carrier fragments on
    either side are lowercased/contracted/given a casual-particle suffix;
    the original PII substring is reinserted byte-for-byte afterward. This
    is what guarantees PAN/AADHAAR/PHONE/BANK_ACCOUNT/UPI_ID/EMAIL and
    PERSON/ADDRESS Latin PII are never mutated by this transform."""
    start, end = find_occurrence(hinglish_text, base_pii_value, occurrence_index=0)
    prefix, suffix = hinglish_text[:start], hinglish_text[end:]

    prefix_transformed = _lowercase_and_contract(prefix)
    suffix_transformed = _lowercase_and_contract(suffix)
    suffix_transformed = suffix_transformed.rstrip(". ")
    particle = templates.INFORMAL_CASUAL_PARTICLES[
        index % len(templates.INFORMAL_CASUAL_PARTICLES)
    ]
    suffix_transformed = f"{suffix_transformed} {particle}"

    text = prefix_transformed + base_pii_value + suffix_transformed

    # Re-verify the span contract holds after reassembly -- fail closed if
    # the reinsertion did not preserve the PII substring exactly.
    reinsert_start = len(prefix_transformed)
    reinsert_end = reinsert_start + len(base_pii_value)
    if text[reinsert_start:reinsert_end] != base_pii_value:
        raise SpanResolutionError(
            "INFORMAL_HINGLISH reassembly failed to preserve the PII "
            f"substring exactly: expected {base_pii_value!r}"
        )
    return text, base_pii_value
