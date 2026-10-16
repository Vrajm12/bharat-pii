"""T08: record assembly.

Ties together templates.py / realizations.py / spans.py / metadata.py into
complete records matching schemas/example.schema.json. Contains no
generation logic of its own beyond orchestration and no validation logic
beyond the basic span contract (Section 15's full validators are T09/T10,
not built here).

No LLM, no external transliteration service. generators.translit.table is
imported and used as ground truth for HI_DEVA_PII's PERSON/ADDRESS value --
never recomputed, never called with anything the T07 table wasn't already
frozen to handle.
"""

from __future__ import annotations

import json
from pathlib import Path

from generators.translit.table import transliterate_value

from . import metadata, realizations
from .spans import find_occurrence
from .templates import NON_TRANSLITERABLE_TYPES, TRANSLITERABLE_TYPES

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BASE_INSTANCES_PATH = _REPO_ROOT / "data" / "raw" / "base_instances.jsonl"
# PROJECT_SPEC.md Section 25 repo layout: "data/generated/  per-condition jsonl"
_OUTPUT_PATH = _REPO_ROOT / "data" / "generated" / "language_realizations.jsonl"

GENERATOR_VERSION = "0.1.0"  # same toolchain version as T04/T07 (OQ-020 precedent)
GUIDELINES_VERSION = "0.11"
SEED = 42

VALIDATION_PENDING = {
    "structural": "PENDING",
    "span": "PENDING",
    "semantic": "PENDING",
    "language": "PENDING",
    "duplicate": "PENDING",
    "human": "PENDING",
}


def load_base_instances(path: Path = _BASE_INSTANCES_PATH) -> list:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _assemble_record(
    base_id: str,
    language: str,
    text: str,
    pii_type: str,
    base_pii_value: str,
    realized_value: str,
    domain: str,
    address_structure,
    hi_variant_collapsed: bool,
) -> dict:
    start, end = find_occurrence(text, realized_value, occurrence_index=0)
    entity = {
        "type": pii_type,
        "base_pii_value": base_pii_value,
        "realized_pii_value": realized_value,
        "pii_script": metadata.pii_script(pii_type, language),
        "start": start,
        "end": end,
        "occurrence_index": 0,
    }
    return {
        "base_id": base_id,
        "variant_id": metadata.variant_id(base_id, language),
        "text": text,
        "entities": [entity],
        "distractors": [],
        "language": language,
        "carrier_script": metadata.carrier_script(language),
        "context": metadata.CONTEXT,
        "domain": domain,
        "perturbation": dict(metadata.NONE_PERTURBATION),
        "difficulty": metadata.difficulty(language),
        "address_structure": address_structure,
        "hi_variant_collapsed": hi_variant_collapsed,
        "synthetic": True,
        "generator_version": GENERATOR_VERSION,
        "guidelines_version": GUIDELINES_VERSION,
        "template_id": f"{language}_{pii_type}_TEMPLATE",
        "seed": SEED,
        "validation": dict(VALIDATION_PENDING),
        "validation_status": "PENDING",
        "review_status": "PENDING",
        "split": None,
    }


def generate_records_for_base(base: dict, base_index: int) -> list:
    """base_index is the base's 0-based position in the fixed dataset file
    order -- the sole source of determinism for cycling IN_EN markers,
    HINGLISH patterns, and INFORMAL_HINGLISH particles. Never randomness."""
    pii_entry = base["pii"][0]
    pii_type = pii_entry["type"]
    base_pii_value = pii_entry["base_pii_value"]
    base_id = base["base_id"]
    canonical_text = base["canonical_text"]
    domain = metadata.record_domain(base["scenario"]["domain"])
    address_structure = base["address_structure"]

    def assemble(language, text, realized_value, hi_collapsed=False):
        return _assemble_record(
            base_id,
            language,
            text,
            pii_type,
            base_pii_value,
            realized_value,
            domain,
            address_structure,
            hi_collapsed,
        )

    records = []

    en_text, en_value = realizations.realize_en(canonical_text, base_pii_value)
    records.append(assemble("EN", en_text, en_value))

    in_en_text, in_en_value = realizations.realize_in_en(
        canonical_text, base_pii_value, base_index
    )
    records.append(assemble("IN_EN", in_en_text, in_en_value))

    rom_hi_text, rom_hi_value = realizations.realize_rom_hi(pii_type, base_pii_value)
    records.append(assemble("ROM_HI", rom_hi_text, rom_hi_value))

    hinglish_text, hinglish_value = realizations.realize_hinglish(
        rom_hi_text, base_pii_value, base_index
    )
    records.append(assemble("HINGLISH", hinglish_text, hinglish_value))

    informal_text, informal_value = realizations.realize_informal_hinglish(
        hinglish_text, base_pii_value, base_index
    )
    records.append(assemble("INFORMAL_HINGLISH", informal_text, informal_value))

    if pii_type in NON_TRANSLITERABLE_TYPES:
        # guidelines.md Section 8.1: generate ONE collapsed Hindi-condition
        # record. Labeled HI_LATIN_PII (not HI_DEVA_PII) because pii_script
        # for these six types is never DEVANAGARI (Section 4.15) -- HI_LATIN_PII
        # is the accurate label; HI_DEVA_PII would misdescribe the data.
        hi_text, hi_value = realizations.realize_hindi_carrier(
            pii_type, base_pii_value
        )
        records.append(assemble("HI_LATIN_PII", hi_text, hi_value, hi_collapsed=True))
    elif pii_type in TRANSLITERABLE_TYPES:
        hi_latin_text, hi_latin_value = realizations.realize_hindi_carrier(
            pii_type, base_pii_value
        )
        records.append(assemble("HI_LATIN_PII", hi_latin_text, hi_latin_value))

        deva_value = transliterate_value(base_pii_value)  # T07, ground truth
        hi_deva_text, hi_deva_value = realizations.realize_hindi_carrier(
            pii_type, deva_value
        )
        records.append(assemble("HI_DEVA_PII", hi_deva_text, hi_deva_value))
    else:
        raise ValueError(f"unsupported PII type: {pii_type!r}")

    return records


def generate_all_records(bases: list) -> list:
    records = []
    for index, base in enumerate(bases):
        records.extend(generate_records_for_base(base, index))
    return records


def write_derived_records(records: list, output_path: Path = _OUTPUT_PATH) -> None:
    if output_path.exists():
        raise FileExistsError(
            f"{output_path} already exists -- refusing to overwrite it. "
            "Move or version the existing file before regenerating."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> list:
    bases = load_base_instances()
    records = generate_all_records(bases)
    write_derived_records(records)
    return records


if __name__ == "__main__":
    main()
