"""Unit tests for benchmark/matching.py.

Tests all 20 required edge cases and invariants from PROJECT_SPEC.md §20.3, §20.4:
1. exact type + exact span
2. exact type + partial overlap
3. wrong type + overlap
4. wrong type + exact span
5. no overlap
6. multiple predictions for one gold
7. one prediction overlapping multiple gold entities
8. nested spans
9. equal-weight situations
10. deterministic tie-breaking
11. reversed input order produces identical matching
12. empty gold
13. empty predictions
14. both empty
15. malformed prediction boundaries
16. prediction extending beyond text
17. zero-length prediction
18. Unicode/code-point offsets
19. duplicate predictions
20. input objects remain unchanged
"""

from __future__ import annotations

import copy
import pytest

from benchmark.matching import match_predictions
from benchmark.schema import GoldEntity, Match, MatchingResult, Prediction


def test_1_exact_type_exact_span():
    gold = [GoldEntity(type="PAN", start=10, end=20)]
    preds = [Prediction(type="PAN", start=10, end=20)]
    res = match_predictions(gold, preds)

    assert len(res.matches) == 1
    assert len(res.unmatched_gold) == 0
    assert len(res.unmatched_predictions) == 0
    m = res.matches[0]
    assert m.gold == gold[0]
    assert m.prediction == preds[0]
    assert m.is_type_match is True
    assert m.is_exact_span is True
    assert m.iou == 1.0
    assert m.weight == 3.0  # 2 + 1.0


def test_2_exact_type_partial_overlap():
    gold = [GoldEntity(type="PERSON", start=10, end=20)]
    preds = [Prediction(type="PERSON", start=15, end=25)]
    res = match_predictions(gold, preds)

    assert len(res.matches) == 1
    m = res.matches[0]
    assert m.is_type_match is True
    assert m.is_exact_span is False
    # overlap: 15..20 (5), union: 10..25 (15) -> iou: 5/15 = 1/3
    assert abs(m.iou - (1.0 / 3.0)) < 1e-6
    assert abs(m.weight - (2.0 + 1.0 / 3.0)) < 1e-6


def test_3_wrong_type_overlap():
    gold = [GoldEntity(type="PERSON", start=10, end=20)]
    preds = [Prediction(type="ORG", start=15, end=25)]
    res = match_predictions(gold, preds)

    assert len(res.matches) == 1
    m = res.matches[0]
    assert m.is_type_match is False
    assert m.is_exact_span is False
    assert abs(m.iou - (1.0 / 3.0)) < 1e-6
    assert abs(m.weight - (1.0 / 3.0)) < 1e-6  # no +2 bonus


def test_4_wrong_type_exact_span():
    gold = [GoldEntity(type="AADHAAR", start=10, end=22)]
    preds = [Prediction(type="BANK_ACCOUNT", start=10, end=22)]
    res = match_predictions(gold, preds)

    assert len(res.matches) == 1
    m = res.matches[0]
    assert m.is_type_match is False
    assert m.is_exact_span is True
    assert m.iou == 1.0
    assert m.weight == 1.0  # iou only, no +2 bonus


def test_5_no_overlap():
    gold = [GoldEntity(type="PAN", start=10, end=20)]
    preds = [Prediction(type="PAN", start=25, end=35)]
    res = match_predictions(gold, preds)

    assert len(res.matches) == 0
    assert len(res.unmatched_gold) == 1
    assert len(res.unmatched_predictions) == 1


def test_6_multiple_predictions_for_one_gold():
    # Gold entity: 10..20
    # Pred1: 10..20 (type match, exact) -> weight 3.0
    # Pred2: 12..18 (type match, partial) -> weight 2.6
    gold = [GoldEntity(type="PAN", start=10, end=20)]
    preds = [
        Prediction(type="PAN", start=12, end=18),
        Prediction(type="PAN", start=10, end=20),
    ]
    res = match_predictions(gold, preds)

    assert len(res.matches) == 1
    assert res.matches[0].prediction == preds[1]  # Higher weight match wins
    assert len(res.unmatched_predictions) == 1
    assert res.unmatched_predictions[0] == preds[0]


def test_7_one_prediction_overlapping_multiple_gold():
    # Pred: 10..30
    # Gold1: 10..18 (type match) -> overlap 8, union 20, iou 0.4, weight 2.4
    # Gold2: 22..30 (type match) -> overlap 8, union 20, iou 0.4, weight 2.4 (tie-broken deterministically)
    gold = [
        GoldEntity(type="PHONE", start=10, end=18),
        GoldEntity(type="PHONE", start=22, end=30),
    ]
    preds = [Prediction(type="PHONE", start=10, end=30)]
    res = match_predictions(gold, preds)

    assert len(res.matches) == 1
    assert len(res.unmatched_gold) == 1
    # Match goes to Gold1 due to lexicographical rank tie-break
    assert res.matches[0].gold == gold[0]
    assert res.unmatched_gold[0] == gold[1]


def test_8_nested_spans():
    # Outer prediction contains inner gold, inner prediction matches inner gold
    gold = [GoldEntity(type="PERSON", start=10, end=20)]
    p_outer = Prediction(type="PERSON", start=5, end=25)  # iou 10/20 = 0.5
    p_exact = Prediction(type="PERSON", start=10, end=20)  # iou 1.0
    res = match_predictions(gold, [p_outer, p_exact])

    assert len(res.matches) == 1
    assert res.matches[0].prediction == p_exact
    assert res.unmatched_predictions[0] == p_outer


