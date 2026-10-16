# Comprehensive Baseline Comparison: B1 through B6

## 1. Executive Summary of Benchmark Progression

The Indian PII Robustness Benchmark systematically evaluates six distinct paradigm baselines across 964 canonical records containing 724 gold standard Indian PII entities under linguistic diversity (English, Hinglish, Hindi Devanagari, Hindi Latin, and Code-Mixed) and realistic synthetic perturbations (whitespace insertion, phonetic distortion, OCR noise, script mixing, and delimiter noise).

Across iterations B1 to B6, the benchmark uncovered critical failure modes in off-the-shelf and zero-shot architectures, resolved structural boundary degradation through transition-constrained decoding, and quantitatively mapped the residual frontiers of Indian PII extraction.

## 2. Baseline Architecture Overview

1. **B1 Regex (v1.0.0, locked canonical)**: Hand-engineered regular expressions for structured Indian PII (Aadhaar, PAN, Phone, Email). Rigid, high precision on clean canonical patterns ($M_1 = 0.6478$, exact $F_1 = 0.5773$), but completely fails on unstructured entities (Name) and perturbed inputs.
2. **B2 spaCy (`en_core_web_sm` v3.8.16)**: Off-the-shelf English statistical/neural pipeline. Severe domain mismatch ($M_1 = 0.0315$, $M_4 = 0.0330$), producing 883 false positives and failing to recognize Indic entity syntaxes.
3. **B3 Microsoft Presidio (v2.2.364 with IN recognizers)**: Standard industrial hybrid framework combining rules and spaCy context. Modest recall ($M_2 = 0.2956$) but severe over-extraction ($M_6 = 0.7539$, 2,105 false positives), demonstrating that standard global PII toolkits cannot be safely deployed without deep Indic domain adaptation.
4. **B4 Zero-Shot XLM-RoBERTa (`Davlan/xlm-roberta-base-ner-hrl`)**: Pretrained massively multilingual model. Cross-lingual zero-shot transfer yields poor recall ($M_2 = 0.1298$, $M_4 = 0.1444$) due to lack of exposure to Indian identifier schemas.
5. **B5 Indian-Adapted XLM-RoBERTa (v5.16.1)**: Fine-tuned on Indian PII adaptation corpus with independent linear classification head. Achieves near-perfect entity localization recall ($M_2 = 0.9742 \pm 0.0008$, type-strict $F_1 = 0.5978 \pm 0.0024$), but suffers severe exact-boundary collapse ($M_4 = 0.3860 \pm 0.0050$) caused by independent token decoding, yielding 250.0 boundary truncation errors and 912.7 false positives.
6. **B6 Indian-Adapted XLM-RoBERTa + Linear CRF (v5.16.1)**: Adds a first-order Linear Chain CRF decoding layer enforcing BIO sequence transition validity. Resolves the boundary collapse: $M_4$ exact $F_1$ rises by **+0.2795** (+72.4% relative, reaching $0.6654 \pm 0.0034$), precision surges to $0.6315 \pm 0.0021$, boundary errors drop by 68.7% (to 78.3), and duplicate sub-token extractions drop by 90.9%.

## 3. Comparative Metric Synthesis

| Baseline | Paradigm | M1 Prec | M2 Rec | M3 F1 (Type) | M4 Exact F1 | M6 FPR | $TP_{exact}$ | $F_2$ (Boundary) | $F_4$ (FP) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **B1** Regex (Canonical) | Single-run | 0.6478 | 0.5207 | 0.5773 | **0.5773** | 0.2371 | 377.0 | 0.0 | 138.0 |
| **B2** spaCy en_core_web_sm | Single-run | 0.0315 | 0.0608 | 0.0415 | **0.0330** | 0.6316 | 35.0 | 9.0 | 883.0 |
| **B3** Microsoft Presidio (IN enabled) | Single-run | 0.0766 | 0.2956 | 0.1217 | **0.1149** | 0.7539 | 202.0 | 12.0 | 2105.0 |
| **B4** XLM-RoBERTa Zero-Shot NER | Single-run | 0.2013 | 0.1298 | 0.1579 | **0.1444** | 0.6039 | 86.0 | 8.0 | 282.0 |
| **B5** Indian-Adapted XLM-RoBERTa | 3-seed Mean | 0.4312 | 0.9742 | 0.5978 | **0.3860** | 0.5580 | 455.3 | 250.0 | 912.7 |
| **B6** Indian-Adapted XLM-RoBERTa + Linear CRF | 3-seed Mean | 0.6315 | 0.9319 | 0.7528 | **0.6654** | 0.3292 | 596.3 | 78.3 | 351.7 |

## 4. Key Scientific Transitions & Lessons

- **Domain Adaptation is Indispensable**: Pretrained zero-shot models (B4) achieve only 0.1444 exact F1. Task adaptation (B5) lifts recall from 0.1298 to 0.9742.
- **Independent Token Heads Cause Boundary Collapse**: In B5, lack of transition constraints allowed sub-word tokens to be omitted or emitted spuriously ($FP_9 = 351.3$), crippling exact boundary precision.
- **Sequence-Constrained Decoding Solves Boundary Truncation**: B6's CRF layer eliminates illegal transition states ($O \to I$, cross-type boundaries), restoring 151 boundary error entities to exact True Positives (in seed 42) and dropping false positives from 912.7 to 351.7.
- **Persistent Frontiers**: Both B5 and B6 retain elevated FPR on held-out hard negative decoy numbers (random 12-digit and 10-digit non-PII strings) and experience boundary degradation under A1 whitespace perturbation, defining the primary technical agenda for future work.
