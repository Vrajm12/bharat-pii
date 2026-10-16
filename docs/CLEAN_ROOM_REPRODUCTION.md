# Clean-Room Reproduction Guide
**Document Identifier**: `DOCS-CLEAN-ROOM-REPRO-V1.0`  
**Benchmark Version**: `0.18`  
**Status**: APPROVED  
**Date**: September 9, 2026  

---

## 1. Objective and Scope

This document provides complete, step-by-step instructions for an independent researcher or external auditor to reproduce Baselines **B5** and **B6** in a clean-room environment, evaluate the generated predictions against the frozen canonical benchmark, and verify consistency against published metrics within accepted scientific numerical tolerance.

> [!IMPORTANT]
> **Canonical vs. Reproduction Separation**:
> All commands in this guide write reproduction outputs strictly into `reproduction/b5/` and `reproduction/b6/`. Canonical artifacts under `predictions/` and `reports/` are immutable and must NEVER be overwritten.

---

## 2. Step-by-Step Reproduction Instructions

### Step 1: Clone Repository
```bash
git clone https://github.com/TODO-repo-placeholder/indian-pii-robust.git
cd indian-pii-robust
```

### Step 2: Set Up Python 3.10 Environment
It is strongly recommended to use a virtual environment with Python 3.10 (verified on Python 3.10.6):
```bash
python -m venv .venv
# On Linux/macOS:
source .venv/bin/activate
# On Windows PowerShell:
.venv\Scripts\Activate.ps1

# Install exact locked dependencies:
pip install -r requirements-lock.txt
```

### Step 3: Obtain Model Dependencies & Checkpoints
- Verify that pre-trained / adapted checkpoint weights are located in:
  - `checkpoints/b5_transformer_adapted_seed{42,43,44}/`
  - `checkpoints/b6/b6_transformer_crf_seed{42,43,44}/`
- If downloading from an external model registry, verify that the SHA-256 hashes match those documented in `docs/MODEL_PROVENANCE.md`.

### Step 4: Verify Canonical Benchmark Data
Confirm that the 964-record canonical benchmark is intact by running the verification check:
```bash
python -m pytest tests/test_scientific_freeze.py -k test_canonical_artifact_hashes
```

### Step 5: Execute Baseline B5 Reproduction
Run inference and evaluation for B5 across the three canonical seeds:
```bash
# Seed 42
python scripts/reproduce_b5.py --seed 42 --device -1
# Seed 43
python scripts/reproduce_b5.py --seed 43 --device -1
# Seed 44
python scripts/reproduce_b5.py --seed 44 --device -1
```
*Outputs generated*: `reproduction/b5/reproduction_b5_seed{42,43,44}_predictions.jsonl` and evaluation summaries.

### Step 6: Execute Baseline B6 Reproduction
Run inference and evaluation for B6 across the three canonical seeds:
```bash
# Seed 42
python scripts/reproduce_b6.py --seed 42 --device -1
# Seed 43
python scripts/reproduce_b6.py --seed 43 --device -1
# Seed 44
python scripts/reproduce_b6.py --seed 44 --device -1
```
*Outputs generated*: `reproduction/b6/reproduction_b6_seed{42,43,44}_predictions.jsonl` and evaluation summaries.

### Step 7: Evaluate Outputs Using Public CLI
You can evaluate any generated prediction file against the canonical benchmark using:
```bash
python -m benchmark.evaluate \
    --gold data/raw/base_instances.jsonl \
    --predictions reproduction/b6/reproduction_b6_seed42_predictions.jsonl \
    --output reproduction/b6/eval_summary_seed42.json
```

---

## 3. Acceptable Numerical Tolerances

Across different operating systems (Linux vs Windows) and accelerator architectures (CPU vs CUDA), floating-point accumulation in transformer self-attention may introduce minor variations in low-significance digits:

| Metric | Target Value (B6 Mean) | Permissible Tolerance | Notes |
| :--- | :---: | :---: | :--- |
| **Exact F1 ($M_4$)** | $0.6654 \pm 0.0034$ | $\pm 0.005$ | Character-level span exact match |
| **Type F1 ($M_3$)** | $0.7528 \pm 0.0022$ | $\pm 0.005$ | Type-strict match with character overlap |
| **Precision ($M_1$)** | $0.6315 \pm 0.0021$ | $\pm 0.005$ | Type-strict precision |
| **Recall ($M_2$)** | $0.9319 \pm 0.0035$ | $\pm 0.005$ | Type-strict recall |
| **Total Gold ($N_{gold}$)** | 724 | Exactly 724 | Fixed invariant: $TP_{exact} + F_1 + F_2 + F_3 == 724$ |

Any deviation exceeding $\pm 0.01$ indicates environment mismatch (e.g., mismatched tokenizer version or differing SentencePiece binary).

---

## 4. Distinguishing Canonical vs. Reproduction Artifacts

- **Canonical Artifacts** (`predictions/`, `reports/`):
  - Sealed during formal freeze.
  - Checksums recorded in `reports/final/CANONICAL_ARTIFACT_HASHES.json`.
  - Immutable historical ground truth.
- **Reproduction Artifacts** (`reproduction/`):
  - Generated dynamically by external researchers.
  - Labeled explicitly with `"artifact_type": "NON-CANONICAL REPRODUCTION ARTIFACT"`.
  - Intended solely for verification of reproducibility.
