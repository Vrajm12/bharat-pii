# Artifact Engineering V1 — Final Comprehensive Report
**Document Identifier**: `REPORTS-ARTIFACT-ENG-FINAL-REPORT-V1.0`  
**Phase**: Artifact Engineering V1 (Post-Scientific-Freeze)  
**Status**: **ARTIFACT ENGINEERING — COMPLETE**  
**Readiness Level**: **CLEAN-ROOM REPRODUCTION READY**  
**Date**: September 9, 2026  

---

## 1. Objective

This engineering phase operationalized the scientifically frozen Indian PII Robustness Benchmark (Baselines B1 through B6, with no Baseline B7) into a clean, reproducible, and externally usable research artifact. 

Strict non-negotiable boundaries were maintained:
- Zero modifications to canonical benchmark records, annotation guidelines, or metric definitions.
- Zero retraining of baselines or regeneration of canonical predictions/reports.
- 100% bitwise cryptographic hash preservation of all 22 canonical locked artifacts.
- Non-canonical reproduction outputs isolated exclusively into `reproduction/`.

---

## 2. Repository Audit Summary

An automated audit of all 478 files in the repository cataloged and classified every component:

| Category | File Count | Description |
| :--- | :---: | :--- |
| **`CANONICAL_SCIENTIFIC`** | 24 | 22 locked canonical files + adaptation datasets + guidelines (Permanently Frozen) |
| **`PUBLIC_RELEASE`** | 72 | Core benchmark package, public CLI tools, documentation, tests, and metadata |
| **`DERIVED_ARTIFACT`** | 35 | Master tables, breakdown CSVs, publication figures, final scientific reports |
| **`EXPERIMENTAL_ARCHIVE`** | 148 | SV-01, SV-02, SV-03, B6 intermediate experiments, analysis JSONs, checkpoints |
| **`DEVELOPMENT_ONLY`** | 77 | Synthetic generators, dataset validators, internal training scripts |
| **`SCRATCH`** | 122 | Temporary exploration scripts and bytecode caches |

Complete records are maintained in `reports/artifact_engineering/REPOSITORY_AUDIT.md` and `REPOSITORY_INVENTORY.json`.

---

## 3. Scientific Freeze Boundary

The frozen boundary encompasses:
1. **Data Layer**: 964 canonical evaluation records ($N_{gold} = 724$), disjoint adaptation corpus (200 train, 50 val base instances), and annotation guidelines.
2. **Model Layer**: Baselines B1 (Regex), B2 (spaCy), B3 (Presidio), B4 (Zero-Shot XLM-R), B5 (Adapted XLM-R), and B6 (Adapted XLM-R + Linear CRF). **No B7 model created.**
3. **Results Layer**: All canonical predictions and evaluation reports for B1–B6, SV-01, SV-02, and SV-03.
4. **Documentation Layer**: `FINAL_SCIENTIFIC_RECORD.md`, `FINAL_CLAIM_AUDIT.md`, `FINAL_LIMITATIONS.md`, and `FINAL_FREEZE_DECLARATION.md`.

Recorded in `reports/artifact_engineering/FREEZE_BOUNDARY.md`.

---

## 4. Public Repository Structure

The repository structure cleanly separates public research tooling from historical archives:
```
indian-pii-robust/
├── README.md                          # Comprehensive 19-section public guide
├── LICENSE                            # MIT License with third-party model notice
├── CITATION.cff                       # Citation metadata
├── pyproject.toml                     # Standard Python packaging configuration
├── requirements.txt                   # Core runtime requirements
├── requirements-lock.txt              # Exact locked environment versions
│
├── benchmark/                         # Public evaluation package
│   ├── evaluate.py                    # CLI: python -m benchmark.evaluate
│   ├── predict.py                     # CLI: python -m benchmark.predict
│   ├── evaluator.py                   # Canonical bipartite matching & evaluation
│   ├── metrics.py                     # Mathematical formulations (M1–M6)
│   ├── schema.py                      # Gold entity and prediction schemas
│   └── runner.py                      # Canonical benchmark loader & stats
│
├── baselines/                         # Standard baseline adapters (B1–B6)
├── scripts/                           # Non-canonical reproduction runners
│   ├── reproduce_b5.py                # B5 inference -> reproduction/b5/
│   └── reproduce_b6.py                # B6 inference -> reproduction/b6/
│
├── docs/                              # Comprehensive technical documentation
│   ├── DATASET.md                     # Dataset schema, records, splits, provenance
│   ├── ANNOTATION.md                  # Annotation rules and span boundaries
│   ├── METRICS.md                     # Metric formulations and accounting invariants
│   ├── BASELINES.md                   # B1–B6 baseline architectures and decoding
│   ├── MODEL_PROVENANCE.md            # Checkpoints, revisions, and seed policy
│   └── CLEAN_ROOM_REPRODUCTION.md     # Step-by-step external reproduction guide
│
├── reports/
│   ├── FINAL_SCIENTIFIC_RECORD.md     # Authoritative 18-section scientific record
│   ├── FINAL_CLAIM_AUDIT.md           # Claim verification register
│   ├── FINAL_LIMITATIONS.md           # Authoritative limitations register
│   ├── FINAL_FREEZE_DECLARATION.md    # Formal freeze certification
│   ├── final/                         # Master tables, breakdown CSVs, figures
│   └── artifact_engineering/          # Audits, manifests, hashes, test records
│
└── tests/                             # Comprehensive automated test suite (1,000 tests)
```

