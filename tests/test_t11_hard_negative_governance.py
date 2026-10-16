"""Governance tests for OQ-042 through OQ-045 (guidelines.md v0.15, decisions
42-47) -- the hard-negative decoy-class construction rules, the 20-base
quota, the frozen `context` value, and the six-realization/120-record
cardinality decision.

OQ-042's two classes have DIFFERENT final statuses and this file tests that
distinction directly: `HANDLE_SHAPE` is resolved constructively (a real
construction rule now exists, grounded in generators/pii/email.py's actual
vocabulary); `ORG_AS_PERSON` is resolved by DEFERRAL -- explicitly excluded
from Pilot v0.1, with no grammar invented for it. A test asserting "OQ-042
resolved" must not be satisfied by `ORG_AS_PERSON` having a fabricated rule;
none exists, and these tests prove none exists.

These tests also prove the boundary this and prior T11 governance turns must
not cross: no generators/hard_negatives.py, no change to validators/spans.py
or validators/semantic.py, no dataset mutation, no hard-negative records of
any kind on disk yet.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDELINES = (ROOT / "annotation" / "guidelines.md").read_text(encoding="utf-8")
SPEC = (ROOT / "PROJECT_SPEC.md").read_text(encoding="utf-8")
OPEN_QUESTIONS = (ROOT / "annotation" / "open_questions.md").read_text(encoding="utf-8")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _section(heading: str, doc: str = GUIDELINES) -> str:
    start = doc.index(heading)
    rest = doc[start + len(heading) :]
    next_heading = re.search(r"\n### \d|\n## \d", rest)
    end = start + len(heading) + (next_heading.start() if next_heading else len(rest))
    return _normalize(doc[start:end])


# --- Version state -----------------------------------------------------------


def test_guidelines_version_is_at_least_0_15():
    """This file's own decisions -- OQ-042 (HANDLE_SHAPE/ORG_AS_PERSON) and
    OQ-044 (six-condition cardinality), plus OQ-043's quota redistribution --
    landed at v0.15 (OQ-045 landed earlier, at v0.14). A later, separate
    governance turn (OQ-046) legitimately moved the version further --
    checking the *current* number here would go stale every time that
    happens, so this checks the durable fact instead: the v0.15 CHANGELOG
    entry itself, frozen at the time these OQs were resolved, still says
    what it always said."""
    changelog = (ROOT / "annotation" / "CHANGELOG.md").read_text(encoding="utf-8")
    start = changelog.index("## v0.15")
    end = changelog.index("## v0.14")
    v0_15_entry = changelog[start:end]
    for oq in ("OQ-042", "OQ-043", "OQ-044"):
        assert oq in v0_15_entry


def test_project_spec_guidelines_pointer_is_never_behind_0_15():
    """The pointer must have moved to at least 0.15 by the time these OQs
    were resolved, and must never regress below it on any later governance
    turn."""
    block = SPEC[SPEC.index("## 35. Version") :]
    match = re.search(r"guidelines_version:\s*(\d+)\.(\d+)", block)
    assert match, "no guidelines_version pointer found in PROJECT_SPEC.md §35"
    major, minor = int(match.group(1)), int(match.group(2))
    assert (major, minor) >= (0, 15)


# --- OQ-042: NUMERIC_SHAPE / ALNUM_SHAPE / NAME_AS_PLACE / PARTIAL_PII ------
# (unchanged from v0.14, re-verified against the real source they reuse)


def test_numeric_shape_reuses_the_actual_frozen_phone_and_aadhaar_regexes():
    section = _section("### 13.8 Hard-negative decoy-class construction rules")
    from validators.structural import _AADHAAR_RE, _PHONE_RE

    assert _PHONE_RE.pattern == r"^[6789][0-9]{9}$"
    assert _AADHAAR_RE.pattern == r"^[0-9]{12}$"
    assert r"^[6789][0-9]{9}$" in section
    assert "ORDER_REFERENCE" in section


def test_alnum_shape_reuses_the_actual_frozen_pan_regex():
    section = _section("### 13.8 Hard-negative decoy-class construction rules")
    from validators.structural import _PAN_RE

    assert _PAN_RE.pattern == r"^[A-Z]{5}[0-9]{4}[A-Z]$"
    assert r"^[A-Z]{5}[0-9]{4}[A-Z]$" in section
    assert "REFERENCE_CODE" in section


def test_partial_pii_reuses_the_actual_frozen_12_digit_format():
    section = _section("### 13.8 Hard-negative decoy-class construction rules")
    from validators.structural import _BANK_ACCOUNT_RE

    assert _BANK_ACCOUNT_RE.pattern == r"^[0-9]{12}$"
    assert "XXXX XXXX 4321" in section
    assert "MASKED_IDENTIFIER" in section


def test_name_as_place_reuses_the_actual_frozen_person_given_names():
    section = _section("### 13.8 Hard-negative decoy-class construction rules")
    from generators.pii.person import _GIVEN_NAMES

    assert "Rahul" in _GIVEN_NAMES
    assert _GIVEN_NAMES[0] == "Rahul"
    assert "_GIVEN_NAMES" in section
    assert "Rahul Nagar" in section
    assert "LOCATION" in section
    assert "LOCALITY" in section


# --- OQ-042: HANDLE_SHAPE -- resolved constructively (v0.15) ----------------


def test_handle_shape_reuses_the_actual_frozen_email_vocabulary():
    """Required check 1: HANDLE_SHAPE is grounded in the real
    generators/pii/email.py vocabulary, not a re-typed duplicate."""
    section = _section("### 13.8 Hard-negative decoy-class construction rules")
    from generators.pii.email import _DOMAIN_LABELS, _LOCAL_PART_WORDS

    assert "rahul" in _LOCAL_PART_WORDS
    assert "corp" in _DOMAIN_LABELS
    assert "_LOCAL_PART_WORDS" in section
    assert "_DOMAIN_LABELS" in section
    assert "email.py" in section


def test_handle_shape_omits_the_reserved_tld():
    """Required check 2: a HANDLE_SHAPE value must fail both EMAIL's and
    UPI_ID's frozen structural regexes precisely because the reserved TLD is
    omitted -- verified by direct regex evaluation, not asserted."""
    section = _section("### 13.8 Hard-negative decoy-class construction rules")
    assert "TLD omitted" in section or "reserved TLD" in section and "omitted" in section

    from validators.structural import _EMAIL_RE, _UPI_ID_RE

    example_value = "rahul4521@corp"
    assert not _EMAIL_RE.match(example_value)
    assert not _UPI_ID_RE.match(example_value)


def test_handle_shape_does_not_change_emails_own_structural_rule():
    section = _section("### 13.8 Hard-negative decoy-class construction rules")
    assert "does not change EMAIL's own structural rule" in section
    from validators.structural import _EMAIL_RE

    # EMAIL's own frozen rule is untouched: a real EMAIL value still passes it.
    assert _EMAIL_RE.match("rahul4521@corp.test")


def test_oq_042_handle_shape_is_marked_resolved_constructively():
    start = OPEN_QUESTIONS.index("## OQ-042")
    end = OPEN_QUESTIONS.index("## OQ-043")
    body = _normalize(OPEN_QUESTIONS[start:end])
    assert "`HANDLE_SHAPE` → A (freeze the current candidate)" in body
    assert "Frozen exactly as presented" in body


# --- OQ-042: ORG_AS_PERSON -- resolved by deferral, no grammar invented ------


def test_org_as_person_is_explicitly_deferred_not_constructed():
    """Required check 3: ORG_AS_PERSON must read as deferred/excluded, never
    as if it had been quietly resolved."""
    section = _section("### 13.8 Hard-negative decoy-class construction rules")
    assert "is deferred from Pilot v0.1, not resolved" in section
    assert "ORG_AS_PERSON" in section


def test_org_as_person_has_no_invented_grammar_anywhere():
    """Required check 4: no value shape, actual_role, surface_type, or
    canonical_text template exists for ORG_AS_PERSON -- it must not appear as
    a row in §13.8's construction table, only in the deferral prose."""
    section = _section("### 13.8 Hard-negative decoy-class construction rules")
    table_start = section.index("| Class | Value shape")
    table_end = section.index("**`HANDLE_SHAPE` reuses")
    table = section[table_start:table_end]
    assert "ORG_AS_PERSON" not in table


