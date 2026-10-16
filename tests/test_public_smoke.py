"""Minimal Fast End-to-End Smoke Test for Public Benchmark CLI and Interfaces.

Validates:
synthetic input -> prediction CLI -> prediction JSONL -> evaluation CLI -> metrics output.
Runs in < 3 seconds without touching canonical benchmark files.
"""

import json
import tempfile
from pathlib import Path
import pytest

from benchmark.evaluate import run_evaluation
from benchmark.predict import run_prediction


class TestPublicBenchmarkSmoke:
    """Smoke test for public CLI prediction and evaluation pipelines."""

    @pytest.fixture
    def smoke_env(self, tmp_path):
        """Set up minimal synthetic gold records and input file."""
        gold_records = [
            {
                "variant_id": "smoke_doc_01",
                "text": "Contact Amit at amit.kumar@example.com for questions.",
                "language": "EN",
                "entities": [
                    {
                        "type": "EMAIL",
                        "start": 16,
                        "end": 38,
                        "value": "amit.kumar@example.com",
                    }
                ],
            },
            {
                "variant_id": "smoke_doc_02",
                "text": "The reference code 9812 3412 8901 is not a mobile number.",
                "language": "EN",
                "entities": [],
            },
        ]

        gold_file = tmp_path / "smoke_gold.jsonl"
        with open(gold_file, "w", encoding="utf-8") as f:
            for r in gold_records:
                f.write(json.dumps(r) + "\n")

        input_file = tmp_path / "smoke_input.jsonl"
        with open(input_file, "w", encoding="utf-8") as f:
            for r in gold_records:
                f.write(json.dumps({"variant_id": r["variant_id"], "text": r["text"]}) + "\n")

        return {
            "tmp_path": tmp_path,
            "gold_file": gold_file,
            "input_file": input_file,
        }

    def test_end_to_end_smoke_pipeline(self, smoke_env):
        """Verify complete pipeline: synthetic input -> B1 predict -> evaluate -> metrics JSON."""
        tmp_path = smoke_env["tmp_path"]
        input_file = smoke_env["input_file"]
        gold_file = smoke_env["gold_file"]

        pred_file = tmp_path / "smoke_predictions.jsonl"
        eval_output = tmp_path / "smoke_metrics.json"

        # 1. Run prediction via CLI wrapper
        pred_count = run_prediction(
            system="b1",
            input_path=input_file,
            output_path=pred_file,
        )
        assert pred_file.exists(), "Prediction output file must be created"
        assert pred_count >= 1, "At least 1 prediction expected for email"

        # Validate prediction JSONL structure
        with open(pred_file, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
        assert len(lines) == pred_count
        for p in lines:
            assert "variant_id" in p
            assert "type" in p
            assert "start" in p
            assert "end" in p
            assert p["start"] <= p["end"]

        # 2. Run evaluation via CLI wrapper
        results = run_evaluation(
            gold_path=gold_file,
            pred_path=pred_file,
            output_path=eval_output,
        )

        assert eval_output.exists(), "Evaluation JSON must be created"
        metrics = results["metrics_overall"]

        # Check expected metric keys
        for k in ["m1_precision", "m2_recall", "m3_f1", "m4_exact_f1", "tp_exact", "f1_missed", "f4_false_pos"]:
            assert k in metrics, f"Missing metric {k}"

        # Gold entity accounting invariant
        total_gold = metrics["tp_exact"] + metrics["f1_missed"] + metrics["f2_wrong_span"] + metrics["f3_wrong_type"]
        assert total_gold == 1, f"Expected 1 gold entity in smoke test, got {total_gold}"
