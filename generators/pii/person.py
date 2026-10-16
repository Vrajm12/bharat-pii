"""Synthetic PERSON (Indian name) generator.

Structural rule implemented: no fixed regex applies -- PERSON is free text
by definition (guidelines.md §5). The rule this generator implements is a
component shape: two space-separated tokens, a synthetic given name
followed by a synthetic family name, each drawn from a small, self-authored
pool of common, generic Indian name components. Nothing here is drawn from,
or checked against, any real named individual (PROJECT_SPEC.md §11:
"Permitted: synthetic names ... generated"). "Rahul Sharma" -- guidelines.md's
own running example throughout the document -- is one of the reachable
outputs, by construction.

Explicitly out of scope for this generator (deferred to later tasks):
- Devanagari transliteration (name_deva) -- T07's deterministic
  transliteration table, applied after base-instance creation, never here.
- Honorifics/titles (Mr, Shri, ji, bhai, ...) -- guidelines.md §5.2 excludes
  these from the PERSON span entirely, so none are ever generated here.
- person_context, scenario, or any base-instance assembly -- T04's job.
"""

from __future__ import annotations

import random

from generators.pii._common import GeneratedPII

# Self-authored, generic given-name and family-name components: common
# Indian first/last names with no tie to any specific real individual.
_GIVEN_NAMES = (
    "Rahul", "Priya", "Amit", "Sneha", "Arjun", "Kavya", "Vikram", "Anjali",
    "Rohan", "Deepika", "Suresh", "Meera", "Karan", "Divya", "Sanjay",
    "Pooja", "Rajesh", "Neha", "Aditya", "Ritu",
)
_FAMILY_NAMES = (
    "Sharma", "Iyer", "Patel", "Reddy", "Nair", "Gupta", "Menon", "Rao",
    "Verma", "Kulkarni", "Chatterjee", "Desai", "Joshi", "Pillai", "Singh",
    "Bose", "Mehta", "Agarwal", "Krishnan", "Bhatt",
)


def generate_person(rng: random.Random) -> GeneratedPII:
    """Generate one synthetic Indian person name.

    Deterministic given `rng` -- a caller-owned `random.Random` instance,
    never the global `random` module (CLAUDE.md seed-42 rule).
    """
    given = rng.choice(_GIVEN_NAMES)
    family = rng.choice(_FAMILY_NAMES)
    return GeneratedPII(type="PERSON", base_pii_value=f"{given} {family}")
