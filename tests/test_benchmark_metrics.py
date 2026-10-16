"""Unit tests for benchmark/metrics.py.

Tests all 20 required metric conditions and scientific invariants from PROJECT_SPEC.md §20.4, §20.5:
1. perfect prediction
2. zero predictions
3. zero gold
4. wrong type
5. wrong span
6. partial overlap
7. mixed correct/wrong/missed predictions
8. multiple predictions
9. overlapping predictions
10. empty/zero-denominator cases
11. hard-negative true negative
12. hard-negative false positive
13. distractor attribution
14. adversarial A1
15. adversarial A3
16. adversarial A5
17. partition identity invariant
18. metric range invariants
19. matching result is consumed rather than recomputed
20. input immutability
"""

from __future__ import annotations

import copy
import pytest

from benchmark.matching import match_predictions
from benchmark.metrics import MetricScore, aggregate_metrics, compute_metrics
from benchmark.schema import GoldEntity, Match, MatchingResult, Prediction


def test_1_perfect_prediction():
    gold = [GoldEntity(type="PAN", start=10, end=20)]
    preds = [Prediction(type="PAN", start=10, end=20)]
    match_res = match_predictions(gold, preds)
    score = compute_metrics(match_res)

    assert score.n_gold == 1
    assert score.n_predictions == 1
    assert score.tp_type == 1
    assert score.tp_exact == 1
    assert score.localized == 1
    assert score.m1_precision == 1.0
    assert score.m2_recall == 1.0
    assert score.m3_f1 == 1.0
    assert score.m4_exact_f1 == 1.0
    assert score.m5_type_accuracy == 1.0
    assert score.m6_fpr == 0.0
    assert score.f1_missed == 0
    assert score.f2_wrong_span == 0
    assert score.f3_wrong_type == 0
    assert score.f4_false_pos == 0


def test_2_zero_predictions():
    gold = [GoldEntity(type="PAN", start=10, end=20)]
    match_res = match_predictions(gold, [])
    score = compute_metrics(match_res)

    assert score.n_gold == 1
    assert score.n_predictions == 0
    assert score.tp_type == 0
    assert score.tp_exact == 0
    assert score.localized == 0
    assert score.m1_precision == 0.0
    assert score.m2_recall == 0.0
    assert score.m3_f1 == 0.0
    assert score.m4_exact_f1 == 0.0
    assert score.m5_type_accuracy == 0.0
    assert score.m6_fpr == 0.0
    assert score.f1_missed == 1


def test_3_zero_gold_false_positives():
    preds = [Prediction(type="PAN", start=10, end=20)]
    match_res = match_predictions([], preds)
    score = compute_metrics(match_res)

    assert score.n_gold == 0
    assert score.n_predictions == 1
    assert score.tp_type == 0
    assert score.tp_exact == 0
    assert score.localized == 0
    assert score.m1_precision == 0.0
    assert score.m2_recall == 0.0
    assert score.m3_f1 == 0.0
    assert score.m4_exact_f1 == 0.0
    assert score.m5_type_accuracy == 0.0
    assert score.m6_fpr == 1.0
    assert score.f4_false_pos == 1


def test_4_wrong_type():
    gold = [GoldEntity(type="AADHAAR", start=10, end=22)]
    preds = [Prediction(type="BANK_ACCOUNT", start=10, end=22)]
    match_res = match_predictions(gold, preds)
    score = compute_metrics(match_res)

    assert score.n_gold == 1
    assert score.n_predictions == 1
    assert score.tp_type == 0
    assert score.tp_exact == 0
    assert score.localized == 1  # localized, but wrong type
    assert score.m1_precision == 0.0
    assert score.m2_recall == 0.0
    assert score.m3_f1 == 0.0
    assert score.m4_exact_f1 == 0.0
    assert score.m5_type_accuracy == 0.0
    assert score.m6_fpr == 0.0  # matched, not unmatched noise
    assert score.f3_wrong_type == 1
    assert score.f1_missed == 0
    assert score.f2_wrong_span == 0


def test_5_wrong_span():
    gold = [GoldEntity(type="PERSON", start=10, end=20)]
    preds = [Prediction(type="PERSON", start=12, end=22)]
    match_res = match_predictions(gold, preds)
    score = compute_metrics(match_res)

    assert score.n_gold == 1
    assert score.n_predictions == 1
    assert score.tp_type == 1  # Type match with overlap
    assert score.tp_exact == 0  # Inexact span
    assert score.localized == 1
    assert score.m1_precision == 1.0
    assert score.m2_recall == 1.0
    assert score.m3_f1 == 1.0  # Lenient F1 is 1.0
    assert score.m4_exact_f1 == 0.0  # Strict F1 is 0.0
    assert score.m5_type_accuracy == 1.0
    assert score.f2_wrong_span == 1
    assert score.f1_missed == 0
    assert score.f3_wrong_type == 0


