# Indian PII Robustness Benchmark — Final Scientific Claim Audit
**Audit Identifier**: `REPORTS-FINAL-CLAIM-AUDIT-V1.0`  
**Benchmark Version**: `0.18`  
**Evaluation Scope**: Baselines B1–B6, Scientific Validations SV-01, SV-02, SV-03  
**Date**: September 9, 2026  
**Status**: AUDITED & LOCKED  

---

## 1. Audit Framework & Classification Standards

Every empirical claim and methodological assertion made in the benchmark publications, technical reports, and baseline documentation has been evaluated against the frozen empirical artifacts. Claims are assigned one of four formal validation statuses:

- **`SUPPORTED`**: The claim is directly substantiated by quantitative empirical evidence across all evaluated seeds and canonical partitions, with zero counter-examples in the locked records.
- **`PARTIALLY_SUPPORTED`**: The claim holds under specific conditions or subsets, but exhibits documented boundary limitations or requires narrower scope qualifications.
- **`UNSUPPORTED`**: The empirical evidence fails to substantiate the claim, or directly refutes the hypothesized mechanism.
- **`REQUIRES_FORMAL_TEST`**: The empirical direction is positive and consistent across all observations, but formal mathematical claims (e.g., "statistical significance") cannot be formally certified without larger sample sizes or designated hypothesis tests.

---

## 2. Comprehensive Claim Registry and Audit Decisions

### Claim 1: Sequence-Constrained CRF Decoding Resolves Exact Boundary Collapse
- **Asserted Claim**: Introducing a Linear Chain CRF decoding layer over the adapted XLM-RoBERTa encoder resolves exact-boundary degradation and significantly improves exact F1 ($M_4$).
- **Evidence**: Across three adaptation seeds ($42, 43, 44$):
  - B5 Mean Exact F1: $0.3860 \pm 0.0061$ (values: $0.3861, 0.3920, 0.3797$).
  - B6 Mean Exact F1: $0.6654 \pm 0.0034$ (values: $0.6689, 0.6622, 0.6652$).
  - Mean Delta: $+0.2795$ (+72.4% relative improvement).
  - Entity-level tracking (seed 42): 151 boundary error entities directly converted to exact true matches, with 450/456 existing exact matches preserved.
- **Audit Decision**: **`SUPPORTED`**
- **Notes**: Consistent across all three seeds with low variance ($\sigma = 0.0034$).

---

### Claim 2: CRF Decoding Eliminates the Vast Majority of Duplicate Subspan Extractions
- **Asserted Claim**: The primary driver of false positives in B5 was duplicate partial subspan emissions ($FP_9$), which the CRF eliminates via transition penalties.
- **Evidence**:
  - B5 Mean $FP_9$ count: $351.3$ extractions.
  - B6 Mean $FP_9$ count: $32.0$ extractions.
  - Net Reduction: $-319.3$ extractions ($-90.9\%$ relative reduction).
  - Transition matrix analysis confirms large negative weights ($< -4.5$) learned for illegal transitions ($O \to I\text{-TYPE}$, $B\text{-TYPE}_1 \to I\text{-TYPE}_2$).
- **Audit Decision**: **`SUPPORTED`**

---

### Claim 3: Pretrained Multilingual Zero-Shot Transfer is Insufficient for Indian PII
- **Asserted Claim**: Off-the-shelf multilingual models (B4 Zero-shot XLM-RoBERTa) without Indic domain adaptation fail to extract Indian PII.
- **Evidence**:
  - B4 Recall ($M_2$): $0.1298$ (only 94 localized entities out of 724 gold).
  - B4 Exact F1 ($M_4$): $0.1444$.
  - Structured identifiers (`AADHAAR`, `PAN`, `VOTER_ID`, `DRIVING_LICENSE`, `UPI_ID`) achieved $0.0\%$ recall in B4.
  - B5 Indic adaptation raised recall to $0.9742 \pm 0.0008$.
- **Audit Decision**: **`SUPPORTED`**

---

### Claim 4: Off-the-Shelf Commercial/Industrial Frameworks are Unsafe for Indic Deployment Without Retraining
- **Asserted Claim**: Standard Western tools like spaCy (`en_core_web_sm`) and Microsoft Presidio produce unacceptable error rates and over-extraction on Indian data.
- **Evidence**:
  - B2 spaCy Precision ($M_1$): $0.0315$, Exact F1 ($M_4$): $0.0330$, False Positives ($F_4$): $883$.
  - B3 Presidio Precision ($M_1$): $0.0766$, Exact F1 ($M_4$): $0.1149$, False Positives ($F_4$): $2,105$, FPR ($M_6$): $0.7539$.
- **Audit Decision**: **`SUPPORTED`**

---

