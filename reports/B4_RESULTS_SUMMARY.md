# Baseline B4 Evaluation Report: Multilingual Transformer NER (XLM-RoBERTa)

**Benchmark Version:** Indian PII Robustness Benchmark (Pilot v0.1 / Guidelines v0.18)  
**Baseline Identifier:** `B4` (Zero-Shot Neural Baseline — `Multilingual Transformer NER`)  
**Companion Contract:** `PROJECT_SPEC.md` §§19–24 (v1.3)  
**Date Evaluated:** 2026-08-28  
**Model & Revision:** `Davlan/xlm-roberta-base-ner-hrl` (revision `253f557bd8249b8515114cfd7f71974fe5fa4d2f`)  
**Runtime Environment:** `transformers==5.16.1`, `torch==2.13.0+cpu`, `tokenizers==0.23.1`, `sentencepiece==0.2.2`  
**Evaluation Status:** **LOCKED & CANONICAL**

---

## 1. Executive Summary & Headline Metrics

Baseline B4 evaluates an off-the-shelf zero-shot multilingual neural token classification model (`Davlan/xlm-roberta-base-ner-hrl`) across the frozen 964-record Indian PII benchmark corpus. 

In contrast to classical English NER models (like spaCy in B2), XLM-RoBERTa demonstrates cross-lingual and script-robust capabilities, achieving a **90.82% $F_1$ score on PERSON entities** and **100.00% recall on names** across all 7 language conditions (including Devanagari Hindi). However, lacking structured Indian PII entity heads, it scores **0.00% $F_1$ on PAN, Aadhaar, Phone, Email, UPI, and Bank Accounts**, and recognizes addresses as raw `LOC` entities (resulting in 91 $F_3$ wrong-type errors).

### Headline Benchmark Results Table

| Metric | Result | Interpretation & Formula |
|:---|:---|:---|
| **Gold Entities ($N_{\text{gold}}$)** | **724** | Ground-truth PII entities across 964 records |
| **Total Predictions ($N_{\text{pred}}$)** | **467** | All emitted valid predictions (0 rejected) |
| **$\text{TP}_{\text{type}}$ (Correct Type & Overlap)** | **94** | Type-strict true positives ($\text{IoU} > 0 \land \text{type}_{\text{pred}} == \text{type}_{\text{gold}}$) |
| **$\text{TP}_{\text{exact}}$ (Exact Span & Type)** | **86** | Exact-boundary true positives ($\text{start}_{\text{pred}} == \text{start}_{\text{gold}} \land \text{end}_{\text{pred}} == \text{end}_{\text{gold}}$) |
| **Localized Entities** | **185** | Predictions with $\text{IoU} > 0$ against gold entities |
| **$M_1$ Precision** | **20.13%** | $\text{TP}_{\text{type}} / N_{\text{pred}} = 94 / 467$ |
| **$M_2$ Recall** | **12.98%** | $\text{TP}_{\text{type}} / N_{\text{gold}} = 94 / 724$ |
| **$M_3$ Type-Strict $F_1$** | **15.79%** | $2 \cdot M_1 \cdot M_2 / (M_1 + M_2)$ |
| **$M_4$ Exact-Boundary $F_1$** | **14.44%** | $2 \cdot \text{TP}_{\text{exact}} / (N_{\text{gold}} + N_{\text{pred}}) = 2 \cdot 86 / (724 + 467)$ |
| **$M_5$ Type Accuracy** | **50.81%** | $\text{TP}_{\text{type}} / \text{Localized} = 94 / 185$ |
| **$M_6$ False Positive Rate (FPR)** | **60.39%** | $F_4 / N_{\text{pred}} = 282 / 467$ |
| **$F_1$ Missed Entities** | **539** | Gold entities with zero overlapping predictions |
| **$F_2$ Wrong Span Boundaries** | **8** | Overlapping correctly typed with inexact boundaries |
| **$F_3$ Wrong PII Type** | **91** | Overlapping predictions with incorrect type label (e.g. `LOC` for `ADDRESS`) |
| **$F_4$ False Positive Spans** | **282** | Predictions with zero overlap to any gold entity |

$$\text{Partition Check: } F_1 (539) + F_2 (8) + F_3 (91) + \text{TP}_{\text{exact}} (86) = 724 \equiv N_{\text{gold}}$$

---

## 2. Performance by PII Taxonomy Type

