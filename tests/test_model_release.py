"""Governance Test Suite for BharatPII-CRF Model Release v1.0.

Verifies:
1. Complete release files exist in models/bharatpii-crf-v1.0/
2. SHA256SUMS.txt integrity across all 9 files
3. Model safetensors tensor count (204) and parameter counts (278,057,044 / 13,396)
4. Fast inference execution and output schema adherence
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest
from safetensors.torch import load_file

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = REPO_ROOT / "models" / "bharatpii-crf-v1.0"

REQUIRED_FILES = [
    "config.json",
    "label_map.json",
    "model.safetensors",
    "MODEL_CARD.md",
    "model_metadata.json",
    "sentencepiece.bpe.model",
    "SHA256SUMS.txt",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
]


def test_model_release_directory_structure():
    assert MODEL_DIR.exists(), f"Missing model release directory: {MODEL_DIR}"
    for fname in REQUIRED_FILES:
        fpath = MODEL_DIR / fname
        assert fpath.exists(), f"Missing required release file: {fname}"
        assert fpath.stat().st_size > 0, f"File is empty: {fname}"


def test_model_release_sha256_manifest():
    manifest_file = MODEL_DIR / "SHA256SUMS.txt"
    assert manifest_file.exists()
    lines = [l.strip() for l in manifest_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 9, f"Expected 9 hashed files, found {len(lines)}"

    for line in lines:
        exp_sha, fname = line.split(maxsplit=1)
        fpath = MODEL_DIR / fname
        assert fpath.exists(), f"File in manifest missing: {fname}"
        hasher = hashlib.sha256()
        with open(fpath, "rb") as f:
            while chunk := f.read(1024 * 1024):
                hasher.update(chunk)
        act_sha = hasher.hexdigest()
        assert act_sha == exp_sha, f"SHA256 mismatch for {fname}: {act_sha} != {exp_sha}"


def test_model_release_parameter_counts():
    sf_path = MODEL_DIR / "model.safetensors"
    sd = load_file(sf_path)
    assert len(sd) == 204, f"Expected 204 tensors, found {len(sd)}"

    roberta_tensors = {k: v for k, v in sd.items() if k.startswith("roberta.")}
    head_tensors = {k: v for k, v in sd.items() if not k.startswith("roberta.")}

    assert len(roberta_tensors) == 199
    assert len(head_tensors) == 5

    n_encoder = sum(t.numel() for t in roberta_tensors.values())
    n_head = sum(t.numel() for t in head_tensors.values())
    n_total = n_encoder + n_head

    assert n_total == 278057044
    assert n_encoder == 278043648
    assert n_head == 13396


def test_model_release_inference_smoke():
    from baselines.transformer_b6 import TransformerB6CRFAdapter
    adapter = TransformerB6CRFAdapter(model_name_or_path=MODEL_DIR, seed=42)
    sample_text = "Call Priya Sharma at 9876543210 regarding PAN ABCDE1234F."
    preds = adapter.predict(sample_text)
    assert len(preds) > 0
    for p in preds:
        assert p.status == "VALID"
        assert sample_text[p.start:p.end] == p.text
