"""T10: dataset-quality semantic validator (literal T10, PROJECT_SPEC.md §31 --
Layer 3 only: guidelines.md §15 "Sentence uses the value in the declared
role"). Layer 4 (language/script), duplicate validation, and human review
are separate, later modules -- not implemented here.

Independent of the generators: every constant this module checks against is
an independent copy of frozen guidelines.md content --

  FROZEN_SEMANTIC_ROLE  -- guidelines.md §13.5 (decision 39, resolves OQ-035)
  LATIN_LABEL / DEVANAGARI_LABEL -- guidelines.md §13.7 (decision 41,
                                     resolves OQ-037), assembled from words
                                     already frozen in §4.10/§4.13, not newly
                                     chosen here

-- never imported from generators/base_instances.py or
generators/language/templates.py, and this module never imports either of
those. Reuses generators/translit/table.py's transliterate_value (via
validators.spans.expected_realized_value, T09's already-existing oracle
function) as the sole source of Devanagari PII-identity ground truth --
T07's transliteration algorithm is never reimplemented here. Does not
duplicate T09's occurrence-walking/span-position logic; where a check needs
a record's already-declared span, it reads the record's own start/end
fields directly rather than re-deriving them.

Four layers, kept separate:
  1. metadata/type-role validation       -> check_semantic_role_matches_type
  2. base/derived linkage validation     -> check_base_linkage
  3. semantic identity validation        -> check_realized_value_identity
  4. condition-specific Layer-3 contract -> check_condition_semantic_contract
     (guidelines.md §13.6 EN/IN_EN, §13.7 the other five)

Cross-record checks (the HI_LATIN_PII/HI_DEVA_PII matched-variant invariant,
and the collapsed non-transliterable representation) are
validate_hindi_matched_pair_semantics / validate_collapsed_hindi_semantics.
Record *existence* for these pairs is T09's job (validate_hindi_collapse_
representation) -- if a expected record is simply absent, these functions
skip rather than duplicate that check.

Every function here is pure: none mutates its `record`/`base` arguments,
and none calls anything non-deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass

from validators.spans import expected_realized_value

SEMANTIC_MISMATCH = "SEMANTIC_MISMATCH"
MISSING_SEMANTIC_ROLE = "MISSING_SEMANTIC_ROLE"
ROLE_UNSUPPORTED_BY_TEXT = "ROLE_UNSUPPORTED_BY_TEXT"

TRANSLITERABLE_TYPES = ("PERSON", "ADDRESS")
NON_TRANSLITERABLE_TYPES = ("PHONE", "EMAIL", "PAN", "AADHAAR", "UPI_ID", "BANK_ACCOUNT")

LATIN_LABEL_CONDITIONS = ("ROM_HI", "HINGLISH", "INFORMAL_HINGLISH")
DEVANAGARI_LABEL_CONDITIONS = ("HI_LATIN_PII", "HI_DEVA_PII")

# guidelines.md §13.5 (decision 39, resolves OQ-035) -- independent copy.
FROZEN_SEMANTIC_ROLE = {
    "PERSON": "PERSON_NAME",
    "ADDRESS": "DELIVERY_ADDRESS",
    "PHONE": "CONTACT_NUMBER",
    "EMAIL": "CONTACT_EMAIL",
    "PAN": "TAX_IDENTIFIER",
    "AADHAAR": "NATIONAL_ID_IDENTIFIER",
    "UPI_ID": "PAYMENT_IDENTIFIER",
    "BANK_ACCOUNT": "PAYMENT_ACCOUNT_IDENTIFIER",
}

# guidelines.md §13.7 (decision 41, resolves OQ-037) -- independent copy,
# assembled from words already frozen in §4.10/§4.13, not newly chosen.
LATIN_LABEL = {
    "PERSON": "naam",
    "ADDRESS": "address",
    "PHONE": "mobile",
    "EMAIL": "email",
    "PAN": "PAN",
    "AADHAAR": "Aadhaar",
    "UPI_ID": "UPI",
    "BANK_ACCOUNT": "account",
}

DEVANAGARI_LABEL = {
    "PERSON": "नाम",
    "ADDRESS": "एड्रेस",
    "PHONE": "मोबाइल",
    "EMAIL": "ईमेल",
    "PAN": "PAN",
    "AADHAAR": "आधार",
    "UPI_ID": "UPI",
    "BANK_ACCOUNT": "अकाउंट",
}


@dataclass
class SemanticValidationIssue:
    """Shaped like validators.spans.SpanValidationIssue for consistency.
    `variant_id` holds a base_id instead for a purely base-level finding
    with no specific derived record at fault (mirrors validators.spans's own
    convention); validate_record_semantic re-keys such findings to the
    calling record's own variant_id when a specific record is at hand."""

    variant_id: str
    reason: str
    detail: str
    validator: str = "validators.semantic"


