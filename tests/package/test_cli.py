"""Command-line interface tests."""

import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = REPO_ROOT / "models" / "bharatpii-crf-v1.0"


def test_cli_info():
    cmd = [sys.executable, "-m", "bharatpii.cli", "--model", str(MODEL_DIR), "--info"]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    assert proc.returncode == 0
    info = json.loads(proc.stdout)
    assert info["model_name"] == "BharatPII-CRF"
    assert info["total_parameters"] == 278057044


def test_cli_text_prediction():
    text = "Call Rahul at 9876543210."
    cmd = [sys.executable, "-m", "bharatpii.cli", "--model", str(MODEL_DIR), "--text", text]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    assert proc.returncode == 0
    res = json.loads(proc.stdout)
    assert res["text"] == text
    assert len(res["entities"]) >= 1


def test_cli_file_input_output(tmp_path):
    in_file = tmp_path / "input.txt"
    out_file = tmp_path / "output.json"
    in_file.write_text("My PAN is ABCDE1234F.", encoding="utf-8")

    cmd = [
        sys.executable,
        "-m",
        "bharatpii.cli",
        "--model",
        str(MODEL_DIR),
        "--input",
        str(in_file),
        "--output",
        str(out_file),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    assert proc.returncode == 0
    assert out_file.exists()
    res = json.loads(out_file.read_text(encoding="utf-8"))
    assert res["text"] == "My PAN is ABCDE1234F."
    assert len(res["entities"]) == 1
    assert res["entities"][0]["label"] == "PAN"
