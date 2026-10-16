# BharatPII Inference & Redaction Demo

This directory contains a minimal, self-contained local inference and redaction demonstration using the official `bharatpii` Python library and the pre-packaged `models/bharatpii-crf-v1.0/` model artifact.

---

## 1. Overview

`bharatpii_demo.py` provides an offline, local demonstration for detecting and redacting sensitive Personally Identifiable Information (PII) from Indian English, Hindi (Devanagari), Hinglish, and transliterated Indic texts.

### Key Capabilities
- **Official Public API**: Integrates exclusively via supported `bharatpii.BharatPII` interfaces (`from_pretrained`, `predict`, `predict_batch`, `info`).
- **Exact Character Offsets**: Guaranteed slice invariant `text[start:end] == entity.text` for all detected spans.
- **Span-Preserving Redaction**: Replaces detected PII spans with category labels (e.g. `[PERSON]`, `[PAN]`, `[PHONE]`), preserving all punctuation, whitespace, and non-PII characters.
- **Multilingual Support**: Supports formal English (`EN`), regional administrative English (`IN_EN`), Hindi in Devanagari script (`HI_DEVA_PII`), code-mixed Hinglish (`HINGLISH`), Romanized Hindi (`ROM_HI`), and informal conversational styles.
- **Canonical Smoke Tests**: Built-in test runner validating character offsets, label classifications, and redaction outputs.
- **100% Local & Offline**: Zero network telemetry, zero external API calls, and zero logging of sensitive texts.

---

## 2. Supported Indian PII Categories

The demo recognizes all 8 canonical Indian PII categories in the BharatPII taxonomy:

| Category | Description | Example Target |
|:---|:---|:---|
| `PERSON` | Indian personal names across naming conventions | `Sneha Sharma`, `अमित वर्मा`, `Divya Rao` |
| `PAN` | 10-character Permanent Account Number | `ABCDE1234F`, `FZZFN0256Z` |
| `AADHAAR` | 12-digit Indian national identity number | `670656272980`, `083172788957` |
| `PHONE` | 10-digit mobile and telephone numbers | `9876543210`, `9247317810` |
| `EMAIL` | Personal, corporate, and institutional email | `sneha8298@webmail.test` |
| `UPI_ID` | Virtual Payment Addresses (VPAs) | `9837770143@mail.test`, `priya@upi` |
| `BANK_ACCOUNT`| Indian commercial bank account numbers (9–18 digits) | `324210249947`, `013990490278` |
| `ADDRESS` | Street, locality, apartment, city, state, PIN code | `Flat 230, Silver Oak Heights, Baner Road, Bengaluru 754235` |

---

## 3. Directory Structure

```
examples/
├── bharatpii_demo.py       # Main CLI demo (interactive, single-text, batch, smoke-tests)
├── web_demo.py             # Lightweight local web interface (HTML5, span highlight, copy)
├── synthetic_examples.py   # Catalog of synthetic test cases across 8 types & 7 languages
├── synthetic_examples.json # JSON-serialized export of synthetic test cases
├── test_demo.py            # Standalone test runner for pytest or direct Python execution
└── README.md               # This setup and usage guide
```

---

## 4. Setup & Installation

### Prerequisites
- Python 3.10+
- PyTorch `>=2.0.0`
- Transformers `>=4.40.0`
- Safetensors `>=0.4.0`
- SentencePiece `>=0.1.99`

### Step 1: Install `bharatpii`
Run editable or standard installation from the repository root:
```bash
pip install -e .
```

### Step 2: Verify Model Artifact
Ensure the model directory `models/bharatpii-crf-v1.0/` is present with required weights and configuration:
- `model.safetensors` (Full model weights)
- `config.json`
- `label_map.json`
- `tokenizer.json` & `tokenizer_config.json`
- `SHA256SUMS.txt`

---

## 5. Exact Run Commands

### 5.1 Run the Full Synthetic Examples Demo
Executes all 23 synthetic examples covering all 8 PII categories in English, Hindi, and Hinglish:
```bash
python examples/bharatpii_demo.py
```

### 5.2 Analyze a Single English Text
```bash
python examples/bharatpii_demo.py --text "Contact Rahul Sharma at 9876543210 regarding PAN ABCDE1234F."
```
**Output:**
```
Input:    Contact Rahul Sharma at 9876543210 regarding PAN ABCDE1234F.
  Detected 3 entity/entities:
  1. [PERSON] 'Rahul Sharma'
     Offsets: [8:20] | Length: 12 chars
     Confidence: 0.8845 | Invariant Check: OK (exact slice)
  2. [PHONE] '9876543210'
     Offsets: [24:34] | Length: 10 chars
     Confidence: 0.8120 | Invariant Check: OK (exact slice)
  3. [PAN] 'ABCDE1234F'
     Offsets: [49:59] | Length: 10 chars
     Confidence: 0.8904 | Invariant Check: OK (exact slice)
Redacted: Contact [PERSON] at [PHONE] regarding PAN [PAN].
```

### 5.3 Analyze Hindi (Devanagari Script)
```bash
python examples/bharatpii_demo.py --text "मेरा नाम राहुल शर्मा है और मेरा ईमेल sneha8298@webmail.test है।"
```
**Output:**
```
Input:    मेरा नाम राहुल शर्मा है और मेरा ईमेल sneha8298@webmail.test है।
  Detected 2 entity/entities:
  1. [PERSON] 'राहुल शर्मा'
     Offsets: [9:20] | Length: 11 chars
     Confidence: 0.8712 | Invariant Check: OK (exact slice)
  2. [EMAIL] 'sneha8298@webmail.test'
     Offsets: [37:59] | Length: 22 chars
     Confidence: 0.8450 | Invariant Check: OK (exact slice)
Redacted: मेरा नाम [PERSON] है और मेरा ईमेल [EMAIL] है।
```

