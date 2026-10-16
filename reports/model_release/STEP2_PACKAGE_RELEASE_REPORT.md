# Step 2 Package Release Report: Official Installable Python Package (`bharatpii`)

**Document Version**: 1.0.0  
**Date**: 2026-09-12  
**Status**: COMPLETE / PASS  
**Task Phase**: Productization Step 2 (Installable Python Library Release)  
**Package Name**: `bharatpii`  
**Package Version**: `1.0.0`  
**Model Name**: BharatPII-CRF  
**Model Release Path**: `models/bharatpii-crf-v1.0/`  

---

## Executive Summary

This report certifies the successful delivery and empirical verification of **Step 2 Productization**: the official installable Python library/package (`bharatpii` v1.0.0) for the scientifically frozen **BharatPII-CRF** model artifact (`models/bharatpii-crf-v1.0/`).

The `bharatpii` package serves as a pure inference and productization wrapper around the frozen Step 1 model release. Built under strict zero-drift and architectural-immutability constraints, the library introduces no weight modifications, no retraining, no pruning, no quantization, and no alterations to canonical benchmarks or evaluation artifacts.

### Key Release Milestones:
1. **Zero Prediction Drift**: 0 prediction mismatches across all 964 canonical test records (1,073 detected entities) compared against frozen canonical B6 predictions (`predictions/experiments/b6/transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.jsonl`). All evaluation metrics reproduced to machine precision.
2. **Decoupled Packaging Architecture**: Built standards-compliant pure Python wheel (`bharatpii-1.0.0-py3-none-any.whl`, 15,029 bytes) and source distribution (`bharatpii-1.0.0.tar.gz`, 101,315 bytes). The wheel cleanly excludes large model weights (1.11 GB), benchmark datasets, and gold labels.
3. **Clean-Room Verification**: Verified in an isolated virtual environment (`.venv_package_test`) outside the repository tree, confirming seamless installation, model loading, and multilingual inference.
4. **Strict Character Offset Slicing**: Validated that for every predicted entity, the slice contract `text[start:end] == entity.text` holds across Latin, Devanagari, Bengali, Tamil, Telugu, and mixed-script inputs.
5. **Comprehensive Test Suite**: 16/16 package tests passing in `tests/package/` and 35/35 full regression and governance tests passing repository-wide.
6. **Privacy & Security Integrity**: Certified offline operation with zero telemetry, zero analytics, zero external network calls, and zero credential dependencies.
7. **Step-1 & Benchmark Immutability**: All 10 Step-1 model release files and all 22 canonical benchmark files verified bitwise identical against their pre-flight SHA-256 and MD5 checksums.

```
======================================================================
STEP 2 STATUS: PASS
PACKAGE: bharatpii 1.0.0
MODEL: bharatpii-crf-v1.0
MODEL PARAMETERS: 278,057,044
TRAINED TASK HEAD: 13,396
CANONICAL PARITY: 0 mismatches / 964 records
WHEEL: PASS
CLEAN INSTALL: PASS
FULL TEST SUITE: PASS
STEP-1 INTEGRITY: PASS
PRIVACY: PASS
LICENSE: VERIFIED
FINAL: PASS
======================================================================
```

---

## 1. Package Architecture and Component Design

The package is structured modularly with clear separation between model weights, neural inference, sequence decoding, token alignment, and developer interfaces:

```
bharatpii/
├── __init__.py      # Top-level namespace exports (BharatPII, Entity, PredictionResult, __version__)
├── version.py       # Single source of truth for package version (__version__ = "1.0.0")
├── types.py         # Strongly-typed immutable dataclasses (Entity, PredictionResult)
├── labels.py        # Canonical 17-label IOB2 taxonomy definitions and label maps
├── model.py         # PyTorch neural layers: LinearChainCRF, BharatPIICRFHead, BharatPIIModel
├── tokenizer.py     # Offline tokenization loading and subword-to-character alignment utilities
├── pipeline.py      # High-level developer pipeline: BharatPII.from_pretrained()
└── cli.py           # Command-line interface: python -m bharatpii or bharatpii executable
```

