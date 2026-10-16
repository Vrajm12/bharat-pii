"""T10 tests: the literal semantic validator (validators/semantic.py),
Layer 3 only (guidelines.md §15: "Sentence uses the value in the declared
role"). Governance for every constant checked here was resolved and frozen
before this file was written (OQ-035/036/037, guidelines.md v0.13,
tests/test_t10_governance.py) -- these tests exercise the validator
implementation itself, not the governance decisions.
"""

import ast
import json
from pathlib import Path

import pytest

from generators.translit.table import transliterate_value
from validators.semantic import (
    DEVANAGARI_LABEL,
    LATIN_LABEL,
    MISSING_SEMANTIC_ROLE,
    ROLE_UNSUPPORTED_BY_TEXT,
    SEMANTIC_MISMATCH,
    check_base_linkage,
    check_condition_semantic_contract,
    check_realized_value_identity,
    check_semantic_role_matches_type,
    validate_collapsed_hindi_semantics,
    validate_dataset,
    validate_hindi_matched_pair_semantics,
    validate_record_semantic,
)

ROOT = Path(__file__).resolve().parent.parent
BASES_PATH = ROOT / "data" / "raw" / "base_instances.jsonl"
RECORDS_PATH = ROOT / "data" / "generated" / "language_realizations.jsonl"

FROZEN_ROLE = {
    "PERSON": "PERSON_NAME",
    "ADDRESS": "DELIVERY_ADDRESS",
    "PHONE": "CONTACT_NUMBER",
    "EMAIL": "CONTACT_EMAIL",
    "PAN": "TAX_IDENTIFIER",
    "AADHAAR": "NATIONAL_ID_IDENTIFIER",
    "UPI_ID": "PAYMENT_IDENTIFIER",
    "BANK_ACCOUNT": "PAYMENT_ACCOUNT_IDENTIFIER",
}


def _load_jsonl(path: Path) -> list:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _base(pii_type, role, base_pii_value="X", domain="general_conversation", canonical_text=None, base_id=None):
    return {
        "base_id": base_id or f"{pii_type}_TEST",
        "base_kind": "POSITIVE",
        "pii": [{"type": pii_type, "base_pii_value": base_pii_value, "semantic_role": role}],
        "person_context": None,
        "scenario": {"domain": domain, "purpose": "test"},
        "address_structure": None,
        "canonical_text": canonical_text or f"Test sentence with {pii_type} value {base_pii_value}.",
        "synthetic": True,
        "generator_version": "0.1.0",
    }


def _record(
    base_id,
    variant_id,
    text,
    pii_type,
    base_pii_value,
    realized_pii_value,
    language,
    start,
    end,
    domain="GENERAL_CONVERSATION",
    context="EXPLICIT",
    perturbation_family="NONE",
    hi_variant_collapsed=False,
):
    return {
        "base_id": base_id,
        "variant_id": variant_id,
        "text": text,
        "entities": [
            {
                "type": pii_type,
                "base_pii_value": base_pii_value,
                "realized_pii_value": realized_pii_value,
                "pii_script": "LATIN",
                "start": start,
                "end": end,
                "occurrence_index": 0,
            }
        ],
        "distractors": [],
        "language": language,
        "carrier_script": "LATIN",
        "context": context,
        "domain": domain,
        "perturbation": {"family": perturbation_family, "type": "NONE", "severity": 0, "target": "NONE"},
        "difficulty": "EASY",
        "address_structure": None,
        "hi_variant_collapsed": hi_variant_collapsed,
        "synthetic": True,
        "generator_version": "0.1.0",
        "guidelines_version": "0.13",
        "template_id": "TEST",
        "seed": 42,
        "validation": {
            "structural": "PENDING", "span": "PENDING", "semantic": "PENDING",
            "language": "PENDING", "duplicate": "PENDING", "human": "PENDING",
        },
        "validation_status": "PENDING",
        "review_status": "PENDING",
        "split": None,
    }


