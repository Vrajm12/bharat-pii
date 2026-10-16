"""Shared plumbing for the eight PII value generators (T03).

Scope boundary (PROJECT_SPEC.md §31: T03 vs T04). These generators produce a
single synthetic PII *value* and its type -- nothing more. They do not
accept, consult, or infer:

- base_kind (validators/base_kind.py's frozen POSITIVE/HARD_NEGATIVE
  invariant is a base-instance-level concern; a raw PII value generator has
  no way to know, and must not need to know, which kind of base it will end
  up in).
- base_id (naming conventions on base_id must never be used to infer
  anything, per guidelines.md §13.4 -- including here, where base_id simply
  does not exist yet).
- semantic_role, scenario, person_context, canonical_text -- all assigned at
  base-instance assembly time (T04), not here.

Determinism. Every generator takes a random.Random instance supplied by the
caller (never the global `random` module), per CLAUDE.md's "deterministic
seed (42) for all non-LLM randomness" rule. Two independently-seeded
`random.Random(42)` instances calling the same generator once each produce
identical output. A caller that owns one shared `random.Random` instance and
calls several generators against it in a fixed order gets a reproducible
sequence.

Identifier safety. Every value produced by any of these generators is
synthetic-by-construction (PROJECT_SPEC.md §11.1 / guidelines.md §11.3).
None of them check output against, derive it from, or match it to any real
record. None of them claim their output is "provably unissued" -- only that
it was constructed synthetically, per CLAUDE.md's explicit prohibition on
overclaiming.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BASE_INSTANCE_SCHEMA = _REPO_ROOT / "schemas" / "base_instance.schema.json"


def _load_pii_types() -> tuple[str, ...]:
    """Load the pii_type enum from schemas/base_instance.schema.json.

    Loaded from the schema rather than redeclared as a second Python-side
    list, so the eight-category enum has exactly one source of truth
    (matches the "use constants already frozen in the repository" scope
    rule for T03).
    """
    schema = json.loads(_BASE_INSTANCE_SCHEMA.read_text(encoding="utf-8"))
    return tuple(schema["$defs"]["pii_type"]["enum"])


PII_TYPES: tuple[str, ...] = _load_pii_types()


@dataclass(frozen=True)
class GeneratedPII:
    """Output of a single T03 generator call.

    Deliberately minimal: `type` and `base_pii_value` are exactly the two
    fields a future base-instance generator (T04) needs from a raw PII
    generator to build one entry of `pii[]`
    (schemas/base_instance.schema.json). `semantic_role`, the third field
    that entry requires, is scenario-dependent and is assigned at
    base-assembly time -- it is out of scope for a type-specific value
    generator.
    """

    type: str
    base_pii_value: str

    def __post_init__(self) -> None:
        if self.type not in PII_TYPES:
            raise ValueError(f"{self.type!r} is not a known pii_type: {PII_TYPES}")
        if not self.base_pii_value:
            raise ValueError("base_pii_value must be non-empty")
