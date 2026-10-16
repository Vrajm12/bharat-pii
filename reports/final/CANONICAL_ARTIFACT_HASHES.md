# Canonical Artifact MD5 Hashes & Immutability Register

**Benchmark**: Indian PII Robustness Benchmark v0.18  
**Freeze Phase**: Scientific Freeze (Terminal Baseline B6)  
**Verification**: 100% Bitwise Match on Prior Canonical Baselines and Datasets  

## 1. Prior 22 Canonical Locked Artifacts

| Rel Path | Expected MD5 | Actual MD5 | Status |
| :--- | :--- | :--- | :---: |
| `data/raw/base_instances.jsonl` | `7006b0c9227d93541d2b71f702407ecc` | `7006b0c9227d93541d2b71f702407ecc` | **MATCH** |
| `data/raw/hard_negative_bases.jsonl` | `b36c6c106548d18ff7083fd00532cb07` | `b36c6c106548d18ff7083fd00532cb07` | **MATCH** |
| `data/generated/language_realizations.jsonl` | `0cb046740507eb9111a214b24b680483` | `0cb046740507eb9111a214b24b680483` | **MATCH** |
| `data/generated/hard_negative_realizations.jsonl` | `ae5537eec4129822e3d97b05170b4fea` | `ae5537eec4129822e3d97b05170b4fea` | **MATCH** |
| `data/generated/adversarial_realizations.jsonl` | `1b678b9597737c85197acf80ab56878d` | `1b678b9597737c85197acf80ab56878d` | **MATCH** |
| `annotation/review_template.csv` | `78c5767f2f8fede2021ff344aaddc32c` | `78c5767f2f8fede2021ff344aaddc32c` | **MATCH** |
| `predictions/regex_1.0.0_v0.18.jsonl` | `8913ac633854a36948a3445e4be0594d` | `8913ac633854a36948a3445e4be0594d` | **MATCH** |
| `reports/evaluation_regex_1.0.0_v0.18.json` | `2958f77985fcc70d704c123e9e952ebd` | `2958f77985fcc70d704c123e9e952ebd` | **MATCH** |
| `predictions/spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.jsonl` | `6c74bd4ec742a1f0c6b8024200937fb5` | `6c74bd4ec742a1f0c6b8024200937fb5` | **MATCH** |
| `reports/evaluation_spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.json` | `a9745314b2e71df861ea71af15a9dd1a` | `a9745314b2e71df861ea71af15a9dd1a` | **MATCH** |
| `predictions/presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.jsonl` | `2c661403efa963275be5f2559a1577b9` | `2c661403efa963275be5f2559a1577b9` | **MATCH** |
| `reports/evaluation_presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.json` | `4831393231e3d15dc674166dcaaaa2b9` | `4831393231e3d15dc674166dcaaaa2b9` | **MATCH** |
| `predictions/transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.jsonl` | `3f53b646fb9f95414bef8b972d2277b1` | `3f53b646fb9f95414bef8b972d2277b1` | **MATCH** |
| `reports/evaluation_transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.json` | `dfe7e6b93e15ca266b29121977b1809e` | `dfe7e6b93e15ca266b29121977b1809e` | **MATCH** |
| `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.jsonl` | `e589c2a3daa96e8a3963d95fecb89012` | `e589c2a3daa96e8a3963d95fecb89012` | **MATCH** |
| `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.jsonl` | `e589c2a3daa96e8a3963d95fecb89012` | `e589c2a3daa96e8a3963d95fecb89012` | **MATCH** |
| `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.jsonl` | `e11d924839cdddebd59104624f667357` | `e11d924839cdddebd59104624f667357` | **MATCH** |
| `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.jsonl` | `a0b17f4b93251463319d0dc1409514bf` | `a0b17f4b93251463319d0dc1409514bf` | **MATCH** |
| `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.json` | `d3a9f9da8e848c7cafb9cf43299b9439` | `d3a9f9da8e848c7cafb9cf43299b9439` | **MATCH** |
| `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.json` | `06ca5638e48dc492c016166d8b1d12a2` | `06ca5638e48dc492c016166d8b1d12a2` | **MATCH** |
| `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.json` | `cfb422de399fa7cb13dec4e30f7b29e1` | `cfb422de399fa7cb13dec4e30f7b29e1` | **MATCH** |
| `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.json` | `90a0a0c9bb83dd4d2f456b6e0f508753` | `90a0a0c9bb83dd4d2f456b6e0f508753` | **MATCH** |

## 2. Baseline B6 Frozen Experimental Artifacts

