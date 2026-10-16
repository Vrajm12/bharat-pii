# Baseline Architectures & System Taxonomy Guide
**Document Identifier**: `DOCS-BASELINES-V1.0`  
**Benchmark Version**: `0.18`  
**Status**: APPROVED  
**Date**: September 9, 2026  

---

## 1. Overview of Evaluated Baseline Paradigms

The benchmark evaluates six baseline systems spanning deterministic rule engines, off-the-shelf industrial tools, zero-shot multilingual foundation models, and Indian-adapted neural sequence decoders.

```
Evaluated Baseline Paradigms
├── Single-Run Baselines (Deterministic / Pretrained)
│   ├── B1: Canonical Regex Engine (v1.0.0)
│   ├── B2: spaCy en_core_web_sm Pipeline (v3.8.16)
│   ├── B3: Microsoft Presidio Analyzer with Indian Recognizers (v2.2.364)
│   └── B4: Zero-Shot Multilingual XLM-RoBERTa (Davlan/xlm-roberta-base-ner-hrl)
└── Three-Seed Adapted Experiments (Seeds 42, 43, 44)
    ├── B5: Indian-Adapted XLM-RoBERTa (Independent Token Classification Head)
    └── B6: Indian-Adapted XLM-RoBERTa + Linear Chain CRF (Sequence Decoding Head)
```

---

## 2. Detailed Baseline Specifications

### Baseline B1: Canonical Regular Expression Engine
- **System Name**: `regex`
- **Version**: `1.0.0`
- **Architecture**: Hand-crafted deterministic regular expressions targeting standard Aadhaar, PAN, Phone, and Email syntaxes.
- **Evaluation Mode**: Single-run (deterministic).
- **Training / Adaptation**: None (rule-based).
- **Dependencies**: Python standard library `re` or `regex`.
- **Artifact Location**: `reports/evaluation_regex_1.0.0_v0.18.json`, `predictions/regex_1.0.0_v0.18.jsonl`.
- **Intended Interpretation**: Represents upper-bound precision for rigid, unperturbed alphanumeric patterns, but completely lacks capability on unstructured entities (Name) and perturbed/code-mixed inputs.

---

### Baseline B2: spaCy Statistical Pipeline
- **System Name**: `spacy`
- **Version**: `3.8.16` (model: `en_core_web_sm` v3.8.0)
- **Architecture**: CNN transition-based parser trained on English OntoNotes 5.0.
- **Evaluation Mode**: Single-run (pretrained).
- **Training / Adaptation**: Off-the-shelf zero-shot evaluation without Indic adaptation.
- **Dependencies**: `spacy==3.8.16`, `en_core_web_sm==3.8.0`.
- **Artifact Location**: `reports/evaluation_spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.json`.
- **Intended Interpretation**: Demonstrates the acute failure of applying standard Western NLP pipelines to Indic multilingual text ($M_1 = 0.0315$, $M_4 = 0.0330$, $883$ false positives).

---

### Baseline B3: Microsoft Presidio Framework
- **System Name**: `presidio`
- **Version**: `2.2.364`
- **Architecture**: Hybrid industrial framework combining regular expressions, checksum validators, and spaCy context recognizers, with Indian country recognizers explicitly enabled.
- **Evaluation Mode**: Single-run (hybrid rules + pretrained context).
- **Training / Adaptation**: Off-the-shelf library configuration.
- **Dependencies**: `presidio-analyzer==2.2.364`, `spacy==3.8.16`.
- **Artifact Location**: `reports/evaluation_presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.json`.
- **Intended Interpretation**: Reflects current enterprise standard de-identification tooling. Shows moderate recall ($M_2 = 0.2956$) but severe over-extraction ($2,105$ false positives, $M_6 = 0.7539$), highlighting the necessity of deep Indic domain adaptation.

---

### Baseline B4: Zero-Shot Multilingual Transformer
- **System Name**: `transformer`
- **Version**: `5.16.1_Davlan_xlm-roberta-base-ner-hrl`
- **Architecture**: XLM-RoBERTa Base fine-tuned on cross-lingual high-resource NER (`Davlan/xlm-roberta-base-ner-hrl`, commit `253f557bd8249b8515114cfd7f71974fe5fa4d2f`).
- **Evaluation Mode**: Single-run (zero-shot transfer).
- **Training / Adaptation**: None on Indian PII data.
- **Dependencies**: `torch==2.13.0`, `transformers==5.16.1`.
- **Artifact Location**: `reports/evaluation_transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.json`.
- **Intended Interpretation**: Evaluates zero-shot cross-lingual transfer from generic multilingual NER models. Achieves only $0.1444$ exact F1 due to zero exposure to Indian identifier schemas.

---

### Baseline B5: Indian-Adapted XLM-RoBERTa (Token Classification)
- **System Name**: `transformer_adapted`
- **Version**: `5.16.1_xlm_roberta_base_indian_v0.18`
- **Architecture**: XLM-RoBERTa Base with an independent linear token classification head emitting logits for 17 IOB2 labels.
- **Evaluation Mode**: Multi-seed experiment (Mean ± Sample SD across seeds `42`, `43`, `44`).
- **Adaptation Corpus**: 200 disjoint Indian PII base instances expanded to 1,000 sequences.
- **Decoding Strategy**: Independent argmax softmax prediction per sub-word token.
- **Dependencies**: `torch==2.13.0`, `transformers==5.16.1`.
- **Artifact Location**: `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.json`.
- **Intended Interpretation**: Demonstrates near-perfect entity localization recall ($M_2 = 0.9742$), but suffers severe exact-boundary collapse ($M_4 = 0.3860$) due to lack of transition constraints between sub-word tokens.

---

### Baseline B6: Indian-Adapted XLM-RoBERTa + Linear Chain CRF
- **System Name**: `transformer_crf`
- **Version**: `5.16.1_xlm_roberta_base_indian_crf_v0.18`
- **Architecture**: Indian-adapted XLM-RoBERTa encoder equipped with a first-order Linear Chain Conditional Random Field (CRF) layer over 17 IOB2 labels.
- **Evaluation Mode**: Multi-seed experiment (Mean ± Sample SD across seeds `42`, `43`, `44`).
- **Decoding Strategy**: Exact Viterbi sequence decoding enforcing first-order transition validity.
- **Dependencies**: `torch==2.13.0`, `transformers==5.16.1`.
- **Artifact Location**: `reports/experiments/b6/B6_FINAL_REPORT.md` and `reports/final/MASTER_RESULTS_TABLE.md`.
- **Key Architectural Intervention**:
  - The CRF layer explicitly penalizes illegal transitions (e.g., $O \to I\text{-TYPE}$ or cross-type boundaries).
  - *Technical Clarification*: The CRF does not impart "semantic understanding" or contextual common-sense reasoning; rather, it enforces **structural transition consistency across sub-tokens**, directly resolving boundary truncation ($F_2$) and duplicate sub-token emission ($FP_9$).
  - Delivers **$+0.2795$ Exact F1** (+72.4% relative) and reduces false positives by **$-61.5\%$**.
