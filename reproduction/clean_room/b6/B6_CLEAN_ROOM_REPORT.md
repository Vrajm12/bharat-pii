# CLEAN-ROOM REPRODUCTION REPORT: BASELINE B6 (Indian-Adapted XLM-RoBERTa + Linear-Chain CRF)

**Artifact Type**: Independent Clean-Room Reproduction Audit  
**System Evaluated**: Baseline B6 (`xlm-roberta-base` adapted on Indian synthetic PII with Linear-Chain CRF decoding layer)  
**Evaluation Scope**: Canonical 964-record Indian PII Robustness Benchmark (`v0.18`)  
**Seeds Evaluated**: 42, 43, 44  
**Date**: 2026-09-09  
**Execution Environment**: Python 3.10.6, PyTorch 2.13.0+cpu, Transformers 5.16.1, Windows 11 AMD64  
**Execution Device**: CPU (`device = -1`)  
**Reproducibility Status**: **EXACT REPRODUCTION CONFIRMED (100% Match)**  

---

## 1. Executive Summary

Baseline B6 was independently executed across all three canonical seeds (42, 43, 44) using the public reproduction entrypoint `scripts/reproduce_b6.py`. Predictions were generated directly from the authoritative checkpoint artifacts (`checkpoints/b6/b6_transformer_crf_seed{42,43,44}`) without modifying or accessing canonical prediction files.

All outputs were written strictly to isolated subdirectories under `reproduction/clean_room/b6/`.

### Key Validation Outcomes:
1. **Prediction-Level Match**: Exactly 0 prediction mismatches across all 3,205 cumulative predictions (1,073 for seed 42, 1,067 for seed 43, 1,065 for seed 44). Every span boundary, entity type, and confidence score is identical to canonical predictions.
2. **Metric Reconciliation Match**: Metric outputs across precision, recall, Type F1, Exact F1, and error partitions ($F_1, F_2, F_3, F_4$) matched canonical evaluation reports down to `< 1e-9` (0.00e+00 difference).
3. **Partition Invariants**: The structural evaluation invariants held identically across all three reproduced runs:
   - $TP_{exact} + F_1 + F_2 + F_3 = 724 = N_{gold}$
   - $TP_{type} = TP_{exact} + F_2$
   - $N_{pred} = TP_{type} + F_3 + F_4$

---

## 2. Execution Log & Environment State

| Parameter | Specification / Value |
|:---|:---|
| Checkpoint Source | `checkpoints/b6/b6_transformer_crf_seed{42,43,44}/` |
| Benchmark Dataset | Canonical 964 records (`data/raw/base_instances.jsonl`, `data/generated/*.jsonl`) |
| Entrypoint Script | `scripts/reproduce_b6.py` |
| Device | CPU (`device = -1`) |
| Seed 42 Predictions Artifact | `reproduction/clean_room/b6/seed42/reproduction_b6_seed42_predictions.jsonl` |
| Seed 42 Evaluation Artifact | `reproduction/clean_room/b6/seed42/reproduction_b6_seed42_evaluation.json` |
| Seed 43 Predictions Artifact | `reproduction/clean_room/b6/seed43/reproduction_b6_seed43_predictions.jsonl` |
| Seed 43 Evaluation Artifact | `reproduction/clean_room/b6/seed43/reproduction_b6_seed43_evaluation.json` |
| Seed 44 Predictions Artifact | `reproduction/clean_room/b6/seed44/reproduction_b6_seed44_predictions.jsonl` |
| Seed 44 Evaluation Artifact | `reproduction/clean_room/b6/seed44/reproduction_b6_seed44_evaluation.json` |

---

## 3. Detailed Results & Canonical Comparison

### Seed 42

| Metric / Counter | Canonical Reference | Clean-Room Reproduced | Discrepancy | Classification |
|:---|:---:|:---:|:---:|:---:|
| $N_{pred}$ | 1,073 | 1,073 | 0 | EXACT MATCH |
| $TP_{exact}$ | 601 | 601 | 0 | EXACT MATCH |
| $F_1$ (Missed) | 7 | 7 | 0 | EXACT MATCH |
| $F_2$ (Wrong Span) | 76 | 76 | 0 | EXACT MATCH |
| $F_3$ (Wrong Type) | 40 | 40 | 0 | EXACT MATCH |
| $F_4$ (False Positives) | 356 | 356 | 0 | EXACT MATCH |
| $TP_{type}$ | 677 | 677 | 0 | EXACT MATCH |
| M1 Precision | 0.630941 | 0.630941 | 0.000000 | EXACT MATCH |
| M2 Recall | 0.935083 | 0.935083 | 0.000000 | EXACT MATCH |
| M3 Type F1 | 0.753478 | 0.753478 | 0.000000 | EXACT MATCH |
| M4 Exact F1 | 0.668893 | 0.668893 | 0.000000 | EXACT MATCH |
| M5 Type Accuracy | 0.944212 | 0.944212 | 0.000000 | EXACT MATCH |
| M6 FPR | 0.331780 | 0.331780 | 0.000000 | EXACT MATCH |

- **Invariant Check 1**: $601 + 7 + 76 + 40 = 724 = N_{gold}$ (VERIFIED)
- **Invariant Check 2**: $TP_{type} = 601 + 76 = 677$ (VERIFIED)
- **Invariant Check 3**: $N_{pred} = 677 + 40 + 356 = 1,073$ (VERIFIED)

---

### Seed 43

