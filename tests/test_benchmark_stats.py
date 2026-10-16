"""Unit tests for benchmark/stats.py."""

from __future__ import annotations

import copy
import pytest

from benchmark.evaluator import EvaluationResult, Evaluator
from benchmark.schema import GoldEntity, Match, MatchingResult, Prediction
from benchmark.stats import (
    aggregate_by_base_kind,
    aggregate_by_decoy_class,
    aggregate_by_difficulty,
    aggregate_by_language,
    aggregate_by_perturbation_family,
    aggregate_by_pii_type,
    aggregate_by_semantic_role,
    aggregate_results,
    count_failures_by_category,
    group_and_aggregate,
)


def _make_eval_res(
    variant_id: str,
    gold_entities: list[GoldEntity],
    predictions: list[Prediction],
    meta: dict,
) -> EvaluationResult:
    evaluator = Evaluator()
    record = dict(meta)
    record["variant_id"] = variant_id
    record["entities"] = [g.to_dict() for g in gold_entities]
    return evaluator.evaluate_record(record, predictions)


def test_1_one_perfect_record():
    r1 = _make_eval_res(
        "PAN_001_EN_01",
        [GoldEntity(type="PAN", start=10, end=20)],
        [Prediction(type="PAN", start=10, end=20)],
        {"language": "EN", "pii_type": "PAN", "base_kind": "POSITIVE"},
    )
    score = aggregate_results([r1])
    assert score.n_gold == 1
    assert score.tp_exact == 1
    assert score.m1_precision == 1.0
    assert score.m3_f1 == 1.0


def test_2_multiple_records():
    r1 = _make_eval_res(
        "PAN_001_EN_01",
        [GoldEntity(type="PAN", start=10, end=20)],
        [Prediction(type="PAN", start=10, end=20)],
        {"language": "EN"},
    )
    r2 = _make_eval_res(
        "PHONE_001_EN_01",
        [GoldEntity(type="PHONE", start=10, end=20)],
        [],
        {"language": "EN"},
    )
    score = aggregate_results([r1, r2])
    assert score.n_gold == 2
    assert score.n_predictions == 1
    assert score.tp_type == 1
    assert score.m2_recall == 0.5


def test_3_pooled_vs_macro_distinction():
    # Record A: 1 gold, 1 correct prediction (Precision = 1.0)
    # Record B: 10 gold, 10 predictions where 0 correct (Precision = 0.0)
    # Macro avg precision would be (1.0 + 0.0) / 2 = 0.5
    # Pooled micro precision is 1 / 11 = 0.0909
    r_a = _make_eval_res(
        "A",
        [GoldEntity(type="PAN", start=0, end=10)],
        [Prediction(type="PAN", start=0, end=10)],
        {},
    )
    r_b = _make_eval_res(
        "B",
        [GoldEntity(type="PAN", start=i * 10, end=(i + 1) * 10) for i in range(10)],
        [Prediction(type="PHONE", start=i * 10, end=(i + 1) * 10) for i in range(10)],
        {},
    )
    score = aggregate_results([r_a, r_b])
    # Must be exact pooled 1 / 11, NOT macro 0.5
    assert abs(score.m1_precision - (1.0 / 11.0)) < 1e-6
    assert abs(score.m2_recall - (1.0 / 11.0)) < 1e-6


def test_4_zero_gold_hard_negative():
    evaluator = Evaluator()
    r = evaluator.evaluate_record(
        {"variant_id": "HN_01", "base_kind": "HARD_NEGATIVE", "text": "Call 1234"},
        [],
    )
    score = aggregate_results([r])
    assert score.n_gold == 0
    assert score.f4_false_pos == 0
    assert score.m3_f1 == 1.0


def test_5_false_positives_on_hard_negatives():
    evaluator = Evaluator()
    r = evaluator.evaluate_record(
        {"variant_id": "HN_01", "base_kind": "HARD_NEGATIVE", "text": "Call 1234"},
        [Prediction(type="PHONE", start=5, end=9)],
    )
    score = aggregate_results([r])
    assert score.n_gold == 0
    assert score.f4_false_pos == 1
    assert score.m6_fpr == 1.0


def test_6_language_grouping():
    r_en = _make_eval_res(
        "1",
        [GoldEntity(type="PAN", start=0, end=10)],
        [Prediction(type="PAN", start=0, end=10)],
        {"language": "EN"},
    )
    r_hi = _make_eval_res(
        "2",
        [GoldEntity(type="PAN", start=0, end=10)],
        [],
        {"language": "HINGLISH"},
    )
    by_lang = aggregate_by_language([r_en, r_hi])
    assert "EN" in by_lang
    assert "HINGLISH" in by_lang
    assert by_lang["EN"].m3_f1 == 1.0
    assert by_lang["HINGLISH"].m3_f1 == 0.0