def test_9_equal_weight_situations():
    # Two identical gold entities, two identical predictions
    gold = [
        GoldEntity(type="PAN", start=0, end=10),
        GoldEntity(type="PAN", start=20, end=30),
    ]
    preds = [
        Prediction(type="PAN", start=0, end=10),
        Prediction(type="PAN", start=20, end=30),
    ]
    res = match_predictions(gold, preds)

    assert len(res.matches) == 2
    assert res.matches[0].gold == gold[0]
    assert res.matches[0].prediction == preds[0]
    assert res.matches[1].gold == gold[1]
    assert res.matches[1].prediction == preds[1]


def test_10_deterministic_tie_breaking():
    # Two predictions with exact same overlap and type for one gold entity
    # p1: 10..20, p2: 10..20 (identical geometry)
    gold = [GoldEntity(type="EMAIL", start=10, end=20)]
    p1 = Prediction(type="EMAIL", start=10, end=20, text="first")
    p2 = Prediction(type="EMAIL", start=10, end=20, text="second")
    res = match_predictions(gold, [p1, p2])

    assert len(res.matches) == 1
    assert len(res.unmatched_predictions) == 1


def test_11_reversed_input_order_produces_identical_matching():
    gold = [
        GoldEntity(type="PERSON", start=10, end=20),
        GoldEntity(type="PHONE", start=30, end=40),
    ]
    preds = [
        Prediction(type="PERSON", start=10, end=20),
        Prediction(type="PHONE", start=30, end=40),
    ]

    res_forward = match_predictions(gold, preds)
    res_reversed = match_predictions(list(reversed(gold)), list(reversed(preds)))

    # Matches must be identical regardless of input order
    assert len(res_forward.matches) == len(res_reversed.matches)
    for m1, m2 in zip(res_forward.matches, res_reversed.matches):
        assert m1.gold == m2.gold
        assert m1.prediction == m2.prediction
        assert m1.weight == m2.weight


def test_12_empty_gold():
    preds = [Prediction(type="PAN", start=10, end=20)]
    res = match_predictions([], preds)

    assert len(res.matches) == 0
    assert len(res.unmatched_gold) == 0
    assert len(res.unmatched_predictions) == 1
    assert res.unmatched_predictions[0] == preds[0]


def test_13_empty_predictions():
    gold = [GoldEntity(type="PAN", start=10, end=20)]
    res = match_predictions(gold, [])

    assert len(res.matches) == 0
    assert len(res.unmatched_gold) == 1
    assert len(res.unmatched_predictions) == 0


def test_14_both_empty():
    res = match_predictions([], [])
    assert len(res.matches) == 0
    assert len(res.unmatched_gold) == 0
    assert len(res.unmatched_predictions) == 0
    assert len(res.malformed_predictions) == 0


def test_15_malformed_prediction_boundaries():
    gold = [GoldEntity(type="PAN", start=10, end=20)]
    # Malformed start < 0 or end <= start
    p_bad1 = Prediction(type="PAN", start=-1, end=10)
    p_bad2 = Prediction(type="PAN", start=15, end=10)
    p_good = Prediction(type="PAN", start=10, end=20)

    res = match_predictions(gold, [p_bad1, p_bad2, p_good])

    assert len(res.matches) == 1
    assert res.matches[0].prediction == p_good
    assert len(res.malformed_predictions) == 2
    for mp in res.malformed_predictions:
        assert mp.status == "REJECTED"
        assert mp.rejection_reason == "INVALID_SPAN_OFFSETS"


def test_16_prediction_extending_beyond_text():
    text = "My PAN is ABCDE1234F."
    gold = [GoldEntity(type="PAN", start=10, end=20)]
    p_overflow = Prediction(type="PAN", start=10, end=30)  # text len is 21
    res = match_predictions(gold, [p_overflow], original_text=text)

    assert len(res.matches) == 0
    assert len(res.malformed_predictions) == 1
    assert res.malformed_predictions[0].status == "REJECTED"


def test_17_zero_length_prediction():
    gold = [GoldEntity(type="PAN", start=10, end=20)]
    p_zero = Prediction(type="PAN", start=10, end=10)
    res = match_predictions(gold, [p_zero])

    assert len(res.matches) == 0
    assert len(res.malformed_predictions) == 1


def test_18_unicode_code_point_offsets():
    text = "नाम: स्नेहा शर्मा।"  # Devanagari Unicode
    gold = [GoldEntity(type="PERSON", start=5, end=16)]
    pred = Prediction(type="PERSON", start=5, end=16)
    res = match_predictions(gold, [pred], original_text=text)

    assert len(res.matches) == 1
    assert res.matches[0].is_exact_span is True


def test_19_duplicate_predictions():
    # Detector emits duplicate predictions covering exact same span
    gold = [GoldEntity(type="PAN", start=10, end=20)]
    p1 = Prediction(type="PAN", start=10, end=20, confidence=0.9)
    p2 = Prediction(type="PAN", start=10, end=20, confidence=0.8)
    res = match_predictions(gold, [p1, p2])

    assert len(res.matches) == 1
    assert len(res.unmatched_predictions) == 1


def test_20_input_objects_remain_unchanged():
    gold = [GoldEntity(type="PAN", start=10, end=20)]
    preds = [
        Prediction(type="PAN", start=10, end=20),
        Prediction(type="PAN", start=-1, end=5),
    ]

    gold_copy = copy.deepcopy(gold)
    preds_copy = copy.deepcopy(preds)

    _ = match_predictions(gold, preds)

    assert gold == gold_copy
    assert preds == preds_copy
