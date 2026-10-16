# Indian PII Robustness Benchmark — Baseline B3 (Microsoft Presidio) Evaluation Report & Cross-Baseline Comparison

**Benchmark Target:** Baseline `B3` — Microsoft Presidio Production Framework Baseline  
**System Evaluated:** `PresidioBaselineAdapter`  
**System Name:** `presidio`  
**System Version:** `2.2.364_en_core_web_sm_in_enabled`  
**Benchmark Corpus:** Canonical 964-record benchmark dataset (724 gold PII entities across 8 taxonomy categories + 140 hard-negative distractor instances)  
**Governing Documents:** `PROJECT_SPEC.md` §§19–24 (v1.3), `annotation/guidelines.md` (v0.18), `annotation/open_questions.md`  
**Status:** **OFFICIALLY LOCKED BENCHMARK RESULT**

---

## 1. B3 Overall Benchmark Results

All metrics are extracted directly from the canonical report `reports/evaluation_presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.json` and conform strictly to the mathematical definitions in `PROJECT_SPEC.md` §20.4:

| Metric / Dimension | Symbol | Mathematical Formulation | Evaluated Decimal | Percentage / Count |
|---|---|---|---|---|
| **Total Gold Entities** | $N_{\text{gold}}$ | $|\text{Gold}|$ | `724` | **724** |
| **Total Emitted Predictions** | $N_{\text{pred}}$ | $|\text{Pred}|$ | `2792` | **2,792** (0 rejected) |
| **Localized Entities** | $|L|$ | $\text{Gold} \cap \{\text{IoU} \ge 0.5\}$ | `687` | **687** ($94.89\%$ localized) |
| **Type-Strict True Positives** | $\text{TP}_{\text{type}}$ | Localized & Correct Type | `214` | **214** |
| **Exact-Boundary True Positives** | $\text{TP}_{\text{exact}}$ | Localized, Correct Type & $\text{IoU} = 1.0$ | `202` | **202** |
| **Missed Entities** | $F_1$ | $\text{IoU} < 0.5$ to any prediction | `37` | **37** ($5.11\%$ of gold) |
| **Wrong Span / Boundary Shift** | $F_2$ | Localized, correct type, $\text{IoU} < 1.0$ | `12` | **12** ($1.66\%$ of gold) |
| **Wrong Type / Mislabeled** | $F_3$ | Localized, incorrect type | `473` | **473** ($65.33\%$ of gold) |
| **Unmatched False Positives** | $F_4$ | $\text{IoU} < 0.5$ to any gold entity | `2105` | **2,105** |
| **$M_1$ Entity Precision** | $M_1$ | $\frac{\text{TP}_{\text{type}}}{N_{\text{pred}}}$ | `0.0766475645` | **7.66%** |
| **$M_2$ Entity Recall** | $M_2$ | $\frac{\text{TP}_{\text{type}}}{N_{\text{gold}}}$ | `0.2955801105` | **29.56%** |
| **$M_3$ Type-Strict $F_1$** | $M_3$ | $\frac{2 \times \text{TP}_{\text{type}}}{N_{\text{pred}} + N_{\text{gold}}}$ | `0.1217292378` | **12.17%** |
| **$M_4$ Exact-Boundary $F_1$** | $M_4$ | $\frac{2 \times \text{TP}_{\text{exact}}}{N_{\text{pred}} + N_{\text{gold}}}$ | `0.1149032992` | **11.49%** |
| **$M_5$ Type Accuracy** | $M_5$ | $\frac{\text{TP}_{\text{type}}}{|L|}$ | `0.3114992722` | **31.15%** |
| **$M_6$ False Positive Rate** | $M_6$ | $\frac{F_4}{N_{\text{pred}}}$ | `0.7539398281` | **75.39%** |

