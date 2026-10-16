"""Command-line interface for BharatPII."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .pipeline import BharatPII
from .version import __version__


def main():
    parser = argparse.ArgumentParser(
        prog="bharatpii",
        description="BharatPII-CRF: Multilingual Indian Personally Identifiable Information (PII) Detection",
    )
    parser.add_argument("--model", type=str, required=False, default="models/bharatpii-crf-v1.0", help="Path to BharatPII model release directory")
    parser.add_argument("--text", type=str, help="Text to detect PII from")
    parser.add_argument("--input", type=str, help="Input text file path")
    parser.add_argument("--output", type=str, help="Optional output JSON file path")
    parser.add_argument("--info", action="store_true", help="Display model metadata and exit")
    parser.add_argument("--version", action="version", version=f"bharatpii {__version__}")

    args = parser.parse_args()

    if args.info:
        try:
            model = BharatPII.from_pretrained(args.model)
            print(json.dumps(model.info(), indent=2, ensure_ascii=False))
            sys.exit(0)
        except Exception as e:
            print(f"Error loading model from '{args.model}': {e}", file=sys.stderr)
            sys.exit(1)

    if args.text is None and args.input is None:
        parser.error("Either --text, --input, or --info must be specified.")

    try:
        model = BharatPII.from_pretrained(args.model)
    except Exception as e:
        print(f"Error loading model from '{args.model}': {e}", file=sys.stderr)
        sys.exit(1)

    if args.text is not None:
        result = model.predict(args.text)
        out_json = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        if args.output:
            Path(args.output).write_text(out_json, encoding="utf-8")
        else:
            print(out_json)
        sys.exit(0)

    if args.input is not None:
        in_path = Path(args.input)
        if not in_path.exists():
            print(f"Input file not found: {in_path}", file=sys.stderr)
            sys.exit(1)
        raw_text = in_path.read_text(encoding="utf-8")
        result = model.predict(raw_text)
        out_json = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        if args.output:
            Path(args.output).write_text(out_json, encoding="utf-8")
        else:
            print(out_json)
        sys.exit(0)


if __name__ == "__main__":
    main()
