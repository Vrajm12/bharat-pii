"""Unit tests for baselines/spacy.py (PROJECT_SPEC.md §19 B2, §19.2, §20.5, §20.6).

Verifies the spaCy NER baseline adapter contract, metadata disclosure,
PERSON mapping, out-of-taxonomy label preservation, Unicode offsets,
prediction validation, determinism, and input immutability.
"""

from __future__ import annotations

import pytest
import spacy

from baselines.base import BaselineAdapter, validate_predictions
from baselines.spacy import SpacyBaselineAdapter
from benchmark.schema import Prediction


def test_1_spacy_adapter_subclasses_baseline_adapter():
    adapter = SpacyBaselineAdapter()
    assert isinstance(adapter, BaselineAdapter)


def test_2_spacy_system_metadata():
    adapter = SpacyBaselineAdapter()
    assert adapter.system_name == "spacy"
    assert spacy.__version__ in adapter.system_version
    assert "en_core_web_sm" in adapter.system_version
    assert "3.8.0" in adapter.system_version


def test_3_person_entity_detection():
    adapter = SpacyBaselineAdapter()
    text = "Yesterday, Rajesh Sharma met with Sneha Verma at the conference."
    preds = adapter.predict(text)

    person_preds = [p for p in preds if p.type == "PERSON"]
    assert len(person_preds) >= 1
    for p in person_preds:
        assert text[p.start : p.end] == p.text


def test_4_out_of_taxonomy_label_preservation():
    adapter = SpacyBaselineAdapter()
    text = "Google and Microsoft were founded in the United States on September 4, 1998."
    preds = adapter.predict(text)

    types = {p.type for p in preds}
    # Standard OntoNotes entities like ORG, GPE, DATE must be preserved
    assert any(t in types for t in ["ORG", "GPE", "DATE"])
    for p in preds:
        assert p.status == "VALID"
        assert text[p.start : p.end] == p.text


def test_5_unsupported_indian_pii_no_artificial_mapping():
    adapter = SpacyBaselineAdapter()
    text = "The PAN number is INOPM1467C and UPI is user@okhdfcbank."
    preds = adapter.predict(text)

    # spaCy should NOT artificially invent PAN or UPI_ID types
    types = {p.type for p in preds}
    assert "PAN" not in types
    assert "UPI_ID" not in types
    assert "AADHAAR" not in types


def test_6_unicode_and_devanagari_offsets():
    adapter = SpacyBaselineAdapter()
    text = "डॉ. Rajesh Sharma ने कल भाषण दिया।"
    preds = adapter.predict(text)

    for p in preds:
        assert 0 <= p.start < p.end <= len(text)
        assert text[p.start : p.end] == p.text


def test_7_prediction_validation_pass_through():
    adapter = SpacyBaselineAdapter()
    text = "Meeting with Dr. Rajesh Sharma from Microsoft in Mumbai tomorrow."
    preds = adapter.predict(text)

    valid, rejected = validate_predictions(preds, original_text=text)
    assert len(rejected) == 0
    assert len(valid) == len(preds)


def test_8_deterministic_output():
    adapter = SpacyBaselineAdapter()
    text = "Priya Nair and Amit Patel visited Tata Motors in Pune."
    preds1 = adapter.predict(text)
    preds2 = adapter.predict(text)

    assert preds1 == preds2
    # Strictly sorted by start, end, type
    for i in range(len(preds1) - 1):
        assert (preds1[i].start, preds1[i].end) <= (preds1[i + 1].start, preds1[i + 1].end)


def test_9_input_text_is_not_mutated():
    adapter = SpacyBaselineAdapter()
    text = "Original immutable string check with Rajesh Sharma."
    text_copy = str(text)
    _ = adapter.predict(text)
    assert text == text_copy


def test_10_clean_text_handling():
    adapter = SpacyBaselineAdapter()
    text = "and or but the of in on at"
    preds = adapter.predict(text)
    assert len(preds) == 0
