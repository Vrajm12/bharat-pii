"""Synthetic BANK_ACCOUNT generator.

Format: BENCHMARK_SYNTHETIC decision (resolves OQ-005, explicit user
decision, annotation/guidelines.md §11.4). Exactly 12 decimal digits,
generated synthetically. Real Indian bank account numbers have no single
standard length -- they vary roughly 9-18 digits by bank -- so 12 digits
here is explicitly NOT claimed to be the universal length or format of
Indian bank accounts. It is a fixed representation chosen for controlled
experiments: the purpose is recognizing account-number-like PII in context,
not validating real bank credentials.
"""

from __future__ import annotations

import random

from generators.pii._common import GeneratedPII


def generate_bank_account(rng: random.Random) -> GeneratedPII:
    """Generate one BENCHMARK_SYNTHETIC 12-digit BANK_ACCOUNT-shaped value.

    Deterministic given `rng`.
    """
    value = "".join(rng.choice("0123456789") for _ in range(12))
    return GeneratedPII(type="BANK_ACCOUNT", base_pii_value=value)