---

## 5. Public CLI Interfaces

1. **Evaluation CLI (`benchmark.evaluate`)**:
   ```bash
   python -m benchmark.evaluate --gold data/raw/base_instances.jsonl --predictions predictions/regex_1.0.0_v0.18.jsonl --output reports/eval.json
   ```
   - Validates prediction JSONL schema.
   - Computes canonical metrics ($M_1$–$M_6$) and error partitions ($F_1$–$F_4$).
   - Emits ASCII summary table and machine-readable JSON.

2. **Prediction CLI (`benchmark.predict`)**:
   ```bash
   python -m benchmark.predict --system b6 --input input.jsonl --output predictions.jsonl --seed 42
   ```
   - Thin wrappers over existing baseline adapters (B1–B6).
   - Generates schema-compliant prediction JSONL.

---

## 6. Documentation Manifest

All required documentation artifacts have been created, cross-referenced, and reviewed:
- [`README.md`](../../README.md) — 19 structured sections, synthetic data notice, frozen results table.
- [`docs/DATASET.md`](../../docs/DATASET.md) — Schemas, synthetic provenance, leakage audits.
- [`docs/ANNOTATION.md`](../../docs/ANNOTATION.md) — Span semantics, boundary rules, referencing `annotation/guidelines.md`.
- [`docs/METRICS.md`](../../docs/METRICS.md) — Exact metric definitions, bipartite matching, accounting invariants.
- [`docs/BASELINES.md`](../../docs/BASELINES.md) — B1–B6 paradigms, CRF sequence decoding without claiming "semantic understanding".
- [`docs/MODEL_PROVENANCE.md`](../../docs/MODEL_PROVENANCE.md) — Upstream commits, seeds, hyperparameters, license requirements.
- [`docs/CLEAN_ROOM_REPRODUCTION.md`](../../docs/CLEAN_ROOM_REPRODUCTION.md) — Step-by-step instructions for clean-room reproduction.

---

## 7. Environment Reproducibility

Exact system versions were audited via `importlib.metadata` and locked:
- **Python**: 3.10.6 (tags/v3.10.6:9c7b4bd)
- **PyTorch**: 2.13.0
- **Transformers**: 5.16.1
- **Tokenizers**: 0.23.1
- **SentencePiece**: 0.2.2
- **Safetensors**: 0.8.0
- **spaCy**: 3.8.16 (model `en_core_web_sm` 3.8.0)
- **Presidio Analyzer**: 2.2.364
- **Matplotlib**: 3.10.9
- **NumPy**: 2.2.6
- **PyTest**: 8.4.2
- Artifacts: `requirements.txt`, `requirements-lock.txt`, and `pyproject.toml`.

---

## 8. Model Provenance

- **Baseline B4**: `Davlan/xlm-roberta-base-ner-hrl` at git commit `253f557bd8249b8515114cfd7f71974fe5fa4d2f`.
- **Baselines B5 & B6**: Derived from `xlm-roberta-base` adapted across frozen seeds `42`, `43`, `44`.
- **Hyperparameters**: Documented in `docs/MODEL_PROVENANCE.md`.
- **License Note**: Third-party model license terms explicitly marked as requiring author verification before public weight hosting.

---

## 9. Release Manifest & Hashes

- **Release Classification**:
  - `RELEASE_REQUIRED`: 81 files (code, canonical data, docs, reports, figures, reproduction scripts).
  - `OPTIONAL`: Extended test files and adaptation sets.
  - `ARCHIVE_ONLY`: Historical experiment JSONs and intermediate model checkpoints.
