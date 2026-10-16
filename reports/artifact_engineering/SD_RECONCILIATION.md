# Standard Deviation (SD) Calculation Reconciliation Report
**Document Identifier**: `REPORTS-ARTIFACT-ENG-SD-RECONCILIATION-V1.0`  
**Phase**: Artifact Engineering V1 (Post-Scientific-Freeze)  
**Topic**: Multi-Seed Variance Accounting for Baselines B5 and B6  
**Status**: APPROVED & CANONICALLY HARMONIZED  
**Date**: September 9, 2026  

---

## 1. Objective of Reconciliation

During benchmark development across B5 and B6, minor numerical discrepancies were noted in the reported Standard Deviation (SD) values between different analytical reports. For example:
- B5 $TP_{exact}$: Reported in some summaries as $455.33 \pm 5.03$ and in others as $455.33 \pm 4.11$.
- B5 $F_2$ (Boundary): Reported in some summaries as $250.00 \pm 5.00$ and in others as $250.00 \pm 4.08$.
- B5 $F_4$ (False Positives): Reported in some summaries as $912.67 \pm 11.68$ and in others as $912.67 \pm 9.53$.
- B6 $TP_{exact}$: Reported in some summaries as $596.33 \pm 4.51$ (or $\pm 4.16$) and in others as $596.33 \pm 3.68$.
- B6 $F_2$ (Boundary): Reported as $78.33 \pm 2.08$ vs $78.33 \pm 1.70$.

This document investigates the mathematical source of these discrepancies, reconciles the conventions, and establishes the authoritative presentation standard for public documentation without altering underlying experimental data.

---

## 2. Mathematical Root Cause Analysis

Across three seeds ($N=3$: seeds $42, 43, 44$), standard deviation can be computed under two distinct statistical conventions:

1. **Sample Standard Deviation ($s$, `ddof=1`)**:
   $$s = \sqrt{\frac{1}{N - 1} \sum_{i=1}^{N} (x_i - \bar{x})^2} = \sqrt{\frac{1}{2} \sum_{i=1}^{3} (x_i - \bar{x})^2}$$
   This is the standard unbiased estimator for sample variance (`np.std(x, ddof=1)` or Python `statistics.stdev`).

2. **Population Standard Deviation ($\sigma$, `ddof=0`)**:
   $$\sigma = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (x_i - \bar{x})^2} = \sqrt{\frac{1}{3} \sum_{i=1}^{3} (x_i - \bar{x})^2}$$
   This computes the variance over the exact 3-seed evaluation cohort (`np.std(x, ddof=0)` or `math.sqrt(var)`).

Because $\frac{s}{\sigma} = \sqrt{\frac{N}{N-1}} = \sqrt{\frac{3}{2}} \approx 1.2247$, sample standard deviation is systematically **$22.47\%$ larger** than population standard deviation.

---

## 3. Seed-Level Empirical Verification

### 3.1 Baseline B5 (Seeds 42, 43, 44)
Raw counts from canonical reports:
- $TP_{exact}$: $[456, 460, 450]$, Mean $= 455.3333$
  - Sample SD (`ddof=1`): $\mathbf{5.0332}$ (rounds to $\mathbf{5.03}$ or $\mathbf{\pm 5.0}$)
  - Population SD (`ddof=0`): $\mathbf{4.1096}$ (rounds to $\mathbf{4.11}$ or $\mathbf{\pm 4.1}$)
- $F_2$ Wrong Span: $[250, 245, 255]$, Mean $= 250.0000$
  - Sample SD (`ddof=1`): $\mathbf{5.0000}$ (rounds to $\mathbf{\pm 5.0}$)
  - Population SD (`ddof=0`): $\mathbf{4.0825}$ (rounds to $\mathbf{\pm 4.1}$)
- $F_4$ False Positives: $[915, 900, 923]$, Mean $= 912.6667$
  - Sample SD (`ddof=1`): $\mathbf{11.6762}$ (rounds to $\mathbf{\pm 11.7}$)
  - Population SD (`ddof=0`): $\mathbf{9.5336}$ (rounds to $\mathbf{\pm 9.5}$)

### 3.2 Baseline B6 (Seeds 42, 43, 44)
Raw counts from canonical reports:
- $TP_{exact}$: $[601, 592, 596]$, Mean $= 596.3333$
  - Sample SD (`ddof=1`): $\mathbf{4.5092}$ (rounds to $\mathbf{4.51}$)
  - Population SD (`ddof=0`): $\mathbf{3.6818}$ (rounds to $\mathbf{3.68}$)
  *(Note: An earlier preliminary analysis script reported $4.16$ due to macro-entity weighting across partition splits; the exact unweighted seed vector $[601, 592, 596]$ yields $4.51$ sample SD and $3.68$ population SD).*
- $F_2$ Wrong Span: $[76, 80, 79]$, Mean $= 78.3333$
  - Sample SD (`ddof=1`): $\mathbf{2.0817}$ (rounds to $\mathbf{2.08}$)
  - Population SD (`ddof=0`): $\mathbf{1.6997}$ (rounds to $\mathbf{1.70}$)
- $F_4$ False Positives: $[356, 352, 347]$, Mean $= 351.6667$
  - Sample SD (`ddof=1`): $\mathbf{4.5092}$ (rounds to $\mathbf{4.51}$)
  - Population SD (`ddof=0`): $\mathbf{3.6818}$ (rounds to $\mathbf{3.68}$)

### 3.3 Rate Metrics ($M_1$–$M_6$) in Canonical JSON Reports
In the canonical evaluation reports:
- `evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.json` (B5):
  - $M_1$ Precision SD: `0.0030409244983516607` $\to$ **Sample SD (`ddof=1`)**
  - $M_2$ Recall SD: `0.0007974451231900728` $\to$ **Sample SD (`ddof=1`)**
  - $M_3$ Type F1 SD: `0.0029152765309522124` $\to$ **Sample SD (`ddof=1`)**
  - $M_4$ Exact F1 SD: `0.006123105538405883` $\to$ **Sample SD (`ddof=1`)**
- `reports/experiments/b6/b6_error_summary.json` (B6):
  - $M_1$ Precision SD: `0.0020607713961946074` $\to$ **Sample SD (`ddof=1`)**
  - $M_2$ Recall SD: `0.003475982705004981` $\to$ **Sample SD (`ddof=1`)**
  - $M_3$ Type F1 SD: `0.0021688347177433206` $\to$ **Sample SD (`ddof=1`)**
  - $M_4$ Exact F1 SD: `0.0033531728173936083` $\to$ **Sample SD (`ddof=1`)**

---

## 4. Authoritative Harmonization & Presentation Standard

To eliminate all ambiguity in published documentation, public tables, and research papers:

1. **Authoritative Standard**: All multi-seed metrics ($M_1$–$M_6$) and error counts ($TP_{exact}, F_1, F_2, F_3, F_4$) in the canonical JSON reports are formalized using **Sample Standard Deviation ($s$, `ddof=1`, denominator $N-1$)**, as is standard in empirical machine learning benchmarks reporting small seed cohorts ($N=3$).
2. **Explicit Documentation**: Wherever summary tables report SDs, the table caption or footer must explicitly state:  
   *`Multi-seed values are reported as Mean ± Sample Standard Deviation (ddof=1 across seeds 42, 43, 44).`*
3. **No Retrospective Modification of Data**: The underlying seed outputs and JSON evaluation files remain 100% frozen. This reconciliation strictly governs presentation text and documentation.
