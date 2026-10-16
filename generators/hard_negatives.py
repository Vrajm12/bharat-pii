"""T11 Phase 1: assemble the 20 pilot HARD_NEGATIVE base instances.

Scope (frozen architecture, guidelines.md §13.8/§13.9/§13.12; quota
confirmed by explicit user decision after a Phase-1 clarification turn):
exactly 20 base instances, base_kind == HARD_NEGATIVE for all, additional
to (never merged into, never modifying) the existing 100 POSITIVE bases.
No derived-record generation -- that is a separate, later phase.

This module implements only the four decoy classes guidelines.md §13.8
actually froze a construction rule for -- NUMERIC_SHAPE, ALNUM_SHAPE,
NAME_AS_PLACE, HANDLE_SHAPE, PARTIAL_PII (five; ORG_AS_PERSON is explicitly
deferred, quota 0, and has no construction function here at all -- not a
stub, not a placeholder, simply absent, so it cannot be silently invented by
a future edit).

Each construction function reuses an existing frozen generator or
vocabulary verbatim (guidelines.md §13.8's own "reused, not new" framing):

    NUMERIC_SHAPE  -> generators.pii.phone / aadhaar / bank_account
    ALNUM_SHAPE    -> generators.pii.pan
    NAME_AS_PLACE  -> generators.pii.person's _GIVEN_NAMES + the literal
                      " Nagar" suffix (guidelines.md §6 / §13.3)
    HANDLE_SHAPE   -> generators.pii.email's _LOCAL_PART_WORDS /
                      _DOMAIN_LABELS, reserved TLD omitted
    PARTIAL_PII    -> generators.pii.aadhaar / bank_account, first 8 digits
                      masked as "XXXX XXXX ", last 4 shown

Two implementation choices are disclosed here because guidelines.md §13.8
authorizes an "or" between underlying shapes without specifying a mix
(NUMERIC_SHAPE: PHONE/AADHAAR/BANK_ACCOUNT; PARTIAL_PII: AADHAAR/
BANK_ACCOUNT) -- this module cycles through the allowed shapes in the order
guidelines.md §13.8's own table lists them, a content-free tie-break
consistent with this project's existing pattern (§4.12's marker cycling,
§13.9's own remainder assignment), not a new policy decision requiring
sign-off, since guidelines.md already delegates the specific choice.

scenario.domain/scenario.purpose are not specified by any frozen decision
for hard negatives (unlike positives' §12.3 domain-distribution matrix).
This module uses one uniform, disclosed value across all 20 --
domain="customer_support" (matching the sole existing worked example,
tests/fixtures/base_instance.hard_negative.valid.json's NUMERIC_SHAPE case)
and purpose="hard_negative_context" (a neutral, decoy-agnostic string,
deliberately not implying an order-specific narrative for classes it
wouldn't fit). This is an implementation-level choice, not a governance
freeze -- flagged here rather than silently generalized from one example.

Determinism: one random.Random(SEED) instance, consumed in fixed class
order (CLASS_ORDER) matching guidelines.md §13.9's own table order, each
class's instances in index order. A rerun of
generate_hard_negative_bases(42) is byte-for-byte identical.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from jsonschema import Draft202012Validator

from generators.pii.aadhaar import generate_aadhaar
from generators.pii.bank_account import generate_bank_account
from generators.pii.email import _DOMAIN_LABELS, _LOCAL_PART_WORDS
from generators.pii.pan import generate_pan
from generators.pii.person import _GIVEN_NAMES
from generators.pii.phone import generate_phone
from validators.base_kind import (
    check_base_kind_hard_negative_decoy_invariant,
    check_base_kind_pii_invariant,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "base_instance.schema.json"
_OUTPUT_PATH = _REPO_ROOT / "data" / "raw" / "hard_negative_bases.jsonl"

SEED = 42

# Same toolchain-version field and convention as generators/base_instances.py
# (schemas/base_instance.schema.json, resolves OQ-020) -- no new version
# number invented for this generator.
GENERATOR_VERSION = "0.1.0"

# Frozen quota, guidelines.md §13.9 (redistributed after ORG_AS_PERSON's
# deferral) -- table order preserved, ORG_AS_PERSON kept explicit at 0
# rather than omitted, so its exclusion is visible, not merely implied.
CLASS_ORDER = (
    "NUMERIC_SHAPE",
    "ALNUM_SHAPE",
    "NAME_AS_PLACE",
    "HANDLE_SHAPE",
    "ORG_AS_PERSON",
    "PARTIAL_PII",
)
DECOY_QUOTA = {
    "NUMERIC_SHAPE": 5,
    "ALNUM_SHAPE": 5,
    "NAME_AS_PLACE": 4,
    "HANDLE_SHAPE": 3,
    "ORG_AS_PERSON": 0,
    "PARTIAL_PII": 3,
}

# Frozen per-class actual_role/canonical_text template, guidelines.md §13.8's
# own table -- reused verbatim, not re-derived.
_ACTUAL_ROLE = {
    "NUMERIC_SHAPE": "ORDER_REFERENCE",
    "ALNUM_SHAPE": "REFERENCE_CODE",
    "NAME_AS_PLACE": "LOCALITY",
    "HANDLE_SHAPE": "INTERNAL_HANDLE",
    "PARTIAL_PII": "MASKED_IDENTIFIER",
}

# Implementation-level scenario choice, disclosed in the module docstring --
# not a governance freeze.
_SCENARIO_DOMAIN = "customer_support"
_SCENARIO_PURPOSE = "hard_negative_context"

# Order-of-mention cycling for classes guidelines.md §13.8 leaves an
# explicit "or" between underlying shapes for -- disclosed, not a new
# policy decision (see module docstring).
_NUMERIC_SHAPE_CYCLE = ("PHONE", "AADHAAR", "BANK_ACCOUNT")
_PARTIAL_PII_CYCLE = ("AADHAAR", "BANK_ACCOUNT")


def _construct_numeric_shape(rng: random.Random, index: int) -> tuple[dict, str]:
    shape = _NUMERIC_SHAPE_CYCLE[index % len(_NUMERIC_SHAPE_CYCLE)]
    if shape == "PHONE":
        value = generate_phone(rng).base_pii_value
    elif shape == "AADHAAR":
        value = generate_aadhaar(rng).base_pii_value
    else:
        value = generate_bank_account(rng).base_pii_value
    decoy = {
        "decoy_class": "NUMERIC_SHAPE",
        "value": value,
        "surface_type": shape,
        "actual_role": _ACTUAL_ROLE["NUMERIC_SHAPE"],
    }
    return decoy, f"The order number is {value}."


def _construct_alnum_shape(rng: random.Random, index: int) -> tuple[dict, str]:
    value = generate_pan(rng).base_pii_value
    decoy = {
        "decoy_class": "ALNUM_SHAPE",
        "value": value,
        "surface_type": "PAN",
        "actual_role": _ACTUAL_ROLE["ALNUM_SHAPE"],
    }
    return decoy, f"The reference code is {value}."


def _construct_name_as_place(rng: random.Random, index: int) -> tuple[dict, str]:
    name = rng.choice(_GIVEN_NAMES)
    value = f"{name} Nagar"
    decoy = {
        "decoy_class": "NAME_AS_PLACE",
        "value": value,
        "surface_type": "LOCATION",
        "actual_role": _ACTUAL_ROLE["NAME_AS_PLACE"],
    }
    return decoy, f"{value} is near the station."


def _construct_handle_shape(rng: random.Random, index: int) -> tuple[dict, str]:
    local = rng.choice(_LOCAL_PART_WORDS) + str(rng.randint(10, 9999))
    label = rng.choice(_DOMAIN_LABELS)
    value = f"{local}@{label}"  # reserved TLD deliberately omitted, §13.8
    decoy = {
        "decoy_class": "HANDLE_SHAPE",
        "value": value,
        "surface_type": "EMAIL",
        "actual_role": _ACTUAL_ROLE["HANDLE_SHAPE"],
    }
    return decoy, f"You can also reach me at {value}."


def _construct_partial_pii(rng: random.Random, index: int) -> tuple[dict, str]:
    shape = _PARTIAL_PII_CYCLE[index % len(_PARTIAL_PII_CYCLE)]
    full_value = (
        generate_aadhaar(rng).base_pii_value
        if shape == "AADHAAR"
        else generate_bank_account(rng).base_pii_value
    )
    masked = "XXXX XXXX " + full_value[-4:]
    decoy = {
        "decoy_class": "PARTIAL_PII",
        "value": masked,
        "surface_type": shape,
        "actual_role": _ACTUAL_ROLE["PARTIAL_PII"],
    }
    return decoy, f"The account number is {masked}."


_CONSTRUCTORS = {
    "NUMERIC_SHAPE": _construct_numeric_shape,
    "ALNUM_SHAPE": _construct_alnum_shape,
    "NAME_AS_PLACE": _construct_name_as_place,
    "HANDLE_SHAPE": _construct_handle_shape,
    "PARTIAL_PII": _construct_partial_pii,
}


def _draw_unique_decoy(decoy_class: str, rng: random.Random, index: int, seen: set) -> tuple[dict, str]:
    """Draw one (decoy, canonical_text) pair, redrawing from the same rng
    stream on a within-class value collision -- same dataset-hygiene
    pattern as generators/base_instances.py's _draw_unique_value, preserving
    full run determinism."""
    constructor = _CONSTRUCTORS[decoy_class]
    for _ in range(10_000):
        decoy, canonical_text = constructor(rng, index)
        if decoy["value"] not in seen:
            seen.add(decoy["value"])
            return decoy, canonical_text
    raise RuntimeError(f"could not draw a unique {decoy_class} value after 10000 attempts")


def generate_hard_negative_bases(seed: int = SEED) -> list:
    """Generate the 20 pilot HARD_NEGATIVE base instances, deterministically.

    ORG_AS_PERSON's quota is 0 (guidelines.md §13.9) -- the loop below
    produces nothing for it, since DECOY_QUOTA["ORG_AS_PERSON"] == 0 and no
    constructor exists for it in _CONSTRUCTORS.
    """
    rng = random.Random(seed)
    records = []
    seen_by_class: dict[str, set] = {c: set() for c in CLASS_ORDER}
    counter = 0

    for decoy_class in CLASS_ORDER:
        count = DECOY_QUOTA[decoy_class]
        for index in range(count):
            counter += 1
            base_id = f"NEG_{counter:03d}"
            decoy, canonical_text = _draw_unique_decoy(
                decoy_class, rng, index, seen_by_class[decoy_class]
            )

            record = {
                "base_id": base_id,
                "base_kind": "HARD_NEGATIVE",
                "pii": [],
                "person_context": None,
                "scenario": {"domain": _SCENARIO_DOMAIN, "purpose": _SCENARIO_PURPOSE},
                "address_structure": None,
                "canonical_text": canonical_text,
                "synthetic": True,
                "generator_version": GENERATOR_VERSION,
                "hard_negative_decoy": decoy,
            }
            records.append(record)

    return records


def assert_hard_negative_dataset_valid(records: list) -> None:
    """All required assertions before any write is attempted. Raises on the
    first violation -- callers must not catch-and-continue."""
    if len(records) != 20:
        raise AssertionError(f"expected exactly 20 records, got {len(records)}")

    class_counts: dict[str, int] = {c: 0 for c in CLASS_ORDER}
    base_ids = []
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    for record in records:
        if record["base_kind"] != "HARD_NEGATIVE":
            raise AssertionError(f"{record['base_id']}: base_kind != HARD_NEGATIVE")
        if record["pii"] != []:
            raise AssertionError(f"{record['base_id']}: pii must be []")
        if "entities" in record or "distractors" in record:
            raise AssertionError(f"{record['base_id']}: entities/distractors must not be present")

        decoy = record.get("hard_negative_decoy")
        if not decoy:
            raise AssertionError(f"{record['base_id']}: hard_negative_decoy must be populated")
        class_counts[decoy["decoy_class"]] += 1
        base_ids.append(record["base_id"])

        validator.validate(record)
        check_base_kind_pii_invariant(record)
        check_base_kind_hard_negative_decoy_invariant(record)

        occurrences = record["canonical_text"].count(decoy["value"])
        if occurrences != 1:
            raise AssertionError(
                f"{record['base_id']}: decoy value occurs {occurrences} times in "
                f"canonical_text, expected exactly 1"
            )

    if class_counts != DECOY_QUOTA:
        raise AssertionError(f"decoy-class counts {class_counts} != {DECOY_QUOTA}")

    if len(base_ids) != len(set(base_ids)):
        raise AssertionError("duplicate base_id detected")


def write_hard_negative_bases(records: list, output_path: Path = _OUTPUT_PATH) -> None:
    """Write JSONL. Fails rather than overwriting an existing file -- never
    silently overwrite a generated dataset (CLAUDE.md), same policy as
    generators/base_instances.py's write_pilot_base_instances."""
    if output_path.exists():
        raise FileExistsError(
            f"{output_path} already exists -- refusing to overwrite it. "
            "Move or version the existing file before regenerating."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> list:
    records = generate_hard_negative_bases(SEED)
    assert_hard_negative_dataset_valid(records)
    write_hard_negative_bases(records)
    return records


if __name__ == "__main__":
    main()