def test_oq_042_org_as_person_is_marked_resolved_by_deferral():
    start = OPEN_QUESTIONS.index("## OQ-042")
    end = OPEN_QUESTIONS.index("## OQ-043")
    body = _normalize(OPEN_QUESTIONS[start:end])
    assert "`ORG_AS_PERSON` → C (remove/defer this class)" in body
    assert "Not resolved constructively" in body


def test_oq_042_heading_distinguishes_the_two_final_statuses():
    match = re.search(r"## OQ-042\b.*$", OPEN_QUESTIONS, re.MULTILINE)
    assert match
    heading = match.group(0)
    assert "HANDLE_SHAPE" in heading and "constructively" in heading
    assert "ORG_AS_PERSON" in heading and "deferral" in heading


def test_scope_consequence_for_the_paper_is_stated():
    section = _section("### 13.8 Hard-negative decoy-class construction rules")
    assert "Scope consequence for the paper" in section
    assert "five of the six" in section


# --- OQ-043: quota, redistributed after ORG_AS_PERSON's deferral ------------


DECOY_QUOTA = {
    "NUMERIC_SHAPE": 5,
    "ALNUM_SHAPE": 5,
    "NAME_AS_PLACE": 4,
    "HANDLE_SHAPE": 3,
    "ORG_AS_PERSON": 0,
    "PARTIAL_PII": 3,
}


