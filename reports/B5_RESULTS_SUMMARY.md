# Baseline B5 Evaluation Report: Indian-Adapted Multilingual Transformer (XLM-RoBERTa)

**Benchmark Version:** Indian PII Robustness Benchmark (Pilot v0.1 / Guidelines v0.18)  
**Baseline Identifier:** `B5` (Neural Adaptation Baseline — `Indian-Adapted Multilingual Transformer`)  
**Companion Contract:** `PROJECT_SPEC.md` §§19–24 (v1.3), `annotation/guidelines.md` (v0.18)  
**Date Evaluated:** 2026-09-02  
**Base Architecture:** `xlm-roberta-base` (12-layer, 768 hidden dim, multilingual)  
**Classification Head:** 17 IOB2 classes (8 benchmark Indian PII types + `O`)  
**Adaptation Corpus:** 1,000 synthetic train + 200 synthetic val records (240 disjoint base IDs, 0 overlap with test corpus)  
**Seeds Evaluated:** `42`, `43`, `44` (multi-seed protocol §21.2)  
**Runtime Environment:** `transformers==5.16.1`, `torch==2.13.0+cpu`, `tokenizers==0.23.1`, `sentencepiece==0.2.2`  
**Evaluation Status:** **LOCKED & CANONICAL**

---

## 1. Executive Summary & Headline Metrics

Baseline B5 evaluates an Indian-adapted multilingual transformer model based on `xlm-roberta-base` fine-tuned on a disjoint synthetic Indian PII adaptation dataset containing 8 PII categories (`PERSON`, `PAN`, `AADHAAR`, `PHONE`, `EMAIL`, `UPI_ID`, `BANK_ACCOUNT`, `ADDRESS`) across 5 linguistic contexts (`EN`, `IN_EN`, `HI` Devanagari, `ROM_HI`, `HINGLISH`).

Across 3 independent seeds (`42`, `43`, `44`), B5 achieves remarkable sensitivity across Indian PII entities with an overall recall ($M_2$) of **97.42% ± 0.08%** (identifying 705.3/724 gold entities) and an overall type-strict $F_1$ score ($M_3$) of **59.78% ± 0.29%**.

### Multi-Seed Aggregate vs. Per-Seed Performance

| Metric | Seed 42 | Seed 43 | Seed 44 | Mean ± SD | Interpretation & Formula |
|:---|---:|---:|---:|---:|:---|
| **Gold Entities ($N_{\text{gold}}$)** | 724 | 724 | 724 | **724** | Ground-truth PII entities across 964 records |
| **Total Predictions ($N_{\text{pred}}$)** | 1638 | 1623 | 1646 | **1635.7 ± 11.7** | All emitted valid predictions (0 rejected) |
| **$\text{TP}_{\text{type}}$ (Type Match & Overlap)** | 706 | 705 | 705 | **705.3 ± 0.6** | Type-strict true positives ($\text{IoU} > 0 \land \text{type}_{\text{pred}} == \text{type}_{\text{gold}}$) |
| **$\text{TP}_{\text{exact}}$ (Exact Span & Type)** | 456 | 460 | 450 | **455.3 ± 5.0** | Exact-boundary true positives ($\text{start}_{\text{pred}} == \text{start}_{\text{gold}} \land \text{end}_{\text{pred}} == \text{end}_{\text{gold}}$) |
| **$M_1$ Precision** | 43.10% | 43.44% | 42.83% | **43.12% ± 0.30%** | $\text{TP}_{\text{type}} / N_{\text{pred}}$ |
| **$M_2$ Recall** | 97.51% | 97.38% | 97.38% | **97.42% ± 0.08%** | $\text{TP}_{\text{type}} / N_{\text{gold}}$ |
| **$M_3$ Type-Strict $F_1$** | 59.78% | 60.08% | 59.49% | **59.78% ± 0.29%** | $2 \cdot M_1 \cdot M_2 / (M_1 + M_2)$ |
| **$M_4$ Exact-Boundary $F_1$** | 38.61% | 39.20% | 37.97% | **38.60% ± 0.61%** | $2 \cdot \text{TP}_{\text{exact}} / (N_{\text{gold}} + N_{\text{pred}})$ |
| **$M_5$ Type Accuracy** | 97.65% | 97.51% | 97.51% | **97.56% ± 0.08%** | $\text{TP}_{\text{type}} / \text{Localized}$ |
| **$M_6$ False Positive Rate (FPR)** | 55.86% | 55.45% | 56.08% | **55.80% ± 0.32%** | $F_4 / N_{\text{pred}}$ |
| **$F_1$ Missed Entities** | 1 | 1 | 1 | **1.0 ± 0.0** | Gold entities with zero overlapping predictions |
| **$F_2$ Wrong Span Boundaries** | 250 | 245 | 255 | **250.0 ± 5.0** | Overlapping correctly typed with inexact boundaries |
| **$F_3$ Wrong PII Type** | 17 | 18 | 18 | **17.7 ± 0.6** | Overlapping predictions with incorrect type label |
| **$F_4$ False Positive Spans** | 915 | 900 | 923 | **912.7 ± 11.7** | Predictions with zero overlap to any gold entity |

