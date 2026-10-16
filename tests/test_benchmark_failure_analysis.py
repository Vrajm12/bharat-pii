"""Unit tests for benchmark/failure_analysis.py.

Tests all failure categories (F1-F9) and error attributions from PROJECT_SPEC.md §23, §20.4, §20.5:
- F1: MISSED_PII
- F2: WRONG_SPAN
- F3: WRONG_TYPE
- F4: FALSE_POSITIVE (and decoy_class attribution)
- F5: CONTEXT_FAILURE
- F6: LINGUISTIC_FAILURE
- F7: FORMATTING_FAILURE
- F8: ADVERSARIAL_FAILURE
- F9: SCRIPT_FAILURE
"""

from __future__ import annotations

import pytest

from benchmark.failure_analysis import FailureInstance, analyze_failures
from benchmark.matching import match_predictions
from benchmark.schema import GoldEntity, Match, MatchingResult, Prediction


def test_f1_missed_pii():
    gold = [GoldEntity(type="PAN", start=10, end=20)]
    match_res = match_predictions(gold, [])
    failures = analyze_failures(match_res)

    assert len(failures) == 1
    f = failures[0]
    assert f.failure_id == "F1"
    assert f.primary_category == "MISSED_PII"
    assert f.gold_entity == gold[0]
    assert f.prediction is None


def test_f2_wrong_span():
    gold = [GoldEntity(type="PERSON", start=10, end=20)]
    preds = [Prediction(type="PERSON", start=12, end=22)]
    match_res = match_predictions(gold, preds)
    failures = analyze_failures(match_res)

    assert len(failures) == 1
    f = failures[0]
    assert f.failure_id == "F2"
    assert f.primary_category == "WRONG_SPAN"
    assert f.gold_entity == gold[0]
    assert f.prediction == preds[0]


def test_f3_wrong_type():
    gold = [GoldEntity(type="AADHAAR", start=10, end=22)]
    preds = [Prediction(type="BANK_ACCOUNT", start=10, end=22)]
    match_res = match_predictions(gold, preds)
    failures = analyze_failures(match_res)

    assert len(failures) == 1
    f = failures[0]
    assert f.failure_id == "F3"
    assert f.primary_category == "WRONG_TYPE"
    assert f.gold_entity == gold[0]
    assert f.prediction == preds[0]


def test_f4_false_positive_undesigned():
    preds = [Prediction(type="ORG", start=50, end=60)]
    match_res = match_predictions([], preds)
    failures = analyze_failures(match_res)

    assert len(failures) == 1
    f = failures[0]
    assert f.failure_id == "F4"
    assert f.primary_category == "FALSE_POSITIVE"
    assert f.prediction == preds[0]
    assert f.decoy_class is None


def test_f4_false_positive_with_decoy_attribution():
    preds = [Prediction(type="PHONE", start=10, end=20)]
    distractors = [{"type": "PHONE", "start": 10, "end": 20, "decoy_class": "NUMERIC_SHAPE"}]
    match_res = match_predictions([], preds)
    failures = analyze_failures(match_res, distractors=distractors)

    assert len(failures) == 1
    f = failures[0]
    assert f.failure_id == "F4"
    assert f.primary_category == "FALSE_POSITIVE"
    assert f.decoy_class == "NUMERIC_SHAPE"
    assert "DECOY_NUMERIC_SHAPE" in f.secondary_tags


def test_f5_context_failure_attribution():
    gold = [GoldEntity(type="PAN", start=10, end=20)]
    match_res = match_predictions(gold, [])
    meta = {"context": "IMPLICIT", "perturbation": {"family": "A4"}}
    failures = analyze_failures(match_res, record_metadata=meta)

    assert len(failures) == 1
    f = failures[0]
    assert "F5_CONTEXT_FAILURE" in f.secondary_tags


def test_f6_linguistic_failure_attribution():
    gold = [GoldEntity(type="PERSON", start=10, end=20)]
    match_res = match_predictions(gold, [])
    meta = {"language": "HINGLISH", "context": "EXPLICIT"}
    failures = analyze_failures(match_res, record_metadata=meta)

    assert len(failures) == 1
    f = failures[0]
    assert "F6_LINGUISTIC_FAILURE" in f.secondary_tags


def test_f7_formatting_failure_attribution():
    gold = [GoldEntity(type="PAN", start=10, end=20)]
    match_res = match_predictions(gold, [])
    meta = {"perturbation": {"family": "A1"}}
    failures = analyze_failures(match_res, record_metadata=meta)

    assert len(failures) == 1
    f = failures[0]
    assert "F7_FORMATTING_FAILURE" in f.secondary_tags


def test_f8_adversarial_failure_attribution():
    gold = [GoldEntity(type="PHONE", start=10, end=20)]
    match_res = match_predictions(gold, [])
    meta = {"difficulty": "ADVERSARIAL", "perturbation": {"family": "A5"}}
    failures = analyze_failures(match_res, record_metadata=meta)

    assert len(failures) == 1
    f = failures[0]
    assert "F8_ADVERSARIAL_FAILURE" in f.secondary_tags
    assert "FAMILY_A5" in f.secondary_tags


def test_f9_script_failure_attribution():
    gold = [GoldEntity(type="PERSON", start=10, end=20)]
    match_res = match_predictions(gold, [])
    meta = {"language": "HI_DEVA_PII", "carrier_script": "DEVANAGARI"}
    failures = analyze_failures(match_res, record_metadata=meta)

    assert len(failures) == 1
    f = failures[0]
    assert "F9_SCRIPT_FAILURE" in f.secondary_tags


def test_mutually_exclusive_primary_failure_labels():
    # An entity match cannot simultaneously be both F2 (WRONG_SPAN) and F3 (WRONG_TYPE)
    # in primary label, because F2 requires is_type_match=True while F3 requires is_type_match=False
    gold = [GoldEntity(type="PERSON", start=10, end=20)]
    pred = Prediction(type="ORG", start=12, end=22)  # Wrong type AND inexact span
    match_res = match_predictions(gold, [pred])
    failures = analyze_failures(match_res)

    assert len(failures) == 1
    # Primary category must be WRONG_TYPE (F3)
    assert failures[0].failure_id == "F3"
    assert failures[0].primary_category == "WRONG_TYPE"