# --- 1. all eight valid type/role pairs -------------------------------------


@pytest.mark.parametrize("pii_type,role", sorted(FROZEN_ROLE.items()))
def test_all_eight_valid_type_role_pairs_pass(pii_type, role):
    base = _base(pii_type, role)
    assert check_semantic_role_matches_type(base) == []


# --- 2. all eight wrong-role cases -------------------------------------------


@pytest.mark.parametrize("pii_type,correct_role", sorted(FROZEN_ROLE.items()))
def test_all_eight_wrong_role_cases_are_rejected(pii_type, correct_role):
    wrong_role = "SOME_OTHER_ROLE_" + correct_role
    base = _base(pii_type, wrong_role)
    issues = check_semantic_role_matches_type(base)
    assert len(issues) == 1
    assert issues[0].reason == SEMANTIC_MISMATCH


# --- 3. unknown role / missing role ------------------------------------------


def test_unknown_role_value_is_rejected():
    base = _base("PAN", "NOT_A_REAL_ROLE_AT_ALL")
    issues = check_semantic_role_matches_type(base)
    assert len(issues) == 1
    assert issues[0].reason == SEMANTIC_MISMATCH


def test_missing_role_is_rejected_as_missing_semantic_role():
    base = _base("PAN", "")
    issues = check_semantic_role_matches_type(base)
    assert len(issues) == 1
    assert issues[0].reason == MISSING_SEMANTIC_ROLE


def test_missing_role_field_entirely_is_rejected():
    base = _base("PAN", "TAX_IDENTIFIER")
    del base["pii"][0]["semantic_role"]
    issues = check_semantic_role_matches_type(base)
    assert len(issues) == 1
    assert issues[0].reason == MISSING_SEMANTIC_ROLE


# --- 4. base linkage mismatch / base PII mutation / derived PII mutation ---


def test_base_linkage_type_mismatch_is_rejected():
    base = _base("PAN", "TAX_IDENTIFIER", base_pii_value="ABCDE1234F")
    record = _record(
        base["base_id"], "V1", "My PAN number is ABCDE1234F.",
        pii_type="AADHAAR", base_pii_value="ABCDE1234F", realized_pii_value="ABCDE1234F",
        language="EN", start=17, end=27,
    )
    issues = check_base_linkage(record, base)
    assert any(i.reason == SEMANTIC_MISMATCH and "type" in i.detail for i in issues)


def test_base_pii_mutation_is_rejected():
    """The base itself declares a different base_pii_value than the record's
    entity claims to link against."""
    base = _base("PAN", "TAX_IDENTIFIER", base_pii_value="ABCDE1234F")
    record = _record(
        base["base_id"], "V1", "My PAN number is ZZZZZ9999Z.",
        pii_type="PAN", base_pii_value="ZZZZZ9999Z", realized_pii_value="ZZZZZ9999Z",
        language="EN", start=17, end=27,
    )
    issues = check_base_linkage(record, base)
    assert any(i.reason == SEMANTIC_MISMATCH and "canonical identity mutated" in i.detail for i in issues)


def test_derived_pii_mutation_is_rejected():
    """base_pii_value matches, but realized_pii_value has been tampered
    with independent of the frozen realization rule."""
    base = _base("PAN", "TAX_IDENTIFIER", base_pii_value="ABCDE1234F")
    record = _record(
        base["base_id"], "V1", "My PAN number is QQQQQ0000Q.",
        pii_type="PAN", base_pii_value="ABCDE1234F", realized_pii_value="QQQQQ0000Q",
        language="EN", start=17, end=27,
    )
    issues = check_realized_value_identity(record, base)
    assert len(issues) == 1
    assert issues[0].reason == SEMANTIC_MISMATCH


