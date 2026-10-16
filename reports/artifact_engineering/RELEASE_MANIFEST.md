# Indian PII Robustness Benchmark — Release Manifest
**Phase**: Artifact Engineering V1 (Post-Scientific-Freeze)
**Total Audited Files**: 382

## 1. Classification Summary

| Category | Count | Description |
| :--- | :---: | :--- |
| **`RELEASE_REQUIRED`** | 81 | Required for minimal public release and reproduction |
| **`OPTIONAL`** | 53 | Extended test suites and adaptation data |
| **`ARCHIVE_ONLY`** | 143 | Historical evidence, checkpoints, and experiment logs |
| **`DEVELOPMENT_ONLY`** | 105 | Internal generators and development utilities |

## 2. Public Figure Audit

| Figure ID | PNG Filename | Source JSON | Status | Resolution / Verification |
| :--- | :--- | :--- | :---: | :--- |
| **fig1** | `fig1_b1_b6_overall_f1.png` | `fig1_b1_b6_overall_f1.json` | **`VERIFIED`** | File size: 177,936 bytes. JSON source valid. |
| **fig2** | `fig2_b1_b6_precision_recall.png` | `fig2_b1_b6_precision_recall.json` | **`VERIFIED`** | File size: 193,162 bytes. JSON source valid. |
| **fig3** | `fig3_b5_b6_error_partition.png` | `fig3_b5_b6_error_partition.json` | **`VERIFIED`** | File size: 195,329 bytes. JSON source valid. |
| **fig4** | `fig4_b5_b6_boundary_errors.png` | `fig4_b5_b6_boundary_errors.json` | **`VERIFIED`** | File size: 186,365 bytes. JSON source valid. |
| **fig5** | `fig5_sv02_ablation.png` | `fig5_sv02_ablation.json` | **`VERIFIED`** | File size: 174,771 bytes. JSON source valid. |
| **fig6** | `fig6_sv03_fp_breakdown.png` | `fig6_sv03_fp_breakdown.json` | **`VERIFIED`** | File size: 167,071 bytes. JSON source valid. |
| **fig7** | `fig7_language_robustness.png` | `fig7_language_robustness.json` | **`VERIFIED`** | File size: 138,317 bytes. JSON source valid. |
| **fig8** | `fig8_perturbation_robustness.png` | `fig8_perturbation_robustness.json` | **`VERIFIED`** | File size: 137,702 bytes. JSON source valid. |

## 3. Release-Required Files Manifest

