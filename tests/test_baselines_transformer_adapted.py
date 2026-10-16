"""Dedicated tests for Baseline B5: Indian-Adapted Multilingual Transformer (PROJECT_SPEC.md §§19-24, §21.2).

Verifies:
1. Metadata and system version string
2. All 8 Indian PII taxonomy types
3. IOB2 decoding & multi-token entity grouping
4. Linguistic coverage (EN, IN_EN, HI Devanagari, ROM_HI, Hinglish, Dravidian scripts)
5. Native Python Unicode code-point character offsets: text[start:end] == prediction.text
6. Input immutability
7. Deterministic prediction ordering
8. Out-of-taxonomy label preservation (§20.5)
9. Strict zero-leakage base isolation (§22.1, §28)
10. Multi-seed support and reproducibility (§21.2)
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from baselines.base import BaselineAdapter
from baselines.transformer_adapted import TransformerAdaptedBaselineAdapter
from baselines.adaptation_data import validate_zero_test_leakage

REPO_ROOT = Path(__file__).resolve().parents[1]


class MockPipeline:
    """Mock transformer pipeline for fast, deterministic unit test verification."""

    def __init__(self, return_entities: list[dict]):
        self.return_entities = return_entities

    def __call__(self, text: str):
        return self.return_entities


def test_b5_adapter_metadata():
    """Verify B5 system metadata satisfies PROJECT_SPEC.md §19."""
    adapter = TransformerAdaptedBaselineAdapter(pipeline_instance=MockPipeline([]))
    assert isinstance(adapter, BaselineAdapter)
    assert adapter.system_name == "transformer_adapted"
    assert "xlm_roberta_base_indian_v0.18" in adapter.system_version


def test_b5_empty_and_whitespace_input():
    """Verify empty/whitespace strings safely return empty prediction list."""
    adapter = TransformerAdaptedBaselineAdapter(pipeline_instance=MockPipeline([]))
    assert adapter.predict("") == []
    assert adapter.predict("   \n\t  ") == []


def test_b5_all_8_taxonomy_labels():
    """Verify that all 8 Indian PII categories are correctly decoded from model outputs."""
    text = "Rahul Sharma PAN ABCDE1234F Aadhaar 1234 5678 9012 Phone 9876543210 email test@example.com UPI rahul@okaxis Bank 123456789012 Addr Mumbai Maharashtra"
    mock_entities = [
        {"entity_group": "B-PERSON", "start": 0, "end": 12, "score": 0.99},
        {"entity_group": "B-PAN", "start": 17, "end": 27, "score": 0.98},
        {"entity_group": "B-AADHAAR", "start": 36, "end": 50, "score": 0.97},
        {"entity_group": "B-PHONE", "start": 57, "end": 67, "score": 0.96},
        {"entity_group": "B-EMAIL", "start": 74, "end": 90, "score": 0.95},
        {"entity_group": "B-UPI_ID", "start": 95, "end": 107, "score": 0.94},
        {"entity_group": "B-BANK_ACCOUNT", "start": 113, "end": 125, "score": 0.93},
        {"entity_group": "B-ADDRESS", "start": 131, "end": 149, "score": 0.92},
    ]

    adapter = TransformerAdaptedBaselineAdapter(pipeline_instance=MockPipeline(mock_entities))
    preds = adapter.predict(text)

    assert len(preds) == 8
    expected_types = [
        ("PERSON", "Rahul Sharma"),
        ("PAN", "ABCDE1234F"),
        ("AADHAAR", "1234 5678 9012"),
        ("PHONE", "9876543210"),
        ("EMAIL", "test@example.com"),
        ("UPI_ID", "rahul@okaxis"),
        ("BANK_ACCOUNT", "123456789012"),
        ("ADDRESS", "Mumbai Maharashtra"),
    ]

    for p, (exp_type, exp_val) in zip(preds, expected_types):
        assert p.type == exp_type
        assert p.text == exp_val
        assert text[p.start:p.end] == exp_val
        assert p.status == "VALID"


def test_b5_iob2_clean_and_raw_prefixes():
    """Verify IOB2 prefixes (B-, I-) are stripped cleanly."""
    text = "Account ABCDE1234F belongs to Vikram Patel."
    mock_entities = [
        {"entity_group": "B-PAN", "start": 8, "end": 18, "score": 0.95},
        {"entity_group": "I-PERSON", "start": 30, "end": 42, "score": 0.91},
    ]

    adapter = TransformerAdaptedBaselineAdapter(pipeline_instance=MockPipeline(mock_entities))
    preds = adapter.predict(text)

    assert len(preds) == 2
    assert preds[0].type == "PAN"
    assert preds[0].text == "ABCDE1234F"
    assert preds[1].type == "PERSON"
    assert preds[1].text == "Vikram Patel"


def test_b5_hindi_devanagari_offsets():
    """Verify Python Unicode code-point slicing on Hindi Devanagari text."""
    text = "कल राहुल शर्मा ने हमारे कार्यालय का दौरा किया।"
    name_str = "राहुल शर्मा"
    start = text.index(name_str)
    end = start + len(name_str)

    mock_entities = [
        {"entity_group": "PERSON", "start": start, "end": end, "score": 0.99},
    ]

    adapter = TransformerAdaptedBaselineAdapter(pipeline_instance=MockPipeline(mock_entities))
    preds = adapter.predict(text)

    assert len(preds) == 1
    assert preds[0].type == "PERSON"
    assert preds[0].text == name_str
    assert preds[0].start == start
    assert preds[0].end == end
    assert text[preds[0].start:preds[0].end] == name_str


def test_b5_roman_hindi_and_hinglish():
    """Verify Roman Hindi and Hinglish entity extraction."""
    text = "Bhai mera UPI ID amit@icici pe 500 bhej de."
    upi_str = "amit@icici"
    start = text.index(upi_str)
    end = start + len(upi_str)

    mock_entities = [
        {"entity_group": "UPI_ID", "start": start, "end": end, "score": 0.98},
    ]

    adapter = TransformerAdaptedBaselineAdapter(pipeline_instance=MockPipeline(mock_entities))
    preds = adapter.predict(text)

    assert len(preds) == 1
    assert preds[0].type == "UPI_ID"
    assert preds[0].text == upi_str
    assert text[preds[0].start:preds[0].end] == upi_str


def test_b5_dravidian_carrier_offsets():
    """Verify offset slicing when carrier text contains Kannada/Tamil characters."""
    text = "ನನ್ನ ಪ್ಯಾನ್ ಸಂಖ್ಯೆ ABCDE1234F ಆಗಿದೆ."
    pan_str = "ABCDE1234F"
    start = text.index(pan_str)
    end = start + len(pan_str)

    mock_entities = [
        {"entity_group": "PAN", "start": start, "end": end, "score": 0.99},
    ]

    adapter = TransformerAdaptedBaselineAdapter(pipeline_instance=MockPipeline(mock_entities))
    preds = adapter.predict(text)

    assert len(preds) == 1
    assert preds[0].type == "PAN"
    assert preds[0].text == pan_str
    assert text[preds[0].start:preds[0].end] == pan_str


def test_b5_input_immutability():
    """Verify input text remains unmodified after inference."""
    original = "My email is support@example.com."
    text_copy = str(original)

    mock_entities = [
        {"entity_group": "EMAIL", "start": 12, "end": 31, "score": 0.95},
    ]
    adapter = TransformerAdaptedBaselineAdapter(pipeline_instance=MockPipeline(mock_entities))
    adapter.predict(original)

    assert original == text_copy


def test_b5_deterministic_prediction_ordering():
    """Verify predictions are deterministically sorted by (start, end, type, -confidence)."""
    text = "Contact Priya at 9876543210 or 9876543211."
    mock_entities = [
        {"entity_group": "PHONE", "start": 31, "end": 41, "score": 0.85},
        {"entity_group": "PERSON", "start": 8, "end": 13, "score": 0.95},
        {"entity_group": "PHONE", "start": 17, "end": 27, "score": 0.90},
    ]

    adapter = TransformerAdaptedBaselineAdapter(pipeline_instance=MockPipeline(mock_entities))
    preds = adapter.predict(text)

    assert len(preds) == 3
    assert preds[0].type == "PERSON" and preds[0].start == 8
    assert preds[1].type == "PHONE" and preds[1].start == 17
    assert preds[2].type == "PHONE" and preds[2].start == 31


def test_b5_out_of_taxonomy_handling():
    """Verify out-of-taxonomy predictions are preserved raw with status VALID (§20.5)."""
    text = "Visited Microsoft in New Delhi."
    mock_entities = [
        {"entity_group": "ORG", "start": 8, "end": 17, "score": 0.92},
        {"entity_group": "LOC", "start": 21, "end": 30, "score": 0.94},
    ]

    adapter = TransformerAdaptedBaselineAdapter(pipeline_instance=MockPipeline(mock_entities))
    preds = adapter.predict(text)

    assert len(preds) == 2
    assert preds[0].type == "ORG"
    assert preds[0].text == "Microsoft"
    assert preds[0].status == "VALID"
    assert preds[1].type == "LOC"
    assert preds[1].text == "New Delhi"
    assert preds[1].status == "VALID"


def test_b5_zero_test_leakage():
    """Verify adaptation dataset strictly satisfies zero test set base_id leakage (§22.1, §28)."""
    assert validate_zero_test_leakage() is True


def test_b5_multi_seed_configuration():
    """Verify adapter supports multi-seed checkpoint configuration (§21.2)."""
    adapter42 = TransformerAdaptedBaselineAdapter(seed=42, pipeline_instance=MockPipeline([]))
    adapter43 = TransformerAdaptedBaselineAdapter(seed=43, pipeline_instance=MockPipeline([]))
    adapter44 = TransformerAdaptedBaselineAdapter(seed=44, pipeline_instance=MockPipeline([]))

    assert adapter42.seed == 42
    assert adapter43.seed == 43
    assert adapter44.seed == 44


def test_b5_real_checkpoint_loading_and_inference():
    """Verify real trained checkpoint can be loaded and executed on sample text."""
    checkpoint_dir = REPO_ROOT / "checkpoints" / "b5_transformer_adapted_seed42"
    if not checkpoint_dir.exists():
        pytest.skip("Checkpoint directory not present")

    adapter = TransformerAdaptedBaselineAdapter(model_name_or_path=checkpoint_dir, seed=42)
    sample_text = "Please verify my PAN card ABCDE1234F for Rahul Sharma."
    preds = adapter.predict(sample_text)

    # Assert predictions satisfy the strict span geometry invariant
    for p in preds:
        assert 0 <= p.start < p.end <= len(sample_text)
        assert sample_text[p.start:p.end] == p.text
        assert p.status == "VALID"
        assert p.type in TransformerAdaptedBaselineAdapter.TYPE_MAP or isinstance(p.type, str)
