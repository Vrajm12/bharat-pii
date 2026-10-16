# CANONICAL ARTIFACT INTEGRITY AUDIT REPORT

**Audit Phase**: Post-Clean-Room Reproduction Integrity Verification  
**Benchmark**: Indian PII Robustness Benchmark (`v0.18`)  
**Timestamp**: 2026-09-09  
**Audit Scope**: All 22 Authoritative Canonical Benchmark Files  
**Status**: **100% UNMODIFIED (Bitwise Identical)**  

---

## 1. Audit Overview & Guarantee

Prior to launching clean-room reproduction experiments, a cryptographic snapshot of all 22 authoritative canonical artifacts was generated in `reproduction/clean_room/HASH_AUDIT_BEFORE.json`.

Following the execution of all reproduction runs across Baselines B5 and B6 (seeds 42, 43, 44), a second cryptographic snapshot was generated in `reproduction/clean_room/HASH_AUDIT_AFTER.json`.

Every canonical file was compared across three dimensions:
1. Exact byte length
2. MD5 checksum
3. SHA-256 checksum

**Result**: Zero bytes were altered. No canonical dataset, prediction file, evaluation report, annotation template, or checkpoint was modified during clean-room reproduction.

---

## 2. Artifact Integrity Verification Matrix

| Canonical File Path | Size (Bytes) | MD5 Checksum | SHA-256 Checksum | Integrity Status |
|:---|:---:|:---:|:---:|:---:|
| `data/raw/base_instances.jsonl` | 46,608 | `7006b0c9227d93541d2b71f702407ecc` | `0e4da95aa3463c34c483a83ac941da5a4c4442d93ecb2c741ded65c0fdc17919` | BITWISE MATCH |
| `data/raw/hard_negative_bases.jsonl` | 8,833 | `b36c6c106548d18ff7083fd00532cb07` | `eb08ab608309296fb2395fb12fb87ca5b2640baa6e203e857f2e7e786fb85c17` | BITWISE MATCH |
| `data/generated/language_realizations.jsonl` | 608,939 | `0cb046740507eb9111a214b24b680483` | `e53e513189933a3bb153e55bb979f4a19b0f68ff68f438ccfd9fc98b8d83b2b4` | BITWISE MATCH |
| `data/generated/hard_negative_realizations.jsonl` | 113,011 | `ae5537eec4129822e3d97b05170b4fea` | `7a60a4fc7fb00f03533be0a9d58fac8d33c82d2f8e63bf484193889c1ba846c1` | BITWISE MATCH |
| `data/generated/adversarial_realizations.jsonl` | 96,473 | `1b678b9597737c85197acf80ab56878d` | `c66208751edf22b7ca6169b4b16e2a917a2b6072bf33bbd53c9bcbb4dfe88ed6` | BITWISE MATCH |
| `annotation/review_template.csv` | 176,912 | `78c5767f2f8fede2021ff344aaddc32c` | `6203b92f3474019903e2fddb4189585ea62cea1ab35ab9355b467feac36c83b2` | BITWISE MATCH |
| `predictions/regex_1.0.0_v0.18.jsonl` | 72,293 | `8913ac633854a36948a3445e4be0594d` | `edc750a0d38b606f4ecf459dd456c3059e111df84817ec9550926daa09138d7f` | BITWISE MATCH |
| `reports/evaluation_regex_1.0.0_v0.18.json` | 15,595 | `2958f77985fcc70d704c123e9e952ebd` | `5142e14e6db19e676092daba9a55cfadd5617fced6d3ccaac237d085deb02234` | BITWISE MATCH |
| `predictions/spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.jsonl` | 166,972 | `6c74bd4ec742a1f0c6b8024200937fb5` | `4865d0f59df5630f4c6fac662d221a4122322980ca16249175f7154a2530e338` | BITWISE MATCH |
| `reports/evaluation_spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.json` | 15,684 | `a9745314b2e71df861ea71af15a9dd1a` | `3c0f8251e4fc5e09189f06353575978793100c18782f35f4d22dc16e3efe76e3` | BITWISE MATCH |
| `predictions/presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.jsonl` | 352,773 | `2c661403efa963275be5f2559a1577b9` | `e76bd770c7624c51235d8b4d90ee5ca7e5e4920dc7570ed0f9e3bcfc407d7081` | BITWISE MATCH |
| `reports/evaluation_presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.json` | 16,005 | `4831393231e3d15dc674166dcaaaa2b9` | `a794508040a6e3c3be0595f5a01250f6b46dd7cacd1d20d7e9831c64edb5f181` | BITWISE MATCH |
| `predictions/transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.jsonl` | 64,279 | `3f53b646fb9f95414bef8b972d2277b1` | `974bbca9c62b2efb015bdcfacd9266e5addbbb289bc711292eb3cab6d7b8588c` | BITWISE MATCH |
| `reports/evaluation_transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.json` | 15,279 | `dfe7e6b93e15ca266b29121977b1809e` | `7cc4d96c332a44123c4999a2bde48c6db802c204f53b8c90847dc358911810d5` | BITWISE MATCH |
| `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.jsonl` | 226,398 | `e589c2a3daa96e8a3963d95fecb89012` | `af6f89d45ee91628e58ce7ed0532421b6ff1b7869fa83385c34dc58af4795a0b` | BITWISE MATCH |
| `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.jsonl` | 226,398 | `e589c2a3daa96e8a3963d95fecb89012` | `af6f89d45ee91628e58ce7ed0532421b6ff1b7869fa83385c34dc58af4795a0b` | BITWISE MATCH |
| `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.jsonl` | 224,490 | `e11d924839cdddebd59104624f667357` | `787a565fcc53325380aac7c1e6979465972b8d4166bede124df0d751793fa54a` | BITWISE MATCH |
| `predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.jsonl` | 227,244 | `a0b17f4b93251463319d0dc1409514bf` | `d6a922ddfd3e09db41e3e46a8b8645625f7ca9cffa97c121714ba60c116c7f63` | BITWISE MATCH |
| `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.json` | 58,886 | `d3a9f9da8e848c7cafb9cf43299b9439` | `c1471c9cfa5430f7ddccf77783e13666703eb5b52d4565e71df3ed64f9e5ca67` | BITWISE MATCH |
| `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.json` | 16,153 | `06ca5638e48dc492c016166d8b1d12a2` | `b9535e88e0e1f3615b9e451ef36e4ba026d292f004be335904402dfae841eeba` | BITWISE MATCH |
| `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.json` | 16,059 | `cfb422de399fa7cb13dec4e30f7b29e1` | `c162005e62375d64d4ae56939a235097e2505793e79ee578def2ee9c875680c7` | BITWISE MATCH |
| `reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.json` | 16,150 | `90a0a0c9bb83dd4d2f456b6e0f508753` | `6ddfd803b8b47d8057b5125f5bf054aec49c2dcdb70d7cfb955e5122c66bf8c7` | BITWISE MATCH |

---

## 3. Governance Audit Summary

- **Total Canonical Files Checked**: 22
- **Bitwise Identical Files**: 22 (100.0%)
- **Modified / Divergent Files**: 0 (0.0%)
- **New Files Added in Canonical Paths**: 0 (0.0%)
- **Audit Verdict**: **ZERO CORRUPTION DETECTED. SCIENTIFIC FREEZE INTACT.**
