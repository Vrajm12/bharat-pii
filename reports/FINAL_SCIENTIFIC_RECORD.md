# Indian PII Robustness Benchmark — Authoritative Scientific Record
**Document Identifier**: `REPORTS-FINAL-SCIENTIFIC-RECORD-V1.0`  
**Benchmark Version**: `0.18`  
**Freeze Stage**: `SCIENTIFIC_FREEZE_B6`  
**Date**: September 9, 2026  
**Status**: APPROVED & LOCKED  

---

## 1. Executive Summary & Benchmark Overview

The **Indian PII Robustness Benchmark** establishes the first comprehensive, multi-lingual, perturbation-aware evaluation framework specifically designed for Personally Identifiable Information (PII) extraction in Indian high-diversity contexts. Modern industrial PII systems (such as regular expressions, off-the-shelf spaCy pipelines, and Microsoft Presidio) are primarily tuned for Western naming conventions and standardized alphanumeric formats. When deployed in Indian digital ecosystems, these systems suffer acute performance degradation due to multilingual code-mixing, non-standardized phonetic transliterations, informal orthography, and unique statutory identifier syntaxes.

This benchmark rigorously evaluates six baseline paradigms across a locked canonical test corpus of 964 records containing 724 gold standard Indian PII entities:
1. **B1 (Regex)**: Deterministic rule-based recognition targeting canonical Indian identifier patterns.
2. **B2 (spaCy)**: General-domain pretrained neural pipeline (`en_core_web_sm`).
3. **B3 (Microsoft Presidio)**: Hybrid rule-and-context framework with Indian recognizers enabled.
4. **B4 (Zero-Shot XLM-RoBERTa)**: Massively multilingual transformer (`Davlan/xlm-roberta-base-ner-hrl`).
5. **B5 (Indian-Adapted XLM-RoBERTa)**: Multi-task fine-tuned transformer with token classification head.
6. **B6 (Indian-Adapted XLM-RoBERTa + Linear CRF)**: Span-aware sequence-constrained transformer decoding.

Through four sequential scientific validation investigations (**Metric Reconciliation**, **SV-01 Distribution Audit**, **SV-02 Controlled Generalization Ablation**, and **SV-03 Systematic Error Mechanism Study**) leading to **Baseline B6**, this benchmark uncovered and resolved the central failure mechanism of neural token classification for Indian PII: **boundary truncation collapse caused by independent sub-token decoding**.

---

## 2. Locked Benchmark Corpus Architecture

The canonical benchmark dataset (`v0.18`) is strictly frozen and immutable across 964 annotated evaluation records:

```
Canonical Benchmark Corpus (N = 964 records)
├── Base Clean Instances: 200 records (200 gold entities)
├── Language & Script Realizations: 400 records (400 gold entities)
│   ├── English (EN): 50 records
│   ├── Hinglish (Code-Mixed Latin): 100 records
│   ├── Hindi Devanagari (HI_DEVA_PII): 100 records
│   ├── Hindi Latin Transliterated (HI_LATN_PII): 100 records
│   └── Multi-Script Mixed (MIXED): 50 records
├── Adversarial Perturbation Realizations: 314 records (124 gold entities, 190 unperturbed/controls)
│   ├── A1 Whitespace Insertion: 63 records
│   ├── A2 Phonetic Perturbation: 63 records
│   ├── A3 Optical Character Recognition (OCR) Noise: 63 records
│   ├── A4 Script Mixing / Cross-Script Substitution: 63 records
│   └── A5 Delimiter Noise & Irregular Separators: 62 records
└── Hard-Negative Pure Decoy Records: 50 records (0 gold entities)
    ├── Structural Decoy Numbers (12-digit non-Aadhaar, 10-digit non-Phone)
    ├── Alphanumeric Non-PII Codes (Tracking IDs, serial numbers)
    └── Common Indian Entity False Friends (Bank names, government schemes)
```

