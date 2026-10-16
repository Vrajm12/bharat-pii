# Step 1 Model Release Report: Official Distributable BharatPII-CRF Model Artifact

**Document Version**: 1.0.0  
**Date**: 2026-09-12  
**Status**: COMPLETE / PASS  
**Task Phase**: Productization Step 1 (Distributable Model Artifact Release)  
**Model Name**: BharatPII-CRF  
**Release Directory**: `models/bharatpii-crf-v1.0/`  

---

## Executive Summary
This report documents the completion of **Step 1 Productization** for the scientifically frozen BharatPII research project: the creation, packaging, and independent verification of the official distributable model artifact for **BharatPII-CRF** (`models/bharatpii-crf-v1.0/`).

The release packages the canonical frozen B6 checkpoint (`transformer_crf`, `5.16.1_xlm_roberta_base_indian_crf_v0.18`, primary seed 42) into a unified, self-contained `safetensors` model format equipped with standard Hugging Face configuration, offline tokenizers, label taxonomy mappings, machine-readable metadata, a comprehensive research model card, and cryptographic checksums. Standalone clean-process validation confirms **exact bitwise prediction parity (0 prediction mismatches across all 964 canonical test records, 1,073 detected entities)** and **100% metric reproduction** without altering any canonical benchmarks, annotations, predictions, reports, or frozen scientific artifacts.

```
======================================================================
STATUS: PASS
MODEL: n:/PROJECTS/indian-pii-robust/models/bharatpii-crf-v1.0
TOTAL PARAMETERS: 278,057,044
TRAINABLE PARAMETERS: 13,396 (in B6 adaptation)
ENCODER PARAMETERS: 278,043,648 (frozen base)
CANONICAL PARITY: 0 mismatches across 964 records (1,073 predictions)
TESTS: ALL PASSED
CANONICAL ARTIFACT INTEGRITY: PASS (22/22 canonical files bitwise identical)
NEXT STEP: Ready for Step 2 (Python Package / Library Development)
======================================================================
```

---

## 1. Canonical Checkpoint Identified
- **Model Name**: BharatPII-CRF
- **System Identifier**: `transformer_crf`
- **System Version**: `5.16.1_xlm_roberta_base_indian_crf_v0.18`
- **Canonical Seeds**: 42 (primary), 43, 44
- **Primary Checkpoint Selected**: Seed 42
  - Checkpoint Directory: `checkpoints/b6/b6_transformer_crf_seed42/`
  - Provenance: Reproduces canonical B6 prediction artifact `predictions/experiments/b6/transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.jsonl` (MD5: `549cce213b1b52e6dbb682810a4544c9`) and canonical evaluation report `reports/experiments/b6/evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.json` (MD5: `575662658e2457359933c3b678de033f`) with bitwise identity.

---

## 2. Exact Source Checkpoint Path
- **CRF Head Checkpoint**: `n:/PROJECTS/indian-pii-robust/checkpoints/b6/b6_transformer_crf_seed42/b6_crf_head.pt` (56,389 bytes, MD5: `c6730316fd029fa56aed99f4dafcda5c`)
- **Tokenizer Source**: `n:/PROJECTS/indian-pii-robust/checkpoints/b6/b6_transformer_crf_seed42/tokenizer.json` and `tokenizer_config.json`
- **Base Encoder Source**: XLM-RoBERTa-base (`C:/Users/VEERAJ/.cache/huggingface/hub/models--xlm-roberta-base/snapshots/e73636d4f797dec63c3081bb6ed5c7b0bb3f2089/`)

---

## 3. Model Architecture
- **Base Encoder**: XLM-RoBERTa-base (`XLMRobertaModel`)
  - Hidden Dimension: 768
  - Layers: 12 Transformer encoder layers
  - Attention Heads: 12
  - Intermediate Dimension: 3,072
  - Vocabulary Size: 250,002
  - Positional Embeddings: Absolute (max length 514)
- **Token Classification Emission Layer**: Linear projection ($768 \to 17$ logits) with dropout $p = 0.1$.
- **Sequence Decoding Layer**: Linear-chain Conditional Random Field (`LinearChainCRF`)
  - Transition Matrix: $17 \times 17$ parameter tensor
  - Boundary Vectors: 17 start-transition parameters, 17 end-transition parameters
  - Decoding Algorithm: Exact Viterbi dynamic programming.

---

## 4–7. Exact Parameter Counts
The parameter breakdown separates base encoder parameters (frozen during adaptation) from the sequence-labeling CRF head (trainable parameters optimized during B6 adaptation):

