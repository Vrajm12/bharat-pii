"""T13: Pilot human-review CSV exporter (PROJECT_SPEC.md §25, §31; guidelines.md §19).

Exports all 964 canonical benchmark records into annotation/review_template.csv
with pre-populated metadata and blank/pending reviewer fields.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

EXPECTED_COLUMNS: list[str] = [
    "variant_id",
    "base_id",
    "base_kind",
    "difficulty",
    "language",
    "carrier_script",
    "context",
    "declared_pii_type",
    "marked_span_text",
    "start",
    "end",
    "perturbation_family",
    "perturbation_target",
    "decoy_class",
    "full_text",
    "reviewer_id",
    "span_correct",
    "type_correct",
    "language_correct",
    "script_correct",
    "meaning_preserved",
    "natural",
    "human_recoverable",
    "review_status",
    "notes",
]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL file into a list of dictionaries."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                records.append(json.loads(line_str))
    return records


def _process_base_instance(rec: dict[str, Any]) -> dict[str, Any]:
    """Convert a positive base instance into a review row."""
    base_id = rec["base_id"]
    text = rec.get("canonical_text", "")
    scenario = rec.get("scenario", {})
    context = scenario.get("context_level", "EXPLICIT")
    difficulty = scenario.get("difficulty", "EASY")

    # Extract first PII entity if available
    pii_list = rec.get("pii", [])
    declared_type = "NONE"
    marked_span = ""
    start_val = ""
    end_val = ""

    if pii_list:
        first_pii = pii_list[0]
        declared_type = first_pii.get("type", "NONE")
        val = first_pii.get("base_pii_value", "")
        # Locate value in canonical_text
        pos = text.find(val)
        if pos != -1:
            marked_span = val
            start_val = str(pos)
            end_val = str(pos + len(val))

    return {
        "variant_id": base_id,
        "base_id": base_id,
        "base_kind": "POSITIVE",
        "difficulty": difficulty,
        "language": "EN",
        "carrier_script": "LATIN",
        "context": context,
        "declared_pii_type": declared_type,
        "marked_span_text": marked_span,
        "start": start_val,
        "end": end_val,
        "perturbation_family": "NONE",
        "perturbation_target": "NONE",
        "decoy_class": "",
        "full_text": text,
        "reviewer_id": "",
        "span_correct": "",
        "type_correct": "",
        "language_correct": "",
        "script_correct": "",
        "meaning_preserved": "",
        "natural": "",
        "human_recoverable": "",
        "review_status": "PENDING",
        "notes": "",
    }


def _process_hard_negative_base(rec: dict[str, Any]) -> dict[str, Any]:
    """Convert a hard-negative base instance into a review row."""
    base_id = rec["base_id"]
    text = rec.get("canonical_text", "")
    scenario = rec.get("scenario", {})
    context = scenario.get("context_level", "EXPLICIT")
    difficulty = scenario.get("difficulty", "EASY")
    decoy = rec.get("hard_negative_decoy", {})
    decoy_class = decoy.get("decoy_class", "")

    return {
        "variant_id": base_id,
        "base_id": base_id,
        "base_kind": "HARD_NEGATIVE",
        "difficulty": difficulty,
        "language": "EN",
        "carrier_script": "LATIN",
        "context": context,
        "declared_pii_type": "NONE",
        "marked_span_text": "",
        "start": "",
        "end": "",
        "perturbation_family": "NONE",
        "perturbation_target": "NONE",
        "decoy_class": decoy_class,
        "full_text": text,
        "reviewer_id": "",
        "span_correct": "",
        "type_correct": "",
        "language_correct": "",
        "script_correct": "",
        "meaning_preserved": "",
        "natural": "",
        "human_recoverable": "",
        "review_status": "PENDING",
        "notes": "",
    }


def _process_derived_record(rec: dict[str, Any], is_hard_negative: bool) -> dict[str, Any]:
    """Convert a derived realization into a review row."""
    base_id = rec.get("base_id", "")
    variant_id = rec.get("variant_id", "")
    text = rec.get("text", "")
    language = rec.get("language", "EN")
    carrier_script = rec.get("carrier_script", "LATIN")
    context = rec.get("context", "EXPLICIT")
    difficulty = rec.get("difficulty", "HARD_NEGATIVE" if is_hard_negative else "STANDARD")
    perturbation = rec.get("perturbation", {})
    pert_family = perturbation.get("family", "NONE")
    pert_target = perturbation.get("target", "NONE")

    base_kind = "HARD_NEGATIVE" if is_hard_negative else "POSITIVE"

    declared_type = "NONE"
    marked_span = ""
    start_val = ""
    end_val = ""
    decoy_class = ""

    if is_hard_negative:
        distractors = rec.get("distractors", [])
        if distractors:
            decoy_class = distractors[0].get("decoy_class", "")
    else:
        entities = rec.get("entities", [])
        if entities:
            first_ent = entities[0]
            declared_type = first_ent.get("type", "NONE")
            start = first_ent.get("start")
            end = first_ent.get("end")
            if start is not None and end is not None:
                start_val = str(start)
                end_val = str(end)
                marked_span = text[start:end]

    return {
        "variant_id": variant_id,
        "base_id": base_id,
        "base_kind": base_kind,
        "difficulty": difficulty,
        "language": language,
        "carrier_script": carrier_script,
        "context": context,
        "declared_pii_type": declared_type,
        "marked_span_text": marked_span,
        "start": start_val,
        "end": end_val,
        "perturbation_family": pert_family,
        "perturbation_target": pert_target,
        "decoy_class": decoy_class,
        "full_text": text,
        "reviewer_id": "",
        "span_correct": "",
        "type_correct": "",
        "language_correct": "",
        "script_correct": "",
        "meaning_preserved": "",
        "natural": "",
        "human_recoverable": "",
        "review_status": "PENDING",
        "notes": "",
    }


def build_review_rows(data_dir: Path = Path("data")) -> list[dict[str, Any]]:
    """Build all 964 review rows from canonical datasets in deterministic order."""
    rows: list[dict[str, Any]] = []

    # 1. 100 Positive base instances
    p_bases = _read_jsonl(data_dir / "raw" / "base_instances.jsonl")
    for rec in p_bases:
        rows.append(_process_base_instance(rec))

    # 2. 20 Hard-negative base instances
    hn_bases = _read_jsonl(data_dir / "raw" / "hard_negative_bases.jsonl")
    for rec in hn_bases:
        rows.append(_process_hard_negative_base(rec))

    # 3. 624 Language realizations
    lang_realizations = _read_jsonl(data_dir / "generated" / "language_realizations.jsonl")
    for rec in lang_realizations:
        rows.append(_process_derived_record(rec, is_hard_negative=False))

    # 4. 120 Hard-negative realizations
    hn_realizations = _read_jsonl(data_dir / "generated" / "hard_negative_realizations.jsonl")
    for rec in hn_realizations:
        rows.append(_process_derived_record(rec, is_hard_negative=True))

    # 5. 100 Adversarial realizations
    adv_realizations = _read_jsonl(data_dir / "generated" / "adversarial_realizations.jsonl")
    for rec in adv_realizations:
        rows.append(_process_derived_record(rec, is_hard_negative=False))

    return rows


def export_pilot_review_csv(
    output_path: Path = Path("annotation/review_template.csv"),
    data_dir: Path = Path("data"),
    overwrite: bool = True,
) -> Path:
    """Export the pilot review CSV template.

    Args:
        output_path: Path to target CSV file.
        data_dir: Directory containing raw and generated datasets.
        overwrite: Allow overwriting existing file.

    Returns:
        The written Path.
    """
    output_path = Path(output_path)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Target review CSV already exists at {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = build_review_rows(data_dir)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    return output_path


if __name__ == "__main__":
    out = export_pilot_review_csv()
    print(f"Exported {out} with 964 review records.")
