# BharatPII Reproducibility & Evaluation Guide

**Release**: `bharatpii-dataset-v1.0`  
**Date**: September 12, 2026  

---

## 1. Obtaining the Dataset
The dataset can be obtained from the official repository release directory:
```
dataset/bharatpii-v1.0/
```
or via the public archive:
```
dataset/bharatpii-dataset-v1.0.tar.gz
```

---

## 2. Verifying Cryptographic Hashes
Verify the integrity of all dataset release files using SHA-256:
```bash
# On Linux/macOS:
sha256sum -c SHA256SUMS.txt

# On Windows PowerShell:
Get-FileHash -Algorithm SHA256 data/train/train.jsonl
```
Compare the output against the authoritative hashes recorded in [`SHA256SUMS.txt`](SHA256SUMS.txt).

---

## 3. Dataset Schema & Loading
Each record is serialized as a single JSON object per line (JSONL).

### Training / Validation Schema (`data/train/train.jsonl`, `data/validation/val.jsonl`):
```json
{
  "variant_id": "TRAIN_0001",
  "base_id": "TRAIN_BASE_001",
  "text": "My name is Sneha Nair.",
  "language": "EN",
  "pii_type": "PERSON",
  "split": "train",
  "entities": [
    {
      "type": "PERSON",
      "text": "Sneha Nair",
      "start": 11,
      "end": 21
    }
  ]
}
```

### Evaluation Inputs Schema (`data/test/test_inputs.jsonl`):
```json
{
  "record_id": "PERSON_001",
  "base_id": "PERSON_001",
  "text": "My name is Sneha Sharma.",
  "language": "EN",
  "carrier_script": "LATIN",
  "base_kind": "POSITIVE",
  "difficulty": "EASY",
  "split": "test",
  "synthetic": true
}
```

---

## 4. Running Validation
To validate dataset syntax, character offset integrity, and split disjointness:
```bash
python scripts/validate_bharatpii_dataset_release.py
```
Expected output:
```
All 20/20 dataset release validation checks PASSED.
```

---

## 5. Computing Release Statistics
To reproduce the official dataset statistics table directly from the release files:
```bash
python scripts/compute_dataset_release_statistics.py
```

---

## 6. Evaluating a Model
1. Ingest `data/test/test_inputs.jsonl`.
2. Produce predictions formatted as JSONL records:
```json
{
  "record_id": "PERSON_001",
  "type": "PERSON",
  "start": 11,
  "end": 23,
  "text": "Sneha Sharma",
  "confidence": 0.96
}
```
3. Evaluate against ground truth using exact match ($TP_{\text{exact}}$) and type match ($TP_{\text{type}}$) criteria as specified in [`DATASET_CARD.md`](DATASET_CARD.md).