def test_scenario_mutation_is_rejected():
    base = _base("PAN", "TAX_IDENTIFIER", domain="banking_payments")
    record = _record(
        base["base_id"], "V1", "My PAN number is X.",
        pii_type="PAN", base_pii_value="X", realized_pii_value="X",
        language="EN", start=17, end=18, domain="TELECOM",
    )
    issues = check_base_linkage(record, base)
    assert any(i.reason == SEMANTIC_MISMATCH and "scenario mutated" in i.detail for i in issues)


def test_unmutated_linkage_and_scenario_pass():
    base = _base("PAN", "TAX_IDENTIFIER", base_pii_value="X", domain="banking_payments")
    record = _record(
        base["base_id"], "V1", "Test sentence with PAN value X.",
        pii_type="PAN", base_pii_value="X", realized_pii_value="X",
        language="EN", start=27, end=28, domain="BANKING_PAYMENTS",
    )
    assert check_base_linkage(record, base) == []


# --- 5. non-transliterable realized-value mutation --------------------------


@pytest.mark.parametrize("pii_type", ["PHONE", "EMAIL", "PAN", "AADHAAR", "UPI_ID", "BANK_ACCOUNT"])
def test_non_transliterable_realized_value_must_equal_base_value(pii_type):
    base = _base(pii_type, FROZEN_ROLE[pii_type], base_pii_value="ORIGINAL")
    for language in ("EN", "IN_EN", "ROM_HI", "HINGLISH", "INFORMAL_HINGLISH", "HI_LATIN_PII", "HI_DEVA_PII"):
        good = _record(
            base["base_id"], "V1", "text ORIGINAL text",
            pii_type=pii_type, base_pii_value="ORIGINAL", realized_pii_value="ORIGINAL",
            language=language, start=5, end=13,
        )
        assert check_realized_value_identity(good, base) == []

        mutated = _record(
            base["base_id"], "V1", "text MUTATED text",
            pii_type=pii_type, base_pii_value="ORIGINAL", realized_pii_value="MUTATED",
            language=language, start=5, end=12,
        )
        issues = check_realized_value_identity(mutated, base)
        assert len(issues) == 1
        assert issues[0].reason == SEMANTIC_MISMATCH


# --- 6. PERSON / ADDRESS transliteration identity ---------------------------


def test_person_transliteration_identity_holds_under_hi_deva_pii():
    base = _base("PERSON", "PERSON_NAME", base_pii_value="Rahul")
    expected_deva = transliterate_value("Rahul")
    record = _record(
        base["base_id"], "V1", f"मेरा नाम {expected_deva} है।",
        pii_type="PERSON", base_pii_value="Rahul", realized_pii_value=expected_deva,
        language="HI_DEVA_PII", start=9, end=9 + len(expected_deva),
    )
    assert check_realized_value_identity(record, base) == []


def test_person_transliteration_identity_rejects_a_guessed_devanagari_value():
    base = _base("PERSON", "PERSON_NAME", base_pii_value="Rahul")
    wrong_deva = "गलत"
    record = _record(
        base["base_id"], "V1", f"मेरा नाम {wrong_deva} है।",
        pii_type="PERSON", base_pii_value="Rahul", realized_pii_value=wrong_deva,
        language="HI_DEVA_PII", start=9, end=9 + len(wrong_deva),
    )
    issues = check_realized_value_identity(record, base)
    assert len(issues) == 1
    assert issues[0].reason == SEMANTIC_MISMATCH


def test_person_non_hi_deva_pii_conditions_use_the_base_value_unchanged():
    base = _base("PERSON", "PERSON_NAME", base_pii_value="Rahul")
    for language in ("EN", "IN_EN", "ROM_HI", "HINGLISH", "INFORMAL_HINGLISH", "HI_LATIN_PII"):
        record = _record(
            base["base_id"], "V1", "mera naam Rahul hai",
            pii_type="PERSON", base_pii_value="Rahul", realized_pii_value="Rahul",
            language=language, start=10, end=15,
        )
        assert check_realized_value_identity(record, base) == []