### Error Partition Identity Verification:
$$\sum \text{Gold Dispositions} = F_1 \text{ (Missed)} + F_2 \text{ (Wrong Span)} + F_3 \text{ (Wrong Type)} + \text{TP}_{\text{exact}} \equiv N_{\text{gold}}$$
$$37 + 12 + 473 + 202 = 724 \equiv 724 \quad (\checkmark \text{ Mathematically Exact})$$

---

## 2. B3 Benchmark Results by PII Type

| PII Taxonomy Type | $N_{\text{gold}}$ | $N_{\text{pred}}$ | $\text{TP}_{\text{type}}$ | $\text{TP}_{\text{exact}}$ | $M_1$ Precision | $M_2$ Recall | $M_3$ $F_1$ | $M_4$ Exact $F_1$ | $M_5$ Type Acc | $M_6$ FPR | $F_1$ | $F_2$ | $F_3$ | $F_4$ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **PAN** | 93 | 228 | 90 | 87 | **39.47%** | **96.77%** | **56.07%** | **54.21%** | **98.90%** | 60.09% | 2 | 3 | 1 | 137 |
| **PERSON** | 94 | 111 | 44 | 35 | **39.64%** | **46.81%** | **42.93%** | **34.15%** | **63.77%** | 37.84% | 25 | 9 | 25 | 42 |
| **PHONE** | 82 | 427 | 80 | 80 | **18.74%** | **97.56%** | **31.43%** | **31.43%** | **97.56%** | 80.80% | 0 | 0 | 2 | 345 |
| **AADHAAR** | 93 | 397 | 0 | 0 | **0.00%** | **0.00%** | **0.00%** | **0.00%** | **0.00%** | 77.08% | 2 | 0 | 91 | 306 |
| **EMAIL** | 82 | 197 | 0 | 0 | **0.00%** | **0.00%** | **0.00%** | **0.00%** | **0.00%** | 61.42% | 6 | 0 | 76 | 121 |
| **BANK_ACCOUNT** | 93 | 313 | 0 | 0 | **0.00%** | **0.00%** | **0.00%** | **0.00%** | **0.00%** | 70.93% | 2 | 0 | 91 | 222 |
| **UPI_ID** | 93 | 502 | 0 | 0 | **0.00%** | **0.00%** | **0.00%** | **0.00%** | **0.00%** | 81.47% | 0 | 0 | 93 | 409 |
| **ADDRESS** | 94 | 381 | 0 | 0 | **0.00%** | **0.00%** | **0.00%** | **0.00%** | **0.00%** | 75.33% | 0 | 0 | 94 | 287 |
| **HARD_NEGATIVE** | 0 | 31 | 0 | 0 | **0.00%** | **0.00%** | **0.00%** | **0.00%** | **0.00%** | 100.00% | 0 | 0 | 0 | 31 |

---

## 3. B3 Results Across Language & Script Conditions

| Language / Realization Condition | Script | $N_{\text{gold}}$ | $N_{\text{pred}}$ | $\text{TP}_{\text{type}}$ | $\text{TP}_{\text{exact}}$ | $M_3$ Type-Strict $F_1$ | $M_4$ Exact $F_1$ | $M_6$ False Positive Rate |
|---|---|---|---|---|---|---|---|---|
| **Hindi w/ Latin PII (`HI_LATIN_PII`)** | Devanagari Carrier / Latin PII | 100 | 297 | 30 | 28 | **15.11%** | 14.11% | 68.01% |
| **Standard English (`EN`)** | Latin | 200 | 569 | 57 | 54 | **14.82%** | 14.04% | 66.96% |
| **Informal Hinglish (`INFORMAL_HINGLISH`)** | Latin | 100 | 324 | 31 | 29 | **14.62%** | 13.68% | 69.75% |
| **Indian English (`IN_EN`)** | Latin | 100 | 353 | 33 | 33 | **14.57%** | 14.57% | 71.95% |
| **Hinglish (`HINGLISH`)** | Latin | 100 | 421 | 32 | 29 | **12.28%** | 11.13% | 76.96% |
| **Romanized Hindi (`ROM_HI`)** | Latin | 100 | 443 | 31 | 29 | **11.42%** | 10.68% | 78.33% |
| **Hindi w/ Deva PII (`HI_DEVA_PII`)** | Devanagari Carrier / Deva PII | 24 | 38 | 0 | 0 | **0.00%** | 0.00% | 63.16% |