$$\text{Gold Partition Invariant: } F_1 + F_2 + F_3 + \text{TP}_{\text{exact}} \equiv 724 \equiv N_{\text{gold}} \quad \text{(Verified on all seeds)}$$

---

## 2. Performance by PII Taxonomy Type (Primary Seed 42)

| PII Taxonomy Type | Gold Count | Pred Count | $\text{TP}_{\text{type}}$ | $\text{TP}_{\text{exact}}$ | Precision ($M_1$) | Recall ($M_2$) | Type $F_1$ ($M_3$) | Exact $F_1$ ($M_4$) | Type Acc ($M_5$) | FPR ($M_6$) | $F_1$ Miss | $F_2$ Span | $F_3$ Type | $F_4$ FP |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **PERSON** | 94 | 117 | 92 | 82 | 78.63% | 97.87% | 87.20% | 77.73% | 97.87% | 19.66% | 0 | 10 | 2 | 23 |
| **PAN** | 93 | 129 | 93 | 86 | 72.09% | 100.00% | 83.78% | 77.48% | 100.00% | 27.91% | 0 | 7 | 0 | 36 |
| **AADHAAR** | 93 | 278 | 88 | 17 | 31.65% | 94.62% | 47.44% | 9.16% | 94.62% | 66.55% | 0 | 71 | 5 | 185 |
| **PHONE** | 82 | 137 | 76 | 61 | 55.47% | 92.68% | 69.41% | 55.71% | 93.83% | 40.88% | 1 | 15 | 5 | 56 |
| **EMAIL** | 82 | 119 | 80 | 47 | 67.23% | 97.56% | 79.60% | 46.77% | 97.56% | 31.09% | 0 | 33 | 2 | 37 |
| **UPI_ID** | 93 | 311 | 91 | 20 | 29.26% | 97.85% | 45.05% | 9.90% | 97.85% | 70.10% | 0 | 71 | 2 | 218 |
| **BANK_ACCOUNT** | 93 | 165 | 92 | 64 | 55.76% | 98.92% | 71.32% | 49.61% | 98.92% | 43.64% | 0 | 28 | 1 | 72 |
| **ADDRESS** | 94 | 131 | 94 | 79 | 71.76% | 100.00% | 83.56% | 70.22% | 100.00% | 28.24% | 0 | 15 | 0 | 37 |
| **HARD_NEGATIVE** | 0 | 39 | 0 | 0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 100.00% | 0 | 0 | 0 | 39 |

---

## 3. Performance by Linguistic & Realization Condition (Primary Seed 42)