def test_7_pii_type_grouping():
    r_pan = _make_eval_res("1", [GoldEntity(type="PAN", start=0, end=10)], [Prediction(type="PAN", start=0, end=10)], {"pii_type": "PAN"})
    r_phone = _make_eval_res("2", [GoldEntity(type="PHONE", start=0, end=10)], [], {"pii_type": "PHONE"})
    by_type = aggregate_by_pii_type([r_pan, r_phone])
    assert by_type["PAN"].tp_exact == 1
    assert by_type["PHONE"].tp_exact == 0


def test_8_semantic_role_grouping():
    r1 = _make_eval_res("1", [GoldEntity(type="PAN", start=0, end=10)], [Prediction(type="PAN", start=0, end=10)], {"semantic_role": "PRIMARY_SUBJECT"})
    by_role = aggregate_by_semantic_role([r1])
    assert "PRIMARY_SUBJECT" in by_role


def test_9_perturbation_grouping():
    r1 = _make_eval_res("1", [GoldEntity(type="PAN", start=0, end=10)], [Prediction(type="PAN", start=0, end=10)], {"perturbation": {"family": "A1"}})
    by_fam = aggregate_by_perturbation_family([r1])
    assert "A1" in by_fam
    assert by_fam["A1"].tp_exact == 1


def test_10_base_kind_grouping():
    r_pos = _make_eval_res("1", [GoldEntity(type="PAN", start=0, end=10)], [Prediction(type="PAN", start=0, end=10)], {"base_kind": "POSITIVE"})
    evaluator = Evaluator()
    r_hn = evaluator.evaluate_record({"variant_id": "2", "base_kind": "HARD_NEGATIVE"}, [])
    by_kind = aggregate_by_base_kind([r_pos, r_hn])
    assert "POSITIVE" in by_kind
    assert "HARD_NEGATIVE" in by_kind


def test_11_adversarial_family_grouping():
    r_a5 = _make_eval_res("1", [GoldEntity(type="PHONE", start=0, end=10)], [Prediction(type="PHONE", start=0, end=10)], {"perturbation": {"family": "A5"}})
    by_fam = aggregate_by_perturbation_family([r_a5])
    assert "A5" in by_fam


def test_12_decoy_class_grouping():
    evaluator = Evaluator()
    r_hn = evaluator.evaluate_record(
        {
            "variant_id": "HN_01",
            "base_kind": "HARD_NEGATIVE",
            "distractors": [{"type": "PHONE", "start": 0, "end": 10, "decoy_class": "NUMERIC_SHAPE"}],
        },
        [Prediction(type="PHONE", start=0, end=10)],
    )
    by_decoy = aggregate_by_decoy_class([r_hn])
    assert "NUMERIC_SHAPE" in by_decoy
    assert by_decoy["NUMERIC_SHAPE"].f4_false_pos == 1


def test_13_empty_groups():
    res = group_and_aggregate([], lambda r: r.record_metadata.get("language"))
    assert res == {}


def test_14_deterministic_ordering():
    r1 = _make_eval_res("1", [], [], {"language": "HINGLISH"})
    r2 = _make_eval_res("2", [], [], {"language": "EN"})
    r3 = _make_eval_res("3", [], [], {"language": "HI_DEVA_PII"})

    by_lang = aggregate_by_language([r1, r2, r3])
    keys = list(by_lang.keys())
    assert keys == ["EN", "HINGLISH", "HI_DEVA_PII"]  # Alphabetical stable order (N < _)


def test_15_input_immutability():
    r = _make_eval_res("1", [GoldEntity(type="PAN", start=0, end=10)], [], {})
    r_copy = copy.deepcopy(r)
    _ = aggregate_results([r])
    assert r == r_copy


def test_16_failure_counts_aggregation():
    r1 = _make_eval_res("1", [GoldEntity(type="PAN", start=0, end=10)], [], {"language": "HINGLISH", "difficulty": "ADVERSARIAL", "perturbation": {"family": "A1"}})
    counts = count_failures_by_category([r1])
    assert counts["F1"] == 1
    assert counts["MISSED_PII"] == 1
    assert counts["F8_ADVERSARIAL_FAILURE"] == 1
    assert counts["F7_FORMATTING_FAILURE"] == 1
    assert counts["F6_LINGUISTIC_FAILURE"] == 1