def test_address_transliteration_identity_holds_under_hi_deva_pii():
    """ADDRESS's Devanagari form is never cached on the base (OQ-021) -- it
    is computed fresh via the same T07 oracle at validation time, exactly as
    at generation time."""
    base = _base("ADDRESS", "DELIVERY_ADDRESS", base_pii_value="MG Road")
    expected_deva = transliterate_value("MG Road")
    record = _record(
        base["base_id"], "V1", f"mera address {expected_deva} hai",
        pii_type="ADDRESS", base_pii_value="MG Road", realized_pii_value=expected_deva,
        language="HI_DEVA_PII", start=13, end=13 + len(expected_deva),
    )
    assert check_realized_value_identity(record, base) == []


def test_invalid_devanagari_transliteration_is_rejected():
    """A record independently supplying/guessing a Devanagari value instead
    of using T07's deterministic table -- must never be accepted."""
    base = _base("ADDRESS", "DELIVERY_ADDRESS", base_pii_value="MG Road")
    guessed = "मेरा रास्ता"  # plausible-looking but not T07's actual output
    assert guessed != transliterate_value("MG Road")
    record = _record(
        base["base_id"], "V1", f"mera address {guessed} hai",
        pii_type="ADDRESS", base_pii_value="MG Road", realized_pii_value=guessed,
        language="HI_DEVA_PII", start=13, end=13 + len(guessed),
    )
    issues = check_realized_value_identity(record, base)
    assert len(issues) == 1
    assert issues[0].reason == SEMANTIC_MISMATCH


# --- 7. EN contract -----------------------------------------------------


def test_en_exact_canonical_equality_passes():
    base = _base("PAN", "TAX_IDENTIFIER", canonical_text="My PAN number is ABCDE1234F.")
    record = _record(
        base["base_id"], "V1", "My PAN number is ABCDE1234F.",
        pii_type="PAN", base_pii_value="X", realized_pii_value="ABCDE1234F",
        language="EN", start=17, end=27,
    )
    assert check_condition_semantic_contract(record, base) == []


def test_en_semantic_mismatch_is_rejected():
    base = _base("PAN", "TAX_IDENTIFIER", canonical_text="My PAN number is ABCDE1234F.")
    record = _record(
        base["base_id"], "V1", "My reference number is ABCDE1234F.",
        pii_type="PAN", base_pii_value="X", realized_pii_value="ABCDE1234F",
        language="EN", start=23, end=33,
    )
    issues = check_condition_semantic_contract(record, base)
    assert len(issues) == 1
    assert issues[0].reason == SEMANTIC_MISMATCH


def test_en_perturbed_record_is_out_of_contract_scope_no_issue_raised():
    """guidelines.md §13.6 scopes the EN contract to context=EXPLICIT,
    perturbation.family=NONE only -- a perturbed EN record has no frozen
    rule to violate."""
    base = _base("PAN", "TAX_IDENTIFIER", canonical_text="My PAN number is ABCDE1234F.")
    record = _record(
        base["base_id"], "V1", "My  PAN  number  is  ABCDE1234F.",
        pii_type="PAN", base_pii_value="X", realized_pii_value="ABCDE1234F",
        language="EN", start=21, end=31, perturbation_family="A1",
    )
    assert check_condition_semantic_contract(record, base) == []


# --- 8. IN_EN contract -----------------------------------------------------


def test_in_en_canonical_containment_passes():
    base = _base("PAN", "TAX_IDENTIFIER", canonical_text="My PAN number is ABCDE1234F.")
    record = _record(
        base["base_id"], "V1", "Kindly note: My PAN number is ABCDE1234F.",
        pii_type="PAN", base_pii_value="X", realized_pii_value="ABCDE1234F",
        language="IN_EN", start=31, end=41,
    )
    assert check_condition_semantic_contract(record, base) == []


