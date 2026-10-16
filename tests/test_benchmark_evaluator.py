"""Unit tests for benchmark/evaluator.py."""

from __future__ import annotations

import copy
import pytest

from benchmark.evaluator import EvaluationResult, Evaluator
from benchmark.schema import GoldEntity, Match, MatchingResult, Prediction


def test_1_perfect_positive_evaluation():
    evaluator = Evaluator()
    record = {
        "variant_id": "PAN_001_EN_01",
        "text": "My PAN is ABCDE1234F.",
        "base_kind": "POSITIVE",
        "entities": [
            {
                "type": "PAN",
                "start": 10,
                "end": 20,
                "base_pii_value": "ABCDE1234F",
                "realized_pii_value": "ABCDE1234F",
                "occurrence_index": 0,
            }
        ],
    }
    preds = [Prediction(type="PAN", start=10, end=20)]
    res = evaluator.evaluate_record(record, preds)

    assert res.variant_id == "PAN_001_EN_01"
    assert res.metrics.tp_exact == 1
    assert res.metrics.m3_f1 == 1.0
    assert len(res.failures) == 0


def test_2_missed_pii():
    evaluator = Evaluator()
    record = {
        "variant_id": "PAN_001_EN_01",
        "text": "My PAN is ABCDE1234F.",
        "base_kind": "POSITIVE",
        "entities": [{"type": "PAN", "start": 10, "end": 20}],
    }
    res = evaluator.evaluate_record(record, [])

    assert res.metrics.f1_missed == 1
    assert len(res.failures) == 1
    assert res.failures[0].failure_id == "F1"


def test_3_wrong_span():
    evaluator = Evaluator()
    record = {
        "variant_id": "PERSON_001_EN_01",
        "text": "Contact Rahul Sharma today.",
        "base_kind": "POSITIVE",
        "entities": [{"type": "PERSON", "start": 8, "end": 20}],
    }
    preds = [Prediction(type="PERSON", start=8, end=13)]  # Only Rahul
    res = evaluator.evaluate_record(record, preds)

    assert res.metrics.f2_wrong_span == 1
    assert len(res.failures) == 1
    assert res.failures[0].failure_id == "F2"


def test_4_wrong_type():
    evaluator = Evaluator()
    record = {
        "variant_id": "AADHAAR_001_EN_01",
        "text": "ID: 123456789012.",
        "base_kind": "POSITIVE",
        "entities": [{"type": "AADHAAR", "start": 4, "end": 16}],
    }
    preds = [Prediction(type="BANK_ACCOUNT", start=4, end=16)]
    res = evaluator.evaluate_record(record, preds)

    assert res.metrics.f3_wrong_type == 1
    assert len(res.failures) == 1
    assert res.failures[0].failure_id == "F3"


def test_5_false_positive():
    evaluator = Evaluator()
    record = {
        "variant_id": "PAN_001_EN_01",
        "text": "Hello world.",
        "base_kind": "POSITIVE",
        "entities": [],
    }
    preds = [Prediction(type="ORG", start=0, end=5)]
    res = evaluator.evaluate_record(record, preds)

    assert res.metrics.f4_false_pos == 1
    assert len(res.failures) == 1
    assert res.failures[0].failure_id == "F4"


def test_6_hard_negative_true_negative():
    evaluator = Evaluator()
    record = {
        "variant_id": "HN_PHONE_001_EN_01",
        "text": "Product order ID is 9876543210.",
        "base_kind": "HARD_NEGATIVE",
        "distractors": [{"type": "PHONE", "start": 20, "end": 30, "decoy_class": "NUMERIC_SHAPE"}],
    }
    res = evaluator.evaluate_record(record, [])

    assert res.metrics.n_gold == 0
    assert res.metrics.f4_false_pos == 0
    assert res.metrics.m3_f1 == 1.0
    assert len(res.failures) == 0


def test_7_hard_negative_false_positive():
    evaluator = Evaluator()
    record = {
        "variant_id": "HN_PHONE_001_EN_01",
        "text": "Product order ID is 9876543210.",
        "base_kind": "HARD_NEGATIVE",
        "distractors": [{"type": "PHONE", "start": 20, "end": 30, "decoy_class": "NUMERIC_SHAPE"}],
    }
    preds = [Prediction(type="PHONE", start=20, end=30)]
    res = evaluator.evaluate_record(record, preds)

    assert res.metrics.f4_false_pos == 1
    assert len(res.failures) == 1
    assert res.failures[0].decoy_class == "NUMERIC_SHAPE"


def test_8_distractor_attribution_undesigned():
    evaluator = Evaluator()
    record = {
        "variant_id": "HN_PHONE_001_EN_01",
        "text": "Product order ID is 9876543210.",
        "base_kind": "HARD_NEGATIVE",
        "distractors": [{"type": "PHONE", "start": 20, "end": 30, "decoy_class": "NUMERIC_SHAPE"}],
    }
    # Prediction on "Product"
    preds = [Prediction(type="ORG", start=0, end=7)]
    res = evaluator.evaluate_record(record, preds)

    assert res.metrics.f4_false_pos == 1
    assert res.failures[0].decoy_class is None


