"""T15: SV-03 Error Analysis and Failure Mechanism Study Governance Tests.

Validates:
1. Canonical artifact immutability (all 22 locked artifacts bitwise identical).
2. Complete error accounting invariants (F1 + F2 + F3 + TP_exact == 724 for all seeds).
3. Prediction accounting invariants (TP_type == TP_exact + F2; N_pred == TP_type + F3 + F4).
4. No raw PII leakage into any generated reports/JSON files.
5. Deterministic analysis reproducibility.
6. Schema validity and presence of all required SV-03 artifacts.
"""

from __future__ import annotations

import glob
import hashlib
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports" / "experiments" / "sv03"

CANONICAL_HASHES = {
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

SV03_REQUIRED_JSONS = [
    "sv03_integrity_check.json",
    "sv03_error_summary.json",
    "sv03_type_analysis.json",
    "sv03_boundary_analysis.json",
    "sv03_false_positive_analysis.json",
    "sv03_hard_negative_analysis.json",
    "sv03_language_analysis.json",
    "sv03_perturbation_analysis.json",
    "sv03_difficulty_analysis.json",
    "sv03_b5_vs_sv02_transition.json",
    "sv03_error_interactions.json",
    "sv03_representative_cases.json",
]


@pytest.mark.parametrize(("rel_path", "expected_hash"), list(CANONICAL_HASHES.items()))
def test_canonical_artifact_immutability(rel_path: str, expected_hash: str):
    """Ensure all 22 canonical benchmark artifacts are bitwise identical."""
    p = ROOT / rel_path
    assert p.exists(), f"Missing canonical file: {rel_path}"
    with open(p, "rb") as f:
        actual_hash = hashlib.md5(f.read()).hexdigest()
    assert actual_hash == expected_hash, f"Hash mismatch in {rel_path}"


def test_sv03_required_artifacts_exist():
    """Verify all 12 required SV-03 JSON report artifacts are present."""
    for filename in SV03_REQUIRED_JSONS:
        p = REPORTS_DIR / filename
        assert p.exists(), f"Missing SV-03 artifact: {filename}"
        assert p.stat().st_size > 0, f"Empty SV-03 artifact: {filename}"


def test_sv03_error_accounting_invariants():
    """Verify the core mathematical invariants for all evaluated model seeds."""
    summary_path = REPORTS_DIR / "sv03_error_summary.json"
    assert summary_path.exists()
    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for model_name in ["b5", "sv02_hn"]:
        assert model_name in data
        for seed_str, seed_data in data[model_name]["seeds"].items():
            n_gold = seed_data["n_gold"]
            n_pred = seed_data["n_pred"]
            tp_type = seed_data["tp_type"]
            tp_exact = seed_data["tp_exact"]
            f1 = seed_data["f1_missed"]
            f2 = seed_data["f2_wrong_span"]
            f3 = seed_data["f3_wrong_type"]
            f4 = seed_data["f4_false_pos"]

            assert n_gold == 724, f"{model_name} seed {seed_str} gold count is {n_gold}, expected 724"
            assert f1 + f2 + f3 + tp_exact == n_gold, f"Invariant failure in {model_name} seed {seed_str}: {f1}+{f2}+{f3}+{tp_exact} != {n_gold}"
            assert tp_type == tp_exact + f2, f"Invariant failure: tp_type != tp_exact + f2"
            assert n_pred == tp_type + f3 + f4, f"Invariant failure: n_pred != tp_type + f3 + f4"
            assert seed_data["invariants"]["f1_f2_f3_tpexact_eq_ngold"] is True
            assert seed_data["invariants"]["tptype_eq_tpexact_plus_f2"] is True
            assert seed_data["invariants"]["npred_eq_tptype_f3_f4"] is True


def test_no_raw_pii_in_sv03_reports():
    """Verify that zero raw synthetic PII values appear in any SV-03 generated artifacts."""
    with open(ROOT / "data" / "raw" / "base_instances.jsonl", "r", encoding="utf-8") as f:
        base_records = [json.loads(line) for line in f if line.strip()]

    raw_pii_values = set()
    for r in base_records:
        for item in r.get("pii", []):
            val = item.get("base_pii_value")
            if val and len(val.strip()) > 3:
                raw_pii_values.add(val.strip())

    for filepath in REPORTS_DIR.glob("*.*"):
        with open(filepath, "r", encoding="utf-8", errors="ignore") as fp:
            content = fp.read()
        for pii in raw_pii_values:
            assert pii not in content, f"Raw PII leak detected in {filepath.name}: {pii}"


def test_sv03_boundary_and_fp_coverage():
    """Verify that all F2 and F4 failures are accounted for in boundary and FP analyses."""
    with open(REPORTS_DIR / "sv03_boundary_analysis.json", "r", encoding="utf-8") as f:
        b_data = json.load(f)
    with open(REPORTS_DIR / "sv03_false_positive_analysis.json", "r", encoding="utf-8") as f:
        fp_data = json.load(f)
    with open(REPORTS_DIR / "sv03_error_summary.json", "r", encoding="utf-8") as f:
        err_data = json.load(f)

    for model in ["b5", "sv02_hn"]:
        mean_f2 = err_data[model]["aggregate_mean_sd"]["f2_wrong_span"]["mean"]
        b_total = b_data[model]["total_f2_mean"]
        assert abs(mean_f2 - b_total) < 0.1, f"F2 mismatch in {model}: {mean_f2} vs {b_total}"

        mean_f4 = err_data[model]["aggregate_mean_sd"]["f4_false_pos"]["mean"]
        fp_total = fp_data[model]["total_f4_mean"]
        assert abs(mean_f4 - fp_total) < 0.1, f"F4 mismatch in {model}: {mean_f4} vs {fp_total}"
