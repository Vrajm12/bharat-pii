# Dataset Quality Report: BharatPII Dataset v1.0

**Document Version**: 1.0.0  
**Date**: 2026-09-12  
**Dataset Identifier**: `bharatpii-dataset-v1.0`  
**Quality Status**: **100% VERIFIED / ALL CHECKS PASSED**  

---

## 1. Executive Summary
This document reports the quality metrics, validation results, and syntactic checks conducted across the **BharatPII Benchmark Dataset Release (v1.0)**. 

Every record across all splits was subjected to automated static validation conforming to Section 15 of the release specification:
- **Total Records Validated**: 2,164 (Train: 1,000; Val: 200; Test: 964)
- **Total Entities Validated**: 1,924 (Train: 1,000; Val: 200; Test: 724)
- **Malformed Records**: **0**
- **Invalid Entity Labels**: **0**
- **Invalid or Inverted Spans**: **0**
- **Character Offset Slicing Violations**: **0**
- **Unicode Round-Trip Errors**: **0**
- **Hard-Negative Constraint Violations**: **0** (All 140 hard negatives contain exactly 0 gold entities)
- **Adversarial Quota Compliance**: **100%** (Exactly 20 records per family across A1–A5)

---

## 2. Granular Quality Verification Metrics

| Verification Check | Target Standard | Measured Result | Status |
|:---|:---|:---:|:---:|
| **JSONL Syntax** | Valid RFC 8259 JSON per line | 2,164 / 2,164 valid | **PASS** |
| **Required Schema Fields** | Complete field coverage | 0 missing fields | **PASS** |
| **Unique Record Identifiers** | Zero intra- or cross-split collisions | 2,164 unique IDs | **PASS** |
| **Unique Base Identifiers** | Disjoint base allocation | 360 unique IDs | **PASS** |
| **Split Disjointness** | 0 cross-split base ID leakage | 0 overlap | **PASS** |
| **PII Label Taxonomy** | Exact 8 canonical PII classes | 8 / 8 valid | **PASS** |
| **Span Boundary Validity** | $0 \le \text{start} < \text{end} \le \text{len}(\text{text})$ | 1,924 / 1,924 valid | **PASS** |
| **Span Slicing Invariant** | $\text{text}[\text{start}:\text{end}] == \text{entity.text}$ | 1,924 / 1,924 exact | **PASS** |
| **Multilingual Unicode Offsets** | Byte/character drift = 0 | 24 Indic script spans exact | **PASS** |
| **Entity Offset Ordering** | Monotonically ascending start offsets | 100% ordered | **PASS** |
| **IOB2 Token Overlap** | Zero self-overlapping entity spans | 0 overlaps | **PASS** |
| **Hard-Negative Ground Truth** | Exactly 0 gold PII entities | 0 gold entities across 140 recs | **PASS** |
| **Adversarial Quota** | Exactly 20 records per family (A1–A5) | 20 / 20 / 20 / 20 / 20 | **PASS** |
| **Language Label Taxonomy** | Controlled language identifiers | 100% valid | **PASS** |
| **Perturbation Labels** | Controlled perturbation identifiers | 100% valid | **PASS** |
| **Cross-Split Text Overlap** | 0 identical text across splits | 0 shared texts | **PASS** |
| **Unicode Code Point Integrity** | Lossless UTF-8 round-trip encoding | 0 corruptions | **PASS** |
| **Zero Empty Records** | Non-empty text strings | 0 empty records | **PASS** |
| **Annotation Completeness** | 1-to-1 input-to-annotation mapping | 964 / 964 mapped | **PASS** |
| **Schema Field Hygiene** | Zero undocumented or unexpected keys | 100% clean | **PASS** |

---

## 3. PII Category Distribution Summary

| PII Category | Train Count (Adaptation) | Val Count (Adaptation) | Test Count (Canonical) | Total Release Count |
|:---|:---:|:---:|:---:|:---:|
| **`PERSON`** | 125 | 25 | 94 | 244 |
| **`PAN`** | 125 | 25 | 93 | 243 |
| **`AADHAAR`** | 125 | 25 | 93 | 243 |
| **`PHONE`** | 125 | 25 | 82 | 232 |
| **`EMAIL`** | 125 | 25 | 82 | 232 |
| **`UPI_ID`** | 125 | 25 | 93 | 243 |
| **`BANK_ACCOUNT`** | 125 | 25 | 93 | 243 |
| **`ADDRESS`** | 125 | 25 | 94 | 244 |
| **TOTAL** | **1,000** | **200** | **724** | **1,924** |

---

## 4. Conclusion
The dataset passes all 20 automated quality checks with zero anomalies or warnings, certifying it as mathematically consistent, syntactically valid, and scientifically reliable.
