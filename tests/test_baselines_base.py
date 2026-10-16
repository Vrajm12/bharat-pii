"""Unit tests for baselines/base.py abstract BaselineAdapter interface (PROJECT_SPEC.md §20.6, §20.7)."""

from __future__ import annotations

import pytest

from baselines.base import BaselineAdapter, validate_predictions
from benchmark.schema import Prediction


class ValidDummyAdapter(BaselineAdapter):
    """A conforming synthetic adapter for testing."""

    @property
    def system_name(self) -> str:
        return "synthetic_dummy"

    @property
    def system_version(self) -> str:
        return "1.0.0"

    def predict(self, text: str) -> list[Prediction]:
        if "ABCDE1234F" in text:
            idx = text.index("ABCDE1234F")
            return [
                Prediction(
                    type="PAN",
                    start=idx,
                    end=idx + len("ABCDE1234F"),
                    text="ABCDE1234F",
                    confidence=0.99,
                )
            ]
        return []


def test_1_baseline_adapter_is_abstract():
    with pytest.raises(TypeError):
        BaselineAdapter()  # type: ignore[abstract]


def test_2_system_name_is_required():
    class MissingNameAdapter(BaselineAdapter):
        @property
        def system_version(self) -> str:
            return "1.0"

        def predict(self, text: str) -> list[Prediction]:
            return []

    with pytest.raises(TypeError):
        MissingNameAdapter()  # type: ignore[abstract]


def test_3_system_version_is_required():
    class MissingVersionAdapter(BaselineAdapter):
        @property
        def system_name(self) -> str:
            return "name"

        def predict(self, text: str) -> list[Prediction]:
            return []

    with pytest.raises(TypeError):
        MissingVersionAdapter()  # type: ignore[abstract]


def test_4_predict_method_is_required():
    class MissingPredictAdapter(BaselineAdapter):
        @property
        def system_name(self) -> str:
            return "name"

        @property
        def system_version(self) -> str:
            return "1.0"

    with pytest.raises(TypeError):
        MissingPredictAdapter()  # type: ignore[abstract]


def test_5_predict_receives_raw_text():
    adapter = ValidDummyAdapter()
    preds = adapter.predict("My PAN is ABCDE1234F.")
    assert len(preds) == 1
    assert preds[0].type == "PAN"
    assert preds[0].start == 10
    assert preds[0].end == 20


def test_6_valid_predictions_use_original_text_code_point_offsets():
    text = "Hello ABCDE1234F world."
    adapter = ValidDummyAdapter()
    preds = adapter.predict(text)
    assert len(preds) == 1
    p = preds[0]
    assert text[p.start : p.end] == "ABCDE1234F"


def test_7_start_end_bounds_validation():
    text = "Short text."
    valid_p = Prediction(type="PAN", start=0, end=5)
    valid, rejected = validate_predictions([valid_p], original_text=text)
    assert len(valid) == 1
    assert len(rejected) == 0


def test_8_start_less_than_end_enforced():
    text = "Short text."
    p_bad1 = Prediction(type="PAN", start=5, end=5)  # Zero length
    p_bad2 = Prediction(type="PAN", start=6, end=4)  # Inverted
    valid, rejected = validate_predictions([p_bad1, p_bad2], original_text=text)
    assert len(valid) == 0
    assert len(rejected) == 2
    for r in rejected:
        assert r.status == "REJECTED"
        assert r.rejection_reason == "INVALID_SPAN_OFFSETS"


def test_9_prediction_text_matching_original_text():
    text = "My PAN is ABCDE1234F."
    p_correct = Prediction(type="PAN", start=10, end=20, text="ABCDE1234F")
    valid, rejected = validate_predictions([p_correct], original_text=text)
    assert len(valid) == 1
    assert len(rejected) == 0

    p_mismatch = Prediction(type="PAN", start=10, end=20, text="WRONG_TEXT")
    valid, rejected = validate_predictions([p_mismatch], original_text=text)
    assert len(valid) == 0
    assert len(rejected) == 1
    assert rejected[0].rejection_reason == "TEXT_SPAN_MISMATCH"


def test_10_malformed_offsets_are_rejected():
    text = "Short text."
    p_overflow = Prediction(type="PAN", start=5, end=50)  # Beyond text len (11)
    p_neg = Prediction(type="PAN", start=-5, end=5)
    valid, rejected = validate_predictions([p_overflow, p_neg], original_text=text)
    assert len(valid) == 0
    assert len(rejected) == 2


def test_11_out_of_taxonomy_prediction_types_remain_valid():
    text = "Organization is Google."
    p_org = Prediction(type="ORG", start=16, end=22, text="Google")
    valid, rejected = validate_predictions([p_org], original_text=text)
    assert len(valid) == 1
    assert valid[0].type == "ORG"
    assert valid[0].status == "VALID"


def test_12_adapter_cannot_silently_drop_malformed_predictions():
    text = "Text"
    p_bad = Prediction(type="PAN", start=10, end=20)
    valid, rejected = validate_predictions([p_bad], original_text=text)
    assert len(rejected) == 1
    assert rejected[0].status == "REJECTED"


def test_13_rejection_reason_is_deterministic():
    text = "Text"
    p1 = Prediction(type="PAN", start=-1, end=2)
    p2 = Prediction(type="PAN", start=-1, end=2)
    _, rej1 = validate_predictions([p1], original_text=text)
    _, rej2 = validate_predictions([p2], original_text=text)
    assert rej1[0].rejection_reason == rej2[0].rejection_reason == "INVALID_SPAN_OFFSETS"


def test_14_input_text_is_not_mutated():
    text = "Original Text 12345"
    text_copy = str(text)
    adapter = ValidDummyAdapter()
    _ = adapter.predict(text)
    assert text == text_copy


def test_15_adapter_metadata_is_deterministic():
    adapter = ValidDummyAdapter()
    assert adapter.system_name == "synthetic_dummy"
    assert adapter.system_version == "1.0.0"


def test_16_unicode_devanagari_offsets_code_point_indexing():
    text = "नाम: स्नेहा शर्मा।"  # Devanagari Unicode
    # 'स्नेहा शर्मा' starts at code-point 5, len is 12 -> ends at 17
    p = Prediction(type="PERSON", start=5, end=17, text="स्नेहा शर्मा")
    valid, rejected = validate_predictions([p], original_text=text)
    assert len(valid) == 1
    assert len(rejected) == 0
    assert text[valid[0].start : valid[0].end] == "स्नेहा शर्मा"
