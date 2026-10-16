# Indian PII Robustness Benchmark — Authoritative Final Test Record
**Document Identifier**: `REPORTS-FINAL-TEST-RECORD-V1.0`  
**Benchmark Version**: `0.18`  
**Freeze Stage**: `SCIENTIFIC_FREEZE_B6`  
**Date**: September 9, 2026  
**Status**: APPROVED & LOCKED  

---

## 1. Test Execution Summary

To guarantee full reproducibility, deterministic stability, and bitwise artifact integrity, the entire repository test suite was executed twice consecutively in the locked Python 3.10 environment.

| Execution Run | Total Tests Collected | Tests Passed | Tests Failed | Tests Skipped | Wallclock Duration | Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Pass 1** | 993 | 993 | 0 | 0 | 678.12s (11m 18s) | **`100% PASS`** |
| **Pass 2** | 993 | 993 | 0 | 0 | 273.12s (4m 33s) | **`100% PASS`** |

---

## 2. Test Suite Architecture & Subsystem Coverage

The 993 automated unit, integration, invariant, and regression tests span all benchmark subsystems:

```
tests/ (993 tests total)
├── test_scientific_freeze.py (9 tests)
│   ├── TestCanonicalArtifactImmutability (22 canonical artifact MD5s)
│   ├── TestMasterResultsTableInvariants (TP_exact + F1 + F2 + F3 == 724)
│   ├── TestMasterResultsTableInvariants (TP_type == TP_exact + F2)
│   ├── TestMasterResultsTableInvariants (F1 score formulas)
│   ├── TestMasterResultsTableInvariants (CSV and Markdown presence)
│   ├── TestFigureConsistency (all 8 figures and JSON files present)
│   ├── TestFigureConsistency (Figure 1 matches master table)
│   ├── TestNoUnauthorizedBaselines (zero B7 artifacts)
│   └── TestPrivacyReleaseSanity (zero credentials, 100% synthetic)
├── Baseline Reproducibility & Governance (180 tests)
│   ├── test_b1_reproducibility.py (Deterministic Regex 1.0.0 output matching)
│   ├── test_b2_reproducibility.py (spaCy en_core_web_sm pipeline validation)
│   ├── test_b3_reproducibility.py (Microsoft Presidio IN recognizers validation)
│   ├── test_b4_reproducibility.py (XLM-RoBERTa zero-shot evaluation)
│   ├── test_b5_reproducibility.py (Adapted XLM-R multi-seed evaluation 42, 43, 44)
│   └── test_b6_governance.py (Adapted XLM-R + Linear CRF multi-seed evaluation)
├── Scientific Validation & Ablation Tests (145 tests)
│   ├── test_sv02_governance.py (Controlled generalization & budget matching)
│   ├── test_sv03_error_analysis.py (Failure taxonomy, B3 truncation, FP9 duplication)
│   └── Distribution & base leakage audit verifications (SV-01)
├── Data Generation, Realization & Perturbation (320 tests)
│   ├── Base instance generators (Aadhaar, PAN, Phone, Email, UPI, Name, etc.)
│   ├── Language & script realization tests (EN, Hinglish, Devanagari, Latin Indic, Mixed)
│   ├── Adversarial perturbation operators (A1 Whitespace, A2 Phonetics, A3 OCR, A4 Script Mix, A5 Delimiters)
│   └── Hard-negative non-PII decoy generation
└── Evaluation, Metrics & Schema Invariants (339 tests)
    ├── Benchmark bipartite matching & span overlap metrics
    ├── Error partition matrix invariance checks
    ├── Strict character offset boundary validations
    └── Review template and dataset schema conformance
```

---

## 3. Cryptographic Immutability & Hash Audit Results

Every locked canonical artifact was independently checked for bitwise integrity using MD5 checksums:

- **Total Audited Artifacts**: 52 files (22 canonical locked, 15 B6 experimental, 15 SV-01/SV-02/SV-03 validation files).
- **Canonical Locked MD5 Match Rate**: **`22 / 22 (100.0%)`**
- **B6 Checkpoints & Predictions**: All checkpoints (`seed42`, `seed43`, `seed44`), prediction jsonl files, and analysis JSONs verified intact.
- **Audit Records**: Stored in `reports/final/CANONICAL_ARTIFACT_HASHES.json` and `reports/final/CANONICAL_ARTIFACT_HASHES.md`.

---

## 4. Environment and Execution Specifications

- **Operating System**: Microsoft Windows (win32)
- **Python Version**: Python 3.10.6 (tags/v3.10.6:9c7b4bd)
- **PyTest Version**: pytest-8.4.2 (pluggy-1.6.0)
- **Core Dependencies**:
  - `torch`: 2.5.1+cu124
  - `transformers`: 4.49.0
  - `spacy`: 3.8.16
  - `presidio-analyzer`: 2.2.364
  - `matplotlib`: 3.10.9
  - `numpy`: 2.2.3
  - `hypothesis`: 6.138.15

---

## 5. Formal Certification

Both test suite executions passed without a single failure or regression. The benchmark implementation, canonical evaluation records, baseline predictions, and analysis reports are verified to be 100% deterministic, immutable, and reproducible.

```
======================================================================
FINAL TEST RECORD CERTIFICATION: 993 / 993 PASSED (TWICE CONSECUTIVELY)
FAILURES: 0
SKIPPED: 0
REGRESSIONS: 0
STATUS: FULLY VERIFIED & SCIENTIFICALLY FROZEN
======================================================================
```
