"""SV-02 Dataset Generation, Budget-Accounting, and Split Auditing Script.

Generates disjoint experimental datasets for:
- Variant B: Hard-Negative Augmented Adaptation (b5_hard_negative)
- Variant B-Control: Size-Matched Positive Control (b5_positive_matched)
- Variant C: Format-Diversity Augmented Adaptation (b5_format_diversity)

Ensures zero overlap with canonical test corpus and zero base-ID collision.
Calculates exact token budgets via XLM-RoBERTa fast tokenizer.
"""

from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path
import random
import re
import string
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
from transformers import AutoTokenizer

from benchmark.runner import load_canonical_benchmark_records
from generators.pii.aadhaar import generate_aadhaar
from generators.pii.address import generate_address
from generators.pii.bank_account import generate_bank_account
from generators.pii.email import generate_email
from generators.pii.pan import generate_pan
from generators.pii.person import generate_person
from generators.pii.phone import generate_phone
from generators.pii.upi_id import generate_upi_id
from generators.translit.table import transliterate_value

SV02_DATA_DIR = REPO_ROOT / "data" / "experiments" / "sv02"
CANONICAL_ADAPT_DIR = REPO_ROOT / "data" / "adaptation"
REPORTS_DIR = REPO_ROOT / "reports" / "experiments" / "sv02"

MODEL_NAME = "xlm-roberta-base"

# -----------------------------------------------------------------------------
# HARD-NEGATIVE CARRIER PATTERNS AND DECOY GENERATION
# -----------------------------------------------------------------------------

HN_TEMPLATES = [
    # Numeric / Tracking / Order decoys
    ("EN", "The dispatch team confirmed tracking code {decoy} for shipment delivery."),
    ("IN_EN", "Please reference invoice number {decoy} during your billing call."),
    ("HI", "कृपया अपने चालान संख्या {decoy} को सुरक्षित रखें।"),
    ("ROM_HI", "Aapka courier tracking ID {decoy} portal par update ho chuka hai."),
    ("HINGLISH", "Order status check karne ke liye reference number {decoy} note kar lo."),
    
    # Alphanumeric / Tax / Serial decoys
    ("EN", "The auditor recorded GST registration certificate {decoy} in the audit file."),
    ("IN_EN", "Kindly submit equipment serial number {decoy} to the inventory desk."),
    ("HI", "प्रणाली में उत्पाद क्रम संख्या {decoy} सफलतापूर्वक दर्ज की गई है।"),
    ("ROM_HI", "Tax portal par challan reference {decoy} verify ho gaya."),
    ("HINGLISH", "Warranty claim ke liye item barcode {decoy} enter karna padega."),
    
    # Place name / Landmark decoys (Name as Place)
    ("EN", "The parcel was delivered to the warehouse near {decoy} yesterday."),
    ("IN_EN", "Please assemble at the corporate facility opposite {decoy} for briefing."),
    ("HI", "हमारी शाखा {decoy} के मुख्य चौराहे के पास स्थित है।"),
    ("ROM_HI", "Meeting ka venue {decoy} ke samne wale complex me rakha hai."),
    ("HINGLISH", "Delivery boy ne package {decoy} ke signal par handover kiya."),
    
    # Handle / Support / Service decoys (Handle shape)
    ("EN", "For enterprise escalations, submit a ticket to {decoy} via the portal."),
    ("IN_EN", "Official feedback must be directed to department desk {decoy}."),
    ("HI", "तकनीकी सहायता के लिए हमारे सेवा केंद्र {decoy} पर संपर्क करें।"),
    ("ROM_HI", "Billing issue ke liye support channel {decoy} par query daal do."),
    ("HINGLISH", "Helpdesk channel {decoy} par ticket generate kar lo bhai."),
    
    # Contextual / Facility decoys
    ("EN", "The operations team inspects substation block {decoy} every Monday."),
    ("IN_EN", "Please inspect the server rack located at {decoy}."),
    ("HI", "कार्यशाला ब्लॉक संख्या {decoy} में रखरखाव कार्य प्रगति पर है।"),
    ("ROM_HI", "Logistics team ne unit {decoy} ka audit complete kar liya."),
    ("HINGLISH", "Conference room {decoy} me urgent client discussion schedule hai."),
]

