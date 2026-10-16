"""Synthetic test examples for BharatPII inference and redaction demo.

Provides diverse, realistic synthetic examples across:
- All 8 supported Indian PII categories:
  PERSON, PAN, AADHAAR, PHONE, EMAIL, UPI_ID, BANK_ACCOUNT, ADDRESS
- 7 linguistic and script variants:
  EN, IN_EN, HI_LATIN_PII, HI_DEVA_PII, ROM_HI, HINGLISH, INFORMAL_HINGLISH
- Multi-entity compound records
- Non-PII hard-negative decoys (order IDs, tracking codes, reference numbers)
"""

from __future__ import annotations

from typing import Any

SYNTHETIC_EXAMPLES: list[dict[str, Any]] = [
    # -------------------------------------------------------------------------
    # 1. PERSON
    # -------------------------------------------------------------------------
    {
        "id": "SYN_PERSON_EN_01",
        "category": "PERSON",
        "language": "EN",
        "description": "Indian English formal name statement",
        "text": "My name is Sneha Sharma.",
        "expected_labels": ["PERSON"],
    },
    {
        "id": "SYN_PERSON_HI_DEVA_01",
        "category": "PERSON",
        "language": "HI_DEVA_PII",
        "description": "Devanagari script Hindi name statement",
        "text": "मेरा नाम अंजलि नायर है।",
        "expected_labels": ["PERSON"],
    },
    {
        "id": "SYN_PERSON_HINGLISH_01",
        "category": "PERSON",
        "language": "HINGLISH",
        "description": "Code-mixed Hinglish personal name statement",
        "text": "mera naam Divya Rao hai, please confirm.",
        "expected_labels": ["PERSON"],
    },
    {
        "id": "SYN_PERSON_HI_LATIN_01",
        "category": "PERSON",
        "language": "HI_LATIN_PII",
        "description": "Devanagari Hindi sentence with Latin script name",
        "text": "मेरा नाम Divya Iyer है।",
        "expected_labels": ["PERSON"],
    },
    # -------------------------------------------------------------------------
    # 2. PAN (Permanent Account Number)
    # -------------------------------------------------------------------------
    {
        "id": "SYN_PAN_EN_01",
        "category": "PAN",
        "language": "EN",
        "description": "10-character alphanumeric PAN in English context",
        "text": "My PAN number is FZZFN0256Z.",
        "expected_labels": ["PAN"],
    },
    {
        "id": "SYN_PAN_ROM_HI_01",
        "category": "PAN",
        "language": "ROM_HI",
        "description": "PAN in Romanized Hindi sentence",
        "text": "mera PAN number FZWDM0733O hai.",
        "expected_labels": ["PAN"],
    },
    {
        "id": "SYN_PAN_INFORMAL_01",
        "category": "PAN",
        "language": "INFORMAL_HINGLISH",
        "description": "PAN in informal conversational Hinglish",
        "text": "sir, mera pan number BDTNL5698D h na",
        "expected_labels": ["PAN"],
    },
    # -------------------------------------------------------------------------
    # 3. AADHAAR (12-digit Indian national identity number)
    # -------------------------------------------------------------------------
    {
        "id": "SYN_AADHAAR_EN_01",
        "category": "AADHAAR",
        "language": "EN",
        "description": "12-digit Aadhaar number in English statement",
        "text": "My Aadhaar number is 670656272980.",
        "expected_labels": ["AADHAAR"],
    },
    {
        "id": "SYN_AADHAAR_ROM_HI_01",
        "category": "AADHAAR",
        "language": "ROM_HI",
        "description": "12-digit Aadhaar number in Romanized Hindi",
        "text": "mera Aadhaar number 033092327193 hai.",
        "expected_labels": ["AADHAAR"],
    },
    # -------------------------------------------------------------------------
    # 4. PHONE (10-digit mobile number)
    # -------------------------------------------------------------------------
    {
        "id": "SYN_PHONE_EN_01",
        "category": "PHONE",
        "language": "EN",
        "description": "10-digit mobile phone number in English",
        "text": "My phone number is 9876543210.",
        "expected_labels": ["PHONE"],
    },
    {
        "id": "SYN_PHONE_ROM_HI_01",
        "category": "PHONE",
        "language": "ROM_HI",
        "description": "Mobile number in Romanized Hindi",
        "text": "mera mobile number 9247317810 hai.",
        "expected_labels": ["PHONE"],
    },
    # -------------------------------------------------------------------------
    # 5. EMAIL (Email address)
    # -------------------------------------------------------------------------
    {
        "id": "SYN_EMAIL_EN_01",
        "category": "EMAIL",
        "language": "EN",
        "description": "Email address in English context",
        "text": "Email me at sneha8298@webmail.test.",
        "expected_labels": ["EMAIL"],
    },
    {
        "id": "SYN_EMAIL_ROM_HI_01",
        "category": "EMAIL",
        "language": "ROM_HI",
        "description": "Email address in Romanized Hindi",
        "text": "mera email priya2210@webmail.test hai.",
        "expected_labels": ["EMAIL"],
    },
    # -------------------------------------------------------------------------
    # 6. UPI_ID (Unified Payments Interface VPA)
    # -------------------------------------------------------------------------
    {
        "id": "SYN_UPI_ID_EN_01",
        "category": "UPI_ID",
        "language": "EN",
        "description": "UPI VPA in English sentence",
        "text": "My UPI ID is 9837770143@mail.test.",
        "expected_labels": ["UPI_ID"],
    },
    {
        "id": "SYN_UPI_ID_ROM_HI_01",
        "category": "UPI_ID",
        "language": "ROM_HI",
        "description": "UPI VPA in Romanized Hindi",
        "text": "mera UPI ID 9498941343@mail.test hai.",
        "expected_labels": ["UPI_ID"],
    },
    # -------------------------------------------------------------------------
    # 7. BANK_ACCOUNT (Indian commercial bank account number)
    # -------------------------------------------------------------------------
    {
        "id": "SYN_BANK_ACCOUNT_EN_01",
        "category": "BANK_ACCOUNT",
        "language": "EN",
        "description": "Bank account number in English statement",
        "text": "My bank account number is 324210249947.",
        "expected_labels": ["BANK_ACCOUNT"],
    },
    {
        "id": "SYN_BANK_ACCOUNT_ROM_HI_01",
        "category": "BANK_ACCOUNT",
        "language": "ROM_HI",
        "description": "Bank account number in Romanized Hindi",
        "text": "mera bank account number 013990490278 hai.",
        "expected_labels": ["BANK_ACCOUNT"],
    },
    # -------------------------------------------------------------------------
    # 8. ADDRESS (Physical street, locality, city, PIN code)
    # -------------------------------------------------------------------------
    {
        "id": "SYN_ADDRESS_EN_01",
        "category": "ADDRESS",
        "language": "EN",
        "description": "Complete Indian residential address in English",
        "text": "My address is Flat 230, Silver Oak Heights, Baner Road, Bengaluru 754235.",
        "expected_labels": ["ADDRESS"],
    },
    {
        "id": "SYN_ADDRESS_HI_DEVA_01",
        "category": "ADDRESS",
        "language": "HI_DEVA_PII",
        "description": "Devanagari script residential address in Mumbai",
        "text": "मेरा एड्रेस फ्लैट 166, ऑर्किड होम्स, बानेर रोड, मुंबई 643039 है।",
        "expected_labels": ["ADDRESS"],
    },
    # -------------------------------------------------------------------------
    # 9. COMPOUND MULTI-ENTITY SAMPLES
    # -------------------------------------------------------------------------
    {
        "id": "SYN_MULTI_EN_01",
        "category": "MULTI",
        "language": "EN",
        "description": "English business message containing PERSON, PHONE, and PAN",
        "text": "Call Rahul Sharma at 9876543210 regarding PAN ABCDE1234F.",
        "expected_labels": ["PERSON", "PHONE", "PAN"],
    },
    {
        "id": "SYN_MULTI_HI_DEVA_01",
        "category": "MULTI",
        "language": "HI_DEVA_PII",
        "description": "Devanagari Hindi sentence containing PERSON and EMAIL",
        "text": "मेरा नाम राहुल शर्मा है और मेरा ईमेल sneha8298@webmail.test है।",
        "expected_labels": ["PERSON", "EMAIL"],
    },
    {
        "id": "SYN_MULTI_HINGLISH_01",
        "category": "MULTI",
        "language": "HINGLISH",
        "description": "Hinglish notification with PHONE and UPI_ID",
        "text": "Mera phone 9876543210 hai aur UPI ID 9498941343@mail.test hai.",
        "expected_labels": ["PHONE", "UPI_ID"],
    },
    # -------------------------------------------------------------------------
    # 10. NON-PII HARD-NEGATIVE DECOYS (Demonstrates safety on non-PII strings)
    # -------------------------------------------------------------------------
    {
        "id": "SYN_DECOY_NON_PII_01",
        "category": "NON_PII",
        "language": "EN",
        "description": "Invoice number that is not a PAN or bank account",
        "text": "Order confirmation received for invoice INV-2026-9901 with tracking number TRK882.",
        "expected_labels": [],
    },
]


def get_examples_by_category(category: str) -> list[dict[str, Any]]:
    """Filter synthetic examples by PII category (e.g. 'PERSON', 'PAN', etc.)."""
    cat_upper = category.upper()
    return [e for e in SYNTHETIC_EXAMPLES if e["category"] == cat_upper]


def get_all_categories() -> list[str]:
    """Return all unique categories represented in the synthetic catalog."""
    seen = set()
    cats = []
    for e in SYNTHETIC_EXAMPLES:
        c = e["category"]
        if c not in seen:
            seen.add(c)
            cats.append(c)
    return cats
