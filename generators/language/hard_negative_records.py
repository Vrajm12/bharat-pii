"""T11 Phase 2: hard-negative derived-record assembly.

Constructs the six frozen realizations (guidelines.md §13.11) for each of
the 20 `HARD_NEGATIVE` base instances (`generators/hard_negatives.py`,
Phase 1), using the frozen §13.13 lexical inventory and carrier grammar for
the five constructible decoy classes. `ORG_AS_PERSON` has quota 0 (Phase 1)
and has no entry in this module's carrier dicts at all -- not a stub, not a
placeholder, simply absent, so a decoy of that class would fail closed
(`KeyError`) rather than silently produce something.

Reused, unmodified:
  - generators.language.metadata: CONTEXT, NONE_PERTURBATION, variant_id,
    carrier_script, difficulty, record_domain -- all PII-type-independent,
    confirmed applicable to records with no PII at all.
  - generators.language.templates: IN_EN_MARKERS, HINGLISH_PATTERNS,
    INFORMAL_CASUAL_PARTICLES, INFORMAL_COPULA_CONTRACTIONS -- confirmed by
    direct execution (T11 Phase 2 pre-audit) to be pure string operations,
    never keyed by PII type.
  - generators.language.spans.find_occurrence -- the same occurrence-walking
    primitive T08 uses for entities, used here for the single distractor.

Not reused, because they are keyed by `pii_type`, which a hard negative does
not have (guidelines.md §13.13, resolves OQ-047):
  - generators.language.templates.CARRIER_TEMPLATE_ROM_HI /
    CARRIER_TEMPLATE_DEVANAGARI
  - generators.language.realizations' realize_rom_hi / realize_hindi_carrier

`_lowercase_and_contract` mirrors `generators/language/realizations.py`'s
private function of the same name exactly, reusing its underlying frozen
data (`templates.INFORMAL_COPULA_CONTRACTIONS`) -- kept as a separate,
parallel definition rather than importing a private cross-module symbol, so
`realizations.py` (T08, positive-PII only) is not touched by this module at
all.

Does not implement distractor-span validation as a `validators/` contract --
that is OQ-048, deliberately left unresolved by this module. Construction-
time correctness (every generated distractor span is verified correct) is
proven by this module's own test suite, which is not the same as extending
`validators/spans.py`'s formal contract.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import metadata, templates
from .spans import SpanResolutionError, find_occurrence

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HARD_NEGATIVE_BASES_PATH = _REPO_ROOT / "data" / "raw" / "hard_negative_bases.jsonl"
# Kept separate from data/generated/language_realizations.jsonl (positive
# records) -- PROJECT_SPEC.md §12.2 frames hard negatives as additional to,
# never merged into, the positive set ("not part of the 100"); the same
# principle applied to the base file in Phase 1 is applied here to the
# derived-record file. Not a filename PROJECT_SPEC.md/guidelines.md names
# explicitly; disclosed as an implementation choice, mirroring
# hard_negative_bases.jsonl's own naming.
_OUTPUT_PATH = _REPO_ROOT / "data" / "generated" / "hard_negative_realizations.jsonl"

GENERATOR_VERSION = "0.1.0"  # same toolchain version as T04/T07/T08 (OQ-020 precedent)
GUIDELINES_VERSION = "0.17"
SEED = 42

VALIDATION_PENDING = {
    "structural": "PENDING",
    "span": "PENDING",
    "semantic": "PENDING",
    "language": "PENDING",
    "duplicate": "PENDING",
    "human": "PENDING",
}

# --- guidelines.md §13.13 frozen carrier grammar, keyed by decoy_class ------
# (NOT pii_type -- a hard negative has no PII type at all). ORG_AS_PERSON is
# deliberately absent: quota 0, no construction rule was frozen for it.

HARD_NEGATIVE_CARRIER_ROM_HI = {
    "NUMERIC_SHAPE": "mera order number {value} hai.",
    "ALNUM_SHAPE": "mera reference code {value} hai.",
    "NAME_AS_PLACE": "{value} station ke paas hai.",
    "HANDLE_SHAPE": "mera contact {value} hai.",
    "PARTIAL_PII": "mera account number {value} hai.",
}

HARD_NEGATIVE_CARRIER_DEVANAGARI = {
    "NUMERIC_SHAPE": "मेरा ऑर्डर नंबर {value} है।",
    "ALNUM_SHAPE": "मेरा रेफरेंस कोड {value} है।",
    "NAME_AS_PLACE": "{value} स्टेशन के पास है।",
    "HANDLE_SHAPE": "मेरा कॉन्टैक्ट {value} है।",
    "PARTIAL_PII": "मेरा अकाउंट नंबर {value} है।",
}


def _lowercase_and_contract(carrier_fragment: str) -> str:
    """Mirrors generators/language/realizations.py's private function of the
    same name exactly (see module docstring for why this is a parallel
    definition, not an import)."""
    out = carrier_fragment.lower()
    for full, short in templates.INFORMAL_COPULA_CONTRACTIONS.items():
        out = out.replace(f" {full}", f" {short}")
    return out


def _realize_informal_hinglish(hinglish_text: str, value: str, index: int) -> str:
    """INFORMAL_HINGLISH for a hard-negative decoy: the distractor value is
    located and carved out BEFORE any transformation; only the carrier
    fragments on either side are lowercased/contracted/given a casual-
    particle suffix; the value is reinserted byte-for-byte afterward. This
    is the identical discipline realize_informal_hinglish already implements
    and verifies for positive PII (T11 Phase 2 pre-audit finding) -- applied
    here to `value` instead of `base_pii_value`."""
    start, end = find_occurrence(hinglish_text, value, occurrence_index=0)
    prefix, suffix = hinglish_text[:start], hinglish_text[end:]

    prefix_transformed = _lowercase_and_contract(prefix)
    suffix_transformed = _lowercase_and_contract(suffix)
    suffix_transformed = suffix_transformed.rstrip(". ")
    particle = templates.INFORMAL_CASUAL_PARTICLES[
        index % len(templates.INFORMAL_CASUAL_PARTICLES)
    ]
    suffix_transformed = f"{suffix_transformed} {particle}"

    text = prefix_transformed + value + suffix_transformed

    reinsert_start = len(prefix_transformed)
    reinsert_end = reinsert_start + len(value)
    if text[reinsert_start:reinsert_end] != value:
        raise SpanResolutionError(
            "INFORMAL_HINGLISH reassembly failed to preserve the distractor "
            f"value exactly: expected {value!r}"
        )
    return text


def _assemble_record(
    base_id: str,
    language: str,
    text: str,
    decoy: dict,
    domain: str,
    hi_variant_collapsed: bool = False,
) -> dict:
    start, end = find_occurrence(text, decoy["value"], occurrence_index=0)
    distractor = {
        "text": decoy["value"],
        "start": start,
        "end": end,
        "surface_type": decoy["surface_type"],
        "actual_role": decoy["actual_role"],
        "decoy_class": decoy["decoy_class"],
    }
    return {
        "base_id": base_id,
        "variant_id": metadata.variant_id(base_id, language),
        "text": text,
        "entities": [],
        "distractors": [distractor],
        "language": language,
        "carrier_script": metadata.carrier_script(language),
        "context": metadata.CONTEXT,
        "domain": domain,
        "perturbation": dict(metadata.NONE_PERTURBATION),
        "difficulty": metadata.difficulty(language),
        "address_structure": None,
        "hi_variant_collapsed": hi_variant_collapsed,
        "synthetic": True,
        "generator_version": GENERATOR_VERSION,
        "guidelines_version": GUIDELINES_VERSION,
        "template_id": f"{language}_{decoy['decoy_class']}_HARD_NEGATIVE_TEMPLATE",
        "seed": SEED,
        "validation": dict(VALIDATION_PENDING),
        "validation_status": "PENDING",
        "review_status": "PENDING",
        "split": None,
    }


def generate_records_for_base(base: dict, base_index: int) -> list:
    """base_index is the base's 0-based position in the fixed dataset file
    order -- the sole source of determinism for cycling IN_EN markers,
    HINGLISH patterns, and INFORMAL_HINGLISH particles, matching
    generators/language/records.py's own convention exactly."""
    decoy = base["hard_negative_decoy"]
    decoy_class = decoy["decoy_class"]
    base_id = base["base_id"]
    canonical_text = base["canonical_text"]
    domain = metadata.record_domain(base["scenario"]["domain"])

    records = []

    # EN: canonical_text unchanged (guidelines.md §13.8's frozen template,
    # value already substituted at base-generation time).
    records.append(_assemble_record(base_id, "EN", canonical_text, decoy, domain))

    # IN_EN: one frozen §4.12 marker, cycled by base_index -- the same
    # generic wrap functions T08 already applies to positive PII sentences.
    _, wrap_fn = templates.IN_EN_MARKERS[base_index % len(templates.IN_EN_MARKERS)]
    in_en_text = wrap_fn(canonical_text)
    records.append(_assemble_record(base_id, "IN_EN", in_en_text, decoy, domain))

    # ROM_HI: guidelines.md §13.13's frozen carrier, keyed by decoy_class.
    rom_hi_text = HARD_NEGATIVE_CARRIER_ROM_HI[decoy_class].format(value=decoy["value"])
    records.append(_assemble_record(base_id, "ROM_HI", rom_hi_text, decoy, domain))

    # HINGLISH: one frozen §4.13 insertion pattern applied to the ROM_HI
    # sentence above -- the same generic, PII-independent pattern functions.
    pattern_fn = templates.HINGLISH_PATTERNS[base_index % len(templates.HINGLISH_PATTERNS)]
    hinglish_text = pattern_fn(rom_hi_text)
    records.append(_assemble_record(base_id, "HINGLISH", hinglish_text, decoy, domain))

    # INFORMAL_HINGLISH: built from HINGLISH, value carved out and preserved.
    informal_text = _realize_informal_hinglish(hinglish_text, decoy["value"], base_index)
    records.append(_assemble_record(base_id, "INFORMAL_HINGLISH", informal_text, decoy, domain))

    # Collapsed Hindi realization: labeled HI_LATIN_PII (guidelines.md
    # §13.11/§13.13), value substituted in its original script, never
    # transliterated -- there is no hard-negative equivalent of T07's table.
    hindi_text = HARD_NEGATIVE_CARRIER_DEVANAGARI[decoy_class].format(value=decoy["value"])
    records.append(
        _assemble_record(base_id, "HI_LATIN_PII", hindi_text, decoy, domain, hi_variant_collapsed=True)
    )

    return records


def load_hard_negative_bases(path: Path = _HARD_NEGATIVE_BASES_PATH) -> list:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def generate_all_records(bases: list) -> list:
    records = []
    for index, base in enumerate(bases):
        records.extend(generate_records_for_base(base, index))
    return records


def write_derived_records(records: list, output_path: Path = _OUTPUT_PATH) -> None:
    """Fails rather than overwriting an existing file -- never silently
    overwrite a generated dataset (CLAUDE.md), same policy as
    generators/language/records.py's write_derived_records."""
    if output_path.exists():
        raise FileExistsError(
            f"{output_path} already exists -- refusing to overwrite it. "
            "Move or version the existing file before regenerating."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> list:
    bases = load_hard_negative_bases()
    records = generate_all_records(bases)
    write_derived_records(records)
    return records


if __name__ == "__main__":
    main()