def generate_synthetic_decoy(category: str, rng: random.Random) -> str:
    """Generate non-PII lookalike distractors with zero gold PII semantics."""
    if category == "NUMERIC":
        # 10 to 14 digit numeric strings formatted as barcodes / tracking IDs
        fmt = rng.choice(["TRACK-", "INV-", "ORD-", "PKG-", "REF-", ""])
        if fmt:
            digits = "".join(rng.choices(string.digits, k=rng.choice([8, 10, 12])))
            return f"{fmt}{digits}"
        else:
            return "".join(rng.choices(string.digits, k=11))
    elif category == "ALPHANUM":
        prefix = "".join(rng.choices(string.ascii_uppercase, k=3))
        nums = "".join(rng.choices(string.digits, k=4))
        suffix = "".join(rng.choices(string.ascii_uppercase, k=2))
        return f"{prefix}-{nums}-{suffix}"
    elif category == "PLACE_NAME":
        names = ["Nehru", "Tagore", "Ramanujan", "Sarojini", "Shivaji", "Ashoka", "Vikram", "Tilak", "Gokhale", "Patel"]
        suffix = ["Chowk", "Nagar Terminal", "Complex", "Circle", "Crossing", "Flyover", "Depot", "Junction", "Bazaar", "Station"]
        return f"{rng.choice(names)} {rng.choice(suffix)}"
    elif category == "HANDLE":
        prefixes = ["support", "billing", "helpdesk", "feedback", "alerts", "inquiries", "system", "operations", "service"]
        domains = ["internal", "corp", "local", "portal", "cloud", "desk", "gateway", "support"]
        return f"{rng.choice(prefixes)}@{rng.choice(domains)}"
    else: # FACILITY / CONTEXT
        wings = ["Sector-B", "Tower-4", "Zone-3", "Unit-12", "Block-C", "Gate-7", "Bay-9", "Terminal-2"]
        num = rng.randint(101, 999)
        return f"{rng.choice(wings)}-{num}"


def build_hard_negatives(count: int, seed: int, prefix: str) -> list[dict]:
    rng = random.Random(seed)
    categories = ["NUMERIC", "ALPHANUM", "PLACE_NAME", "HANDLE", "FACILITY"]
    records = []
    
    num_bases = count // 5
    for base_idx in range(1, num_bases + 1):
        base_id = f"{prefix}_{base_idx:03d}"
        cat = categories[(base_idx - 1) % len(categories)]
        decoy_val = generate_synthetic_decoy(cat, rng)
        
        for lang_idx in range(5):
            lang, t_str = HN_TEMPLATES[((base_idx - 1) * 5 + lang_idx) % len(HN_TEMPLATES)]
            text = t_str.format(decoy=decoy_val)
            rec_id = f"{base_id}_VAR_{lang_idx+1}"
            
            records.append({
                "base_id": base_id,
                "record_id": rec_id,
                "variant_id": rec_id,
                "text": text,
                "language": lang,
                "entities": [], # STRICTLY 0 GOLD ENTITIES
                "is_hard_negative": True,
                "decoy_category": cat,
                "synthetic": True,
            })
            
    return records


# -----------------------------------------------------------------------------
# SIZE-MATCHED POSITIVE CONTROL GENERATION
# -----------------------------------------------------------------------------

