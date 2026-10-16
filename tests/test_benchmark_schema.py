"""Unit tests for benchmark/schema.py."""

from __future__ import annotations

import pytest

from benchmark.schema import GoldEntity, Match, MatchingResult, Prediction


def test_prediction_creation_and_fields():
    p = Prediction(
        type="PAN",
        start=10,
        end=20,
        text="ABCDE1234F",
        confidence=0.95,
        variant_id="PAN_001_EN_01",
    )
    assert p.type == "PAN"
    assert p.start == 10
    assert p.end == 20
    assert p.text == "ABCDE1234F"
    assert p.confidence == 0.95
    assert p.variant_id == "PAN_001_EN_01"
    assert p.status == "VALID"
    assert p.rejection_reason is None


def test_prediction_structural_validation():
    # Valid
    assert Prediction(type="PAN", start=0, end=10).is_structurally_valid(15) is True
    assert Prediction(type="PAN", start=0, end=15).is_structurally_valid(15) is True
    assert Prediction(type="PAN", start=0, end=15).is_structurally_valid(None) is True

    # Invalid start < 0
    assert Prediction(type="PAN", start=-1, end=10).is_structurally_valid() is False

    # Invalid end <= start
    assert Prediction(type="PAN", start=10, end=10).is_structurally_valid() is False
    assert Prediction(type="PAN", start=10, end=5).is_structurally_valid() is False

    # Invalid beyond text length
    assert Prediction(type="PAN", start=10, end=20).is_structurally_valid(15) is False


def test_prediction_serialization_roundtrip():
    p = Prediction(
        type="PERSON",
        start=5,
        end=17,
        text="Sneha Sharma",
        confidence=0.88,
        variant_id="PERSON_001_EN_01",
    )
    d = p.to_dict()
    assert d["type"] == "PERSON"
    assert d["start"] == 5
    assert d["end"] == 17
    assert d["text"] == "Sneha Sharma"
    assert d["confidence"] == 0.88
    assert d["variant_id"] == "PERSON_001_EN_01"
    assert "status" not in d

    p_recovered = Prediction.from_dict(d)
    assert p == p_recovered


def test_rejected_prediction_serialization():
    p = Prediction(
        type="PHONE",
        start=10,
        end=5,
        status="REJECTED",
        rejection_reason="INVALID_SPAN_OFFSETS",
    )
    d = p.to_dict()
    assert d["status"] == "REJECTED"
    assert d["rejection_reason"] == "INVALID_SPAN_OFFSETS"

    p_recovered = Prediction.from_dict(d)
    assert p == p_recovered


def test_gold_entity_roundtrip():
    g = GoldEntity(
        type="AADHAAR",
        start=20,
        end=32,
        base_pii_value="123456789012",
        realized_pii_value="123456789012",
        occurrence_index=1,
    )
    d = g.to_dict()
    assert d["type"] == "AADHAAR"
    assert d["start"] == 20
    assert d["end"] == 32
    assert d["occurrence_index"] == 1

    g_recovered = GoldEntity.from_dict(d)
    assert g == g_recovered
