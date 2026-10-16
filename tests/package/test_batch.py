"""Batch prediction order, independence, and isolation tests."""

from pathlib import Path
import pytest
from bharatpii import BharatPII

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = REPO_ROOT / "models" / "bharatpii-crf-v1.0"


@pytest.fixture(scope="module")
def model():
    return BharatPII.from_pretrained(MODEL_DIR)


def test_batch_ordering_and_independence(model):
    texts = [
        "Call Rahul Sharma at 9876543210 regarding PAN ABCDE1234F.",
        "No PII here in this routine financial update.",
        "Send payment to priya@oksbi or contact amit@example.com.",
    ]

    batch_results = model.predict_batch(texts)
    assert len(batch_results) == 3

    # Individual predictions
    indiv_results = [model.predict(t) for t in texts]

    for b_res, i_res, orig_text in zip(batch_results, indiv_results, texts):
        assert b_res.text == orig_text
        assert len(b_res) == len(i_res)
        for b_ent, i_ent in zip(b_res.entities, i_res.entities):
            assert b_ent.text == i_ent.text
            assert b_ent.start == i_ent.start
            assert b_ent.end == i_ent.end
            assert b_ent.label == i_ent.label
            assert abs((b_ent.score or 0.0) - (i_ent.score or 0.0)) < 1e-5
