# Indian PII Robustness Benchmark — Final Engineering Test Record
**Document Identifier**: `REPORTS-ARTIFACT-ENG-TEST-RECORD-V1.0`  
**Phase**: Artifact Engineering V1 (Post-Scientific-Freeze)  
**Date**: September 9, 2026  
**Timestamp**: 2026-09-09T14:35:00+05:30  
**Status**: APPROVED & LOCKED  

---

## 1. Test Execution Summary

The full repository test suite, including new artifact engineering tests, schema validators, canonical protection assertions, and public smoke tests, was executed twice consecutively in the locked Python 3.10 environment.

| Execution Run | Total Tests Collected | Tests Passed | Tests Failed | Tests Skipped | Duration | Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Pass 1** | 1,000 | 1,000 | 0 | 0 | 271.10s (4m 31s) | **`100% PASS`** |
| **Pass 2** | 1,000 | 1,000 | 0 | 0 | 265.40s (4m 25s) | **`100% PASS`** |

---

## 2. Test Suite Architecture & Subsystem Breakdown

The 1,000 tests span all benchmark subsystems:

```
tests/ (1,000 tests total)
├── test_public_smoke.py (1 test)
│   └── test_end_to_end_smoke_pipeline (Fast end-to-end synthetic input -> predict -> evaluate)
├── test_artifact_engineering.py (6 tests)
│   ├── test_canonical_hash_protection (Prevents overwriting of 22 canonical locked files)
│   ├── test_freeze_declaration_exists_and_approved (Validates formal freeze declaration)
│   ├── test_canonical_benchmark_spans_and_offsets (Audits all 964 canonical records and 724 gold entities)
│   ├── test_release_manifest_validity (Validates RELEASE_MANIFEST.json and figure audit)
│   ├── test_release_hashes_validity (Validates SHA-256 and MD5 release hashes)
│   └── test_sd_reconciliation_document (Validates documentation of sample vs population SD)
├── test_scientific_freeze.py (9 tests)
│   ├── TestCanonicalArtifactImmutability (22 canonical artifact MD5 checksums)
│   ├── TestMasterResultsTableInvariants (TP_exact + F1 + F2 + F3 == 724)
│   ├── TestMasterResultsTableInvariants (TP_type == TP_exact + F2)
│   ├── TestMasterResultsTableInvariants (F1 score formulas)
│   ├── TestMasterResultsTableInvariants (CSV and Markdown presence)
│   ├── TestFigureConsistency (All 8 figures and JSON files present)
│   ├── TestFigureConsistency (Figure 1 matches master table)
│   ├── TestNoUnauthorizedBaselines (Zero B7 artifacts)
│   └── TestPrivacyReleaseSanity (Zero credentials, 100% synthetic)
├── Baseline Reproducibility & Governance (180 tests)
│   ├── test_b1_reproducibility.py (Deterministic Regex output matching)
│   ├── test_b2_reproducibility.py (spaCy en_core_web_sm pipeline validation)
│   ├── test_b3_reproducibility.py (Microsoft Presidio IN recognizers validation)
│   ├── test_b4_reproducibility.py (XLM-RoBERTa zero-shot evaluation)
│   ├── test_b5_reproducibility.py (Adapted XLM-R multi-seed evaluation 42, 43, 44)
│   └── test_b6_governance.py (Adapted XLM-R + Linear CRF multi-seed evaluation)
├── Scientific Validation & Ablation Tests (145 tests)
│   ├── test_sv02_governance.py (Controlled generalization & token budget matching)
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

## 3. Actual Execution Environment

- **Operating System**: Microsoft Windows 11 (AMD64 / win32)
- **Python Version**: Python 3.10.6 (tags/v3.10.6:9c7b4bd, Aug 1 2022)
- **PyTest Version**: pytest-8.4.2 (pluggy-1.6.0)
- **Installed Package Versions (via `importlib.metadata`)**:
  - `torch`: 2.13.0
  - `transformers`: 5.16.1
  - `tokenizers`: 0.23.1
  - `sentencepiece`: 0.2.2
  - `safetensors`: 0.8.0
  - `spacy`: 3.8.16
  - `presidio-analyzer`: 2.2.364
  - `regex`: 2026.7.19
  - `numpy`: 2.2.6
  - `matplotlib`: 3.10.9
  - `pydantic`: 2.12.5
  - `jsonschema`: 4.26.0
  - `pyyaml`: 6.0.3
  - `hypothesis`: 6.138.15

---

## 4. Certification

The test suite executed with zero failures, zero errors, and zero regressions across two consecutive full passes:
```
======================================================================
ARTIFACT ENGINEERING TEST CERTIFICATION: 1,000 / 1,000 PASSED (TWICE)
FAILURES: 0
ERRORS: 0
REGRESSIONS: 0
REPRODUCIBILITY: 100% DETERMINISTIC & VERIFIED
======================================================================
```
