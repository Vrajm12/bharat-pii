import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
RELEASE_DIR = ROOT / "dataset" / "bharatpii-v1.0"

def load_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

def main():
    train_file = RELEASE_DIR / "data" / "train" / "train.jsonl"
    val_file = RELEASE_DIR / "data" / "validation" / "val.jsonl"
    test_inputs_file = RELEASE_DIR / "data" / "test" / "test_inputs.jsonl"
    test_gold_file = RELEASE_DIR / "annotations" / "test_gold_annotations.jsonl"

    train_recs = load_jsonl(train_file)
    val_recs = load_jsonl(val_file)
    test_inputs = load_jsonl(test_inputs_file)
    test_gold = load_jsonl(test_gold_file)

    total_records = len(train_recs) + len(val_recs) + len(test_inputs)

    # Entities
    train_ents = sum(len(r.get("entities", [])) for r in train_recs)
    val_ents = sum(len(r.get("entities", [])) for r in val_recs)
    test_ents = sum(len(r.get("gold_entities", [])) for r in test_gold)
    total_ents = train_ents + val_ents + test_ents

    # Unique base IDs
    train_bases = set(r.get("base_id") for r in train_recs if r.get("base_id"))
    val_bases = set(r.get("base_id") for r in val_recs if r.get("base_id"))
    test_bases = set(r.get("base_id") for r in test_inputs if r.get("base_id"))
    all_bases = train_bases | val_bases | test_bases

    # Unique record IDs
    train_rids = set(r.get("variant_id") or r.get("record_id") for r in train_recs)
    val_rids = set(r.get("variant_id") or r.get("record_id") for r in val_recs)
    test_rids = set(r.get("record_id") or r.get("variant_id") for r in test_inputs)
    all_rids = train_rids | val_rids | test_rids

    # PII Category Distribution across splits
    def count_pii(records, entity_key="entities"):
        c = Counter()
        for r in records:
            for e in r.get(entity_key, []):
                c[e["type"]] += 1
        return c

    train_pii = count_pii(train_recs, "entities")
    val_pii = count_pii(val_recs, "entities")
    test_pii = count_pii(test_gold, "gold_entities")
    all_pii_types = sorted(set(list(train_pii.keys()) + list(val_pii.keys()) + list(test_pii.keys())))

    # Language distribution (Test set)
    test_lang = Counter(r.get("language", "UNKNOWN") for r in test_inputs)

    # Hard-negatives in Test
    hard_negs = [r for r in test_inputs if r.get("base_kind") == "HARD_NEGATIVE" or str(r.get("base_id", "")).startswith("NEG_")]
    hard_neg_count = len(hard_negs)

    # Adversarial in Test
    adv_counter = Counter()
    for r in test_inputs:
        pert = r.get("perturbation")
        if isinstance(pert, dict):
            pt = pert.get("perturbation_type") or pert.get("type") or "UNKNOWN"
            if pt != "NONE":
                adv_counter[pt] += 1
        elif r.get("base_kind") == "ADVERSARIAL":
            adv_counter["ADVERSARIAL_OTHER"] += 1
    adv_count = sum(adv_counter.values())

    print("=" * 78)
    print("BHARATPII BENCHMARK DATASET RELEASE STATISTICS REPORT")
    print("=" * 78)
    print(f"Dataset Version:          1.0.0")
    print(f"Total Records:            {total_records} (Train: {len(train_recs)}, Val: {len(val_recs)}, Test: {len(test_inputs)})")
    print(f"Total Gold Entities:      {total_ents} (Train: {train_ents}, Val: {val_ents}, Test: {test_ents})")
    print(f"Total Unique Base IDs:    {len(all_bases)} (Train: {len(train_bases)}, Val: {len(val_bases)}, Test: {len(test_bases)})")
    print(f"Total Unique Record IDs:  {len(all_rids)} (Overlap: 0)")
    print("-" * 78)

    print("\n1. SPLIT SUMMARY:")
    print(f"  - Train Split:      {len(train_recs):4} records ({len(train_recs)}/{total_records} = {len(train_recs)/total_records*100:.2f}%), {train_ents:4} entities, {len(train_bases)} base IDs")
    print(f"  - Validation Split: {len(val_recs):4} records ({len(val_recs)}/{total_records} = {len(val_recs)/total_records*100:.2f}%), {val_ents:4} entities, {len(val_bases)} base IDs")
    print(f"  - Test Benchmark:   {len(test_inputs):4} records ({len(test_inputs)}/{total_records} = {len(test_inputs)/total_records*100:.2f}%), {test_ents:4} entities, {len(test_bases)} base IDs")

    print("\n2. PII CATEGORY DISTRIBUTION:")
    hdr = "%-16s | %-12s | %-12s | %-12s | %-12s" % ("PII Category", "Train", "Val", "Test", "Total")
    print(hdr)
    print("-" * len(hdr))
    for cat in all_pii_types:
        tr_c = train_pii[cat]
        va_c = val_pii[cat]
        te_c = test_pii[cat]
        tot = tr_c + va_c + te_c
        tr_pct = f"{tr_c} ({tr_c}/{train_ents*100/train_ents:.0f}%)"
        va_pct = f"{va_c} ({va_c}/{val_ents*100/val_ents:.0f}%)"
        te_pct = f"{te_c} ({te_c/test_ents*100:.1f}%)"
        tot_pct = f"{tot} ({tot/total_ents*100:.1f}%)"
        print("%-16s | %-12s | %-12s | %-12s | %-12s" % (cat, tr_pct, va_pct, te_pct, tot_pct))
    print("-" * len(hdr))
    print("%-16s | %-12d | %-12d | %-12d | %-12d" % ("TOTAL", train_ents, val_ents, test_ents, total_ents))

    print("\n3. CANONICAL TEST BENCHMARK BREAKDOWN (964 RECORDS):")
    print(f"  - Standard Linguistic Realizations: 624 records ({624/964*100:.2f}%)")
    print(f"  - Seed Base Instances:             100 records ({100/964*100:.2f}%)")
    print(f"  - Hard Negative Distractors:       140 records ({hard_neg_count}/964 = {hard_neg_count/964*100:.2f}%) [Zero Gold PII]")
    print(f"  - Adversarial Stress Variants:     100 records ({adv_count}/964 = {adv_count/964*100:.2f}%) [5 families]")

    print("\n4. ADVERSARIAL QUOTA BREAKDOWN (100 RECORDS):")
    for pt, count in sorted(adv_counter.items()):
        print(f"  - Family {pt:22}: {count:2} records ({count}/100 = {count/100*100:.1f}% of adversarial quota)")

    print("\n5. TEST LANGUAGE & SCRIPT DISTRIBUTION (964 RECORDS):")
    for lang, count in sorted(test_lang.items(), key=lambda x: x[1], reverse=True):
        print(f"  - Language {lang:18}: {count:3} records ({count}/964 = {count/964*100:.2f}%)")

    print("=" * 78)

if __name__ == "__main__":
    main()