### Critical Dataset Invariants
- **Total Gold Entities ($N_{gold}$)**: Exactly 724 entities across all 964 records.
- **Entity Type Schema ($\mathcal{T}$, 9 categories)**: `NAME`, `PHONE`, `EMAIL`, `AADHAAR`, `PAN`, `PASSPORT`, `VOTER_ID`, `DRIVING_LICENSE`, `UPI_ID`.
- **Base Overlap Audit (SV-01)**: 0% base instance overlap between adaptation training data (200 base instances) and canonical benchmark test instances (200 test base instances). Absolute zero record leakage verified.
- **Decoy Independence**: 50 pure hard-negative records containing zero gold entities to measure decoy susceptibility and pure false-positive generation.

---

## 3. Authoritative Metric Definitions & Invariant Formulation

To prevent ambiguities across evaluation regimes, the benchmark enforces exact, bipartite matching with strict error partition accounting:

### Core Formulations
Let $N_{gold} = 724$ be the total gold entities, and $N_{pred}$ be the total predictions produced by a model.
1. **Exact Match ($TP_{exact}$)**: Predicted span matches gold span start offset, end offset, and entity type identically: $(\hat{s} = s \land \hat{e} = e \land \hat{t} = t)$.
2. **Type-Strict Overlap ($TP_{type}$)**: Predicted entity matches gold entity type and exhibits non-zero character intersection: $(\hat{t} = t \land \max(s, \hat{s}) < \min(e, \hat{e}))$. By definition:
   $$TP_{type} = TP_{exact} + F_2$$
3. **Error Partition**:
   - $F_1$ (Missed / False Negatives): Gold entities with zero overlapping predictions.
   - $F_2$ (Wrong Span / Boundary Error): Gold entities localized with correct type but mismatched character span boundaries.
   - $F_3$ (Wrong Type / Classification Error): Gold entities overlapping with a prediction of incorrect entity type.
   - $F_4$ (False Positives): Predictions with no matching gold entity, or excess spurious extractions.

### Non-Negotiable Accounting Invariant
For every baseline and every evaluation seed, the error partition strictly satisfies:
$$TP_{exact} + F_1 + F_2 + F_3 = N_{gold} = 724$$
$$N_{pred} = TP_{type} + F_3 + F_4$$

### Standard Metrics
- **$M_1$ Precision (Type-Strict)**: $\frac{TP_{type}}{N_{pred}}$
- **$M_2$ Recall (Type-Strict)**: $\frac{TP_{type}}{N_{gold}}$
- **$M_3$ F1 (Type-Strict)**: $\frac{2 \cdot M_1 \cdot M_2}{M_1 + M_2} = \frac{2 \cdot TP_{type}}{N_{pred} + N_{gold}}$
- **$M_4$ Exact F1**: $\frac{2 \cdot TP_{exact}}{N_{pred} + N_{gold}}$
- **$M_5$ Type Accuracy**: $\frac{TP_{type}}{TP_{type} + F_3}$
- **$M_6$ False Positive Rate (Entity-level)**: $\frac{F_4}{N_{pred}}$

---

## 4. Complete Baselines Taxonomy

| Baseline | System / Checkpoint | Model Family | Decoding Paradigm | Total Params | Runtime Hardware |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **B1** | `regex_1.0.0` | Deterministic Rules | Regular Expression Engine | N/A | CPU |
| **B2** | `en_core_web_sm` (v3.8.16) | Statistical / CNN | spaCy Transition Parser | 13.0M | CPU |
| **B3** | Microsoft Presidio (v2.2.364) | Hybrid (Rules + spaCy) | Thresholded Pattern Matching | ~13.0M | CPU |
| **B4** | `Davlan/xlm-roberta-base-ner-hrl` | Multilingual Transformer | Independent Softmax Token Head | 278.0M | GPU / CPU |
| **B5** | `xlm_roberta_base_indian` | Indian-Adapted Transformer | Independent Softmax Token Head | 277.5M | GPU / CPU |
| **B6** | `xlm_roberta_base_indian_crf` | Indian-Adapted Transformer | First-Order Linear Chain CRF | 277.5M | GPU / CPU |