- **Cryptographic Hashes**:
  - All 22 canonical locked files match their frozen MD5 hashes ($100.0\%$).
  - All release files supplemented with SHA-256 in `reports/artifact_engineering/RELEASE_HASHES.json` and `.md`.

---

## 10. Privacy & Synthetic Data Compliance

- **Zero Real PII**: All 964 evaluation records and adaptation instances were synthetically constructed.
- **Zero Credentials**: Automated scan detected zero API tokens, passwords, private keys, or credentials.
- **Compliance**: Conforms with the Indian Digital Personal Data Protection (DPDP) Act 2023. Certified in `reports/final/PRIVACY_RELEASE_AUDIT.md`.

---

## 11. License Audit

- **Benchmark Code**: MIT License (`LICENSE`).
- **Benchmark Data**: CC BY 4.0 recommended for public dataset release.
- **Dependencies**: All permissive open source (MIT, BSD-3, Apache-2.0).
- **Checkpoints**: Upstream model license terms require author verification before binary weight redistribution. Documented in `reports/artifact_engineering/LICENSE_AUDIT.md`.

---

## 12. Public Figure Audit

All 8 publication figures in `reports/final/figures/` were verified against canonical data:
- `fig1` (Overall F1), `fig2` (Precision-Recall), `fig3` (Error Partition), `fig4` (Boundary Errors), `fig5` (SV-02 Ablation), `fig6` (FP Breakdown), `fig7` (Language Robustness), `fig8` (Perturbation Profile).
- High resolution (300 DPI), clean typography, zero misleading annotations.
- Every figure has an identical companion `.json` source file.

---

## 13. Standard Deviation (SD) Reconciliation

- **Reconciliation Finding**: Canonical JSON evaluation reports utilize **Sample Standard Deviation ($s$, `ddof=1`, denominator $N-1$)**, while certain earlier summary tables reported population SD (`ddof=0`, denominator $N$).
- **Standard Established**: All multi-seed tables and summaries consistently present **Mean ± Sample Standard Deviation (`ddof=1`) across seeds 42, 43, 44**.
- Documented in `reports/artifact_engineering/SD_RECONCILIATION.md`.

---

## 14. Full Test Suite Results

The complete repository test suite was executed **TWICE consecutively** on Windows 11 with Python 3.10.6:
- **Pass 1**: **1,000 passed** in 271.10s (0 failures, 0 errors).
- **Pass 2**: **1,000 passed** in 265.40s (0 failures, 0 errors).
- Documented in `reports/artifact_engineering/FINAL_ENGINEERING_TEST_RECORD.md`.

---

## 15. Known Limitations

1. **A1 Whitespace Sensitivity**: Exact F1 drops from 0.7812 (clean) to 0.2941 (A1) due to SentencePiece BPE sub-word splitting.
2. **Decoy FPR**: 100% record-level FPR on held-out pure hard-negative decoy numbers.
3. **Synthetic Domain Boundary**: Does not yet evaluate non-Hindi Indic scripts (e.g., Tamil, Telugu, Bengali) or physical scan noise.

---

## 16. Remaining Release Blockers (Pre-Publication Checklist)

Before public release to PyPI, GitHub, and Hugging Face:
1. [ ] Fill author names and affiliations in `CITATION.cff` and `README.md`.
2. [ ] Update public repository URL in `CITATION.cff` and `pyproject.toml`.
3. [ ] Confirm upstream model license terms for `Davlan/xlm-roberta-base-ner-hrl` before binary weight distribution.

---

## 17. Clean-Room Reproduction Readiness

The repository is fully equipped for independent clean-room execution:
- Detailed instructions in `docs/CLEAN_ROOM_REPRODUCTION.md`.
- Isolated runner scripts (`scripts/reproduce_b5.py`, `scripts/reproduce_b6.py`).
- Isolated output directories (`reproduction/b5/`, `reproduction/b6/`).
- Numerical tolerances and verification commands clearly defined.

---

## Final Status

```
======================================================================
ARTIFACT ENGINEERING: COMPLETE
BENCHMARK VERSION: 0.18.0
CANONICAL HASHES: 100% MATCH (22 / 22)
TEST SUITE: 1,000 / 1,000 PASSED (TWICE CONSECUTIVELY)
CANONICAL PROTECTIONS: VERIFIED
NEXT PHASE: CLEAN-ROOM REPRODUCTION READY
======================================================================
```