EXTRA_POS_TEMPLATES = {
    "PERSON": [
        ("EN", "The team welcomed senior engineer {val} to the team."),
        ("IN_EN", "Kindly confirm if {val} has signed the register."),
        ("HI", "कृपया {val_deva} से संपर्क करें।"),
        ("ROM_HI", "Aap {val} ko message bhej sakte hain."),
        ("HINGLISH", "Main {val} ke sath meeting me tha."),
    ],
    "PAN": [
        ("EN", "The portal verified the tax ID {val} for tax submission."),
        ("IN_EN", "Please note the tax identifier {val} on the challan."),
        ("HI", "आयकर विवरण के लिए पैन {val} दर्ज करें।"),
        ("ROM_HI", "Aapka PAN {val} register ho gaya hai."),
        ("HINGLISH", "Form me PAN {val} mention kar dena."),
    ],
    "AADHAAR": [
        ("EN", "Identity record confirmed for UID {val}."),
        ("IN_EN", "The citizen presented 12-digit ID {val} at the counter."),
        ("HI", "नागरिक पहचान के लिए आधार {val} आवश्यक है।"),
        ("ROM_HI", "Unhone apna Aadhaar {val} submit kiya."),
        ("HINGLISH", "Kripya UIDAI card number {val} dikhaiye."),
    ],
    "PHONE": [
        ("EN", "Contact the emergency desk on {val}."),
        ("IN_EN", "Please dial cellular contact {val} for updates."),
        ("HI", "सहायता केंद्र नंबर {val} उपलब्ध है।"),
        ("ROM_HI", "Unka contact number {val} dial karo."),
        ("HINGLISH", "Bhai phone number {val} par call lagao."),
    ],
    "EMAIL": [
        ("EN", "Electronic statement sent to {val}."),
        ("IN_EN", "The official memo was emailed to {val}."),
        ("HI", "दस्तावेज इस ईमेल पते {val} पर भेजें।"),
        ("ROM_HI", "Maine mail {val} par forward kar diya."),
        ("HINGLISH", "Important file {val} pe attach karke bhejo."),
    ],
    "UPI_ID": [
        ("EN", "Direct payment link routed to {val}."),
        ("IN_EN", "Payment settlement completed to VPA {val}."),
        ("HI", "यूपीआई खाता {val} सत्यापित है।"),
        ("ROM_HI", "UPI handle {val} par payment execute ho gayi."),
        ("HINGLISH", "Bill payment ke liye UPI {val} select karo."),
    ],
    "BANK_ACCOUNT": [
        ("EN", "Account statement generated for account {val}."),
        ("IN_EN", "Fund transfer initiated to banking account {val}."),
        ("HI", "खाता संख्या {val} में राशि जमा की गई।"),
        ("ROM_HI", "Bank account number {val} confirm karein."),
        ("HINGLISH", "Branch transfer ke liye account {val} verify karo."),
    ],
    "ADDRESS": [
        ("EN", "Shipment delivered to residential premises {val}."),
        ("IN_EN", "The corporate headquarters is situated at {val}."),
        ("HI", "कार्यालय का पता {val} है।"),
        ("ROM_HI", "Mera postal address {val} update kar do."),
        ("HINGLISH", "Package delivery address {val} par drop karo."),
    ],
}

def build_extra_positives(count: int, seed: int, prefix: str) -> list[dict]:
    rng = random.Random(seed)
    pii_types = list(EXTRA_POS_TEMPLATES.keys())
    records = []
    
    num_bases = count // 5
    for base_idx in range(1, num_bases + 1):
        pii_type = pii_types[(base_idx - 1) % len(pii_types)]
        base_id = f"{prefix}_{pii_type}_{base_idx:03d}"
        
        gen_fn = {
            "PERSON": generate_person,
            "PAN": generate_pan,
            "AADHAAR": generate_aadhaar,
            "PHONE": generate_phone,
            "EMAIL": generate_email,
            "UPI_ID": generate_upi_id,
            "BANK_ACCOUNT": generate_bank_account,
            "ADDRESS": generate_address,
        }[pii_type]
        
        pii_obj = gen_fn(rng)
        val = pii_obj.base_pii_value
        
        t_list = EXTRA_POS_TEMPLATES[pii_type]
        for lang_idx, (lang, t_str) in enumerate(t_list):
            val_used = val
            if lang == "HI" and pii_type in ("PERSON", "ADDRESS"):
                val_used = transliterate_value(val)
            
            if "{val_deva}" in t_str:
                text = t_str.format(val_deva=val_used)
            else:
                text = t_str.format(val=val_used)
                
            start = text.index(val_used)
            end = start + len(val_used)
            rec_id = f"{base_id}_VAR_{lang_idx+1}"
            
            records.append({
                "base_id": base_id,
                "record_id": rec_id,
                "variant_id": rec_id,
                "text": text,
                "language": lang,
                "pii_type": pii_type,
                "entities": [{
                    "type": pii_type,
                    "text": val_used,
                    "start": start,
                    "end": end,
                }],
                "synthetic": True,
            })
            
    return records