---

## 5. Comprehensive Performance Results

### Authoritative Master Results Table
Single-run baselines (B1–B4) are evaluated once on the canonical benchmark. Multi-seed adapted baselines (B5 and B6) are evaluated across three random adaptation seeds ($S \in \{42, 43, 44\}$) and reported as Mean ± Standard Deviation.

| ID | Baseline System | Mode | M1 Precision | M2 Recall | M3 F1 (Type) | M4 Exact F1 | M5 Type Acc | M6 FPR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **B1** | Regex (Canonical v1.0.0) | Single-run | 0.6478 | 0.5207 | 0.5773 | **0.5773** | 0.8491 | 0.2371 |
| **B2** | spaCy `en_core_web_sm` | Single-run | 0.0315 | 0.0608 | 0.0415 | **0.0330** | 0.0854 | 0.6316 |
| **B3** | Presidio (IN Enabled) | Single-run | 0.0766 | 0.2956 | 0.1217 | **0.1149** | 0.3115 | 0.7539 |
| **B4** | Zero-Shot XLM-RoBERTa | Single-run | 0.2013 | 0.1298 | 0.1579 | **0.1444** | 0.5081 | 0.6039 |
| **B5** | Indian-Adapted XLM-R | 3-seed Mean | 0.4312 ± 0.0030 | 0.9742 ± 0.0008 | 0.5978 ± 0.0029 | **0.3860 ± 0.0061** | 0.9756 ± 0.0008 | 0.5580 ± 0.0032 |
| **B6** | Indian-Adapted XLM-R + CRF | 3-seed Mean | **0.6315 ± 0.0021** | 0.9319 ± 0.0035 | **0.7528 ± 0.0022** | **0.6654 ± 0.0034** | 0.9414 ± 0.0028 | **0.3292 ± 0.0025** |

### Absolute Error Partition Counts ($N_{gold} = 724$)

| ID | Baseline System | $TP_{exact}$ | $TP_{type}$ | $F_1$ Missed | $F_2$ Boundary | $F_3$ Wrong Type | $F_4$ False Pos |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **B1** | Regex (Canonical v1.0.0) | 377 | 377 | 280 | 0 | 67 | 138 |
| **B2** | spaCy `en_core_web_sm` | 35 | 44 | 209 | 9 | 471 | 883 |
| **B3** | Presidio (IN Enabled) | 202 | 214 | 37 | 12 | 473 | 2105 |
| **B4** | Zero-Shot XLM-RoBERTa | 86 | 94 | 539 | 8 | 91 | 282 |
| **B5** | Indian-Adapted XLM-R | 455.3 ± 4.1 | 705.3 ± 0.5 | 1.0 ± 0.0 | 250.0 ± 4.1 | 17.7 ± 0.5 | 912.7 ± 9.5 |
| **B6** | Indian-Adapted XLM-R + CRF | 596.3 ± 3.7 | 674.7 ± 2.1 | 7.7 ± 0.9 | 78.3 ± 1.7 | 41.7 ± 1.2 | 351.7 ± 3.7 |

---

## 6. Error Partitioning & Transition Dynamics (B5 → B6)

The transition from Baseline B5 to Baseline B6 directly tests the hypothesis formulated in SV-03: *independent sub-token classification causes structural boundary truncation and duplicate partial span emission*.

### Detailed Entity-Level Transition Tracking (Seed 42)
Tracing all 724 gold standard entities and their individual prediction states from B5 to B6 reveals:
1. **$F_2$ Boundary Errors Converted to $TP_{exact}$**: **151 entities** previously truncated or expanded by B5 were corrected to exact character matches by B6's sequence transition constraints.
2. **$TP_{exact}$ Preservation**: **450 out of 456** ($98.7\%$) exact true positives established by B5 were preserved by B6.
3. **Net True Positive Gain**: $+145$ exact matches ($456 \to 601$ entities).
4. **False Positive Suppression**: False positive predictions plummeted from 915 to 356 (**$-61.1\%$ reduction**).
5. **Partial Subspan Extractions ($FP_9$)**: Dropped from 351.3 to 32.0 (**$-90.9\%$ reduction**), proving that the CRF layer successfully penalizes illicit token-level BIO transitions.

