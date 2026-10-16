# Benchmark Dataset Specification & Schema Guide
**Document Identifier**: `DOCS-DATASET-V1.0`  
**Benchmark Version**: `0.18`  
**Status**: APPROVED  
**Date**: September 9, 2026  

---

## 1. Overview & Dataset Dimensions

The Indian PII Robustness Benchmark corpus comprises **964 evaluation records** containing **724 gold standard Indian PII entities**. The corpus is entirely synthetic, guaranteeing zero real-world privacy leakage while providing rigorous evaluation across 5 language regimes, 5 perturbation types, and dedicated hard-negative decoys.

```
Canonical Benchmark Corpus (964 records, 724 gold entities)
├── Base Clean Instances (200 records, 200 gold entities)
├── Language Realizations (400 records, 400 gold entities)
├── Adversarial Perturbations (314 records, 124 gold entities, 190 control records)
└── Hard-Negative Pure Decoys (50 records, 0 gold entities)
```

---

## 2. Canonical JSONL Record Schema

Each record in the dataset is represented as a single-line JSON object with the following fields:

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `variant_id` | `string` | Unique record identifier (e.g., `base_0042`, `lang_hi_deva_0120`, `adv_a1_0055`) |
| `base_id` | `string` | Identifier of the originating base instance template (e.g., `base_0042`) |
| `text` | `string` | Complete context text containing potential PII or decoy elements |
| `language` | `string` | Language/script category: `EN`, `HINGLISH`, `HI_DEVA_PII`, `HI_LATN_PII`, `MIXED` |
| `entities` | `list[dict]` | List of gold standard PII entity annotations |
| `perturbation_family` | `string` | Perturbation type: `none`, `a1_whitespace`, `a2_phonetic`, `a3_ocr`, `a4_script_mix`, `a5_delimiters` |
| `difficulty` | `string` | Stratified difficulty tier: `EASY`, `MEDIUM`, `HARD` |
| `is_hard_negative` | `bool` | `true` if record is a pure non-PII decoy instance; `false` otherwise |
| `decoy_class` | `string \| null` | Classification of decoy mechanism (e.g., `STRUCTURAL_NUMBER`, `TRACKING_CODE`) |

### Gold Entity Schema (`entities` array elements)
| Subfield | Type | Description |
| :--- | :--- | :--- |
| `type` | `string` | One of 9 supported PII categories |
| `start` | `int` | 0-indexed character offset (inclusive) in Python Unicode code-points |
| `end` | `int` | 0-indexed character offset (exclusive) in Python Unicode code-points |
| `value` | `string` | Exact slice of text: `text[start:end] == value` |

---

## 3. Supported PII Categories ($\mathcal{T}$)

1. **`NAME`**: Common Indian personal names (first name, middle name, surname) across diverse regional naming conventions.
2. **`PHONE`**: Indian 10-digit mobile numbers, landlines, and international prefixes (`+91`, `0`).
3. **`EMAIL`**: Standard personal and professional email addresses with synthetic fictitious domains.
4. **`AADHAAR`**: 12-digit Indian unique identity numbers (formatted with or without spaces/hyphens).
5. **`PAN`**: Permanent Account Number (10-character alphanumeric: 5 uppercase letters, 4 digits, 1 uppercase letter).
6. **`PASSPORT`**: Indian passport numbers (1 uppercase letter followed by 7 digits).
7. **`VOTER_ID`**: Election Photo Identity Card (EPIC) numbers (3 uppercase letter state/district prefix followed by 7 digits).
8. **`DRIVING_LICENSE`**: Indian driving license numbers with two-letter state prefix.
9. **`UPI_ID`**: Unified Payments Interface virtual payment addresses (e.g., `name@bank`, `handle@okhdfcbank`).

---

## 4. Concrete Synthetic Record Examples

> [!NOTE]
> All examples presented below are 100% synthetic fictitious test strings. No actual personal data is depicted.

### Example 1: Standard Base Clean Instance (English)
```json
{
  "variant_id": "base_0012",
  "base_id": "base_0012",
  "text": "Please transfer the monthly maintenance to rahul.sharma@okaxis immediately.",
  "language": "EN",
  "perturbation_family": "none",
  "difficulty": "EASY",
  "is_hard_negative": false,
  "entities": [
    {
      "type": "UPI_ID",
      "start": 43,
      "end": 64,
      "value": "rahul.sharma@okaxis"
    }
  ]
}
```

### Example 2: Language Realization (Hindi Devanagari)
```json
{
  "variant_id": "lang_hi_deva_0045",
  "base_id": "base_0045",
  "text": "कृपया अपने आधार कार्ड संख्या 5482 1204 9831 को बैंक खाते से लिंक करें।",
  "language": "HI_DEVA_PII",
  "perturbation_family": "none",
  "difficulty": "MEDIUM",
  "is_hard_negative": false,
  "entities": [
    {
      "type": "AADHAAR",
      "start": 29,
      "end": 43,
      "value": "5482 1204 9831"
    }
  ]
}
```

### Example 3: Adversarial Perturbation Instance (A1 Whitespace Insertion)
```json
{
  "variant_id": "adv_a1_0088",
  "base_id": "base_0088",
  "text": "Customer pan details submitted: A B C P D 1 2 3 4 E for verification.",
  "language": "EN",
  "perturbation_family": "a1_whitespace",
  "difficulty": "HARD",
  "is_hard_negative": false,
  "entities": [
    {
      "type": "PAN",
      "start": 32,
      "end": 51,
      "value": "A B C P D 1 2 3 4 E"
    }
  ]
}
```

### Example 4: Pure Hard-Negative Decoy Instance
```json
{
  "variant_id": "hn_decoy_0023",
  "base_id": "hn_base_0023",
  "text": "Consignment tracking reference code is 9812 3412 8901 for shipment updates.",
  "language": "EN",
  "perturbation_family": "none",
  "difficulty": "MEDIUM",
  "is_hard_negative": true,
  "decoy_class": "STRUCTURAL_NUMBER",
  "entities": []
}
```

---

## 5. Train / Validation / Test Disjointness & Leakage Controls

- **Complete Independence**: The 200 base instances used to construct the canonical 964 test benchmark records are strictly disjoint from the 200 base instances used in the adaptation training corpus (`data/adaptation/train_instances.jsonl`).
- **Audit Certification (SV-01)**: An exhaustive 1-to-1 string matching, n-gram overlap, and template hash audit verified that there is **0.0% instance leakage** between adaptation and benchmark sets.
- **Privacy Guarantees**: Conforms with the Indian Digital Personal Data Protection (DPDP) Act 2023.