### Architectural Design Principles:
- **Separation of Weights and Code**: Model weights (1.11 GB) reside in `models/bharatpii-crf-v1.0/` or any local directory, decoupled from package code.
- **Offline Self-Sufficiency**: Tokenizers and configuration are loaded with `local_files_only=True`. No runtime requests to Hugging Face Hub or internet endpoints occur.
- **Pure PyTorch Inference**: The architecture leverages standard PyTorch modules and Hugging Face Transformers primitives without external C++ compilation requirements.
- **Deterministic Viterbi Decoding**: The exact dynamic programming implementation reproduces the transition scores of the canonical B6 architecture with mathematical exactness.

---

## 2. Public API Specification

The package exposes an ergonomic, type-hinted public API adhering to Python conventions:

### Core Classes & Exports:
- `BharatPII`: The main inference pipeline object.
  - `BharatPII.from_pretrained(model_path, device=None)`: Factory method to load model, tokenizer, and config from local filesystem.
  - `predict(text: str) -> PredictionResult`: Analyzes a single string and returns typed entity spans.
  - `predict_batch(texts: List[str], batch_size: int = 16) -> List[PredictionResult]`: High-throughput batch inference with sequence padding.
  - `info() -> Dict[str, Any]`: Returns architecture metadata, parameter counts, label taxonomy, and device location.
- `Entity`: Immutable dataclass representing an extracted PII entity:
  - `text: str`: Exact substring extracted from source text.
  - `label: str`: Canonical PII entity category (e.g., `NAME`, `PHONE`, `AADHAAR`, `PAN`, `ADDRESS`, `EMAIL`, `BANK_ACCOUNT`, `DATE_OF_BIRTH`).
  - `start: int`: 0-indexed character start position in original text.
  - `end: int`: Character end position (exclusive) in original text.
  - `confidence: float`: Posterior confidence score (`1.0` for Viterbi sequence optimal).
  - `to_dict() -> Dict[str, Any]`: Serialization to dictionary.
- `PredictionResult`: Result container for an input text:
  - `text: str`: Original input string.
  - `entities: List[Entity]`: List of detected PII entities ordered by character position.
  - `to_dict() -> Dict[str, Any]`: Structured dictionary serialization.

---

## 3. Character Offset Guarantee & Invariants

A critical requirement in PII redaction and compliance pipelines is byte/character alignment integrity. Subword tokenization (especially BPE with SentencePiece) can misalign spans across multibyte Unicode code points in Indic scripts.

### Slicing Contract:
For every returned entity e in result.entities:
`text[e.start:e.end] == e.text`

### Verification:
1. **Latin & ASCII**: Validated on phone numbers, PAN cards, email addresses, and names.
2. **Devanagari (Hindi/Marathi)**: Validated on names, addresses, and date expressions containing complex ligatures, viramas, and combining diacritics.
3. **Bengali, Tamil, Telugu**: Validated on Indic script sequences in `tests/package/test_inference.py`.
4. **Mixed Code-Switched Inputs**: Validated on Hindi-English transliterated and mixed-script text.
5. **Boundary Invariants**: In `tests/package/test_canonical_parity.py`, all 1,073 predictions across 964 benchmark texts were programmatically asserted against the slicing contract with zero violations.

---

## 4. Distribution Artifacts

The package was compiled using standard PEP 517 build tooling (`build` v1.6.1, `setuptools` v84.0.0, `wheel` v0.46.3):

| Artifact Filename | Format | Size (Bytes) | SHA-256 Checksum |
|:---|:---:|:---:|:---|
| `bharatpii-1.0.0-py3-none-any.whl` | Pure Python Wheel | 15,029 | `99c1caa1a6dc5dc9fd30eda485405341ebbc2a5b19ea160aa1fc58ed19873105` |
| `bharatpii-1.0.0.tar.gz` | Source Distribution | 101,315 | `b464f0dc0b1068b0b1c9b0fef7030c5e3d6a4efcb0948db8f3edc321873feab9` |

---

## 5. Model Decoupling & Distribution Architecture

### Rationale for Weight Separation:
The model weights (`model.safetensors`) occupy 1.11 GB (1,112,252,632 bytes), while tokenizer and vocab models occupy an additional 22 MB. Bundling these weights directly inside a Python wheel violates standard package repository constraints (e.g., PyPI 100 MB file limit) and prevents downstream users from caching or containerizing model weights independently.

