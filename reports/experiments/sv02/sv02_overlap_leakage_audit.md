# SV-02 Dataset Overlap and Leakage Audit Report

**Date:** 2026-09-03  
**Canonical Test Corpus Size:** 964 records (120 Base IDs, 724 gold entities)  
**Overall Audit Verdict:** **PASS — ZERO LEAKAGE DETECTED ACROSS ALL SV-02 VARIANTS**  

## 1. Variant Audit Summary Table

| Variant | Train Records | Val Records | Train Tokens | Base-ID Overlap | Text Overlap | HN Label Violations | Span Errors | Status |
|:---|---:|---:|---:|---:|---:|---:|---:|:---|
| `b5_hard_negative` | 1250 | 250 | 24464 | 0 | 0 | 0 | 0 | **PASS** |
| `b5_positive_matched` | 1250 | 250 | 24164 | 0 | 0 | 0 | 0 | **PASS** |
| `b5_format_diversity` | 1250 | 250 | 24585 | 0 | 0 | 0 | 0 | **PASS** |

## 2. Key Audit Findings
1. **Base-ID Isolation:** Zero base IDs from the canonical benchmark test set appear in any SV-02 training or validation split.
2. **Text Disjointness:** Zero exact or whitespace/case-normalized text overlap exists between SV-02 adaptation sets and the canonical test set.
3. **Hard-Negative Integrity:** All 300 synthetic hard negatives (250 train, 50 val) in `b5_hard_negative` are strictly 100% labeled `O` with 0 entities.
4. **Span Alignment:** 100% of entity character offsets in all variants match their underlying text substrings exactly.
5. **Token-Budget Matching:** `b5_hard_negative` (24,464 tokens), `b5_positive_matched` (24,164 tokens), and `b5_format_diversity` (24,585 tokens) are closely budget-matched.
