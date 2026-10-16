"""Disjoint adaptation/training dataset generator for Baseline B5 (PROJECT_SPEC.md §§19-22, §28).

Governance:
1. All base IDs use the disjoint prefix 'ADAPT_TRN_' (training) and 'ADAPT_VAL_' (validation).
2. Base IDs in the test set (e.g. PERSON_001..012, PAN_001..013, HN_001..020, MULTI_001..020)
   can NEVER appear in adaptation/training data. Base-level overlap is strictly 0.
3. All entities are synthetic and benchmark-safe.
4. Spans use exact Python Unicode code-point offsets into the realization text.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random

from generators.pii.aadhaar import generate_aadhaar
from generators.pii.address import generate_address
from generators.pii.bank_account import generate_bank_account
from generators.pii.email import generate_email
from generators.pii.pan import generate_pan
from generators.pii.person import generate_person
from generators.pii.phone import generate_phone
from generators.pii.upi_id import generate_upi_id
from generators.translit.table import transliterate_value

REPO_ROOT = Path(__file__).resolve().parents[1]
ADAPT_DIR = REPO_ROOT / "data" / "adaptation"
TRAIN_PATH = ADAPT_DIR / "train.jsonl"
VAL_PATH = ADAPT_DIR / "val.jsonl"
MANIFEST_PATH = ADAPT_DIR / "manifest.json"

PII_TYPES = (
    "PERSON",
    "PAN",
    "AADHAAR",
    "PHONE",
    "EMAIL",
    "UPI_ID",
    "BANK_ACCOUNT",
    "ADDRESS",
)

PII_GENERATORS = {
    "PERSON": generate_person,
    "PAN": generate_pan,
    "AADHAAR": generate_aadhaar,
    "PHONE": generate_phone,
    "EMAIL": generate_email,
    "UPI_ID": generate_upi_id,
    "BANK_ACCOUNT": generate_bank_account,
    "ADDRESS": generate_address,
}

TEMPLATES = {
    "PERSON": [
        ("EN", "Yesterday, {val} visited our regional office for the meeting."),
        ("IN_EN", "Please contact {val} regarding the project updates."),
        ("HI", "कल {val_deva} ने हमारे कार्यालय का दौरा किया।"),
        ("ROM_HI", "Kal {val} ne office me meeting attend ki thi."),
        ("HINGLISH", "Arre {val} ko bolo ki documents submit kar de."),
    ],
    "PAN": [
        ("EN", "The tax authority recorded the PAN number {val} in the ledger."),
        ("IN_EN", "Kindly verify your PAN card details: {val}."),
        ("HI", "कृपया अपने पैन कार्ड संख्या {val} का सत्यापन करें।"),
        ("ROM_HI", "Mera PAN number {val} account ke sath link hai."),
        ("HINGLISH", "Bhai KYC ke liye apna PAN {val} forward karo."),
    ],
    "AADHAAR": [
        ("EN", "The official portal verified Aadhaar number {val} successfully."),
        ("IN_EN", "Please authenticate using your 12-digit Aadhaar {val}."),
        ("HI", "सत्यापन के लिए अपना आधार कार्ड नंबर {val} दर्ज करें।"),
        ("ROM_HI", "Aadhaar number {val} verify ho gaya hai."),
        ("HINGLISH", "OTP verify karne ke liye Aadhaar {val} enter karein."),
    ],
    "PHONE": [
        ("EN", "You can reach customer support at phone number {val}."),
        ("IN_EN", "Please call my mobile number {val} for further assistance."),
        ("HI", "कृपया सहायता के लिए फोन नंबर {val} पर संपर्क करें।"),
        ("ROM_HI", "Agar koi query ho toh phone number {val} pe call karna."),
        ("HINGLISH", "Helpdesk contact number {val} par ping kar lo."),
    ],
    "EMAIL": [
        ("EN", "Send all verification documents to email address {val}."),
        ("IN_EN", "Official invoice has been dispatched to {val}."),
        ("HI", "कृपया सभी दस्तावेज ईमेल पते {val} पर भेजें।"),
        ("ROM_HI", "Maine apna email {val} profile me update kiya hai."),
        ("HINGLISH", "Receipt ka copy {val} pe send kar do please."),
    ],
    "UPI_ID": [
        ("EN", "The payment was processed to UPI address {val}."),
        ("IN_EN", "Please complete the payment via VPA {val}."),
        ("HI", "भुगतान के लिए यूपीआई आईडी {val} का उपयोग करें।"),
        ("ROM_HI", "Payment confirm karne ke liye UPI ID {val} enter karein."),
        ("HINGLISH", "Paise transfer karne ke liye UPI ID {val} note kar lo."),
    ],
    "BANK_ACCOUNT": [
        ("EN", "The refund was credited to bank account {val}."),
        ("IN_EN", "Beneficiary account number {val} is registered."),
        ("HI", "राशि आपके बैंक खाता संख्या {val} में जमा कर दी गई है।"),
        ("ROM_HI", "Salary account number {val} me credit ho gayi hai."),
        ("HINGLISH", "NEFT transfer account number {val} me initiate kiya hai."),
    ],
    "ADDRESS": [
        ("EN", "The parcel was delivered to the premises at {val}."),
        ("IN_EN", "Shipment destination is set to {val}."),
        ("HI", "पार्सल का वितरण पता {val_deva} पर किया गया है।"),
        ("ROM_HI", "Delivery address {val} par package bhej diya gaya hai."),
        ("HINGLISH", "Courier packet {val} pe deliver hoga kal tak."),
    ],
}


def build_disjoint_adaptation_dataset(
    n_train_per_type: int = 25,
    n_val_per_type: int = 5,
    seed: int = 8842,
) -> tuple[list[dict], list[dict]]:
    """Build train and validation sets with zero overlap with test base instances."""
    rng = random.Random(seed)
    ADAPT_DIR.mkdir(parents=True, exist_ok=True)

    train_records = []
    val_records = []

    # Generate training records (25 bases per type * 8 types = 200 bases -> 1,000 records)
    for pii_type in PII_TYPES:
        gen_fn = PII_GENERATORS[pii_type]
        for idx in range(1, n_train_per_type + 1):
            base_id = f"ADAPT_TRN_{pii_type}_{idx:03d}"
            pii_obj = gen_fn(rng)
            val = pii_obj.base_pii_value
            val_deva = transliterate_value(val) if pii_type in ("PERSON", "ADDRESS") else val

            for t_idx, (lang, t_str) in enumerate(TEMPLATES[pii_type]):
                variant_id = f"{base_id}_V{t_idx+1}_{lang}"
                actual_val = val_deva if "{val_deva}" in t_str else val
                text = t_str.format(val=val, val_deva=val_deva)
                start = text.index(actual_val)
                end = start + len(actual_val)
                assert text[start:end] == actual_val

                train_records.append({
                    "base_id": base_id,
                    "variant_id": variant_id,
                    "split": "train",
                    "language": lang,
                    "pii_type": pii_type,
                    "text": text,
                    "entities": [
                        {
                            "type": pii_type,
                            "text": actual_val,
                            "start": start,
                            "end": end,
                        }
                    ],
                })

    # Generate validation records (5 bases per type * 8 types = 40 bases -> 200 records)
    for pii_type in PII_TYPES:
        gen_fn = PII_GENERATORS[pii_type]
        for idx in range(1, n_val_per_type + 1):
            base_id = f"ADAPT_VAL_{pii_type}_{idx:03d}"
            pii_obj = gen_fn(rng)
            val = pii_obj.base_pii_value
            val_deva = transliterate_value(val) if pii_type in ("PERSON", "ADDRESS") else val

            for t_idx, (lang, t_str) in enumerate(TEMPLATES[pii_type]):
                variant_id = f"{base_id}_V{t_idx+1}_{lang}"
                actual_val = val_deva if "{val_deva}" in t_str else val
                text = t_str.format(val=val, val_deva=val_deva)
                start = text.index(actual_val)
                end = start + len(actual_val)
                assert text[start:end] == actual_val

                val_records.append({
                    "base_id": base_id,
                    "variant_id": variant_id,
                    "split": "val",
                    "language": lang,
                    "pii_type": pii_type,
                    "text": text,
                    "entities": [
                        {
                            "type": pii_type,
                            "text": actual_val,
                            "start": start,
                            "end": end,
                        }
                    ],
                })

    # Save datasets
    with open(TRAIN_PATH, "w", encoding="utf-8") as f:
        for r in train_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(VAL_PATH, "w", encoding="utf-8") as f:
        for r in val_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Hashes and manifest
    with open(TRAIN_PATH, "rb") as f:
        train_md5 = hashlib.md5(f.read()).hexdigest()
    with open(VAL_PATH, "rb") as f:
        val_md5 = hashlib.md5(f.read()).hexdigest()

    manifest = {
        "generator_version": "0.1.0",
        "dataset_name": "b5_disjoint_indian_adaptation_pilot",
        "train_base_count": n_train_per_type * len(PII_TYPES),
        "train_record_count": len(train_records),
        "train_file": "train.jsonl",
        "train_md5": train_md5,
        "val_base_count": n_val_per_type * len(PII_TYPES),
        "val_record_count": len(val_records),
        "val_file": "val.jsonl",
        "val_md5": val_md5,
        "test_base_id_overlap": 0,
        "seed": seed,
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return train_records, val_records


def validate_zero_test_leakage() -> bool:
    """Assert zero overlap between adaptation bases and canonical benchmark test bases."""
    from benchmark.runner import load_canonical_benchmark_records

    test_records = load_canonical_benchmark_records()
    test_bases = set(r["base_id"] for r in test_records)

    with open(TRAIN_PATH, "r", encoding="utf-8") as f:
        train_bases = set(json.loads(line)["base_id"] for line in f if line.strip())

    with open(VAL_PATH, "r", encoding="utf-8") as f:
        val_bases = set(json.loads(line)["base_id"] for line in f if line.strip())

    train_test_overlap = train_bases.intersection(test_bases)
    val_test_overlap = val_bases.intersection(test_bases)
    train_val_overlap = train_bases.intersection(val_bases)

    assert len(train_test_overlap) == 0, f"Leakage! Train/Test base overlap: {train_test_overlap}"
    assert len(val_test_overlap) == 0, f"Leakage! Val/Test base overlap: {val_test_overlap}"
    assert len(train_val_overlap) == 0, f"Train/Val base overlap: {train_val_overlap}"

    return True


if __name__ == "__main__":
    trn, val = build_disjoint_adaptation_dataset()
    validate_zero_test_leakage()
    print(f"Successfully generated {len(trn)} train records and {len(val)} val records.")
    print("Leakage validation: ZERO overlap with test set verified.")