| PII Taxonomy Type | Gold Count | Pred Count | $\text{TP}_{\text{type}}$ | $\text{TP}_{\text{exact}}$ | Precision ($M_1$) | Recall ($M_2$) | Type $F_1$ ($M_3$) | Exact $F_1$ ($M_4$) | Type Acc ($M_5$) | FPR ($M_6$) | $F_1$ Miss | $F_2$ Span | $F_3$ Type | $F_4$ FP |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **PERSON** | 94 | 113 | 94 | 86 | **83.19%** | **100.00%** | **90.82%** | **83.09%** | 100.00% | 16.81% | 0 | 8 | 0 | 19 |
| **ADDRESS** | 94 | 325 | 0 | 0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 72.00% | 3 | 0 | 91 | 234 |
| **PAN** | 93 | 0 | 0 | 0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 93 | 0 | 0 | 0 |
| **AADHAAR** | 93 | 0 | 0 | 0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 93 | 0 | 0 | 0 |
| **PHONE** | 82 | 0 | 0 | 0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 82 | 0 | 0 | 0 |
| **EMAIL** | 82 | 0 | 0 | 0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 82 | 0 | 0 | 0 |
| **UPI_ID** | 93 | 0 | 0 | 0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 93 | 0 | 0 | 0 |
| **BANK_ACCOUNT** | 93 | 0 | 0 | 0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 93 | 0 | 0 | 0 |
| *HARD_NEGATIVE (Distractors)* | 0 | 4 | 0 | 0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 100.00% | 0 | 0 | 0 | 4 |

---

## 3. Performance by Linguistic & Realization Condition

| Language Condition | Description | Gold | Pred | $\text{TP}_{\text{type}}$ | $\text{TP}_{\text{exact}}$ | Precision | Recall | Type $F_1$ ($M_3$) | Exact $F_1$ ($M_4$) | FPR ($M_6$) |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **`EN`** | Standard English | 200 | 81 | 22 | 21 | 27.16% | 11.00% | 15.66% | 14.95% | 49.38% |
| **`IN_EN`** | Indian English Markers | 100 | 54 | 12 | 11 | 22.22% | 12.00% | 15.58% | 14.29% | 55.56% |
| **`ROM_HI`** | Romanized Hindi Loanwords | 100 | 56 | 12 | 10 | 21.43% | 12.00% | 15.38% | 12.82% | 57.14% |
| **`HINGLISH`** | Code-Mixed Hindi-English | 100 | 53 | 12 | 12 | 22.64% | 12.00% | 15.69% | 15.69% | 54.72% |
| **`INFORMAL_HINGLISH`** | Social / Colloquial Hinglish | 100 | 52 | 12 | 12 | 23.08% | 12.00% | 15.79% | 15.79% | 53.85% |
| **`HI_LATIN_PII`** | Hindi Carrier + Latin PII | 100 | 61 | 12 | 9 | 19.67% | 12.00% | 14.91% | 11.18% | 60.66% |
| **`HI_DEVA_PII`** | Native Devanagari Script PII | 24 | 58 | 12 | 11 | 20.69% | **50.00%** | **29.27%** | **26.83%** | 58.62% |

---

## 4. Performance by Perturbation Family & Difficulty

### By Perturbation Family

| Family | Perturbation Description | Gold | Pred | $\text{TP}_{\text{type}}$ | $\text{TP}_{\text{exact}}$ | Precision | Recall | $F_1$ ($M_3$) | FPR ($M_6$) |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| **`NONE`** | Clean canonical realizations | 624 | 438 | 84 | 77 | 19.18% | 13.46% | 15.82% | 61.64% |
| **`A1`** | Punctuation / Delimiter Insertion | 20 | 2 | 2 | 1 | 100.00% | 10.00% | 18.18% | 0.00% |
| **`A2`** | Spacing Variations / Whitespace | 20 | 8 | 2 | 2 | 25.00% | 10.00% | 14.29% | 50.00% |
| **`A3`** | Letter Substitution / Typos | 20 | 8 | 2 | 2 | 25.00% | 10.00% | 14.29% | 50.00% |
| **`A4`** | Numeric Word / Token Spans | 20 | 8 | 2 | 2 | 25.00% | 10.00% | 14.29% | 50.00% |
| **`A5`** | Homoglyph Substitutions | 20 | 3 | 2 | 2 | 66.67% | 10.00% | 17.39% | 0.00% |

### By Difficulty Tier

| Difficulty Tier | Description | Gold Entities | Predictions | $\text{TP}_{\text{type}}$ | Precision | Recall | $F_1$ ($M_3$) |
|:---|:---|---:|---:|---:|---:|---:|---:|
| **`EASY`** | Single-PII Standard English | 200 | 106 | 24 | 22.64% | 12.00% | 15.69% |
| **`MEDIUM`** | Code-mixed, transliterated, informal | 424 | 280 | 60 | 21.43% | 14.15% | 17.05% |
| **`ADVERSARIAL`** | Perturbed spans (A1–A5) | 100 | 29 | 10 | 34.48% | 10.00% | 15.50% |

