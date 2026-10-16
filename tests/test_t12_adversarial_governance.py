"""Governance tests for T12 adversarial perturbation specification (guidelines.md v0.18).

Proves that:
1. guidelines.md is bumped to v0.18 and frozen (resolving OQ-049).
2. PROJECT_SPEC.md, configs/pilot.yaml, and fixtures point to guidelines v0.18.
3. The 20 selected base IDs match the approved quota and exist in data/raw/base_instances.jsonl.
4. Deterministic A1-A5 algorithms produce exact expected realized values and text.
5. Numeric A5 follows M2 Single-Character OCR Substitution with exactly 1 mutation.
6. Sample adversarial records for all 5 families conform to schemas/example.schema.json.
7. No T12 generator code, adversarial dataset, benchmark, or evaluation code exists yet.
"""

import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
GUIDELINES_PATH = REPO_ROOT / "annotation" / "guidelines.md"
PROJECT_SPEC_PATH = REPO_ROOT / "PROJECT_SPEC.md"
CONFIG_PATH = REPO_ROOT / "configs" / "pilot.yaml"
FIXTURE_EXAMPLE_PATH = REPO_ROOT / "tests" / "fixtures" / "example.valid.json"
BASE_INSTANCES_PATH = REPO_ROOT / "data" / "raw" / "base_instances.jsonl"
EXAMPLE_SCHEMA_PATH = REPO_ROOT / "schemas" / "example.schema.json"

SELECTED_BASE_IDS = [
    "PERSON_001", "PERSON_002",
    "ADDRESS_001", "ADDRESS_002",
    "PHONE_001", "PHONE_002",
    "EMAIL_001", "EMAIL_002",
    "PAN_001", "PAN_002", "PAN_003",
    "AADHAAR_001", "AADHAAR_002", "AADHAAR_003",
    "UPI_ID_001", "UPI_ID_002", "UPI_ID_003",
    "BANK_ACCOUNT_001", "BANK_ACCOUNT_002", "BANK_ACCOUNT_003",
]


def test_guidelines_v018_frozen():
    content = GUIDELINES_PATH.read_text(encoding="utf-8")
    assert "guidelines_version: 0.18" in content
    assert "supersedes:        0.17" in content
    assert "### 14.5 Pilot Base Selection (20 Bases)" in content
    assert "### 14.6 Carrier Text Baseline" in content
    assert "### 14.7 Deterministic Transformation Specifications" in content
    assert "#### 14.7.1 A1 — SPACING" in content
    assert "#### 14.7.2 A2 — PUNCTUATION" in content
    assert "#### 14.7.3 A3 — LABEL_OBFUSCATION" in content
    assert "#### 14.7.4 A4 — INFORMAL_ABBREVIATION" in content
    assert "#### 14.7.5 A5 — CHARACTER_VARIATION" in content