| File Path | Size (Bytes) |
| :--- | :---: |
| `CITATION.cff` | 1,185 |
| `LICENSE` | 1,465 |
| `README.md` | 12,326 |
| `baselines/base.py` | 2,989 |
| `baselines/presidio.py` | 4,320 |
| `baselines/regex.py` | 6,068 |
| `baselines/spacy.py` | 2,221 |
| `baselines/transformer.py` | 3,649 |
| `baselines/transformer_adapted.py` | 4,512 |
| `baselines/transformer_b6.py` | 13,292 |
| `benchmark/.gitkeep` | 0 |
| `benchmark/__init__.py` | 1,416 |
| `benchmark/evaluate.py` | 6,919 |
| `benchmark/evaluator.py` | 4,026 |
| `benchmark/failure_analysis.py` | 7,866 |
| `benchmark/matching.py` | 7,928 |
| `benchmark/metrics.py` | 6,352 |
| `benchmark/predict.py` | 6,027 |
| `benchmark/runner.py` | 6,274 |
| `benchmark/schema.py` | 5,351 |
| `benchmark/stats.py` | 5,010 |
| `data/generated/adversarial_realizations.jsonl` | 96,473 |
| `data/generated/hard_negative_realizations.jsonl` | 113,011 |
| `data/generated/language_realizations.jsonl` | 608,939 |
| `data/raw/base_instances.jsonl` | 46,608 |
| `data/raw/hard_negative_bases.jsonl` | 8,833 |
| `docs/ANNOTATION.md` | 4,562 |
| `docs/BASELINES.md` | 6,343 |
| `docs/CLEAN_ROOM_REPRODUCTION.md` | 4,670 |
| `docs/DATASET.md` | 6,117 |
| `docs/METRICS.md` | 4,444 |
| `docs/MODEL_PROVENANCE.md` | 4,775 |
| `docs/research/construction_log.md` | 98,335 |
| `pyproject.toml` | 1,404 |
| `reports/FINAL_CLAIM_AUDIT.md` | 8,848 |
| `reports/FINAL_FREEZE_DECLARATION.md` | 6,117 |
| `reports/FINAL_LIMITATIONS.md` | 6,559 |
| `reports/FINAL_SCIENTIFIC_RECORD.md` | 20,154 |
| `reports/artifact_engineering/FREEZE_BOUNDARY.md` | 6,604 |
| `reports/artifact_engineering/LICENSE_AUDIT.md` | 3,700 |
| `reports/artifact_engineering/REPOSITORY_AUDIT.md` | 4,147 |
| `reports/artifact_engineering/REPOSITORY_INVENTORY.json` | 97,153 |
| `reports/artifact_engineering/SCRATCH_AUDIT.md` | 3,964 |
| `reports/artifact_engineering/SD_RECONCILIATION.md` | 5,736 |
| `reports/final/B1_B6_COMPARISON.md` | 4,755 |
| `reports/final/CANONICAL_ARTIFACT_HASHES.json` | 12,316 |
| `reports/final/CANONICAL_ARTIFACT_HASHES.md` | 7,703 |
| `reports/final/DIFFICULTY_RESULTS.csv` | 197 |
| `reports/final/FINAL_METRIC_DEFINITIONS.md` | 3,642 |
| `reports/final/FINAL_TEST_RECORD.md` | 4,975 |
| `reports/final/MASTER_RESULTS_TABLE.csv` | 2,337 |
| `reports/final/MASTER_RESULTS_TABLE.json` | 6,024 |
| `reports/final/MASTER_RESULTS_TABLE.md` | 2,510 |
| `reports/final/PERTURBATION_RESULTS.csv` | 345 |
| `reports/final/PER_LANGUAGE_RESULTS.csv` | 948 |
| `reports/final/PER_TYPE_RESULTS.csv` | 953 |
| `reports/final/PRIVACY_RELEASE_AUDIT.md` | 4,214 |
| `reports/final/SV02_ABLATION_TABLE.csv` | 588 |
| `reports/final/SV03_ERROR_TABLE.csv` | 705 |
| `reports/final/figures/fig1_b1_b6_overall_f1.json` | 984 |
| `reports/final/figures/fig1_b1_b6_overall_f1.png` | 177,936 |
| `reports/final/figures/fig2_b1_b6_precision_recall.json` | 1,446 |
| `reports/final/figures/fig2_b1_b6_precision_recall.png` | 193,162 |
| `reports/final/figures/fig3_b5_b6_error_partition.json` | 498 |
| `reports/final/figures/fig3_b5_b6_error_partition.png` | 195,329 |
| `reports/final/figures/fig4_b5_b6_boundary_errors.json` | 575 |
| `reports/final/figures/fig4_b5_b6_boundary_errors.png` | 186,365 |
| `reports/final/figures/fig5_sv02_ablation.json` | 513 |
| `reports/final/figures/fig5_sv02_ablation.png` | 174,771 |
| `reports/final/figures/fig6_sv03_fp_breakdown.json` | 383 |
| `reports/final/figures/fig6_sv03_fp_breakdown.png` | 167,071 |
| `reports/final/figures/fig7_language_robustness.json` | 638 |
| `reports/final/figures/fig7_language_robustness.png` | 138,317 |
| `reports/final/figures/fig8_perturbation_robustness.json` | 464 |
| `reports/final/figures/fig8_perturbation_robustness.png` | 137,702 |
| `requirements-lock.txt` | 1,207 |
| `requirements.txt` | 364 |
| `scripts/audit_repository.py` | 7,921 |
| `scripts/reproduce_b5.py` | 5,105 |
| `scripts/reproduce_b6.py` | 5,097 |
| `tests/test_scientific_freeze.py` | 6,620 |
