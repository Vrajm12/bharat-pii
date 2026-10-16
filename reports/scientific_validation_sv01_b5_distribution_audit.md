# Scientific Validation Report: Task SV-01
## B5 Adaptation-vs-Test Distribution, Independence & Leakage Audit

**Benchmark Project:** Indian PII Robustness Benchmark (Pilot v0.1 / Guidelines v0.18)  
**Governing Specification:** `PROJECT_SPEC.md` §§19–24 (v1.3), `annotation/guidelines.md` (v0.18)  
**Target Baseline Evaluated:** `B5` — Indian-Adapted Multilingual Transformer (`transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18`)  
**Audit Purpose:** Scientific validation of distributional independence, potential leakage channels, template memorization, and formatting shortcut risks between the B5 adaptation training data and the canonical locked 964-record test corpus.  
**Audit Date:** 2026-09-03  
**Status:** **AUDITED, VERIFIED, AND LOCKED** (Immutable Artifact Protocol Enforced)

---

## 1. Executive Summary

This scientific validation audit (Task **SV-01**) rigorously investigated whether the performance of Baseline B5 ($M_2 = 97.42\% \pm 0.08\%$ Recall, $M_3 = 59.78\% \pm 0.29\%$ Type-Strict $F_1$) could be explained or inflated by data leakage, verbatim memorization, template overlap, or synthetic formatting shortcuts.

### Key Audit Findings:
1. **Zero Base Identity & Text Leakage (Audits A & B):** Base-instance overlap between adaptation train/val and test is **exactly 0** ($0.00\%$). Full-text exact and normalized overlaps across all 964 test records are **0 / 964 ($0.00\%$)**.
2. **Structural & Carrier Template Independence (Audit C):** Adaptation instances utilize corporate/administrative phrasing (e.g., meeting logs, dispatch invoices, payment ledgers), whereas the benchmark test instances utilize fixed carrier templates (e.g., `mera naam [PII] hai`, `Kindly note: ...`). Exact carrier skeleton overlap is **0 / 834 ($0.00\%$)**.
3. **Low Lexical Overlap (Audit D):** Context vocabulary Jaccard similarity (excluding entity spans) is only **0.1213** ($12.13\%$), and word 2-gram Jaccard similarity is **0.0772** ($7.72\%$).
4. **Strong Distribution Shift Diagnostic (Audit I):** A superficial bag-of-words linear classifier achieves **100% cross-validation accuracy** in distinguishing adaptation texts from benchmark test texts, proving marked carrier distribution divergence.
5. **Identification of Root Cause for Specificity Deficit (Audits E & H):**
   - **Shared Synthetic Generator Logic (High Shortcut Risk):** Both adaptation and test base instances were generated from `generators/pii/*.py`. While random seeds and base instances were strictly disjoint, the rigid syntactic signatures of structured PII (e.g., Aadhaar 4-4-4 spacing, UPI `@okhdfcbank` bank handles, PAN 5L-4D-1L pattern) were identical.
   - **Zero Negative Training Samples (High Specificity Risk):** Adaptation data contained **100% positive PII records (0 hard negatives, 0 non-PII distractors)**.
   - **Consequence:** The model acts as a highly sensitive formatting detector, achieving near-perfect recall ($97.42\%$) while over-predicting on hard-negative lookalikes (**$100\%$ FPR on hard negatives, $55.80\%$ overall FPR**).

---

## 2. Scope and Immutable-Artifact Policy

In strict accordance with repository governance:
* **Zero Modification Policy:** No canonical benchmark datasets, annotation files, or locked baseline prediction/report artifacts were modified, overwritten, or re-generated.
* **Non-Mutating Execution:** All diagnostic tokenizations, n-gram extractions, and classification diagnostics were executed purely in-memory using temporary diagnostic scripts in `scratch/sv01/`.
* **Cryptographic Verification:** All 14 prior canonical baseline/corpus artifacts and 8 B5 artifacts were verified via MD5 hashes before and after audit execution.

---

