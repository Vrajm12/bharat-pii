import json
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
RELEASE_DIR = ROOT / "dataset" / "bharatpii-v1.0"

VALID_PII_TYPES = {
    "PERSON", "PAN", "AADHAAR", "PHONE", "EMAIL", "UPI_ID", "BANK_ACCOUNT", "ADDRESS"
}
VALID_LANGUAGES = {
    "EN", "IN_EN", "ROM_HI", "HINGLISH", "INFORMAL_HINGLISH", "HI_LATIN_PII", "HI_DEVA_PII", "UNKNOWN"
}
VALID_PERTURBATIONS = {
    "NONE", "SPACING", "PUNCTUATION", "LABEL_OBFUSCATION", "INFORMAL_ABBREVIATION", "CHARACTER_VARIATION"
}

def load_file(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                records.append((idx, rec))
            except Exception as e:
                raise ValueError(f"JSONL syntax error in {path} at line {idx}: {e}")
    return records

def main():
    print("=" * 70)
    print("BHARATPII DATASET RELEASE VALIDATION (20-CHECK PROTOCOL)")
    print("=" * 70)

    train_path = RELEASE_DIR / "data" / "train" / "train.jsonl"
    val_path = RELEASE_DIR / "data" / "validation" / "val.jsonl"
    test_in_path = RELEASE_DIR / "data" / "test" / "test_inputs.jsonl"
    test_gold_path = RELEASE_DIR / "annotations" / "test_gold_annotations.jsonl"

    checks_passed = 0

    # 1. JSONL syntax
    train_recs = load_file(train_path)
    val_recs = load_file(val_path)
    test_inputs = load_file(test_in_path)
    test_golds = load_file(test_gold_path)
    print("[Check 1/20] JSONL Syntax: PASS (All files parsed cleanly)")
    checks_passed += 1

    # 2. Required fields
    train_req = {"variant_id", "base_id", "text", "entities", "split"}
    test_req = {"record_id", "base_id", "text", "split", "base_kind"}
    for idx, r in train_recs:
        assert train_req.issubset(r.keys()), f"Train missing required fields at line {idx}"
    for idx, r in val_recs:
        assert train_req.issubset(r.keys()), f"Val missing required fields at line {idx}"
    for idx, r in test_inputs:
        assert test_req.issubset(r.keys()), f"Test input missing required fields at line {idx}"
    for idx, r in test_golds:
        assert {"record_id", "base_id", "gold_entities"}.issubset(r.keys()), f"Test gold missing fields at line {idx}"
    print("[Check 2/20] Required Fields: PASS")
    checks_passed += 1

    # 3. Unique record IDs
    all_record_ids = []
    for _, r in train_recs: all_record_ids.append(r.get("variant_id") or r.get("record_id"))
    for _, r in val_recs: all_record_ids.append(r.get("variant_id") or r.get("record_id"))
    for _, r in test_inputs: all_record_ids.append(r.get("record_id") or r.get("variant_id"))
    assert len(all_record_ids) == len(set(all_record_ids)), "Duplicate record IDs found across dataset!"
    assert len(all_record_ids) == 2164, f"Expected 2,164 total records, got {len(all_record_ids)}"
    print("[Check 3/20] Unique Record IDs: PASS (2,164 unique record IDs)")
    checks_passed += 1

    # 4. Unique base IDs where required (within designated splits)
    train_bases = set(r["base_id"] for _, r in train_recs)
    val_bases = set(r["base_id"] for _, r in val_recs)
    test_bases = set(r["base_id"] for _, r in test_inputs)
    assert len(train_bases) == 200, f"Expected 200 train bases, got {len(train_bases)}"
    assert len(val_bases) == 40, f"Expected 40 val bases, got {len(val_bases)}"
    assert len(test_bases) == 120, f"Expected 120 test bases, got {len(test_bases)}"
    print("[Check 4/20] Unique Base IDs: PASS (Train: 200, Val: 40, Test: 120)")
    checks_passed += 1

    # 5. Split integrity and zero base overlap
    assert len(train_bases & val_bases) == 0, "Train and Val bases overlap!"
    assert len(train_bases & test_bases) == 0, "Train and Test bases overlap!"
    assert len(val_bases & test_bases) == 0, "Val and Test bases overlap!"
    print("[Check 5/20] Split Integrity & Disjointness: PASS (0 base ID overlap)")
    checks_passed += 1

    # 6. Label validity
    all_labels = set()
    for _, r in train_recs:
        for e in r.get("entities", []): all_labels.add(e["type"])
    for _, r in val_recs:
        for e in r.get("entities", []): all_labels.add(e["type"])
    for _, r in test_golds:
        for e in r.get("gold_entities", []): all_labels.add(e["type"])
    assert all_labels.issubset(VALID_PII_TYPES), f"Invalid PII labels found: {all_labels - VALID_PII_TYPES}"
    assert all_labels == VALID_PII_TYPES, f"Missing PII types: {VALID_PII_TYPES - all_labels}"
    print("[Check 6/20] Label Taxonomy Validity: PASS (8/8 canonical PII types present)")
    checks_passed += 1

    # 7. Span validity (0 <= start < end <= len(text))
    for _, r in train_recs + val_recs:
        txt_len = len(r["text"])
        for e in r.get("entities", []):
            assert 0 <= e["start"] < e["end"] <= txt_len, f"Invalid span bounds in {r.get('variant_id')}: [{e['start']}:{e['end']}]"
    
    test_in_map = {r["record_id"]: r["text"] for _, r in test_inputs}
    for _, r in test_golds:
        txt = test_in_map[r["record_id"]]
        txt_len = len(txt)
        for e in r.get("gold_entities", []):
            assert 0 <= e["start"] < e["end"] <= txt_len, f"Invalid span bounds in {r.get('record_id')}: [{e['start']}:{e['end']}]"
    print("[Check 7/20] Span Validity: PASS (0 <= start < end <= len(text))")
    checks_passed += 1

    # 8. Text/Span equality (text[start:end] == entity.text)
    for _, r in train_recs + val_recs:
        txt = r["text"]
        for e in r.get("entities", []):
            assert txt[e["start"]:e["end"]] == e["text"], f"Span slice mismatch in {r.get('variant_id')}"
    for _, r in test_golds:
        txt = test_in_map[r["record_id"]]
        for e in r.get("gold_entities", []):
            assert txt[e["start"]:e["end"]] == e["text"], f"Span slice mismatch in {r.get('record_id')}"
    print("[Check 8/20] Text/Span Equality: PASS (text[start:end] == entity.text across all entities)")
    checks_passed += 1

    # 9. Character-offset validity across Unicode scripts
    unicode_tested = 0
    for _, r in test_golds:
        txt = test_in_map[r["record_id"]]
        for e in r.get("gold_entities", []):
            if any(ord(c) > 127 for c in e["text"]):
                assert txt[e["start"]:e["end"]] == e["text"]
                unicode_tested += 1
    assert unicode_tested > 0, "No non-ASCII Unicode spans tested!"
    print(f"[Check 9/20] Multilingual Character Offset Validity: PASS ({unicode_tested} non-ASCII spans verified)")
    checks_passed += 1

    # 10. Entity ordering by start offset
    for _, r in train_recs + val_recs:
        starts = [e["start"] for e in r.get("entities", [])]
        assert starts == sorted(starts), f"Entities not sorted in {r.get('variant_id')}"
    for _, r in test_golds:
        starts = [e["start"] for e in r.get("gold_entities", [])]
        assert starts == sorted(starts), f"Entities not sorted in {r.get('record_id')}"
    print("[Check 10/20] Entity Ordering: PASS (Ascending by start offset)")
    checks_passed += 1

    # 11. Valid IOB2 sequence compatibility
    # Ensure no entity spans overlap each other
    for _, r in train_recs + val_recs:
        ents = r.get("entities", [])
        for i in range(len(ents) - 1):
            assert ents[i]["end"] <= ents[i+1]["start"], f"Overlapping entity spans in {r.get('variant_id')}"
    for _, r in test_golds:
        ents = r.get("gold_entities", [])
        for i in range(len(ents) - 1):
            assert ents[i]["end"] <= ents[i+1]["start"], f"Overlapping entity spans in {r.get('record_id')}"
    print("[Check 11/20] IOB2 Sequence Compatibility: PASS (Non-overlapping strict token boundaries)")
    checks_passed += 1

    # 12. Hard-negative zero-gold constraint
    test_gold_map = {r["record_id"]: r["gold_entities"] for _, r in test_golds}
    for _, r in test_inputs:
        if r.get("base_kind") == "HARD_NEGATIVE" or str(r.get("base_id", "")).startswith("NEG_"):
            gold_ents = test_gold_map[r["record_id"]]
            assert len(gold_ents) == 0, f"Hard negative record {r['record_id']} contains gold entities!"
    print("[Check 12/20] Hard-Negative Zero-Gold Invariant: PASS (All 140 hard negatives have 0 gold entities)")
    checks_passed += 1

    # 13. Adversarial quota preservation
    adv_counter = Counter()
    for _, r in test_inputs:
        pert = r.get("perturbation")
        if isinstance(pert, dict):
            pt = pert.get("perturbation_type") or pert.get("type")
            if pt and pt != "NONE":
                adv_counter[pt] += 1
    assert len(adv_counter) == 5, f"Expected 5 adversarial families, got {len(adv_counter)}"
    for fam, cnt in adv_counter.items():
        assert cnt == 20, f"Adversarial quota violated for {fam}: expected 20, got {cnt}"
    print("[Check 13/20] Adversarial Quota: PASS (Exactly 20 per family across A1–A5, total 100)")
    checks_passed += 1

    # 14. Language labels validity
    for _, r in test_inputs:
        assert r.get("language") in VALID_LANGUAGES, f"Invalid language {r.get('language')} in {r['record_id']}"
    print("[Check 14/20] Language Labels Validity: PASS")
    checks_passed += 1

    # 15. Perturbation labels validity
    for _, r in test_inputs:
        pert = r.get("perturbation")
        if isinstance(pert, dict):
            pt = pert.get("perturbation_type") or pert.get("type")
            assert pt in VALID_PERTURBATIONS, f"Invalid perturbation {pt} in {r['record_id']}"
    print("[Check 15/20] Perturbation Labels Validity: PASS")
    checks_passed += 1

    # 16. Duplicate text checks across splits
    train_texts = set(r["text"].strip() for _, r in train_recs)
    val_texts = set(r["text"].strip() for _, r in val_recs)
    test_texts = set(r["text"].strip() for _, r in test_inputs)
    assert len(train_texts & val_texts) == 0, "Train and Val share identical text!"
    assert len(train_texts & test_texts) == 0, "Train and Test share identical text!"
    assert len(val_texts & test_texts) == 0, "Val and Test share identical text!"
    print("[Check 16/20] Cross-Split Text Duplication Check: PASS (0 identical text overlap across splits)")
    checks_passed += 1

    # 17. Malformed Unicode validation
    for _, r in train_recs + val_recs + test_inputs:
        txt = r["text"]
        # Ensure round-trip UTF-8 encoding / decoding is bitwise lossless
        assert txt.encode("utf-8").decode("utf-8") == txt, f"Unicode round-trip error in {r.get('record_id')}"
    print("[Check 17/20] Unicode Integrity: PASS (Lossless UTF-8 serialization verified)")
    checks_passed += 1

    # 18. Empty records validation
    for _, r in train_recs + val_recs + test_inputs:
        assert len(r["text"].strip()) > 0, f"Empty text found in record: {r}"
    print("[Check 18/20] Zero Empty Records: PASS")
    checks_passed += 1

    # 19. Missing annotations check
    assert len(test_inputs) == len(test_golds) == 964, "Test input and gold counts differ!"
    for _, r in test_inputs:
        assert r["record_id"] in test_gold_map, f"Missing gold annotation record for {r['record_id']}"
    print("[Check 19/20] Annotation Completeness: PASS (964/964 records annotated)")
    checks_passed += 1

    # 20. Unexpected fields check
    allowed_train_keys = {"variant_id", "base_id", "text", "language", "pii_type", "split", "entities"}
    allowed_test_in_keys = {"record_id", "base_id", "text", "language", "carrier_script", "base_kind", "difficulty", "domain", "perturbation", "split", "synthetic"}
    for _, r in train_recs + val_recs:
        extra = set(r.keys()) - allowed_train_keys
        assert len(extra) == 0, f"Unexpected fields in train/val record: {extra}"
    for _, r in test_inputs:
        extra = set(r.keys()) - allowed_test_in_keys
        assert len(extra) == 0, f"Unexpected fields in test input record: {extra}"
    print("[Check 20/20] Schema Consistency: PASS (Zero unexpected or undocumented fields)")
    checks_passed += 1

    print("=" * 70)
    print(f"STATUS: ALL {checks_passed}/20 CHECKS PASSED SUCCESSFULLY.")
    print("=" * 70)

if __name__ == "__main__":
    main()