---

## 4. B3 Results by Perturbation Family

| Perturbation Family | Target Entity Component | $N_{\text{gold}}$ | $N_{\text{pred}}$ | $\text{TP}_{\text{type}}$ | $\text{TP}_{\text{exact}}$ | $M_3$ $F_1$ | $M_4$ Exact $F_1$ | $M_6$ FPR | Robustness Gap ($\Delta M_3$ vs `NONE`) |
|---|---|---|---|---|---|---|---|---|---|
| **$A_2$ (Punctuation Variation)** | VALUE | 20 | 36 | 6 | 3 | **21.43%** | 10.71% | 47.22% | $+9.53\%$ |
| **$A_4$ (Informal Abbreviations)** | LABEL | 20 | 54 | 7 | 7 | **18.92%** | 18.92% | 62.96% | $+7.02\%$ |
| **$A_3$ (Label Obfuscation)** | LABEL | 20 | 58 | 6 | 6 | **15.38%** | 15.38% | 67.24% | $+3.48\%$ |
| **$A_5$ (Character Substitution)** | VALUE | 20 | 37 | 3 | 3 | **10.53%** | 10.53% | 59.46% | $-1.37\%$ |
| **$A_1$ (Spacing Variations)** | VALUE | 20 | 37 | 2 | 2 | **7.02%** | 7.02% | 56.76% | $-4.88\%$ |
| **`NONE` (Clean Baseline)** | — | 624 | 2570 | 190 | 181 | **11.90%** | 11.33% | 76.73% | *Reference Condition* |

---

## 5. B3 Results by Corpus Difficulty

| Corpus Difficulty Tier | $N_{\text{gold}}$ | $N_{\text{pred}}$ | $\text{TP}_{\text{type}}$ | $\text{TP}_{\text{exact}}$ | $M_3$ Type-Strict $F_1$ | $M_4$ Exact $F_1$ | $M_6$ False Positive Rate |
|---|---|---|---|---|---|---|---|
| **Adversarial (`ADVERSARIAL`)** | 100 | 222 | 24 | 21 | **14.91%** | 13.04% | 59.91% |
| **Easy (`EASY`)** | 200 | 700 | 66 | 66 | **14.67%** | 14.67% | 71.71% |
| **Medium (`MEDIUM`)** | 424 | 1523 | 124 | 115 | **12.74%** | 11.81% | 73.74% |

---

## 6. Detailed Error Profile Analysis

The quantitative evaluation reveals four structural failure mechanisms driving B3 error attribution:

1. **Massive Out-of-Taxonomy False Alarms ($F_4 = 2,105$, $M_6 = 75.39\%$):**
   - Presidio Analyzer runs general global recognizers alongside spaCy NER, emitting 2,026 out-of-taxonomy predictions across the corpus: `DATE_TIME` (645), `US_BANK_NUMBER` (332), `US_DRIVER_LICENSE` (327), `UK_NHS` (308), `ORGANIZATION` (224), `LOCATION` (128), and `URL` (54).
   - Off-the-shelf US and UK identifier recognizers aggressively trigger on standard Indian 10-digit phone numbers and 12-digit numeric sequences.

2. **Dominance of Wrong Type Classifications ($F_3 = 473$, $65.33\%$ of Gold Entities):**
   - **$94.89\%$ of all gold entities ($687 / 724$) are successfully localized** with $\text{IoU} \ge 0.5$, but **473 of them are labeled with incorrect types**.
   - Examples: Indian domestic bank accounts are detected as `US_BANK_NUMBER` or `UK_NHS`; Aadhaar spans are detected as `DATE_TIME`; addresses are segmented into isolated `LOCATION` tokens.

