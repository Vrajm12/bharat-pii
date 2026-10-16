# Indian PII Robustness Benchmark — Formal Scientific Freeze Declaration
**Declaration Identifier**: `REPORTS-FINAL-FREEZE-DECLARATION-V1.0`  
**Benchmark Version**: `0.18`  
**Evaluation Scope**: Baselines B1–B6, Scientific Validations SV-01, SV-02, SV-03  
**Freeze Status**: **SCIENTIFIC FREEZE — APPROVED**  
**Date**: September 9, 2026  
**Authority**: Benchmark Lead & Scientific Governance Committee  

---

## 1. Official Declaration of Scientific Freeze

The Indian PII Robustness Benchmark has completed all designated phases of empirical development, systematic error analysis, controlled ablation, and architectural remediation (Baselines B1 through B6).

**Effective immediately, the benchmark is declared SCIENTIFICALLY FROZEN.**

### 1.1 Non-Negotiable Freeze Boundaries
1. **Zero New Baselines**: No baseline beyond Baseline B6 (e.g., "B7") shall be introduced into this benchmark iteration. All subsequent modeling experiments belong to future benchmark generations.
2. **Canonical Benchmark Immutability**: The 964-record canonical benchmark corpus containing 724 gold standard Indian PII entities remains permanently immutable. No records, character spans, entity labels, or metadata shall be modified, regenerated, re-split, or normalized.
3. **Artifact Hash Preservation**: All 22 canonical locked artifacts (raw bases, realization sets, review templates, predictions, and reports for B1–B5) and all B6 experimental artifacts are permanently locked and verified via cryptographic MD5 checksums.
4. **Metric Definition Stability**: Authoritative metric definitions ($M_1$ through $M_6$, Exact F1 $M_4$, Type Accuracy $M_5$, and the strict accounting invariant $TP_{exact} + F_1 + F_2 + F_3 = N_{gold} = 724$) remain fixed without retrospective adjustment.

---

## 2. Summary of Authoritative Scientific Findings

| Baseline | Paradigm | Mode | M1 Precision | M2 Recall | M3 F1 (Type) | M4 Exact F1 | M6 FPR | $TP_{exact}$ | $F_2$ (Boundary) | $F_4$ (False Pos) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **B1** | Regex | Single-run | 0.6478 | 0.5207 | 0.5773 | **0.5773** | 0.2371 | 377 | 0 | 138 |
| **B2** | spaCy `en_core_web_sm` | Single-run | 0.0315 | 0.0608 | 0.0415 | **0.0330** | 0.6316 | 35 | 9 | 883 |
| **B3** | Presidio (IN Enabled) | Single-run | 0.0766 | 0.2956 | 0.1217 | **0.1149** | 0.7539 | 202 | 12 | 2105 |
| **B4** | Zero-Shot XLM-RoBERTa | Single-run | 0.2013 | 0.1298 | 0.1579 | **0.1444** | 0.6039 | 86 | 8 | 282 |
| **B5** | Indian-Adapted XLM-R | 3-seed Mean | 0.4312 ± 0.0030 | 0.9742 ± 0.0008 | 0.5978 ± 0.0029 | **0.3860 ± 0.0061** | 0.5580 ± 0.0032 | 455.3 ± 4.1 | 250.0 ± 4.1 | 912.7 ± 9.5 |
| **B6** | Indian-Adapted XLM-R + CRF | 3-seed Mean | **0.6315 ± 0.0021** | 0.9319 ± 0.0035 | **0.7528 ± 0.0022** | **0.6654 ± 0.0034** | **0.3292 ± 0.0025** | **596.3 ± 3.7** | **78.3 ± 1.7** | **351.7 ± 3.7** |

### Key Scientific Takeaways
1. **Resolution of Boundary Collapse**: Transitioning from independent token decoding (B5) to sequence-constrained CRF decoding (B6) delivers a massive gain of **$+0.2795$ Exact F1** (+72.4% relative) and reduces boundary errors by **$-68.7\%$** ($250.0 \to 78.3$).
2. **False Positive Mechanism Resolution**: CRF sequence decoding penalizes illegal sub-token emissions, reducing duplicate subspan false positives ($FP_9$) by **$-90.9\%$** ($351.3 \to 32.0$) and total false positives by **$-61.5\%$** ($912.7 \to 351.7$).
3. **Identified Residual Frontiers**:
   - *A1 Whitespace Insertion Vulnerability*: Exact F1 degrades to $0.2941$ due to sub-word tokenizer fragmentation.
   - *Decoy Susceptibility*: 100% record-level FPR on pure non-PII numeric strings.
   These two open problems define the technical agenda for subsequent research iterations.

---

## 3. Publication and Release Deliverables Manifest

All required release artifacts have been generated, verified, and placed under version-controlled directories:

```
reports/final/
├── CANONICAL_ARTIFACT_HASHES.json & .md  (Bitwise cryptographic verification of all 22+ artifacts)
├── MASTER_RESULTS_TABLE.json, .csv, .md  (Authoritative master performance and error matrices)
├── PER_TYPE_RESULTS.csv                  (Breakdown across 9 Indian PII categories)
├── PER_LANGUAGE_RESULTS.csv              (Breakdown across 5 Indic script & language regimes)
├── PERTURBATION_RESULTS.csv              (Breakdown across Clean + A1–A5 perturbation types)
├── DIFFICULTY_RESULTS.csv                (Breakdown across Easy, Medium, and Hard tiers)
├── SV02_ABLATION_TABLE.csv               (Findings from controlled hard-negative ablation)
├── SV03_ERROR_TABLE.csv                  (Taxonomy of error categories B5 vs B6)
├── B1_B6_COMPARISON.md                   (Comprehensive evolutionary baseline analysis)
├── FINAL_METRIC_DEFINITIONS.md           (Mathematical definitions and accounting invariants)
├── PRIVACY_RELEASE_AUDIT.md              (Zero-PII and secrets compliance certification)
├── FINAL_TEST_RECORD.md                  (Authoritative test suite pass logs)
└── figures/
    ├── fig1_b1_b6_overall_f1.png & .json
    ├── fig2_b1_b6_precision_recall.png & .json
    ├── fig3_b5_b6_error_partition.png & .json
    ├── fig4_b5_b6_boundary_errors.png & .json
    ├── fig5_sv02_ablation.png & .json
    ├── fig6_sv03_fp_breakdown.png & .json
    ├── fig7_language_robustness.png & .json
    └── fig8_perturbation_robustness.png & .json
```

---

## 4. Verification & Governance Certification

- **Canonical Hash Audit**: 100% MATCH across all 22 canonical locked artifacts.
- **Test Suite Status**: All automated unit, regression, governance, and freeze tests PASS without errors or warnings.
- **Privacy Release Audit**: PASS (100% synthetic data, zero credential leakage).
- **Claim Audit**: All empirical claims certified as SUPPORTED or appropriately qualified.

**Sign-off**:  
`SCIENTIFIC FREEZE — APPROVED AND LOCKED`  
*Indian PII Robustness Benchmark Project*
