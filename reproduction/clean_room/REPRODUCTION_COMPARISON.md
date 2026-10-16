# REPRODUCTION COMPARISON AUDIT: CANONICAL VS CLEAN-ROOM

**Benchmark**: Indian PII Robustness Benchmark (`v0.18`)  
**Audit Phase**: Clean-Room Independent Reproduction Validation  
**Evaluated Systems**: Baseline B5 (XLM-R Indian Adapted) & Baseline B6 (XLM-R Indian Adapted + Linear CRF)  
**Seeds Evaluated**: 42, 43, 44  
**Date**: 2026-09-09  
**Overall Verdict**: **EXACT MATCH (100% Deterministic Reproducibility)**  

---

## 1. Scope and Classification Schema

Every clean-room reproduced run is compared against its corresponding frozen canonical artifact using the following classification hierarchy:
1. **EXACT MATCH**: Bitwise or numerical equality across predictions, metrics, and partition counters ($\Delta = 0$).
2. **NUMERICALLY EQUIVALENT**: Metric deviations within floating-point tolerance ($\Delta < 1 \times 10^{-4}$).
3. **SUBSTANTIVELY REPRODUCED**: Metric deviations within $\pm 0.01$ F1 without qualitative shift.
4. **DISCREPANT**: Statistically or methodologically significant drift ($\Delta \ge 0.01$ F1).
5. **FAILED**: Non-execution, crash, or invariant breach.

---

## 2. Baseline B5 Per-Seed Comparison

### Seed 42

| Counter / Metric | Canonical Reference | Clean-Room Reproduced | Absolute Delta ($\Delta$) | Status |
|:---|:---:|:---:|:---:|:---:|
| Total Predictions ($N_{pred}$) | 1,638 | 1,638 | 0 | EXACT MATCH |
| Exact True Positives ($TP_{exact}$) | 456 | 456 | 0 | EXACT MATCH |
| Type True Positives ($TP_{type}$) | 706 | 706 | 0 | EXACT MATCH |
| Missed Entities ($F_1$) | 1 | 1 | 0 | EXACT MATCH |
| Boundary Errors ($F_2$) | 250 | 250 | 0 | EXACT MATCH |
| Classification Errors ($F_3$) | 17 | 17 | 0 | EXACT MATCH |
| False Positives ($F_4$) | 915 | 915 | 0 | EXACT MATCH |
| M1 Precision | 0.431013 | 0.431013 | 0.000000 | EXACT MATCH |
| M2 Recall | 0.975138 | 0.975138 | 0.000000 | EXACT MATCH |
| M3 Type F1 | 0.597798 | 0.597798 | 0.000000 | EXACT MATCH |
| M4 Exact F1 | 0.386113 | 0.386113 | 0.000000 | EXACT MATCH |
| M5 Type Accuracy | 0.976487 | 0.976487 | 0.000000 | EXACT MATCH |
| M6 FPR | 0.558608 | 0.558608 | 0.000000 | EXACT MATCH |

- Prediction File Span Discrepancies: **0 / 1,638**

### Seed 43

| Counter / Metric | Canonical Reference | Clean-Room Reproduced | Absolute Delta ($\Delta$) | Status |
|:---|:---:|:---:|:---:|:---:|
| Total Predictions ($N_{pred}$) | 1,623 | 1,623 | 0 | EXACT MATCH |
| Exact True Positives ($TP_{exact}$) | 460 | 460 | 0 | EXACT MATCH |
| Type True Positives ($TP_{type}$) | 705 | 705 | 0 | EXACT MATCH |
| Missed Entities ($F_1$) | 1 | 1 | 0 | EXACT MATCH |
| Boundary Errors ($F_2$) | 245 | 245 | 0 | EXACT MATCH |
| Classification Errors ($F_3$) | 18 | 18 | 0 | EXACT MATCH |
| False Positives ($F_4$) | 900 | 900 | 0 | EXACT MATCH |
| M1 Precision | 0.434381 | 0.434381 | 0.000000 | EXACT MATCH |
| M2 Recall | 0.973757 | 0.973757 | 0.000000 | EXACT MATCH |
| M3 Type F1 | 0.600767 | 0.600767 | 0.000000 | EXACT MATCH |
| M4 Exact F1 | 0.391990 | 0.391990 | 0.000000 | EXACT MATCH |
| M5 Type Accuracy | 0.975104 | 0.975104 | 0.000000 | EXACT MATCH |
| M6 FPR | 0.554529 | 0.554529 | 0.000000 | EXACT MATCH |

- Prediction File Span Discrepancies: **0 / 1,623**

### Seed 44

