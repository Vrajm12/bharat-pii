"""Synthetic UPI_ID generator.

Format: BENCHMARK_SYNTHETIC decision (resolves OQ-006, explicit user
decision, annotation/guidelines.md §10.3, Grammar 3). Exactly:

    <10-digit-synthetic-phone>@mail.test

e.g. "9876543210@mail.test". This is a single, fixed grammar -- no
additional UPI_ID local-part or domain variants exist in T03.

Why this shape, and not one closer to real UPI syntax (real PSP suffixes
are a single token, never dotted, e.g. "@paytm", "@ybl", "@oksbi"):
PROJECT_SPEC.md §7 explicitly designs UPI_ID to "Shape-collide with EMAIL --
context-dependent typing," the specific property RQ3 and the
*Unmasking*-motivated part of this benchmark measure. The dotted
"@mail.test" suffix deliberately mirrors the EMAIL generator's own grammar
(generators/pii/email.py) so that surface-form collision is real, not
accidental -- while `mail.test` sits on the same RFC 2606 reserved TLD
(`.test`) EMAIL already uses, so it is guaranteed non-resolvable and cannot
route a real payment. It is additionally never a valid PSP token shape
(real PSP handles are never dotted), so it cannot be mistaken for a live
NPCI-registered handle even at the shape level. No real PSP handle or
domain is used or resembled.

The 10-digit local part mimics the "phone number as VPA" pattern, one of
the most common real-world UPI ID conventions, but is never a real phone
number -- it is generated the same way generators/pii/phone.py generates
its value (first digit 6-9, matching real Indian mobile numbering and every
phone example in the governing documents), independently and synthetically,
never sourced from any real number.

No government/payment checksum or validation logic is applied or claimed --
this value is not intended to represent an issued or NPCI-registered UPI
handle. Downstream base instances/records carrying this value set
`"synthetic": true` per the existing base-instance/record schema
requirement (schemas/base_instance.schema.json, schemas/example.schema.json)
-- that flag is a base-instance/record-level field, not something this
value-only generator sets itself.
"""

from __future__ import annotations

import random

from generators.pii._common import GeneratedPII

_LOCAL_FIRST_DIGITS = "6789"
_FIXED_DOMAIN = "mail.test"


def _synthetic_phone_shaped_local(rng: random.Random) -> str:
    first = rng.choice(_LOCAL_FIRST_DIGITS)
    rest = "".join(rng.choice("0123456789") for _ in range(9))
    return first + rest


def generate_upi_id(rng: random.Random) -> GeneratedPII:
    """Generate one BENCHMARK_SYNTHETIC UPI_ID value: <10-digit local>@mail.test.

    Deterministic given `rng`.
    """
    local = _synthetic_phone_shaped_local(rng)
    value = f"{local}@{_FIXED_DOMAIN}"
    return GeneratedPII(type="UPI_ID", base_pii_value=value)