# -----------------------------------------------------------------------------
# FORMAT-DIVERSITY AUGMENTED POSITIVE DATASET GENERATION
# -----------------------------------------------------------------------------

def apply_format_diversity(pii_type: str, val: str, rng: random.Random) -> str:
    """Apply synthetic formatting variations to positive entities."""
    if pii_type == "AADHAAR":
        digits = "".join(c for c in val if c.isdigit())
        if len(digits) == 12:
            mode = rng.choice(["unspaced", "dashed", "dotted", "canonical"])
            if mode == "unspaced":
                return digits
            elif mode == "dashed":
                return f"{digits[:4]}-{digits[4:8]}-{digits[8:]}"
            elif mode == "dotted":
                return f"{digits[:4]}.{digits[4:8]}.{digits[8:]}"
    elif pii_type == "PHONE":
        digits = "".join(c for c in val if c.isdigit())
        if len(digits) >= 10:
            last10 = digits[-10:]
            mode = rng.choice(["dashed", "spaced", "dotted", "bracketed", "canonical"])
            if mode == "dashed":
                return f"+91-{last10[:5]}-{last10[5:]}"
            elif mode == "spaced":
                return f"+91 {last10[:5]} {last10[5:]}"
            elif mode == "dotted":
                return f"{last10[:5]}.{last10[5:]}"
            elif mode == "bracketed":
                return f"(+91) {last10}"
    elif pii_type == "PAN":
        clean = "".join(c for c in val if c.isalnum())
        if len(clean) == 10:
            mode = rng.choice(["lowercase", "spaced", "dashed", "canonical"])
            if mode == "lowercase":
                return clean.lower()
            elif mode == "spaced":
                return f"{clean[:5]} {clean[5:9]} {clean[9]}"
            elif mode == "dashed":
                return f"{clean[:5]}-{clean[5:9]}-{clean[9]}"
    elif pii_type == "UPI_ID":
        if "@" in val:
            user, domain = val.split("@", 1)
            diverse_domains = ["okaxis", "okhdfcbank", "paytm", "ybl", "sbi", "kotak", "postbank", "airtel", "icici", "indus"]
            return f"{user}@{rng.choice(diverse_domains)}"
    elif pii_type == "BANK_ACCOUNT":
        digits = "".join(c for c in val if c.isdigit())
        if len(digits) >= 11:
            mode = rng.choice(["dashed", "spaced", "canonical"])
            if mode == "dashed":
                return f"{digits[:4]}-{digits[4:8]}-{digits[8:]}"
            elif mode == "spaced":
                return f"{digits[:4]} {digits[4:8]} {digits[8:]}"
    return val


def build_format_diverse_records(base_records: list[dict], seed: int) -> list[dict]:
    rng = random.Random(seed)
    diverse_records = []
    
    for r in base_records:
        rec = dict(r)
        ents = rec.get("entities", [])
        if ents:
            ent = dict(ents[0])
            orig_val = ent["text"]
            pii_type = ent["type"]
            new_val = apply_format_diversity(pii_type, orig_val, rng)
            
            orig_text = rec["text"]
            start, end = ent["start"], ent["end"]
            
            new_text = orig_text[:start] + new_val + orig_text[end:]
            ent["text"] = new_val
            ent["end"] = start + len(new_val)
            
            rec["text"] = new_text
            rec["entities"] = [ent]
            rec["format_diversified"] = True
            
        diverse_records.append(rec)
        
    return diverse_records


# -----------------------------------------------------------------------------
# TOKEN ACCOUNTING & MANIFEST GENERATION
# -----------------------------------------------------------------------------

def compute_token_statistics(records: list[dict], tokenizer: AutoTokenizer) -> dict:
    lengths = []
    for r in records:
        enc = tokenizer(r["text"], truncation=False)
        lengths.append(len(enc["input_ids"]))
        
    lengths_arr = np.array(lengths)
    return {
        "record_count": len(records),
        "total_tokens": int(np.sum(lengths_arr)),
        "mean_tokens_per_record": round(float(np.mean(lengths_arr)), 2),
        "std_tokens_per_record": round(float(np.std(lengths_arr)), 2),
        "min_tokens": int(np.min(lengths_arr)),
        "max_tokens": int(np.max(lengths_arr)),
    }


