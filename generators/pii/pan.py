"""Synthetic PAN generator.

Structural rule implemented: 5 uppercase letters + 4 digits + 1 uppercase
letter (10 characters total), e.g. "ABCDE1234F". This shape has the
strongest evidentiary basis of any type in this task: guidelines.md reuses
this *exact* value as its canonical worked example throughout the entire
document (§2, §5.4, §11.1, §17, and elsewhere) -- a concrete, repeated,
document-native example, not outside knowledge applied by this generator.

Explicitly out of scope: real PAN's internal semantic structure (the 4th
character conventionally encodes the holder category -- individual,
company, etc., in the real-world format). Neither governing document
mentions this, and encoding it would add a layer of realism beyond what
either document asked for; letters and digits here are uniform-random
within their character classes, matching the shape only.
"""

from __future__ import annotations

import random
import string

from generators.pii._common import GeneratedPII


def generate_pan(rng: random.Random) -> GeneratedPII:
    """Generate one synthetic PAN-shaped value.

    Deterministic given `rng`.
    """
    letters_a = "".join(rng.choice(string.ascii_uppercase) for _ in range(5))
    digits = "".join(rng.choice(string.digits) for _ in range(4))
    letter_z = rng.choice(string.ascii_uppercase)
    value = f"{letters_a}{digits}{letter_z}"
    return GeneratedPII(type="PAN", base_pii_value=value)
