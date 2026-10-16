# BharatPII: Multilingual Indian Personally Identifiable Information (PII) Detection

[![Package Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](pyproject.toml)
[![Model Compatibility](https://img.shields.io/badge/model-bharatpii--crf--v1.0-brightgreen.svg)](models/bharatpii-crf-v1.0/MODEL_CARD.md)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-informational.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

`bharatpii` is the official Python library for extracting sensitive Personally Identifiable Information (PII) from Indian multilingual, code-mixed (Hinglish), and transliterated texts using the scientifically verified **BharatPII-CRF** sequence-constrained architecture.

---

## 1. What BharatPII Is
`bharatpii` provides an offline, local inference engine designed specifically for the Indian linguistic and administrative landscape. It addresses the systemic failure modes of Western PII de-identification tools on Indian identifier syntaxes, phonetic variations, and mixed-script orthography by combining a multilingual transformer encoder with exact linear-chain Conditional Random Field (CRF) sequence decoding.

---

## 2. Supported PII Categories
The library identifies 8 distinct Indian PII entity categories in IOB2 tagging format:

| Entity Type | Description | Example Pattern / Realization |
|:---|:---|:---|
| **`PERSON`** | Indian personal names across regional demographics | `Rahul Sharma`, `Priya Iyer`, `अमित वर्मा` |
| **`PAN`** | Permanent Account Number (10 alphanumeric) | `ABCDE1234F`, `BKRPK8921L` |
| **`AADHAAR`** | 12-digit Indian national identity number | `1234 5678 9012`, `987654321098` |
| **`PHONE`** | 10-digit mobile, landline, and STD numbers | `9876543210`, `+91 98765 43210` |
| **`EMAIL`** | Personal, institutional, and business email | `rahul.sharma@example.com` |
| **`UPI_ID`** | Virtual Payment Addresses (VPAs) | `rahul@oksbi`, `priya@upi` |
| **`BANK_ACCOUNT`** | Indian commercial bank account numbers (9–18 digits) | `12345678901234` |
| **`ADDRESS`** | Street, locality, apartment, city, state, PIN code | `Flat 402, Lake View Road, Kolkata 700029` |

---

## 3. Supported Linguistic & Script Coverage
The model is calibrated across 7 linguistic and script variants:
1. **`EN`**: Indian English formal syntax.
2. **`IN_EN`**: Indian English bureaucratic and regional administrative phrasing.
3. **`HI_LATIN_PII`**: Hindi in Latin script with transliterated PII.
4. **`HI_DEVA_PII`**: Hindi in Devanagari script with Devanagari-script PII.
5. **`ROM_HI`**: Romanized colloquial Hindi.
6. **`HINGLISH`**: Code-switched Hindi-English.
7. **`INFORMAL_HINGLISH`**: Conversational SMS-style Hinglish with orthographic variations.

---

## 4. Installation

### From Source or Local Wheel
```bash
# Clone the repository
git clone https://github.com/Vrajm12/bharat-pii.git
cd bharat-pii

# Install package
pip install .
```

### Development Installation
```bash
pip install -e .
```

---

## 5. Model Acquisition & Loading
`bharatpii` separates code distribution from model distribution. The model weights are not bundled inside the Python wheel to keep package installation lightweight.

Download or locate the official release directory (`models/bharatpii-crf-v1.0/`):

```python
from bharatpii import BharatPII

# Load the local model artifact
model = BharatPII.from_pretrained("models/bharatpii-crf-v1.0")
```

To enable cryptographic validation of all release files on startup:
```python
model = BharatPII.from_pretrained("models/bharatpii-crf-v1.0", verify_checksums=True)
```

---

## 6. Python Usage Examples

### Single Text Inference
```python
from bharatpii import BharatPII

model = BharatPII.from_pretrained("models/bharatpii-crf-v1.0")

text = "मेरा नाम Rahul Sharma है और मेरा PAN ABCDE1234F है। Call 9876543210."
result = model.predict(text)

# Access entities
for entity in result:
    print(f"[{entity.label}] '{entity.text}' (offset {entity.start}:{entity.end}, score: {entity.score})")

# Export as JSON-serializable dictionary
print(result.to_dict())
```

### Batch Inference
```python
texts = [
    "Contact Priya at priya@example.com regarding order 502.",
    "Aadhaar 1234 5678 9012 linked to bank account 987654321012.",
]

results = model.predict_batch(texts)
for res in results:
    print(res.text, "->", len(res.entities), "entities")
```

---

## 7. Command-Line Interface (CLI)

```bash
# Inspect model metadata and parameter accounting
bharatpii --model models/bharatpii-crf-v1.0 --info

# Predict on raw text argument
bharatpii --model models/bharatpii-crf-v1.0 --text "Contact Rahul at 9876543210"

# Process input file and write structured JSON output
bharatpii --model models/bharatpii-crf-v1.0 --input input.txt --output output.json
```

---

## 8. Output Format & Span Offsets
Inference produces structured `PredictionResult` objects containing `Entity` records.

### Offsets Contract:
- `start`: 0-indexed character offset in raw Unicode text.
- `end`: 0-indexed exclusive end character offset.
- **Invariant**: `text[start:end] == entity.text` holds for every detected entity.
- Character offsets correspond strictly to native Python string indices (code points), not byte offsets.

### Score Semantics:
- `score` represents the average token emission softmax probability across the tokens comprising the span.
- **Note**: This is an emission confidence indicator, **not** a calibrated sequence posterior probability.

---

## 9. Model Architecture & Parameter Accounting

BharatPII-CRF consists of:
- **Base Encoder**: XLM-RoBERTa-base (`xlm-roberta-base`), 12 Transformer layers, 768 hidden dimension, 12 attention heads.
- **Emission Layer**: Linear projection ($768 \to 17$).
- **Sequence Decoder**: Linear-chain Conditional Random Field (`LinearChainCRF`) with exact Viterbi decoding.

### Parameter Accounting
| Component | Tensors | Parameter Count | Trainable in BharatPII Adaptation |
|:---|:---:|:---:|:---:|
| **XLM-R Encoder** | 199 | 278,043,648 | No (Frozen base weights) |
| **Linear Emission Layer** | 2 | 13,073 | Yes |
| **CRF Transitions** | 3 | 323 | Yes |
| **Task-Specific Head Subtotal** | **5** | **13,396** | **Yes** |
| **Total Model Parameters** | **204** | **278,057,044** | **13,396** |

> **Accurate Parameter Statement**:
> "BharatPII-CRF is built on a 278.06M-parameter XLM-R base encoder with a 13,396-parameter task-specific classifier/CRF head used for the BharatPII adaptation."

---

## 10. Canonical Benchmark Performance
Evaluated on the frozen 964-record canonical benchmark corpus (724 gold entities, 140 non-PII hard-negative decoys):
- **Exact Precision ($M_1$)**: 63.09%
- **Exact Recall ($M_2$)**: 93.51%
- **Type-Strict $F_1$ ($M_3$)**: 75.35%
- **Exact-Span $F_1$ ($M_4$)**: 66.89%
- **Instance Accuracy ($M_5$)**: 94.42%
- **False Positive Rate ($M_6$)**: 33.18%
- **Error Partition**: $TP_{\text{exact}} = 601$, $F_1 = 7$, $F_2 = 76$, $F_3 = 40$, $F_4 = 356$ (Partition sum: $601 + 7 + 76 + 40 = 724$).

---

## 11. Known Limitations & Failure Modes
1. **Alphanumeric Decoy Over-Triggering ($F_4 = 356$)**: Due to its high-recall objective (93.51%), the model may flag non-PII order codes, invoice numbers, or tracking identifiers that mimic PAN or account number structures.
2. **Boundary Truncations on Long Spans ($F_2 = 76$)**: While CRF decoding reduces span fragmentation by $68.7\%$ compared to unconstrained softmax, complex multi-token addresses and honorific-prefixed names may experience boundary offsets.
3. **Synthetic Training Distribution**: The model was adapted on rule-synthesized Indic contexts. OCR noise, missing characters, or unpunctuated colloquial vernacular may degrade performance.

---

## 12. Security, Privacy & Non-Claims
- **Local/Offline Inference**: Inference runs 100% locally when a local model directory is provided. No telemetry, no remote network calls, no unredacted PII logging.
- **Non-Claims**:
  - This is an academic research library; it is **not** certified as "production ready" without human-in-the-loop validation.
  - Not government-certified or formally certified under the Digital Personal Data Protection Act (DPDPA 2023).
  - Does not guarantee 100% detection accuracy or zero false positives.
  - Does not cover all 22 scheduled Indian languages.

---

## 13. Citation
```bibtex
@article{bharatpii2026,
  title={BharatPII: Sequence-Constrained Multilingual PII Extraction for Indian Linguistic Environments},
  author={Murthy, et al.},
  journal={Empirical NLP & Privacy},
  year={2026}
}
```

---

## 14. License
`bharatpii` is licensed under the [MIT License](LICENSE). Third-party weights (`xlm-roberta-base`) are governed by Meta AI's MIT License.
