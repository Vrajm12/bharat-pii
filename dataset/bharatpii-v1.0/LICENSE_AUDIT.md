# Dataset License Audit: BharatPII Dataset v1.0

**Document Version**: 1.0.0  
**Date**: 2026-09-12  
**Status**: AUDITED / GOVERNANCE BOUNDARIES DOCUMENTED  

---

## 1. Executive Summary
This document defines the formal intellectual property and licensing boundaries for the **BharatPII Benchmark Dataset Release (v1.0)**. 

To maintain scientific integrity and prevent legal ambiguity, the project enforces a strict tripartite license separation:
1. **Dataset License** (Data instances, splits, schemas, synthetic spans): Separated from code.
2. **Software Package License** (`bharatpii` Python library): MIT License.
3. **Upstream Model License** (`xlm-roberta-base`): Apache License 2.0.

---

## 2. Component Licensing Matrix

| Component | Files / Scope | License Recommendation | Status | Notes |
|:---|:---|:---:|:---:|:---|
| **Benchmark Dataset** | `data/`, `annotations/`, `examples/` | **CC BY 4.0** | **UNRESOLVED (Pending Board Approval)** | Synthetic data; attribution required. |
| **Label Schemas & Metadata** | `label_schema.json`, metadata | **CC0 / Public Domain** | **VERIFIED** | Open specifications. |
| **Software Package** | `bharatpii/` | **MIT License** | **VERIFIED** | Permissive open-source code. |
| **Upstream Encoder** | `models/` base weights | **Apache License 2.0** | **VERIFIED** | Meta AI attribution preserved. |

---

## 3. Governance Ratification Statement
As required by benchmark release governance (Master Task Section 18):
- The dataset license is NOT automatically set to MIT.
- The project recommends **Creative Commons Attribution 4.0 International (CC BY 4.0)** for all synthetic benchmark instances.
- Formal legal ratification status is marked as:
  **`STATUS: RECOMMENDED CC BY 4.0 (UNRESOLVED PENDING FORMAL GOVERNANCE BOARD RATIFICATION)`**
- No fabricated licensing authority has been assumed.

---

## 4. Synthetic Data Integrity Notice
The benchmark contains synthetic PII and is not intended to represent real individuals or real credentials.
