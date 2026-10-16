# Baseline B1 (Regex) Experimental Evaluation Summary

**Benchmark Version:** Indian PII Robustness Benchmark (Pilot v0.1 / Guidelines v0.18)  
**System Evaluated:** `RegexBaselineAdapter` (B1, v1.1.0)  
**Corpus Evaluated:** 964 canonical records (724 gold PII entities, 140 non-PII hard-negative instances)  
**Evaluation Status:** **FROZEN & FULLY REPRODUCIBLE**

---

## 1. Executive Summary

Baseline **B1 (Regex)** represents the structured-identifier ceiling and heuristic rule benchmark for Indian PII detection. Evaluated across 964 benchmark instances in 7 language/script conditions and 5 adversarial perturbation families, B1 achieved an overall **Type-Strict $F_1$ of 81.54%** (Precision: **79.87%**, Recall: **83.29%**).

While B1 demonstrates high accuracy on rigidly structured alphanumeric identifiers in Latin script (Email: **91.95%**, Phone: **89.41%**, UPI: **88.78%**, PAN: **88.42%**), it exhibits severe vulnerabilities when exposed to Indic scripts (Devanagari: **0.00%**), adversarial noise ($A_1$ Spacing: **0.00%**, $A_2$ Punctuation: **29.63%**), and lookalike distractor numbers.

---

## 2. Headline Performance Metrics

| Metric | Code | Exact Fraction | Percentage | Interpretation |
|---|---|---|---|---|
| **Precision** | $M_1$ | $603 / 755$ | **79.87%** | 79.87% of detected entities are genuine PII of correct type. |
| **Recall** | $M_2$ | $603 / 724$ | **83.29%** | Recovers 83.29% of all gold PII instances. |
| **Type-Strict $F_1$** | $M_3$ | $2 \cdot \frac{603}{755 + 724}$ | **81.54%** | Primary benchmark headline metric. |
| **Exact-Boundary $F_1$** | $M_4$ | $2 \cdot \frac{601}{755 + 724}$ | **81.27%** | Requires character-for-character exact boundary alignment. |
| **Type Accuracy** | $M_5$ | $603 / 606$ | **99.50%** | When a span is localized, type classification is 99.50% accurate. |
| **False Positive Rate** | $M_6$ | $149 / 755$ | **19.74%** | 19.74% of emitted predictions are false alarms. |

---

## 3. Performance by PII Type

| PII Type | Gold Count | Detections | Correct ($\text{TP}$) | Precision | Recall | $F_1$ Score | Primary Behavior |
|---|---|---|---|---|---|---|---|
| **EMAIL** | 82 | 92 | 80 | 86.96% | 97.56% | **91.95%** | RFC syntax matches reliably |
| **PHONE** | 82 | 88 | 76 | 86.36% | 92.68% | **89.41%** | Strong 10-digit mobile detection |
| **UPI_ID** | 93 | 103 | 87 | 84.47% | 93.55% | **88.78%** | Broad VPA and domain coverage |
| **PAN** | 93 | 97 | 84 | 86.60% | 90.32% | **88.42%** | Rigid 10-character alphanumeric format |
| **ADDRESS** | 94 | 88 | 76 | 86.36% | 80.85% | **83.52%** | Multi-part structural address pattern |
| **AADHAAR** | 93 | 81 | 68 | 83.95% | 73.12% | **78.16%** | Spaced and contextual 12-digit rules |
| **BANK_ACCOUNT** | 93 | 81 | 68 | 83.95% | 73.12% | **78.16%** | Contextual 9–18 digit sequences |
| **PERSON** | 94 | 76 | 64 | 84.21% | 68.09% | **75.29%** | Misses unlabelled names and Devanagari |

---

## 4. Performance Across Language & Script Conditions

| Language / Condition | Script | Gold Count | Precision | Recall | $F_1$ Score | Key Finding |
|---|---|---|---|---|---|---|
| **Indian English (`IN_EN`)** | Latin | 100 | 93.46% | 100.00% | **96.62%** | Clean Latin carrier |
| **Romanized Hindi (`ROM_HI`)** | Latin | 100 | 93.46% | 100.00% | **96.62%** | Handled via Romanized triggers |
| **Hinglish (`HINGLISH`)** | Latin | 100 | 93.46% | 100.00% | **96.62%** | Code-mixing handled when Latin |
| **Informal Hinglish (`INFORMAL_HINGLISH`)** | Latin | 100 | 93.46% | 100.00% | **96.62%** | Slang particles ignored cleanly |
| **Standard English (`EN`)** | Latin | 200 | 93.38% | 70.50% | **80.34%** | Canonical English baseline |
| **Hindi w/ Latin PII (`HI_LATIN_PII`)** | Devanagari | 100 | 89.86% | 62.00% | **73.37%** | Devanagari context words unparsed |
| **Hindi w/ Deva PII (`HI_DEVA_PII`)** | Devanagari | 24 | 0.00% | 0.00% | **0.00%** | **Total blindness to Devanagari script** |

---

## 5. Adversarial Robustness ($A_1$–$A_5$)

| Perturbation Family | Description | Gold Count | $F_1$ Score | Severity & Analysis |
|---|---|---|---|---|
| **$A_1$ SPACING** | Inter-character whitespace (`S n e h a`) | 20 | **0.00%** | **Catastrophic Failure**: Regex token boundaries break completely. |
| **$A_2$ PUNCTUATION** | Structural delimiters / hyphens | 20 | **29.63%** | **Severe Degradation**: Internal punctuation truncates spans. |
| **$A_5$ CHAR_VARIATION** | Single-glyph OCR substitution (`0` $\rightarrow$ `O`) | 20 | **51.85%** | **Moderate Degradation**: Rigid character classes fail on glyph errors. |
| **$A_3$ LABEL_OBFUSCATION** | Punctuation in label (`My P.A.N. No:`) | 20 | **75.00%** | Survives on self-contained identifiers; fails on context-dependent. |
| **$A_4$ INFORMAL_ABBREVIATION** | Shortened label (`pan no:`) | 20 | **94.74%** | Captures abbreviated contextual triggers (`name:`, `pan no:`). |

---

## 6. Hard-Negative Distractor Vulnerability

When evaluated on 140 non-PII records containing realistic distractors:
* **Alphanumeric Shape Distractors (`ALNUM_SHAPE`)**: 30 false positives. Reference codes (e.g. `UFRXH2764U`) are falsely classified as `PAN`.
* **Numeric Shape Distractors (`NUMERIC_SHAPE`)**: 12 false positives. 10-digit order references (e.g. `6043321819`) are falsely classified as `PHONE`.
* **Takeaway**: Regex rules lack semantic role awareness and trigger high false alarm rates on lookalike business references.

---

## 7. Primary Error Breakdown ($F_1$–$F_4$)

* **$F_1$ Missed PII (118 instances / 16.30%)**: Undetected entities (Devanagari text, adversarial spacing).
* **$F_2$ Wrong Span (2 instances / 0.28%)**: Partial span matches on hyphenated tokens.
* **$F_3$ Wrong Type (3 instances / 0.41%)**: Type confusion on ambiguous mutated identifiers.
* **$F_4$ False Positives (149 instances)**: False alarms on non-PII text and distractors.

---

## 8. Benchmark Artifact Locations

* **Predictions Artifact**: `predictions/regex_1.1.0_v0.18.jsonl` (MD5: `2f4a56a59b660c6d99723ec0b0aa8c12`)
* **Machine-Readable Report**: `reports/evaluation_regex_1.1.0_v0.18.json` (MD5: `ee38dd94ff8a34bbcd92080a0aa15518`)
