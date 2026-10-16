# Dataset Leakage Audit: Cross-Split Disjointness & Overlap Evaluation

**Document Version**: 1.0.0  
**Date**: 2026-09-12  
**Dataset Release**: `bharatpii-dataset-v1.0`  
**Audit Status**: **PASSED / ZERO CONTAMINATION DETECTED**  

---

## 1. Executive Summary
Data leakage between training, validation, and evaluation splits is an insidious failure mode in machine learning benchmarks. In PII extraction, leakage can manifest at multiple structural granularities:
1. **Base-Instance Level**: Realizations in test originating from templates seen in training.
2. **Record / Identifier Level**: Overlapping unique variant identifiers across splits.
3. **Raw Text Level**: Verbatim carrier sentence duplication.
4. **Normalized Text Level**: Surface duplication up to case and whitespace normalization.
5. **Entity-Value Level**: Exact memorization of synthetic personal names or alphanumeric sequences.

This audit executes exhaustive cross-split intersection tests across all 2,164 records.

---

## 2. Cross-Split Overlap Evaluation Matrix

| Leakage Dimension | Evaluated Comparison | Intersection Count | Status | Notes |
|:---|:---|:---:|:---:|:---|
| **Base Instance ID** | Train (200) $\cap$ Test (120) | **0** | **PASS** | Completely disjoint base instances |
| **Base Instance ID** | Val (40) $\cap$ Test (120) | **0** | **PASS** | Completely disjoint base instances |
| **Base Instance ID** | Train (200) $\cap$ Val (40) | **0** | **PASS** | Completely disjoint base instances |
| **Record / Variant ID** | Train (1,000) $\cap$ Test (964) | **0** | **PASS** | Zero ID collisions |
| **Record / Variant ID** | Val (200) $\cap$ Test (964) | **0** | **PASS** | Zero ID collisions |
| **Record / Variant ID** | Train (1,000) $\cap$ Val (200) | **0** | **PASS** | Zero ID collisions |
| **Exact Raw Text** | Train $\cap$ Test | **0** | **PASS** | Zero verbatim string overlap |
| **Exact Raw Text** | Val $\cap$ Test | **0** | **PASS** | Zero verbatim string overlap |
| **Exact Raw Text** | Train $\cap$ Val | **0** | **PASS** | Zero verbatim string overlap |
| **Normalized Text (lower+strip)** | Train $\cap$ Test | **0** | **PASS** | Zero normalized string overlap |
| **Normalized Text (lower+strip)** | Val $\cap$ Test | **0** | **PASS** | Zero normalized string overlap |
| **Normalized Text (lower+strip)** | Train $\cap$ Val | **0** | **PASS** | Zero normalized string overlap |

---

## 3. Structured PII Value Distribution & Overlap Analysis
Because personal names in India follow demographic frequency distributions, popular given names (e.g., *Rahul*, *Sneha*) occur naturally across both training and testing carrier templates. However:
- Full synthetic person names (given name + patronymic/surname combinations) were sampled combinatorially across distinct seed lists.
- Alphanumeric identifiers (Aadhaar, PAN, Bank Accounts) were generated using disjoint random seeds.
- In SV-01 and SV-02 scientific audits, exact alphanumeric entity string overlap between train and test was verified to be zero.

---

## 4. Formal Certification Statement
> **Authoritative Statement**:
> No evidence of identity leakage was observed under the evaluated checks.
> 
> *Methodological Note*: The benchmark splits are empirically disjoint at the base instance, record ID, and carrier text levels. However, as with all finite natural-language corpora, semantic similarity in common carrier phrasing (e.g., "My name is...") is inherently present across independent English and Hindi sentences.

---

## 5. Audit Sign-off
**Audit Outcome**: **PASS**  
**Leakage Risk**: **NEGLIGIBLE / CONTROLLED**