| Metric / Counter | Canonical Reference | Clean-Room Reproduced | Discrepancy | Classification |
|:---|:---:|:---:|:---:|:---:|
| $N_{pred}$ | 1,067 | 1,067 | 0 | EXACT MATCH |
| $TP_{exact}$ | 593 | 593 | 0 | EXACT MATCH |
| $F_1$ (Missed) | 8 | 8 | 0 | EXACT MATCH |
| $F_2$ (Wrong Span) | 79 | 79 | 0 | EXACT MATCH |
| $F_3$ (Wrong Type) | 44 | 44 | 0 | EXACT MATCH |
| $F_4$ (False Positives) | 351 | 351 | 0 | EXACT MATCH |
| $TP_{type}$ | 672 | 672 | 0 | EXACT MATCH |
| M1 Precision | 0.629803 | 0.629803 | 0.000000 | EXACT MATCH |
| M2 Recall | 0.928177 | 0.928177 | 0.000000 | EXACT MATCH |
| M3 Type F1 | 0.750419 | 0.750419 | 0.000000 | EXACT MATCH |
| M4 Exact F1 | 0.662200 | 0.662200 | 0.000000 | EXACT MATCH |
| M5 Type Accuracy | 0.938547 | 0.938547 | 0.000000 | EXACT MATCH |
| M6 FPR | 0.328960 | 0.328960 | 0.000000 | EXACT MATCH |

- **Invariant Check 1**: $593 + 8 + 79 + 44 = 724 = N_{gold}$ (VERIFIED)
- **Invariant Check 2**: $TP_{type} = 593 + 79 = 672$ (VERIFIED)
- **Invariant Check 3**: $N_{pred} = 672 + 44 + 351 = 1,067$ (VERIFIED)

---

### Seed 44

| Metric / Counter | Canonical Reference | Clean-Room Reproduced | Discrepancy | Classification |
|:---|:---:|:---:|:---:|:---:|
| $N_{pred}$ | 1,065 | 1,065 | 0 | EXACT MATCH |
| $TP_{exact}$ | 595 | 595 | 0 | EXACT MATCH |
| $F_1$ (Missed) | 7 | 7 | 0 | EXACT MATCH |
| $F_2$ (Wrong Span) | 80 | 80 | 0 | EXACT MATCH |
| $F_3$ (Wrong Type) | 42 | 42 | 0 | EXACT MATCH |
| $F_4$ (False Positives) | 348 | 348 | 0 | EXACT MATCH |
| $TP_{type}$ | 675 | 675 | 0 | EXACT MATCH |
| M1 Precision | 0.633803 | 0.633803 | 0.000000 | EXACT MATCH |
| M2 Recall | 0.932320 | 0.932320 | 0.000000 | EXACT MATCH |
| M3 Type F1 | 0.754612 | 0.754612 | 0.000000 | EXACT MATCH |
| M4 Exact F1 | 0.665176 | 0.665176 | 0.000000 | EXACT MATCH |
| M5 Type Accuracy | 0.941423 | 0.941423 | 0.000000 | EXACT MATCH |
| M6 FPR | 0.326761 | 0.326761 | 0.000000 | EXACT MATCH |

- **Invariant Check 1**: $595 + 7 + 80 + 42 = 724 = N_{gold}$ (VERIFIED)
- **Invariant Check 2**: $TP_{type} = 595 + 80 = 675$ (VERIFIED)
- **Invariant Check 3**: $N_{pred} = 675 + 42 + 348 = 1,065$ (VERIFIED)

---

## 4. Aggregate Summary Across Seeds (Mean ± Sample SD, ddof=1)

| Metric | Clean-Room Mean ± SD ($s$, $N=3$) | Canonical Reference |
|:---|:---:|:---:|
| M1 Precision | 0.6315 ± 0.0021 | 0.6315 ± 0.0021 |
| M2 Recall | 0.9319 ± 0.0035 | 0.9319 ± 0.0035 |
| M3 Type F1 | 0.7528 ± 0.0022 | 0.7528 ± 0.0022 |
| M4 Exact F1 | 0.6654 ± 0.0034 | 0.6654 ± 0.0034 |
| M5 Type Accuracy | 0.9414 ± 0.0028 | 0.9414 ± 0.0028 |
| M6 FPR | 0.3292 ± 0.0025 | 0.3292 ± 0.0025 |
| False Positives ($F_4$) | 351.7 ± 4.0 | 351.7 ± 4.0 |
| Wrong Span ($F_2$) | 78.3 ± 2.1 | 78.3 ± 2.1 |
| Exact Matches ($TP_{exact}$) | 596.3 ± 4.2 | 596.3 ± 4.2 |

---

## 5. Scientific Limitations & Boundary Observations

The clean-room execution of B6 re-confirms the findings established during the scientific validation phase:
1. **Structural Span Decoding**: Adding a linear-chain CRF layer markedly reduces boundary fragmentation ($F_2$ dropped from 250.0 to 78.3) and suppresses sub-span over-generation ($F_4$ dropped from 912.7 to 351.7), raising Exact F1 from 0.3860 to 0.6654.
2. **Persistent Limitations**:
   - The CRF layer does **not** possess semantic reasoning; it enforces sequence transition validity.
   - Systematic degradation remains under whitespace perturbations (adversarial A1 whitespace injection breaks token alignment).
   - Hard-negative decoy identifiers (such as synthetic Aadhaar/PAN formats) remain prone to residual false-positive activations (351.7 remaining false positives), confirming that boundary constraints do not eliminate structural semantic confusion.

---

## 6. Conclusion

Baseline B6 execution via `scripts/reproduce_b6.py` reproduces the canonical benchmark results with 100% bitwise and numerical fidelity across seeds 42, 43, and 44.
