"""Governance tests for OQ-046 (guidelines.md v0.16, decision 48) -- the
hard_negative_decoy construction-ground-truth architecture decision.

These prove the governing-document text itself, distinct from
tests/test_schemas.py (schema shape) and tests/test_base_kind_invariant.py
(the cross-field invariant): that the decision is recorded, that pii[]/
entities[]/distractors[] rules are explicitly stated as unchanged, that RNG
replay is recorded as rejected, and that no implementation boundary was
crossed while freezing this architecture.
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


def _section(heading: str) -> str:
    start = GUIDELINES.index(heading)
    rest = GUIDELINES[start + len(heading) :]
    next_heading = re.search(r"\n### \d|\n## \d", rest)
    end = start + len(heading) + (next_heading.start() if next_heading else len(rest))
    return _normalize(GUIDELINES[start:end])


def test_guidelines_v0_16_changelog_entry_still_says_what_it_always_said():
    """This file's own decision (OQ-046) landed at v0.16. A later, separate
    governance turn (OQ-047) legitimately moved the version further --
    checking the *current* number here would go stale every time that
    happens, so this checks the durable fact instead: the v0.16 CHANGELOG
    entry itself, frozen at the time OQ-046 was resolved, still says what it
    always said."""
    changelog = (ROOT / "annotation" / "CHANGELOG.md").read_text(encoding="utf-8")
    start = changelog.index("## v0.16")
    end = changelog.index("## v0.15")
    v0_16_entry = changelog[start:end]
    assert "OQ-046" in v0_16_entry


def test_project_spec_guidelines_pointer_is_never_behind_0_16():
    """The pointer must have moved to at least 0.16 by the time OQ-046 was
    resolved, and must never regress below it on any later governance turn."""
    block = SPEC[SPEC.index("## 35. Version") :]
    match = re.search(r"guidelines_version:\s*(\d+)\.(\d+)", block)
    assert match, "no guidelines_version pointer found in PROJECT_SPEC.md §35"
    major, minor = int(match.group(1)), int(match.group(2))
    assert (major, minor) >= (0, 16)


def test_section_13_12_exists_and_resolves_oq_046():
    section = _section("### 13.12 Hard-negative construction ground truth")
    assert "resolves OQ-046" in section


def test_section_states_pii_stays_empty_unchanged():
    section = _section("### 13.12 Hard-negative construction ground truth")
    assert "pii[]` stays empty" in section
    assert "decision 16" in section


def test_section_states_entities_and_distractors_stay_derived_record_only():
    section = _section("### 13.12 Hard-negative construction ground truth")
    assert "stay derived-record-only" in section
    assert "must not, gain a" in section


def test_section_states_why_persisted_metadata_is_necessary():
    section = _section("### 13.12 Hard-negative construction ground truth")
    assert "persisted decoy metadata is necessary" in section


def test_section_explicitly_rejects_rng_replay():
    section = _section("### 13.12 Hard-negative construction ground truth")
    assert "RNG replay was rejected" in section
    assert "T08 reads only" in section


def test_section_describes_how_phase_2_will_use_the_field():
    section = _section("### 13.12 Hard-negative construction ground truth")
    assert "How Phase 2 will use this field" in section
    assert "design note, not an implementation commitment" in section


def test_section_states_schema_vs_validator_boundary_is_consistency_not_incapacity():
    """The section must not claim JSON Schema is incapable of expressing the
    conditional -- only that using it would break an established convention."""
    section = _section("### 13.12 Hard-negative construction ground truth")
    assert "express this conditional" in section
    assert "not by an" in section and "if" in section.lower()


def test_decision_48_is_recorded():
    assert "48. **`hard_negative_decoy` is added" in GUIDELINES


def test_oq_046_is_marked_resolved():
    match = re.search(r"## OQ-046\b.*$", OPEN_QUESTIONS, re.MULTILINE)
    assert match and "— **RESOLVED" in match.group(0)


def test_oq_046_records_both_candidates_and_the_rejection_reason():
    start = OPEN_QUESTIONS.index("## OQ-046")
    body = _normalize(OPEN_QUESTIONS[start:])
    assert "Persist construction metadata on the base instance" in body
    assert "Re-derive it from `base_id` + RNG replay" in body
    assert "explicitly rejected" in body


# --- Boundary: this turn is governance + schema only -------------------------
#
# generators/hard_negatives.py did not exist as of this turn -- that was
# true when this file was written and is not re-asserted here, since a
# later, explicitly-authorized T11 Phase 1 turn correctly created it. What
# remains checkable, and still matters, is that no hard-negative *data* came
# from this particular (governance + schema only) turn.


def test_no_hard_negative_base_instances_exist_on_disk():
    """This decision authorizes a schema field, not data. No base with
    base_kind == HARD_NEGATIVE should exist in the canonical dataset yet."""
    bases = [
        json.loads(line)
        for line in (ROOT / "data" / "raw" / "base_instances.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert len(bases) == 100
    assert all(b["base_kind"] == "POSITIVE" for b in bases)
    assert all("hard_negative_decoy" not in b for b in bases)


def test_derived_records_file_unchanged_in_count():
    records = [
        json.loads(line)
        for line in (ROOT / "data" / "generated" / "language_realizations.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert len(records) == 624


def test_validators_spans_and_semantic_are_unmodified_in_scope():
    for name in ("spans.py", "semantic.py"):
        source = (ROOT / "validators" / name).read_text(encoding="utf-8")
        assert "hard_negative_decoy" not in source