def test_in_en_semantic_mismatch_is_rejected():
    base = _base("PAN", "TAX_IDENTIFIER", canonical_text="My PAN number is ABCDE1234F.")
    record = _record(
        base["base_id"], "V1", "Kindly note: my reference is ABCDE1234F.",
        pii_type="PAN", base_pii_value="X", realized_pii_value="ABCDE1234F",
        language="IN_EN", start=30, end=40,
    )
    issues = check_condition_semantic_contract(record, base)
    assert len(issues) == 1
    assert issues[0].reason == SEMANTIC_MISMATCH


# --- 9. each of the five §13.7 label-driven conditions ----------------------


@pytest.mark.parametrize("language", ["ROM_HI", "HINGLISH", "INFORMAL_HINGLISH"])
@pytest.mark.parametrize("pii_type", sorted(FROZEN_ROLE))
def test_latin_label_condition_passes_when_label_present(language, pii_type):
    base = _base(pii_type, FROZEN_ROLE[pii_type])
    label = LATIN_LABEL[pii_type]
    text = f"mera {label} X hai"
    record = _record(
        base["base_id"], "V1", text,
        pii_type=pii_type, base_pii_value="X", realized_pii_value="X",
        language=language, start=text.index("X"), end=text.index("X") + 1,
    )
    assert check_condition_semantic_contract(record, base) == []


@pytest.mark.parametrize("language", ["HI_LATIN_PII", "HI_DEVA_PII"])
@pytest.mark.parametrize("pii_type", sorted(FROZEN_ROLE))
def test_devanagari_label_condition_passes_when_label_present(language, pii_type):
    base = _base(pii_type, FROZEN_ROLE[pii_type])
    label = DEVANAGARI_LABEL[pii_type]
    text = f"मेरा {label} X है"
    record = _record(
        base["base_id"], "V1", text,
        pii_type=pii_type, base_pii_value="X", realized_pii_value="X",
        language=language, start=text.index("X"), end=text.index("X") + 1,
    )
    assert check_condition_semantic_contract(record, base) == []


# --- 10. wrong semantic label / missing semantic label -----------------------


def test_wrong_semantic_label_is_rejected_as_role_unsupported_by_text():
    """A hand-mutated record whose text carries a different type's label
    instead of its own declared type's."""
    base = _base("AADHAAR", "NATIONAL_ID_IDENTIFIER")
    record = _record(
        base["base_id"], "V1", "mera account number X hai",
        pii_type="AADHAAR", base_pii_value="X", realized_pii_value="X",
        language="HINGLISH", start=21, end=22,
    )
    issues = check_condition_semantic_contract(record, base)
    assert len(issues) == 1
    assert issues[0].reason == ROLE_UNSUPPORTED_BY_TEXT


def test_missing_semantic_label_is_rejected_as_role_unsupported_by_text():
    base = _base("PHONE", "CONTACT_NUMBER")
    record = _record(
        base["base_id"], "V1", "X hai",
        pii_type="PHONE", base_pii_value="X", realized_pii_value="X",
        language="ROM_HI", start=0, end=1,
    )
    issues = check_condition_semantic_contract(record, base)
    assert len(issues) == 1
    assert issues[0].reason == ROLE_UNSUPPORTED_BY_TEXT


def test_devanagari_label_condition_is_case_sensitive_script_has_no_case():
    base = _base("PAN", "TAX_IDENTIFIER")
    record = _record(
        base["base_id"], "V1", "मेरा pan X है",  # Latin "pan", not the frozen Devanagari-carrier "PAN"
        pii_type="PAN", base_pii_value="X", realized_pii_value="X",
        language="HI_DEVA_PII", start=9, end=10,
    )
    issues = check_condition_semantic_contract(record, base)
    assert len(issues) == 1
    assert issues[0].reason == ROLE_UNSUPPORTED_BY_TEXT
    # but "PAN" (correct case, per §4.13's own note it stays Latin/uppercase) passes
    record_ok = _record(
        base["base_id"], "V1", "मेरा PAN X है",
        pii_type="PAN", base_pii_value="X", realized_pii_value="X",
        language="HI_DEVA_PII", start=8, end=9,
    )
    assert check_condition_semantic_contract(record_ok, base) == []