3. **Verhoeff Checksum & Predefined Model Gaps on Aadhaar & Email:**
   - **Aadhaar ($0.00\% \text{ } F_1$):** Presidio's `InAadhaarRecognizer` validates candidate 12-digit numbers using the Verhoeff checksum algorithm and non-palindromic checks. Realized synthetic benchmark instances failing this mathematical checksum are rejected by Presidio and misclassified by other recognizers as `DATE_TIME`.
   - **Email ($0.00\% \text{ } F_1$):** `InPanRecognizer` regex captures the 5-letter + 4-digit prefix of email usernames (e.g. `sneha8298@`), mislabeling the prefix as `PAN` ($F_3$), while `EmailRecognizer` rejects `.test` pseudo-TLDs due to Public Suffix List parsing.

4. **Zero Capability on Unsupported Indian PII Formats:**
   - `UPI_ID` (93 gold) and `BANK_ACCOUNT` (93 gold) achieve $0.00\% \text{ } F_1$ because Presidio Analyzer contains no off-the-shelf domestic Indian recognizers for Virtual Payment Addresses or IFSC/account numbers.

---

## 7. Cross-Baseline Comparative Evaluation (B1 vs B2 vs B3)

| Baseline | System ID & Version | Total Preds | $\text{TP}_{\text{type}}$ | $\text{TP}_{\text{exact}}$ | $M_1$ Precision | $M_2$ Recall | $M_3$ Type-Strict $F_1$ | $M_4$ Exact-Span $F_1$ | $M_5$ Type Accuracy | $M_6$ FPR |
|---|---|---|---|---|---|---|---|---|---|---|
| **B1** | `regex_1.0.0` | **582** | **377** | **377** | **64.78%** | **52.07%** | **57.73%** | **57.73%** | **84.91%** | **23.71%** |
| **B2** | `spacy_3.8.16_en_core_web_sm` | **1398** | **44** | **35** | **3.15%** | **6.08%** | **4.15%** | **3.30%** | **8.54%** | **63.16%** |
| **B3** | `presidio_2.2.364_en_core_web_sm_in_enabled` | **2792** | **214** | **202** | **7.66%** | **29.56%** | **12.17%** | **11.49%** | **31.15%** | **75.39%** |

---

## 8. Baseline Rankings by Primary Evaluation Metrics

* **Rank 1 by $M_3$ Type-Strict $F_1$:** **B1 Regex Baseline** ($57.73\%$)  
  *(Rank 2: B3 Presidio — $12.17\%$; Rank 3: B2 spaCy — $4.15\%$. **Winner: B1**)*
* **Rank 1 by $M_4$ Exact-Boundary $F_1$:** **B1 Regex Baseline** ($57.73\%$)  
  *(Rank 2: B3 Presidio — $11.49\%$; Rank 3: B2 spaCy — $3.30\%$. **Winner: B1**)*
* **Rank 1 by $M_2$ Entity Recall:** **B1 Regex Baseline** ($52.07\%$)  
  *(Rank 2: B3 Presidio — $29.56\%$; Rank 3: B2 spaCy — $6.08\%$. **Winner: B1**)*
* **Rank 1 by $M_1$ Entity Precision:** **B1 Regex Baseline** ($64.78\%$)  
  *(Rank 2: B3 Presidio — $7.66\%$; Rank 3: B2 spaCy — $3.15\%$. **Winner: B1**)*
* **Rank 1 by $M_6$ Lowest False Positive Rate:** **B1 Regex Baseline** ($23.71\%$)  
  *(Rank 2: B2 spaCy — $63.16\%$; Rank 3: B3 Presidio — $75.39\%$. **Winner: B1**)*

---

## 9. Key Evidence-Based Research Findings

