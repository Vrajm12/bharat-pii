"""Governance tests for OQ-038 through OQ-041 (PROJECT_SPEC.md v1.3) -- the four
implementation-adjacent gaps found while producing the T11 evaluation-layer
design report: the baseline adapter interface, prediction persistence format,
malformed-prediction log scope, and evaluation-report artifact format.

These tests prove two things, and two things only:

1. The four decisions were actually written into PROJECT_SPEC.md, each
   carrying its own "freezes X, not the implementation" caveat -- not just
   asserted in a chat response.
2. Resolving them did NOT cross OQ-034's boundary: no evaluation-layer code
   exists as a result. This file does not, and must not, import or exercise
   any benchmark/baselines code, because none was created and none may be
   created by this governance turn.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = (ROOT / "PROJECT_SPEC.md").read_text(encoding="utf-8")
GUIDELINES = (ROOT / "annotation" / "guidelines.md").read_text(encoding="utf-8")
OPEN_QUESTIONS = (ROOT / "annotation" / "open_questions.md").read_text(encoding="utf-8")


# --- PROJECT_SPEC.md version state ------------------------------------------


def test_project_spec_header_declares_version_1_3():
    assert "**Version:** 1.3" in SPEC


def test_project_spec_header_supersedes_1_2():
    header = SPEC[: SPEC.index("## 0. How to read this document")]
    assert "**Supersedes:** v1.2" in header


def test_project_spec_section_35_version_block_matches_header():
    block = SPEC[SPEC.index("## 35. Version") :]
    assert "spec_version:        1.3" in block
    assert "supersedes:          1.2" in block


def test_changes_in_v1_3_section_exists_and_names_the_oq_range():
    assert "### Changes in v1.3" in SPEC
    section = SPEC[SPEC.index("### Changes in v1.3") :]
    section = section[: section.index("---")]
    assert "OQ-038 through OQ-041" in section


def test_guidelines_v0_13_changelog_entry_does_not_mention_oq_038_041():
    """This turn (OQ-038-041, PROJECT_SPEC.md v1.3) resolves PROJECT_SPEC.md-owned
    questions only -- it must not be why guidelines.md's own version ever moved.
    A later, separate governance turn legitimately bumped guidelines.md again for
    unrelated reasons (OQ-042/043/045, v0.14) -- checking the *current* version
    number would break on that legitimate, later change, so this checks the
    durable fact instead: the v0.13 CHANGELOG entry itself, frozen at the time
    of the OQ-038-041 turn, was never about those four OQs."""
    changelog = (ROOT / "annotation" / "CHANGELOG.md").read_text(encoding="utf-8")
    start = changelog.index("## v0.13")
    end = changelog.index("## v0.12")
    v0_13_entry = changelog[start:end]
    for oq in ("OQ-038", "OQ-039", "OQ-040", "OQ-041"):
        assert oq not in v0_13_entry


# --- Each new subsection exists and carries its own non-implementation caveat


def _normalize(text: str) -> str:
    """Collapse whitespace runs (including markdown soft-wrap newlines) to a
    single space, so a multi-line phrase can be checked as one substring."""
    return re.sub(r"\s+", " ", text)


def _section(spec_text: str, heading: str) -> str:
    """Extract one ### subsection's raw text, normalized so a phrase that
    happens to fall across a markdown soft-wrap line break can still be
    checked as a single substring."""
    start = spec_text.index(heading)
    rest = spec_text[start + len(heading) :]
    next_heading = re.search(r"\n### \d", rest)
    end = start + len(heading) + (next_heading.start() if next_heading else len(rest))
    return _normalize(spec_text[start:end])


def test_section_20_7_baseline_adapter_interface_freezes_shape_not_implementation():
    section = _section(SPEC, "### 20.7 Baseline adapter interface")
    assert "resolves OQ-038" in section
    assert "predict(text: str) -> list[Prediction]" in section
    assert "freezes the interface shape, not the implementation" in section
    assert "No `Prediction`" in section and "no `BaselineAdapter` base class" in section


def test_section_20_8_prediction_persistence_freezes_format_not_implementation():
    section = _section(SPEC, "### 20.8 Prediction persistence")
    assert "resolves OQ-039" in section
    assert "JSONL" in section
    assert "freezes the artifact format, not the implementation" in section


def test_section_20_9_malformed_prediction_log_excludes_data_rejected():
    section = _normalize(_section(SPEC, "### 20.9 Malformed-prediction log scope"))
    assert "resolves OQ-040" in section
    assert "it is not into `data/rejected/`" in section
    assert "`data/rejected/` itself is unchanged" in section


def test_section_20_10_report_format_freezes_format_not_report():
    section = _section(SPEC, "### 20.10 Evaluation report artifact format")
    assert "resolves OQ-041" in section
    assert "JSON file per experiment" in section
    assert "freezes a file format, not a report" in section


def test_section_20_11_explicitly_reaffirms_oq_034_boundary():
    section = _section(SPEC, "### 20.11 Scope note")
    assert "OQ-034" in section
    assert "not authorized under the current Pilot v0.1 milestone" in section
    assert "unchanged and unaffected by this revision" in section


# --- open_questions.md marks all four resolved -------------------------------


def test_oq_038_through_041_are_marked_resolved():
    for oq in ("OQ-038", "OQ-039", "OQ-040", "OQ-041"):
        heading_pattern = re.compile(rf"## {oq}\b.*$", re.MULTILINE)
        match = heading_pattern.search(OPEN_QUESTIONS)
        assert match, f"{oq} heading not found"
        assert "RESOLVED" in match.group(0), f"{oq} heading does not say RESOLVED"


def test_governance_note_common_to_oq_038_041_exists():
    assert "Governance note common to OQ-038" in OPEN_QUESTIONS


# --- The actual boundary: no evaluation-layer code exists --------------------
#
# benchmark/, baselines/, training/, experiments/, and application/ exist as
# empty directories (a bare `.gitkeep` each) -- part of T01's repository
# skeleton per PROJECT_SPEC.md §25/§58, not evaluation-layer implementation.
# The boundary this governance turn must not cross is CONTENT, not the
# directory's mere existence.


def _only_contains_gitkeep(dir_name: str) -> bool:
    directory = ROOT / dir_name
    if not directory.exists():
        return True
    entries = [p for p in directory.iterdir() if p.name != "__pycache__"]
    return all(p.name == ".gitkeep" for p in entries)


def test_training_experiments_and_application_directories_hold_no_implementation():
    for name in ("training", "experiments", "application"):
        assert _only_contains_gitkeep(name), f"{name}/ must hold no code yet (OQ-034)"


def test_no_concrete_baseline_or_experiments_exist_yet():
    assert not (ROOT / "training" / "train.py").exists()
    assert not (ROOT / "experiments" / "E01_baseline.py").exists()


# --- Dataset/guideline files this turn must not have touched -----------------


def test_data_rejected_directory_semantics_unchanged():
    """PROJECT_SPEC.md §15.1's own text (the thing OQ-040 explicitly declined
    to repurpose) must still say what it always said."""
    section_start = SPEC.index("### 15.1 Rejection log")
    section = _normalize(SPEC[section_start : section_start + 400])
    assert "what the generator cannot produce" in section


def test_base_and_derived_dataset_files_unchanged_in_count():
    import json

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
