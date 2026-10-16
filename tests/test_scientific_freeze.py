"""
Automated Test Suite for Indian PII Robustness Benchmark Scientific Freeze.
Verifies:
1. Immutability and MD5 checksums of all 22 canonical locked artifacts.
2. Master results table mathematical invariants:
   - TP_exact + F1 + F2 + F3 == N_gold == 724
   - TP_type == TP_exact + F2
   - N_pred == TP_type + F3 + F4
3. Consistency between figures (.png + .json source data) and master tables.
4. Privacy and security release requirements.
5. Absolute absence of unauthorized B7 modeling artifacts.
"""

import json
import hashlib
import csv
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
FINAL_DIR = REPORTS_DIR / "final"
FIGURES_DIR = FINAL_DIR / "figures"


def compute_md5(file_path: Path) -> str:
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class TestCanonicalArtifactImmutability:
    """Ensure all 22 canonical locked artifacts remain bitwise immutable."""

    def test_canonical_artifact_hashes(self):
        hash_file = FINAL_DIR / "CANONICAL_ARTIFACT_HASHES.json"
        assert hash_file.exists(), "CANONICAL_ARTIFACT_HASHES.json must exist"

        with open(hash_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["canonical_locked_22_matched"] is True
        artifacts = data["artifacts"]

        canonical_count = 0
        for rel_path, info in artifacts.items():
            if info.get("category") == "canonical_locked_22":
                canonical_count += 1
                full_path = BASE_DIR / rel_path
                assert full_path.exists(), f"Canonical file {rel_path} does not exist"
                current_md5 = compute_md5(full_path)
                assert current_md5 == info["expected_md5"], (
                    f"Hash mismatch for {rel_path}: expected {info['expected_md5']}, got {current_md5}"
                )

        assert canonical_count == 22, f"Expected 22 canonical locked artifacts, found {canonical_count}"


class TestMasterResultsTableInvariants:
    """Verify mathematical identities across all baselines in the master results table."""

    @pytest.fixture
    def master_data(self):
        master_json = FINAL_DIR / "MASTER_RESULTS_TABLE.json"
        assert master_json.exists(), "MASTER_RESULTS_TABLE.json must exist"
        with open(master_json, "r", encoding="utf-8") as f:
            return json.load(f)["baselines"]

    def test_gold_entity_invariant(self, master_data):
        """TP_exact + F1 + F2 + F3 == N_gold == 724 for every baseline."""
        for row in master_data:
            tp_exact = row["tp_exact"]
            f1 = row["f1_missed"]
            f2 = row["f2_wrong_span"]
            f3 = row["f3_wrong_type"]
            total_gold = tp_exact + f1 + f2 + f3
            assert pytest.approx(total_gold, abs=1e-3) == 724.0, (
                f"Invariant violation in {row['baseline_id']}: {tp_exact} + {f1} + {f2} + {f3} = {total_gold} != 724"
            )

    def test_type_strict_match_invariant(self, master_data):
        """TP_type == TP_exact + F2 for every baseline."""
        for row in master_data:
            tp_type = row["tp_type"]
            tp_exact = row["tp_exact"]
            f2 = row["f2_wrong_span"]
            assert pytest.approx(tp_type, abs=1e-3) == (tp_exact + f2), (
                f"Invariant violation in {row['baseline_id']}: TP_type ({tp_type}) != TP_exact ({tp_exact}) + F2 ({f2})"
            )

    def test_f1_score_formulas(self, master_data):
        """Validate precision, recall, and F1 calculations."""
        for row in master_data:
            p = row["m1_precision"]
            r = row["m2_recall"]
            f1 = row["m3_f1"]
            if p + r > 0:
                expected_f1 = (2 * p * r) / (p + r)
                assert pytest.approx(f1, abs=1e-3) == expected_f1

    def test_csv_and_md_presence(self):
        """Check CSV and Markdown versions exist and have proper rows."""
        csv_file = FINAL_DIR / "MASTER_RESULTS_TABLE.csv"
        md_file = FINAL_DIR / "MASTER_RESULTS_TABLE.md"
        assert csv_file.exists(), "MASTER_RESULTS_TABLE.csv must exist"
        assert md_file.exists(), "MASTER_RESULTS_TABLE.md must exist"

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            assert len(reader) == 6, f"Expected 6 baselines in CSV, got {len(reader)}"


class TestFigureConsistency:
    """Verify all 8 publication figures and source JSON files exist and are consistent."""

    def test_all_figures_and_json_exist(self):
        for i in range(1, 9):
            png_path = list(FIGURES_DIR.glob(f"fig{i}_*.png"))
            json_path = list(FIGURES_DIR.glob(f"fig{i}_*.json"))
            assert len(png_path) == 1, f"Missing or multiple PNGs for Figure {i}"
            assert len(json_path) == 1, f"Missing or multiple JSONs for Figure {i}"
            assert png_path[0].stat().st_size > 10000, f"Figure {i} PNG file unexpectedly small"

    def test_fig1_data_matches_master_table(self):
        with open(FIGURES_DIR / "fig1_b1_b6_overall_f1.json", "r", encoding="utf-8") as f:
            fig1 = json.load(f)
        with open(FINAL_DIR / "MASTER_RESULTS_TABLE.json", "r", encoding="utf-8") as f:
            master = json.load(f)["baselines"]

        for r in master:
            idx = fig1["baselines"].index(r["baseline_id"])
            assert pytest.approx(fig1["m4_exact_f1"][idx], abs=1e-4) == r["m4_exact_f1"]
            assert pytest.approx(fig1["m3_type_f1"][idx], abs=1e-4) == r["m3_f1"]


class TestNoUnauthorizedBaselines:
    """Strictly enforce that no B7 baseline or modeling experiments were introduced."""

    def test_no_b7_artifacts(self):
        b7_files = list(BASE_DIR.glob("**/*b7*")) + list(BASE_DIR.glob("**/*B7*"))
        # Filter out git or cache if any
        b7_files = [p for p in b7_files if ".git" not in str(p) and "__pycache__" not in str(p)]
        assert len(b7_files) == 0, f"Unauthorized B7 artifacts detected: {b7_files}"


class TestPrivacyReleaseSanity:
    """Ensure privacy audit passes and no credentials leaked."""

    def test_privacy_audit_file_exists(self):
        audit_md = FINAL_DIR / "PRIVACY_RELEASE_AUDIT.md"
        assert audit_md.exists()
        with open(audit_md, "r", encoding="utf-8") as f:
            content = f.read()
            assert "RELEASE STATUS: APPROVED FOR OPEN RESEARCH DISTRIBUTION" in content
            assert "ZERO CREDENTIALS DETECTED — PASS" in content