# --- Layer 1 of 4: metadata/type-role validation (guidelines.md §13.5) -----


def check_semantic_role_matches_type(base: dict) -> list:
    """Base-level, independent of any derived record: the base's declared
    PII type must be consistent with the frozen §13.5 semantic_role
    mapping. Rejects wrong role, unknown role, and missing role."""
    issues = []
    base_id = base.get("base_id", "<unknown>")
    for entry in base.get("pii", []):
        pii_type = entry.get("type")
        declared_role = entry.get("semantic_role")
        if not declared_role:
            issues.append(
                SemanticValidationIssue(
                    base_id, MISSING_SEMANTIC_ROLE, f"{pii_type}: no semantic_role declared"
                )
            )
            continue
        expected_role = FROZEN_SEMANTIC_ROLE.get(pii_type)
        if expected_role is None:
            issues.append(
                SemanticValidationIssue(
                    base_id, SEMANTIC_MISMATCH, f"unknown PII type: {pii_type!r}"
                )
            )
            continue
        if declared_role != expected_role:
            issues.append(
                SemanticValidationIssue(
                    base_id,
                    SEMANTIC_MISMATCH,
                    f"{pii_type}: semantic_role={declared_role!r}, expected "
                    f"{expected_role!r} (guidelines.md §13.5)",
                )
            )
    return issues


# --- Layer 2 of 4: base/derived linkage validation --------------------------


def check_base_linkage(record: dict, base: dict) -> list:
    """PII type matches; base_pii_value matches (canonical identity has not
    mutated); scenario is unchanged (record.domain still derives from the
    linked base's scenario.domain, guidelines.md's own T08 domain-casing
    convention)."""
    issues = []
    variant_id = record.get("variant_id", "<unknown>")
    entities = record.get("entities") or []
    base_pii_list = base.get("pii") or []
    if not entities or not base_pii_list:
        return issues

    entity = entities[0]
    base_pii = base_pii_list[0]

    if entity.get("type") != base_pii.get("type"):
        issues.append(
            SemanticValidationIssue(
                variant_id,
                SEMANTIC_MISMATCH,
                f"linked base's PII type {base_pii.get('type')!r} does not match "
                f"record entity type {entity.get('type')!r}",
            )
        )

    if entity.get("base_pii_value") != base_pii.get("base_pii_value"):
        issues.append(
            SemanticValidationIssue(
                variant_id,
                SEMANTIC_MISMATCH,
                "record entity base_pii_value does not match the linked base's "
                "base_pii_value -- canonical identity mutated",
            )
        )

    scenario = base.get("scenario") or {}
    expected_domain = scenario.get("domain")
    expected_domain = expected_domain.upper() if isinstance(expected_domain, str) else expected_domain
    actual_domain = record.get("domain")
    if actual_domain != expected_domain:
        issues.append(
            SemanticValidationIssue(
                variant_id,
                SEMANTIC_MISMATCH,
                f"record.domain={actual_domain!r} does not match linked base "
                f"scenario.domain={expected_domain!r} -- scenario mutated",
            )
        )

    return issues


# --- Layer 3 of 4: semantic identity validation -----------------------------


def check_realized_value_identity(record: dict, base: dict) -> list:
    """For non-transliterable types: realized_pii_value == base_pii_value.
    For PERSON/ADDRESS: every condition except HI_DEVA_PII uses the base
    value unchanged; HI_DEVA_PII uses T07's deterministic transliteration.
    Reuses validators.spans.expected_realized_value (T09/T07's own oracle)
    -- never reimplements the transliteration selection logic."""
    variant_id = record.get("variant_id", "<unknown>")
    entities = record.get("entities") or []
    base_pii_list = base.get("pii") or []
    if not entities or not base_pii_list:
        return []

    entity = entities[0]
    base_pii = base_pii_list[0]
    expected = expected_realized_value(
        record.get("language"), base_pii.get("type"), base_pii.get("base_pii_value")
    )
    actual = entity.get("realized_pii_value")
    if actual != expected:
        return [
            SemanticValidationIssue(
                variant_id,
                SEMANTIC_MISMATCH,
                f"realized_pii_value identity not preserved: got={actual!r}, "
                f"expected={expected!r} (guidelines.md §4.4/§4.5)",
            )
        ]
    return []


# --- Layer 4 of 4: condition-specific Layer-3 semantic contract ------------
# (guidelines.md §13.6 for EN/IN_EN, §13.7 for the other five)


