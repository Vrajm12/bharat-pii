"""Synthetic AADHAAR generator.

Format: BENCHMARK_SYNTHETIC decision (resolves OQ-004, explicit user
decision, annotation/guidelines.md §11.4). Exactly 12 decimal digits,
generated synthetically. This is NOT claimed to be the official Indian
Aadhaar format -- neither governing document specifies Aadhaar's real digit
count or structure anywhere (see OQ-004's evidentiary record in
annotation/open_questions.md); every worked example in both documents uses
a `<AADHAAR_VALUE>` placeholder, never a concrete value. This generator
therefore implements a benchmark-only representation, chosen for controlled
experiments, not a real-world identifier format.

No UIDAI checksum (Verhoeff algorithm) or issuance-range validation is
applied or claimed -- per the explicit decision, none is required. Digits
are uniform-random across all 12 positions, including the first; no
leading-digit exclusion is applied, since this value is not intended to
represent an issued identifier in the first place.
"""

from __future__ import annotations

import random

from generators.pii._common import GeneratedPII


def generate_aadhaar(rng: random.Random) -> GeneratedPII:
    """Generate one BENCHMARK_SYNTHETIC 12-digit AADHAAR-shaped value.

    Deterministic given `rng`.
    """
    value = "".join(rng.choice("0123456789") for _ in range(12))
    return GeneratedPII(type="AADHAAR", base_pii_value=value)