def test_latin_label_condition_is_case_insensitive():
    """Justified by guidelines.md §4.14's own frozen INFORMAL_HINGLISH
    all-lowercase feature."""
    base = _base("EMAIL", "CONTACT_EMAIL")
    record = _record(
        base["base_id"], "V1", "EMAIL pe msg kr X",
        pii_type="EMAIL", base_pii_value="X", realized_pii_value="X",
        language="INFORMAL_HINGLISH", start=16, end=17,
    )
    assert check_condition_semantic_contract(record, base) == []


# --- 11. HI_LATIN_PII / HI_DEVA_PII matched pair -----------------------------


def test_matched_pair_passes_when_carrier_text_is_identical_outside_pii_span():
    base = _base("PERSON", "PERSON_NAME")
    latin = _record(
        base["base_id"], "PERSON_TEST_HI_LATIN_PII", "मेरा नाम Rahul है।",
        pii_type="PERSON", base_pii_value="Rahul", realized_pii_value="Rahul",
        language="HI_LATIN_PII", start=9, end=14, domain="GENERAL_CONVERSATION",
    )
    deva = _record(
        base["base_id"], "PERSON_TEST_HI_DEVA_PII", "मेरा नाम राहुल है।",
        pii_type="PERSON", base_pii_value="Rahul", realized_pii_value="राहुल",
        language="HI_DEVA_PII", start=9, end=14, domain="GENERAL_CONVERSATION",
    )
    assert validate_hindi_matched_pair_semantics([latin, deva], base) == []


def test_matched_pair_rejects_diverging_carrier_text():
    base = _base("PERSON", "PERSON_NAME")
    latin = _record(
        base["base_id"], "PERSON_TEST_HI_LATIN_PII", "मेरा नाम Rahul है।",
        pii_type="PERSON", base_pii_value="Rahul", realized_pii_value="Rahul",
        language="HI_LATIN_PII", start=9, end=14,
    )
    deva = _record(
        base["base_id"], "PERSON_TEST_HI_DEVA_PII", "यह नाम राहुल है।",  # different prefix
        pii_type="PERSON", base_pii_value="Rahul", realized_pii_value="राहुल",
        language="HI_DEVA_PII", start=7, end=12,
    )
    issues = validate_hindi_matched_pair_semantics([latin, deva], base)
    assert any(i.reason == SEMANTIC_MISMATCH and "carrier text diverges" in i.detail for i in issues)


def test_matched_pair_rejects_diverging_domain():
    base = _base("ADDRESS", "DELIVERY_ADDRESS")
    latin = _record(
        base["base_id"], "V1", "मेरा address X है",
        pii_type="ADDRESS", base_pii_value="X", realized_pii_value="X",
        language="HI_LATIN_PII", start=12, end=13, domain="DELIVERY_ADDRESS",
    )
    deva = _record(
        base["base_id"], "V2", "मेरा address Y है",
        pii_type="ADDRESS", base_pii_value="X", realized_pii_value="Y",
        language="HI_DEVA_PII", start=12, end=13, domain="TELECOM",
    )
    issues = validate_hindi_matched_pair_semantics([latin, deva], base)
    assert any("domain diverges" in i.detail for i in issues)


def test_matched_pair_skips_when_one_record_is_missing():
    """Existence is T09's job -- this function must not duplicate it."""
    base = _base("PERSON", "PERSON_NAME")
    latin_only = _record(
        base["base_id"], "V1", "मेरा नाम Rahul है।",
        pii_type="PERSON", base_pii_value="Rahul", realized_pii_value="Rahul",
        language="HI_LATIN_PII", start=9, end=14,
    )
    assert validate_hindi_matched_pair_semantics([latin_only], base) == []


