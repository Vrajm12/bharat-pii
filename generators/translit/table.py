"""T07: deterministic transliteration table (guidelines.md Section 4.7-4.9).

This is a benchmark-specific deterministic transliteration table, not a
general-purpose Hindi transliteration system.

Token-level lookup only: one entry per Latin token reachable from the
frozen T03 PERSON (generators/pii/person.py) and ADDRESS
(generators/pii/address.py) vocabularies, each mapped to a single, curated
Devanagari string. No character-level substitution, no LLM, no
probabilistic method, no external general-purpose transliteration
algorithm or library is used anywhere in this module (guidelines.md
Section 4.7 / Section 4.9 / OQ-016 / OQ-019).

A lookup miss fails closed (Section 4.9 / OQ-018): TransliterationError is
raised, never a guess, never a passthrough.

Numeric runs and punctuation/whitespace are never looked up -- they pass
through a transliterated value unchanged (Section 4.8 / OQ-017).

`ABC` -> `एबीसी` and `MG` -> `एमजी` (Section 4.8 / OQ-022) are frozen,
benchmark-specific deterministic conventions -- not claims about universal
correct transliteration of these abbreviations/initialisms.
"""

from __future__ import annotations

import re

# --- PERSON: generators/pii/person.py's frozen given-name vocabulary (20) ---
_PERSON_GIVEN_NAMES = {
    "Rahul": "राहुल",
    "Priya": "प्रिया",
    "Amit": "अमित",
    "Sneha": "स्नेहा",
    "Arjun": "अर्जुन",
    "Kavya": "काव्या",
    "Vikram": "विक्रम",
    "Anjali": "अंजलि",
    "Rohan": "रोहन",
    "Deepika": "दीपिका",
    "Suresh": "सुरेश",
    "Meera": "मीरा",
    "Karan": "करण",
    "Divya": "दिव्या",
    "Sanjay": "संजय",
    "Pooja": "पूजा",
    "Rajesh": "राजेश",
    "Neha": "नेहा",
    "Aditya": "आदित्य",
    "Ritu": "ऋतु",
}

# --- PERSON: generators/pii/person.py's frozen family-name vocabulary (20) ---
_PERSON_FAMILY_NAMES = {
    "Sharma": "शर्मा",
    "Iyer": "अय्यर",
    "Patel": "पटेल",
    "Reddy": "रेड्डी",
    "Nair": "नायर",
    "Gupta": "गुप्ता",
    "Menon": "मेनन",
    "Rao": "राव",
    "Verma": "वर्मा",
    "Kulkarni": "कुलकर्णी",
    "Chatterjee": "चटर्जी",
    "Desai": "देसाई",
    "Joshi": "जोशी",
    "Pillai": "पिल्लई",
    "Singh": "सिंह",
    "Bose": "बोस",
    "Mehta": "मेहता",
    "Agarwal": "अग्रवाल",
    "Krishnan": "कृष्णन",
    "Bhatt": "भट्ट",
}

# --- ADDRESS: generators/pii/address.py's frozen city vocabulary (8) ---
_ADDRESS_CITIES = {
    "Pune": "पुणे",
    "Mumbai": "मुंबई",
    "Bengaluru": "बेंगलुरु",
    "Hyderabad": "हैदराबाद",
    "Chennai": "चेन्नई",
    "Kolkata": "कोलकाता",
    "Jaipur": "जयपुर",
    "Lucknow": "लखनऊ",
}

# --- ADDRESS: words split from _BUILDING_NAMES, _ROAD_NAMES, and the
# literal "Flat" -- every one of these is a standard English loanword with
# an established, conventional Devanagari rendering. (29 entries)
_ADDRESS_WORDS = {
    "Flat": "फ्लैट",
    "Apartments": "अपार्टमेंट्स",
    "Green": "ग्रीन",
    "Valley": "वैली",
    "Residency": "रेजिडेंसी",
    "Sunrise": "सनराइज़",
    "Towers": "टावर्स",
    "Lotus": "लोटस",
    "Enclave": "एन्क्लेव",
    "Silver": "सिल्वर",
    "Oak": "ओक",
    "Heights": "हाइट्स",
    "Palm": "पाम",
    "Grove": "ग्रोव",
    "Society": "सोसाइटी",
    "Maple": "मेपल",
    "Orchid": "ऑर्किड",
    "Homes": "होम्स",
    "Baner": "बानेर",
    "Road": "रोड",
    "Ring": "रिंग",
    "Station": "स्टेशन",
    "Church": "चर्च",
    "Street": "स्ट्रीट",
    "Lake": "लेक",
    "View": "व्यू",
    "Hill": "हिल",
    "Side": "साइड",
    "Market": "मार्केट",
}

# --- ADDRESS: abbreviation/initialism tokens (OQ-022) -- frozen,
# benchmark-specific conventions, not universal transliteration claims (2)
_ADDRESS_ABBREVIATIONS = {
    "ABC": "एबीसी",
    "MG": "एमजी",
}

# The one unified table (79 entries: 40 PERSON + 39 ADDRESS). No collisions
# exist between the PERSON and ADDRESS vocabularies.
TABLE: dict = {
    **_PERSON_GIVEN_NAMES,
    **_PERSON_FAMILY_NAMES,
    **_ADDRESS_CITIES,
    **_ADDRESS_WORDS,
    **_ADDRESS_ABBREVIATIONS,
}

assert len(TABLE) == 79, f"expected 79 table entries, got {len(TABLE)}"

# Splits a value into alphabetic runs, digit runs, and "everything else"
# (whitespace, punctuation) runs. The three alternatives partition every
# character, so concatenating all matched groups in original order always
# reconstructs the input exactly.
_TOKEN_RE = re.compile(r"[A-Za-z]+|[0-9]+|[^A-Za-z0-9]+")


class TransliterationError(ValueError):
    """Raised on a transliteration-table lookup miss (fail closed, Section 4.9).

    Never guess, never call an LLM, never call an external service, never
    pass an untranslated token through silently.
    """


def transliterate_token(token: str) -> str:
    """Look up one alphabetic token. Raises TransliterationError on miss."""
    try:
        return TABLE[token]
    except KeyError:
        raise TransliterationError(
            f"no transliteration-table entry for {token!r} -- fails closed "
            f"(guidelines.md Section 4.9); never guessed, never passed through"
        ) from None


def transliterate_value(value: str) -> str:
    """Transliterate a full PERSON or ADDRESS base_pii_value.

    Alphabetic runs are looked up in TABLE (raises TransliterationError on
    miss). Digit runs and all other runs (whitespace, punctuation) pass
    through unchanged (Section 4.8).
    """
    pieces = []
    for run in _TOKEN_RE.findall(value):
        if run[0].isalpha():
            pieces.append(transliterate_token(run))
        else:
            pieces.append(run)
    return "".join(pieces)
