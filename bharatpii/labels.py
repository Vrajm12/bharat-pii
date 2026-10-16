"""Label taxonomy and IOB2 mapping for BharatPII."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CANONICAL_IOB2_LABELS: list[str] = [
    "O",
    "B-PERSON",
    "I-PERSON",
    "B-PAN",
    "I-PAN",
    "B-AADHAAR",
    "I-AADHAAR",
    "B-PHONE",
    "I-PHONE",
    "B-EMAIL",
    "I-EMAIL",
    "B-UPI_ID",
    "I-UPI_ID",
    "B-BANK_ACCOUNT",
    "I-BANK_ACCOUNT",
    "B-ADDRESS",
    "I-ADDRESS",
]

CANONICAL_PII_TYPES: list[str] = [
    "PERSON",
    "PAN",
    "AADHAAR",
    "PHONE",
    "EMAIL",
    "UPI_ID",
    "BANK_ACCOUNT",
    "ADDRESS",
]

DEFAULT_LABEL2ID: dict[str, int] = {lbl: i for i, lbl in enumerate(CANONICAL_IOB2_LABELS)}
DEFAULT_ID2LABEL: dict[int, str] = {i: lbl for i, lbl in enumerate(CANONICAL_IOB2_LABELS)}


def load_label_map(model_dir: str | Path) -> tuple[dict[int, str], dict[str, int]]:
    """Load label map from label_map.json in the model directory."""
    label_map_path = Path(model_dir) / "label_map.json"
    if not label_map_path.exists():
        raise FileNotFoundError(f"Required label map not found: {label_map_path}")

    with open(label_map_path, "r", encoding="utf-8") as f:
        raw_map: dict[str, str] = json.load(f)

    id2label = {int(k): v for k, v in raw_map.items()}
    label2id = {v: k for k, v in id2label.items()}
    return id2label, label2id
