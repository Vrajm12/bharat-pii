"""Governance tests for the T11 Phase 2 pre-implementation investigation of
OQ-047 (hard-negative non-EN/IN_EN realization content) and OQ-048
(distractor-span validation).

OQ-047 was resolved in a later turn than the one that created this file
(guidelines.md v0.17, decision 49) -- the tests below that asserted it was
still open have been updated to assert the resolution instead, since that
is a correction of this file's own premise by an explicitly-authorized
governance turn, not a regression. OQ-048 remains unresolved, and those
tests are unchanged.

No generator or derived-record code exists as a result of either turn. This
file does not import or exercise generators/hard_negatives.py's language-
realization behavior, because none exists yet.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDELINES = (ROOT / "annotation" / "guidelines.md").read_text(encoding="utf-8")
OPEN_QUESTIONS = (ROOT / "annotation" / "open_questions.md").read_text(encoding="utf-8")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _section_13_13() -> str:
    start = GUIDELINES.index("### 13.13 Hard-negative realization inventory")
    end = GUIDELINES.index("## 14. Adversarial variants")
    return GUIDELINES[start:end]


def test_oq_047_is_now_resolved():
    match = re.search(r"## OQ-047\b.*$", OPEN_QUESTIONS, re.MULTILINE)
    assert match and "— **RESOLVED" in match.group(0)


def test_oq_048_is_still_unresolved():
    match = re.search(r"## OQ-048\b.*$", OPEN_QUESTIONS, re.MULTILINE)
    assert match and match.group(0).strip().endswith("**UNRESOLVED**")


def test_oq_047_records_all_five_candidates_evaluated():
    start = OPEN_QUESTIONS.index("## OQ-047")
    end = OPEN_QUESTIONS.index("## OQ-048")
    body = _normalize(OPEN_QUESTIONS[start:end])
    for candidate in (
        "Candidate A", "Candidate B", "Candidate C", "Candidate D", "Candidate E",
    ):
        assert candidate in body


def test_oq_047_records_the_partial_pii_near_miss_and_its_eventual_resolution():
    """The audit found PARTIAL_PII constructible from zero new vocabulary but
    did not silently promote that to a resolution -- the eventual human
    decision must still distinguish 'words already frozen' from 'template
    frozen now', not erase that distinction once approved."""
    start = OPEN_QUESTIONS.index("## OQ-047")
    end = OPEN_QUESTIONS.index("## OQ-048")
    body = _normalize(OPEN_QUESTIONS[start:end])
    assert "PARTIAL_PII" in body and "zero new" in body
    assert "not adopted as resolved" in body  # the original audit's own wording, preserved
    assert "Human decision, 2026-08-25" in body
    assert "closing the exact gap the first audit pass identified" in body


def test_oq_047_candidate_b_rejection_cites_the_semantic_constraint():
    start = OPEN_QUESTIONS.index("## OQ-047")
    end = OPEN_QUESTIONS.index("## OQ-048")
    body = _normalize(OPEN_QUESTIONS[start:end])
    assert "falsely claim the distractor" in body
    assert "HANDLE_SHAPE" in body and "EMAIL" in body


def test_oq_048_re_audit_addresses_every_sub_question():
    start = OPEN_QUESTIONS.index("## OQ-048")
    body = _normalize(OPEN_QUESTIONS[start:])
    required_phrases = [
        "Can T09's existing span contract be extended",
        "Does the schema already make",
        "Do guidelines.md §18 or PROJECT_SPEC.md §15.1",
        "Does a distractor span mismatch have an existing rejection reason",
        "Would adding distractor validation merely apply an existing invariant",
    ]
    for phrase in required_phrases:
        assert phrase in body, phrase


def test_oq_048_conclusion_is_a_new_requirement_not_an_existing_one():
    start = OPEN_QUESTIONS.index("## OQ-048")
    body = _normalize(OPEN_QUESTIONS[start:])
    assert "requires a genuinely new" in body
    assert "it is not already implied" in body


def test_guidelines_section_4_4_scopes_the_span_match_rule_to_realized_pii_value():
    """The literal textual basis for OQ-048's conclusion -- confirms the
    rule really is entity-specific, not a paraphrase."""
    section_start = GUIDELINES.index("### 4.4 Required schema consequence")
    section = GUIDELINES[section_start : section_start + 1200]
    assert "text[start:end] == realized_pii_value" in section
    assert "distractor" not in section.lower()


def test_no_hard_negative_derived_record_exists_anywhere():
    """This turn is investigation only -- no Phase 2 output of any kind."""
    generated_path = ROOT / "data" / "generated" / "language_realizations.jsonl"
    text = generated_path.read_text(encoding="utf-8")
    assert "NEG_" not in text


def test_dataset_counts_remain_exactly_as_before_this_turn():
    import json

    positive_bases = [
        json.loads(line)
        for line in (ROOT / "data" / "raw" / "base_instances.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    hard_negative_bases = [
        json.loads(line)
        for line in (ROOT / "data" / "raw" / "hard_negative_bases.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    derived_records = [
        json.loads(line)
        for line in (ROOT / "data" / "generated" / "language_realizations.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert len(positive_bases) == 100
    assert len(hard_negative_bases) == 20
    assert len(derived_records) == 624


def test_guidelines_version_reflects_the_oq_047_resolution():
    """OQ-047 was resolved in this later turn -- guidelines.md must have
    moved to at least v0.17, not stayed at v0.16."""
    block = GUIDELINES[GUIDELINES.index("## 22. Version") :]
    match = re.search(r"guidelines_version:\s*(\d+)\.(\d+)", block)
    assert match, "no guidelines_version found in guidelines.md §22"
    major, minor = int(match.group(1)), int(match.group(2))
    assert (major, minor) >= (0, 17)


def test_section_13_13_exists_and_resolves_oq_047():
    assert "### 13.13 Hard-negative realization inventory" in GUIDELINES
    assert "resolves OQ-047" in _section_13_13()


def test_section_13_13_labels_new_words_distinctly_from_reused_words():
    section = _normalize(_section_13_13())
    assert "A — already frozen" in section
    assert "B — new policy, frozen now" in section
    for new_word in ("order", "reference code", "station", "contact"):
        assert new_word in section


def test_section_13_13_carrier_table_covers_all_five_constructible_classes():
    section = _section_13_13()
    for decoy_class in (
        "NUMERIC_SHAPE", "ALNUM_SHAPE", "NAME_AS_PLACE", "HANDLE_SHAPE", "PARTIAL_PII",
    ):
        assert decoy_class in section
    assert "ORG_AS_PERSON" in section  # named as still deferred, not silently dropped


def test_section_13_13_states_it_is_not_a_general_translation_system():
    section = _normalize(_section_13_13())
    assert "not a general-purpose Hindi translation system" in section


def test_section_13_13_rejects_reusing_email_carrier_for_handle_shape():
    section = _normalize(_section_13_13())
    assert "does **not** reuse EMAIL's frozen" in section
    assert "HANDLE_SHAPE" in section and "contact" in section
