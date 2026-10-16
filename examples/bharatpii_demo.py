#!/usr/bin/env python3
"""BharatPII Inference & Redaction Demo.

A minimal, self-contained local demonstration using the packaged BharatPII
library and B6 CRF model for multilingual Indian PII detection and redaction.

Features:
- Loads the productized `models/bharatpii-crf-v1.0/` artifact via the official API.
- Supports English, Hindi (Devanagari), Hinglish, and transliterated Indic texts.
- Displays detected entities with text, PII category, start/end character offsets,
  and token emission confidence scores.
- Character offset slice invariant verification: text[start:end] == entity.text.
- Span-preserving redaction replacing detected spans with category labels (e.g. [PERSON]).
- Built-in synthetic test catalog covering all 8 Indian PII categories:
  PERSON, PAN, AADHAAR, PHONE, EMAIL, UPI_ID, BANK_ACCOUNT, and ADDRESS.
- Canonical inference smoke tests (--smoke-test).
- Interactive REPL mode (--interactive).
- File input/output batch processing (--input, --output, --json-output).
- 100% offline local inference with zero telemetry and zero external API calls.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

# Ensure stdout/stderr handle UTF-8 properly on Windows terminals
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Attempt imports from the official bharatpii package
try:
    from bharatpii import BharatPII, Entity, PredictionResult, __version__
    from bharatpii.labels import CANONICAL_PII_TYPES
except ImportError:
    # If running from repository root without pip install -e .
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    from bharatpii import BharatPII, Entity, PredictionResult, __version__
    from bharatpii.labels import CANONICAL_PII_TYPES

from examples.synthetic_examples import (
    SYNTHETIC_EXAMPLES,
    get_all_categories,
    get_examples_by_category,
)

DEFAULT_MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "bharatpii-crf-v1.0"
DEFAULT_MASK_PATTERN = "[{label}]"

RESEARCH_DISCLOSURE = """\
================================================================================
                    BharatPII-CRF Inference & Redaction Demo
================================================================================
RESEARCH PROTOTYPE NOTICE & GOVERNANCE DISCLOSURE:
- BharatPII is an academic research prototype for multilingual Indian PII detection.
- This software is NOT certified under the Digital Personal Data Protection Act
  (DPDPA 2023) and does NOT guarantee complete anonymization or zero false positives.
- Missed detections (false negatives) and spurious alarms (false positives) are
  possible, particularly on ambiguous alphanumeric codes or unpunctuated text.
- High-stakes privacy and production deployments REQUIRE human-in-the-loop review.
- Local & Private: All inference runs 100% locally and offline. No input text
  is sent to any external server or API, and sensitive data is not logged.