1. **B1 Pure Regex Substantially Outperforms Production Presidio and spaCy NER:**
   - Pure structural regular expressions (B1) achieve $M_3 = 57.73\%$, nearly $5\times$ the $F_1$ score of Microsoft Presidio ($12.17\%$) and nearly $14\times$ the $F_1$ of spaCy NER ($4.15\%$).
2. **Presidio Successfully Bridges `PAN`, `PHONE`, and `PERSON` Across Modalities:**
   - Presidio recovers $96.77\%$ of `PAN` entities ($F_1 = 56.07\%$) and $97.56\%$ of `PHONE` entities ($F_1 = 31.43\%$) via its built-in rule engines, while simultaneously retaining spaCy's `PERSON` entity detection ($46.81\%$ recall, $F_1 = 42.93\%$).
3. **Severe Global Recognizer Cross-Talk in Off-the-Shelf Production Frameworks:**
   - Presidio emits 2,792 total predictions across 964 records ($75.39\%$ FPR), driven by foreign ID recognizers (`US_BANK_NUMBER`, `US_DRIVER_LICENSE`, `UK_NHS`) triggering indiscriminately on Indian numeric sequences.
4. **Localizing vs Typing Disconnect ($M_2$ vs $M_5$):**
   - Presidio achieves a very high localization rate ($687 / 724 = 94.89\%$), but type accuracy among localized spans is only $31.15\%$ because $65.33\%$ of gold spans are mislabeled ($F_3 = 473$).
5. **Vulnerability to Spacing Perturbations ($A_1$):**
   - Spacing variations in structured tokens ($A_1$) cause Presidio's $F_1$ to drop from $11.90\%$ (clean) down to $7.02\%$ ($\Delta = -4.88\%$), demonstrating that whitespace tokenization breaks built-in regex recognizers.
6. **Total Failure on Devanagari Script PII (`HI_DEVA_PII`):**
   - All three baselines (B1, B2, B3) achieve $0.00\% \text{ } F_1$ on Devanagari script PII, confirming that existing production tools lack native Indic script entity extraction.

---

## 10. Integrity & Reproducibility Verification

All 12 canonical datasets, review templates, and experimental baseline artifacts remain 100% byte-identical and cryptographically verified:

```
data/raw/base_instances.jsonl                                      : MD5 7006b0c9227d93541d2b71f702407ecc (MATCH)
data/raw/hard_negative_bases.jsonl                                 : MD5 b36c6c106548d18ff7083fd00532cb07 (MATCH)
data/generated/language_realizations.jsonl                         : MD5 0cb046740507eb9111a214b24b680483 (MATCH)
data/generated/hard_negative_realizations.jsonl                    : MD5 ae5537eec4129822e3d97b05170b4fea (MATCH)
data/generated/adversarial_realizations.jsonl                     : MD5 1b678b9597737c85197acf80ab56878d (MATCH)
annotation/review_template.csv                                     : MD5 78c5767f2f8fede2021ff344aaddc32c (MATCH)
predictions/regex_1.0.0_v0.18.jsonl                                : MD5 8913ac633854a36948a3445e4be0594d (MATCH)
reports/evaluation_regex_1.0.0_v0.18.json                          : MD5 2958f77985fcc70d704c123e9e952ebd (MATCH)
predictions/spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.jsonl        : MD5 6c74bd4ec742a1f0c6b8024200937fb5 (MATCH)
reports/evaluation_spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.json  : MD5 a9745314b2e71df861ea71af15a9dd1a (MATCH)
predictions/presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.jsonl: MD5 2c661403efa963275be5f2559a1577b9 (MATCH)
reports/evaluation_presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.json: MD5 4831393231e3d15dc674166dcaaaa2b9 (MATCH)
```

* **Full Pytest Suite:** **887 passed in 32.13s** (100% pass across all unit, governance, and reproducibility tests).