def check_condition_semantic_contract(record: dict, base: dict) -> list:
    """The text-content half of Layer 3: does the sentence itself assert the
    declared role? Scoped exactly to guidelines.md §13.6/§13.7 -- does not
    inspect T08's carrier templates and does not attempt sentence-structure
    parsing. A record outside the frozen scope (e.g. a perturbed EN record,
    for which no contract exists) is reported as neither PASS nor FAIL --
    this function returns no issue for it, since there is no rule to
    violate."""
    variant_id = record.get("variant_id", "<unknown>")
    language = record.get("language")
    text = record.get("text") or ""
    base_pii_list = base.get("pii") or []
    pii_type = base_pii_list[0].get("type") if base_pii_list else None
    canonical_text = base.get("canonical_text")

    if language == "EN":
        perturbation = record.get("perturbation") or {}
        in_scope = record.get("context") == "EXPLICIT" and perturbation.get("family") == "NONE"
        if in_scope and text != canonical_text:
            return [
                SemanticValidationIssue(
                    variant_id,
                    SEMANTIC_MISMATCH,
                    "EN text does not equal base.canonical_text (guidelines.md §13.6)",
                )
            ]
        return []

    if language == "IN_EN":
        if canonical_text not in text:
            return [
                SemanticValidationIssue(
                    variant_id,
                    SEMANTIC_MISMATCH,
                    "IN_EN text does not contain base.canonical_text (guidelines.md §13.7)",
                )
            ]
        return []

    if language in LATIN_LABEL_CONDITIONS:
        label = LATIN_LABEL.get(pii_type)
        if label is None:
            return [
                SemanticValidationIssue(
                    variant_id, SEMANTIC_MISMATCH, f"no frozen §13.7 label for type {pii_type!r}"
                )
            ]
        if label.lower() not in text.lower():
            return [
                SemanticValidationIssue(
                    variant_id,
                    ROLE_UNSUPPORTED_BY_TEXT,
                    f"required label {label!r} not found in text (guidelines.md §13.7)",
                )
            ]
        return []

    if language in DEVANAGARI_LABEL_CONDITIONS:
        label = DEVANAGARI_LABEL.get(pii_type)
        if label is None:
            return [
                SemanticValidationIssue(
                    variant_id, SEMANTIC_MISMATCH, f"no frozen §13.7 label for type {pii_type!r}"
                )
            ]
        if label not in text:
            return [
                SemanticValidationIssue(
                    variant_id,
                    ROLE_UNSUPPORTED_BY_TEXT,
                    f"required label {label!r} not found in text (guidelines.md §13.7)",
                )
            ]
        return []

    return [
        SemanticValidationIssue(
            variant_id, SEMANTIC_MISMATCH, f"unrecognized language condition: {language!r}"
        )
    ]


# --- Per-record orchestration -----------------------------------------------


def validate_record_semantic(record: dict, base_by_id: dict) -> list:
    """Fully self-contained per-record entry point: validates one arbitrary
    derived record against its linked base, independent of any other
    record. Combines all four layers; a base-level §13.5 finding is
    re-keyed to this record's own variant_id, since a record derived from a
    base with a wrong semantic_role is itself semantically invalid."""
    variant_id = record.get("variant_id", "<unknown>")
    base = base_by_id.get(record.get("base_id"))
    if base is None:
        return [
            SemanticValidationIssue(
                variant_id, SEMANTIC_MISMATCH, "base_id not found in base_instances.jsonl"
            )
        ]

    if base.get("base_kind") == "HARD_NEGATIVE":
        # guidelines.md §13.3/§13.4 (frozen well before this validator
        # existed): a hard negative declares no PII and therefore no
        # semantic_role to assert -- Layer 3 ("sentence uses the value in
        # the declared role") has no role to check for this record at all,
        # not a role it fails to assert. Without this guard,
        # check_condition_semantic_contract would look up a §13.7 label by
        # pii_type=None for the five non-EN/IN_EN conditions and report a
        # spurious SEMANTIC_MISMATCH on every hard-negative record in those
        # conditions -- a validator bug, not a property of the data.
        return []

    issues = []
    for issue in check_semantic_role_matches_type(base):
        issues.append(SemanticValidationIssue(variant_id, issue.reason, issue.detail))
    issues.extend(check_base_linkage(record, base))
    issues.extend(check_realized_value_identity(record, base))
    issues.extend(check_condition_semantic_contract(record, base))
    return issues


# --- Cross-record checks ----------------------------------------------------


