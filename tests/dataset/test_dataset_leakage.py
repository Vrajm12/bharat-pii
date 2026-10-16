import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RELEASE_DIR = REPO_ROOT / "dataset" / "bharatpii-v1.0"

def load_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

def test_zero_text_leakage():
    train_recs = load_jsonl(RELEASE_DIR / "data" / "train" / "train.jsonl")
    val_recs = load_jsonl(RELEASE_DIR / "data" / "validation" / "val.jsonl")
    test_inputs = load_jsonl(RELEASE_DIR / "data" / "test" / "test_inputs.jsonl")

    train_texts = set(r["text"].strip() for r in train_recs)
    val_texts = set(r["text"].strip() for r in val_recs)
    test_texts = set(r["text"].strip() for r in test_inputs)

    assert len(train_texts & val_texts) == 0, "Train and Val share exact text!"
    assert len(train_texts & test_texts) == 0, "Train and Test share exact text!"
    assert len(val_texts & test_texts) == 0, "Val and Test share exact text!"

def test_zero_normalized_text_leakage():
    train_recs = load_jsonl(RELEASE_DIR / "data" / "train" / "train.jsonl")
    val_recs = load_jsonl(RELEASE_DIR / "data" / "validation" / "val.jsonl")
    test_inputs = load_jsonl(RELEASE_DIR / "data" / "test" / "test_inputs.jsonl")

    def norm(t): return " ".join(t.lower().split())

    train_norm = set(norm(r["text"]) for r in train_recs)
    val_norm = set(norm(r["text"]) for r in val_recs)
    test_norm = set(norm(r["text"]) for r in test_inputs)

    assert len(train_norm & val_norm) == 0
    assert len(train_norm & test_norm) == 0
    assert len(val_norm & test_norm) == 0
