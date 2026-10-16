# Annotation Specification & Span Boundary Guidelines
**Document Identifier**: `DOCS-ANNOTATION-V1.0`  
**Benchmark Version**: `0.18`  
**Higher Authority Contract**: [`annotation/guidelines.md`](file:///n:/PROJECTS/indian-pii-robust/annotation/guidelines.md)  
**Status**: APPROVED  
**Date**: September 9, 2026  

---

## 1. Authority Hierarchy

The definitive authority on all entity definitions, span boundaries, script policies, and ambiguity resolutions is the companion contract:
**[`annotation/guidelines.md` v0.18](file:///n:/PROJECTS/indian-pii-robust/annotation/guidelines.md)**.

This document summarizes the core annotation conventions and boundaries for researchers and external evaluators. Where any conflict appears, `annotation/guidelines.md` strictly supersedes.

---

## 2. Span Boundary & Offset Conventions

1. **Character-Level Offsets**: All entity spans are demarcated by 0-indexed Python Unicode code-point offsets `[start, end)`.
   - `start`: Index of the first character of the entity.
   - `end`: Index immediately following the last character of the entity.
   - Exact Slice Invariant: `text[start:end] == entity_value`.
2. **Exclusion of Contextual Particles**: Leading or trailing punctuation, quotation marks, introductory prefixes (e.g., `"Aadhaar:"`, `"PAN No:"`), and conversational markers must NOT be included within the entity span.
3. **Internal Spacing**: For structured identifiers that natively contain internal delimiters or spaces (e.g., formatted Aadhaar `"5482 1204 9831"` or spaced phone numbers), the internal spaces are preserved as part of the entity span.

---

## 3. PII Entity Taxonomy & Label Rules

| PII Type | Valid Structure / Syntax | Boundary Rule |
| :--- | :--- | :--- |
| **`NAME`** | Full personal names (e.g., `"Sunita Rao"`, `"Amitabh Kumar"`) | Includes title/honorific ONLY if syntactically fused; excludes external greetings. |
| **`PHONE`** | 10-digit mobile, landlines, or international format | Includes country code (`+91`) if directly prefixed; excludes labels (`"Mob:"`). |
| **`EMAIL`** | Standard RFC-compliant address format | Bounds from first alphanumeric character to top-level domain suffix. |
| **`AADHAAR`** | 12 digits (with optional spaces/hyphens every 4 digits) | Exact 12 digits (or 14 characters if spaced `XXXX XXXX XXXX`). |
| **`PAN`** | 10 alphanumeric characters (`[A-Z]{5}[0-9]{4}[A-Z]`) | Exactly 10 characters; case-insensitive in text, normalized in uppercase. |
| **`PASSPORT`** | 1 uppercase letter followed by 7 digits (`[A-Z][0-9]{7}`) | Exactly 8 alphanumeric characters. |
| **`VOTER_ID`** | 3 uppercase letters followed by 7 digits (`[A-Z]{3}[0-9]{7}`) | Exactly 10 alphanumeric characters. |
| **`DRIVING_LICENSE`**| State prefix (2 letters) followed by 13-14 alphanumeric chars | Entire license string including hyphens if present. |
| **`UPI_ID`** | Virtual Payment Address (`[a-zA-Z0-9.\-_]+@[a-zA-Z]+`) | Starts at handle and ends at the bank identifier suffix. |

---

## 4. Hard-Negative and Decoy Policy

To guard against detectors relying on local alphanumeric shape without contextual understanding, the benchmark incorporates pure hard negatives:
- **Structural Decoys**: 12-digit numbers that are not Aadhaar numbers (e.g., bill numbers, courier barcodes, transaction IDs).
- **Alphanumeric Decoys**: 10-character alphanumeric strings that mimic PAN syntax but refer to product SKU codes or train reservation PNRs.
- **Annotation Policy**: In hard-negative instances, the decoy strings are explicitly **unannotated** (`entities: []`). Any prediction emitted on these strings is scored as an $F_4$ False Positive.

---

## 5. Adversarial Perturbation Annotation Policy

When perturbation operators inject noise into PII entities:
- **A1 Whitespace Insertion**: If spaces are inserted between characters of an entity (e.g., `"A B C D E 1 2 3 4 F"`), the entire perturbed sequence is labeled as a single unified entity span. Sub-token segmentation by a model is penalized as an $F_2$ boundary error.
- **A2 Phonetics / A3 OCR / A4 Script Mix**: Even if characters are misspelled or cross-script substituted, the ground truth bounds the full corrupted span and retains the original intended entity type.

---

## 6. Review & Adjudication Workflow

All canonical records underwent two-phase expert review:
1. Automated schema and span boundary validation (`validators/spans.py`, `validators/structural.py`).
2. Human adjudicator review recorded in `annotation/review_template.csv` confirming 100% agreement on entity boundaries and category types.
