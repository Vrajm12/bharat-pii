# Indian PII Robustness Benchmark — Authoritative Freeze Boundary
**Document Identifier**: `REPORTS-ARTIFACT-ENG-FREEZE-BOUNDARY-V1.0`  
**Phase**: Artifact Engineering V1 (Post-Scientific-Freeze)  
**Status**: ACTIVE & STRICTLY ENFORCED  
**Date**: September 9, 2026  

---

## 1. Principle of the Scientific Freeze Boundary

Scientific experimentation for this benchmark iteration concluded with Baseline B6 and the subsequent formal freeze declaration (`reports/FINAL_FREEZE_DECLARATION.md`). Under no circumstances may any file within the **Frozen Scientific Boundary** be modified, retrained, regenerated, normalized, or retrospectively adjusted during software engineering, artifact packaging, or public release preparation.

---

## 2. Exhaustive Boundary Definition

### 2.1 Benchmark Data Layer (FROZEN)
- **Canonical 964-Record Benchmark**:
  - `data/raw/base_instances.jsonl` (200 base clean instances, 200 gold entities, MD5: `7006b0c9227d93541d2b71f702407ecc`)
  - `data/raw/hard_negative_bases.jsonl` (50 base decoy instances, 0 gold entities, MD5: `b36c6c106548d18ff7083fd00532cb07`)
  - `data/generated/language_realizations.jsonl` (400 records across 5 language regimes, 400 gold entities, MD5: `0cb046740507eb9111a214b24b680483`)
  - `data/generated/adversarial_realizations.jsonl` (314 records across A1–A5 perturbations, 124 gold entities, MD5: `1b678b9597737c85197acf80ab56878d`)
  - `data/generated/hard_negative_realizations.jsonl` (50 records, 0 gold entities, MD5: `ae5537eec4129822e3d97b05170b4fea`)
  - `annotation/review_template.csv` (Canonical human review template, MD5: `78c5767f2f8fede2021ff344aaddc32c`)
- **Adaptation Corpus**:
  - `data/adaptation/train_instances.jsonl` (200 base instances, 1,000 augmented sequences)
  - `data/adaptation/val_instances.jsonl` (50 base instances, 250 augmented sequences)
  - *Invariant*: 0% overlap between adaptation base instances and test benchmark instances (verified in SV-01).
- **Annotation & Schema Specifications**:
  - `PROJECT_SPEC.md`
  - `annotation/guidelines.md`
  - `schemas/base_instance.schema.json`
  - `schemas/example.schema.json`

### 2.2 Baseline Model Checkpoints & Architectures (FROZEN)
- **B1 Regex (Canonical v1.0.0)**: Fixed regular expressions targeting standard Aadhaar, PAN, Phone, and Email patterns.
- **B2 spaCy (`en_core_web_sm` v3.8.16)**: Standard off-the-shelf English statistical pipeline.
- **B3 Microsoft Presidio (v2.2.364)**: Off-the-shelf hybrid analyzer with Indian recognizers enabled.
- **B4 Zero-Shot XLM-RoBERTa**: Pretrained checkpoint `Davlan/xlm-roberta-base-ner-hrl` (commit `253f557bd8249b8515114cfd7f71974fe5fa4d2f`).
- **B5 Indian-Adapted XLM-RoBERTa**: Fine-tuned XLM-RoBERTa with independent linear token classification head across frozen seeds `42`, `43`, `44`.
- **B6 Indian-Adapted XLM-RoBERTa + Linear CRF**: Fine-tuned XLM-RoBERTa with first-order linear chain CRF decoding across frozen seeds `42`, `43`, `44`.
- **PROHIBITION**: No Baseline B7 or alternative modeling experiment shall be created in this repository.

### 2.3 Empirical Results & Evaluation Reports (FROZEN)
- **Canonical Prediction JSONL Files**:
  - `predictions/regex_1.0.0_v0.18.jsonl`
  - `predictions/spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.jsonl`
  - `predictions/presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.jsonl`
  - `predictions/transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.jsonl`
  - `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.jsonl`
  - `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.jsonl`
  - `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.jsonl`
  - `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.jsonl`
  - `predictions/experiments/b6/transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.jsonl`
  - `predictions/experiments/b6/transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed42_v0.18.jsonl`
  - `predictions/experiments/b6/transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed43_v0.18.jsonl`
  - `predictions/experiments/b6/transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed44_v0.18.jsonl`
- **Canonical Evaluation Reports**:
  - `reports/evaluation_regex_1.0.0_v0.18.json`
  - `reports/evaluation_spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.json`
  - `reports/evaluation_presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.json`
  - `reports/evaluation_transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.json`
  - `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.json`
  - `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.json`
  - `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.json`
  - `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.json`
  - `reports/experiments/b6/evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.json`
  - `reports/experiments/b6/evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed42_v0.18.json`
  - `reports/experiments/b6/evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed43_v0.18.json`
  - `reports/experiments/b6/evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed44_v0.18.json`
- **Scientific Validation Studies**:
  - SV-01: `reports/scientific_validation_sv01_b5_distribution_audit.json` & `.md`
  - SV-02: `reports/experiments/sv02/` (11 reports and JSON files)
  - SV-03: `reports/experiments/sv03/` (13 reports and JSON files)
  - B6 Analysis: `reports/experiments/b6/` (11 analysis JSON files and `B6_FINAL_REPORT.md`)

### 2.4 Authoritative Governance Records (FROZEN)
- `reports/FINAL_SCIENTIFIC_RECORD.md`
- `reports/FINAL_CLAIM_AUDIT.md`
- `reports/FINAL_LIMITATIONS.md`
- `reports/FINAL_FREEZE_DECLARATION.md`
- `reports/final/CANONICAL_ARTIFACT_HASHES.json` & `.md`

---

## 3. Allowed Engineering Activities

The following activities are strictly permitted in this post-scientific-freeze phase:
1. Creating non-invasive CLI entrypoints (`benchmark.evaluate`, `benchmark.predict`).
2. Creating reproduction runner scripts writing strictly to `reproduction/` (non-canonical).
3. Authoring public documentation in `docs/` and updating `README.md`.
4. Packaging (`pyproject.toml`, `requirements.txt`, `requirements-lock.txt`, `CITATION.cff`).
5. Authoring automated smoke, schema, and canonical protection tests.
6. Compiling release manifests and release hash registries.

Any attempt to recompute, overwrite, or mutate an artifact listed in Section 2 is an immediate governance violation.