| Component | Tensor Count | Parameter Count | Trainable in B6 Adaptation | Notes |
|:---|:---:|:---:|:---:|:---|
| **4. Total Model Parameters** | **204** | **278,057,044** | — | Full model parameter set |
| **5. Trainable Parameters (B6)** | **5** | **13,396** | Yes | Head module (`TransformerB6CRFHead`) |
| **6. Encoder Parameters** | **199** | **278,043,648** | No (Frozen) | Base `xlm-roberta-base` weights |
| **7. CRF / Head Parameters** | **5** | **13,396** | Yes | Linear emission layer + CRF transitions |

### Head Tensor Breakdown:
- `classifier.weight`: $17 \times 768 = 13,056$ parameters
- `classifier.bias`: $17$ parameters
- `crf.transitions`: $17 \times 17 = 289$ parameters
- `crf.start_transitions`: $17$ parameters
- `crf.end_transitions`: $17$ parameters
- **Head Subtotal**: $13,056 + 17 + 289 + 17 + 17 = 13,396$ parameters.

---

## 8–10. Exported Model Files, File Sizes, and SHA-256 Checksums
All files are located in `models/bharatpii-crf-v1.0/`:

| Filename | File Size | SHA-256 Hash | Purpose |
|:---|:---:|:---|:---|
| `model.safetensors` | 1,112,252,632 bytes | `2b2196763d59a179786dcb2a5772a73786261dd14203ae84d24e2c8f9d52463c` | Unified float32 weights (204 tensors) |
| `config.json` | 1,506 bytes | `51b11af165eda20f028cfbdc296d9010a3f628eefa6516524cf07f62638b1d4d` | Hugging Face model architecture & label config |
| `label_map.json` | 349 bytes | `15f649301cb906beefeea6f067f3f9e451355b278ec30457d4843864d17fad3d` | Canonical 17-label IOB2 taxonomy map |
| `tokenizer.json` | 17,098,351 bytes | `a04dec98c0804beeedde93263778442d924081d88090d4ac3db097205fa959bd` | Fast tokenizer serialization |
| `tokenizer_config.json` | 358 bytes | `e695499389997ed77bc95644e7f8a116f47b1dc583bb984a936603926410f995` | Tokenizer settings and special token mappings |
| `sentencepiece.bpe.model` | 5,069,051 bytes | `cfc8146abe2a0488e9e2a0c56de7952f7c11ab059eca145a0a727afce0db2865` | Offline SentencePiece BPE vocabulary model |
| `special_tokens_map.json` | 174 bytes | `ec90664240d635ffbc5072475bf9d4ba62e260c39c9409301ab2a4d5d140417c` | Special tokens configuration |
| `model_metadata.json` | 1,765 bytes | `9d64914dfc73769434fdeb70b38f06fe3ce6944310854b035e6ef188c0289573` | Machine-readable release metadata |
| `MODEL_CARD.md` | 5,570 bytes | `890c74b605d86e4d94fbb97cf521d2975a525e4aeef21d7d0970e3e727ecab47` | Research documentation, scope, and metrics |
| `SHA256SUMS.txt` | 767 bytes | — | Cryptographic release manifest |

---

## 11. Tokenizer Information
- **Tokenizer Type**: `XLMRobertaTokenizer` / `XLMRobertaTokenizerFast`
- **Vocabulary Size**: 250,002 tokens
- **Subword Algorithm**: SentencePiece Byte-Pair Encoding (BPE)
- **Special Tokens**: `<s>` (BOS, id 0), `<pad>` (PAD, id 1), `</s>` (EOS/SEP, id 2), `<unk>` (UNK, id 3), `<mask >`.replace(' ', '') (MASK, id 250001)
- **Offline Usability**: All tokenizer dependencies (`tokenizer.json`, `sentencepiece.bpe.model`, `special_tokens_map.json`, `tokenizer_config.json`) are bundled inside the release directory. No remote network calls required.

---

## 12. Label Mapping (Canonical 17-Tag IOB2 Taxonomy)
The label IDs match the classifier linear layer outputs and CRF transition matrix indices:
```json
{
  "0": "O",
  "1": "B-PERSON",
  "2": "I-PERSON",
  "3": "B-PAN",
  "4": "I-PAN",
  "5": "B-AADHAAR",
  "6": "I-AADHAAR",
  "7": "B-PHONE",
  "8": "I-PHONE",
  "9": "B-EMAIL",
  "10": "I-EMAIL",
  "11": "B-UPI_ID",
  "12": "I-UPI_ID",
  "13": "B-BANK_ACCOUNT",
  "14": "I-BANK_ACCOUNT",
  "15": "B-ADDRESS",
  "16": "I-ADDRESS"
}
```

---

## 13–15. Canonical Parity Test & Metric Reproduction

### Parity Test Protocol:
The standalone validation script (`scripts/validate_bharatpii_model_release.py`) loaded `models/bharatpii-crf-v1.0/` independently and performed inference across all 964 canonical benchmark records.

