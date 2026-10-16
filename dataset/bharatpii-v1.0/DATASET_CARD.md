# BharatPII Dataset Card: Multilingual Indian PII Robustness Benchmark

**Dataset Identifier**: `bharatpii-dataset-v1.0`  
**Version**: `1.0.0` (Benchmark Engine: `v0.18`)  
**Release Date**: September 12, 2026  
**Governance**: Benchmark Scientific Governance Committee  

---

## 1. Dataset Name
**BharatPII: Indian Multilingual Personally Identifiable Information Robustness Benchmark** (Release: `bharatpii-dataset-v1.0`).

## 2. Version
Version `1.0.0`. Corresponds to the scientifically frozen canonical benchmark corpus `v0.18`.

## 3. Motivation
Extracting personally identifiable information (PII) from Indian digital communication presents distinct challenges not addressed by Western NLP benchmarks:
- Complex regional identifier syntax (12-digit Verhoeff Aadhaar, 10-char alphanumeric PAN, UPI VPAs).
- Extreme linguistic and orthographic variation (Hindi–English code-mixing, Romanized Hindi, native Devanagari script).
- Common adversarial and informal surface noise (spacing, punctuation distortion, phonetic substitutions, character variations).
BharatPII was constructed to provide a standardized, reproducible, and fine-grained evaluation benchmark to quantify detection accuracy, boundary localization collapse, and false-alarm resistance.

## 4. Scope
The benchmark evaluates named entity recognition and token classification systems on Indian PII entities embedded in synthetic carrier sentences simulating customer support, e-commerce delivery, banking, and citizen services.

## 5. Intended Use
- Evaluating and benchmarking automated PII redaction and de-identification systems.
- Scientific error analysis of token boundary localization and false-alarm susceptibility under Indic linguistic variation.
- Assessing adversarial robustness against synthetic character and spacing perturbations.
- Training and fine-tuning privacy-preserving models using the disjoint adaptation splits.

## 6. Out-of-Scope Use
- **Do not use for surveillance, targeted profiling, or re-identification of real individuals.**
- Do not use as a standalone verification system for real government identity documents.
- Do not use for automated decision-making affecting individuals' legal status or rights.

## 7. Synthetic Data Statement
> [!IMPORTANT]
> **The benchmark contains synthetic PII and is not intended to represent real individuals or real credentials.**
All personal names, alphanumeric identity numbers, addresses, telephone numbers, emails, bank accounts, and UPI handles were synthetically generated using rule-guided combinatorial algorithms. Format validity does not imply association with any real person or financial institution.

## 8. PII Categories
The benchmark standardizes 8 high-impact Indian PII categories:
1. `PERSON`: Individual names across diverse Indian demographics and naming conventions.
2. `PAN`: Permanent Account Number (10-character alphanumeric).
3. `AADHAAR`: 12-digit unique identity number validated via Verhoeff checksum.
4. `PHONE`: Indian 10-digit mobile and landline numbers.
5. `EMAIL`: Synthetic email addresses using reserved non-routable domains.
6. `UPI_ID`: Unified Payments Interface handles (`handle@psp`).
7. `BANK_ACCOUNT`: Commercial bank account numbers (9–18 digits).
8. `ADDRESS`: Multi-token Indian delivery addresses with localities and 6-digit PIN codes.

## 9. Languages and Scripts
The benchmark covers 5 distinct linguistic regimes:
- **`EN`**: Standard Indian English in Latin script.
- **`IN_EN`**: Indian English carrier syntax.
- **`ROM_HI`**: Romanized Hindi (Hindi language written in Latin script).
- **`HINGLISH` / `INFORMAL_HINGLISH`**: Hindi-English code-mixed communication.
- **`HI_DEVA_PII`**: Native Hindi text written in Devanagari script.

## 10. Dataset Composition
The release consists of 2,164 total records across three strictly disjoint splits:
- **Adaptation Train Split** (`data/train/train.jsonl`): 1,000 records, 1,000 entities, 200 base IDs (exactly 125 instances per PII category).
- **Adaptation Validation Split** (`data/validation/val.jsonl`): 200 records, 200 entities, 40 base IDs (exactly 25 instances per PII category).
- **Canonical Test Benchmark** (`data/test/test_inputs.jsonl`): 964 records, 724 gold entities, 120 base IDs (100 positive base IDs + 20 hard-negative base IDs).

