"""Cross-field validator for the base_kind / pii-cardinality invariant.

Scope: this module enforces exactly one cross-field rule, defined in
annotation/guidelines.md §13.4 (resolves OQ-003):

    base_kind == POSITIVE      => len(pii) >= 1
    base_kind == HARD_NEGATIVE => len(pii) == 0

This is deliberately narrow. It is not the general structural validator
(PROJECT_SPEC.md T05) — it assumes the input already satisfies
schemas/base_instance.schema.json (base_kind is one of the two enum values,
pii is an array) and checks only the relationship between those two fields.

base_id naming conventions (e.g. a NEG_ prefix) are never consulted here,
per guidelines.md §13.4: base_kind is the sole discriminator.
"""

from __future__ import annotations

POSITIVE = "POSITIVE"
HARD_NEGATIVE = "HARD_NEGATIVE"
VALID_BASE_KINDS = (POSITIVE, HARD_NEGATIVE)


class BaseKindInvariantError(ValueError):
    """Raised when base_kind and pii cardinality disagree (guidelines.md §13.4)."""


def check_base_kind_pii_invariant(base_instance: dict) -> None:
    """Raise BaseKindInvariantError if base_kind and pii cardinality disagree.

    Assumes base_instance already validates against
    schemas/base_instance.schema.json (base_kind is a known enum value, pii
    is a list). Enum membership itself is schema-enforced and is not
    re-checked here.
    """
    base_kind = base_instance["base_kind"]
    pii_count = len(base_instance["pii"])

    if base_kind == POSITIVE and pii_count < 1:
        raise BaseKindInvariantError(
            f"base_kind == POSITIVE requires len(pii) >= 1, got {pii_count} "
            f"(base_id={base_instance.get('base_id')!r})"
        )

    if base_kind == HARD_NEGATIVE and pii_count != 0:
        raise BaseKindInvariantError(
            f"base_kind == HARD_NEGATIVE requires len(pii) == 0, got {pii_count} "
            f"(base_id={base_instance.get('base_id')!r})"
        )


def check_base_kind_hard_negative_decoy_invariant(base_instance: dict) -> None:
    """Raise BaseKindInvariantError if base_kind and hard_negative_decoy
    presence disagree (guidelines.md §13.12, resolves OQ-046).

        base_kind == POSITIVE      => hard_negative_decoy absent or null
        base_kind == HARD_NEGATIVE => hard_negative_decoy present and populated

    Assumes base_instance already validates against
    schemas/base_instance.schema.json -- when hard_negative_decoy is present
    and non-null, its own four required sub-fields (decoy_class, value,
    surface_type, actual_role) are already structurally enforced there. This
    function checks only the relationship between base_kind and whether the
    field is populated at all, kept as a separate function from
    check_base_kind_pii_invariant so each cross-field rule this module
    enforces stays independently testable, matching that function's own
    "deliberately narrow" scope.
    """
    base_kind = base_instance["base_kind"]
    decoy = base_instance.get("hard_negative_decoy")

    if base_kind == POSITIVE and decoy is not None:
        raise BaseKindInvariantError(
            f"base_kind == POSITIVE requires hard_negative_decoy to be absent or null, "
            f"got {decoy!r} (base_id={base_instance.get('base_id')!r})"
        )

    if base_kind == HARD_NEGATIVE and decoy is None:
        raise BaseKindInvariantError(
            f"base_kind == HARD_NEGATIVE requires a populated hard_negative_decoy, "
            f"got None (base_id={base_instance.get('base_id')!r})"
        )
