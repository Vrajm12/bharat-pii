# Indian PII Robustness Benchmark — License & Third-Party Audit
**Document Identifier**: `REPORTS-ARTIFACT-ENG-LICENSE-AUDIT-V1.0`  
**Phase**: Artifact Engineering V1 (Post-Scientific-Freeze)  
**Status**: AUDITED — RELEASE PREREQUISITES DOCUMENTED  
**Date**: September 9, 2026  

---

## 1. Executive Summary

This license audit examines the intellectual property, copyright, and distribution terms across all components of the benchmark repository:
1. Benchmark Source Code & CLI tools
2. Benchmark Canonical Synthetic Datasets
3. Third-Party Python Dependencies
4. Upstream Pretrained Models and Checkpoints
5. Visualization Assets and Typography

---

## 2. Component-by-Component License Analysis

### 2.1 Benchmark Source Code
- **Repository Code**: `benchmark/`, `baselines/`, `scripts/`, `tests/`
- **Applicable License**: MIT License (`LICENSE`)
- **Permissible Usage**: Unrestricted academic and commercial use with attribution.
- **Status**: **`VERIFIED — READY`**

### 2.2 Canonical Benchmark Dataset & Synthetic Instances
- **Files**: `data/raw/base_instances.jsonl`, `data/generated/*.jsonl`, `annotation/*.csv`
- **Provenance**: 100% synthetically generated via rule-guided Python scripts; contains no crawled private data or copyrighted text.
- **Recommended Data License**: Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Status**: **`VERIFIED — READY`**

### 2.3 Core Python Dependencies
| Package | Upstream Version | Upstream License | Distribution Compatibility |
| :--- | :--- | :--- | :--- |
| **`torch`** | 2.13.0 | BSD-3-Clause | Compatible |
| **`transformers`** | 5.16.1 | Apache-2.0 | Compatible |
| **`spacy`** | 3.8.16 | MIT | Compatible |
| **`presidio-analyzer`** | 2.2.364 | MIT | Compatible |
| **`regex`** | 2026.7.19 | Apache-2.0 | Compatible |
| **`matplotlib`** | 3.10.9 | PSF / BSD compatible | Compatible |
| **`numpy`** | 2.2.6 | BSD-3-Clause | Compatible |
| **`pydantic`** | 2.12.5 | MIT | Compatible |
| **`jsonschema`** | 4.26.0 | MIT | Compatible |
| **`pytest`** | 8.4.2 | MIT | Compatible |

- **Status**: **`VERIFIED — ALL PERMISSIVE OPEN SOURCE`**

### 2.4 Upstream Pretrained Models & Checkpoint Weights
| Model | Upstream Source | Claimed / Expected License | Release Status |
| :--- | :--- | :--- | :--- |
| **`xlm-roberta-base`** | Meta / Facebook AI | MIT / CC-BY-NC / Open Source | **Requires Author Confirmation** |
| **`Davlan/xlm-roberta-base-ner-hrl`** | Hugging Face Hub (Davlan) | Apache-2.0 / Open Access | **Requires Author Confirmation** |
| **Adapted B5/B6 Checkpoints** | Trained internally from XLM-R Base | Derived from upstream weights | **Requires Author Confirmation** |

> [!WARNING]
> **Release Blocker Note**:
> While the training code, architecture wrappers, and evaluation scripts are released under MIT, redistribution of binary model checkpoint weights (`model.safetensors`, `pytorch_model.bin`) requires formal confirmation of Meta's `xlm-roberta-base` terms and Davlan's upstream repository card terms before public hosting on Hugging Face Hub or Zenodo.

### 2.5 Figure Fonts & Visual Assets
- **Figures**: `reports/final/figures/*.png`
- **Font Stack**: Default Matplotlib sans-serif stack (`DejaVu Sans` / `Bitstream Vera Sans`), licensed under permissive free software terms (Bitstream Vera / DejaVu license).
- **Status**: **`VERIFIED — FULLY PERMISSIVE`**

---

## 3. Release Action Items

1. [ ] Confirm upstream license terms for `Davlan/xlm-roberta-base-ner-hrl` before publishing binary weights.
2. [ ] Attach CC BY 4.0 license metadata to Hugging Face Dataset repository when mirroring `data/`.
3. [ ] Ensure binary weights are distributed with appropriate third-party notices.