def test_6_partial_overlap_identity():
    # Identity: M2 = M5 * (L / N)
    gold = [
        GoldEntity(type="PERSON", start=0, end=10),
        GoldEntity(type="PHONE", start=20, end=30),
    ]
    preds = [
        Prediction(type="PERSON", start=2, end=10),  # Right type, partial span
        Prediction(type="AADHAAR", start=20, end=30),  # Wrong type, exact span
    ]
    match_res = match_predictions(gold, preds)
    score = compute_metrics(match_res)

    assert score.n_gold == 2
    assert score.tp_type == 1
    assert score.localized == 2
    assert score.m2_recall == 0.5
    assert score.m5_type_accuracy == 0.5
    # Verify M2 == M5 * (L / N) -> 0.5 == 0.5 * (2 / 2)
    assert abs(score.m2_recall - (score.m5_type_accuracy * (score.localized / score.n_gold))) < 1e-6


def test_7_mixed_correct_wrong_missed():
    gold = [
        GoldEntity(type="PAN", start=0, end=10),
        GoldEntity(type="PHONE", start=20, end=30),
        GoldEntity(type="EMAIL", start=40, end=60),
    ]
    preds = [
        Prediction(type="PAN", start=0, end=10),  # Exact match (TP_exact)
        Prediction(type="PHONE", start=22, end=30),  # Inexact span (F2)
        Prediction(type="UNKNOWN", start=80, end=90),  # False positive (F4)
        # EMAIL is missed (F1)
    ]
    match_res = match_predictions(gold, preds)
    score = compute_metrics(match_res)

    assert score.n_gold == 3
    assert score.n_predictions == 3
    assert score.tp_type == 2
    assert score.tp_exact == 1
    assert score.localized == 2
    assert score.f1_missed == 1
    assert score.f2_wrong_span == 1
    assert score.f3_wrong_type == 0
    assert score.f4_false_pos == 1
    # Check partition invariant
    assert score.f1_missed + score.f2_wrong_span + score.f3_wrong_type + score.tp_exact == score.n_gold


def test_8_multiple_predictions_aggregation():
    res1 = match_predictions(
        [GoldEntity(type="PAN", start=0, end=10)],
        [Prediction(type="PAN", start=0, end=10)],
    )
    res2 = match_predictions(
        [GoldEntity(type="PHONE", start=0, end=10)],
        [],
    )
    agg_score = aggregate_metrics([res1, res2])

    assert agg_score.n_gold == 2
    assert agg_score.n_predictions == 1
    assert agg_score.tp_type == 1
    assert agg_score.tp_exact == 1
    assert agg_score.m1_precision == 1.0
    assert agg_score.m2_recall == 0.5
    assert abs(agg_score.m3_f1 - (2.0 / 3.0)) < 1e-6


def test_9_overlapping_predictions():
    # Detector produces two predictions for one gold
    gold = [GoldEntity(type="PAN", start=10, end=20)]
    preds = [
        Prediction(type="PAN", start=10, end=20),
        Prediction(type="PAN", start=12, end=18),
    ]
    match_res = match_predictions(gold, preds)
    score = compute_metrics(match_res)

    assert score.n_gold == 1
    assert score.n_predictions == 2
    assert score.tp_type == 1
    assert score.m1_precision == 0.5
    assert score.m2_recall == 1.0
    assert score.m6_fpr == 0.5


def test_10_empty_zero_denominator():
    match_res = match_predictions([], [])
    score = compute_metrics(match_res)

    assert score.n_gold == 0
    assert score.n_predictions == 0
    assert score.m1_precision == 1.0
    assert score.m2_recall == 1.0
    assert score.m3_f1 == 1.0
    assert score.m4_exact_f1 == 1.0
    assert score.m5_type_accuracy == 0.0
    assert score.m6_fpr == 0.0


def test_11_hard_negative_true_negative():
    # Hard negative record with 0 predictions -> true negative
    match_res = match_predictions([], [])
    score = compute_metrics(match_res)

    assert score.n_gold == 0
    assert score.n_predictions == 0
    assert score.tp_type == 0
    assert score.tp_exact == 0
    assert score.localized == 0
    assert score.f4_false_pos == 0
    assert score.m3_f1 == 1.0


