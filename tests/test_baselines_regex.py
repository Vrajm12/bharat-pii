"""Unit tests for baselines/regex.py (PROJECT_SPEC.md §19 B1, §20.6, §20.7).

Verifies the structured Indian PII regular expression baseline detector independently
on small synthetic examples without benchmark memorization.
"""

from __future__ import annotations

import pytest

from baselines.base import BaselineAdapter, validate_predictions
from baselines.regex import RegexBaselineAdapter
from benchmark.schema import Prediction


def test_1_regex_adapter_subclasses_baseline_adapter():
    adapter = RegexBaselineAdapter()
    assert isinstance(adapter, BaselineAdapter)


def test_2_system_metadata():
    adapter = RegexBaselineAdapter()
    assert adapter.system_name == "regex"
    assert adapter.system_version == "1.0.0"


def test_3_pan_canonical_format():
    adapter = RegexBaselineAdapter()
    text = "The customer's PAN is INOPM1467C for verification."
    preds = adapter.predict(text)
    assert len(preds) == 1
    assert preds[0].type == "PAN"
    assert preds[0].text == "INOPM1467C"
    assert preds[0].start == 22
    assert preds[0].end == 32
    assert text[preds[0].start : preds[0].end] == "INOPM1467C"


def test_4_aadhaar_formatted_space_grouped():
    adapter = RegexBaselineAdapter()
    text = "Aadhaar Card: 5771 6789 9924 registered with UIDAI."
    preds = adapter.predict(text)
    assert len(preds) == 1
    assert preds[0].type == "AADHAAR"
    assert preds[0].text == "5771 6789 9924"
    assert text[preds[0].start : preds[0].end] == "5771 6789 9924"


def test_5_aadhaar_canonical_unspaced_12_digits():
    adapter = RegexBaselineAdapter()
    text = "UID: 577167899924."
    preds = adapter.predict(text)
    assert len(preds) == 1
    assert preds[0].type == "AADHAAR"
    assert preds[0].text == "577167899924"
    assert text[preds[0].start : preds[0].end] == "577167899924"


def test_6_email_format():
    adapter = RegexBaselineAdapter()
    text = "Please reach out to support.team@example.com for queries."
    preds = adapter.predict(text)
    assert len(preds) == 1
    assert preds[0].type == "EMAIL"
    assert preds[0].text == "support.team@example.com"
    assert text[preds[0].start : preds[0].end] == "support.team@example.com"


def test_7_upi_format_and_precedence():
    adapter = RegexBaselineAdapter()
    text = "Pay via UPI to merchant@okhdfcbank or 9876543210@mail.test immediately."
    preds = adapter.predict(text)
    assert len(preds) == 2
    assert preds[0].type == "UPI_ID"
    assert preds[0].text == "merchant@okhdfcbank"
    assert preds[1].type == "UPI_ID"
    assert preds[1].text == "9876543210@mail.test"
    # Ensure neither UPI is duplicate-classified as generic EMAIL
    types = [p.type for p in preds]
    assert types == ["UPI_ID", "UPI_ID"]


def test_8_phone_format():
    adapter = RegexBaselineAdapter()
    text = "Contact numbers: 9876543210 and +91 8765432109."
    preds = adapter.predict(text)
    assert len(preds) == 2
    assert preds[0].type == "PHONE"
    assert preds[0].text == "9876543210"
    assert preds[1].type == "PHONE"
    assert preds[1].text == "+91 8765432109"


def test_9_bank_account_format():
    adapter = RegexBaselineAdapter()
    text = "Transfer funds to account: 123456789012 now."
    preds = adapter.predict(text)
    ba_preds = [p for p in preds if p.type == "BANK_ACCOUNT"]
    assert len(ba_preds) == 1
    assert ba_preds[0].text == "123456789012"
    assert text[ba_preds[0].start : ba_preds[0].end] == "123456789012"


def test_10_unicode_code_point_offsets():
    adapter = RegexBaselineAdapter()
    text = "कृपया 9876543210 पर कॉल करें।"
    preds = adapter.predict(text)
    assert len(preds) == 1
    p = preds[0]
    assert p.type == "PHONE"
    assert text[p.start : p.end] == "9876543210"


def test_11_multiple_matches_and_distinct_types():
    adapter = RegexBaselineAdapter()
    text = "PAN ABCDE1234F, Email priya@example.com, Phone 9876543210."
    preds = adapter.predict(text)
    types = [p.type for p in preds]
    assert types == ["PAN", "EMAIL", "PHONE"]
    for p in preds:
        assert text[p.start : p.end] == p.text


def test_12_deterministic_ordering():
    adapter = RegexBaselineAdapter()
    text = "Details: PAN ABCDE1234F, Email test@example.com, Phone 9876543210."
    preds1 = adapter.predict(text)
    preds2 = adapter.predict(text)
    assert preds1 == preds2

    # Check strictly monotonic ordering by start offset
    for i in range(len(preds1) - 1):
        assert (preds1[i].start, preds1[i].end) <= (preds1[i + 1].start, preds1[i + 1].end)


def test_13_all_predictions_pass_validation():
    adapter = RegexBaselineAdapter()
    text = "User info: PAN FGHIJ5678K, UPI 9876543210@mail.test, Mobile 9876543210, Aadhaar 1234 5678 9012."
    preds = adapter.predict(text)
    valid, rejected = validate_predictions(preds, original_text=text)
    assert len(rejected) == 0
    assert len(valid) == len(preds)


def test_14_clean_non_pii_text_produces_no_predictions():
    adapter = RegexBaselineAdapter()
    text = "This is a general system notification with no personal identifiers."
    preds = adapter.predict(text)
    assert len(preds) == 0


def test_15_input_text_is_not_mutated():
    adapter = RegexBaselineAdapter()
    text = "Immutable text check ABCDE1234F"
    text_copy = str(text)
    _ = adapter.predict(text)
    assert text == text_copy
