# Indian PII Robustness Benchmark — Repository Audit Report
**Phase**: Artifact Engineering V1 (Post-Scientific-Freeze)
**Total Files Audited**: 478

## 1. Classification Summary

| Classification Category | File Count | Description |
| :--- | :---: | :--- |
| **`CANONICAL_SCIENTIFIC`** | 24 | 22 canonical locked artifacts + adaptation data + guidelines (Bitwise Frozen) |
| **`EXPERIMENTAL_ARCHIVE`** | 148 | SV-01, SV-02, SV-03, B6 intermediate experiments, checkpoints, and model weights |
| **`DERIVED_ARTIFACT`** | 35 | Master tables, breakdown CSVs, publication figures, final scientific records |
| **`PUBLIC_RELEASE`** | 72 | Public code, CLI tools, tests, documentation, dependencies, and packaging |
| **`DEVELOPMENT_ONLY`** | 77 | Training scripts, data generators, internal validators, and review scripts |
| **`SCRATCH`** | 122 | Temporary cache files and scratch exploratory scripts |

## 2. Canonical Scientific Artifacts (Frozen Boundary)

All 22 canonical locked artifacts are strictly frozen and protected against modification:

| File Path | Size (Bytes) | MD5 Checksum |
| :--- | :---: | :--- |
| `PROJECT_SPEC.md` | 61,344 | `7f9ebfca9e655295791736c9e7510fa7` |
| `annotation/guidelines.md` | 107,097 | `a212a9fce3a35622edfe2e23d05f2383` |
| `annotation/review_template.csv` | 176,912 | `78c5767f2f8fede2021ff344aaddc32c` |
| `data/generated/adversarial_realizations.jsonl` | 96,473 | `1b678b9597737c85197acf80ab56878d` |
| `data/generated/hard_negative_realizations.jsonl` | 113,011 | `ae5537eec4129822e3d97b05170b4fea` |
| `data/generated/language_realizations.jsonl` | 608,939 | `0cb046740507eb9111a214b24b680483` |
| `data/raw/base_instances.jsonl` | 46,608 | `7006b0c9227d93541d2b71f702407ecc` |
| `data/raw/hard_negative_bases.jsonl` | 8,833 | `b36c6c106548d18ff7083fd00532cb07` |
| `predictions/presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.jsonl` | 352,773 | `2c661403efa963275be5f2559a1577b9` |
| `predictions/regex_1.0.0_v0.18.jsonl` | 72,293 | `8913ac633854a36948a3445e4be0594d` |
| `predictions/spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.jsonl` | 166,972 | `6c74bd4ec742a1f0c6b8024200937fb5` |
| `predictions/transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.jsonl` | 64,279 | `3f53b646fb9f95414bef8b972d2277b1` |
| `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.jsonl` | 226,398 | `e589c2a3daa96e8a3963d95fecb89012` |
| `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.jsonl` | 224,490 | `e11d924839cdddebd59104624f667357` |
| `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.jsonl` | 227,244 | `a0b17f4b93251463319d0dc1409514bf` |
| `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.jsonl` | 226,398 | `e589c2a3daa96e8a3963d95fecb89012` |
| `reports/evaluation_presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.json` | 16,005 | `4831393231e3d15dc674166dcaaaa2b9` |
| `reports/evaluation_regex_1.0.0_v0.18.json` | 15,595 | `2958f77985fcc70d704c123e9e952ebd` |
| `reports/evaluation_spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.json` | 15,684 | `a9745314b2e71df861ea71af15a9dd1a` |
| `reports/evaluation_transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.json` | 15,279 | `dfe7e6b93e15ca266b29121977b1809e` |
| `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.json` | 16,153 | `06ca5638e48dc492c016166d8b1d12a2` |
| `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.json` | 16,059 | `cfb422de399fa7cb13dec4e30f7b29e1` |
| `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.json` | 16,150 | `90a0a0c9bb83dd4d2f456b6e0f508753` |
| `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.json` | 58,886 | `d3a9f9da8e848c7cafb9cf43299b9439` |

## 3. Preservation & Non-Destruction Commitment

No files were removed or destructively reorganized during this audit. All experimental archives (SV-01, SV-02, SV-03, B6 checkpoints) are preserved in their original relative paths to maintain historical test and governance compliance.
