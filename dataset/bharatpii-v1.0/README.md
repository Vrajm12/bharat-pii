# BharatPII Benchmark Dataset (v1.0.0)

**The Official Multilingual Indian PII Robustness Benchmark**

[![Dataset Version](https://img.shields.io/badge/dataset-v1.0.0-blue.svg)](dataset_metadata.json)
[![License](https://img.shields.io/badge/license-CC--BY--4.0-green.svg)](LICENSE)
[![Benchmark Version](https://img.shields.io/badge/benchmark-v0.18-orange.svg)](DATASET_CARD.md)

---

## Overview

**BharatPII** is a standardized, multilingual evaluation benchmark designed to measure the precision, recall, boundary localization accuracy, and adversarial robustness of Personally Identifiable Information (PII) extraction systems in Indian digital contexts.

### Key Highlights:
- **Canonical Test Benchmark**: 964 evaluation records featuring **724 gold standard PII entities** across **8 Indian PII categories**.
- **Linguistic Diversity**: Covers 5 language/script regimes including standard Indian English, Romanized Hindi, Hindi-English code-mixing (Hinglish), and native Devanagari Hindi.
- **Stress-Testing**: Features **140 hard-negative distractor records** and **100 adversarial stress-test variants** across 5 perturbation families (A1–A5).
- **Disjoint Adaptation Split**: Includes **1,000 adaptation training records** and **200 validation records** derived from completely disjoint base instances (0 base ID, 0 record ID, and 0 text overlap with test).
- **Privacy Guaranteed**: **100% synthetic data**. Contains zero real personal data, credentials, or private identifiers.

> [!IMPORTANT]
> **Synthetic Data Notice**:
> The benchmark contains synthetic PII and is not intended to represent real individuals or real credentials.

---

## Directory Structure

```
bharatpii-v1.0/
├── data/
│   ├── train/
│   │   └── train.jsonl               # 1,000 adaptation records (Public)
│   ├── validation/
│   │   └── val.jsonl                 # 200 validation records (Public)
│   └── test/
│       └── test_inputs.jsonl         # 964 evaluation inputs without gold spans (Public)
├── annotations/
│   ├── test_gold_annotations.jsonl   # 724 canonical gold spans for test records (Controlled)
│   └── review_template.csv           # Canonical 964-record human review sheet (Controlled)
├── examples/
│   └── synthetic_examples.jsonl      # Demonstration examples across 8 PII categories
├── docs/
│   └── annotation_guidelines.md      # Detailed annotation guidelines and definitions
├── label_schema.json                 # PII taxonomy, character offsets, IOB2 definitions
├── dataset_metadata.json             # Machine-readable dataset metadata
├── DATASET_CARD.md                   # Full 22-section dataset card
├── DATA_RELEASE_POLICY.md            # Public vs Controlled data governance policy
├── REPRODUCIBILITY.md                # Verification, loading, and evaluation guide
├── LICENSE                           # License terms (Recommended CC BY 4.0)
├── LICENSE_AUDIT.md                  # Comprehensive IP and license audit
└── CITATION.cff                      # Citation format (approved authors only)
```

---

## Quickstart: Loading the Data

```python
import json
from pathlib import Path

# 1. Load training records
train_path = Path("data/train/train.jsonl")
train_records = []
with train_path.open(encoding="utf-8") as f:
    for line in f:
        train_records.append(json.loads(line))

print(f"Loaded {len(train_records)} training records")
sample = train_records[0]
print("Text:", sample["text"])
print("Entities:", sample["entities"])

# 2. Verify character offset slicing contract
for e in sample["entities"]:
    assert sample["text"][e["start"]:e["end"]] == e["text"], "Offset mismatch!"
print("Character slice contract verified: text[start:end] == entity.text")
```

---

## PII Entity Categories

| Category | Description | Canonical Syntax / Examples |
|:---|:---|:---|
| **`PERSON`** | Individual names across regional conventions | `Sneha Sharma`, `विक्रम राव`, `Rahul Patel` |
| **`PAN`** | Permanent Account Number | 10-char alphanumeric (`BDTNL5698D`) |
| **`AADHAAR`** | Unique Identification Number | 12-digit numeric, Verhoeff checksum (`548923019842`) |
| **`PHONE`** | Mobile / telephone numbers | 10 digits, optional country code (`+91 9876543210`) |
| **`EMAIL`** | Electronic mail address | RFC 5322 syntax (`sneha.nair@example.test`) |
| **`UPI_ID`** | Virtual Payment Address | `handle@psp` (`9498941343@mail.test`, `ananya@okhdfcbank`) |
| **`BANK_ACCOUNT`** | Commercial bank account | 9 to 18 digits (`324210249947`) |
| **`ADDRESS`** | Physical delivery address | Multi-component address (`Flat 230, Silver Oak Heights...`) |

---

## Character Offset Convention
All entity boundaries use **0-indexed character offsets** into the raw UTF-8 string:
$$\text{text}[\text{start}:\text{end}] == \text{entity.text}$$
- `start`: 0-based character index of the first character.
- `end`: 0-based character index immediately following the last character (exclusive).
- Compatible with native Python string slicing across Unicode scripts.

---

## Baseline Reference Models
The reference model for this benchmark is **BharatPII-CRF v1.0**, installable via the official Python package:
```bash
pip install bharatpii
```
See [`DATASET_CARD.md`](DATASET_CARD.md) and [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) for full benchmark evaluation protocols.