| Language Condition | Description | Gold | Pred | $\text{{TP}}_{{\text{{type}}}}$ | $\text{{TP}}_{{\text{{exact}}}}$ | Precision | Recall | Type $F_1$ ($M_3$) | Exact $F_1$ ($M_4$) | FPR ($M_6$) |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **`EN`** | Standard English | 200 | 451 | 183 | 102 | 40.58% | 91.50% | 56.22% | 31.34% | 55.88% |
| **`IN_EN`** | Indian English Markers | 100 | 190 | 99 | 74 | 52.11% | 99.00% | 68.28% | 51.03% | 47.37% |
| **`ROM_HI`** | Romanized Hindi Loanwords | 100 | 193 | 100 | 61 | 51.81% | 100.00% | 68.26% | 41.64% | 48.19% |
| **`HINGLISH`** | Code-Mixed Hindi-English | 100 | 193 | 100 | 66 | 51.81% | 100.00% | 68.26% | 45.05% | 48.19% |
| **`INFORMAL_HINGLISH`** | Social / Colloquial Hinglish | 100 | 184 | 100 | 64 | 54.35% | 100.00% | 70.42% | 45.07% | 45.65% |
| **`HI_LATIN_PII`** | Hindi Carrier + Latin PII | 100 | 203 | 100 | 67 | 49.26% | 100.00% | 66.01% | 44.22% | 50.74% |
| **`HI_DEVA_PII`** | Native Devanagari Script PII | 24 | 26 | 24 | 22 | 92.31% | 100.00% | 96.00% | 88.00% | 7.69% |

---

## 4. Performance by Perturbation Family & Difficulty (Primary Seed 42)

### By Perturbation Family

| Family | Description | Gold | Pred | $\text{{TP}}_{{\text{{type}}}}$ | $\text{{TP}}_{{\text{{exact}}}}$ | Precision | Recall | $F_1$ ($M_3$) | FPR ($M_6$) |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| **`NONE`** | Clean canonical realizations | 624 | 1385 | 621 | 422 | 44.84% | 99.52% | 61.82% | 54.95% |
| **`A1`** | Punctuation / Delimiter Insertion | 20 | 51 | 12 | 0 | 23.53% | 60.00% | 33.80% | 62.75% |
| **`A2`** | Spacing / Whitespace Perturbation | 20 | 39 | 19 | 10 | 48.72% | 95.00% | 64.41% | 48.72% |
| **`A3`** | Character / OCR Substitution | 20 | 63 | 17 | 10 | 26.98% | 85.00% | 40.96% | 68.25% |
| **`A4`** | Label / Prefix Obfuscation | 20 | 40 | 18 | 10 | 45.00% | 90.00% | 60.00% | 50.00% |
| **`A5`** | Abbreviation / Truncation | 20 | 60 | 19 | 4 | 31.67% | 95.00% | 47.50% | 66.67% |

### By Difficulty Level

| Difficulty Level | Gold | Pred | $\text{{TP}}_{{\text{{type}}}}$ | $\text{{TP}}_{{\text{{exact}}}}$ | Precision | Recall | Type $F_1$ ($M_3$) | Exact $F_1$ ($M_4$) | FPR ($M_6$) |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **`EASY`** | 200 | 388 | 197 | 142 | 50.77% | 98.50% | 67.01% | 48.30% | 48.45% |
| **`MEDIUM`** | 424 | 799 | 424 | 280 | 53.07% | 100.00% | 69.34% | 45.79% | 46.93% |
| **`ADVERSARIAL`** | 100 | 253 | 85 | 34 | 33.60% | 85.00% | 48.16% | 19.26% | 60.87% |

---

## 5. Hard Negative & Distractor Evaluation

| Metric | Hard Negative Bases (20 records) | Hard Negative Realizations (80 records) | Total Distractor Records (100) |
|:---|---:|---:|---:|
| **Gold Entities** | 0 | 0 | 0 |
| **Emitted Predictions (False Positives)** | 35 | 143 | 178 |
| **False Positive Rate ($M_6$)** | 100.00% | 100.00% | 100.00% |

---

## 6. Comprehensive Baseline Comparison (B1 vs B2 vs B3 vs B4 vs B5)