| Rel Path | Frozen MD5 | Status |
| :--- | :--- | :---: |
| `predictions/experiments/b6/transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.jsonl` | `549cce213b1b52e6dbb682810a4544c9` | **FROZEN** |
| `predictions/experiments/b6/transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed42_v0.18.jsonl` | `549cce213b1b52e6dbb682810a4544c9` | **FROZEN** |
| `predictions/experiments/b6/transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed43_v0.18.jsonl` | `6e42cb0960464396937777d258074847` | **FROZEN** |
| `predictions/experiments/b6/transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed44_v0.18.jsonl` | `060294f557d9795e124aa1f26dfa3693` | **FROZEN** |
| `reports/experiments/b6/evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.json` | `575662658e2457359933c3b678de033f` | **FROZEN** |
| `reports/experiments/b6/evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed42_v0.18.json` | `575662658e2457359933c3b678de033f` | **FROZEN** |
| `reports/experiments/b6/evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed43_v0.18.json` | `bfec1ca3a013e567fab553c17a8d1820` | **FROZEN** |
| `reports/experiments/b6/evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed44_v0.18.json` | `b6b6e40135fb1022efceed8635d10881` | **FROZEN** |
| `reports/experiments/b6/b6_error_summary.json` | `5f7de4c90da2597ffe72cae5037527c9` | **FROZEN** |
| `reports/experiments/b6/b6_boundary_analysis.json` | `725de79c7a0d382cc2799c712b54d5ee` | **FROZEN** |
| `reports/experiments/b6/b6_false_positive_analysis.json` | `b08d064cc9c6718b8dea47e49db74bfe` | **FROZEN** |
| `reports/experiments/b6/b6_type_analysis.json` | `50cbd12a00e6c2f044f43ec0d12bbe6a` | **FROZEN** |
| `reports/experiments/b6/b6_language_analysis.json` | `8f24615bbb4a2fb5d7a99a5463d8b329` | **FROZEN** |
| `reports/experiments/b6/b6_perturbation_analysis.json` | `90072f902a55889cf867b58f515205dc` | **FROZEN** |
| `reports/experiments/b6/b6_difficulty_analysis.json` | `546528eb21dd0e20c0f7677a59efc1a5` | **FROZEN** |
| `reports/experiments/b6/b6_hard_negative_analysis.json` | `865a8183e96ba68d5e9a8d87980c32ce` | **FROZEN** |
| `reports/experiments/b6/b6_b5_vs_b6_transition.json` | `923a48b67f57ce40e2aaed076711dc83` | **FROZEN** |
| `reports/experiments/b6/b6_error_interactions.json` | `338adfa5d01a34afb03a582acd4041f8` | **FROZEN** |
| `reports/experiments/b6/b6_representative_cases.json` | `b58ea8dfcdf6f57cc1ed54f57285e91c` | **FROZEN** |
| `reports/experiments/b6/B6_FINAL_REPORT.md` | `41c70b83c34e4194dbb5999af37a52a2` | **FROZEN** |

## 3. Scientific Validation (SV-01, SV-02, SV-03) Frozen Artifacts

| Rel Path | Frozen MD5 | Status |
| :--- | :--- | :---: |
| `reports/scientific_validation_sv01_b5_distribution_audit.json` | `5b2021437fa8356be86a044318a6b8c0` | **FROZEN** |
| `reports/scientific_validation_sv01_b5_distribution_audit.md` | `6f47cd5a1ffe63b38b4f93893757d5ff` | **FROZEN** |
| `reports/experiments/sv02/SV02_FINAL_REPORT.md` | `156f8a36eaa94d8c17aaeb875fe131f3` | **FROZEN** |
| `reports/experiments/sv02/sv02_master_evaluation.json` | `fa41e738c8c5203419a990ef38b464cb` | **FROZEN** |
| `reports/experiments/sv03/SV03_FINAL_REPORT.md` | `a8a190667ae8faad6a0476698bc82c0d` | **FROZEN** |
| `reports/experiments/sv03/sv03_error_summary.json` | `9aa504ab9a279ba0f943d6568bbc6f3e` | **FROZEN** |
| `reports/experiments/sv03/sv03_boundary_analysis.json` | `af351e3e7d081f0e34413880e46c83bb` | **FROZEN** |
| `reports/experiments/sv03/sv03_false_positive_analysis.json` | `f88c079a83cc9c56266459329be236bb` | **FROZEN** |
| `reports/experiments/sv03/sv03_type_analysis.json` | `ac6aa5d5a153bbdd1e2c48f0ced19d13` | **FROZEN** |
| `reports/experiments/sv03/sv03_b5_vs_sv02_transition.json` | `3287f092996adf5ce896e2a01abd1c2c` | **FROZEN** |