def test_9_adversarial_a1():
    evaluator = Evaluator()
    record = {
        "variant_id": "PAN_001_EN_A1_01",
        "text": "My PAN is F Z Z F N 0 2 5 6 Z.",
        "base_kind": "POSITIVE",
        "difficulty": "ADVERSARIAL",
        "perturbation": {"family": "A1", "target": "VALUE"},
        "entities": [{"type": "PAN", "start": 10, "end": 29}],
    }
    preds = [Prediction(type="PAN", start=10, end=29)]
    res = evaluator.evaluate_record(record, preds)
    assert res.metrics.tp_exact == 1


def test_10_adversarial_a3():
    evaluator = Evaluator()
    record = {
        "variant_id": "PAN_001_EN_A3_01",
        "text": "My P-A-N is FZZFN0256Z.",
        "base_kind": "POSITIVE",
        "difficulty": "ADVERSARIAL",
        "perturbation": {"family": "A3", "target": "LABEL"},
        "entities": [{"type": "PAN", "start": 12, "end": 22}],
    }
    preds = [Prediction(type="PAN", start=12, end=22)]
    res = evaluator.evaluate_record(record, preds)
    assert res.metrics.tp_exact == 1


def test_11_adversarial_a5():
    evaluator = Evaluator()
    record = {
        "variant_id": "PHONE_001_EN_A5_01",
        "text": "Call me at 7B34657871.",
        "base_kind": "POSITIVE",
        "difficulty": "ADVERSARIAL",
        "perturbation": {"family": "A5", "target": "VALUE"},
        "entities": [{"type": "PHONE", "start": 11, "end": 21}],
    }
    preds = [Prediction(type="PHONE", start=11, end=21)]
    res = evaluator.evaluate_record(record, preds)
    assert res.metrics.tp_exact == 1


def test_12_multilingual_record():
    evaluator = Evaluator()
    record = {
        "variant_id": "PERSON_001_HINGLISH_01",
        "text": "Mera naam Rahul Sharma hai.",
        "language": "HINGLISH",
        "base_kind": "POSITIVE",
        "entities": [{"type": "PERSON", "start": 10, "end": 22}],
    }
    res = evaluator.evaluate_record(record, [])
    assert res.metrics.f1_missed == 1
    assert "F6_LINGUISTIC_FAILURE" in res.failures[0].secondary_tags


def test_13_repeated_evaluation_determinism():
    evaluator = Evaluator()
    record = {
        "variant_id": "PAN_001_EN_01",
        "text": "My PAN is ABCDE1234F.",
        "base_kind": "POSITIVE",
        "entities": [{"type": "PAN", "start": 10, "end": 20}],
    }
    preds = [Prediction(type="PAN", start=10, end=20)]

    res1 = evaluator.evaluate_record(record, preds)
    res2 = evaluator.evaluate_record(record, preds)
    assert res1 == res2


def test_14_prediction_order_invariance():
    evaluator = Evaluator()
    record = {
        "variant_id": "MULTI_01",
        "text": "PAN: ABCDE1234F, PHONE: 9876543210.",
        "base_kind": "POSITIVE",
        "entities": [
            {"type": "PAN", "start": 5, "end": 15},
            {"type": "PHONE", "start": 24, "end": 34},
        ],
    }
    p1 = Prediction(type="PAN", start=5, end=15)
    p2 = Prediction(type="PHONE", start=24, end=34)

    res_fwd = evaluator.evaluate_record(record, [p1, p2])
    res_rev = evaluator.evaluate_record(record, [p2, p1])

    assert res_fwd.metrics == res_rev.metrics


def test_15_composition_check():
    # Evaluator produces matching_result, metrics, and failures directly from submodules
    evaluator = Evaluator()
    record = {
        "variant_id": "PAN_001_EN_01",
        "text": "My PAN is ABCDE1234F.",
        "base_kind": "POSITIVE",
        "entities": [{"type": "PAN", "start": 10, "end": 20}],
    }
    res = evaluator.evaluate_record(record, [Prediction(type="PAN", start=10, end=20)])
    assert isinstance(res.matching_result, MatchingResult)
    assert isinstance(res.metrics, type(res.metrics))
    assert isinstance(res.failures, list)


def test_16_malformed_prediction_behavior():
    evaluator = Evaluator()
    record = {
        "variant_id": "PAN_001_EN_01",
        "text": "My PAN is ABCDE1234F.",
        "base_kind": "POSITIVE",
        "entities": [{"type": "PAN", "start": 10, "end": 20}],
    }
    p_bad = Prediction(type="PAN", start=10, end=50)  # Beyond text length (21)
    res = evaluator.evaluate_record(record, [p_bad])

    assert len(res.matching_result.malformed_predictions) == 1
    assert res.matching_result.malformed_predictions[0].status == "REJECTED"
    assert res.metrics.f1_missed == 1


def test_17_batch_evaluation():
    evaluator = Evaluator()
    records = [
        {"variant_id": "R1", "text": "PAN: ABCDE1234F", "base_kind": "POSITIVE", "entities": [{"type": "PAN", "start": 5, "end": 15}]},
        {"variant_id": "R2", "text": "HN 123", "base_kind": "HARD_NEGATIVE", "distractors": []},
    ]
    preds = {
        "R1": [Prediction(type="PAN", start=5, end=15)],
        "R2": [],
    }
    batch_res = evaluator.evaluate_batch(records, preds)
    assert len(batch_res) == 2
    assert batch_res[0].variant_id == "R1"
    assert batch_res[1].variant_id == "R2"
