"""T09: dataset-quality span validator (literal T09, PROJECT_SPEC.md Section 31:
"span extractor + occurrence-aware validator") -- distinct from, and not
depending on, the evaluation-layer scoring methodology in Section 20.2-20.6.

Independently re-derives the expected PII occurrence for each derived (T08)
record and compares it against what the record actually declares. Never
repairs anything -- only detects and reports. Never writes to
data/generated/language_realizations.jsonl or any other dataset file.

Reuses generators/language/spans.py's occurrence-walking primitives rather
than duplicating span-resolution logic -- the same fail-closed
find_all_occurrences() used at generation time is used here, independently,
at validation time. Reuses generators/translit/table.py's transliterate_value
as the sole source of Devanagari ground truth for PERSON/ADDRESS under
HI_DEVA_PII -- transliteration is never reimplemented here.

Separation of concerns:
  extraction/calculation -> generators.language.spans (reused, not duplicated)
  validation              -> validate_record_span / validate_hindi_collapse_representation
  rejection representation -> SpanValidationIssue, using guidelines.md Section 18's
                               existing rejection-reason vocabulary (no new reasons
                               invented)
"""

from __future__ import annotations

from dataclasses import dataclass

from generators.language.spans import find_all_occurrences
from generators.translit.table import transliterate_value

TRANSLITERABLE_TYPES = ("PERSON", "ADDRESS")

# guidelines.md Section 18's existing rejection-reason vocabulary -- reused
# exactly, nothing new invented.
PII_NOT_FOUND = "PII_NOT_FOUND"
SPAN_MISMATCH = "SPAN_MISMATCH"
OCCURRENCE_MISMATCH = "OCCURRENCE_MISMATCH"


@dataclass
class SpanValidationIssue:
    """Rejection information shaped for guidelines.md Section 18's rejection
    log (reason, the validator that fired, generator_version) -- not itself
    written to data/rejected/ by this module; that is the caller's decision."""

    variant_id: str
    reason: str
    detail: str
    validator: str = "validators.spans"


def expected_realized_value(language: str, entity_type: str, base_pii_value: str) -> str:
    """The oracle for what realized_pii_value SHOULD be, given the source
    base's own base_pii_value. T07's transliterate_value is the ONLY source
    of Devanagari truth -- never recomputed any other way."""
    if entity_type in TRANSLITERABLE_TYPES and language == "HI_DEVA_PII":
        return transliterate_value(base_pii_value)
    return base_pii_value


def validate_record_span(record: dict, base_by_id: dict) -> list:
    """Independently re-validate one derived record's type/value/span/
    occurrence contract. Returns [] if valid; a list of SpanValidationIssue
    otherwise. Never raises for an ordinary validation failure -- every
    failure mode this function can detect is reported, not thrown."""
    issues = []
    variant_id = record.get("variant_id", "<unknown>")

    base = base_by_id.get(record.get("base_id"))
    if base is None:
        return [
            SpanValidationIssue(
                variant_id, PII_NOT_FOUND, "base_id not found in base_instances.jsonl"
            )
        ]

    entities = record.get("entities") or []
    base_kind = base.get("base_kind")

    if base_kind == "HARD_NEGATIVE":
        # guidelines.md §13.3 (frozen since v0.1, long before this validator
        # existed): a hard negative has an empty entities array by
        # definition -- this is the correct, expected state, not a failure
        # to find PII. A HARD_NEGATIVE record that unexpectedly *does* carry
        # an entity is the actual error here, mirroring
        # validators/base_kind.py's own base_kind/pii cardinality invariant.
        if entities:
            return [
                SpanValidationIssue(
                    variant_id,
                    SPAN_MISMATCH,
                    "HARD_NEGATIVE record must not have any entities, "
                    f"found {len(entities)}",
                )
            ]
        return []

    if not entities:
        return [SpanValidationIssue(variant_id, PII_NOT_FOUND, "record has no entities")]

    entity = entities[0]
    base_pii = base["pii"][0]
    text = record.get("text", "")
    language = record.get("language")

    if entity.get("type") != base_pii["type"]:
        issues.append(
            SpanValidationIssue(
                variant_id,
                SPAN_MISMATCH,
                f"type mismatch: entity={entity.get('type')!r} "
                f"source base={base_pii['type']!r}",
            )
        )

    if entity.get("base_pii_value") != base_pii["base_pii_value"]:
        issues.append(
            SpanValidationIssue(
                variant_id, SPAN_MISMATCH, "base_pii_value changed from source base"
            )
        )

    expected_value = expected_realized_value(
        language, base_pii["type"], base_pii["base_pii_value"]
    )
    declared_value = entity.get("realized_pii_value")
    if declared_value != expected_value:
        issues.append(
            SpanValidationIssue(
                variant_id,
                SPAN_MISMATCH,
                f"realized_pii_value mismatch: got={declared_value!r} "
                f"expected={expected_value!r}",
            )
        )

    start, end = entity.get("start"), entity.get("end")

    # Fundamental span contract on the DECLARED offsets and DECLARED value --
    # independent of the oracle above. This is what catches a stale span
    # after text mutation: even if realized_pii_value happens to be right,
    # the offsets must still point at it inside THIS text.
    if not (
        isinstance(start, int)
        and isinstance(end, int)
        and 0 <= start < end <= len(text)
    ):
        issues.append(
            SpanValidationIssue(
                variant_id, SPAN_MISMATCH, f"start/end out of range: ({start},{end})"
            )
        )
        return issues  # cannot safely slice further
    if text[start:end] != declared_value:
        issues.append(
            SpanValidationIssue(
                variant_id,
                SPAN_MISMATCH,
                f"text[{start}:{end}] == {text[start:end]!r} != "
                f"realized_pii_value {declared_value!r}",
            )
        )

    # Occurrence resolution: walk every occurrence of the EXPECTED value in
    # this text (never a bare str.find()), and check the declared
    # occurrence_index resolves to the declared span. PII_NOT_FOUND and
    # OCCURRENCE_MISMATCH are kept distinct per guidelines.md Section 18.
    matches = find_all_occurrences(text, expected_value)
    if not matches:
        issues.append(
            SpanValidationIssue(
                variant_id, PII_NOT_FOUND, f"{expected_value!r} does not occur in text"
            )
        )
        return issues

    declared_occurrence = entity.get("occurrence_index")
    if not isinstance(declared_occurrence, int) or not (
        0 <= declared_occurrence < len(matches)
    ):
        issues.append(
            SpanValidationIssue(
                variant_id,
                OCCURRENCE_MISMATCH,
                f"occurrence_index={declared_occurrence!r} invalid for "
                f"{len(matches)} occurrence(s) of {expected_value!r}",
            )
        )
        return issues

    expected_start = matches[declared_occurrence]
    expected_end = expected_start + len(expected_value)
    if (start, end) != (expected_start, expected_end):
        issues.append(
            SpanValidationIssue(
                variant_id,
                OCCURRENCE_MISMATCH,
                f"declared span ({start},{end}) does not match the position of "
                f"occurrence_index={declared_occurrence} "
                f"({expected_start},{expected_end})",
            )
        )

    return issues