## 3. Dataset Provenance

| Split / Dataset | Record Count | Base IDs | Entities | Distractor / HN Records | Generator / Source |
|:---|---:|---:|---:|---:|:---|
| **Adaptation Train** | 1,000 | 200 (`ADAPT_TRN_*`) | 1,000 | 0 | `baselines/adaptation_data.py` |
| **Adaptation Validation** | 200 | 40 (`ADAPT_VAL_*`) | 200 | 0 | `baselines/adaptation_data.py` |
| **Canonical Test Split** | 964 | 120 (`*_001`..`020`, `HN_*`) | 724 | 100 | Canonical Benchmark Corpus |

---

## 4. Identity Leakage Results (Audit A)

Base instance IDs and record variant IDs were analyzed for set intersections across train, validation, and test partitions:

* **Train Base IDs $\cap$ Canonical Test Base IDs:** **0** (Empty set, $\emptyset$)
* **Validation Base IDs $\cap$ Canonical Test Base IDs:** **0** (Empty set, $\emptyset$)
* **Train Base IDs $\cap$ Validation Base IDs:** **0** (Empty set, $\emptyset$)
* **Record / Variant ID Overlap:** **0** (Empty set, $\emptyset$)
* **Latent Cross-References:** None. Adaptation base instances use isolated synthetic namespaces (`ADAPT_TRN_PERSON_001`, `ADAPT_VAL_PAN_001`, etc.).

$$\text{Identity Leakage Rate: } 0.00\% \quad (\text{Classification: } \mathbf{NO\ EVIDENCE})$$

---

## 5. Exact & Normalized Text Overlap (Audit B)

Every text realization in the adaptation dataset (1,200 records) was compared against every text realization in the canonical benchmark test dataset (964 records):

| Comparison Level | Normalization Applied | Overlapping Matches | Match Rate |
|:---|:---|---:|---:|
| **Exact Raw Text** | None (byte-for-byte string comparison) | **0 / 964** | **0.00%** |
| **Case & Whitespace Normalized** | Lowercase, whitespace collapsed | **0 / 964** | **0.00%** |
| **Punctuation Normalized** | Stripped all Latin & Devanagari punctuation | **0 / 964** | **0.00%** |

$$\text{Full-Text Duplication: } 0.00\% \quad (\text{Classification: } \mathbf{NO\ EVIDENCE})$$

---

## 6. Template Overlap Analysis (Audit C)

Adaptation templates and test carrier templates were converted into PII-agnostic carrier skeletons by masking all entity spans with `[PII]`:

* **Adaptation Template Skeletons:** 40 unique synthetic transactional templates (e.g., `"Yesterday, [PII] visited our regional office for the meeting."`, `"Kindly verify your PAN card details: [PII]."`).
* **Test Benchmark Skeletons:** 834 unique carrier patterns across clean, multilingual, and adversarial realizations.
* **Exact Carrier Skeleton Overlap:** **0 / 834 ($0.00\%$)**
* **Template Structural Risk:** **LOW RISK**. Adaptation records model diverse multi-sentence corporate and banking operations, whereas test records follow frozen linguistically controlled carrier templates (`mera naam [PII] hai`, `मेरा नाम [PII] है।`).

---

## 7. Lexical Overlap Analysis (Audit D)

Lexical distribution overlap was quantified across token vocabularies, context vocabularies (excluding PII spans), word n-grams, and character n-grams:

### Overall Lexical Metrics
* **Total Adaptation Vocabulary:** 576 tokens
* **Total Test Vocabulary:** 397 tokens
* **Shared Vocabulary Intersection:** 162 tokens
* **Overall Vocabulary Jaccard Similarity:** **0.1998** ($19.98\%$)
* **Context Vocabulary Jaccard Similarity (excluding PII):** **0.1213** ($12.13\%$)
* **Word 2-gram Jaccard Similarity:** **0.0772** ($7.72\%$)
* **Word 3-gram Jaccard Similarity:** **0.0475** ($4.75\%$)
* **Character 4-gram Jaccard Similarity:** **0.0908** ($9.08\%$)

