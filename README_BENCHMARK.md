# Indian PII Robustness Benchmark

[![Benchmark Version](https://img.shields.io/badge/benchmark-v0.18-blue.svg)](docs/DATASET.md)
[![Scientific Freeze](https://img.shields.io/badge/scientific_freeze-APPROVED-success.svg)](reports/FINAL_FREEZE_DECLARATION.md)
[![Python Version](https://img.shields.io/badge/python-3.10-informational.svg)](pyproject.toml)
[![Data Integrity](https://img.shields.io/badge/data-100%25_synthetic-brightgreen.svg)](docs/DATASET.md)

An empirical benchmark for evaluating the accuracy, exact-boundary precision, and perturbation robustness of Personally Identifiable Information (PII) extraction systems in Indian multilingual contexts.

---

## 1. What the Benchmark Is

The **Indian PII Robustness Benchmark** is a standardized, multi-lingual, perturbation-aware evaluation framework designed to measure how effectively Natural Language Processing (NLP) systems detect and de-identify sensitive Indian personal data.

The benchmark evaluates six baseline systems spanning:
- Deterministic rule engines (**B1 Regex**)
- General-domain pretrained neural models (**B2 spaCy**)
- Industrial hybrid frameworks (**B3 Microsoft Presidio**)
- Pretrained multilingual transformers (**B4 Zero-Shot XLM-RoBERTa**)
- Indian-adapted transformers with independent token heads (**B5**)
- Indian-adapted transformers with sequence-constrained CRF decoding (**B6**)

---

## 2. Why It Exists

Standard industrial PII de-identification tools (e.g., Presidio, spaCy) are overwhelmingly calibrated on Western naming conventions, clean alphanumeric formats, and English syntax. When deployed on Indian conversational and administrative text, these tools exhibit severe performance degradation:
1. **Linguistic Diversity**: Frequent code-mixing (Hinglish), transliteration into Latin script, and use of native Indic scripts (Devanagari).
2. **Distinct Statutory Syntaxes**: Unique identifier formats such as Aadhaar (12 digits), PAN (10 alphanumeric), Voter ID (EPIC), and UPI virtual payment addresses.
3. **Real-World Orthographic Noise**: Informal whitespace insertion (e.g., `1 2 3 4 5 6 7 8 9 0 1 2`), phonetic substitutions, OCR noise, and irregular delimiter usage.

This benchmark provides the first systematically controlled evaluation corpus to diagnose failure modes and quantify architectural solutions.

---

## 3. Dataset Size & Scope

- **Canonical Test Corpus**: **964 records** containing **724 gold standard Indian PII entities**.
- **Base Clean Instances**: 200 records (200 gold entities).
- **Language Realizations**: 400 records (400 gold entities).
- **Adversarial Perturbations**: 314 records (124 gold entities, 190 control records).
- **Pure Hard-Negative Decoys**: 50 records (0 gold entities).
- **Disjoint Adaptation Set**: 200 base instances (1,000 sequences) completely independent of test instances (0% instance overlap audited in SV-01).

---

## 4. Supported PII Categories

The benchmark evaluates 9 Indian PII categories:
1. `NAME`: Indian personal names across regional demographics.
2. `PHONE`: 10-digit mobile numbers, landlines, and international formats.
3. `EMAIL`: Personal and business email addresses.
4. `AADHAAR`: 12-digit Indian unique identity numbers.
5. `PAN`: 10-character alphanumeric Permanent Account Numbers.
6. `PASSPORT`: Indian passport numbers (1 letter + 7 digits).
7. `VOTER_ID`: Election Photo Identity Card numbers (3 letters + 7 digits).
8. `DRIVING_LICENSE`: Indian state-prefixed driving licenses.
9. `UPI_ID`: Unified Payments Interface handles (`name@bank`).

---

## 5. Languages & Script Realization Regimes

1. **`EN`**: Formal and informal English context (200 gold entities).
2. **`HINGLISH`**: Code-mixed Hindi-English in Latin script (100 gold entities).
3. **`HI_DEVA_PII`**: Hindi context with PII expressed in Devanagari script (100 gold entities).
4. **`HI_LATN_PII`**: Hindi text phonetically transliterated into Latin script (100 gold entities).
5. **`MIXED`**: Multi-script code-switching between Devanagari and Latin (50 gold entities).

---

## 6. Robustness Dimensions & Perturbations

- **`clean`**: Unperturbed standard format.
- **`a1_whitespace`**: Internal space insertion within structured identifiers.
- **`a2_phonetic`**: Phonetic character swaps and regional transliteration variation.
- **`a3_ocr`**: Optical Character Recognition confusion artifacts (`0` $\leftrightarrow$ `O`, `1` $\leftrightarrow$ `I`).
- **`a4_script_mix`**: Cross-script character substitutions (e.g., Devanagari numerals in Latin text).
- **`a5_delimiters`**: Irregular delimiters, hyphens, and non-standard symbols.
- **Hard-Negative Decoys**: 50 records containing non-PII numeric sequences (courier tracking numbers, order codes, bank reference numbers) designed to test false-positive suppression.

---

## 7. Baseline Paradigms (B1–B6)

| Baseline | Paradigm | Architecture | Decoding Strategy | Evaluation Mode |
| :--- | :--- | :--- | :--- | :--- |
| **B1** | Regex | Deterministic rules (v1.0.0) | Regular expression patterns | Single-run |
| **B2** | spaCy | `en_core_web_sm` (v3.8.16) | Statistical transition parser | Single-run |
| **B3** | Presidio | Microsoft Presidio (v2.2.364) | Hybrid rules + spaCy context | Single-run |
| **B4** | Zero-Shot XLM-R | `Davlan/xlm-roberta-base-ner-hrl` | Independent softmax token head | Single-run |
| **B5** | Adapted XLM-R | Fine-tuned XLM-RoBERTa Base | Independent softmax token head | 3-seed Mean ± SD |
| **B6** | Adapted XLM-R + CRF | Fine-tuned XLM-RoBERTa Base | First-Order Linear Chain CRF | 3-seed Mean ± SD |

---

## 8. Frozen Scientific Results Table

> **Note on Methodology**: Single-run baselines (B1–B4) are evaluated once. Adapted baselines (B5, B6) are evaluated across three random adaptation seeds ($S \in \{42, 43, 44\}$) and reported as **Mean ± Sample Standard Deviation (ddof=1)**. Exact boundary matching ($M_4$) requires character-level start, end, and type alignment.

| Baseline | System / Model | Mode | M1 Precision | M2 Recall | M3 Type F1 | M4 Exact F1 | M6 FPR | $TP_{exact}$ | $F_2$ Boundary | $F_4$ False Pos |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **B1** | Regex (Canonical v1.0.0) | Single-run | 0.6478 | 0.5207 | 0.5773 | **0.5773** | 0.2371 | 377 | 0 | 138 |
| **B2** | spaCy `en_core_web_sm` | Single-run | 0.0315 | 0.0608 | 0.0415 | **0.0330** | 0.6316 | 35 | 9 | 883 |
| **B3** | Presidio (IN Recognizers) | Single-run | 0.0766 | 0.2956 | 0.1217 | **0.1149** | 0.7539 | 202 | 12 | 2105 |
| **B4** | Zero-Shot XLM-RoBERTa | Single-run | 0.2013 | 0.1298 | 0.1579 | **0.1444** | 0.6039 | 86 | 8 | 282 |
| **B5** | Indian-Adapted XLM-R | 3-seed Mean | 0.4312 ± 0.0030 | 0.9742 ± 0.0008 | 0.5978 ± 0.0029 | **0.3860 ± 0.0061** | 0.5580 ± 0.0032 | 455.3 ± 5.0 | 250.0 ± 5.0 | 912.7 ± 11.7 |
| **B6** | Indian-Adapted XLM-R + CRF | 3-seed Mean | **0.6315 ± 0.0021** | 0.9319 ± 0.0035 | **0.7528 ± 0.0022** | **0.6654 ± 0.0034** | **0.3292 ± 0.0025** | **596.3 ± 4.5** | **78.3 ± 2.1** | **351.7 ± 4.5** |

*All results are permanently frozen as of September 9, 2026. See [`reports/final/MASTER_RESULTS_TABLE.md`](reports/final/MASTER_RESULTS_TABLE.md).*

---

## 9. Evaluation Metrics & Invariants

- **$M_1$ Precision (Type-Strict)**: Fraction of emitted predictions matching gold entity type with non-zero overlap.
- **$M_2$ Recall (Type-Strict)**: Fraction of gold entities detected with correct type.
- **$M_3$ Type F1 Score**: Harmonic mean of Type-Strict Precision and Recall.
- **$M_4$ Exact F1 Score**: Strict metric requiring exact character start offset, end offset, and entity type match.
- **$M_5$ Type Accuracy**: Classification accuracy conditional on span localization.
- **$M_6$ False Positive Rate (Entity-level)**: $\frac{F_4}{N_{pred}}$.
- **Error Partition Invariant**: Every evaluation satisfies $TP_{exact} + F_1 + F_2 + F_3 = N_{gold} = 724$.

See [`docs/METRICS.md`](docs/METRICS.md) for full mathematical specifications.

---

## 10. Installation

```bash
# Clone the repository
git clone https://github.com/TODO-repo-placeholder/indian-pii-robust.git
cd indian-pii-robust

# Create virtual environment (Python 3.10 recommended)
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .venv\Scripts\Activate.ps1

# Install exact frozen dependencies
pip install -r requirements-lock.txt
```

---

## 11. Dataset Format

Benchmark records are stored in JSON Lines (`.jsonl`) format:
```json
{
  "variant_id": "lang_hi_deva_0045",
  "base_id": "base_0045",
  "text": "कृपया अपने आधार कार्ड संख्या 5482 1204 9831 को बैंक खाते से लिंक करें।",
  "language": "HI_DEVA_PII",
  "perturbation_family": "none",
  "difficulty": "MEDIUM",
  "is_hard_negative": false,
  "entities": [
    {"type": "AADHAAR", "start": 29, "end": 43, "value": "5482 1204 9831"}
  ]
}
```
See [`docs/DATASET.md`](docs/DATASET.md) for schema details.

---

## 12. Prediction Format

Model predictions must be emitted as one JSON object per line:
```json
{"variant_id": "lang_hi_deva_0045", "type": "AADHAAR", "start": 29, "end": 43, "text": "5482 1204 9831", "confidence": 0.985}
```

---

## 13. Evaluation CLI Usage

To evaluate a predictions file against a gold standard JSONL file:
```bash
python -m benchmark.evaluate \
    --gold data/raw/base_instances.jsonl \
    --predictions predictions/regex_1.0.0_v0.18.jsonl \
    --output reports/my_eval_report.json
```

---

## 14. Reproduction

Reproduction scripts execute inference over the canonical benchmark and write exclusively to `reproduction/` (non-canonical):
```bash
# Reproduce Baseline B5 (Seed 42)
python scripts/reproduce_b5.py --seed 42 --device -1

# Reproduce Baseline B6 (Seed 42)
python scripts/reproduce_b6.py --seed 42 --device -1
```
See [`docs/CLEAN_ROOM_REPRODUCTION.md`](docs/CLEAN_ROOM_REPRODUCTION.md).

---

## 15. Scientific Freeze Status

> [!IMPORTANT]
> Scientific experimentation on this benchmark iteration is **OFFICIALLY FROZEN**.
> - No Baseline B7 will be added.
> - Canonical datasets, predictions, and reports under `data/`, `predictions/`, and `reports/` are cryptographically verified via MD5 and permanently immutable.
> - See [`reports/FINAL_FREEZE_DECLARATION.md`](reports/FINAL_FREEZE_DECLARATION.md).

---

## 16. Known Limitations

1. **A1 Whitespace Insertion Vulnerability**: When spaces are inserted within structured identifiers (e.g., `5 4 8 2 1 2 0 4 9 8 3 1`), sub-word tokenizers fragment numbers into single-digit tokens. Exact F1 in B6 collapses from $0.7812$ (clean) to $0.2941$ (A1).
2. **Held-Out Hard-Negative Decoys**: Both B5 and B6 exhibit 100% record-level False Positive Rate on pure non-PII 12-digit and 10-digit decoy numbers.
3. **Synthetic Generator Boundary**: Evaluation is conducted on rule-guided synthetic realizations. Real-world physical scan artifacts and non-Hindi Indic scripts (e.g., Tamil, Telugu, Bengali) are not yet represented.
4. See [`reports/FINAL_LIMITATIONS.md`](reports/FINAL_LIMITATIONS.md).

---

## 17. Synthetic Data & Privacy Statement

- **100% Synthetic Data**: All benchmark records, personal names, phone numbers, and identifier strings were generated synthetically using randomized templates.
- **Zero Real PII**: No data belonging to any real individual or government identity system exists in this repository.
- **Compliance**: Conforms with the Indian Digital Personal Data Protection (DPDP) Act 2023. See [`reports/final/PRIVACY_RELEASE_AUDIT.md`](reports/final/PRIVACY_RELEASE_AUDIT.md).

---

## 18. Citation

If you use this benchmark or codebase in your research, please cite:
```bibtex
@misc{indian_pii_robust_2026,
  title={Indian PII Robustness Benchmark: Multilingual, Perturbation-Aware Evaluation of Personally Identifiable Information Extraction in Indian Contexts},
  author={TODO: Author Names Pending Release Authorization},
  year={2026},
  version={0.18.0}
}
```
See [`CITATION.cff`](CITATION.cff).

---

## 19. License

- **Benchmark Code**: See [`LICENSE`](LICENSE).
- **Upstream Dependencies & Model Checkpoints**: See [`reports/artifact_engineering/LICENSE_AUDIT.md`](reports/artifact_engineering/LICENSE_AUDIT.md). Upstream model license terms require author verification prior to public binary weight distribution.
