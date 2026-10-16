"""Unit tests for baselines/presidio.py (PROJECT_SPEC.md §19 B3, §19.2, §20.5, §20.6).

Verifies the Microsoft Presidio baseline adapter contract, metadata disclosure,
India recognizers configuration, taxonomy mapping, out-of-taxonomy label preservation,
Unicode offsets, prediction validation, determinism, and input immutability.
"""

from __future__ import annotations

import pytest

from baselines.base import BaselineAdapter, validate_predictions
from baselines.presidio import PresidioBaselineAdapter
from benchmark.schema import Prediction


def test_1_presidio_adapter_subclasses_baseline_adapter():
    adapter = PresidioBaselineAdapter()
    assert isinstance(adapter, BaselineAdapter)


def test_2_presidio_system_metadata():
    adapter = PresidioBaselineAdapter()
    assert adapter.system_name == "presidio"
    assert "2.2.364" in adapter.system_version
    assert "en_core_web_sm" in adapter.system_version
    assert "in_enabled" in adapter.system_version


def test_3_person_entity_detection():
    adapter = PresidioBaselineAdapter()
    text = "Yesterday, Rajesh Sharma met with Sneha Verma at the conference."
    preds = adapter.predict(text)

    person_preds = [p for p in preds if p.type == "PERSON"]
    assert len(person_preds) >= 1
    for p in person_preds:
        assert text[p.start : p.end] == p.text


def test_4_pan_entity_detection():
    adapter = PresidioBaselineAdapter()
    text = "My tax PAN card number is ABCDE1234F for verification."
    preds = adapter.predict(text)

    pan_preds = [p for p in preds if p.type == "PAN"]
    assert len(pan_preds) >= 1
    assert any(p.text == "ABCDE1234F" for p in pan_preds)


def test_5_aadhaar_entity_detection():
    adapter = PresidioBaselineAdapter()
    # 2000 0000 0009 is a valid Verhoeff-checksummed 12-digit UID
    text = "Please verify Aadhaar card: 2000 0000 0009."
    preds = adapter.predict(text)

    aadhaar_preds = [p for p in preds if p.type == "AADHAAR"]
    assert len(aadhaar_preds) >= 1
    assert any(p.text == "2000 0000 0009" for p in aadhaar_preds)


def test_6_phone_entity_detection():
    adapter = PresidioBaselineAdapter()
    text = "Contact our support helpline at +91 9876543210 immediately."
    preds = adapter.predict(text)

    phone_preds = [p for p in preds if p.type == "PHONE"]
    assert len(phone_preds) >= 1
    for p in phone_preds:
        assert text[p.start : p.end] == p.text


def test_7_email_entity_detection():
    adapter = PresidioBaselineAdapter()
    text = "Send your application to rajesh.sharma@example.com before Friday."
    preds = adapter.predict(text)

    email_preds = [p for p in preds if p.type == "EMAIL"]
    assert len(email_preds) >= 1
    assert any(p.text == "rajesh.sharma@example.com" for p in email_preds)


def test_8_out_of_taxonomy_label_preservation():
    adapter = PresidioBaselineAdapter()
    text = "Microsoft was founded in Redmond on April 4, 1975."
    preds = adapter.predict(text)

    types = {p.type for p in preds}
    # Out-of-taxonomy types like ORGANIZATION, LOCATION, DATE_TIME must be preserved
    assert any(t in types for t in ["ORGANIZATION", "LOCATION", "DATE_TIME"])
    for p in preds:
        assert p.status == "VALID"
        assert text[p.start : p.end] == p.text


def test_9_no_artificial_upi_or_bank_account_detection():
    adapter = PresidioBaselineAdapter()
    text = "Transfer to user@okhdfcbank or account 9876543210123."
    preds = adapter.predict(text)

    types = {p.type for p in preds}
    # Presidio has no built-in UPI_ID or domestic Indian BANK_ACCOUNT recognizer
    assert "UPI_ID" not in types
    assert "BANK_ACCOUNT" not in types


def test_10_no_artificial_address_mapping():
    adapter = PresidioBaselineAdapter()
    text = "Flat 402, Shanti Niketan, Bandra West, Mumbai 400050."
    preds = adapter.predict(text)

    types = {p.type for p in preds}
    # Presidio should NOT invent an ADDRESS entity from partial locations
    assert "ADDRESS" not in types


def test_11_unicode_and_devanagari_offsets():
    adapter = PresidioBaselineAdapter()
    text = "डॉ. Rajesh Sharma का PAN नंबर ABCDE1234F है।"
    preds = adapter.predict(text)

    for p in preds:
        assert 0 <= p.start < p.end <= len(text)
        assert text[p.start : p.end] == p.text


def test_12_prediction_validation_pass_through():
    adapter = PresidioBaselineAdapter()
    text = "PAN ABCDE1234F, Email test@example.com, Phone +91 9876543210."
    preds = adapter.predict(text)

    valid, rejected = validate_predictions(preds, original_text=text)
    assert len(rejected) == 0
    assert len(valid) == len(preds)


def test_13_deterministic_output():
    adapter = PresidioBaselineAdapter()
    text = "Priya Nair with PAN ABCDE1234F and email priya@test.com."
    preds1 = adapter.predict(text)
    preds2 = adapter.predict(text)

    assert preds1 == preds2
    # Check deterministic ordering
    for i in range(len(preds1) - 1):
        assert (preds1[i].start, preds1[i].end) <= (preds1[i + 1].start, preds1[i + 1].end)


def test_14_input_text_is_not_mutated():
    adapter = PresidioBaselineAdapter()
    text = "Original string with PAN ABCDE1234F."
    text_copy = str(text)
    _ = adapter.predict(text)
    assert text == text_copy
