"""Automated test suite for BharatPII inference demo, entity offsets, and redaction.

Validates:
1. Pure redaction logic across diverse span configurations and mask formats.
2. Character slice invariant contract: text[start:end] == entity.text.
3. Model inference across all 8 canonical Indian PII categories in multiple scripts.
4. Synthetic catalog coverage and data integrity.
5. End-to-end CLI options including --smoke-test, --text, and file I/O.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import pytest

from bharatpii import BharatPII, Entity
from bharatpii.labels import CANONICAL_PII_TYPES

from examples.bharatpii_demo import (
    DEFAULT_MASK_PATTERN,
    process_single_text,
    redact_text,
    validate_entity_offsets,
)
from examples.synthetic_examples import (
    SYNTHETIC_EXAMPLES,
    get_all_categories,
    get_examples_by_category,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = REPO_ROOT / "models" / "bharatpii-crf-v1.0"
DEMO_SCRIPT = REPO_ROOT / "examples" / "bharatpii_demo.py"


@pytest.fixture(scope="module")
def model():
    """Load the BharatPII model once for the test session."""
    assert MODEL_DIR.exists(), f"Model directory not found: {MODEL_DIR}"
    return BharatPII.from_pretrained(MODEL_DIR)


# =============================================================================
# 1. Unit Tests for Redaction Logic
# =============================================================================


class TestRedactionUnit:
    """Unit tests for redact_text function without requiring model inference."""

    def test_empty_string(self):
        assert redact_text("", []) == ""
        assert redact_text("", [Entity("test", 0, 4, "PERSON")]) == ""

    def test_no_entities_preserves_text_verbatim(self):
        text = "Hello world! This has no PII: 1234, @#$%, \n\t."
        assert redact_text(text, []) == text

    def test_single_entity_replacement(self):
        text = "My name is Sneha Sharma."
        entities = [Entity(text="Sneha Sharma", start=11, end=23, label="PERSON")]
        assert redact_text(text, entities) == "My name is [PERSON]."

    def test_multiple_non_overlapping_entities(self):
        text = "Call Rahul Sharma at 9876543210 regarding PAN ABCDE1234F."
        entities = [
            Entity(text="Rahul Sharma", start=5, end=17, label="PERSON"),
            Entity(text="9876543210", start=21, end=31, label="PHONE"),
            Entity(text="ABCDE1234F", start=46, end=56, label="PAN"),
        ]
        redacted = redact_text(text, entities)
        assert redacted == "Call [PERSON] at [PHONE] regarding PAN [PAN]."

    def test_unsorted_entities_handled_properly(self):
        text = "Call Rahul Sharma at 9876543210 regarding PAN ABCDE1234F."
        entities = [
            Entity(text="ABCDE1234F", start=46, end=56, label="PAN"),
            Entity(text="Rahul Sharma", start=5, end=17, label="PERSON"),
            Entity(text="9876543210", start=21, end=31, label="PHONE"),
        ]
        redacted = redact_text(text, entities)
        assert redacted == "Call [PERSON] at [PHONE] regarding PAN [PAN]."

    def test_custom_mask_patterns(self):
        text = "Contact priya@upi today."
        entities = [Entity(text="priya@upi", start=8, end=17, label="UPI_ID")]

        assert redact_text(text, entities, mask_pattern="<{label}>") == "Contact <UPI_ID> today."
        assert redact_text(text, entities, mask_pattern="***{label}***") == "Contact ***UPI_ID*** today."
        assert redact_text(text, entities, mask_pattern="[REDACTED]") == "Contact [REDACTED] today."

    def test_overlapping_spans_handled_safely(self):
        text = "Account reference 1234567890."
        entities = [
            Entity(text="1234567890", start=18, end=28, label="BANK_ACCOUNT"),
            Entity(text="12345", start=18, end=23, label="PHONE"),  # Overlapping
        ]
        redacted = redact_text(text, entities)
        assert redacted == "Account reference [BANK_ACCOUNT]."

    def test_unicode_and_indic_scripts_preservation(self):
        text = "मेरा नाम राहुल शर्मा है और मेरा ईमेल rahul@example.com है।"
        entities = [
            Entity(text="राहुल शर्मा", start=9, end=20, label="PERSON"),
            Entity(text="rahul@example.com", start=37, end=54, label="EMAIL"),
        ]
        redacted = redact_text(text, entities)
        assert redacted == "मेरा नाम [PERSON] है और मेरा ईमेल [EMAIL] है।"


# =============================================================================
# 2. Synthetic Catalog Structure & Coverage Tests
# =============================================================================


class TestSyntheticCatalog:
    """Verifies coverage and schema of the synthetic examples catalog."""

    def test_catalog_has_all_eight_pii_types(self):
        categories = get_all_categories()
        for pii_type in CANONICAL_PII_TYPES:
            assert pii_type in categories, f"Missing category in catalog: {pii_type}"

    def test_multilingual_coverage(self):
        languages = {e["language"] for e in SYNTHETIC_EXAMPLES}
        expected_langs = {"EN", "HI_DEVA_PII", "HINGLISH", "ROM_HI", "INFORMAL_HINGLISH"}
        for lang in expected_langs:
            assert lang in languages, f"Missing language variant: {lang}"

    def test_catalog_records_valid(self):
        for e in SYNTHETIC_EXAMPLES:
            assert "id" in e and len(e["id"]) > 0
            assert "category" in e
            assert "language" in e
            assert "text" in e and len(e["text"]) > 0
            assert "expected_labels" in e


# =============================================================================
# 3. Model Inference & Character Slice Invariant Tests
# =============================================================================


class TestModelInferenceAndOffsets:
    """Tests running the real BharatPII model against test inputs."""

    def test_slice_invariant_contract(self, model):
        """text[start:end] == entity.text MUST strictly hold for every prediction."""
        for ex in SYNTHETIC_EXAMPLES:
            text = ex["text"]
            res = model.predict(text)
            valid, errors = validate_entity_offsets(text, res.entities)
            assert valid, f"Offset invariant failed on {ex['id']}: {errors}"

            for ent in res.entities:
                assert text[ent.start:ent.end] == ent.text
                assert 0 <= ent.start < ent.end <= len(text)
                assert ent.label in CANONICAL_PII_TYPES
                if ent.score is not None:
                    assert 0.0 <= ent.score <= 1.0

    def test_detection_across_all_pii_categories(self, model):
        """Verify each of the 8 canonical PII types is detected in synthetic cases."""
        detected_types = set()
        for ex in SYNTHETIC_EXAMPLES:
            res = model.predict(ex["text"])
            for ent in res.entities:
                detected_types.add(ent.label)

        for pii_type in CANONICAL_PII_TYPES:
            assert pii_type in detected_types, f"Category {pii_type} was never detected in catalog"

    def test_end_to_end_redaction(self, model):
        """Verify process_single_text produces valid redaction preserving non-PII text."""
        test_text = "Call Rahul Sharma at 9876543210 regarding PAN ABCDE1234F."
        info = process_single_text(model, test_text)
        assert info["offsets_valid"] is True
        assert len(info["offset_errors"]) == 0
        assert info["redacted_text"] == "Call [PERSON] at [PHONE] regarding PAN [PAN]."

        # Devanagari redaction
        deva_text = "मेरा नाम राहुल शर्मा है और मेरा ईमेल sneha8298@webmail.test है।"
        deva_info = process_single_text(model, deva_text)
        assert deva_info["offsets_valid"] is True
        assert "[PERSON]" in deva_info["redacted_text"]
        assert "[EMAIL]" in deva_info["redacted_text"]
        assert "मेरा नाम" in deva_info["redacted_text"]
        assert "है।" in deva_info["redacted_text"]


# =============================================================================
# 4. CLI Smoke Tests via Subprocess
# =============================================================================


class TestDemoCLI:
    """Validates CLI invocation, exits codes, and output modes."""

    def test_cli_help(self):
        cmd = [sys.executable, "-X", "utf8", str(DEMO_SCRIPT), "--help"]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        assert res.returncode == 0
        assert "BharatPII-CRF" in res.stdout
        assert "--smoke-test" in res.stdout
        assert "--mask-pattern" in res.stdout

    def test_cli_smoke_test_flag(self):
        cmd = [sys.executable, "-X", "utf8", str(DEMO_SCRIPT), "--smoke-test", "--quiet"]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=60)
        assert res.returncode == 0, f"Smoke test failed: {res.stderr}\n{res.stdout}"
        assert "ALL SMOKE TESTS PASSED" in res.stdout

    def test_cli_single_text(self):
        cmd = [
            sys.executable,
            "-X",
            "utf8",
            str(DEMO_SCRIPT),
            "--text",
            "My PAN number is FZZFN0256Z.",
            "--quiet",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=60)
        assert res.returncode == 0
        assert "Redacted: My PAN number is [PAN]." in res.stdout

    def test_cli_file_io(self, tmp_path):
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        json_output = tmp_path / "output.json"

        input_file.write_text("My phone number is 9876543210.", encoding="utf-8")

        cmd = [
            sys.executable,
            "-X",
            "utf8",
            str(DEMO_SCRIPT),
            "--input",
            str(input_file),
            "--output",
            str(output_file),
            "--json-output",
            str(json_output),
            "--quiet",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=60)
        assert res.returncode == 0
        assert output_file.exists()
        assert output_file.read_text(encoding="utf-8") == "My phone number is [PHONE]."
        assert json_output.exists()
        data = json.loads(json_output.read_text(encoding="utf-8"))
        assert data["offsets_valid"] is True
        assert len(data["entities"]) == 1
        assert data["entities"][0]["label"] == "PHONE"


# =============================================================================
# 5. Web Demonstration Server Tests
# =============================================================================


class TestWebDemoServer:
    """Validates local web demo server, endpoints, and offline privacy guarantee."""

    def test_web_server_endpoints(self, model):
        import http.server
        import threading
        import urllib.request
        from examples.web_demo import BharatPIIWebHandler

        BharatPIIWebHandler.model = model
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), BharatPIIWebHandler)
        host, port = server.server_address

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            # 1. GET / serves UI with privacy notice and components
            with urllib.request.urlopen(f"http://{host}:{port}/") as resp:
                assert resp.status == 200
                html_body = resp.read().decode("utf-8")
                assert "BharatPII" in html_body
                assert "Privacy & Research Prototype Notice" in html_body
                assert "Detect & Redact PII" in html_body
                assert "Verified 100% Offline" in html_body

            # 2. GET /api/health
            with urllib.request.urlopen(f"http://{host}:{port}/api/health") as resp:
                assert resp.status == 200
                data = json.loads(resp.read().decode("utf-8"))
                assert data["status"] == "healthy"
                assert data["offline_mode"] is True

            # 3. GET /api/examples
            with urllib.request.urlopen(f"http://{host}:{port}/api/examples") as resp:
                assert resp.status == 200
                examples_list = json.loads(resp.read().decode("utf-8"))
                assert len(examples_list) >= 8

            # 4. POST /api/predict
            req_payload = json.dumps({
                "text": "Call Rahul Sharma at 9876543210 regarding PAN ABCDE1234F."
            }).encode("utf-8")
            req = urllib.request.Request(
                f"http://{host}:{port}/api/predict",
                data=req_payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req) as resp:
                assert resp.status == 200
                pred_data = json.loads(resp.read().decode("utf-8"))
                assert pred_data["offsets_valid"] is True
                assert pred_data["offline_mode"] is True
                assert pred_data["redacted_text"] == "Call [PERSON] at [PHONE] regarding PAN [PAN]."
                assert len(pred_data["entities"]) == 3
        finally:
            server.shutdown()
            server.server_close()