### Architecture:
- The wheel is lightweight (15 KB), containing only code, types, and schemas.
- The model weights reside in their own versioned directory (`models/bharatpii-crf-v1.0/`).
- Loading is explicit and clean:
  ```python
  from bharatpii import BharatPII
  model = BharatPII.from_pretrained("models/bharatpii-crf-v1.0")
  ```

---

## 6. Wheel Packaging Audit

A granular zip inspection was performed on `dist/bharatpii-1.0.0-py3-none-any.whl` to ensure complete isolation:

### Included Files in Wheel:
- `bharatpii/__init__.py`
- `bharatpii/cli.py`
- `bharatpii/labels.py`
- `bharatpii/model.py`
- `bharatpii/pipeline.py`
- `bharatpii/tokenizer.py`
- `bharatpii/types.py`
- `bharatpii/version.py`
- `bharatpii-1.0.0.dist-info/*` (METADATA, WHEEL, entry_points.txt, RECORD, licenses/LICENSE)

### Verification of Exclusions:
- **Model weights**: 0 weight files included (`model.safetensors` is absent).
- **Gold test labels**: 0 test data or annotations included.
- **Benchmark datasets**: 0 CSV/JSON/JSONL test splits included.
- **Experimental checkpoints**: All `checkpoints/` excluded.
- **Internal research code**: All `baselines/`, `analysis/`, `scripts/` excluded.

---

## 7. Model Parameters and Disaggregation

The parameter counts in the loaded `BharatPIIModel` match the canonical Step 1 audit with exact bitwise precision:

| Component | Tensor Count | Parameter Count | Trainable in B6 Adaptation | Description |
|:---|:---:|:---:|:---|:---|
| **Base Encoder** | 199 | 278,043,648 | No (Frozen) | XLM-RoBERTa-base transformer layers |
| **Token Emission Head** | 2 | 13,073 | Yes | Linear projection (768 -> 17) + bias |
| **CRF Transitions** | 3 | 323 | Yes | Transition matrix (17 x 17) + start/end transitions |
| **Task Head Subtotal** | **5** | **13,396** | **Yes** | Task-specific adaptation parameters |
| **Total Model Parameters** | **204** | **278,057,044** | — | Complete model parameter set |

*Scientific Integrity Note*: 13,396 parameters were optimized during B6 adaptation. The base transformer encoder (278,043,648 parameters) was kept frozen throughout training.

---

## 8. Canonical Prediction Parity Verification

The `bharatpii` package pipeline was evaluated against the entire canonical benchmark test split (964 records) using the exact evaluation methodology.

### Zero-Mismatch Parity Result:
- **Total Records Evaluated**: 964
- **Total Released Package Predictions**: 1,073
- **Total Canonical B6 Predictions**: 1,073
- **Prediction Mismatches**: **0** (100.0% exact match on span boundaries, entity types, and record associations)

### Metric Reproduction Table:

| Metric Code | Metric Description | Canonical B6 Benchmark | `bharatpii` Package | Absolute Delta | Status |
|:---|:---|:---:|:---:|:---:|:---:|
| **TP_exact** | Exact Span & Type True Positives | 601 | 601 | 0 | **PASS** |
| **TP_type** | Type Match True Positives | 677 | 677 | 0 | **PASS** |
| **F1** | Missed Entities (False Negatives) | 7 | 7 | 0 | **PASS** |
| **F2** | Wrong Span Boundaries | 76 | 76 | 0 | **PASS** |
| **F3** | Wrong Entity Type | 40 | 40 | 0 | **PASS** |
| **F4** | False Positive Entities | 356 | 356 | 0 | **PASS** |
| **M1** | Entity Precision | 0.6309 | 0.6309 | 0.0000 | **PASS** |
| **M2** | Entity Recall | 0.9351 | 0.9351 | 0.0000 | **PASS** |
| **M3** | Type F1-Score | 0.7535 | 0.7535 | 0.0000 | **PASS** |
| **M4** | Exact F1-Score | 0.6689 | 0.6689 | 0.0000 | **PASS** |
| **M5** | System Accuracy | 0.9442 | 0.9442 | 0.0000 | **PASS** |
| **M6** | False Positive Rate (FPR) | 0.3318 | 0.3318 | 0.0000 | **PASS** |

