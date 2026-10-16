# Indian PII Robustness Benchmark — Scratch & Experimental Audit
**Document Identifier**: `REPORTS-ARTIFACT-ENG-SCRATCH-AUDIT-V1.0`  
**Phase**: Artifact Engineering V1 (Post-Scientific-Freeze)  
**Status**: APPROVED  
**Date**: September 9, 2026  

---

## 1. Audit Scope & Guidelines

This audit reviews all non-canonical exploratory materials in `scratch/` and historical validation records in `reports/experiments/`.

**Non-Destructive Principle**: In accordance with the scientific freeze governance, no files are deleted. Instead, each artifact is categorized to determine whether it constitutes:
- **`ESSENTIAL_EVIDENCE`**: Required to substantiate claims in `FINAL_SCIENTIFIC_RECORD.md`.
- **`USEFUL_ARCHIVE`**: Valuable historical or diagnostic script, retained for provenance.
- **`DEVELOPMENT_ONLY`**: Internal debugging code, not needed for external evaluation.
- **`SAFE_TO_EXCLUDE_FROM_RELEASE`**: To be omitted from the minimal clean public source distribution (e.g., PyPI package or clean release zip).

---

## 2. Directory: `scratch/`

| Path | File Type | Purpose | Classification | Release Action |
| :--- | :--- | :--- | :--- | :--- |
| `scratch/audit_reports.py` | Python script | Diagnostic metric reconciliation script | `USEFUL_ARCHIVE` | Exclude from PyPI / clean release |
| `scratch/sv01/run_sv01_audit.py` | Python script | Prototype execution script for SV-01 | `USEFUL_ARCHIVE` | Exclude from PyPI / clean release |
| `scratch/sv01/diagnostic_results.json` | JSON data | Diagnostic overlap computations | `USEFUL_ARCHIVE` | Exclude from PyPI / clean release |
| `scratch/sv01/__pycache__/` | Cache | Python bytecode cache | `SCRATCH` | Exclude from all releases (`.gitignore`) |

**Recommendation for `scratch/`**: Retain in local repository git history for full audit trail, but exclude from public PyPI source distributions and public release tarballs.

---

## 3. Directory: `reports/experiments/`

### 3.1 `reports/experiments/sv02/` (Controlled Generalization Ablation)
- **Files**: 11 JSON evaluation reports (`evaluation_sv02_b5_*.json`, `sv02_master_evaluation.json`, `sv02_overlap_leakage_audit.json`).
- **Classification**: **`ESSENTIAL_EVIDENCE`**
- **Rationale**: Contains the multi-seed empirical data substantiating Claim 5 (that hard-negative data interventions alone do not solve exact-boundary collapse).
- **Release Action**: Retain in public repository under `reports/experiments/sv02/`.

### 3.2 `reports/experiments/sv03/` (Systematic Error Analysis)
- **Files**: 13 JSON analysis files (`sv03_error_summary.json`, `sv03_boundary_analysis.json`, `sv03_false_positive_analysis.json`, etc.) and `SV03_FINAL_REPORT.md`.
- **Classification**: **`ESSENTIAL_EVIDENCE`**
- **Rationale**: Substantiates the identification of $B_3$ (structured identifier truncation) and $FP_9$ (duplicate subspan emission) as the root failure mechanisms of independent token classification.
- **Release Action**: Retain in public repository under `reports/experiments/sv03/`.

### 3.3 `reports/experiments/b6/` (Sequence-Constrained CRF Baseline)
- **Files**: 15 files including seed evaluation reports (`seed42`, `seed43`, `seed44`), `b6_error_summary.json`, `b6_boundary_analysis.json`, `b6_representative_cases.json`, and `B6_FINAL_REPORT.md`.
- **Classification**: **`ESSENTIAL_EVIDENCE`**
- **Rationale**: Primary experimental proof of Baseline B6's $+0.2795$ Exact F1 gain and $-68.7\%$ boundary error reduction.
- **Release Action**: Retain in public repository under `reports/experiments/b6/`.

---

## 4. Release Distribution Filter Rules

When building public release artifacts (`.tar.gz`, `.whl`):
```
# Include in Public Source Distribution:
benchmark/
baselines/
docs/
reports/final/
reports/FINAL_*.md
CITATION.cff
LICENSE
README.md
pyproject.toml
requirements.txt
requirements-lock.txt

# Exclude from Minimal Package Build:
scratch/
checkpoints/ (host on Hugging Face Model Hub instead)
.pytest_cache/
__pycache__/
```
