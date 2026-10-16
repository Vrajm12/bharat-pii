# Data Release Policy: Public, Controlled, and Frozen Governance

**Document Version**: 1.0.0  
**Date**: 2026-09-12  
**Dataset Release**: `bharatpii-dataset-v1.0`  
**Governance Authority**: Benchmark Scientific Governance Committee  

---

## 1. Purpose & Benchmark Integrity Principles
A central challenge in evaluating NLP security and de-identification systems is **test-set contamination**, **train-on-test leakage**, and **leaderboard gaming**. If test-set answer keys (ground-truth entity spans) are distributed freely without boundary controls, models can easily overfit or memorize gold labels, destroying the scientific utility of the benchmark.

To prevent benchmark degradation while enabling open, reproducible research, this policy classifies all dataset assets into three formal tiers:
1. **PUBLIC**
2. **CONTROLLED**
3. **INTERNAL / FROZEN**

---

## 2. Component Classification Matrix

| Tier | Component / File | Purpose | Distribution Policy | Rationale |
|:---|:---|:---|:---:|:---|
| **PUBLIC** | `data/train/train.jsonl` | Model adaptation & training (1,000 records) | Public download | Unrestricted training data. |
| **PUBLIC** | `data/validation/val.jsonl` | Hyperparameter tuning & validation (200 records) | Public download | Unrestricted tuning data. |
| **PUBLIC** | `data/test/test_inputs.jsonl` | Official blind evaluation inputs (964 records) | Public download | Blind evaluation without answer keys. |
| **PUBLIC** | `examples/synthetic_examples.jsonl` | Demonstration examples (11 records) | Public download | Educational and integration reference. |
| **PUBLIC** | `label_schema.json` | 8 PII categories, character offset contract | Public download | Standardized output schema. |
| **PUBLIC** | `dataset_metadata.json` | Release metadata, record counts, hashes | Public download | Machine-readable provenance. |
| **PUBLIC** | `README.md`, `DATASET_CARD.md`, `REPRODUCIBILITY.md` | Complete documentation | Public download | Open science transparency. |
| **CONTROLLED** | `annotations/test_gold_annotations.jsonl` | Canonical 724 gold entity spans for 964 test records | Controlled research access | Withheld from public test archives to preserve benchmark longevity. |
| **CONTROLLED** | `annotations/review_template.csv` | Human reviewer audit sheet (964 rows) | Controlled research access | Detailed reviewer adjudication records. |
| **INTERNAL / FROZEN** | `data/raw/base_instances.jsonl` | Raw generative seed templates (100 records) | Internal locked archive | Scientific freeze immutability. |
| **INTERNAL / FROZEN** | `data/raw/hard_negative_bases.jsonl` | Raw hard-negative seed templates (20 records) | Internal locked archive | Scientific freeze immutability. |
| **INTERNAL / FROZEN** | `data/generated/*.jsonl` | Pre-split realization sets | Internal locked archive | Scientific freeze immutability. |
| **INTERNAL / FROZEN** | `predictions/`, `reports/experiments/` | Canonical baseline predictions and raw reports | Internal locked archive | Scientific freeze immutability. |

---

## 3. Public Distribution Archive (`bharatpii-dataset-v1.0.tar.gz`)
The official public distribution archive includes strictly:
- `data/train/train.jsonl`
- `data/validation/val.jsonl`
- `data/test/test_inputs.jsonl`
- `examples/synthetic_examples.jsonl`
- `docs/annotation_guidelines.md`
- `README.md`, `DATASET_CARD.md`, `label_schema.json`, `dataset_metadata.json`, `LICENSE`, `CITATION.cff`, `SHA256SUMS.txt`, `RELEASE_MANIFEST.json`, `REPRODUCIBILITY.md`

The public archive **STRICTLY EXCLUDES**:
- `annotations/test_gold_annotations.jsonl` (controlled ground truth)
- Model checkpoints and prediction files
- Internal scratch files, logs, and caches.

---

## 4. Evaluation Protocol for Independent Researchers
Independent researchers evaluating models on BharatPII:
1. Ingest `data/test/test_inputs.jsonl`.
2. Generate predictions conforming to `label_schema.json` (`record_id`, `type`, `start`, `end`, `text`, `confidence`).
3. For official benchmark scoring and leaderboard verification, predictions are submitted to the benchmark governance committee or evaluated using the controlled evaluation harness.