### Partition Invariant:
TP_exact + F1 + F2 + F3 = 601 + 7 + 76 + 40 = 724 = N_gold.
Verified exactly.

---

## 9. Clean-Room Environment Verification

A clean virtual environment was created and isolated to verify wheel installation:
- Environment Path: `.venv_package_test`
- Installation Command: `pip install --no-deps dist/bharatpii-1.0.0-py3-none-any.whl`
- Execution Context: Executed from external user home directory (`C:\Users\VEERAJ`) outside the repository to ensure no repository imports were shadow-loading.
- Result:
  - Package import: `import bharatpii` succeeded.
  - `bharatpii.__version__`: returned `"1.0.0"`.
  - Model loading: loaded `BharatPII.from_pretrained("n:/PROJECTS/indian-pii-robust/models/bharatpii-crf-v1.0")` cleanly.
  - Inference: Correctly extracted entities in both English and Devanagari text with zero errors.

---

## 10. Package Test Suite Verification

The package-specific test suite located in `tests/package/` contains 16 automated tests covering the entire package surface:

| Test File | Test Name | Focus Area | Result |
|:---|:---|:---|:---:|
| `test_import.py` | `test_package_import_and_version` | Namespace exports, version string | PASS |
| `test_import.py` | `test_entity_dataclass` | Dataclass fields, offset validation, dict export | PASS |
| `test_import.py` | `test_prediction_result_dataclass` | Result structure, entity ordering, dict export | PASS |
| `test_model_loading.py` | `test_model_loading_and_parameter_counts` | Model architecture, parameter counts (278M / 13K) | PASS |
| `test_model_loading.py` | `test_model_info` | `.info()` dictionary structure and fields | PASS |
| `test_model_loading.py` | `test_missing_model_directory_raises` | Error handling for non-existent path | PASS |
| `test_model_loading.py` | `test_corrupted_manifest_raises` | Error handling for corrupt model files | PASS |
| `test_inference.py` | `test_empty_string_inference` | Edge case: empty string handling | PASS |
| `test_inference.py` | `test_single_english_inference` | Standard English sentence inference | PASS |
| `test_inference.py` | `test_devanagari_and_code_mixed_inference` | Multilingual Devanagari & code-switched text | PASS |
| `test_inference.py` | `test_character_slice_invariant_across_scripts` | Mathematical slice invariant across Indic scripts | PASS |
| `test_batch.py` | `test_batch_ordering_and_independence` | Batch inference ordering, batch vs single consistency | PASS |
| `test_cli.py` | `test_cli_info` | CLI `--info` flag output | PASS |
| `test_cli.py` | `test_cli_text_prediction` | CLI `--text` prediction execution | PASS |
| `test_cli.py` | `test_cli_file_input_output` | CLI `--input` / `--output` JSON batch execution | PASS |
| `test_canonical_parity.py` | `test_canonical_prediction_and_metric_parity` | Full canonical 964-record zero-mismatch evaluation | PASS |

**Package Test Suite Summary**: 16/16 PASSED (100% pass rate).

---

## 11. Full Regression & Governance Verification

A full regression run across the entire test suite was executed:
- `tests/package/`: 16/16 PASSED
- `tests/test_model_release.py`: 4/4 PASSED
- `tests/test_scientific_freeze.py`: 9/9 PASSED
- `tests/test_b6_governance.py`: 6/6 PASSED

**Total Regression Suite**: 35/35 PASSED (100% pass rate in 107.17 seconds).

---

## 12. Engineering Performance Benchmarks

Inference performance was empirically profiled using `scripts/benchmark_package_performance.py` on CPU:

### Profiling Environment:
- **Operating System**: Windows 10 (AMD64)
- **Processor**: Intel64 Family 6 Model 186 Stepping 2, GenuineIntel
- **Python**: 3.10.6
- **PyTorch**: 2.13.0+cpu
- **Device**: CPU

