"""Synthetic PHONE generator.

Structural rule implemented: 10 digits, first digit in {6, 7, 8, 9}. The
10-digit shape is directly evidenced by guidelines.md §8's own worked
examples, which reuse one value across the document -- "9876543210",
"+91 9876543210", "+91-9876543210", "98765 43210" -- every one a 10-digit
number starting with 9. The {6,7,8,9} first-digit constraint matches real
Indian mobile numbering and every example in the docs; it is recorded here
as a documented assumption (no "reserved test range" is claimed -- none is
documented in the governing documents, so this falls under
PROJECT_SPEC.md §11.1's synthetic-by-construction fallback).

This generator returns the plain 10-digit canonical form only
("9876543210"). Intrinsic formatting variants (+91 prefix, hyphen, internal
5+5 space split) are a language-realization / adversarial-perturbation
concern (PROJECT_SPEC.md §8 language realizations, §10 perturbation family
A1 SPACING), applied later to a *record* derived from a base -- not a
base-value-generation concern, and out of scope here.
"""

from __future__ import annotations

import random

from generators.pii._common import GeneratedPII

_FIRST_DIGITS = "6789"


def generate_phone(rng: random.Random) -> GeneratedPII:
    """Generate one synthetic 10-digit Indian mobile-shaped number.

    Deterministic given `rng`.
    """
    first = rng.choice(_FIRST_DIGITS)
    rest = "".join(rng.choice("0123456789") for _ in range(9))
    return GeneratedPII(type="PHONE", base_pii_value=first + rest)
