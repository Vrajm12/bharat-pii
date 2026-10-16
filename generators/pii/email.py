"""Synthetic EMAIL generator.

Structural rule implemented: `<local-part>@<label>.<reserved TLD>`, TLD
restricted to exactly {test, invalid, example}. This is the one PII type in
T03 with a fully specified, zero-ambiguity safety rule -- explicitly
required by CLAUDE.md ("Email domains restricted to .test, .invalid,
.example"), guidelines.md §9, and PROJECT_SPEC.md §11.1, all independently
stating the same three TLDs. These are RFC 2606 reserved special-use TLDs:
the entire TLD is reserved for documentation/testing use, not just specific
names under it, so any label chosen before the TLD is guaranteed
non-resolvable and never a real mailbox. No judgment call was needed for
this generator, unlike the others in this task.

local-part is a synthetic username-like token (lowercased name component +
a random digit suffix); the second-level label before the TLD is an
arbitrary synthetic word.
"""

from __future__ import annotations

import random

from generators.pii._common import GeneratedPII

_RESERVED_TLDS = ("test", "invalid", "example")
_LOCAL_PART_WORDS = (
    "rahul", "priya", "amit", "sneha", "arjun", "kavya", "vikram", "anjali",
    "rohan", "deepika",
)
_DOMAIN_LABELS = ("mail", "corp", "webmail", "inbox")


def generate_email(rng: random.Random) -> GeneratedPII:
    """Generate one synthetic email address on a reserved TLD.

    Deterministic given `rng`.
    """
    local = rng.choice(_LOCAL_PART_WORDS) + str(rng.randint(10, 9999))
    label = rng.choice(_DOMAIN_LABELS)
    tld = rng.choice(_RESERVED_TLDS)
    value = f"{local}@{label}.{tld}"
    return GeneratedPII(type="EMAIL", base_pii_value=value)