| Counter / Metric | Canonical Reference | Clean-Room Reproduced | Absolute Delta ($\Delta$) | Status |
|:---|:---:|:---:|:---:|:---:|
| Total Predictions ($N_{pred}$) | 1,646 | 1,646 | 0 | EXACT MATCH |
| Exact True Positives ($TP_{exact}$) | 450 | 450 | 0 | EXACT MATCH |
| Type True Positives ($TP_{type}$) | 705 | 705 | 0 | EXACT MATCH |
| Missed Entities ($F_1$) | 1 | 1 | 0 | EXACT MATCH |
| Boundary Errors ($F_2$) | 255 | 255 | 0 | EXACT MATCH |
| Classification Errors ($F_3$) | 18 | 18 | 0 | EXACT MATCH |
| False Positives ($F_4$) | 923 | 923 | 0 | EXACT MATCH |
| M1 Precision | 0.428311 | 0.428311 | 0.000000 | EXACT MATCH |
| M2 Recall | 0.973757 | 0.973757 | 0.000000 | EXACT MATCH |
| M3 Type F1 | 0.594937 | 0.594937 | 0.000000 | EXACT MATCH |
| M4 Exact F1 | 0.379747 | 0.379747 | 0.000000 | EXACT MATCH |
| M5 Type Accuracy | 0.975104 | 0.975104 | 0.000000 | EXACT MATCH |
| M6 FPR | 0.560753 | 0.560753 | 0.000000 | EXACT MATCH |

- Prediction File Span Discrepancies: **0 / 1,646**

---

## 3. Baseline B6 Per-Seed Comparison

### Seed 42

| Counter / Metric | Canonical Reference | Clean-Room Reproduced | Absolute Delta ($\Delta$) | Status |
|:---|:---:|:---:|:---:|:---:|
| Total Predictions ($N_{pred}$) | 1,073 | 1,073 | 0 | EXACT MATCH |
| Exact True Positives ($TP_{exact}$) | 601 | 601 | 0 | EXACT MATCH |
| Type True Positives ($TP_{type}$) | 677 | 677 | 0 | EXACT MATCH |
| Missed Entities ($F_1$) | 7 | 7 | 0 | EXACT MATCH |
| Boundary Errors ($F_2$) | 76 | 76 | 0 | EXACT MATCH |
| Classification Errors ($F_3$) | 40 | 40 | 0 | EXACT MATCH |
| False Positives ($F_4$) | 356 | 356 | 0 | EXACT MATCH |
| M1 Precision | 0.630941 | 0.630941 | 0.000000 | EXACT MATCH |
| M2 Recall | 0.935083 | 0.935083 | 0.000000 | EXACT MATCH |
| M3 Type F1 | 0.753478 | 0.753478 | 0.000000 | EXACT MATCH |
| M4 Exact F1 | 0.668893 | 0.668893 | 0.000000 | EXACT MATCH |
| M5 Type Accuracy | 0.944212 | 0.944212 | 0.000000 | EXACT MATCH |
| M6 FPR | 0.331780 | 0.331780 | 0.000000 | EXACT MATCH |

- Prediction File Span Discrepancies: **0 / 1,073**

### Seed 43

| Counter / Metric | Canonical Reference | Clean-Room Reproduced | Absolute Delta ($\Delta$) | Status |
|:---|:---:|:---:|:---:|:---:|
| Total Predictions ($N_{pred}$) | 1,067 | 1,067 | 0 | EXACT MATCH |
| Exact True Positives ($TP_{exact}$) | 593 | 593 | 0 | EXACT MATCH |
| Type True Positives ($TP_{type}$) | 672 | 672 | 0 | EXACT MATCH |
| Missed Entities ($F_1$) | 8 | 8 | 0 | EXACT MATCH |
| Boundary Errors ($F_2$) | 79 | 79 | 0 | EXACT MATCH |
| Classification Errors ($F_3$) | 44 | 44 | 0 | EXACT MATCH |
| False Positives ($F_4$) | 351 | 351 | 0 | EXACT MATCH |
| M1 Precision | 0.629803 | 0.629803 | 0.000000 | EXACT MATCH |
| M2 Recall | 0.928177 | 0.928177 | 0.000000 | EXACT MATCH |
| M3 Type F1 | 0.750419 | 0.750419 | 0.000000 | EXACT MATCH |
| M4 Exact F1 | 0.662200 | 0.662200 | 0.000000 | EXACT MATCH |
| M5 Type Accuracy | 0.938547 | 0.938547 | 0.000000 | EXACT MATCH |
| M6 FPR | 0.328960 | 0.328960 | 0.000000 | EXACT MATCH |

- Prediction File Span Discrepancies: **0 / 1,067**

### Seed 44