def test_matched_pair_not_applicable_to_non_transliterable_types():
    base = _base("PAN", "TAX_IDENTIFIER")
    assert validate_hindi_matched_pair_semantics([], base) == []


# --- 12. collapsed Hindi representation --------------------------------------


def test_collapsed_hindi_representation_passes_when_well_formed():
    base = _base("BANK_ACCOUNT", "PAYMENT_ACCOUNT_IDENTIFIER", base_pii_value="123456789012")
    collapsed = _record(
        base["base_id"], "V1", "mera account 123456789012 hai",
        pii_type="BANK_ACCOUNT", base_pii_value="123456789012", realized_pii_value="123456789012",
        language="HI_LATIN_PII", start=13, end=25, hi_variant_collapsed=True,
    )
    assert validate_collapsed_hindi_semantics([collapsed], base) == []


def test_collapsed_hindi_representation_rejects_missing_collapsed_flag():
    base = _base("BANK_ACCOUNT", "PAYMENT_ACCOUNT_IDENTIFIER", base_pii_value="123456789012")
    collapsed = _record(
        base["base_id"], "V1", "mera account 123456789012 hai",
        pii_type="BANK_ACCOUNT", base_pii_value="123456789012", realized_pii_value="123456789012",
        language="HI_LATIN_PII", start=13, end=25, hi_variant_collapsed=False,
    )
    issues = validate_collapsed_hindi_semantics([collapsed], base)
    assert any("hi_variant_collapsed" in i.detail for i in issues)


def test_collapsed_hindi_representation_rejects_identity_mutation():
    base = _base("BANK_ACCOUNT", "PAYMENT_ACCOUNT_IDENTIFIER", base_pii_value="123456789012")
    collapsed = _record(
        base["base_id"], "V1", "mera account 999999999999 hai",
        pii_type="BANK_ACCOUNT", base_pii_value="123456789012", realized_pii_value="999999999999",
        language="HI_LATIN_PII", start=13, end=25, hi_variant_collapsed=True,
    )
    issues = validate_collapsed_hindi_semantics([collapsed], base)
    assert any("semantic identity not preserved" in i.detail for i in issues)


def test_collapsed_hindi_not_applicable_to_transliterable_types():
    base = _base("PERSON", "PERSON_NAME")
    assert validate_collapsed_hindi_semantics([], base) == []


# --- 13. determinism / immutability -----------------------------------------


def test_deterministic_repeated_validation():
    bases = _load_jsonl(BASES_PATH)
    records = _load_jsonl(RECORDS_PATH)
    first = validate_dataset(records, bases)
    second = validate_dataset(records, bases)
    assert first["total_records"] == second["total_records"]
    assert first["valid_records"] == second["valid_records"]
    assert len(first["issues"]) == len(second["issues"])


def test_input_immutability():
    base = _base("PAN", "TAX_IDENTIFIER")
    record = _record(
        base["base_id"], "V1", "Test sentence with PAN value X.",
        pii_type="PAN", base_pii_value="X", realized_pii_value="X",
        language="EN", start=27, end=28,
    )
    base_copy = json.loads(json.dumps(base))
    record_copy = json.loads(json.dumps(record))
    validate_record_semantic(record, {base["base_id"]: base})
    assert base == base_copy
    assert record == record_copy


# --- 14. all 624 frozen records ----------------------------------------------


def test_all_624_frozen_records_pass_semantic_validation():
    bases = _load_jsonl(BASES_PATH)
    records = _load_jsonl(RECORDS_PATH)
    assert len(bases) == 100
    assert len(records) == 624
    report = validate_dataset(records, bases)
    assert report["total_records"] == 624
    assert report["issues"] == []
    assert report["valid_records"] == 624


# --- 15. static inspection: no generator-implementation dependency ---------


