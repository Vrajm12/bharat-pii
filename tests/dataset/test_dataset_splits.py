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

def test_split_counts_and_disjointness():
    train_recs = load_jsonl(RELEASE_DIR / "data" / "train" / "train.jsonl")
    val_recs = load_jsonl(RELEASE_DIR / "data" / "validation" / "val.jsonl")
    test_inputs = load_jsonl(RELEASE_DIR / "data" / "test" / "test_inputs.jsonl")

    assert len(train_recs) == 1000, f"Expected 1,000 train records, got {len(train_recs)}"
    assert len(val_recs) == 200, f"Expected 200 val records, got {len(val_recs)}"
    assert len(test_inputs) == 964, f"Expected 964 test records, got {len(test_inputs)}"
    assert len(train_recs) + len(val_recs) + len(test_inputs) == 2164

    # Unique base IDs
    train_bases = set(r["base_id"] for r in train_recs)
    val_bases = set(r["base_id"] for r in val_recs)
    test_bases = set(r["base_id"] for r in test_inputs)

    assert len(train_bases) == 200
    assert len(val_bases) == 40
    assert len(test_bases) == 120

    # Base disjointness
    assert len(train_bases & val_bases) == 0, "Train and Val bases overlap!"
    assert len(train_bases & test_bases) == 0, "Train and Test bases overlap!"
    assert len(val_bases & test_bases) == 0, "Val and Test bases overlap!"

def test_unique_record_ids():
    train_recs = load_jsonl(RELEASE_DIR / "data" / "train" / "train.jsonl")
    val_recs = load_jsonl(RELEASE_DIR / "data" / "validation" / "val.jsonl")
    test_inputs = load_jsonl(RELEASE_DIR / "data" / "test" / "test_inputs.jsonl")

    rids = [r.get("variant_id") or r.get("record_id") for r in train_recs + val_recs + test_inputs]
    assert len(rids) == len(set(rids)) == 2164
