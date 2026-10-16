"""T12: Adversarial record generation and assembly (guidelines.md v0.18 Section 14).

Orchestrates the 5 perturbation families (A1-A5) across the 20 frozen positive base instances,
producing exactly 100 adversarial records conforming to schemas/example.schema.json.
"""

from __future__ import annotations

import json
from pathlib import Path

from generators.perturbations import (
    realize_abbreviation,
    realize_char_variation,
    realize_label_obfuscation,
    realize_punctuation,
    realize_spacing,
)

from . import metadata
from .spans import find_occurrence

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BASE_INSTANCES_PATH = _REPO_ROOT / "data" / "raw" / "base_instances.jsonl"
_OUTPUT_PATH = _REPO_ROOT / "data" / "generated" / "adversarial_realizations.jsonl"

GENERATOR_VERSION = "0.1.0"
GUIDELINES_VERSION = "0.18"
SEED = 42

SELECTED_BASE_IDS = [
    "PERSON_001",
    "PERSON_002",
    "ADDRESS_001",
    "ADDRESS_002",
    "PHONE_001",
    "PHONE_002",
    "EMAIL_001",
    "EMAIL_002",
    "PAN_001",
    "PAN_002",
    "PAN_003",
    "AADHAAR_001",
    "AADHAAR_002",
    "AADHAAR_003",
    "UPI_ID_001",
    "UPI_ID_002",
    "UPI_ID_003",
    "BANK_ACCOUNT_001",
    "BANK_ACCOUNT_002",
    "BANK_ACCOUNT_003",
]

VALIDATION_PENDING = {
    "structural": "PENDING",
    "span": "PENDING",
    "semantic": "PENDING",
    "language": "PENDING",
    "duplicate": "PENDING",
    "human": "PENDING",
}


def load_selected_bases(path: Path = _BASE_INSTANCES_PATH) -> list[dict]:
    """Load the 20 frozen positive bases from data/raw/base_instances.jsonl."""
    all_bases = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    base_map = {b["base_id"]: b for b in all_bases}
    return [base_map[bid] for bid in SELECTED_BASE_IDS]


def _assemble_adversarial_record(
    base_id: str,
    family: str,
    ptype: str,
    target: str,
    text: str,
    base_pii_value: str,
    realized_pii_value: str,
    domain: str,
    address_structure: dict | None,
) -> dict:
    start, end = find_occurrence(text, realized_pii_value, occurrence_index=0)
    entity = {
        "type": ptype,
        "base_pii_value": base_pii_value,
        "realized_pii_value": realized_pii_value,
        "pii_script": metadata.pii_script(ptype, "EN"),
        "start": start,
        "end": end,
        "occurrence_index": 0,
    }
    return {
        "base_id": base_id,
        "variant_id": f"{base_id}_EN_{family}_01",
        "text": text,
        "entities": [entity],
        "distractors": [],
        "language": "EN",
        "carrier_script": "LATIN",
        "context": "EXPLICIT",
        "domain": domain,
        "perturbation": {
            "family": family,
            "type": ptype_for_family(family),
            "severity": 1,
            "target": target,
        },
        "difficulty": "ADVERSARIAL",
        "address_structure": address_structure,
        "hi_variant_collapsed": False,
        "synthetic": True,
        "generator_version": GENERATOR_VERSION,
        "guidelines_version": GUIDELINES_VERSION,
        "template_id": f"EN_{ptype}_{family}_TEMPLATE",
        "seed": SEED,
        "validation": dict(VALIDATION_PENDING),
        "validation_status": "PENDING",
        "review_status": "PENDING",
        "split": None,
    }


def ptype_for_family(family: str) -> str:
    mapping = {
        "A1": "SPACING",
        "A2": "PUNCTUATION",
        "A3": "LABEL_OBFUSCATION",
        "A4": "INFORMAL_ABBREVIATION",
        "A5": "CHARACTER_VARIATION",
    }
    if family not in mapping:
        raise ValueError(f"unknown perturbation family: {family!r}")
    return mapping[family]


def generate_adversarial_records_for_base(base: dict) -> list[dict]:
    """Generate 5 adversarial variants (A1-A5) for a single positive base."""
    base_id = base["base_id"]
    pii_entry = base["pii"][0]
    pii_type = pii_entry["type"]
    base_pii_value = pii_entry["base_pii_value"]
    canonical_text = base["canonical_text"]
    domain = metadata.record_domain(base["scenario"]["domain"])
    address_structure = base["address_structure"]

    records = []

    # A1 SPACING (target: VALUE)
    a1_text, a1_val = realize_spacing(canonical_text, base_pii_value)
    records.append(
        _assemble_adversarial_record(
            base_id, "A1", pii_type, "VALUE", a1_text, base_pii_value, a1_val, domain, address_structure
        )
    )

    # A2 PUNCTUATION (target: VALUE)
    a2_text, a2_val = realize_punctuation(pii_type, canonical_text, base_pii_value)
    records.append(
        _assemble_adversarial_record(
            base_id, "A2", pii_type, "VALUE", a2_text, base_pii_value, a2_val, domain, address_structure
        )
    )

    # A3 LABEL_OBFUSCATION (target: LABEL)
    a3_text, a3_val = realize_label_obfuscation(pii_type, canonical_text, base_pii_value)
    records.append(
        _assemble_adversarial_record(
            base_id, "A3", pii_type, "LABEL", a3_text, base_pii_value, a3_val, domain, address_structure
        )
    )

    # A4 INFORMAL_ABBREVIATION (target: LABEL)
    a4_text, a4_val = realize_abbreviation(pii_type, canonical_text, base_pii_value)
    records.append(
        _assemble_adversarial_record(
            base_id, "A4", pii_type, "LABEL", a4_text, base_pii_value, a4_val, domain, address_structure
        )
    )

    # A5 CHARACTER_VARIATION (target: VALUE)
    a5_text, a5_val = realize_char_variation(pii_type, canonical_text, base_pii_value)
    records.append(
        _assemble_adversarial_record(
            base_id, "A5", pii_type, "VALUE", a5_text, base_pii_value, a5_val, domain, address_structure
        )
    )

    return records


def generate_all_adversarial_records(bases: list[dict]) -> list[dict]:
    """Generate all 100 adversarial records across the selected bases."""
    records = []
    for base in bases:
        records.extend(generate_adversarial_records_for_base(base))
    return records


def write_adversarial_records(records: list[dict], output_path: Path = _OUTPUT_PATH) -> None:
    """Write adversarial records to disk. Refuses overwrite if file exists."""
    if output_path.exists():
        raise FileExistsError(
            f"{output_path} already exists -- refusing to overwrite it. "
            "Move or version the existing file before regenerating."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> list[dict]:
    bases = load_selected_bases()
    records = generate_all_adversarial_records(bases)
    write_adversarial_records(records)
    return records


if __name__ == "__main__":
    main()