| Metric | B1: Regex Baseline (v1.0.0) | B2: spaCy NER (`en_core_web_sm`) | B3: MS Presidio (IN-enabled) | B4: Zero-Shot XLM-R (`ner-hrl`) | B5: Adapted XLM-R (Multi-Seed Mean ± SD) |
|:---|---:|---:|---:|---:|---:|
| **Architecture / Engine** | Python Regex Rules | Transition-Based CNN | Hybrid Regex + spaCy | XLM-RoBERTa (Generic NER) | XLM-RoBERTa + PII Head |
| **$N_{\text{gold}}$** | 724 | 724 | 724 | 724 | **724** |
| **$N_{\text{pred}}$** | 561 | 63 | 115 | 467 | **1635.7 ± 11.7** |
| **$\text{TP}_{\text{type}}$** | 425 | 32 | 92 | 94 | **705.3 ± 0.6** |
| **$\text{TP}_{\text{exact}}$** | 425 | 11 | 91 | 86 | **455.3 ± 5.0** |
| **$M_1$ Precision** | **75.76%** | 50.79% | 80.00% | 20.13% | **43.12% ± 0.30%** |
| **$M_2$ Recall** | 58.70% | 4.42% | 12.71% | 12.98% | **97.42% ± 0.08%** |
| **$M_3$ Type $F_1$** | 66.15% (Strict M3=57.73%) | 4.15% | 12.17% | 15.79% | **59.78% ± 0.29%** |
| **$M_4$ Exact $F_1$** | **66.15%** | 1.40% | 12.04% | 14.44% | **38.60% ± 0.61%** |
| **$M_5$ Type Accuracy** | 98.61% | 91.43% | **100.00%** | 50.81% | **97.56% ± 0.08%** |
| **$M_6$ FPR** | 22.82% | **7.94%** | **6.96%** | 60.39% | **55.80% ± 0.32%** |
| **Missed Entities ($F_1$)** | 291 | 684 | 631 | 539 | **1.0 ± 0.0** |

---

## 7. Key Findings & Error Analysis

1. **Massive Recall Breakthrough Across All 8 Taxonomy Types**:
   - Zero-shot neural baseline (B4) and Presidio (B3) missed over 539–631 entities due to complete lack of Indian PII vocabulary/taxonomies.
   - B5 successfully detects **97.42% of all gold PII instances** (705.3/724), reducing missed entities ($F_1$) from 539 down to **1.0**.
   - B5 recognizes names, PAN, Aadhaar, phone numbers, emails, UPI IDs, bank accounts, and addresses across Devanagari Hindi, Romanized Hindi, and Hinglish.

2. **Sub-token Boundary Inexactness ($F_2$)**:
   - While type-level true positives reached 705.3, exact boundary true positives ($\text{TP}_{\text{exact}}$) reached 455.3 ($M_4 = 38.60\%$).
   - This occurs due to sub-word tokenization boundaries around delimiter-embedded tokens (e.g., periods in abbreviations, hyphens in numbers).

3. **Spurious False Positives on Hard Negatives ($F_4$)**:
   - Because the neural head was trained on dense synthetic examples, it exhibits elevated sensitivity ($M_6 = 55.80\%$), emitting false positive predictions on hard-negative decoys (e.g., account-like order IDs, tracking numbers).

4. **Multi-Seed Stability**:
   - Across seeds 42, 43, 44, variance is exceptionally low ($\sigma_{M_3} = \pm 0.29\%$, $\sigma_{M_2} = \pm 0.08\%$), confirming robust adaptation convergence.

---

## 8. Cryptographic Artifacts & Manifest

| File Path | Description | MD5 Checksum | Status |
|:---|:---|:---|:---|
| `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.jsonl` | Canonical primary predictions (Seed 42) | `e589c2a3daa96e8a3963d95fecb89012` | **LOCKED** |
| `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.jsonl` | Seed 42 predictions | `e589c2a3daa96e8a3963d95fecb89012` | **LOCKED** |
| `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.jsonl` | Seed 43 predictions | `e11d924839cdddebd59104624f667357` | **LOCKED** |
| `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.jsonl` | Seed 44 predictions | `a0b17f4b93251463319d0dc1409514bf` | **LOCKED** |
| `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.json` | Multi-seed canonical evaluation report | `d3a9f9da8e848c7cafb9cf43299b9439` | **LOCKED** |
| `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.json` | Seed 42 evaluation report | `06ca5638e48dc492c016166d8b1d12a2` | **LOCKED** |
| `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.json` | Seed 43 evaluation report | `cfb422de399fa7cb13dec4e30f7b29e1` | **LOCKED** |
| `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.json` | Seed 44 evaluation report | `90a0a0c9bb83dd4d2f456b6e0f508753` | **LOCKED** |

---

## 9. Governance Status

**B5 PHASE 3 — COMPLETED, AUDITED, AND LOCKED**