---

## 7. Per-Entity Type Analysis

Performance varies substantially across structured vs. unstructured Indian PII categories:

| PII Category | B1 Exact F1 | B4 Exact F1 | B5 Exact F1 (Mean) | B6 Exact F1 (Mean) | Delta (B6 vs B5) | Dominant Residual Failure Mode |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **AADHAAR** | 0.8120 | 0.0000 | 0.3275 | **0.8682** | **+0.5407** | Whitespace insertion splitting 12 digits |
| **DRIVING_LICENSE** | 0.5714 | 0.0000 | 0.4444 | **0.7812** | **+0.3368** | State code prefix boundary variation |
| **EMAIL** | 0.8657 | 0.6500 | 0.7619 | **0.8750** | **+0.1131** | OCR delimiter noise (`.` vs `,`) |
| **NAME** | 0.0000 | 0.2857 | 0.4721 | **0.6214** | **+0.1493** | Honorific inclusion (`Shri`, `Dr.`) |
| **PAN** | 0.8400 | 0.0000 | 0.4512 | **0.8814** | **+0.4302** | 5th character entity surname check |
| **PASSPORT** | 0.7442 | 0.0000 | 0.3913 | **0.7586** | **+0.3673** | Letter prefix / alphanumeric boundary |
| **PHONE** | 0.6842 | 0.0000 | 0.3120 | **0.6521** | **+0.3401** | Country code prefix (`+91`) attachment |
| **UPI_ID** | 0.4737 | 0.0000 | 0.2814 | **0.5124** | **+0.2310** | Handle suffix truncation (`@okhdfcbank`) |
| **VOTER_ID** | 0.6154 | 0.0000 | 0.3684 | **0.7647** | **+0.3963** | 3-letter assembly constituency prefix |

---

## 8. Language & Script Robustness

The benchmark tests cross-lingual generalization across five distinct Indian script regimes:

| Language Regime | Gold Entities | B1 Exact F1 | B4 Exact F1 | B5 Exact F1 | B6 Exact F1 | Linguistic Mechanism |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **English (EN)** | 200 | 0.5541 | 0.1622 | 0.3750 | **0.5957** | Formal grammar, standard delimiters |
| **Hinglish** | 100 | 0.9662 | 0.1500 | 0.4762 | **0.7672** | Latin code-mixed colloquial context |
| **HI_DEVA_PII** | 100 | 0.0000 | 0.0600 | 0.4120 | **0.7143** | Devanagari script for both context & PII |
| **HI_LATN_PII** | 100 | 0.9412 | 0.1600 | 0.4320 | **0.7320** | Hindi syntax in Latin transliterated text |
| **Mixed Script** | 50 | 0.4211 | 0.1100 | 0.3450 | **0.6120** | Code-switching across Devanagari & Latin |

---

## 9. Perturbation Sensitivity Profile

Adversarial perturbations systematically probe model stability under synthetic degradation:

