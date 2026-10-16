# CLEAN-ROOM REPRODUCTION REPORT: BASELINE B5 (Indian-Adapted XLM-RoBERTa)

**Artifact Type**: Independent Clean-Room Reproduction Audit  
**System Evaluated**: Baseline B5 (`xlm-roberta-base` adapted on Indian synthetic PII + hard negatives)  
**Evaluation Scope**: Canonical 964-record Indian PII Robustness Benchmark (`v0.18`)  
**Seeds Evaluated**: 42, 43, 44  
**Date**: 2026-09-09  
**Execution Environment**: Python 3.10.6, PyTorch 2.13.0+cpu, Transformers 5.16.1, Windows 11 AMD64  
**Execution Device**: CPU (`device = -1`)  
**Reproducibility Status**: **EXACT REPRODUCTION CONFIRMED (100% Match)**  

---

## 1. Executive Summary

Baseline B5 was executed independently across all three canonical seeds (42, 43, 44) using the public reproduction entrypoint `scripts/reproduce_b5.py`. Predictions were generated directly from the authoritative checkpoint artifacts without modifying or accessing the canonical prediction records.

All outputs were written strictly to isolated subdirectories under `reproduction/clean_room/b5/`.

### Key Validation Outcomes:
1. **Prediction-Level Match**: Exactly 0 prediction mismatches across all 4,907 cumulative predictions (1,638 for seed 42, 1,623 for seed 43, 1,646 for seed 44). Every span boundary, entity type, and confidence score is numerically identical to canonical predictions.
2. **Metric Reconciliation Match**: Metric outputs across precision, recall, Type F1, Exact F1, and error decompositions ($F_1, F_2, F_3, F_4$) matched canonical evaluation reports down to `< 1e-9`.
3. **Partition Invariants**: The structural evaluation invariants held identically across all three reproduced runs:
   - $TP_{exact} + F_1 + F_2 + F_3 = 724 = N_{gold}$
   - $TP_{type} = TP_{exact} + F_2$
   - $N_{pred} = TP_{type} + F_3 + F_4$

---

## 2. Execution Log & Environment State

| Parameter | Specification / Value |
|:---|:---|
| Checkpoint Source | `checkpoints/b5_transformer_adapted_seed{42,43,44}/` |
| Benchmark Dataset | Canonical 964 records (`data/raw/base_instances.jsonl`, `data/generated/*.jsonl`) |
| Entrypoint Script | `scripts/reproduce_b5.py` |
| Device | CPU (`device = -1`) |
| Seed 42 Predictions Artifact | `reproduction/clean_room/b5/seed42/reproduction_b5_seed42_predictions.jsonl` |
| Seed 42 Evaluation Artifact | `reproduction/clean_room/b5/seed42/reproduction_b5_seed42_evaluation.json` |
| Seed 43 Predictions Artifact | `reproduction/clean_room/b5/seed43/reproduction_b5_seed43_predictions.jsonl` |
| Seed 43 Evaluation Artifact | `reproduction/clean_room/b5/seed43/reproduction_b5_seed43_evaluation.json` |
| Seed 44 Predictions Artifact | `reproduction/clean_room/b5/seed44/reproduction_b5_seed44_predictions.jsonl` |
| Seed 44 Evaluation Artifact | `reproduction/clean_room/b5/seed44/reproduction_b5_seed44_evaluation.json` |

---

## 3. Detailed Results & Canonical Comparison

### Seed 42

| Metric / Counter | Canonical Reference | Clean-Room Reproduced | Discrepancy | Classification |
|:---|:---:|:---:|:---:|:---:|
| $N_{pred}$ | 1,638 | 1,638 | 0 | EXACT MATCH |
| $TP_{exact}$ | 456 | 456 | 0 | EXACT MATCH |
| $F_1$ (Missed) | 1 | 1 | 0 | EXACT MATCH |
| $F_2$ (Wrong Span) | 250 | 250 | 0 | EXACT MATCH |
| $F_3$ (Wrong Type) | 17 | 17 | 0 | EXACT MATCH |
| $F_4$ (False Positives) | 915 | 915 | 0 | EXACT MATCH |
| $TP_{type}$ | 706 | 706 | 0 | EXACT MATCH |
| M1 Precision | 0.431013 | 0.431013 | 0.000000 | EXACT MATCH |
| M2 Recall | 0.975138 | 0.975138 | 0.000000 | EXACT MATCH |
| M3 Type F1 | 0.597798 | 0.597798 | 0.000000 | EXACT MATCH |
| M4 Exact F1 | 0.386113 | 0.386113 | 0.000000 | EXACT MATCH |
| M5 Type Accuracy | 0.976487 | 0.976487 | 0.000000 | EXACT MATCH |
| M6 FPR | 0.558608 | 0.558608 | 0.000000 | EXACT MATCH |

- **Invariant Check 1**: $456 + 1 + 250 + 17 = 724 = N_{gold}$ (VERIFIED)
- **Invariant Check 2**: $TP_{type} = 456 + 250 = 706$ (VERIFIED)
- **Invariant Check 3**: $N_{pred} = 706 + 17 + 915 = 1,638$ (VERIFIED)

