import hashlib
import json
from pathlib import Path

ROOT = Path(".")

CANONICAL_22 = {
    "data/raw/base_instances.jsonl": "7006b0c9227d93541d2b71f702407ecc",
    "data/raw/hard_negative_bases.jsonl": "b36c6c106548d18ff7083fd00532cb07",
    "data/generated/language_realizations.jsonl": "0cb046740507eb9111a214b24b680483",
    "data/generated/hard_negative_realizations.jsonl": "ae5537eec4129822e3d97b05170b4fea",
    "data/generated/adversarial_realizations.jsonl": "1b678b9597737c85197acf80ab56878d",
    "annotation/review_template.csv": "78c5767f2f8fede2021ff344aaddc32c",
    "predictions/regex_1.0.0_v0.18.jsonl": "8913ac633854a36948a3445e4be0594d",
    "reports/evaluation_regex_1.0.0_v0.18.json": "2958f77985fcc70d704c123e9e952ebd",
    "predictions/spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.jsonl": "6c74bd4ec742a1f0c6b8024200937fb5",
    "reports/evaluation_spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.json": "a9745314b2e71df861ea71af15a9dd1a",
    "predictions/presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.jsonl": "2c661403efa963275be5f2559a1577b9",
    "reports/evaluation_presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.json": "4831393231e3d15dc674166dcaaaa2b9",
    "predictions/transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.jsonl": "3f53b646fb9f95414bef8b972d2277b1",
    "reports/evaluation_transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.json": "dfe7e6b93e15ca266b29121977b1809e",
    "predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.jsonl": "e589c2a3daa96e8a3963d95fecb89012",
    "predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.jsonl": "e589c2a3daa96e8a3963d95fecb89012",
    "predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.jsonl": "e11d924839cdddebd59104624f667357",
    "predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.jsonl": "a0b17f4b93251463319d0dc1409514bf",
    "reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.json": "d3a9f9da8e848c7cafb9cf43299b9439",
    "reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.json": "06ca5638e48dc492c016166d8b1d12a2",
    "reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.json": "cfb422de399fa7cb13dec4e30f7b29e1",
    "reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.json": "90a0a0c9bb83dd4d2f456b6e0f508753",
}

B6_ARTIFACTS = [
    "predictions/experiments/b6/transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.jsonl",
    "predictions/experiments/b6/transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed42_v0.18.jsonl",
    "predictions/experiments/b6/transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed43_v0.18.jsonl",
    "predictions/experiments/b6/transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed44_v0.18.jsonl",
    "reports/experiments/b6/evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.json",
    "reports/experiments/b6/evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed42_v0.18.json",
    "reports/experiments/b6/evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed43_v0.18.json",
    "reports/experiments/b6/evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed44_v0.18.json",
    "reports/experiments/b6/b6_error_summary.json",
    "reports/experiments/b6/b6_boundary_analysis.json",
    "reports/experiments/b6/b6_false_positive_analysis.json",
    "reports/experiments/b6/b6_type_analysis.json",
    "reports/experiments/b6/b6_language_analysis.json",
    "reports/experiments/b6/b6_perturbation_analysis.json",
    "reports/experiments/b6/b6_difficulty_analysis.json",
    "reports/experiments/b6/b6_hard_negative_analysis.json",
    "reports/experiments/b6/b6_b5_vs_b6_transition.json",
    "reports/experiments/b6/b6_error_interactions.json",
    "reports/experiments/b6/b6_representative_cases.json",
    "reports/experiments/b6/B6_FINAL_REPORT.md",
]

SV_ARTIFACTS = [
    "reports/scientific_validation_sv01_b5_distribution_audit.json",
    "reports/scientific_validation_sv01_b5_distribution_audit.md",
    "reports/experiments/sv02/SV02_FINAL_REPORT.md",
    "reports/experiments/sv02/sv02_master_evaluation.json",
    "reports/experiments/sv03/SV03_FINAL_REPORT.md",
    "reports/experiments/sv03/sv03_error_summary.json",
    "reports/experiments/sv03/sv03_boundary_analysis.json",
    "reports/experiments/sv03/sv03_false_positive_analysis.json",
    "reports/experiments/sv03/sv03_type_analysis.json",
    "reports/experiments/sv03/sv03_b5_vs_sv02_transition.json",
]


def hash_file(p: Path) -> str:
    with open(p, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def main():
    all_hashes = {}
    canonical_match = True

    for path, expected in CANONICAL_22.items():
        p = ROOT / path
        actual = hash_file(p)
        matched = actual == expected
        if not matched:
            canonical_match = False
        all_hashes[path] = {
            "category": "canonical_locked_22",
            "expected_md5": expected,
            "actual_md5": actual,
            "status": "MATCH" if matched else "MISMATCH",
        }

    for path in B6_ARTIFACTS:
        p = ROOT / path
        actual = hash_file(p)
        all_hashes[path] = {
            "category": "b6_experimental_locked",
            "actual_md5": actual,
            "status": "FROZEN",
        }

    for path in SV_ARTIFACTS:
        p = ROOT / path
        actual = hash_file(p)
        all_hashes[path] = {
            "category": "scientific_validation_locked",
            "actual_md5": actual,
            "status": "FROZEN",
        }

    print("Canonical 22 Match:", canonical_match)
    assert canonical_match, "FATAL: Canonical artifact MD5 mismatch!"

    # Write JSON
    Path("reports/final").mkdir(parents=True, exist_ok=True)
    with open("reports/final/CANONICAL_ARTIFACT_HASHES.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "freeze_stage": "SCIENTIFIC_FREEZE_B6",
                "total_audited_artifacts": len(all_hashes),
                "canonical_locked_22_matched": canonical_match,
                "artifacts": all_hashes,
            },
            f,
            indent=2,
        )

    # Write Markdown
    md_lines = [
        "# Canonical Artifact MD5 Hashes & Immutability Register",
        "",
        "**Benchmark**: Indian PII Robustness Benchmark v0.18  ",
        "**Freeze Phase**: Scientific Freeze (Terminal Baseline B6)  ",
        "**Verification**: 100% Bitwise Match on Prior Canonical Baselines and Datasets  ",
        "",
        "## 1. Prior 22 Canonical Locked Artifacts",
        "",
        "| Rel Path | Expected MD5 | Actual MD5 | Status |",
        "| :--- | :--- | :--- | :---: |",
    ]

    for path, d in all_hashes.items():
        if d["category"] == "canonical_locked_22":
            md_lines.append(
                f"| `{path}` | `{d['expected_md5']}` | `{d['actual_md5']}` | **{d['status']}** |"
            )

    md_lines.extend(
        [
            "",
            "## 2. Baseline B6 Frozen Experimental Artifacts",
            "",
            "| Rel Path | Frozen MD5 | Status |",
            "| :--- | :--- | :---: |",
        ]
    )

    for path, d in all_hashes.items():
        if d["category"] == "b6_experimental_locked":
            md_lines.append(f"| `{path}` | `{d['actual_md5']}` | **{d['status']}** |")

    md_lines.extend(
        [
            "",
            "## 3. Scientific Validation (SV-01, SV-02, SV-03) Frozen Artifacts",
            "",
            "| Rel Path | Frozen MD5 | Status |",
            "| :--- | :--- | :---: |",
        ]
    )

    for path, d in all_hashes.items():
        if d["category"] == "scientific_validation_locked":
            md_lines.append(f"| `{path}` | `{d['actual_md5']}` | **{d['status']}** |")

    with open("reports/final/CANONICAL_ARTIFACT_HASHES.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print("Canonical artifact hashes successfully audited and saved.")


if __name__ == "__main__":
    main()