| Perturbation Type | Description | B5 Exact F1 | B6 Exact F1 | Delta (M4) | Key Finding |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Clean Control** | Unperturbed standard format | 0.4850 | **0.7812** | **+0.2962** | Peak performance for sequence decoding |
| **A1 Whitespace** | Internal space insertion in identifiers | 0.1420 | **0.2941** | **+0.1521** | Severe residual degradation; splits sub-tokens |
| **A2 Phonetic** | Transliteration and phonetic swaps | 0.4120 | **0.6923** | **+0.2803** | Robust semantic preservation in XLM-R |
| **A3 OCR Noise** | Character confusion (`0` $\leftrightarrow$ `O`, `1` $\leftrightarrow$ `I`) | 0.3850 | **0.6750** | **+0.2900** | CRF prevents illegal character transitions |
| **A4 Script Mix** | Intra-word Devanagari/Latin mixing | 0.3620 | **0.6410** | **+0.2790** | Sub-word tokenizer fragmentation mitigated |
| **A5 Delimiters** | Irregular symbols (`#`, `_`, `/`, `-`) | 0.4310 | **0.7241** | **+0.2931** | CRF bounds structured spans cleanly |

---

## 10. Difficulty Stratification

Records are stratified into three difficulty tiers based on linguistic complexity and perturbation intensity:

| Difficulty Tier | Record Count | Gold Entities | B5 Exact F1 | B6 Exact F1 | Precision Gain (B5 $\to$ B6) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **EASY** | 250 | 250 | 0.4621 | **0.7654** | $+0.2312$ ($0.4810 \to 0.7122$) |
| **MEDIUM** | 450 | 350 | 0.3814 | **0.6620** | $+0.1984$ ($0.4250 \to 0.6234$) |
| **HARD** | 264 | 124 | 0.2642 | **0.5120** | $+0.1651$ ($0.3620 \to 0.5271$) |

---

## 11. Controlled Generalization & Hard-Negative Ablation (SV-02)

Investigation SV-02 evaluated whether false positives and precision deficits in adapted transformers stemmed from training data shortcuts:
- **Variant 1 (`b5_positive_matched`)**: Baseline adaptation budget matched to token count without negatives ($M_1 = 0.4312$, exact $F_1 = 0.3860$).
- **Variant 2 (`b5_format_diversity`)**: Diversified formatting during adaptation ($M_1 = 0.4480$, exact $F_1 = 0.3892$).
- **Variant 3 (`b5_hard_negative`)**: Hard-negative supervision included during adaptation ($M_1 = 0.4645$, exact $F_1 = 0.3924$).

**Conclusion**: Hard-negative supervision provided marginal precision gains ($+0.0333$) but left exact boundary F1 virtually unchanged ($0.3860 \to 0.3924$). This conclusively demonstrated that **the root bottleneck was structural decoding architecture, not training data distribution**.

---

## 12. Systematic Error Analysis & Mechanism Discovery (SV-03)

Investigation SV-03 isolated the specific error mechanisms governing B5:
1. **$B_3$ Structured Truncation**: In independent token classification, sub-word boundary tokens are frequently misclassified as `O` (outside), truncating 12-digit Aadhaar or 10-digit PAN numbers into partial invalid substrings (accounting for 179 errors in seed 42).
2. **$FP_9$ Duplicate Partial Subspans**: The model frequently predicted overlapping duplicate entities for the same underlying string (e.g., predicting `AADHAAR` on characters 0–4 and another `AADHAAR` on characters 5–12), generating 351.3 spurious predictions.
3. **$FP_1$ Decoy Susceptibility**: Pure hard-negative decoy numbers (12-digit random numbers embedded in text) produced a 100% record-level False Positive Rate across all seeds, demonstrating over-reliance on local alphanumeric shape without contextual semantic verification.

---

## 13. Span-Aware Decoding & Transition Enforcement (B6)

Baseline B6 introduced a first-order Linear Chain Conditional Random Field (CRF) atop the adapted XLM-RoBERTa encoder representations:
$$s(X, y) = \sum_{i=1}^{T} P_{i, y_i} + \sum_{i=0}^{T} A_{y_i, y_{i+1}}$$
where $P$ is the emission matrix from the transformer encoder, and $A$ is the learnable transition matrix.

### Quantitative Impacts
- **$M_4$ Exact F1 jumped by $+0.2795$** (+72.4% relative, from $0.3860$ to $0.6654$).
- **Boundary errors ($F_2$) plummeted by $-68.7\%$** ($250.0 \to 78.3$).
- **Partial subspan extractions ($FP_9$) dropped by $-90.9\%$** ($351.3 \to 32.0$).
- **Structured identifier truncations ($B_3$) dropped by $-86.0\%$** ($179 \to 25$).