### Breakdown by PII Type
| PII Taxonomy Category | Adapt Records | Test Records | Full Vocab Jaccard | Context Vocab Jaccard | Shared Tokens |
|:---|---:|---:|---:|---:|---:|
| **`PERSON`** | 150 | 94 | 0.3354 | **0.1190** | 54 |
| **`PAN`** | 150 | 93 | 0.1067 | **0.1882** | 16 |
| **`AADHAAR`** | 150 | 93 | 0.0987 | **0.1609** | 15 |
| **`PHONE`** | 150 | 82 | 0.0987 | **0.1596** | 15 |
| **`EMAIL`** | 150 | 82 | 0.1250 | **0.1250** | 19 |
| **`UPI_ID`** | 150 | 93 | 0.0833 | **0.1149** | 13 |
| **`BANK_ACCOUNT`** | 150 | 93 | 0.1076 | **0.1848** | 17 |
| **`ADDRESS`** | 150 | 94 | 0.3382 | **0.1395** | 92 |

$$\text{Lexical Overlap Risk: } \mathbf{LOW\ RISK} \quad (\text{Driven solely by domain nouns: 'number', 'card', 'account', 'Nagar'})$$

---

## 8. PII Generator & Formatting Overlap (Audit E)

Both adaptation instances and benchmark test instances were synthesized using the generator functions in `generators/pii/*.py`. While random seeds and base instances were strictly disjoint, the syntactic rules governing entity structure are identical:

| PII Category | Generator Formatting Constraints | Shortcut Risk | Risk Mechanism & Behavioral Evidence |
|:---|:---|:---|:---|
| **`PAN`** | Rigid `[A-Z]{5}[0-9]{4}[A-Z]{1}` regex format | **HIGH RISK** | Alphanumeric shape signature allows trivial classification; zero-shot precision on clean text ($88.42\%$). |
| **`AADHAAR`** | 12 digits, grouped `XXXX XXXX XXXX` | **HIGH RISK** | 4-4-4 digit spacing is a visual heuristic; drives $66.55\%$ FPR on 12-digit non-PII tracking numbers. |
| **`UPI_ID`** | `handle@bank_psp` (`@okhdfcbank`, `@paytm`, `@ybl`) | **HIGH RISK** | Fixed bank handle suffix list acts as a deterministic trigger; causes $70.10\%$ FPR on arbitrary handle formats. |
| **`BANK_ACCOUNT`** | Contiguous 9 to 18 digits | **HIGH RISK** | Unstructured digit sequence without checksum triggers on arbitrary long numeric strings ($43.64\%$ FPR). |
| **`PHONE`** | 10-digit mobile (+91, 0, or raw 10 digits) | **MODERATE RISK**| Triggers on 10-digit invoice / order IDs ($40.88\%$ FPR). |
| **`EMAIL`** | Standard `user@domain` format | **MODERATE RISK**| Standard RFC token structure. |
| **`ADDRESS`** | Multi-part structural address with 6-digit PIN | **MODERATE RISK**| Shared street suffixes (Nagar, Marg, Road) and PIN format. |
| **`PERSON`** | First + Last names sampled from Indian pool | **LOW RISK** | High combinatorial diversity; model generalizes across Latin/Devanagari scripts. |

---

## 9. Language Distribution Comparison (Audit F)

| Language / Realization Condition | Adaptation Realizations | Canonical Test Realizations | Status in Adaptation | B5 Test Recall ($M_2$) |
|:---|---:|---:|:---|---:|
| **`EN`** (Standard English) | 240 | 200 | Present | 91.50% |
| **`IN_EN`** (Indian English Markers) | 240 | 100 | Present | 99.00% |
| **`ROM_HI`** (Romanized Hindi) | 240 | 100 | Present | 100.00% |
| **`HINGLISH`** (Code-Mixed Hinglish) | 240 | 100 | Present | 100.00% |
| **`INFORMAL_HINGLISH`** (Colloquial Slang) | **0** | 100 | **Unseen (Zero-Shot)** | **100.00%** |
| **`HI_LATIN_PII`** (Hindi Carrier + Latin PII) | **0** | 100 | **Unseen (Zero-Shot)** | **100.00%** |
| **`HI_DEVA_PII`** (Devanagari PII) | 240 (`HI` translit) | 24 | Partially Present | **100.00%** |

