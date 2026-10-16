"""T08: frozen carrier templates and marker/insertion inventories.

Every constant here reproduces content already frozen in annotation/guidelines.md
v0.11 (Section 4.12-4.14, Section 4.15). Nothing here is invented -- this module
is the machine-readable form of those tables. No LLM, no external service, no
randomness.
"""

from __future__ import annotations

LANGUAGES = (
    "EN",
    "IN_EN",
    "HI_LATIN_PII",
    "HI_DEVA_PII",
    "ROM_HI",
    "HINGLISH",
    "INFORMAL_HINGLISH",
)

TRANSLITERABLE_TYPES = ("PERSON", "ADDRESS")
NON_TRANSLITERABLE_TYPES = (
    "PHONE",
    "EMAIL",
    "PAN",
    "AADHAAR",
    "UPI_ID",
    "BANK_ACCOUNT",
)

# --- ROM_HI carrier templates (guidelines.md Section 4.10/4.13) ------------
CARRIER_TEMPLATE_ROM_HI = {
    "PERSON": "mera naam {value} hai.",
    "ADDRESS": "mera address {value} hai.",
    "PHONE": "mera mobile number {value} hai.",
    "EMAIL": "mera email {value} hai.",
    "PAN": "mera PAN number {value} hai.",
    "AADHAAR": "mera Aadhaar number {value} hai.",
    "BANK_ACCOUNT": "mera bank account number {value} hai.",
    "UPI_ID": "mera UPI ID {value} hai.",
}

# --- Devanagari carrier templates, shared by HI_LATIN_PII and HI_DEVA_PII
# (guidelines.md Section 4.11: matched-variant invariant -- same template,
# only {value}'s script differs) --------------------------------------------
CARRIER_TEMPLATE_DEVANAGARI = {
    "PERSON": "मेरा नाम {value} है।",
    "ADDRESS": "मेरा एड्रेस {value} है।",
    "PHONE": "मेरा मोबाइल नंबर {value} है।",
    "EMAIL": "मेरा ईमेल {value} है।",
    "PAN": "मेरा PAN नंबर {value} है।",
    "AADHAAR": "मेरा आधार नंबर {value} है।",
    "BANK_ACCOUNT": "मेरा बैंक अकाउंट नंबर {value} है।",
    "UPI_ID": "मेरा UPI ID {value} है।",
}

# --- IN_EN: frozen 8-item Indian-English marker inventory (guidelines.md
# Section 4.12). Each entry is (marker_name, wrap_function). wrap_function
# takes the canonical_text (already containing the PII) and returns the
# IN_EN realization -- always a fixed prepend/append, never touching the
# PII substring itself. -------------------------------------------------
def _wrap_kindly(sentence: str) -> str:
    return f"Kindly note: {sentence}"


def _wrap_do_the_needful(sentence: str) -> str:
    return f"{sentence} Kindly do the needful."


def _wrap_revert(sentence: str) -> str:
    return f"{sentence} Please revert with confirmation."


def _wrap_prepone(sentence: str) -> str:
    return f"{sentence} Kindly prepone action if required."


def _wrap_please_find_below(sentence: str) -> str:
    return f"Please find the details below: {sentence}"


def _wrap_intimate(sentence: str) -> str:
    return f"{sentence} Please intimate any discrepancy."


def _wrap_the_same(sentence: str) -> str:
    return f"{sentence} Kindly confirm the same."


def _wrap_at_the_earliest(sentence: str) -> str:
    return f"{sentence} Please process at the earliest."


IN_EN_MARKERS = (
    ("kindly", _wrap_kindly),
    ("do the needful", _wrap_do_the_needful),
    ("revert", _wrap_revert),
    ("prepone", _wrap_prepone),
    ("please find below/attached", _wrap_please_find_below),
    ("intimate", _wrap_intimate),
    ("the same", _wrap_the_same),
    ("at the earliest", _wrap_at_the_earliest),
)

# --- HINGLISH: frozen insertion inventory (guidelines.md Section 4.13).
# Two deterministic construction patterns, each using only frozen-inventory
# words. Chosen deterministically by caller (base index parity), never
# randomly. --------------------------------------------------------------
HINGLISH_INSERTION_WORDS = (
    "please",
    "sir",
    "ma'am",
    "confirm",
    "actually",
    "check",
    "sorry",
    "thanks",
    "thank you",
    "okay",
    "ok",
    "problem",
    "update",
)


def _hinglish_prefix_pattern(rom_hi_sentence: str) -> str:
    """Uses 'sir' -- frozen HINGLISH insertion word."""
    return f"Sir, {rom_hi_sentence}"


def _hinglish_suffix_pattern(rom_hi_sentence: str) -> str:
    """Uses 'please' and 'confirm' -- frozen HINGLISH insertion words."""
    stem = rom_hi_sentence.rstrip(".")
    return f"{stem}, please confirm."


HINGLISH_PATTERNS = (_hinglish_prefix_pattern, _hinglish_suffix_pattern)

# --- INFORMAL_HINGLISH: frozen marker categories (guidelines.md Section 4.14) --
INFORMAL_ABBREVIATIONS = ("u", "ur", "pls", "plz", "thx", "msg")
INFORMAL_CASUAL_PARTICLES = ("yaar", "bro", "na", "toh", "arre")
INFORMAL_COPULA_CONTRACTIONS = {"hai": "h", "hoon": "hu"}
