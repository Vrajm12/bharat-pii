"""Public Prediction CLI for the Indian PII Robustness Benchmark.

Usage:
    python -m benchmark.predict --system <b1|b2|b3|b4|b5|b6> --input <input.jsonl> --output <predictions.jsonl> [--seed 42]

Provides a standardized inference interface over public baseline systems:
- b1: Regex (Canonical Deterministic Rules v1.0.0)
- b2: spaCy (en_core_web_sm v3.8.16)
- b3: Microsoft Presidio (v2.2.364 with Indian recognizers)
- b4: Zero-Shot XLM-RoBERTa (Davlan/xlm-roberta-base-ner-hrl)
- b5: Indian-Adapted XLM-RoBERTa (Token Classification)
- b6: Indian-Adapted XLM-RoBERTa + Linear Chain CRF (Sequence Decoding)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from baselines.base import BaselineAdapter, validate_predictions
from benchmark.schema import Prediction


def get_adapter(system: str, seed: int = 42, device: int | str = -1) -> BaselineAdapter:
    """Instantiate the requested baseline adapter."""
    system_key = system.lower().strip()

    # Normalize device for neural baselines
    dev_norm: int | str = -1
    if isinstance(device, str):
        if device in ["-1", "cpu"]:
            dev_norm = -1
        elif device.isdigit():
            dev_norm = int(device)
        else:
            dev_norm = device
    else:
        dev_norm = device

    if system_key == "b1":
        from baselines.regex import RegexBaselineAdapter
        return RegexBaselineAdapter()

    elif system_key == "b2":
        from baselines.spacy import SpacyBaselineAdapter
        return SpacyBaselineAdapter()

    elif system_key == "b3":
        from baselines.presidio import PresidioBaselineAdapter
        return PresidioBaselineAdapter()

    elif system_key == "b4":
        from baselines.transformer import TransformerBaselineAdapter
        return TransformerBaselineAdapter(device=dev_norm)

    elif system_key == "b5":
        from baselines.transformer_adapted import TransformerAdaptedBaselineAdapter
        return TransformerAdaptedBaselineAdapter(seed=seed, device=dev_norm)

    elif system_key == "b6":
        from baselines.transformer_b6 import TransformerB6CRFAdapter
        return TransformerB6CRFAdapter(seed=seed, device=dev_norm)

    else:
        raise ValueError(f"Unknown system: '{system}'. Supported systems: b1, b2, b3, b4, b5, b6")


def load_input_records(input_path: Path) -> list[dict[str, Any]]:
    """Load text input records from JSONL or raw text."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    records = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            # Try parsing as JSONL
            if line.startswith("{") and line.endswith("}"):
                try:
                    data = json.loads(line)
                    vid = data.get("variant_id") or data.get("record_id") or data.get("id") or f"doc_{line_num}"
                    text = data.get("text") or data.get("canonical_text") or ""
                    records.append({"variant_id": str(vid), "text": text})
                    continue
                except json.JSONDecodeError:
                    pass

            # Fallback to plain text line
            records.append({"variant_id": f"doc_{line_num}", "text": line})

    return records


def run_prediction(
    system: str,
    input_path: Path,
    output_path: Path,
    seed: int = 42,
    device: int | str = -1,
) -> int:
    """Run prediction on input records and save predictions to output_path."""
    records = load_input_records(input_path)
    adapter = get_adapter(system, seed=seed, device=device)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    total_preds = 0

    with open(output_path, "w", encoding="utf-8") as out_f:
        for rec in records:
            vid = rec["variant_id"]
            text = rec["text"]
            raw_preds = adapter.predict(text)

            valid_preds, rejected_preds = validate_predictions(raw_preds, original_text=text)

            for p in raw_preds:
                pred_dict = {
                    "variant_id": vid,
                    "type": p.type,
                    "start": p.start,
                    "end": p.end,
                    "text": p.text,
                    "confidence": p.confidence,
                    "status": p.status,
                    "rejection_reason": p.rejection_reason,
                }
                out_f.write(json.dumps(pred_dict, ensure_ascii=False) + "\n")
                total_preds += 1

    return total_preds


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run PII extraction predictions using Indian PII Robustness Benchmark baseline systems."
    )
    parser.add_argument(
        "--system",
        choices=["b1", "b2", "b3", "b4", "b5", "b6"],
        required=True,
        help="Baseline system to evaluate (b1=Regex, b2=spaCy, b3=Presidio, b4=Zero-shot XLM-R, b5=Adapted XLM-R, b6=Adapted XLM-R+CRF).",
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to input JSONL file (with 'text' field) or plain text file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to write predictions JSONL file.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for adapted transformer models (default: 42).",
    )
    parser.add_argument(
        "--device",
        default="-1",
        help="Device to run neural models on ('-1' for CPU, '0' for CUDA GPU, default: -1).",
    )

    args = parser.parse_args(argv)

    try:
        total = run_prediction(
            system=args.system,
            input_path=args.input,
            output_path=args.output,
            seed=args.seed,
            device=args.device,
        )
        print(f"[SUCCESS] System {args.system.upper()} emitted {total} predictions to {args.output}")
        return 0
    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