## 11. Annotation Methodology
Data construction followed a two-phase generative and verification protocol:
1. **Rule-Guided Parametric Generation**: Base seed instances and linguistic realizations were generated using deterministic template engines parameterizing carrier text, entity syntax, and perturbation operators.
2. **Human Expert Verification**: 100% of canonical benchmark records were reviewed via a standardized 25-column adjudication template (`review_template.csv`) verifying span boundaries, category assignments, naturalness, and recoverability.

## 12. Split Methodology & Leakage Isolation
Splits were constructed using strict **base-instance disjoint stratification**:
- Every base instance family exists in exactly ONE split.
- $\text{Train Bases} \cap \text{Val Bases} = \emptyset$
- $\text{Train Bases} \cap \text{Test Bases} = \emptyset$
- $\text{Val Bases} \cap \text{Test Bases} = \emptyset$
- Record ID overlap = 0.
- Raw text overlap = 0 across splits.

## 13. Hard Negatives
The test set incorporates **140 hard-negative distractor records** (20 base instances + 120 realizations):
- Syntactically structured numeric sequences (12-digit order IDs, tracking numbers resembling Aadhaar).
- 10-character alphanumeric strings (promo codes, coupon vouchers resembling PAN).
- Purpose: Benchmarking false-positive resistance and measuring model specificity ($M_6$ FPR).
- Invariant: Hard-negative records contain **zero gold PII entities**.

## 14. Adversarial Stress-Test Variants
The test set contains **100 adversarial stress records** distributed across 5 balanced perturbation families (20 records each):
- **A1 Spacing**: Intra-identifier whitespace insertion (e.g., `B D T N L 5 6 9 8 D`).
- **A2 Punctuation**: Punctuation injection (e.g., `BDTNL-5698-D`).
- **A3 Label Obfuscation**: Camouflaged field descriptors and indirect phrasing.
- **A4 Informal Abbreviation**: Chat shorthand, slang, and phonetic abbreviations.
- **A5 Character Variation**: Leet-speak and optical character substitutions (e.g., `0` for `O`, `1` for `I`).

## 15. Quality Assurance
Automated verification asserts:
- Zero malformed JSONL records.
- 100% compliance with the character-offset slicing contract: `text[start:end] == entity.text`.
- Zero inverted spans (`start < end`).
- 100% valid IOB2 sequence transitions.

## 16. Leakage Controls
Automated cross-split leakage audits verify zero base ID, record ID, or text overlap between development and test data.
Evaluation result: *No evidence of identity leakage was observed under the evaluated checks.*

## 17. Known Limitations
- Synthetically generated carrier sentences do not capture all nuances of spontaneous speech or multi-turn dialogues.
- Coverage is focused on 8 high-risk PII categories; specialized identifiers (such as Voter ID or Driving License) are not included in this release.
- Context lengths are capped at paragraph-level sentences (maximum ~128 tokens).

## 18. Ethical Considerations
PII de-identification is critical for data privacy compliance under India's Digital Personal Data Protection (DPDP) Act 2023. This benchmark is developed to strengthen privacy-enhancing technologies. Dual-use risks (e.g., using extraction models for mass data harvesting) are mitigated by releasing synthetic benchmarks rather than scrapings of real personal data.

## 19. Privacy Considerations
- Zero real personal records, corporate secrets, or credentials are contained in the dataset.
- Format compliance with Indian identity syntax is purely structural.

## 20. License
- Recommended License: **Creative Commons Attribution 4.0 International (CC BY 4.0)**.
- Formal Governance Ratification Status: **UNRESOLVED PENDING GOVERNANCE BOARD APPROVAL**.
- Software package is licensed separately under the MIT License.

## 21. Citation
```bibtex
@dataset{bharatpii2026,
  author    = {Matnale, Veeraj Sanjog and Jadhav, Vedant Vinayak and More, Tanushree Dinesh and Kharat, Pratiksha Santosh and Jadhav, Kiran},
  title     = {BharatPII: Multilingual, Perturbation-Aware Benchmark for Personally Identifiable Information Extraction in Indian Contexts},
  year      = {2026},
  version   = {1.0.0},
  publisher = {BharatPII Research Consortium}
}
```

## 22. Maintenance and Governance
Maintained by the BharatPII Scientific Governance Committee. For benchmark verification and evaluation access, consult [`DATA_RELEASE_POLICY.md`](DATA_RELEASE_POLICY.md).
