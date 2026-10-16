import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RELEASE_DIR = REPO_ROOT / "dataset" / "bharatpii-v1.0"

def test_label_schema_json():
    schema_path = RELEASE_DIR / "label_schema.json"
    assert schema_path.exists(), "label_schema.json must exist"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    assert schema["title"] == "BharatPIILabelSchema"
    assert len(schema["pii_categories"]) == 8
    assert schema["iob2_taxonomy"]["num_classes"] == 17
    assert len(schema["iob2_taxonomy"]["labels"]) == 17

def test_metadata_json():
    meta_path = RELEASE_DIR / "dataset_metadata.json"
    assert meta_path.exists(), "dataset_metadata.json must exist"
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["totals"]["total_records"] == 2164
    assert meta["totals"]["total_gold_entities"] == 1924
    assert meta["totals"]["total_unique_base_ids"] == 360

def test_train_val_test_record_schemas():
    train_path = RELEASE_DIR / "data" / "train" / "train.jsonl"
    val_path = RELEASE_DIR / "data" / "validation" / "val.jsonl"
    test_in_path = RELEASE_DIR / "data" / "test" / "test_inputs.jsonl"

    with open(train_path, "r", encoding="utf-8") as f:
        rec = json.loads(f.readline())
        assert {"variant_id", "base_id", "text", "entities", "split"}.issubset(rec.keys())

    with open(val_path, "r", encoding="utf-8") as f:
        rec = json.loads(f.readline())
        assert {"variant_id", "base_id", "text", "entities", "split"}.issubset(rec.keys())

    with open(test_in_path, "r", encoding="utf-8") as f:
        rec = json.loads(f.readline())
        assert {"record_id", "base_id", "text", "split", "base_kind"}.issubset(rec.keys())
        assert "entities" not in rec, "Public test inputs must not contain entities!"