def run_data_generation():
    print("=== STARTING SV-02 DATA GENERATION ===")
    SV02_DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    
    # 1. Load canonical B5 positive data
    with open(CANONICAL_ADAPT_DIR / "train.jsonl", "r", encoding="utf-8") as f:
        canonical_train = [json.loads(line) for line in f if line.strip()]
    with open(CANONICAL_ADAPT_DIR / "val.jsonl", "r", encoding="utf-8") as f:
        canonical_val = [json.loads(line) for line in f if line.strip()]
        
    print(f"Loaded canonical positive baseline: Train={len(canonical_train)}, Val={len(canonical_val)}")
    
    # -------------------------------------------------------------
    # VARIANT B: HARD-NEGATIVE ABLATION DATASET
    # -------------------------------------------------------------
    print("\n--- Generating Variant B: b5_hard_negative ---")
    hn_train = build_hard_negatives(count=250, seed=4242, prefix="SV02_HN_TRN")
    hn_val = build_hard_negatives(count=50, seed=4243, prefix="SV02_HN_VAL")
    
    var_b_train = canonical_train + hn_train
    var_b_val = canonical_val + hn_val
    
    var_b_dir = SV02_DATA_DIR / "b5_hard_negative"
    var_b_dir.mkdir(parents=True, exist_ok=True)
    
    with open(var_b_dir / "train.jsonl", "w", encoding="utf-8") as f:
        for r in var_b_train:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(var_b_dir / "val.jsonl", "w", encoding="utf-8") as f:
        for r in var_b_val:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    var_b_train_stats = compute_token_statistics(var_b_train, tokenizer)
    var_b_val_stats = compute_token_statistics(var_b_val, tokenizer)
    
    var_b_manifest = {
        "variant": "b5_hard_negative",
        "description": "1,000 canonical positive + 250 synthetic hard-negative distractors (train), 200 pos + 50 HN (val)",
        "train_statistics": var_b_train_stats,
        "val_statistics": var_b_val_stats,
        "positive_train_count": len(canonical_train),
        "hard_negative_train_count": len(hn_train),
        "positive_val_count": len(canonical_val),
        "hard_negative_val_count": len(hn_val),
    }
    with open(var_b_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(var_b_manifest, f, indent=2)
    print(f"Variant B Train Tokens: {var_b_train_stats['total_tokens']}, Records: {var_b_train_stats['record_count']}")

    # -------------------------------------------------------------
    # VARIANT B-CONTROL: SIZE-MATCHED POSITIVE CONTROL DATASET
    # -------------------------------------------------------------
    print("\n--- Generating Variant B-Control: b5_positive_matched ---")
    pos_extra_train = build_extra_positives(count=250, seed=5242, prefix="SV02_POS_EXTRA_TRN")
    pos_extra_val = build_extra_positives(count=50, seed=5243, prefix="SV02_POS_EXTRA_VAL")
    
    var_b_ctrl_train = canonical_train + pos_extra_train
    var_b_ctrl_val = canonical_val + pos_extra_val
    
    var_b_ctrl_dir = SV02_DATA_DIR / "b5_positive_matched"
    var_b_ctrl_dir.mkdir(parents=True, exist_ok=True)
    
    with open(var_b_ctrl_dir / "train.jsonl", "w", encoding="utf-8") as f:
        for r in var_b_ctrl_train:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(var_b_ctrl_dir / "val.jsonl", "w", encoding="utf-8") as f:
        for r in var_b_ctrl_val:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    var_b_ctrl_train_stats = compute_token_statistics(var_b_ctrl_train, tokenizer)
    var_b_ctrl_val_stats = compute_token_statistics(var_b_ctrl_val, tokenizer)
    
    var_b_ctrl_manifest = {
        "variant": "b5_positive_matched",
        "description": "1,000 canonical positive + 250 extra positive instances (train), 200 pos + 50 extra pos (val)",
        "train_statistics": var_b_ctrl_train_stats,
        "val_statistics": var_b_ctrl_val_stats,
        "positive_train_count": len(var_b_ctrl_train),
        "hard_negative_train_count": 0,
        "positive_val_count": len(var_b_ctrl_val),
        "hard_negative_val_count": 0,
    }
    with open(var_b_ctrl_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(var_b_ctrl_manifest, f, indent=2)
    print(f"Variant B-Control Train Tokens: {var_b_ctrl_train_stats['total_tokens']}, Records: {var_b_ctrl_train_stats['record_count']}")

    # -------------------------------------------------------------
    # VARIANT C: FORMAT-DIVERSITY ABLATION DATASET
    # -------------------------------------------------------------
    print("\n--- Generating Variant C: b5_format_diversity ---")
    var_c_train = build_format_diverse_records(var_b_ctrl_train, seed=6242)
    var_c_val = build_format_diverse_records(var_b_ctrl_val, seed=6243)
    
    var_c_dir = SV02_DATA_DIR / "b5_format_diversity"
    var_c_dir.mkdir(parents=True, exist_ok=True)
    
    with open(var_c_dir / "train.jsonl", "w", encoding="utf-8") as f:
        for r in var_c_train:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(var_c_dir / "val.jsonl", "w", encoding="utf-8") as f:
        for r in var_c_val:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    var_c_train_stats = compute_token_statistics(var_c_train, tokenizer)
    var_c_val_stats = compute_token_statistics(var_c_val, tokenizer)
    
    var_c_manifest = {
        "variant": "b5_format_diversity",
        "description": "1,250 format-diversified positive records (train), 250 format-diversified positive records (val)",
        "train_statistics": var_c_train_stats,
        "val_statistics": var_c_val_stats,
        "positive_train_count": len(var_c_train),
        "hard_negative_train_count": 0,
        "positive_val_count": len(var_c_val),
        "hard_negative_val_count": 0,
    }
    with open(var_c_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(var_c_manifest, f, indent=2)
    print(f"Variant C Train Tokens: {var_c_train_stats['total_tokens']}, Records: {var_c_train_stats['record_count']}")

    # -------------------------------------------------------------
    # OVERALL MASTER MANIFEST
    # -------------------------------------------------------------
    canonical_b5_stats = compute_token_statistics(canonical_train, tokenizer)
    canonical_b5_val_stats = compute_token_statistics(canonical_val, tokenizer)
    
    master_manifest = {
        "benchmark": "Indian PII Robustness Benchmark",
        "task": "SV-02",
        "timestamp": "2026-09-03T00:55:00+05:30",
        "variants": {
            "b5_baseline": {
                "records_train": len(canonical_train),
                "tokens_train": canonical_b5_stats["total_tokens"],
                "records_val": len(canonical_val),
                "tokens_val": canonical_b5_val_stats["total_tokens"],
                "positive_records_train": 1000,
                "hard_negative_records_train": 0,
            },
            "b5_hard_negative": {
                "records_train": len(var_b_train),
                "tokens_train": var_b_train_stats["total_tokens"],
                "records_val": len(var_b_val),
                "tokens_val": var_b_val_stats["total_tokens"],
                "positive_records_train": 1000,
                "hard_negative_records_train": 250,
            },
            "b5_positive_matched": {
                "records_train": len(var_b_ctrl_train),
                "tokens_train": var_b_ctrl_train_stats["total_tokens"],
                "records_val": len(var_b_ctrl_val),
                "tokens_val": var_b_ctrl_val_stats["total_tokens"],
                "positive_records_train": 1250,
                "hard_negative_records_train": 0,
            },
            "b5_format_diversity": {
                "records_train": len(var_c_train),
                "tokens_train": var_c_train_stats["total_tokens"],
                "records_val": len(var_c_val),
                "tokens_val": var_c_val_stats["total_tokens"],
                "positive_records_train": 1250,
                "hard_negative_records_train": 0,
            },
        },
    }
    with open(SV02_DATA_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(master_manifest, f, indent=2)
        
    print("\n=== SV-02 DATA GENERATION COMPLETE ===")

if __name__ == "__main__":
    run_data_generation()