def test_12_hard_negative_false_positive():
    # Hard negative record with 1 prediction -> false positive
    preds = [Prediction(type="PHONE", start=10, end=20)]
    match_res = match_predictions([], preds)
    score = compute_metrics(match_res)

    assert score.n_gold == 0
    assert score.n_predictions == 1
    assert score.tp_type == 0
    assert score.f4_false_pos == 1
    assert score.m1_precision == 0.0
    assert score.m6_fpr == 1.0


def test_13_distractor_attribution_behavior():
    # Matching does not ingest distractors as gold entities
    preds = [Prediction(type="NUMERIC_SHAPE", start=10, end=20)]
    match_res = match_predictions([], preds)
    score = compute_metrics(match_res)

    assert score.n_gold == 0
    assert score.f4_false_pos == 1


def test_14_adversarial_a1():
    # A1 Spaced gold entity
    gold = [GoldEntity(type="PAN", start=17, end=36, realized_pii_value="F Z Z F N 0 2 5 6 Z")]
    pred = Prediction(type="PAN", start=17, end=36)
    match_res = match_predictions(gold, [pred])
    score = compute_metrics(match_res)

    assert score.tp_exact == 1
    assert score.m3_f1 == 1.0


def test_15_adversarial_a3():
    # A3 Label obfuscation: gold span is unperturbed value
    gold = [GoldEntity(type="PAN", start=15, end=25, realized_pii_value="FZZFN0256Z")]
    pred = Prediction(type="PAN", start=15, end=25)
    match_res = match_predictions(gold, [pred])
    score = compute_metrics(match_res)

    assert score.tp_exact == 1
    assert score.m3_f1 == 1.0


def test_16_adversarial_a5():
    # A5 Character variation: gold span is transformed value
    gold = [GoldEntity(type="PHONE", start=19, end=29, realized_pii_value="7B34657871")]
    pred = Prediction(type="PHONE", start=19, end=29)
    match_res = match_predictions(gold, [pred])
    score = compute_metrics(match_res)

    assert score.tp_exact == 1
    assert score.m3_f1 == 1.0


def test_17_partition_identity_invariant():
    gold = [
        GoldEntity(type="PERSON", start=0, end=10),
        GoldEntity(type="PHONE", start=20, end=30),
        GoldEntity(type="EMAIL", start=40, end=50),
        GoldEntity(type="AADHAAR", start=60, end=72),
    ]
    preds = [
        Prediction(type="PERSON", start=0, end=10),  # TP_exact
        Prediction(type="PHONE", start=22, end=30),  # F2 (WRONG_SPAN)
        Prediction(type="BANK_ACCOUNT", start=40, end=50),  # F3 (WRONG_TYPE)
        # AADHAAR is F1 (MISSED_PII)
    ]
    match_res = match_predictions(gold, preds)
    score = compute_metrics(match_res)

    assert score.tp_exact == 1
    assert score.f2_wrong_span == 1
    assert score.f3_wrong_type == 1
    assert score.f1_missed == 1
    assert score.f1_missed + score.f2_wrong_span + score.f3_wrong_type + score.tp_exact == score.n_gold


def test_18_metric_range_invariants():
    gold = [GoldEntity(type="PAN", start=0, end=10)]
    preds = [Prediction(type="PAN", start=0, end=5)]
    score = compute_metrics(match_predictions(gold, preds))

    for m in [
        score.m1_precision,
        score.m2_recall,
        score.m3_f1,
        score.m4_exact_f1,
        score.m5_type_accuracy,
        score.m6_fpr,
    ]:
        assert 0.0 <= m <= 1.0


def test_19_matching_result_consumed():
    match_res = MatchingResult(
        matches=[
            Match(
                gold=GoldEntity(type="PAN", start=0, end=10),
                prediction=Prediction(type="PAN", start=0, end=10),
                weight=3.0,
                iou=1.0,
                is_type_match=True,
                is_exact_span=True,
            )
        ],
        unmatched_gold=[],
        unmatched_predictions=[],
        malformed_predictions=[],
    )
    score = compute_metrics(match_res)
    assert score.tp_exact == 1
    assert score.m1_precision == 1.0


def test_20_input_immutability():
    match_res = MatchingResult(
        matches=[
            Match(
                gold=GoldEntity(type="PAN", start=0, end=10),
                prediction=Prediction(type="PAN", start=0, end=10),
                weight=3.0,
                iou=1.0,
                is_type_match=True,
                is_exact_span=True,
            )
        ],
        unmatched_gold=[],
        unmatched_predictions=[],
        malformed_predictions=[],
    )
    match_copy = copy.deepcopy(match_res)
    _ = compute_metrics(match_res)

    assert match_res == match_copy
