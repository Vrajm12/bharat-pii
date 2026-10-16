import json
import hashlib
from collections import Counter
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

def test_hard_negative_zero_gold():
    test_inputs = load_jsonl(RELEASE_DIR / "data" / "test" / "test_inputs.jsonl")
    test_golds = load_jsonl(RELEASE_DIR / "annotations" / "test_gold_annotations.jsonl")
    gold_map = {r["record_id"]: r["gold_entities"] for r in test_golds}

    hard_negs = [r for r in test_inputs if r.get("base_kind") == "HARD_NEGATIVE" or str(r.get("base_id", "")).startswith("NEG_")]
    assert len(hard_negs) == 140, f"Expected 140 hard negatives, found {len(hard_negs)}"

    for r in hard_negs:
        assert len(gold_map[r["record_id"]]) == 0, f"Hard negative {r['record_id']} has non-zero gold entities!"

def test_adversarial_quota():
    test_inputs = load_jsonl(RELEASE_DIR / "data" / "test" / "test_inputs.jsonl")
    c = Counter()
    for r in test_inputs:
        pert = r.get("perturbation")
        if isinstance(pert, dict):
            pt = pert.get("perturbation_type") or pert.get("type")
            if pt and pt != "NONE":
                c[pt] += 1
    assert len(c) == 5
    for fam, cnt in c.items():
        assert cnt == 20, f"Adversarial quota violated for {fam}: got {cnt}"

def test_public_vs_controlled_boundary():
    archive_path = REPO_ROOT / "dataset" / "bharatpii-dataset-v1.0.tar.gz"
    assert archive_path.exists(), "Public archive must exist"

    import tarfile
    with tarfile.open(archive_path, "r:gz") as tar:
        names = tar.getnames()
        for n in names:
            assert not n.startswith("bharatpii-dataset-v1.0/annotations/"), f"Controlled annotation leaked in archive: {n}"

def test_sha256sums_manifest():
    sums_path = RELEASE_DIR / "SHA256SUMS.txt"
    assert sums_path.exists()
    with open(sums_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                expected_hash, rel_path = line.strip().split("  ")
                fpath = RELEASE_DIR / rel_path
                assert fpath.exists(), f"File {rel_path} in SHA256SUMS.txt does not exist"
                cur_hash = hashlib.sha256(fpath.read_bytes()).hexdigest()
                assert cur_hash == expected_hash, f"SHA256 mismatch for {rel_path}"