def test_decoy_quota_sums_to_twenty():
    assert sum(DECOY_QUOTA.values()) == 20


def test_decoy_quota_covers_all_six_schema_enum_values():
    """The schema's decoy_class enum is untouched -- ORG_AS_PERSON is still a
    valid taxonomy value, just allocated zero bases in this pilot."""
    schema = json.loads((ROOT / "schemas" / "example.schema.json").read_text(encoding="utf-8"))
    assert set(schema["$defs"]["decoy_class"]["enum"]) == set(DECOY_QUOTA)


def test_section_13_9_matches_the_redistributed_quota():
    section = _section("### 13.9 Hard-negative decoy-class distribution")
    assert "redistributed v0.15" in section
    for decoy_class, count in DECOY_QUOTA.items():
        assert re.search(rf"`{decoy_class}`\s*\|\s*{count}\s*\|", section), decoy_class
    assert "**20**" in section


def test_section_13_9_marks_org_as_person_deferred_in_the_table_itself():
    section = _section("### 13.9 Hard-negative decoy-class distribution")
    assert "deferred, excluded from Pilot v0.1" in section


def test_oq_043_is_marked_resolved():
    match = re.search(r"## OQ-043\b.*$", OPEN_QUESTIONS, re.MULTILINE)
    assert match and "— **RESOLVED" in match.group(0)


# --- OQ-045: context value (unchanged) ---------------------------------------


def test_section_13_10_freezes_explicit_context():
    section = _section("### 13.10 Hard-negative `context` value")
    assert "resolves OQ-045" in section
    assert 'context: "EXPLICIT"' in section
    assert "Not a redesign" in section


def test_oq_045_is_marked_resolved():
    match = re.search(r"## OQ-045\b.*$", OPEN_QUESTIONS, re.MULTILINE)
    assert match and "— **RESOLVED" in match.group(0)


# --- OQ-044: resolved, six realizations, 120 records -------------------------


def test_oq_044_is_now_resolved():
    match = re.search(r"## OQ-044\b.*$", OPEN_QUESTIONS, re.MULTILINE)
    assert match and "— **RESOLVED" in match.group(0)


def test_oq_044_reconciliation_history_is_preserved():
    """The original three-reading reconciliation table must survive as the
    historical record of what was considered, even though a decision was
    later made."""
    start = OPEN_QUESTIONS.index("## OQ-044")
    end = OPEN_QUESTIONS.index("## OQ-045")
    body = _normalize(OPEN_QUESTIONS[start:end])
    assert "Reconciliation against the exact wording" in body
    assert "140" in body and "120" in body and "~60" in body


def test_oq_044_records_the_human_decision_for_option_b():
    start = OPEN_QUESTIONS.index("## OQ-044")
    end = OPEN_QUESTIONS.index("## OQ-045")
    body = _normalize(OPEN_QUESTIONS[start:end])
    assert "the user selected **B" in body
    assert "deliberate extension of §8.1's rationale" in body or "deliberate extension" in body


