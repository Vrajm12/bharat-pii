# BharatPII-CRF Model Card

## Model Details
- **Model Name**: BharatPII-CRF
- **Model Version**: 1.0.0
- **System Name**: `transformer_crf`
- **System Version**: `5.16.1_xlm_roberta_base_indian_crf_v0.18`
- **Base Architecture**: XLM-RoBERTa-base (`xlm-roberta-base`)
- **Decoder Architecture**: Linear-chain Conditional Random Field (CRF) with Viterbi sequence decoding
- **Primary Canonical Seed**: 42 (Canonical seeds evaluated: 42, 43, 44)
- **Framework**: PyTorch (>=2.0.0), Hugging Face Transformers (5.16.1), `safetensors`
- **Format**: `safetensors` (float32)

---

## Parameter Breakdown
| Component | Tensors | Parameter Count | Trainable in B6 Adaptation | Notes |
|:---|:---:|:---:|:---:|:---|
| **Encoder (`xlm-roberta-base`)** | 199 | 278,043,648 | No (Frozen) | 12 layers, 768 hidden, 12 attention heads |
| **Linear Emission Layer** | 2 | 13,073 | Yes | 768 -> 17 classes (`weight`: 13,056, `bias`: 17) |
| **LinearChainCRF Decoder** | 3 | 323 | Yes | `transitions`: 289, `start`: 17, `end`: 17 |
| **CRF Head Subtotal** | 5 | 13,396 | Yes | Head module (`TransformerB6CRFHead`) |
| **Total Model** | **204** | **278,057,044** | **13,396** | Full model parameter set |

---

## Intended Use & Scope
- **Intended Use**: Academic and empirical evaluation of Indian PII detection, sequence-constrained decoding, and structural robustness across multilingual, code-mixed, and adversarial text.
- **Out-of-Scope Use**:
  - Direct unattended production redaction of sensitive citizen records without human-in-the-loop review.
  - Legal compliance certification (e.g., claiming automated compliance with India's DPDPA 2023).
  - High-stakes automated financial or judicial data redaction.

---

## Supported PII Categories (8 Types, 17 IOB2 Labels)
The model detects 8 Indian PII categories in IOB2 tagging format:
1. `PERSON`: Indian personal names across multiple ethnicities and naming conventions.
2. `PAN`: 10-character alphanumeric Permanent Account Number.
3. `AADHAAR`: 12-digit Indian national identity number.
4. `PHONE`: 10-digit Indian mobile and landline telephone numbers.
5. `EMAIL`: Email addresses.
6. `UPI_ID`: Unified Payments Interface Virtual Payment Addresses (VPAs).
7. `BANK_ACCOUNT`: Indian bank account numbers (9-18 digits).
8. `ADDRESS`: Indian street, locality, city, state, and PIN code physical addresses.

### Label Space
`0: O`, `1: B-PERSON`, `2: I-PERSON`, `3: B-PAN`, `4: I-PAN`, `5: B-AADHAAR`, `6: I-AADHAAR`, `7: B-PHONE`, `8: I-PHONE`, `9: B-EMAIL`, `10: I-EMAIL`, `11: B-UPI_ID`, `12: I-UPI_ID`, `13: B-BANK_ACCOUNT`, `14: I-BANK_ACCOUNT`, `15: B-ADDRESS`, `16: I-ADDRESS`.

---

## Supported Linguistic & Script Coverage
Evaluated across 7 language/script variants established in the canonical benchmark:
1. `EN`: Indian English formal.
2. `IN_EN`: Indian English bureaucratic and regional phrasing.
3. `HI_LATIN_PII`: Hindi written in Latin script with transliterated PII.
4. `HI_DEVA_PII`: Hindi written in Devanagari script with Devanagari-script PII.
5. `ROM_HI`: Romanized colloquial Hindi.
6. `HINGLISH`: Code-switched Hindi-English.
7. `INFORMAL_HINGLISH`: Informal conversational Hinglish with SMS abbreviations.

---

## Canonical Benchmark Performance (Seed 42 / v0.18)
Evaluated against the frozen 964-record canonical benchmark corpus (724 gold entities, 140 non-PII hard-negative decoy instances):
- **Exact Precision ($M_1$)**: 63.09%
- **Exact Recall ($M_2$)**: 93.51%
- **Type-Strict $F_1$ ($M_3$)**: 75.35%
- **Exact-Span $F_1$ ($M_4$)**: 66.89%
- **Instance Accuracy ($M_5$)**: 94.42%
- **False Positive Rate ($M_6$)**: 33.18%
- **Error Partition Breakdown**:
  - $TP_{	ext{exact}}$: 601
  - $F_1$ (missed entities): 7
  - $F_2$ (boundary/span errors): 76
  - $F_3$ (type confusion): 40
  - $F_4$ (spurious false positives): 356
  - Invariant: $TP_{	ext{exact}} + F_1 + F_2 + F_3 = 601 + 7 + 76 + 40 = 724$.

---

## Failure Modes & Limitations
1. **False Positives on Decoys ($F_4 = 356$)**: The high recall objective ($93.51\%$) results in over-triggering on contextually ambiguous alphanumeric strings (e.g., transaction references resembling account numbers or PANs).
2. **Boundary Precision ($F_2 = 76$)**: While CRF decoding reduces span fragmentation compared to unconstrained softmax ($F_2$ reduced from 243 in B5 to 76 in B6), multi-token addresses and romanized names with honorifics still experience boundary shifts.
3. **Synthetic Training Distribution**: Trained on rule-synthesized Indic contexts and hard negatives. Real-world noisy scans, OCR degradation, or heavy vernacular slang may induce out-of-distribution degradation.

---

## Output Contract
Inference produces span predictions with exact native Python Unicode slice indices:
`text[start:end] == predicted_text`
Each entity dictionary contains:
- `text`: Extracted entity substring.
- `start`: 0-indexed start character offset in raw text.
- `end`: 0-indexed end character offset (exclusive).
- `type`: Entity label (`PERSON`, `PAN`, etc.).
- `confidence`: Average token-level emission probability across the entity span (note: this is token emission confidence, not calibrated sequence posterior).

---

## Governance & Safety Notice
This model artifact is part of a research reproduction suite. No actual citizen PII was used in the training or evaluation of this model; all benchmark and adaptation data consists of synthetically generated instances adhering to Indian syntactic specifications and anonymized templates.