def test_semantic_validator_source_does_not_import_generator_templates_or_base_instances():
    source = (ROOT / "validators" / "semantic.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    forbidden = {"generators.base_instances", "generators.language.templates"}
    assert not (imported_modules & forbidden), imported_modules

    for module_name in imported_modules:
        assert "templates" not in module_name
        assert "base_instances" not in module_name


def test_semantic_validator_source_text_never_mentions_forbidden_modules():
    source = (ROOT / "validators" / "semantic.py").read_text(encoding="utf-8")
    assert "generators.language.templates" not in source
    assert "generators.base_instances" not in source
    assert "CARRIER_TEMPLATE" not in source
    assert "CANONICAL_TEMPLATE" not in source


# --- HARD_NEGATIVE compatibility (T11 Phase 2 pre-audit, guidelines.md §13.3) -
#
# A hard negative declares no PII and therefore no semantic_role to assert --
# Layer 3 doesn't apply to it at all, for any language condition. Without a
# guard, check_condition_semantic_contract would look up a §13.7 label by
# pii_type=None for ROM_HI/HINGLISH/INFORMAL_HINGLISH/HI_LATIN_PII/
# HI_DEVA_PII and report a spurious SEMANTIC_MISMATCH on every one -- these
# tests prove the guard, across several conditions, and prove the existing
# POSITIVE-record behavior is unchanged.


_HARD_NEGATIVE_BASE = {
    "base_id": "NEG_001",
    "base_kind": "HARD_NEGATIVE",
    "pii": [],
    "scenario": {"domain": "customer_support", "purpose": "hard_negative_context"},
    "canonical_text": "The order number is 9876543210.",
    "hard_negative_decoy": {
        "decoy_class": "NUMERIC_SHAPE",
        "value": "9876543210",
        "surface_type": "PHONE",
        "actual_role": "ORDER_REFERENCE",
    },
}


@pytest.mark.parametrize(
    "language", ["EN", "IN_EN", "ROM_HI", "HINGLISH", "INFORMAL_HINGLISH", "HI_LATIN_PII"]
)
def test_hard_negative_record_passes_semantic_validation_on_every_condition(language):
    record = {
        "base_id": "NEG_001",
        "variant_id": f"NEG_001_{language}",
        "text": "kisi bhi tarah ka text yahan ho sakta hai",
        "entities": [],
        "language": language,
        "context": "EXPLICIT",
        "domain": "CUSTOMER_SUPPORT",
        "perturbation": {"family": "NONE", "type": "NONE", "severity": 0, "target": "NONE"},
    }
    assert validate_record_semantic(record, {"NEG_001": _HARD_NEGATIVE_BASE}) == []


def test_positive_record_semantic_validation_is_unaffected_by_the_guard():
    """Regression guard: the HARD_NEGATIVE early return must not fire for
    (or otherwise change the outcome of) an ordinary POSITIVE record."""
    base = {
        "base_id": "PAN_001",
        "base_kind": "POSITIVE",
        "pii": [{"type": "PAN", "base_pii_value": "ABCDE1234F", "semantic_role": "TAX_IDENTIFIER"}],
        "scenario": {"domain": "banking_payments", "purpose": "identity_verification"},
        "canonical_text": "My PAN number is ABCDE1234F.",
    }
    record = {
        "base_id": "PAN_001",
        "variant_id": "PAN_001_EN",
        "text": "My PAN number is ABCDE1234F.",
        "entities": [
            {
                "type": "PAN",
                "base_pii_value": "ABCDE1234F",
                "realized_pii_value": "ABCDE1234F",
                "pii_script": "LATIN",
                "start": 17,
                "end": 27,
                "occurrence_index": 0,
            }
        ],
        "language": "EN",
        "context": "EXPLICIT",
        "domain": "BANKING_PAYMENTS",
        "perturbation": {"family": "NONE", "type": "NONE", "severity": 0, "target": "NONE"},
    }
    assert validate_record_semantic(record, {"PAN_001": base}) == []