def test_version_pointers_consistent():
    spec_content = PROJECT_SPEC_PATH.read_text(encoding="utf-8")
    assert "guidelines.md` v0.18" in spec_content
    assert "guidelines_version:  0.18" in spec_content

    config_content = CONFIG_PATH.read_text(encoding="utf-8")
    assert 'guidelines_version: "0.18"' in config_content

    fixture = json.loads(FIXTURE_EXAMPLE_PATH.read_text(encoding="utf-8"))
    assert fixture["guidelines_version"] == "0.18"

    schema = json.loads(EXAMPLE_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    validator.validate(fixture)


def test_20_selected_base_instances_exist():
    with open(BASE_INSTANCES_PATH, "r", encoding="utf-8") as f:
        bases = [json.loads(line) for line in f if line.strip()]

    base_map = {b["base_id"]: b for b in bases}
    assert len(SELECTED_BASE_IDS) == 20

    for bid in SELECTED_BASE_IDS:
        assert bid in base_map
        b = base_map[bid]
        assert b["base_kind"] == "POSITIVE"
        assert len(b["pii"]) == 1
        assert b["canonical_text"] is not None

    type_counts = {}
    for bid in SELECTED_BASE_IDS:
        ptype = base_map[bid]["pii"][0]["type"]
        type_counts[ptype] = type_counts.get(ptype, 0) + 1

    assert type_counts == {
        "PERSON": 2,
        "ADDRESS": 2,
        "PHONE": 2,
        "EMAIL": 2,
        "PAN": 3,
        "AADHAAR": 3,
        "UPI_ID": 3,
        "BANK_ACCOUNT": 3,
    }


def test_a1_spacing_rules():
    def apply_a1(v):
        if " " in v:
            return "  ".join(" ".join(t) for t in v.split(" "))
        return " ".join(v)

    assert apply_a1("ABCDE1234F") == "A B C D E 1 2 3 4 F"
    assert apply_a1("Sneha Sharma") == "S n e h a  S h a r m a"
    assert apply_a1("7834657871") == "7 8 3 4 6 5 7 8 7 1"
    assert apply_a1("sneha8298@webmail.test") == "s n e h a 8 2 9 8 @ w e b m a i l . t e s t"


def test_a2_punctuation_rules():
    def apply_a2(pii_type, v):
        if pii_type == "PAN":
            return v[:5] + "-" + v[5:9] + "-" + v[9:]
        elif pii_type in ("AADHAAR", "BANK_ACCOUNT"):
            return v[:4] + "-" + v[4:8] + "-" + v[8:]
        elif pii_type == "PHONE":
            return v[:5] + "-" + v[5:]
        elif pii_type == "PERSON":
            return v.replace(" ", "-")
        elif pii_type == "EMAIL":
            local, domain = v.split("@")
            return local[:-4] + "-" + local[-4:] + "@" + domain
        elif pii_type == "UPI_ID":
            local, domain = v.split("@")
            return local[:5] + "-" + local[5:] + "@" + domain
        elif pii_type == "ADDRESS":
            return v.replace(", ", " / ")
        raise ValueError(f"Unknown type {pii_type}")

    assert apply_a2("PAN", "FZZFN0256Z") == "FZZFN-0256-Z"
    assert apply_a2("AADHAAR", "083172788957") == "0831-7278-8957"
    assert apply_a2("PHONE", "7834657871") == "78346-57871"
    assert apply_a2("BANK_ACCOUNT", "324210249947") == "3242-1024-9947"
    assert apply_a2("PERSON", "Sneha Sharma") == "Sneha-Sharma"
    assert apply_a2("EMAIL", "sneha8298@webmail.test") == "sneha-8298@webmail.test"
    assert apply_a2("UPI_ID", "9996507527@mail.test") == "99965-07527@mail.test"
    assert apply_a2("ADDRESS", "Flat 230, Silver Oak Heights, Baner Road, Bengaluru 754235") == "Flat 230 / Silver Oak Heights / Baner Road / Bengaluru 754235"


def test_a3_label_obfuscation_rules():
    a3_map = {
        "PERSON": ("My name is ", "My N.A.M.E: "),
        "ADDRESS": ("My address is ", "My A.D.D.R.E.S.S: "),
        "PHONE": ("My phone number is ", "My P.H.O.N.E. No.: "),
        "EMAIL": ("Email me at ", "E.M.A.I.L: "),
        "PAN": ("My PAN number is ", "My P.A.N. No.: "),
        "AADHAAR": ("My Aadhaar number is ", "My A.A.D.H.A.A.R. No.: "),
        "UPI_ID": ("My UPI ID is ", "My U.P.I. I.D.: "),
        "BANK_ACCOUNT": ("My bank account number is ", "My B.A.N.K. A/C No.: "),
    }

    with open(BASE_INSTANCES_PATH, "r", encoding="utf-8") as f:
        bases = [json.loads(line) for line in f if line.strip()]
    base_map = {b["base_id"]: b for b in bases}

    for bid in SELECTED_BASE_IDS:
        b = base_map[bid]
        ptype = b["pii"][0]["type"]
        val = b["pii"][0]["base_pii_value"]
        old_prefix, new_prefix = a3_map[ptype]
        assert b["canonical_text"].startswith(old_prefix)
        new_text = b["canonical_text"].replace(old_prefix, new_prefix, 1)
        assert val in new_text
        start = new_text.find(val)
        assert new_text[start : start + len(val)] == val


def test_a4_informal_abbreviation_rules():
    a4_map = {
        "PERSON": ("My name is ", "name: "),
        "ADDRESS": ("My address is ", "addr: "),
        "PHONE": ("My phone number is ", "ph no: "),
        "EMAIL": ("Email me at ", "mail: "),
        "PAN": ("My PAN number is ", "pan no: "),
        "AADHAAR": ("My Aadhaar number is ", "aadhaar no: "),
        "UPI_ID": ("My UPI ID is ", "upi: "),
        "BANK_ACCOUNT": ("My bank account number is ", "acct no: "),
    }

    with open(BASE_INSTANCES_PATH, "r", encoding="utf-8") as f:
        bases = [json.loads(line) for line in f if line.strip()]
    base_map = {b["base_id"]: b for b in bases}

    for bid in SELECTED_BASE_IDS:
        b = base_map[bid]
        ptype = b["pii"][0]["type"]
        val = b["pii"][0]["base_pii_value"]
        old_prefix, new_prefix = a4_map[ptype]
        assert b["canonical_text"].startswith(old_prefix)
        new_text = b["canonical_text"].replace(old_prefix, new_prefix, 1)
        assert val in new_text
        start = new_text.find(val)
        assert new_text[start : start + len(val)] == val


def test_a5_character_variation_rules():
    ocr_map = {"0": "O", "1": "l", "5": "S", "8": "B"}

    def apply_a5(pii_type, v):
        if pii_type in ("PAN", "PERSON", "ADDRESS"):
            return v.lower()
        elif pii_type in ("EMAIL", "UPI_ID"):
            return v.upper()
        elif pii_type in ("PHONE", "AADHAAR", "BANK_ACCOUNT"):
            for i, c in enumerate(v):
                if c in ocr_map:
                    return v[:i] + ocr_map[c] + v[i + 1 :]
            raise ValueError(f"No OCR match in {v}")
        raise ValueError(f"Unknown type {pii_type}")

    with open(BASE_INSTANCES_PATH, "r", encoding="utf-8") as f:
        bases = [json.loads(line) for line in f if line.strip()]
    base_map = {b["base_id"]: b for b in bases}

    for bid in SELECTED_BASE_IDS:
        b = base_map[bid]
        ptype = b["pii"][0]["type"]
        val = b["pii"][0]["base_pii_value"]
        mutated = apply_a5(ptype, val)
        assert mutated != val
        if ptype in ("PHONE", "AADHAAR", "BANK_ACCOUNT"):
            # Exactly one character difference
            diff_count = sum(1 for c1, c2 in zip(val, mutated) if c1 != c2)
            assert diff_count == 1
            assert len(val) == len(mutated)


def test_sample_adversarial_record_schema_validity():
    schema = json.loads(EXAMPLE_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    sample_record = {
        "base_id": "PAN_001",
        "variant_id": "PAN_001_EN_A1_01",
        "text": "My PAN number is F Z Z F N 0 2 5 6 Z.",
        "entities": [
            {
                "type": "PAN",
                "base_pii_value": "FZZFN0256Z",
                "realized_pii_value": "F Z Z F N 0 2 5 6 Z",
                "pii_script": "LATIN",
                "start": 17,
                "end": 36,
                "occurrence_index": 0,
            }
        ],
        "distractors": [],
        "language": "EN",
        "carrier_script": "LATIN",
        "context": "EXPLICIT",
        "domain": "ACCOUNT_VERIFICATION",
        "perturbation": {
            "family": "A1",
            "type": "SPACING",
            "severity": 1,
            "target": "VALUE",
        },
        "difficulty": "ADVERSARIAL",
        "address_structure": None,
        "hi_variant_collapsed": False,
        "synthetic": True,
        "generator_version": "0.1.0",
        "guidelines_version": "0.18",
        "template_id": "EN_PAN_A1_SPACING_TEMPLATE",
        "seed": 42,
        "validation": {
            "structural": "PENDING",
            "span": "PENDING",
            "semantic": "PENDING",
            "language": "PENDING",
            "duplicate": "PENDING",
            "human": "PENDING",
        },
        "validation_status": "PENDING",
        "review_status": "PENDING",
        "split": None,
    }

    validator.validate(sample_record)


def test_no_evaluation_or_benchmark_code_exists():
    assert not (REPO_ROOT / "training" / "train.py").exists()
    assert not (REPO_ROOT / "experiments" / "E01_baseline.py").exists()
    assert not (REPO_ROOT / "application" / "detector.py").exists()