### Claim 5: Data-Centric Hard-Negative Training Eliminates Precision Collapse in Token Classifiers
- **Asserted Claim**: The precision collapse observed in adapted transformers is primarily caused by an absence of hard negatives in the adaptation corpus, and adding hard negatives solves the problem.
- **Evidence (from SV-02 Controlled Ablation)**:
  - Token-matched positive baseline (`b5_positive_matched`): Precision $= 0.4312$, Exact F1 $= 0.3860$.
  - Hard-negative supervised variant (`b5_hard_negative`): Precision $= 0.4645$, Exact F1 $= 0.3924$.
  - Net Precision Shift: $+0.0333$. Net Exact F1 Shift: $+0.0064$.
  - Boundary errors ($F_2$) remained high at $256$ entities.
- **Audit Decision**: **`UNSUPPORTED`**
- **Corrected Scientific Finding**: Hard-negative training yields minor precision gains ($+0.033$) but cannot overcome the architectural boundary collapse of independent token decoding. Structural decoding (CRF) is required.

---

### Claim 6: Indian-Adapted Models Achieve Uniform Robustness Across All Perturbations
- **Asserted Claim**: Adapted models are robust across all realistic noise conditions and adversarial perturbations.
- **Evidence**:
  - Phonetic (A2), OCR (A3), Script Mix (A4), and Delimiters (A5) show strong resilience in B6, retaining Exact F1 between $0.6410$ and $0.7241$.
  - However, Whitespace Insertion (A1) causes catastrophic degradation: B5 Exact F1 drops to $0.1420$, and B6 Exact F1 drops to $0.2941$.
- **Audit Decision**: **`PARTIALLY_SUPPORTED`**
- **Required Qualification**: Models are robust to character-level noise, phonetic variation, and script-mixing, but remain severely vulnerable to internal token-splitting whitespace perturbations.

---

### Claim 7: B6 Eliminates False Positives on Held-Out Hard Negative Decoy Records
- **Asserted Claim**: The sequence-constrained model correctly rejects pure non-PII decoy sequences.
- **Evidence**:
  - Canonical benchmark contains 50 pure hard-negative records with non-PII 12-digit and 10-digit decoy strings.
  - B5 Record-Level FPR on hard negatives: $100.0\%$ (all 50 records triggered extractions).
  - B6 Record-Level FPR on hard negatives: $100.0\%$ (all 50 records still triggered extractions).
- **Audit Decision**: **`UNSUPPORTED`**
- **Corrected Scientific Finding**: Neither B5 nor B6 solves held-out decoy number rejection. The CRF resolves structural span boundaries but does not provide deep semantic negative discrimination.

---

### Claim 8: The Improvement of B6 over B5 is Statistically Significant
- **Asserted Claim**: The performance leap from B5 to B6 is statistically significant.
- **Evidence**:
  - The performance gain is substantial ($+0.2795$ Exact F1, $-171.7$ boundary errors) and holds consistently without exception across all three seeds ($42, 43, 44$).
  - However, because the adaptation seeds were $N=3$, standard non-parametric hypothesis tests (e.g., Wilcoxon signed-rank, bootstrap permutation test) lack sufficient degrees of freedom to formally claim statistical significance at $p < 0.05$.
- **Audit Decision**: **`REQUIRES_FORMAL_TEST`**
- **Required Language Policy**: In all official documentation and publications, the phrasing must state: *"The improvement is supported consistently across three random seeds"* rather than *"statistically significant"*.

---

## 3. Claim Audit Summary Table

| Claim # | Topic | Asserted Premise | Empirical Status | Required Scientific Phrasing |
| :---: | :--- | :--- | :--- | :--- |
| **C1** | Decoding Architecture | CRF resolves exact boundary collapse | **`SUPPORTED`** | Direct, validated claim |
| **C2** | Error Mechanism | CRF eliminates duplicate subspans | **`SUPPORTED`** | Direct, validated claim (-90.9% FP9) |
| **C3** | Zero-Shot Transfer | Pretrained multilingual models fail | **`SUPPORTED`** | Direct, validated claim (B4 F1=0.144) |
| **C4** | Industrial Toolkits | Off-the-shelf tools unsafe for India | **`SUPPORTED`** | Direct, validated claim (B2/B3 high FPR) |
| **C5** | Training Interventions | Hard negatives solve precision deficit | **`UNSUPPORTED`** | Refuted by SV-02; structural decode needed |
| **C6** | Noise Robustness | Robust to all perturbations | **`PARTIALLY_SUPPORTED`**| Robust except A1 whitespace perturbations |
| **C7** | Decoy Discrimination | Eliminates held-out decoy false positives | **`UNSUPPORTED`** | Refuted; 100% record-level decoy FPR remains |
| **C8** | Statistical Rigor | Improvement is statistically significant | **`REQUIRES_FORMAL_TEST`**| Must use "supported consistently across 3 seeds" |

---

## 4. Governance Action

All scientific texts, summary tables, and final declarations have been reviewed to ensure compliance with this audit register. No unsupported or unverified claims remain in the authoritative scientific record.
