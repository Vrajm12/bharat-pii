# Dataset Release Hash Audit: Source vs Release Integrity

**Document Version**: 1.0.0  
**Date**: 2026-09-12  
**Dataset Release**: `bharatpii-dataset-v1.0`  
**Integrity Status**: **100% MATCH / ZERO BYTE DRIFT**  

---

## 1. Canonical Source Artifacts (Bitwise Preservation)
Every canonical source artifact from which the release was constructed retains its exact pre-flight MD5, SHA-256, and byte size:

| Source File Path | Role | Expected Byte Size | Expected MD5 | Actual MD5 | Status |
|:---|:---|:---:|:---|:---|:---:|
| `annotation/review_template.csv` | annotation_master_template | 176912 bytes | `78c5767f2f8fede2021ff344aaddc32c` | `78c5767f2f8fede2021ff344aaddc32c` | **MATCH** |
| `data/adaptation/manifest.json` | adaptation_manifest | 415 bytes | `03b39e1595486cfe19f70d35f9668f28` | `03b39e1595486cfe19f70d35f9668f28` | **MATCH** |
| `data/adaptation/train.jsonl` | adaptation_train | 327879 bytes | `8b00a18177a4fc889dcd2b71d39fe72d` | `8b00a18177a4fc889dcd2b71d39fe72d` | **MATCH** |
| `data/adaptation/val.jsonl` | adaptation_val | 65235 bytes | `485c5113f129294ea3e7844b94a27fb8` | `485c5113f129294ea3e7844b94a27fb8` | **MATCH** |
| `data/generated/adversarial_realizations.jsonl` | test_adv_realizations | 96473 bytes | `1b678b9597737c85197acf80ab56878d` | `1b678b9597737c85197acf80ab56878d` | **MATCH** |
| `data/generated/hard_negative_realizations.jsonl` | test_hard_neg_realizations | 113011 bytes | `ae5537eec4129822e3d97b05170b4fea` | `ae5537eec4129822e3d97b05170b4fea` | **MATCH** |
| `data/generated/language_realizations.jsonl` | test_lang_realizations | 608939 bytes | `0cb046740507eb9111a214b24b680483` | `0cb046740507eb9111a214b24b680483` | **MATCH** |
| `data/raw/base_instances.jsonl` | test_base_instances | 46608 bytes | `7006b0c9227d93541d2b71f702407ecc` | `7006b0c9227d93541d2b71f702407ecc` | **MATCH** |
| `data/raw/hard_negative_bases.jsonl` | test_hard_neg_bases | 8833 bytes | `b36c6c106548d18ff7083fd00532cb07` | `b36c6c106548d18ff7083fd00532cb07` | **MATCH** |

---

## 2. Release Dataset Files Manifest
The cryptographic fingerprints of all generated files in `dataset/bharatpii-v1.0/`:

| Release File Path | Byte Size | SHA-256 Checksum |
|:---|:---:|:---|
| `CITATION.cff` | 1288 bytes | `6674a6f1df81c55753a4cada955af54f32a4268439d22a15146fcc2558d1ecff` |
| `DATASET_CARD.md` | 8855 bytes | `7325e35e937eeb73192e0dee14c4bc6332d8b2d1decf3671d1593a1e8d0df291` |
| `DATA_RELEASE_POLICY.md` | 4214 bytes | `9941af1e326a83c2b8977318e12a1bd9648667a40e69918687c7a71b2670076c` |
| `LICENSE` | 1198 bytes | `d264aa0250fc6532dc0af951ddc05530ae837c0766d2bbf1d2b5453ac7d1137d` |
| `LICENSE_AUDIT.md` | 2043 bytes | `6d0a0e92d2b2ab80adf065e72e7ec4978e6ba20ec26a0dbc7ebbf7de41c49596` |
| `README.md` | 5588 bytes | `d146d8e9893b1bbf5a00565de77e5615b139459c1c3f3886cc788a1cf8233c38` |
| `REPRODUCIBILITY.md` | 2468 bytes | `956bc8961b62cd30dbb24cb72ff9b8d5b8fad8b91a8e827ea58b774e47633ca9` |
| `annotations/review_template.csv` | 176912 bytes | `6203b92f3474019903e2fddb4189585ea62cea1ab35ab9355b467feac36c83b2` |
| `annotations/test_gold_annotations.jsonl` | 194636 bytes | `c7baa5b5fc169a758106c02a7ab4b3246ce4ff75fbd6d81a99d52c567b3a1212` |
| `data/test/test_inputs.jsonl` | 342455 bytes | `0f2d099e3dc5397c5b1ee7e24d1980ea5b2206f8ed1ed1898472a93466727f3b` |
| `data/train/train.jsonl` | 327879 bytes | `02f0e9990ea775133ccd3612321870be7dd8b53991fd659617e6a88a896fac58` |
| `data/validation/val.jsonl` | 65235 bytes | `f66c0689fea5798e3b702b2255d7590d41ff7c85491c5e6c8b9d908a7bc5c60b` |
| `dataset_metadata.json` | 1703 bytes | `a3fc314efb22a49bcf01188ace19e33be0d4eeae2626b80b23ccc42fd69a49c0` |
| `docs/annotation_guidelines.md` | 107097 bytes | `53922b3724cbab9053f1f90ddc3a9b9ed3bb6800b3cc1376a53dbfd79ab2ab4b` |
| `examples/synthetic_examples.jsonl` | 3784 bytes | `96dcafadac5dbc7c4e864acf333c47092319a834c86f58e1e942d17b9e78acf9` |
| `label_schema.json` | 3867 bytes | `7e245a1046a7269974fd44f7bec54793852196a9da85f7e4cc3002656f97f381` |

---

## 3. Cryptographic Verification Conclusion
All canonical source files are confirmed bitwise identical against their pre-flight hashes. Zero byte drift has occurred across any locked scientific artifacts.
