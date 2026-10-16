"""Single-string inference, Unicode handling, and character slice tests."""

from pathlib import Path
import pytest
from bharatpii import BharatPII

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = REPO_ROOT / "models" / "bharatpii-crf-v1.0"


@pytest.fixture(scope="module")
def model():
    return BharatPII.from_pretrained(MODEL_DIR)


def test_empty_string_inference(model):
    res = model.predict("")
    assert len(res) == 0
    assert res.text == ""

    res2 = model.predict("   ")
    assert len(res2) == 0


def test_single_english_inference(model):
    text = "Call Rahul Sharma at 9876543210 regarding PAN ABCDE1234F."
    res = model.predict(text)
    assert len(res) >= 2
    for ent in res:
        assert text[ent.start:ent.end] == ent.text
        assert ent.label in ["PERSON", "PHONE", "PAN"]
        if ent.score is not None:
            assert 0.0 <= ent.score <= 1.0


def test_devanagari_and_code_mixed_inference(model):
    text = "मेरा नाम राहुल शर्मा है और मेरा ईमेल rahul@example.com है।"
    res = model.predict(text)
    assert len(res) >= 1
    for ent in res:
        assert text[ent.start:ent.end] == ent.text
        assert 0.0 <= ent.score <= 1.0


def test_character_slice_invariant_across_scripts(model):
    texts = [
        "Aadhaar 1234 5678 9012 registered to Priya in Bengaluru 560001",
        "Send 500 rupees to priya@upi or call +919876543210",
        "फ्लैट 101, सूर्य अपार्टमेंट, एमजी रोड, मुंबई 400001",
    ]
    for t in texts:
        res = model.predict(t)
        for ent in res:
            assert t[ent.start:ent.end] == ent.text
            assert ent.start >= 0
            assert ent.end > ent.start
