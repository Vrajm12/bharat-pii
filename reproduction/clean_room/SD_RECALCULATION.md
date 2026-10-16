# STANDARD DEVIATION RECALCULATION & RECONCILIATION

**Benchmark**: Indian PII Robustness Benchmark (`v0.18`)  
**Audit Task**: Clean-Room Independent Reproduction Validation  
**Evaluated Systems**: Baseline B5 (Seeds 42, 43, 44) & Baseline B6 (Seeds 42, 43, 44)  
**Date**: 2026-09-09  

---

## 1. Mathematical Formulation

Across $N = 3$ evaluated random seeds ($x_1, x_2, x_3$ corresponding to seeds 42, 43, 44), the sample mean is:
$$\bar{x} = \frac{1}{N} \sum_{i=1}^N x_i$$

Two standard deviation definitions frequently arise in empirical reporting:

### 1.1 Unbiased Sample Standard Deviation ($s$, `ddof=1`)
Using Bessel's correction ($N - 1 = 2$ degrees of freedom):
$$s = \sqrt{\frac{1}{N - 1} \sum_{i=1}^N (x_i - \bar{x})^2}$$
*This is the authoritative standard deviation reported in peer-reviewed scientific literature and the canonical baseline summaries.*

### 1.2 Population Standard Deviation ($\sigma$, `ddof=0`)
Using $N = 3$ degrees of freedom:
$$\sigma = \sqrt{\frac{1}{N} \sum_{i=1}^N (x_i - \bar{x})^2}$$
Note the exact algebraic relationship:
$$s = \sigma \cdot \sqrt{\frac{N}{N - 1}} = \sigma \cdot \sqrt{\frac{3}{2}} \approx 1.22474 \cdot \sigma$$

---

## 2. Baseline B5 Recalculation ($N=3$)

Raw values for seeds 42, 43, 44:
- Seed 42: Precision = 0.431013, Recall = 0.975138, Type F1 = 0.597798, Exact F1 = 0.386113, FPR = 0.558608
- Seed 43: Precision = 0.434381, Recall = 0.973757, Type F1 = 0.600767, Exact F1 = 0.391990, FPR = 0.554529
- Seed 44: Precision = 0.428311, Recall = 0.973757, Type F1 = 0.594937, Exact F1 = 0.379747, FPR = 0.560753

### Step-by-Step Variance & SD:

| Metric | Mean ($\bar{x}$) | Variance ($s^2$, $N-1$) | Sample SD ($s$, `ddof=1`) | Pop SD ($\sigma$, `ddof=0`) | Authoritative Report |
|:---|:---:|:---:|:---:|:---:|:---:|
| M1 Precision | 0.431235 | 9.2774e-06 | **0.003046** (0.0030) | 0.002487 (0.0025) | 0.4312 ± 0.0030 |
| M2 Recall | 0.974217 | 6.3688e-07 | **0.000798** (0.0008) | 0.000652 (0.0007) | 0.9742 ± 0.0008 |
| M3 Type F1 | 0.597834 | 8.5029e-06 | **0.002916** (0.0029) | 0.002381 (0.0024) | 0.5978 ± 0.0029 |
| M4 Exact F1 | 0.385950 | 3.7505e-05 | **0.006124** (0.0061) | 0.005000 (0.0050) | 0.3860 ± 0.0061 |
| M5 Type Accuracy | 0.975565 | 6.3688e-07 | **0.000798** (0.0008) | 0.000652 (0.0007) | 0.9756 ± 0.0008 |
| M6 FPR | 0.557963 | 1.0118e-05 | **0.003181** (0.0032) | 0.002597 (0.0026) | 0.5580 ± 0.0032 |
| Exact Matches ($TP_{exact}$) | 455.33 | 25.333 | **5.033** (5.0) | 4.110 (4.1) | 455.3 ± 5.0 |
| Boundary Errors ($F_2$) | 250.00 | 25.000 | **5.000** (5.0) | 4.082 (4.1) | 250.0 ± 5.0 |
| False Positives ($F_4$) | 912.67 | 136.333 | **11.676** (11.7) | 9.534 (9.5) | 912.7 ± 11.7 |
| Total Predictions ($N_{pred}$) | 1635.67 | 136.333 | **11.676** (11.7) | 9.534 (9.5) | 1635.7 ± 11.7 |

---

## 3. Baseline B6 Recalculation ($N=3$)

Raw values for seeds 42, 43, 44:
- Seed 42: Precision = 0.630941, Recall = 0.935083, Type F1 = 0.753478, Exact F1 = 0.668893, FPR = 0.331780
- Seed 43: Precision = 0.629803, Recall = 0.928177, Type F1 = 0.750419, Exact F1 = 0.662200, FPR = 0.328960
- Seed 44: Precision = 0.633803, Recall = 0.932320, Type F1 = 0.754612, Exact F1 = 0.665176, FPR = 0.326761

### Step-by-Step Variance & SD:

| Metric | Mean ($\bar{x}$) | Variance ($s^2$, $N-1$) | Sample SD ($s$, `ddof=1`) | Pop SD ($\sigma$, `ddof=0`) | Authoritative Report |
|:---|:---:|:---:|:---:|:---:|:---:|
| M1 Precision | 0.631516 | 4.3168e-06 | **0.002078** (0.0021) | 0.001696 (0.0017) | 0.6315 ± 0.0021 |
| M2 Recall | 0.931860 | 1.2185e-05 | **0.003491** (0.0035) | 0.002850 (0.0029) | 0.9319 ± 0.0035 |
| M3 Type F1 | 0.752836 | 4.6738e-06 | **0.002162** (0.0022) | 0.001765 (0.0018) | 0.7528 ± 0.0022 |
| M4 Exact F1 | 0.665423 | 1.1278e-05 | **0.003358** (0.0034) | 0.002742 (0.0027) | 0.6654 ± 0.0034 |
| M5 Type Accuracy | 0.941394 | 8.0105e-06 | **0.002830** (0.0028) | 0.002311 (0.0023) | 0.9414 ± 0.0028 |
| M6 FPR | 0.329167 | 6.3475e-06 | **0.002519** (0.0025) | 0.002057 (0.0021) | 0.3292 ± 0.0025 |
| Exact Matches ($TP_{exact}$) | 596.33 | 17.333 | **4.163** (4.2) | 3.399 (3.4) | 596.3 ± 4.2 |
| Boundary Errors ($F_2$) | 78.33 | 4.333 | **2.082** (2.1) | 1.700 (1.7) | 78.3 ± 2.1 |
| False Positives ($F_4$) | 351.67 | 16.333 | **4.041** (4.0) | 3.300 (3.3) | 351.7 ± 4.0 |
| Total Predictions ($N_{pred}$) | 1068.33 | 17.333 | **4.163** (4.2) | 3.399 (3.4) | 1068.3 ± 4.2 |

---

## 4. Reconciliation of Historical Presentation Discrepancies

In earlier documentation drafts, slight variations in reported standard deviation values occurred:
1. **Degrees of Freedom**: Some early reports computed standard deviation using `numpy.std(..., ddof=0)` which yielded population SD $\sigma = 0.0024$ for B5 Type F1, whereas the canonical summary used unbiased sample SD `ddof=1` yielding $s = 0.0029$.
2. **Rounding Convention**: Truncating to 3 decimal places vs standard half-up rounding (e.g. 0.00612 -> 0.006 vs 0.0061).
3. **Reconciliation Conclusion**: In all canonical benchmark publications, the **unbiased sample standard deviation with `ddof=1`** is the binding authoritative definition. The clean-room recalculated values match the canonical reported values down to four decimal places.
