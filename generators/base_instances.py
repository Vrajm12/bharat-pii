"""T04: assemble the 100 pilot POSITIVE, single-PII base instances.

Scope (approved T04 design, 2026-08-23): exactly 100 base instances, one
target PII item each, base_kind == POSITIVE for all. No language variants,
no multi-PII bases, no hard negatives, no adversarial variants, no splits.

This module owns four decisions that were explicitly frozen by the user
before generation, not invented here:

1. `SEMANTIC_ROLE` -- one fixed value per PII type. These are BENCHMARK
   semantic roles, not claims about universal real-world roles.
2. `DOMAIN_SEQUENCE` -- the approved type x domain allocation matrix,
   expanded into a deterministic per-base domain assignment. No domain is
   ever chosen independently or at random; `_validate_matrix()` asserts the
   expansion reconciles exactly against both the per-category totals
   (CATEGORY_COUNTS) and PROJECT_SPEC.md Section 12.3's per-domain totals.
3. `CANONICAL_TEMPLATE` -- canonical_text is produced here, absorbing what
   PROJECT_SPEC.md Section 31 separately labels T06, per explicit decision:
   schemas/base_instance.schema.json requires canonical_text on every valid
   base instance, so T04 cannot produce schema-valid output without it.
4. Uniqueness of `base_pii_value` within each PII category is a documented
   dataset-hygiene constraint chosen for this generation run -- it is not a
   requirement stated anywhere in guidelines.md or PROJECT_SPEC.md.

`person_context.name_deva` is populated via `generators.translit.table` (T07,
guidelines.md §4.5/§4.7) -- a pure lookup with no rng consumption, so its
addition does not alter the draw sequence or value of any other field.
`generator_version` (schemas/base_instance.schema.json, OQ-020) is recorded
on every record.

Determinism: one `random.Random(SEED)` instance, consumed in a fixed
category order (CATEGORY_ORDER), each category's bases in index order. A
rerun of `generate_pilot_base_instances(42)` is byte-for-byte identical.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from jsonschema import Draft202012Validator

from generators.pii.aadhaar import generate_aadhaar
from generators.pii.address import generate_address
from generators.pii.bank_account import generate_bank_account
from generators.pii.email import generate_email
from generators.pii.pan import generate_pan
from generators.pii.person import generate_person
from generators.pii.phone import generate_phone
from generators.pii.upi_id import generate_upi_id
from generators.translit.table import transliterate_value
from validators.base_kind import check_base_kind_pii_invariant

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "base_instance.schema.json"
_OUTPUT_PATH = _REPO_ROOT / "data" / "raw" / "base_instances.jsonl"

SEED = 42

# Toolchain version recorded on every base instance (schemas/base_instance.schema.json,
# resolves OQ-020). One version number covers PII generation (T03), base-instance
# assembly (T04), and the transliteration table (T07) -- PROJECT_SPEC.md §8.3 /
# guidelines.md §4.5 record the transliteration table's version in this same field,
# not a separate one.
GENERATOR_VERSION = "0.1.0"

# Fixed category order and counts -- PROJECT_SPEC.md Section 12.2.
CATEGORY_ORDER = (
    "PERSON", "ADDRESS", "PHONE", "EMAIL",
    "PAN", "AADHAAR", "UPI_ID", "BANK_ACCOUNT",
)
CATEGORY_COUNTS = {
    "PERSON": 12, "ADDRESS": 12, "PHONE": 12, "EMAIL": 12,
    "PAN": 13, "AADHAAR": 13, "UPI_ID": 13, "BANK_ACCOUNT": 13,
}

_GENERATORS = {
    "PERSON": generate_person,
    "ADDRESS": generate_address,
    "PHONE": generate_phone,
    "EMAIL": generate_email,
    "PAN": generate_pan,
    "AADHAAR": generate_aadhaar,
    "UPI_ID": generate_upi_id,
    "BANK_ACCOUNT": generate_bank_account,
}

# Frozen semantic_role mapping (user decision, 2026-08-23; PERSON revised
# 2026-08-23 per OQ-007 -- see annotation/guidelines.md §12.5 and
# annotation/open_questions.md). BENCHMARK semantic roles, not claims about
# universal real-world roles. semantic_role describes the role/type of the
# PII value itself; scenario.domain / scenario.purpose carry the contextual
# use -- PERSON_NAME is deliberately domain-neutral so it fits an employee,
# a patient, a delivery recipient, an account holder, or a person mentioned
# in casual conversation without implying any one of those relationships.
SEMANTIC_ROLE = {
    "PERSON": "PERSON_NAME",
    "ADDRESS": "DELIVERY_ADDRESS",
    "PHONE": "CONTACT_NUMBER",
    "EMAIL": "CONTACT_EMAIL",
    "PAN": "TAX_IDENTIFIER",
    "AADHAAR": "NATIONAL_ID_IDENTIFIER",
    "UPI_ID": "PAYMENT_IDENTIFIER",
    "BANK_ACCOUNT": "PAYMENT_ACCOUNT_IDENTIFIER",
}

# Frozen canonical-sentence templates (approved T04 design report).
CANONICAL_TEMPLATE = {
    "PERSON": "My name is {value}.",
    "ADDRESS": "My address is {value}.",
    "PHONE": "My phone number is {value}.",
    "EMAIL": "Email me at {value}.",
    "PAN": "My PAN number is {value}.",
    "AADHAAR": "My Aadhaar number is {value}.",
    "UPI_ID": "My UPI ID is {value}.",
    "BANK_ACCOUNT": "My bank account number is {value}.",
}

# Frozen purpose-per-domain mapping (approved T04 design report).
PURPOSE_BY_DOMAIN = {
    "banking_payments": "payment_processing",
    "customer_support": "support_ticket_resolution",
    "delivery_address": "delivery_confirmation",
    "account_verification": "identity_verification",
    "telecom": "service_activation",
    "employment_hr": "employee_onboarding",
    "healthcare_administration": "patient_registration",
    "general_conversation": "casual_mention",
}

# Frozen type x domain allocation matrix (approved T04 design report),
# expanded in fixed column order (banking_payments, customer_support,
# delivery_address, account_verification, telecom, employment_hr,
# healthcare_administration, general_conversation; zero cells omitted).
# DOMAIN_SEQUENCE[category][i] is the domain of the (i+1)-th base of that
# category -- a deterministic table lookup, never a random draw.
DOMAIN_SEQUENCE = {
    "PERSON": (
        ["delivery_address"] * 1
        + ["employment_hr"] * 5
        + ["healthcare_administration"] * 3
        + ["general_conversation"] * 3
    ),
    "ADDRESS": ["delivery_address"] * 12,
    "PHONE": ["customer_support"] * 2 + ["telecom"] * 10,
    "EMAIL": (
        ["customer_support"] * 6
        + ["delivery_address"] * 2
        + ["healthcare_administration"] * 2
        + ["general_conversation"] * 2
    ),
    "PAN": ["banking_payments"] * 5 + ["account_verification"] * 8,
    "AADHAAR": ["banking_payments"] * 6 + ["account_verification"] * 7,
    "UPI_ID": ["banking_payments"] * 1 + ["customer_support"] * 12,
    "BANK_ACCOUNT": ["banking_payments"] * 13,
}

_EXPECTED_DOMAIN_TOTALS = {
    "banking_payments": 25,
    "customer_support": 20,
    "delivery_address": 15,
    "account_verification": 15,
    "telecom": 10,
    "employment_hr": 5,
    "healthcare_administration": 5,
    "general_conversation": 5,
}


def _validate_matrix() -> None:
    """Fail fast (at import time) if DOMAIN_SEQUENCE ever drifts from the
    approved per-category or per-domain totals."""
    for category, count in CATEGORY_COUNTS.items():
        actual = len(DOMAIN_SEQUENCE[category])
        if actual != count:
            raise AssertionError(
                f"DOMAIN_SEQUENCE[{category!r}] has {actual} entries, expected {count}"
            )

    domain_totals: dict[str, int] = {}
    for sequence in DOMAIN_SEQUENCE.values():
        for domain in sequence:
            domain_totals[domain] = domain_totals.get(domain, 0) + 1

    if domain_totals != _EXPECTED_DOMAIN_TOTALS:
        raise AssertionError(
            f"domain allocation totals {domain_totals} do not match the "
            f"approved matrix {_EXPECTED_DOMAIN_TOTALS}"
        )


_validate_matrix()


def _draw_unique_value(category: str, rng: random.Random, seen: set):
    """Draw one GeneratedPII for `category`, redrawing from the same `rng`
    stream on collision (dataset-hygiene constraint, not a research-spec
    requirement: base_pii_value must be unique within each PII category).
    Redrawing from the same stream preserves full run determinism."""
    generator = _GENERATORS[category]
    for _ in range(10_000):
        candidate = generator(rng)
        if candidate.base_pii_value not in seen:
            seen.add(candidate.base_pii_value)
            return candidate
    raise RuntimeError(
        f"could not draw a unique {category} value after 10000 attempts"
    )


def generate_pilot_base_instances(seed: int = SEED) -> list:
    """Generate the 100 pilot POSITIVE base instances, deterministically."""
    rng = random.Random(seed)
    records = []
    seen_by_category = {category: set() for category in CATEGORY_ORDER}

    for category in CATEGORY_ORDER:
        count = CATEGORY_COUNTS[category]
        for index in range(1, count + 1):
            target = _draw_unique_value(category, rng, seen_by_category[category])
            base_id = f"{category}_{index:03d}"

            if category == "PERSON":
                person_name = target.base_pii_value
            else:
                person_name = generate_person(rng).base_pii_value
            # transliterate_value consumes no rng state -- adding this call
            # does not alter the draw sequence of any other field (T07,
            # guidelines.md §4.5/§4.7; resolves the T04-deferred name_deva).
            person_name_deva = transliterate_value(person_name)

            domain = DOMAIN_SEQUENCE[category][index - 1]
            purpose = PURPOSE_BY_DOMAIN[domain]
            canonical_text = CANONICAL_TEMPLATE[category].format(
                value=target.base_pii_value
            )

            record = {
                "base_id": base_id,
                "base_kind": "POSITIVE",
                "pii": [
                    {
                        "type": target.type,
                        "base_pii_value": target.base_pii_value,
                        "semantic_role": SEMANTIC_ROLE[category],
                    }
                ],
                "person_context": {"name": person_name, "name_deva": person_name_deva},
                "scenario": {"domain": domain, "purpose": purpose},
                "address_structure": "SINGLE" if category == "ADDRESS" else None,
                "canonical_text": canonical_text,
                "synthetic": True,
                "generator_version": GENERATOR_VERSION,
            }
            records.append(record)

    return records


def assert_dataset_valid(records: list) -> None:
    """All required assertions before any write is attempted. Raises on the
    first violation -- callers must not catch-and-continue."""
    if len(records) != 100:
        raise AssertionError(f"expected exactly 100 records, got {len(records)}")

    category_counts: dict[str, int] = {}
    for record in records:
        category = record["base_id"].rsplit("_", 1)[0]
        category_counts[category] = category_counts.get(category, 0) + 1
    if category_counts != CATEGORY_COUNTS:
        raise AssertionError(f"category counts {category_counts} != {CATEGORY_COUNTS}")

    base_ids = [record["base_id"] for record in records]
    if len(base_ids) != len(set(base_ids)):
        raise AssertionError("duplicate base_id detected")

    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    seen_by_category: dict[str, set] = {}

    for record in records:
        if record["base_kind"] != "POSITIVE":
            raise AssertionError(f"{record['base_id']}: base_kind != POSITIVE")
        if len(record["pii"]) != 1:
            raise AssertionError(f"{record['base_id']}: expected exactly 1 pii item")

        entry = record["pii"][0]
        category = record["base_id"].rsplit("_", 1)[0]
        seen = seen_by_category.setdefault(category, set())
        if entry["base_pii_value"] in seen:
            raise AssertionError(
                f"duplicate {category} base_pii_value: {entry['base_pii_value']!r}"
            )
        seen.add(entry["base_pii_value"])

        validator.validate(record)
        check_base_kind_pii_invariant(record)

        occurrences = record["canonical_text"].count(entry["base_pii_value"])
        if occurrences != 1:
            raise AssertionError(
                f"{record['base_id']}: target PII occurs {occurrences} times in "
                f"canonical_text, expected exactly 1"
            )


def write_pilot_base_instances(
    records: list, output_path: Path = _OUTPUT_PATH
) -> None:
    """Write JSONL. Fails rather than overwriting an existing file -- never
    silently overwrite a generated dataset (CLAUDE.md)."""
    if output_path.exists():
        raise FileExistsError(
            f"{output_path} already exists -- refusing to overwrite it. "
            "Move or version the existing file before regenerating."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> list:
    records = generate_pilot_base_instances(SEED)
    assert_dataset_valid(records)
    write_pilot_base_instances(records)
    return records


if __name__ == "__main__":
    main()