---

### Seed 43

| Metric / Counter | Canonical Reference | Clean-Room Reproduced | Discrepancy | Classification |
|:---|:---:|:---:|:---:|:---:|
| $N_{pred}$ | 1,623 | 1,623 | 0 | EXACT MATCH |
| $TP_{exact}$ | 460 | 460 | 0 | EXACT MATCH |
| $F_1$ (Missed) | 1 | 1 | 0 | EXACT MATCH |
| $F_2$ (Wrong Span) | 245 | 245 | 0 | EXACT MATCH |
| $F_3$ (Wrong Type) | 18 | 18 | 0 | EXACT MATCH |
| $F_4$ (False Positives) | 900 | 900 | 0 | EXACT MATCH |
| $TP_{type}$ | 705 | 705 | 0 | EXACT MATCH |
| M1 Precision | 0.434381 | 0.434381 | 0.000000 | EXACT MATCH |
| M2 Recall | 0.973757 | 0.973757 | 0.000000 | EXACT MATCH |
| M3 Type F1 | 0.600767 | 0.600767 | 0.000000 | EXACT MATCH |
| M4 Exact F1 | 0.391990 | 0.391990 | 0.000000 | EXACT MATCH |
| M5 Type Accuracy | 0.975104 | 0.975104 | 0.000000 | EXACT MATCH |
| M6 FPR | 0.554529 | 0.554529 | 0.000000 | EXACT MATCH |

- **Invariant Check 1**: $460 + 1 + 245 + 18 = 724 = N_{gold}$ (VERIFIED)
- **Invariant Check 2**: $TP_{type} = 460 + 245 = 705$ (VERIFIED)
- **Invariant Check 3**: $N_{pred} = 705 + 18 + 900 = 1,623$ (VERIFIED)

---

### Seed 44

| Metric / Counter | Canonical Reference | Clean-Room Reproduced | Discrepancy | Classification |
|:---|:---:|:---:|:---:|:---:|
| $N_{pred}$ | 1,646 | 1,646 | 0 | EXACT MATCH |
| $TP_{exact}$ | 450 | 450 | 0 | EXACT MATCH |
| $F_1$ (Missed) | 1 | 1 | 0 | EXACT MATCH |
| $F_2$ (Wrong Span) | 255 | 255 | 0 | EXACT MATCH |
| $F_3$ (Wrong Type) | 18 | 18 | 0 | EXACT MATCH |
| $F_4$ (False Positives) | 923 | 923 | 0 | EXACT MATCH |
| $TP_{type}$ | 705 | 705 | 0 | EXACT MATCH |
| M1 Precision | 0.428311 | 0.428311 | 0.000000 | EXACT MATCH |
| M2 Recall | 0.973757 | 0.973757 | 0.000000 | EXACT MATCH |
| M3 Type F1 | 0.594937 | 0.594937 | 0.000000 | EXACT MATCH |
| M4 Exact F1 | 0.379747 | 0.379747 | 0.000000 | EXACT MATCH |
| M5 Type Accuracy | 0.975104 | 0.975104 | 0.000000 | EXACT MATCH |
| M6 FPR | 0.560753 | 0.560753 | 0.000000 | EXACT MATCH |

- **Invariant Check 1**: $450 + 1 + 255 + 18 = 724 = N_{gold}$ (VERIFIED)
- **Invariant Check 2**: $TP_{type} = 450 + 255 = 705$ (VERIFIED)
- **Invariant Check 3**: $N_{pred} = 705 + 18 + 923 = 1,646$ (VERIFIED)

---

## 4. Aggregate Summary Across Seeds (Mean ± Sample SD, ddof=1)

| Metric | Clean-Room Mean ± SD ($s$, $N=3$) | Canonical Reference |
|:---|:---:|:---:|
| M1 Precision | 0.4312 ± 0.0030 | 0.4312 ± 0.0030 |
| M2 Recall | 0.9742 ± 0.0008 | 0.9742 ± 0.0008 |
| M3 Type F1 | 0.5978 ± 0.0029 | 0.5978 ± 0.0029 |
| M4 Exact F1 | 0.3859 ± 0.0061 | 0.3859 ± 0.0061 |
| M5 Type Accuracy | 0.9756 ± 0.0008 | 0.9756 ± 0.0008 |
| M6 FPR | 0.5580 ± 0.0032 | 0.5580 ± 0.0032 |
| False Positives ($F_4$) | 912.7 ± 11.7 | 912.7 ± 11.7 |
| Wrong Span ($F_2$) | 250.0 ± 5.0 | 250.0 ± 5.0 |
| Exact Matches ($TP_{exact}$) | 455.3 ± 5.0 | 455.3 ± 5.0 |

---

## 5. Conclusion

Baseline B5 execution via `scripts/reproduce_b5.py` reproduces the canonical benchmark results with 100% bitwise and metric fidelity. No deviations, drift, or numerical instability were observed across seeds 42, 43, or 44.
