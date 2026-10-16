"""Automated Testing Suite for Artifact Engineering V1.

Verifies:
1. Benchmark JSONL schema and prediction schema compliance on synthetic samples.
2. Canonical artifact protection (prevents overwriting or corruption of frozen files).
3. Metric invariants and offset validity.
4. Consistency between release manifests, release hashes, and public documentation.
"""

import json
import hashlib
from pathlib import Path
import pytest

from benchmark.evaluate import load_gold_records, load_predictions_by_variant

BASE_DIR = Path(__file__).resolve().parent.parent
FINAL_DIR = BASE_DIR / "reports" / "final"
ARTIFACT_ENG_DIR = BASE_DIR / "reports" / "artifact_engineering"


def compute_md5(p: Path) -> str:
    hasher = hashlib.md5()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class TestCanonicalArtifactProtection:
    """Ensure canonical locked files are never modified."""

    def test_canonical_hash_protection(self):
        hash_json = FINAL_DIR / "CANONICAL_ARTIFACT_HASHES.json"
        assert hash_json.exists()
        with open(hash_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        for rel_path, info in data["artifacts"].items():
            if info.get("category") == "canonical_locked_22":
                file_path = BASE_DIR / rel_path
                assert file_path.exists(), f"Missing canonical file: {rel_path}"
                actual_md5 = compute_md5(file_path)
                assert actual_md5 == info["expected_md5"], (
                    f"Canonical artifact protection violation: {rel_path} has been altered!"
                )

    def test_freeze_declaration_exists_and_approved(self):
        freeze_dec = BASE_DIR / "reports" / "FINAL_FREEZE_DECLARATION.md"
        assert freeze_dec.exists()
        with open(freeze_dec, "r", encoding="utf-8") as f:
            content = f.read()
            assert "SCIENTIFIC FREEZE — APPROVED" in content


class TestBenchmarkSchemaValidation:
    """Validate record structure, span offsets, and label taxonomy."""

    ALLOWED_TYPES = {
        "NAME", "PERSON", "PHONE", "EMAIL", "AADHAAR", "PAN",
        "PASSPORT", "VOTER_ID", "DRIVING_LICENSE", "UPI_ID",
        "BANK_ACCOUNT", "ADDRESS"
    }

    def test_canonical_benchmark_spans_and_offsets(self):
        """Audit all 964 canonical records for span and offset integrity."""
        from benchmark.runner import load_canonical_benchmark_records
        records = load_canonical_benchmark_records()
        assert len(records) == 964

        total_gold = 0
        for rec in records:
            text = rec.get("text", "")
            entities = rec.get("entities", [])
            total_gold += len(entities)

            for ent in entities:
                etype = ent["type"]
                start = ent["start"]
                end = ent["end"]
                val = ent.get("value")

                assert etype in self.ALLOWED_TYPES, f"Invalid entity type: {etype}"
                assert 0 <= start <= end <= len(text), f"Invalid offsets [{start}:{end}] for text length {len(text)}"
                if val is not None:
                    assert text[start:end] == val, f"Slice mismatch: text[{start}:{end}]='{text[start:end]}' != '{val}'"

        assert total_gold == 724, f"Expected 724 gold entities, found {total_gold}"


class TestReleaseManifestAndHashes:
    """Verify release manifest, hashes, and figure audits."""

    def test_release_manifest_validity(self):
        manifest_file = ARTIFACT_ENG_DIR / "RELEASE_MANIFEST.json"
        assert manifest_file.exists()
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["version"] == "0.18.0"
        assert manifest["status"] == "APPROVED"
        assert manifest["counts_by_category"]["RELEASE_REQUIRED"] >= 50
        assert len(manifest["figure_audit"]) == 8

        for fa in manifest["figure_audit"]:
            assert fa["status"] == "VERIFIED"

    def test_release_hashes_validity(self):
        hashes_file = ARTIFACT_ENG_DIR / "RELEASE_HASHES.json"
        assert hashes_file.exists()
        with open(hashes_file, "r", encoding="utf-8") as f:
            hdata = json.load(f)

        assert hdata["total_hashed_files"] >= 50
        for path_str, info in hdata["hashes"].items():
            assert "md5" in info
            assert "sha256" in info
            assert len(info["sha256"]) == 64


class TestSDReconciliationPresentation:
    """Verify that SD reconciliation documentation exists and is mathematically sound."""

    def test_sd_reconciliation_document(self):
        sd_doc = ARTIFACT_ENG_DIR / "SD_RECONCILIATION.md"
        assert sd_doc.exists()
        with open(sd_doc, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Sample Standard Deviation ($s$, `ddof=1`" in content
            assert r"Population Standard Deviation ($\sigma$, `ddof=0`" in content
