"""Synthetic ADDRESS generator.

Structural rule implemented: no fixed regex applies -- ADDRESS is free text
(guidelines.md §7). The rule implemented here is the component shape
guidelines.md §7.1's own worked example uses: "<flat>, <building>, <road>,
<city> <PIN>". All components (flat number, building name, road name, PIN
digits) are self-authored / synthetic-by-construction; city names are
well-known public Indian city names, not personal data -- guidelines.md's
own example uses "Pune" the same way.

PIN code: six digits, first digit 1-8 (the real Indian PIN code
numbering-zone convention). No publicly documented reserved/test PIN range
exists anywhere in the governing documents or, to this generator's
knowledge, in public India Post documentation, unlike email's RFC 2606 TLDs
-- so this is synthetic-by-construction per PROJECT_SPEC.md §11.1's
fallback ("where none is documented, values are synthetic-by-construction"),
not drawn from any reserved range, and no claim of reservedness is made.

Explicitly out of scope for this generator (deferred to later tasks):
- Devanagari transliteration -- T07.
- address_structure (SINGLE vs SPLIT, guidelines.md §7.3) governs how many
  spans an address becomes inside a generated *sentence*; this generator
  always returns one contiguous address string as base_pii_value, matching
  the SINGLE case. Splitting is a sentence-construction concern (T06),
  not a value-generation concern.
- Landmark-relative phrasing ("near X", guidelines.md §7.2) is spanning
  behaviour for generated sentence text, not something this generator
  produces -- it has no sentence to place a landmark phrase into.
"""

from __future__ import annotations

import random

from generators.pii._common import GeneratedPII

_BUILDING_NAMES = (
    "ABC Apartments", "Green Valley Residency", "Sunrise Towers",
    "Lotus Enclave", "Silver Oak Heights", "Palm Grove Society",
    "Maple Residency", "Orchid Homes",
)
_ROAD_NAMES = (
    "Baner Road", "MG Road", "Ring Road", "Station Road", "Church Street",
    "Lake View Road", "Hill Side Road", "Market Road",
)
_CITIES = (
    "Pune", "Mumbai", "Bengaluru", "Hyderabad", "Chennai", "Kolkata",
    "Jaipur", "Lucknow",
)
_PIN_FIRST_DIGITS = "12345678"


def _synthetic_pin_code(rng: random.Random) -> str:
    first = rng.choice(_PIN_FIRST_DIGITS)
    rest = "".join(rng.choice("0123456789") for _ in range(5))
    return first + rest


def generate_address(rng: random.Random) -> GeneratedPII:
    """Generate one synthetic, single-span Indian address.

    Deterministic given `rng`.
    """
    house_no = rng.randint(1, 499)
    building = rng.choice(_BUILDING_NAMES)
    road = rng.choice(_ROAD_NAMES)
    city = rng.choice(_CITIES)
    pin = _synthetic_pin_code(rng)
    value = f"Flat {house_no}, {building}, {road}, {city} {pin}"
    return GeneratedPII(type="ADDRESS", base_pii_value=value)
