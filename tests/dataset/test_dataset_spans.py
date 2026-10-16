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

def test_character_offset_slice_contract():
    train_recs = load_jsonl(RELEASE_DIR / "data" / "train" / "train.jsonl")
    val_recs = load_jsonl(RELEASE_DIR / "data" / "validation" / "val.jsonl")
    test_inputs = load_jsonl(RELEASE_DIR / "data" / "test" / "test_inputs.jsonl")
    test_golds = load_jsonl(RELEASE_DIR / "annotations" / "test_gold_annotations.jsonl")

    test_in_map = {r["record_id"]: r["text"] for r in test_inputs}

    total_checked = 0

    for r in train_recs + val_recs:
        txt = r["text"]
        for e in r.get("entities", []):
            assert txt[e["start"]:e["end"]] == e["text"]
            assert 0 <= e["start"] < e["end"] <= len(txt)
            total_checked += 1

    for r in test_golds:
        txt = test_in_map[r["record_id"]]
        for e in r.get("gold_entities", []):
            assert txt[e["start"]:e["end"]] == e["text"]
            assert 0 <= e["start"] < e["end"] <= len(txt)
            total_checked += 1

    assert total_checked == 1924, f"Expected 1,924 entities verified, got {total_checked}"

def test_unicode_indic_spans():
    test_inputs = load_jsonl(RELEASE_DIR / "data" / "test" / "test_inputs.jsonl")
    test_golds = load_jsonl(RELEASE_DIR / "annotations" / "test_gold_annotations.jsonl")
    test_in_map = {r["record_id"]: r["text"] for r in test_inputs}

    deva_checked = 0
    for r in test_golds:
        txt = test_in_map[r["record_id"]]
        for e in r.get("gold_entities", []):
            if any(ord(c) > 127 for c in e["text"]):
                assert txt[e["start"]:e["end"]] == e["text"]
                deva_checked += 1

    assert deva_checked == 24, f"Expected 24 Devanagari entities checked, got {deva_checked}"