def validate_hindi_collapse_representation(records_for_base: list, base: dict) -> list:
    """Cross-record check (guidelines.md Section 8.1 / Section 4.11): for
    transliterable types, both HI_LATIN_PII and HI_DEVA_PII must exist,
    neither collapsed. For non-transliterable types, exactly one
    HI_LATIN_PII record must exist, marked hi_variant_collapsed=true, and no
    HI_DEVA_PII record at all."""
    issues = []
    base_id = base["base_id"]
    pii_type = base["pii"][0]["type"]
    by_language = {r["language"]: r for r in records_for_base if r["language"] in (
        "HI_LATIN_PII", "HI_DEVA_PII"
    )}

    if pii_type in TRANSLITERABLE_TYPES:
        for language in ("HI_LATIN_PII", "HI_DEVA_PII"):
            record = by_language.get(language)
            if record is None:
                issues.append(
                    SpanValidationIssue(
                        base_id, SPAN_MISMATCH, f"transliterable base missing {language}"
                    )
                )
                continue
            if record.get("hi_variant_collapsed") is not False:
                issues.append(
                    SpanValidationIssue(
                        record.get("variant_id"),
                        SPAN_MISMATCH,
                        f"{language} on a transliterable base must not be collapsed",
                    )
                )
    else:
        if "HI_DEVA_PII" in by_language:
            issues.append(
                SpanValidationIssue(
                    base_id,
                    SPAN_MISMATCH,
                    "non-transliterable base has an unexpected HI_DEVA_PII record",
                )
            )
        latin_record = by_language.get("HI_LATIN_PII")
        if latin_record is None:
            issues.append(
                SpanValidationIssue(
                    base_id,
                    SPAN_MISMATCH,
                    "non-transliterable base missing its collapsed HI_LATIN_PII record",
                )
            )
        elif latin_record.get("hi_variant_collapsed") is not True:
            issues.append(
                SpanValidationIssue(
                    latin_record.get("variant_id"),
                    SPAN_MISMATCH,
                    "collapsed non-transliterable record missing hi_variant_collapsed=true",
                )
            )

    return issues


def validate_dataset(records: list, bases: list) -> dict:
    """Top-level orchestrator. Read-only: never mutates `records` or `bases`,
    never writes to disk. Returns a report suitable for consumption by later
    validators (T10) or the pilot quality report (T14) -- never invented as
    a new persisted artifact format by this module."""
    base_by_id = {b["base_id"]: b for b in bases}
    issues = []

    for record in records:
        issues.extend(validate_record_span(record, base_by_id))

    by_base = {}
    for record in records:
        by_base.setdefault(record["base_id"], []).append(record)
    for base_id, recs in by_base.items():
        base = base_by_id.get(base_id)
        if base is not None:
            issues.extend(validate_hindi_collapse_representation(recs, base))

    invalid_variant_ids = {i.variant_id for i in issues}
    return {
        "total_records": len(records),
        "valid_records": len(records) - len(invalid_variant_ids & {r["variant_id"] for r in records}),
        "issues": issues,
    }
