# Indian PII Robustness Benchmark — Authoritative Limitations Register
**Document Identifier**: `REPORTS-FINAL-LIMITATIONS-V1.0`  
**Benchmark Version**: `0.18`  
**Evaluation Scope**: Baselines B1–B6 and Scientific Validations  
**Date**: September 9, 2026  
**Status**: APPROVED & LOCKED  

---

## 1. Purpose and Governance

Scientific integrity requires transparent, rigorous accounting of benchmark boundaries, experimental scope constraints, and residual technical limitations. This document serves as the authoritative limitations register for the Indian PII Robustness Benchmark and the final Baseline B6 system.

---

## 2. Benchmark Corpus & Data Generation Limitations

### 2.1 Synthetic Base Construction
- **Scope**: To strictly guarantee zero private data leakage and conform to Indian privacy statutes (e.g., Digital Personal Data Protection Act 2023), all 964 evaluation records were synthetically generated using rule-guided templates and controlled perturbation operators.
- **Limitation**: While synthetic generation allows precise ground-truth offset labeling, real-world Indian text contains unmodeled physical artifacts, handwritten notes, scanning skew, camera capture glare, and unpredictable document layouts that are absent from clean text corpora.

### 2.2 Linguistic Scope & Language Representation
- **Covered Languages**: The benchmark evaluates English (EN), Hinglish (Code-Mixed Latin), Hindi Devanagari (HI_DEVA_PII), Hindi Latin Transliterated (HI_LATN_PII), and Mixed Script (MIXED).
- **Unrepresented Languages**: Major Indian linguistic families—specifically Dravidian languages (Tamil, Telugu, Kannada, Malayalam), Eastern Indo-Aryan languages (Bengali, Assamese, Odia), and Western Indic languages (Marathi, Gujarati, Punjabi)—are not yet represented in the canonical test set. Performance cannot be assumed to generalize across non-Hindi Indic scripts without targeted empirical validation.

### 2.3 Domain Specialization
- **Covered Domains**: Administrative, banking/KYC, telecommunications, and conversational e-commerce dialogues.
- **Uncovered Domains**: Specialized professional domains such as clinical healthcare records, electronic medical records (EMR), court legal judgements, and land revenue records feature distinct terminological and syntactical conventions not evaluated by this benchmark.

---

## 3. Modeling & Algorithmic Limitations

### 3.1 Sub-Word Tokenizer Fragility under A1 Whitespace Perturbation
- **Mechanism**: The underlying multilingual encoder (XLM-RoBERTa) relies on a SentencePiece BPE tokenizer trained on whitespace-separated words. When internal spaces are inserted into structured identifiers (e.g., `5 4 8 2 1 2 0 4 9 8 3 1`), the tokenizer shatters the string into 12 distinct isolated tokens.
- **Empirical Impact**: Baseline B6's exact boundary F1 plunges from **$0.7812$** on clean instances to **$0.2941$** on A1 whitespace perturbations. Even with sequence transition constraints, the model struggles to link disconnected single-digit tokens across whitespace boundaries.
- **Remediation Frontier**: Future architectures must incorporate byte-level or character-aware encoders (e.g., Canine, ByT5) or character-level convolutional pre-tokenizers.

### 3.2 Persistent Decoy Susceptibility (Hard-Negative Over-Extraction)
- **Mechanism**: Both B5 and B6 exhibit a **$100.0\%$ record-level False Positive Rate** on the 50 held-out pure hard-negative decoy records.
- **Empirical Impact**: When an arbitrary 12-digit number (e.g., tracking code, order reference number) appears in a sentence without explicit negative disclaimers, the encoder flags it as an `AADHAAR` entity based solely on alphanumeric shape, ignoring non-PII contextual cues.
- **Remediation Frontier**: Contrastive sequence-level negative pretraining or downstream checksum validation layers (e.g., Verhoeff algorithm for Aadhaar) are necessary to eliminate decoy false positives.

### 3.3 Locality of Linear Chain CRF Transitions
- **Mechanism**: First-order Linear Chain CRFs model only pairwise transitions between adjacent token labels ($y_{i-1} \to y_i$).
- **Limitation**: They cannot capture long-range semantic dependencies, document-level entity consistency, or global cardinality constraints (e.g., ensuring an individual record does not contain multiple conflicting PAN numbers).

---

## 4. Evaluation & Statistical Limitations

### 4.1 Adaptation Seed Cardinality ($N=3$)
- **Scope**: Baselines B5 and B6 were trained and evaluated across three designated random seeds ($42, 43, 44$).
- **Limitation**: While standard deviations across these three seeds are extremely narrow ($\sigma = 0.0034$ for exact F1, $\sigma = 0.0021$ for precision), establishing formal non-parametric statistical significance ($p < 0.05$) requires larger seed cohorts ($N \ge 10$).
- **Reporting Requirement**: All findings are certified as *"supported consistently across three seeds"* rather than *"statistically significant"*.

### 4.2 Strict Character Offset Metrics
- **Limitation**: Exact F1 ($M_4$) requires perfect character boundary alignment. In instances where an entity is preceded or followed by punctuation (e.g., `"Contact: +919876543210."`), predicting the trailing period as part of the entity incurs a full boundary error penalty ($F_2$). While strict scoring is essential for scientific benchmarking, real-world redaction pipelines may tolerate minor punctuation padding.

---

## 5. Deployment, Operational & Privacy Considerations

### 5.1 Precision-Recall Asymmetry in Automated Redaction
- **Operational Reality**: Baseline B6 achieves **$0.9319$ Recall** with **$0.6315$ Precision**.
- **Risk Assessment**:
  - *Data Protection Perspective*: High recall ensures that over 93% of sensitive Indian PII entities are successfully detected and suppressed.
  - *Usability Perspective*: Moderate precision means that approximately 37% of emitted predictions are false positives. In automated production workflows, this leads to over-redaction of non-sensitive contextual terms (e.g., order numbers, postal codes, product references).
- **Recommendation**: B6 should be deployed with human-in-the-loop review for high-consequence administrative processing, or coupled with deterministic post-processing validators.

### 5.2 Adversarial Manipulation Risk
- Malicious users aware of tokenizer whitespace sensitivity could deliberately insert spaces or zero-width joiners into PII to evade automated compliance filters. Defense-in-depth requires regex pre-normalization prior to neural inference.