- **Evaluated Records**: 964 / 964 records
- **Total Released Predictions**: 1,073
- **Total Canonical Predictions**: 1,073
- **Prediction Mismatch Count**: **0 mismatches** (100% exact match on span offsets, entity types, text slices, and confidence scores).
- **Native Python Unicode Slice Contract**: $100\%$ verified (`text[start:end] == p.text`).

### Metric Comparison Table:
| Metric | Released Distributable Model | Canonical B6 Checkpoint (v0.18) | Difference | Status |
|:---|:---:|:---:|:---:|:---:|
| **$TP_{\text{exact}}$** | 601 | 601 | 0 | EXACT |
| **$TP_{\text{type}}$** | 677 | 677 | 0 | EXACT |
| **$F_1$ (Missed Entities)** | 7 | 7 | 0 | EXACT |
| **$F_2$ (Boundary / Wrong Span)** | 76 | 76 | 0 | EXACT |
| **$F_3$ (Type Confusion)** | 40 | 40 | 0 | EXACT |
| **$F_4$ (False Positives on Decoys)** | 356 | 356 | 0 | EXACT |
| **Partition Sum ($TP_{\text{exact}} + F_1 + F_2 + F_3$)** | **724** | **724** | **0** | **INVARIANT HOLDS** |
| **$M_1$ (Exact Precision)** | 63.09% | 63.09% | 0.00% | EXACT |
| **$M_2$ (Exact Recall)** | 93.51% | 93.51% | 0.00% | EXACT |
| **$M_3$ (Type-Strict $F_1$)** | 75.35% | 75.35% | 0.00% | EXACT |
| **$M_4$ (Exact-Span $F_1$)** | 66.89% | 66.89% | 0.00% | EXACT |
| **$M_5$ (Instance Accuracy)** | 94.42% | 94.42% | 0.00% | EXACT |
| **$M_6$ (False Positive Rate)** | 33.18% | 33.18% | 0.00% | EXACT |

---

## 16. Test Suite Result
The full repository test suite was executed:
- **Command**: `python -m pytest tests/ -q`
- **Result**: ALL PASSED (1,000+ tests passed, 0 failures, 0 errors).
- **Model Release Suite**: `tests/test_model_release.py` passed 4/4 tests.
- **B6 Governance Suite**: `tests/test_b6_governance.py` passed 6/6 tests.

---

## 17. Canonical Artifact Integrity Result
All 22 canonical locked repository artifacts remain 100% bitwise identical with zero byte drift:
- `data/raw/base_instances.jsonl`: PASS
- `data/raw/hard_negative_bases.jsonl`: PASS
- `data/generated/language_realizations.jsonl`: PASS
- `data/generated/hard_negative_realizations.jsonl`: PASS
- `data/generated/adversarial_realizations.jsonl`: PASS
- `annotation/review_template.csv`: PASS
- `predictions/regex_1.0.0_v0.18.jsonl`: PASS
- `reports/evaluation_regex_1.0.0_v0.18.json`: PASS
- `predictions/spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.jsonl`: PASS
- `reports/evaluation_spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.json`: PASS
- `predictions/presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.jsonl`: PASS
- `reports/evaluation_presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.json`: PASS
- `predictions/transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.jsonl`: PASS
- `reports/evaluation_transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.json`: PASS
- `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.jsonl`: PASS
- `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.jsonl`: PASS
- `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.jsonl`: PASS
- `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.jsonl`: PASS
- `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.json`: PASS
- `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.json`: PASS
- `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.json`: PASS
- `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.json`: PASS

Canonical B6 predictions (`predictions/experiments/b6/transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.jsonl`) and canonical B6 evaluation reports (`reports/experiments/b6/evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.json`) also remain 100% bitwise identical.

---

## 18. Known Limitations & Failure Modes
1. **Decoy Alphanumeric False Positives ($F_4 = 356$)**: High sensitivity to Indian identifier formats causes false alarms on non-PII transaction IDs, invoice references, and order tracking codes.
2. **Boundary Imprecision on Complex Spans ($F_2 = 76$)**: While CRF sequence constraints drastically outperform unconstrained softmax ($F_2$ reduced by $68.7\%$), multi-component addresses and code-mixed names with prefixes still experience boundary truncations.
3. **Synthetic Domain Transfer**: The model was adapted on synthetic Indic templates and hard negatives. Real-world OCR transcripts with missing characters or irregular whitespace may degrade tokenization.

---

## 19. Unresolved Licensing & Provenance Questions
- **Base Model License**: XLM-RoBERTa is licensed under the MIT License (Facebook AI / Meta).
- **Adaptation Weights & Model Release**: Licensed for Academic and Research Evaluation purposes.
- **Data Privacy**: No private or actual citizen records were included; all data is synthetic.
- **Non-Goals Preserved**: No Python package, wheel, `setup.py`, or `pyproject.toml` library was created in this step. Step 1 successfully prepares the distributable artifact for downstream packaging in Step 2.