def test_section_13_11_freezes_exactly_six_realizations():
    """Required check 5."""
    section = _section("### 13.11 Hard-negative language-condition count")
    assert "resolves OQ-044" in section
    for language in ("EN", "IN_EN", "ROM_HI", "HINGLISH", "INFORMAL_HINGLISH"):
        assert f"\n{language}\n" in GUIDELINES[GUIDELINES.index("### 13.11") :][:600] or language in section
    assert "exactly" in section and "six" in section


def test_section_13_11_does_not_list_hi_latin_pii_and_hi_deva_pii_as_separate_frozen_realizations():
    """Required check 6: the collapsed Hindi realization must occur exactly
    once. The frozen enumerated block itself (not the surrounding prose,
    which legitimately discusses both codes to explain why they collapse)
    must list six items with no separate HI_LATIN_PII/HI_DEVA_PII entries."""
    block_start = GUIDELINES.index("```\nEN\nIN_EN\nROM_HI\nHINGLISH\nINFORMAL_HINGLISH")
    block_end = GUIDELINES.index("```", block_start + 3)
    frozen_block = GUIDELINES[block_start:block_end]
    lines = [line.strip() for line in frozen_block.splitlines() if line.strip() and line.strip() != "```"]
    assert lines == [
        "EN",
        "IN_EN",
        "ROM_HI",
        "HINGLISH",
        "INFORMAL_HINGLISH",
        "one collapsed Hindi realization",
    ]
    assert "HI_LATIN_PII" not in frozen_block
    assert "HI_DEVA_PII" not in frozen_block

    section = _section("### 13.11 Hard-negative language-condition count")
    assert "one collapsed Hindi realization" in section
    assert "hi_variant_collapsed" in section


def test_section_13_11_extension_is_explicitly_labeled_as_such():
    section = _section("### 13.11 Hard-negative language-condition count")
    assert "deliberate extension" in section
    assert "not a claim that §8.1" in section or "not a claim" in section


def test_planned_cardinality_20_bases_times_6_is_120():
    """Required check 7."""
    section = _section("### 13.11 Hard-negative language-condition count")
    assert 20 * 6 == 120
    assert "120" in section


def test_planned_combined_totals_match_120_bases_744_derived_864_combined():
    """Required check 8. Purely arithmetic -- no dataset file is read or
    changed by this test."""
    existing_positive_bases = 100
    new_hard_negative_bases = 20
    total_bases = existing_positive_bases + new_hard_negative_bases
    assert total_bases == 120

    existing_positive_derived = 624
    hard_negative_derived = new_hard_negative_bases * 6
    total_derived = existing_positive_derived + hard_negative_derived
    assert total_derived == 744

    combined = total_bases + total_derived
    assert combined == 864


# --- Boundary: no implementation happened this turn or any prior T11 turn ---
#
# Required check 10 (no generators/hard_negatives.py) applied to this turn's
# own scope (OQ-042/043/044 governance only) -- it did not exist then. A
# later, explicitly-authorized T11 Phase 1 turn correctly created it, so
# that specific assertion is retired here rather than left to fail forever.


# Required check 11 (T09/T10 must not have been touched) applied to this
# turn's own scope (OQ-042/043/044 governance only) -- true when written. A
# later, explicitly-authorized T11 Phase 2 pre-audit turn correctly extended
# both validators to handle HARD_NEGATIVE records (guidelines.md §13.3's
# empty-entities rule predates both validators), so that specific assertion
# is retired here rather than left to fail forever. See
# tests/test_span_validator.py and tests/test_semantic_validator.py's own
# HARD_NEGATIVE-compatibility regression tests for the current, correct
# coverage of that change.


def test_no_evaluation_layer_files_were_introduced():
    """This turn is governance-only for T11; it must not have also slipped
    in evaluation-layer implementation (out of scope per OQ-034)."""
    for name in ("training", "experiments", "application"):
        directory = ROOT / name
        if directory.exists():
            entries = [p for p in directory.iterdir() if p.name != "__pycache__"]
            assert all(p.name == ".gitkeep" for p in entries), name


def test_dataset_files_unchanged_in_count():
    """Required check 9."""
    bases = [
        json.loads(line)
        for line in (ROOT / "data" / "raw" / "base_instances.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    records = [
        json.loads(line)
        for line in (ROOT / "data" / "generated" / "language_realizations.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert len(bases) == 100
    assert len(records) == 624
    assert all(b["base_kind"] == "POSITIVE" for b in bases)
