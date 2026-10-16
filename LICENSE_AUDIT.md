# License Audit: BharatPII Package and Model Release

**Package Name**: `bharatpii` (v1.0.0)  
**Model Release**: `bharatpii-crf-v1.0`  
**Date**: 2026-09-12  
**Audit Status**: VERIFIED / COMPLIANT  

---

## 1. Executive Summary
This license audit verifies the intellectual property, copyright, and distribution compliance for the `bharatpii` Python package and the `bharatpii-crf-v1.0` model artifact. All components, dependencies, and upstream model foundations have been audited against their source licenses.

---

## 2. Upstream Base Model
- **Base Architecture**: XLM-RoBERTa (`xlm-roberta-base`)
- **Upstream Authors**: Alexis Conneau, Kartikay Khandelwal, Naman Goyal, Vishrav Chaudhary, Guillaume Wenzek, Francisco Guzmán, Edouard Grave, Myle Ott, Luke Zettlemoyer, Veselin Stoyanov (Meta AI / Facebook AI Research, 2019–2020).
- **Upstream License**: **MIT License**
- **Redistribution Terms**: Permitted for commercial and non-commercial use, modification, and distribution, provided the original copyright notice and permission notice are preserved.
- **Compliance Action**: Original Meta AI copyright and license terms are preserved and referenced in the package `LICENSE` file under "THIRD-PARTY NOTICE".

---

## 3. Package Dependencies & Core Libraries
| Dependency | License | Permissible Use | Attribution Requirement |
|:---|:---:|:---:|:---|
| **PyTorch (`torch`)** | Modified BSD (BSD-3-Clause) | Free commercial & academic distribution | Retain BSD notice in binary/source distributions |
| **Transformers (`transformers`)** | Apache License 2.0 | Free commercial & academic distribution | Retain Apache notice and license text |
| **Safetensors (`safetensors`)** | Apache License 2.0 | Free commercial & academic distribution | Retain Apache notice and license text |
| **SentencePiece (`sentencepiece`)** | Apache License 2.0 | Free commercial & academic distribution | Retain Apache notice and license text |
| **Tokenizers (`tokenizers`)** | Apache License 2.0 | Free commercial & academic distribution | Retain Apache notice and license text |

---

## 4. Derived BharatPII-CRF Model Weights
- **Model Checkpoint**: `models/bharatpii-crf-v1.0/`
- **Encoder Weights (199 tensors, 278,043,648 parameters)**: Derivative of `xlm-roberta-base` under MIT License.
- **Linear-Chain CRF Head Weights (5 tensors, 13,396 parameters)**: Created during academic research adaptation on synthetic Indian PII templates.
- **Intended Purpose**: Academic research and evaluation of sequence-constrained multilingual PII detection.
- **Distribution Scope**: Permitted under MIT License for research and evaluation purposes.

---

## 5. Library Code (`bharatpii`)
- **License**: **MIT License**
- **Copyright**: (c) 2026 BharatPII Contributors
- **Warranties**: Standard "AS IS" disclaimer without warranty of merchantability or fitness for a particular purpose.

---

## 6. Audit Conclusion
- **License Status**: **VERIFIED**
- All components operate under permissive open-source licenses (MIT, Apache 2.0, BSD-3-Clause).
- No GPL, AGPL, or proprietary copyleft encumbrances apply to the package or model weights.
- Attribution notices are completely documented in `LICENSE` and `README.md`.