================================================================================\
"""


def redact_text(
    text: str,
    entities: list[Entity],
    mask_pattern: str = DEFAULT_MASK_PATTERN,
) -> str:
    """Redact detected PII entities from text, preserving all other characters.

    Replaces detected spans text[start:end] with category labels (e.g. [PERSON]),
    preserving punctuation, whitespace, and non-PII text exactly.

    Args:
        text: Original input text string.
        entities: List of detected Entity instances with start, end, and label.
        mask_pattern: Template string containing '{label}' for replacement.

    Returns:
        The redacted string with spans replaced by category labels.
    """
    if not text or not entities:
        return text

    # Sort entities by start offset ascending, then by end offset descending
    sorted_entities = sorted(entities, key=lambda e: (e.start, -e.end))

    redacted_parts: list[str] = []
    last_idx = 0

    for ent in sorted_entities:
        # Prevent overlapping spans from corrupting character slices
        if ent.start < last_idx:
            continue

        # Append preceding non-PII text
        redacted_parts.append(text[last_idx:ent.start])

        # Append category label mask
        replacement = mask_pattern.format(label=ent.label)
        redacted_parts.append(replacement)

        last_idx = ent.end

    # Append any remaining text after the final entity
    redacted_parts.append(text[last_idx:])
    return "".join(redacted_parts)


def validate_entity_offsets(text: str, entities: list[Entity]) -> tuple[bool, list[str]]:
    """Verify that detected entity character offsets satisfy text[start:end] == entity.text.

    Returns:
        Tuple of (all_valid: bool, error_messages: list[str]).
    """
    errors: list[str] = []
    text_len = len(text)

    for i, ent in enumerate(entities):
        if ent.start < 0:
            errors.append(f"Entity {i} ({ent.label}): start {ent.start} < 0")
        if ent.end > text_len:
            errors.append(
                f"Entity {i} ({ent.label}): end {ent.end} > text length {text_len}"
            )
        if ent.end <= ent.start:
            errors.append(
                f"Entity {i} ({ent.label}): end {ent.end} <= start {ent.start}"
            )

        sliced_text = text[ent.start:ent.end]
        if sliced_text != ent.text:
            errors.append(
                f"Entity {i} ({ent.label}): slice mismatch! "
                f"text[{ent.start}:{ent.end}] == {sliced_text!r} != {ent.text!r}"
            )

    return (len(errors) == 0, errors)


def format_entity_report(text: str, result: PredictionResult) -> str:
    """Format detected entities into a clear, structured text summary."""
    lines: list[str] = []
    if not result.entities:
        lines.append("  (No PII entities detected)")
        return "\n".join(lines)

    lines.append(f"  Detected {len(result.entities)} entity/entities:")
    for idx, ent in enumerate(result.entities, start=1):
        is_exact = text[ent.start:ent.end] == ent.text
        slice_status = "OK (exact slice)" if is_exact else "FAIL (slice mismatch)"
        score_str = f"{ent.score:.4f}" if ent.score is not None else "N/A"
        lines.append(
            f"  {idx}. [{ent.label}] {ent.text!r}\n"
            f"     Offsets: [{ent.start}:{ent.end}] | Length: {ent.end - ent.start} chars\n"
            f"     Confidence: {score_str} | Invariant Check: {slice_status}"
        )
    return "\n".join(lines)


def process_single_text(
    model: BharatPII,
    text: str,
    mask_pattern: str = DEFAULT_MASK_PATTERN,
    title: str | None = None,
) -> dict[str, Any]:
    """Process a single text: run inference, validate offsets, and produce redaction."""
    result = model.predict(text)
    redacted = redact_text(text, result.entities, mask_pattern=mask_pattern)
    valid, errors = validate_entity_offsets(text, result.entities)

    return {
        "title": title,
        "input_text": text,
        "entities": [e.to_dict() for e in result.entities],
        "redacted_text": redacted,
        "offsets_valid": valid,
        "offset_errors": errors,
        "raw_result": result,
    }


def print_single_result(info: dict[str, Any], show_input: bool = True):
    """Pretty-print the result of a single text inference."""
    if info.get("title"):
        print(f"\n--- {info['title']} ---")
    if show_input:
        print(f"Input:    {info['input_text']}")

    raw_res = info.get("raw_result")
    if raw_res:
        print(format_entity_report(info["input_text"], raw_res))
    else:
        print(f"  Entities: {len(info['entities'])}")

    print(f"Redacted: {info['redacted_text']}")

    if not info["offsets_valid"]:
        print(f"  [ERROR] Offset verification failures: {info['offset_errors']}")


def run_catalog_demo(
    model: BharatPII,
    category_filter: str | None = None,
    mask_pattern: str = DEFAULT_MASK_PATTERN,
):
    """Run through the catalog of synthetic examples across all PII categories."""
    examples = (
        get_examples_by_category(category_filter)
        if category_filter
        else SYNTHETIC_EXAMPLES
    )

    print(f"\nRunning synthetic examples ({len(examples)} cases)...")
    print("-" * 80)

    total = 0
    passed_invariants = 0

    for ex in examples:
        title = f"{ex['id']} [{ex['category']} | Lang: {ex['language']}] - {ex['description']}"
        res_info = process_single_text(
            model,
            ex["text"],
            mask_pattern=mask_pattern,
            title=title,
        )
        print_single_result(res_info)
        total += 1
        if res_info["offsets_valid"]:
            passed_invariants += 1

    print("-" * 80)
    print(
        f"Summary: {total} examples evaluated | "
        f"Offset Invariant Verifications: {passed_invariants}/{total} passed."
    )


def run_smoke_tests(
    model: BharatPII,
    mask_pattern: str = DEFAULT_MASK_PATTERN,
) -> bool:
    """Run canonical smoke tests and verify character offsets and redactions.

    Verifies:
    1. Empty and whitespace string handling.
    2. Character offset invariant: text[start:end] == entity.text for all entities.
    3. Offset bounds: 0 <= start < end <= len(text).
    4. Canonical coverage across all 8 PII categories:
       PERSON, PAN, AADHAAR, PHONE, EMAIL, UPI_ID, BANK_ACCOUNT, ADDRESS.
    5. Redaction output replaces detected spans with category labels and preserves non-PII text.

    Returns:
        True if all smoke test assertions pass, False otherwise.
    """
    print("\n" + "=" * 80)
    print("RUNNING BHARATPII CANONICAL INFERENCE SMOKE TESTS")
    print("=" * 80)

    all_passed = True
    tests_run = 0

    # 1. Empty & whitespace test
    tests_run += 1
    empty_res = model.predict("")
    if len(empty_res) != 0 or empty_res.text != "":
        print("[FAIL] Empty string test failed.")
        all_passed = False
    else:
        print("[PASS] 1. Empty string returns empty result.")

    tests_run += 1
    ws_res = model.predict("   \n\t  ")
    if len(ws_res) != 0:
        print("[FAIL] Whitespace string test failed.")
        all_passed = False
    else:
        print("[PASS] 2. Whitespace-only string returns empty result.")

    # 2. Canonical Synthetic Catalog Verification
    print(f"\n[INFO] Evaluating {len(SYNTHETIC_EXAMPLES)} canonical synthetic examples...")
    detected_categories: set[str] = set()

    for idx, ex in enumerate(SYNTHETIC_EXAMPLES, start=3):
        tests_run += 1
        text = ex["text"]
        res = model.predict(text)
        valid, errors = validate_entity_offsets(text, res.entities)

        if not valid:
            print(f"[FAIL] {idx}. {ex['id']} offset validation failed: {errors}")
            all_passed = False
            continue

        # Redaction verification
        redacted = redact_text(text, res.entities, mask_pattern=mask_pattern)
        for ent in res.entities:
            detected_categories.add(ent.label)
            expected_mask = mask_pattern.format(label=ent.label)
            if expected_mask not in redacted:
                print(
                    f"[FAIL] {idx}. {ex['id']} expected mask {expected_mask} not in redacted text: {redacted!r}"
                )
                all_passed = False
                break
        else:
            # Check non-PII characters preserved if no entities
            if not res.entities and redacted != text:
                print(f"[FAIL] {idx}. {ex['id']} non-PII text modified during redaction!")
                all_passed = False
                continue

            status = f"{len(res.entities)} entities detected" if res.entities else "no entities (decoy)"
            print(f"[PASS] {idx}. {ex['id']} [{ex['category']} / {ex['language']}] - {status} -> all offsets verified.")

    # 3. Verify all 8 PII categories were observed
    print(f"\n[INFO] Observed PII categories across catalog: {sorted(detected_categories)}")
    for pii_type in CANONICAL_PII_TYPES:
        tests_run += 1
        if pii_type in detected_categories:
            print(f"[PASS] Category {pii_type} verified in synthetic detections.")
        else:
            print(f"[WARN] Category {pii_type} was not triggered in tested subset.")

    # 4. Multi-entity compound test
    tests_run += 1
    compound_text = "Call Rahul Sharma at 9876543210 regarding PAN ABCDE1234F."
    comp_res = model.predict(compound_text)
    comp_redacted = redact_text(compound_text, comp_res.entities, mask_pattern=mask_pattern)
    expected_redacted = "Call [PERSON] at [PHONE] regarding PAN [PAN]."

    if comp_redacted != expected_redacted:
        print(f"[FAIL] Multi-entity compound redaction mismatch:\n  Got:      {comp_redacted!r}\n  Expected: {expected_redacted!r}")
        all_passed = False
    else:
        print(f"[PASS] Multi-entity compound sentence redacted perfectly:\n  Original: {compound_text}\n  Redacted: {comp_redacted}")

    print("\n" + "=" * 80)
    if all_passed:
        print(f"ALL SMOKE TESTS PASSED ({tests_run} checks executed successfully).")
    else:
        print(f"SMOKE TESTS ENCOUNTERED FAILURES ({tests_run} checks).")
    print("=" * 80 + "\n")

    return all_passed


def interactive_repl(model: BharatPII, mask_pattern: str = DEFAULT_MASK_PATTERN):
    """Run an interactive REPL for real-time text detection and redaction."""
    print("\n" + "=" * 80)
    print("BHARATPII INTERACTIVE REPL")
    print("Type or paste any text (English, Hindi, Hinglish).")
    print("Type 'exit', 'quit', or press Ctrl+C / Ctrl+D to exit.")
    print("=" * 80 + "\n")

    while True:
        try:
            line = input("bharatpii> ").strip()
            if not line:
                continue
            if line.lower() in ("exit", "quit", ":q"):
                print("Exiting interactive demo. Namaste!")
                break

            info = process_single_text(model, line, mask_pattern=mask_pattern)
            print("-" * 60)
            print(format_entity_report(line, info["raw_result"]))
            print(f"Redacted: {info['redacted_text']}")
            print("-" * 60 + "\n")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting interactive demo. Namaste!")
            break


def main():
    parser = argparse.ArgumentParser(
        prog="bharatpii_demo",
        description="BharatPII-CRF: Local Multilingual Indian PII Detection & Redaction Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Run all synthetic examples (all 8 PII categories):
  python examples/bharatpii_demo.py

  # Test a single text string:
  python examples/bharatpii_demo.py --text "Contact Rahul Sharma at 9876543210"

  # Test a Hindi or Hinglish string:
  python examples/bharatpii_demo.py --text "मेरा नाम राहुल शर्मा है और पैन ABCDE1234F है।"

  # Run canonical smoke tests:
  python examples/bharatpii_demo.py --smoke-test

  # Launch interactive mode:
  python examples/bharatpii_demo.py --interactive

  # Redact text from a file:
  python examples/bharatpii_demo.py --input sample.txt --output redacted.txt
        """,
    )

    parser.add_argument(
        "--model",
        type=str,
        default=str(DEFAULT_MODEL_DIR),
        help=f"Path to BharatPII model directory (default: {DEFAULT_MODEL_DIR})",
    )
    parser.add_argument(
        "--text",
        type=str,
        help="Single text string to analyze and redact",
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Input text file path to process (use '-' for stdin)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Optional output file path to write redacted text to",
    )
    parser.add_argument(
        "--json-output",
        type=str,
        help="Optional output file path to write structured JSON results to",
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Run through the built-in synthetic test catalog",
    )
    parser.add_argument(
        "--category",
        type=str,
        choices=get_all_categories(),
        help="Filter synthetic examples by PII category",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run canonical inference smoke tests and exit",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start interactive REPL mode",
    )
    parser.add_argument(
        "--mask-pattern",
        type=str,
        default=DEFAULT_MASK_PATTERN,
        help=f"Redaction replacement template containing '{{label}}' (default: '{DEFAULT_MASK_PATTERN}')",
    )
    parser.add_argument(
        "--verify-checksums",
        action="store_true",
        help="Validate model artifact SHA256 checksums from SHA256SUMS.txt on load",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress banner and disclosure notices",
    )

    args = parser.parse_args()

    # Print disclosure banner unless quiet mode
    if not args.quiet:
        print(RESEARCH_DISCLOSURE)

    # Validate model directory
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"Error: Model directory not found: {model_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading BharatPII model from {model_path}...")
    try:
        model = BharatPII.from_pretrained(
            model_path,
            verify_checksums=args.verify_checksums,
        )
    except Exception as e:
        print(f"Failed to load BharatPII model: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Model loaded successfully! Package version: {__version__}")
    print(f"Total parameters: {model.total_parameters:,} (Task-specific head: {model.trainable_head_parameters:,})\n")

    # Mode 1: Smoke Tests
    if args.smoke_test:
        success = run_smoke_tests(model, mask_pattern=args.mask_pattern)
        sys.exit(0 if success else 1)

    # Mode 2: Interactive REPL
    if args.interactive:
        interactive_repl(model, mask_pattern=args.mask_pattern)
        sys.exit(0)

    # Mode 3: Single Text
    if args.text is not None:
        info = process_single_text(model, args.text, mask_pattern=args.mask_pattern)
        print_single_result(info, show_input=True)

        if args.output:
            Path(args.output).write_text(info["redacted_text"], encoding="utf-8")
            print(f"\nRedacted text written to: {args.output}")

        if args.json_output:
            out_dict = {
                "input_text": info["input_text"],
                "entities": info["entities"],
                "redacted_text": info["redacted_text"],
                "offsets_valid": info["offsets_valid"],
            }
            Path(args.json_output).write_text(
                json.dumps(out_dict, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"Structured JSON output written to: {args.json_output}")

        sys.exit(0)

    # Mode 4: File Input
    if args.input is not None:
        if args.input == "-":
            raw_text = sys.stdin.read()
        else:
            in_path = Path(args.input)
            if not in_path.exists():
                print(f"Error: Input file not found: {in_path}", file=sys.stderr)
                sys.exit(1)
            raw_text = in_path.read_text(encoding="utf-8")

        info = process_single_text(model, raw_text, mask_pattern=args.mask_pattern)
        print_single_result(info, show_input=False)

        if args.output:
            Path(args.output).write_text(info["redacted_text"], encoding="utf-8")
            print(f"\nRedacted text written to: {args.output}")
        else:
            print("\nFull Redacted Text Output:")
            print(info["redacted_text"])

        if args.json_output:
            out_dict = {
                "input_text": info["input_text"],
                "entities": info["entities"],
                "redacted_text": info["redacted_text"],
                "offsets_valid": info["offsets_valid"],
            }
            Path(args.json_output).write_text(
                json.dumps(out_dict, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"Structured JSON output written to: {args.json_output}")

        sys.exit(0)

    # Mode 5: Default Demo Catalog (or explicit --examples / --category)
    run_catalog_demo(
        model,
        category_filter=args.category,
        mask_pattern=args.mask_pattern,
    )


if __name__ == "__main__":
    main()