### Empirical Benchmark Metrics:
- **Model Cold Load Time**: 6.089 s
- **Process Memory (Pre-Load)**: 287.6 MB
- **Process Memory (Post-Load)**: 1,683.5 MB
- **Memory Delta (Model Footprint)**: +1,395.9 MB
- **Process Peak Memory**: 1,690.0 MB
- **Average Single-Text Latency**: 35.88 ms
- **Minimum Single-Text Latency**: 29.91 ms
- **Maximum Single-Text Latency**: 50.42 ms
- **Batch Throughput (Batch Size 10)**: 24.68 texts/second (0.405 s for 10 texts)

---

## 13. Privacy and Security Audit Summary

A dedicated privacy audit (`PACKAGE_PRIVACY_AUDIT.md`) evaluated the package for data exposure risks:
1. **Zero External Network Connectivity**: All tokenization, configuration, and weights load with `local_files_only=True`. No requests are initiated to Hugging Face, analytics servers, or remote endpoints.
2. **Zero Telemetry / Analytics**: The codebase contains zero telemetry libraries, tracking beacons, analytics SDKs, or usage reporting logic.
3. **No Credential Requirements**: The library requires no API keys, tokens, or environment credentials to run.
4. **Data Minimization & In-Memory Isolation**: Input texts processed by `predict()` and `predict_batch()` are held solely in volatile memory during tensor operations and are never logged, serialized to temporary files, or cached to disk.
5. **DPDPA 2023 Alignment**: The offline operational profile complies with the stringent data fiduciary requirements under the Indian Digital Personal Data Protection Act (DPDPA 2023).

---

## 14. License Compliance Audit Summary

A dedicated open-source license audit (`LICENSE_AUDIT.md`) verified all component dependencies:
1. **Package License**: Released under the permissive **MIT License**.
2. **Upstream Model Attribution**: The underlying base encoder (`xlm-roberta-base`) is distributed under the **Apache License 2.0**. Full Apache 2.0 copyright notices and disclaimers are preserved in `LICENSE` and `MODEL_CARD.md`.
3. **Third-Party Compatibility**: All core dependencies (`torch`, `transformers`, `safetensors`) use permissive open-source licenses (BSD, Apache 2.0).

---

## 15. Step-1 Model Artifact & Canonical Benchmark Immutability

The cryptographic hashes of all Step 1 release files and all canonical benchmark artifacts were verified before and after Step 2 execution:

### Step 1 Release Files (`models/bharatpii-crf-v1.0/`):
- `config.json`: `51b11af165eda20f028cfbdc296d9010a3f628eefa6516524cf07f62638b1d4d` — **MATCH**
- `label_map.json`: `15f649301cb906beefeea6f067f3f9e451355b278ec30457d4843864d17fad3d` — **MATCH**
- `model.safetensors`: `2b2196763d59a179786dcb2a5772a73786261dd14203ae84d24e2c8f9d52463c` — **MATCH**
- `MODEL_CARD.md`: `890c74b605d86e4d94fbb97cf521d2975a525e4aeef21d7d0970e3e727ecab47` — **MATCH**
- `model_metadata.json`: `9d64914dfc73769434fdeb70b38f06fe3ce6944310854b035e6ef188c0289573` — **MATCH**
- `sentencepiece.bpe.model`: `cfc8146abe2a0488e9e2a0c56de7952f7c11ab059eca145a0a727afce0db2865` — **MATCH**
- `special_tokens_map.json`: `ec90664240d635ffbc5072475bf9d4ba62e260c39c9409301ab2a4d5d140417c` — **MATCH**
- `tokenizer.json`: `a04dec98c0804beeedde93263778442d924081d88090d4ac3db097205fa959bd` — **MATCH**
- `tokenizer_config.json`: `e695499389997ed77bc95644e7f8a116f47b1dc583bb984a936603926410f995` — **MATCH**

### Canonical Benchmark Artifacts:
- All 22 canonical benchmark files verified bitwise untouched via `tests/test_scientific_freeze.py`.

---

## 16. Conclusion & Next Steps

Step 2 Productization is complete with 100% validation success. The `bharatpii` package provides a production-ready, zero-drift, privacy-preserving inference interface for the frozen BharatPII-CRF model, ready for downstream integration and public distribution.