---

## 14. Residual Failure Modes & Open Challenges

Despite B6's dramatic improvements, two core frontiers remain unsolved:
1. **A1 Whitespace Perturbation Vulnerability**: When spaces are inserted into structured identifiers (e.g., `1 2 3 4 5 6 7 8 9 0 1 2`), exact F1 drops from 0.7812 (clean) to 0.2941. Sub-word tokenizers split these inputs into isolated single-digit tokens, disrupting sequence coherence.
2. **Held-Out Hard-Negative Decoy False Positives**: Both B5 and B6 exhibit 100% record-level False Positive Rate on the 50 pure hard-negative records. Decoy 12-digit strings mimicking Aadhaar syntax trigger extraction even when surrounded by negative context ("Account ref code: 9812 3412 8901"). Context-aware negative regularization remains an essential area for future research.

---

## 15. Scientific Claims Register & Audit Summary

Every empirical claim in the benchmark reports was subjected to an adversarial claim audit (documented in detail in `FINAL_CLAIM_AUDIT.md`):
- **Claim 1 (CRF resolves boundary collapse)**: **SUPPORTED** across all 3 seeds ($M_4$ gain $+0.2795$, $F_2$ reduction $-171.7$).
- **Claim 2 (Adaptation improves Indic recall over zero-shot)**: **SUPPORTED** ($M_2$ rises from $0.1298$ in B4 to $0.9742$ in B5 and $0.9319$ in B6).
- **Claim 3 (SV-02 ablation confirms decoding bottleneck)**: **SUPPORTED** (data interventions yielded $<0.01$ exact F1 shift).
- **Statistical Language Clarification**: All multi-seed findings are described as *"supported consistently across three seeds"* rather than *"statistically significant"*, adhering to rigorous scientific reporting standards given $N=3$ seeds.

---

## 16. Threats to Validity & Limitations Summary

1. **Synthetic Base Generation**: Test instances were synthetically constructed to avoid private data leakage. Real-world OCR documents may feature irregular physical artifacts not fully captured by synthetic perturbations.
2. **Scale of Test Set**: $N = 964$ records provides robust error categorization, but rare edge cases in minor Indic languages require broader field testing.
3. **Seed Cardinality ($N=3$)**: Three seeds establish low standard error ($\sigma \le 0.006$) for baseline stability, but formal non-parametric hypothesis tests require larger seed batches.

---

## 17. Reproducibility & Immutability Verification

All 22 canonical locked artifacts and all B6 experimental artifacts were audited via MD5 checksum verification:
- **Canonical Locked MD5s**: 22 / 22 matched ($100.0\%$).
- **Random Seeds**: Adaptation and training seeds strictly frozen at `42`, `43`, `44`.
- **Python Environment**: Python 3.10.9, PyTorch 2.5.1, Transformers 4.49.0, spaCy 3.8.16, Presidio 2.2.364.
- **Artifact Hashes**: Formally registered in `reports/final/CANONICAL_ARTIFACT_HASHES.json`.

---

## 18. Final Scientific Conclusions & Future Roadmap

The Indian PII Robustness Benchmark demonstrates that while pre-trained multilingual foundation models possess the latent capacity for cross-lingual Indic representation, extracting structured PII with high precision and exact boundaries requires:
1. **Explicit Indic task adaptation** to bridge dialectal and lexical domain gaps.
2. **Sequence-level transition constraints (CRF)** to prevent sub-token boundary collapse and duplicate subspan emissions.
3. **Dedicated whitespace-invariant tokenization and contextual negative modeling** to conquer residual frontiers.

This benchmark, its dataset, baselines B1–B6, and experimental artifacts are hereby declared **SCIENTIFICALLY FROZEN**.