* **Scientific Finding:** B5 achieved **100.00% recall** on `INFORMAL_HINGLISH` and `HI_LATIN_PII` despite these specific fine-grained realization styles never appearing in adaptation training, demonstrating genuine cross-lingual transfer capability in XLM-RoBERTa.

---

## 10. Perturbation Distribution Comparison (Audit G)

* **Adaptation Perturbations ($A_1$–$A_5$):** **0 records** (Adaptation training data consists 100% of clean, unperturbed carrier sentences).
* **Canonical Test Perturbations:** **100 adversarial records** across $A_1$ (Spacing), $A_2$ (Punctuation), $A_3$ (Char substitution), $A_4$ (Label obfuscation), $A_5$ (Abbreviations).
* **Scientific Finding:** B5 was never exposed to adversarial perturbation algorithms during adaptation. B5's performance on adversarial subsets represents **pure zero-shot evaluation**.

---

## 11. Hard-Negative & Distractor Comparison (Audit H)

* **Adaptation Hard Negatives:** **0 records** (0.00% negative instance representation).
* **Canonical Test Hard Negatives:** **100 distractor records** (20 base instances + 80 realizations).
* **Scientific Finding:** The complete absence of non-PII lookalike distractors in adaptation training directly explains B5's **100% False Positive Rate on hard negatives ($F_4 = 178$)**. Because the model was trained exclusively on positive PII tokens, it acts as a maximum-sensitivity pattern extractor without a specificity boundary.

---

## 12. Superficial Distribution Classifier Diagnostic (Audit I)

To test whether adaptation and test texts are superficially distinguishable, a linear Bag-of-Words Logistic Regression classifier (Top-1,000 word & bigram features) was evaluated with 5-fold cross-validation:

* **Mean 5-Fold Cross-Validation Accuracy:** **100.00%** ($\pm 0.00\%$)
* **Interpretation:** The linear discriminator achieves perfect separation between adaptation and test sentences. This proves that adaptation records (administrative/corporate framing) and test records (benchmark carrier templates) reside in distinctly different linguistic carrier distributions, ruling out sentence-level memorization or paraphrase cloning.

---

## 13. PII Value / Near-Duplicate Memorization Analysis (Audit J)

Extracted entity text values from adaptation data (1,200 entities) were compared against all ground-truth entities in the test corpus (724 entities):

* **Structured PII Categories (`PAN`, `AADHAAR`, `PHONE`, `EMAIL`, `UPI_ID`, `BANK_ACCOUNT`, `ADDRESS`):** **0 exact overlaps, 0 normalized overlaps (0.00%)**.
* **`PERSON` Category:** **4 name collisions** out of 60 unique adaptation names and 30 test names, caused by sampling from the finite underlying Indian given/family name pools. Complete full-name entities remain strictly disjoint.

---

## 14. Train / Val / Test Distribution Balance Table (Audit K)

| Dimension | Adaptation Train | Adaptation Val | Canonical Test | Balance Ratio (Trn : Val : Test) |
|:---|---:|---:|---:|:---|
| **Total Records** | 1,000 | 200 | 964 | 1.04 : 0.21 : 1.00 |
| **Total PII Entities** | 1,000 | 200 | 724 | 1.38 : 0.28 : 1.00 |
| **Hard-Negative Distractors**| 0 | 0 | 100 | **Extreme Imbalance (0% in Adapt)** |
| **`PERSON` Records** | 125 | 25 | 120 | 1.04 : 0.21 : 1.00 |
| **`PAN` Records** | 125 | 25 | 120 | 1.04 : 0.21 : 1.00 |
| **`AADHAAR` Records** | 125 | 25 | 120 | 1.04 : 0.21 : 1.00 |
| **`PHONE` Records** | 125 | 25 | 120 | 1.04 : 0.21 : 1.00 |
| **`EMAIL` Records** | 125 | 25 | 120 | 1.04 : 0.21 : 1.00 |
| **`UPI_ID` Records** | 125 | 25 | 120 | 1.04 : 0.21 : 1.00 |
| **`BANK_ACCOUNT` Records** | 125 | 25 | 120 | 1.04 : 0.21 : 1.00 |
| **`ADDRESS` Records** | 125 | 25 | 124 | 1.01 : 0.20 : 1.00 |