---

## 5. Cross-Baseline Comparative Evaluation (B1 vs B2 vs B3 vs B4)

| Baseline | System Version | Total Preds | $\text{TP}_{\text{type}}$ | $\text{TP}_{\text{exact}}$ | $M_1$ Precision | $M_2$ Recall | $M_3$ Type $F_1$ | $M_4$ Exact $F_1$ | $M_5$ Type Acc | $M_6$ FPR |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **B1 (Regex)** | `regex_1.0.0` | 582 | 377 | 377 | **64.78%** | **52.07%** | **57.73%** | **57.73%** | **84.91%** | **23.71%** |
| **B2 (spaCy)** | `spacy_3.8.16_en_core_web_sm` | 1398 | 44 | 35 | 3.15% | 6.08% | 4.15% | 3.30% | 8.54% | 63.16% |
| **B3 (Presidio)** | `presidio_2.2.364_in_enabled` | 2792 | 214 | 202 | 7.66% | 29.56% | 12.17% | 11.49% | 31.15% | 75.39% |
| **B4 (XLM-R)** | `transformer_5.16.1_xlm_roberta` | 467 | 94 | 86 | **20.13%** | **12.98%** | **15.79%** | **14.44%** | **50.81%** | **60.39%** |

### Per-PII Type $F_1$ Score Comparison Across Baselines

| PII Category | B1 (Regex) | B2 (spaCy) | B3 (Presidio) | B4 (XLM-RoBERTa) | Best Baseline |
|:---|---:|---:|---:|---:|:---|
| **`PERSON`** | 0.00% | 42.31% | 42.93% | **90.82%** | **B4 (XLM-RoBERTa)** |
| **`PAN`** | **100.00%** | 0.00% | 56.07% | 0.00% | **B1 (Regex)** |
| **`AADHAAR`** | **79.52%** | 0.00% | 0.00% | 0.00% | **B1 (Regex)** |
| **`PHONE`** | 71.05% | 0.00% | 31.43% | 0.00% | **B1 (Regex)** |
| **`EMAIL`** | **100.00%** | 0.00% | 0.00% | 0.00% | **B1 (Regex)** |
| **`UPI_ID`** | **100.00%** | 0.00% | 0.00% | 0.00% | **B1 (Regex)** |
| **`BANK_ACCOUNT`** | 0.00% | 0.00% | 0.00% | 0.00% | *None* |
| **`ADDRESS`** | 0.00% | 0.00% | 0.00% | 0.00% | *None* |

---

## 6. Canonical Artifact Registry & Verification Hashes

All 14 repository artifacts and benchmark files are locked and mathematically verified:

```
[1]  data/raw/base_instances.jsonl                                      : MD5 7006b0c9227d93541d2b71f702407ecc
[2]  data/raw/hard_negative_bases.jsonl                                 : MD5 b36c6c106548d18ff7083fd00532cb07
[3]  data/generated/language_realizations.jsonl                         : MD5 0cb046740507eb9111a214b24b680483
[4]  data/generated/hard_negative_realizations.jsonl                    : MD5 ae5537eec4129822e3d97b05170b4fea
[5]  data/generated/adversarial_realizations.jsonl                     : MD5 1b678b9597737c85197acf80ab56878d
[6]  annotation/review_template.csv                                     : MD5 78c5767f2f8fede2021ff344aaddc32c
[7]  predictions/regex_1.0.0_v0.18.jsonl                                : MD5 8913ac633854a36948a3445e4be0594d
[8]  reports/evaluation_regex_1.0.0_v0.18.json                          : MD5 2958f77985fcc70d704c123e9e952ebd
[9]  predictions/spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.jsonl        : MD5 6c74bd4ec742a1f0c6b8024200937fb5
[10] reports/evaluation_spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.json  : MD5 a9745314b2e71df861ea71af15a9dd1a
[11] predictions/presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.jsonl: MD5 2c661403efa963275be5f2559a1577b9
[12] reports/evaluation_presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.json: MD5 4831393231e3d15dc674166dcaaaa2b9
[13] predictions/transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.jsonl: MD5 3f53b646fb9f95414bef8b972d2277b1
[14] reports/evaluation_transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.json: MD5 dfe7e6b93e15ca266b29121977b1809e
```