| Counter / Metric | Canonical Reference | Clean-Room Reproduced | Absolute Delta ($\Delta$) | Status |
|:---|:---:|:---:|:---:|:---:|
| Total Predictions ($N_{pred}$) | 1,065 | 1,065 | 0 | EXACT MATCH |
| Exact True Positives ($TP_{exact}$) | 595 | 595 | 0 | EXACT MATCH |
| Type True Positives ($TP_{type}$) | 675 | 675 | 0 | EXACT MATCH |
| Missed Entities ($F_1$) | 7 | 7 | 0 | EXACT MATCH |
| Boundary Errors ($F_2$) | 80 | 80 | 0 | EXACT MATCH |
| Classification Errors ($F_3$) | 42 | 42 | 0 | EXACT MATCH |
| False Positives ($F_4$) | 348 | 348 | 0 | EXACT MATCH |
| M1 Precision | 0.633803 | 0.633803 | 0.000000 | EXACT MATCH |
| M2 Recall | 0.932320 | 0.932320 | 0.000000 | EXACT MATCH |
| M3 Type F1 | 0.754612 | 0.754612 | 0.000000 | EXACT MATCH |
| M4 Exact F1 | 0.665176 | 0.665176 | 0.000000 | EXACT MATCH |
| M5 Type Accuracy | 0.941423 | 0.941423 | 0.000000 | EXACT MATCH |
| M6 FPR | 0.326761 | 0.326761 | 0.000000 | EXACT MATCH |

- Prediction File Span Discrepancies: **0 / 1,065**

---

## 4. Evaluation Invariant Audit

All six runs satisfied the three strict benchmark structural invariants:
$$\text{Invariant 1: } TP_{exact} + F_1 + F_2 + F_3 = 724 = N_{gold}$$
$$\text{Invariant 2: } TP_{type} = TP_{exact} + F_2$$
$$\text{Invariant 3: } N_{pred} = TP_{type} + F_3 + F_4$$

| System & Seed | Invariant 1 ($N_{gold}=724$) | Invariant 2 ($TP_{type}$) | Invariant 3 ($N_{pred}$) |
|:---|:---:|:---:|:---:|
| B5 Seed 42 | $456 + 1 + 250 + 17 = 724$ | $456 + 250 = 706$ | $706 + 17 + 915 = 1,638$ |
| B5 Seed 43 | $460 + 1 + 245 + 18 = 724$ | $460 + 245 = 705$ | $705 + 18 + 900 = 1,623$ |
| B5 Seed 44 | $450 + 1 + 255 + 18 = 724$ | $450 + 255 = 705$ | $705 + 18 + 923 = 1,646$ |
| B6 Seed 42 | $601 + 7 + 76 + 40 = 724$ | $601 + 76 = 677$ | $677 + 40 + 356 = 1,073$ |
| B6 Seed 43 | $593 + 8 + 79 + 44 = 724$ | $593 + 79 = 672$ | $672 + 44 + 351 = 1,067$ |
| B6 Seed 44 | $595 + 7 + 80 + 42 = 724$ | $595 + 80 = 675$ | $675 + 42 + 348 = 1,065$ |

All six evaluations pass all three invariants with zero anomalies.

---

## 5. Comparative Transition Delta (B5 -> B6)

The clean-room execution perfectly reproduces the observed B5 -> B6 transition dynamics:

| Metric / Dimension | B5 Clean-Room Mean | B6 Clean-Room Mean | Clean-Room Delta ($\Delta$) | Canonical Delta |
|:---|:---:|:---:|:---:|:---:|
| Exact Matches ($TP_{exact}$) | 455.3 | 596.3 | +141.0 (+31.0%) | +141.0 (+31.0%) |
| Boundary Errors ($F_2$) | 250.0 | 78.3 | -171.7 (-68.7%) | -171.7 (-68.7%) |
| False Positives ($F_4$) | 912.7 | 351.7 | -561.0 (-61.5%) | -561.0 (-61.5%) |
| Total Predictions ($N_{pred}$) | 1635.7 | 1068.3 | -567.4 (-34.7%) | -567.4 (-34.7%) |
| M1 Precision | 0.4312 | 0.6315 | +0.2003 | +0.2003 |
| M2 Recall | 0.9742 | 0.9319 | -0.0423 | -0.0423 |
| M3 Type F1 | 0.5978 | 0.7528 | +0.1550 | +0.1550 |
| M4 Exact F1 | 0.3860 | 0.6654 | +0.2794 | +0.2794 |
| M6 FPR | 0.5580 | 0.3292 | -0.2288 | -0.2288 |

---

## 6. Audit Conclusion

The clean-room reproduction yields **100% exact numerical and prediction-level match** against the canonical B5 and B6 artifacts. No divergence in predictions, counters, invariants, or aggregated metrics occurred.