def validate_hindi_matched_pair_semantics(records_for_base: list, base: dict) -> list:
    """For transliterable bases: HI_LATIN_PII and HI_DEVA_PII must share
    identical scenario/domain and identical carrier text outside the PII
    span (guidelines.md §4.11). Existence of both records is T09's job
    (validate_hindi_collapse_representation) -- if either is missing, this
    function has nothing to compare and skips rather than duplicating that
    check. Reads each record's own already-declared start/end; does not
    re-derive occurrence positions."""
    issues = []
    base_id = base.get("base_id", "<unknown>")
    base_pii_list = base.get("pii") or []
    pii_type = base_pii_list[0].get("type") if base_pii_list else None
    if pii_type not in TRANSLITERABLE_TYPES:
        return issues

    by_language = {
        r.get("language"): r
        for r in records_for_base
        if r.get("language") in ("HI_LATIN_PII", "HI_DEVA_PII")
    }
    latin, deva = by_language.get("HI_LATIN_PII"), by_language.get("HI_DEVA_PII")
    if latin is None or deva is None:
        return issues

    latin_entities = latin.get("entities") or []
    deva_entities = deva.get("entities") or []
    if not latin_entities or not deva_entities:
        return issues

    l_entity, d_entity = latin_entities[0], deva_entities[0]
    l_start, l_end = l_entity.get("start"), l_entity.get("end")
    d_start, d_end = d_entity.get("start"), d_entity.get("end")
    if not all(isinstance(v, int) for v in (l_start, l_end, d_start, d_end)):
        return issues  # malformed spans are T09's job

    l_text, d_text = latin.get("text", ""), deva.get("text", "")
    l_prefix, l_suffix = l_text[:l_start], l_text[l_end:]
    d_prefix, d_suffix = d_text[:d_start], d_text[d_end:]
    if (l_prefix, l_suffix) != (d_prefix, d_suffix):
        issues.append(
            SemanticValidationIssue(
                base_id,
                SEMANTIC_MISMATCH,
                "HI_LATIN_PII / HI_DEVA_PII carrier text diverges outside the PII "
                "span (guidelines.md §4.11 matched-variant invariant)",
            )
        )

    if latin.get("domain") != deva.get("domain"):
        issues.append(
            SemanticValidationIssue(
                base_id, SEMANTIC_MISMATCH, "HI_LATIN_PII / HI_DEVA_PII domain diverges"
            )
        )

    return issues


def validate_collapsed_hindi_semantics(records_for_base: list, base: dict) -> list:
    """For non-transliterable types: the single collapsed HI_LATIN_PII
    record must carry hi_variant_collapsed=true and preserve semantic
    identity (realized_pii_value == base_pii_value, since these types are
    never transliterated at all). Existence of the collapsed record is
    T09's job -- if it is missing, this function skips."""
    issues = []
    base_pii_list = base.get("pii") or []
    pii_type = base_pii_list[0].get("type") if base_pii_list else None
    if pii_type not in NON_TRANSLITERABLE_TYPES:
        return issues

    collapsed = next(
        (r for r in records_for_base if r.get("language") == "HI_LATIN_PII"), None
    )
    if collapsed is None:
        return issues

    variant_id = collapsed.get("variant_id", "<unknown>")
    if collapsed.get("hi_variant_collapsed") is not True:
        issues.append(
            SemanticValidationIssue(
                variant_id,
                SEMANTIC_MISMATCH,
                "non-transliterable HI_LATIN_PII record missing hi_variant_collapsed=true",
            )
        )

    entities = collapsed.get("entities") or []
    if entities and base_pii_list:
        realized = entities[0].get("realized_pii_value")
        expected = base_pii_list[0].get("base_pii_value")
        if realized != expected:
            issues.append(
                SemanticValidationIssue(
                    variant_id,
                    SEMANTIC_MISMATCH,
                    f"collapsed record's realized value {realized!r} != "
                    f"base_pii_value {expected!r} -- semantic identity not preserved",
                )
            )

    return issues


# --- Top-level orchestrator --------------------------------------------------


def validate_dataset(records: list, bases: list) -> dict:
    """Read-only: never mutates `records` or `bases`, never writes to disk."""
    base_by_id = {b["base_id"]: b for b in bases}
    issues = []

    for record in records:
        issues.extend(validate_record_semantic(record, base_by_id))

    by_base = {}
    for record in records:
        by_base.setdefault(record["base_id"], []).append(record)
    for base_id, recs in by_base.items():
        base = base_by_id.get(base_id)
        if base is not None:
            issues.extend(validate_hindi_matched_pair_semantics(recs, base))
            issues.extend(validate_collapsed_hindi_semantics(recs, base))

    invalid_variant_ids = {i.variant_id for i in issues}
    return {
        "total_records": len(records),
        "valid_records": len(records)
        - len(invalid_variant_ids & {r["variant_id"] for r in records}),
        "issues": issues,
    }