### 5.4 Analyze Code-Mixed Hinglish
```bash
python examples/bharatpii_demo.py --text "Mera phone 9876543210 hai aur UPI ID 9498941343@mail.test hai."
```
**Output:**
```
Input:    Mera phone 9876543210 hai aur UPI ID 9498941343@mail.test hai.
  Detected 2 entity/entities:
  1. [PHONE] '9876543210'
     Offsets: [11:21] | Length: 10 chars
     Confidence: 0.7932 | Invariant Check: OK (exact slice)
  2. [UPI_ID] '9498941343@mail.test'
     Offsets: [37:57] | Length: 20 chars
     Confidence: 0.7610 | Invariant Check: OK (exact slice)
Redacted: Mera phone [PHONE] hai aur UPI ID [UPI_ID] hai.
```

### 5.5 Interactive REPL Mode
Type or paste any text dynamically and view real-time span detection and redaction:
```bash
python examples/bharatpii_demo.py --interactive
```

### 5.6 File Processing (Input, Redacted Output & JSON Export)
Process an input text file and save the redacted text alongside structured JSON prediction metadata:
```bash
python examples/bharatpii_demo.py --input sample.txt --output redacted.txt --json-output output.json
```

### 5.7 Filter Synthetic Examples by PII Category
Inspect model performance on a specific category:
```bash
# Filter by PAN:
python examples/bharatpii_demo.py --category PAN

# Filter by ADDRESS:
python examples/bharatpii_demo.py --category ADDRESS

# Filter by AADHAAR:
python examples/bharatpii_demo.py --category AADHAAR
```

### 5.8 Custom Redaction Mask Patterns
Customize the redaction placeholder using `--mask-pattern`:
```bash
# Using angle brackets:
python examples/bharatpii_demo.py --text "My phone is 9876543210" --mask-pattern "<{label}>"
# Output: My phone is <PHONE>

# Using stars:
python examples/bharatpii_demo.py --text "My phone is 9876543210" --mask-pattern "***{label}***"
# Output: My phone is ***PHONE***
```

### 5.9 Cryptographic Release Validation
Verify all release files against `SHA256SUMS.txt` during loading:
```bash
python examples/bharatpii_demo.py --verify-checksums
```

### 5.10 Launch Local Web Interface
Start the lightweight, dependency-free interactive web application:
```bash
python examples/web_demo.py --port 8080
```
Open [http://127.0.0.1:8080](http://127.0.0.1:8080) in any modern browser to access:
- Multilingual text input and synthetic example selector
- Visual color-coded entity span highlighting
- Detailed entity table with native character offsets and slice invariant validation
- Span-preserving redaction with one-click clipboard copy
- Verified 100% offline local privacy indicator

---

## 6. Running Smoke Tests & Verification

### Option A: Demo Built-in Smoke Tests
Runs all canonical assertions and prints a detailed test status report:
```bash
python examples/bharatpii_demo.py --smoke-test
```
Exits with code `0` on complete pass.

### Option B: Pytest Test Suite
Runs the comprehensive automated test suite (18 unit, integration, and CLI tests):
```bash
python -m pytest tests/test_demo_redaction.py -v
```
Or via the standalone runner in `examples/`:
```bash
python examples/test_demo.py
```

---

## 7. Python API Integration Example

To integrate BharatPII and redaction directly inside Python applications:

```python
from pathlib import Path
from bharatpii import BharatPII
from examples.bharatpii_demo import redact_text

# 1. Load model artifact
model = BharatPII.from_pretrained("models/bharatpii-crf-v1.0")

# 2. Extract entities
text = "Contact Amit Verma at 9876543210 or email amit@corp.in."
result = model.predict(text)

# 3. Inspect detected entities and verify offsets
for ent in result.entities:
    print(f"[{ent.label}] {ent.text} (slice {ent.start}:{ent.end})")
    assert text[ent.start:ent.end] == ent.text

# 4. Redact sensitive spans
redacted = redact_text(text, result.entities, mask_pattern="[{label}]")
print("Redacted text:", redacted)
# Output: "Contact [PERSON] at [PHONE] or email [EMAIL]."
```

---

## 8. Research Prototype Notice & Limitations

> [!WARNING]
> **Research Prototype Notice**:
> - BharatPII is an **academic research prototype** developed for investigating sequence-constrained multilingual PII extraction in Indian linguistic settings.
> - **Not Certified**: This model is **not certified** under India's Digital Personal Data Protection Act (DPDPA 2023) and does **not** guarantee complete anonymization or zero false positives.
> - **Potential Failure Modes**:
>   1. **False Positives on Decoys**: High recall ($93.51\%$) causes over-triggering on ambiguous alphanumeric codes (order IDs, tracking numbers resembling account numbers or PANs).
>   2. **Boundary Truncations**: While linear-chain CRF decoding reduces span fragmentation by $68.7\%$ compared to unconstrained softmax, complex multi-token addresses or honorific prefixes may exhibit slight boundary shifts.
>   3. **Synthetic Training Distribution**: Adapted on synthetically generated Indic contexts; degraded performance may occur on noisy OCR scans or extreme slang.
> - **Human Review Required**: Unattended production deployment on sensitive citizen data is strongly discouraged without human-in-the-loop review.
> - **Privacy Guarantee**: All operations run **strictly offline and locally**. No text is transmitted externally.