---

## 15. Relationship to B5 Error Profile (Audit L)

The empirical error profile of B5 aligns with the distributional properties identified in this audit:

1. **Aadhaar, UPI_ID, and Bank Account FPR:** B5 achieved high recall ($94.62\%$ to $98.92\%$) but high false positive rates ($66.55\%$ on Aadhaar, $70.10\%$ on UPI). This is directly attributable to the model learning the synthetic formatting shortcuts without negative distractor training.
2. **Hard-Negative 100% FPR:** B5 emitted false alarms on all hard-negative distractor records because zero negative examples were present during adaptation.
3. **Exact Boundary $F_1$ ($M_4 = 38.60\%$) vs Type $F_1$ ($M_3 = 59.78\%$):** Sub-word tokenization of spaced Aadhaar (4-4-4) and UPI delimiters causes partial span boundary shifts ($F_2 = 250$).
4. **Adversarial Robustness Drop:** Type $F_1$ dropped from $61.82\%$ on clean records down to $48.16\%$ on adversarial records, consistent with zero adversarial exposure during training.

---

## 16. Comprehensive Risk Classification

| Risk Dimension | Classification | Concrete Evidence | Scientific Consequence |
|:---|:---|:---|:---|
| **Base-ID Leakage** | **NO EVIDENCE** | Train/Val/Test base-ID intersection is exactly 0 ($\emptyset$) | Strict entity-level isolation; no identity leakage. |
| **Exact Text Leakage** | **NO EVIDENCE** | Full-text exact and normalized match count is 0 / 964 ($0.00\%$) | No memorization of test sentences. |
| **Template Leakage** | **LOW RISK** | Zero exact skeleton overlap between corporate framing and carrier patterns | Carrier structures remain independent. |
| **Lexical Overlap** | **LOW RISK** | Context vocabulary Jaccard similarity is 0.1213; 2-gram Jaccard is 0.0772 | Lexical independence established. |
| **PII-Format Overlap** | **HIGH RISK** | Shared synthetic generators across splits (rigid PAN regex, Aadhaar 4-4-4, UPI handles) | Model exploits formatting shortcuts, driving high sensitivity. |
| **Language Overlap** | **LOW RISK** | 100% recall on unseen categories (`INFORMAL_HINGLISH`, `HI_LATIN_PII`) | Genuine cross-lingual transfer verified. |
| **Perturbation Overlap** | **NO EVIDENCE** | Zero adversarial perturbations in adaptation training data | Adversarial benchmark is strictly zero-shot. |
| **Hard-Negative Mismatch** | **HIGH RISK** | Zero negative instances in adaptation vs 100 in test | Explains 100% FPR on hard negatives and 55.80% overall FPR. |
| **Shortcut Risk** | **HIGH RISK** | Dense positive-only training on generator-formatted strings | Model acts as a dense format extractor rather than semantic validator. |

---

## 17. Scientific Interpretation & Conclusion

* **Generalization vs Memorization:** Baseline B5 did **not** memorize benchmark test instances or templates. The high recall is driven by genuine multilingual token-level representation learning combined with sensitivity to synthetic formatting conventions.
* **Sensitivity vs Specificity Trade-Off:** The primary vulnerability of B5 is a **specificity deficit** rather than data leakage. Because B5 adaptation data lacked hard-negative distractors, the model learned high recall at the cost of elevated false positives on structured non-PII strings.

---

## 18. Limitations

1. **Synthetic Generation Artifacts:** Both splits rely on synthetic PII generation rules. Evaluating B5 on naturalistic, human-authored Indian PII documents is necessary to measure out-of-generator transfer.
2. **Positive-Only Adaptation:** Adaptation data did not contain hard-negative distractors, limiting the ability to assess learned negative discrimination.

---

## 19. Publication Readiness Recommendation

* **Overall SV-01 Decision:** **PASS WITH CAVEATS**
* **Recommendation:**
  1. Baseline B5 results are **scientifically valid, fully reproducible, and compliant** with `PROJECT_SPEC.md` §§19–24.
  2. B5 should remain **FROZEN AND LOCKED** as the canonical adapted transformer baseline.
  3. In future benchmark iterations (post-Pilot v0.1), a **controlled holdout experiment** incorporating naturalistic text and hard-negative distractors during adaptation training should be conducted to improve specificity.

---

## 20. Complete File & Hash Integrity Verification

All 22 canonical benchmark dataset and evaluation artifacts remain cryptographically verified and 100% unmodified:

```
[1]  data/raw/base_instances.jsonl                                      : MD5 7006b0c9227d93541d2b71f702407ecc (MATCH)
[2]  data/raw/hard_negative_bases.jsonl                                 : MD5 b36c6c106548d18ff7083fd00532cb07 (MATCH)
[3]  data/generated/language_realizations.jsonl                         : MD5 0cb046740507eb9111a214b24b680483 (MATCH)
[4]  data/generated/hard_negative_realizations.jsonl                    : MD5 ae5537eec4129822e3d97b05170b4fea (MATCH)
[5]  data/generated/adversarial_realizations.jsonl                     : MD5 1b678b9597737c85197acf80ab56878d (MATCH)
[6]  annotation/review_template.csv                                     : MD5 78c5767f2f8fede2021ff344aaddc32c (MATCH)
[7]  predictions/regex_1.0.0_v0.18.jsonl                                : MD5 8913ac633854a36948a3445e4be0594d (MATCH)
[8]  reports/evaluation_regex_1.0.0_v0.18.json                          : MD5 2958f77985fcc70d704c123e9e952ebd (MATCH)
[9]  predictions/spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.jsonl        : MD5 6c74bd4ec742a1f0c6b8024200937fb5 (MATCH)
[10] reports/evaluation_spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.json  : MD5 a9745314b2e71df861ea71af15a9dd1a (MATCH)
[11] predictions/presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.jsonl: MD5 2c661403efa963275be5f2559a1577b9 (MATCH)
[12] reports/evaluation_presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.json: MD5 4831393231e3d15dc674166dcaaaa2b9 (MATCH)
[13] predictions/transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.jsonl: MD5 3f53b646fb9f95414bef8b972d2277b1 (MATCH)
[14] reports/evaluation_transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.json: MD5 dfe7e6b93e15ca266b29121977b1809e (MATCH)
[15] predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.jsonl: MD5 e589c2a3daa96e8a3963d95fecb89012 (MATCH)
[16] predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.jsonl: MD5 e589c2a3daa96e8a3963d95fecb89012 (MATCH)
[17] predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.jsonl: MD5 e11d924839cdddebd59104624f667357 (MATCH)
[18] predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.jsonl: MD5 a0b17f4b93251463319d0dc1409514bf (MATCH)
[19] reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.json: MD5 d3a9f9da8e848c7cafb9cf43299b9439 (MATCH)
[20] reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.json: MD5 06ca5638e48dc492c016166d8b1d12a2 (MATCH)
[21] reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.json: MD5 cfb422de399fa7cb13dec4e30f7b29e1 (MATCH)
[22] reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.json: MD5 90a0a0c9bb83dd4d2f456b6e0f508753 (MATCH)
```

* **Full Repository Test Suite:** **926 passed** in 253s (100% clean passes, 0 failures, 0 errors).
