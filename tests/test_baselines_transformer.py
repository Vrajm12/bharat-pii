"""Unit tests for baselines/transformer.py (PROJECT_SPEC.md §19 B4, §20.5, §20.6).

Phase 2 pre-benchmark validation suite covering:
1. Adapter subclasses BaselineAdapter.
2. Exact system metadata.
3. Model/tokenizer initialization.
4. PERSON/PER detection.
5. Out-of-taxonomy labels are preserved.
6. No artificial PAN mapping.
7. No artificial AADHAAR mapping.
8. No artificial PHONE mapping.
9. No artificial EMAIL mapping.
10. No artificial UPI_ID mapping.
11. No artificial BANK_ACCOUNT mapping.
12. No artificial ADDRESS mapping.
13. Devanagari Unicode offsets.
14. Code-mixed Hindi/English offsets.
15. Prediction validation through validate_predictions().
16. Deterministic repeated output.
17. Deterministic sorting.
18. Input text immutability.
19. Every offset satisfies text[start:end] == predicted span.
20. Empty/clean text handling.
"""

from __future__ import annotations

import pytest
from transformers import AutoModelForTokenClassification, AutoTokenizer

from baselines.base import BaselineAdapter, validate_predictions
from baselines.transformer import TransformerBaselineAdapter
from benchmark.schema import Prediction


@pytest.fixture(scope="module")
def shared_adapter() -> TransformerBaselineAdapter:
    """Instantiate a shared adapter once for fast and deterministic test execution."""
    return TransformerBaselineAdapter()


def test_1_adapter_subclasses_baseline_adapter(shared_adapter: TransformerBaselineAdapter):
    """1. Adapter subclasses BaselineAdapter."""
    assert isinstance(shared_adapter, BaselineAdapter)


def test_2_exact_system_metadata(shared_adapter: TransformerBaselineAdapter):
    """2. Exact system metadata."""
    assert shared_adapter.system_name == "transformer"
    assert "Davlan_xlm-roberta-base-ner-hrl" in shared_adapter.system_version
    assert "5.16.1" in shared_adapter.system_version


def test_3_model_tokenizer_initialization():
    """3. Model/tokenizer initialization."""
    model_name = "Davlan/xlm-roberta-base-ner-hrl"
    tok = AutoTokenizer.from_pretrained(model_name)
    mod = AutoModelForTokenClassification.from_pretrained(model_name)
    assert tok.is_fast, "Model must use a Fast Tokenizer for precise character-level alignment."
    assert mod.num_labels == 9
    assert "B-PER" in mod.config.id2label.values()


def test_4_person_per_detection(shared_adapter: TransformerBaselineAdapter):
    """4. PERSON/PER detection."""
    text = "Yesterday, Rajesh Sharma met with Sneha Verma at the conference."
    preds = shared_adapter.predict(text)

    person_preds = [p for p in preds if p.type == "PERSON"]
    assert len(person_preds) >= 1
    for p in person_preds:
        assert p.status == "VALID"
        assert text[p.start : p.end] == p.text
        assert p.confidence is not None and 0.0 <= p.confidence <= 1.0


def test_5_out_of_taxonomy_labels_preserved(shared_adapter: TransformerBaselineAdapter):
    """5. Out-of-taxonomy labels are preserved."""
    text = "Google was founded in Menlo Park in September 1998."
    preds = shared_adapter.predict(text)

    types = {p.type for p in preds}
    assert any(t in types for t in ["LOC", "ORG", "DATE", "MISC"])
    for p in preds:
        assert p.status == "VALID"
        assert text[p.start : p.end] == p.text


def test_6_no_artificial_pan_mapping(shared_adapter: TransformerBaselineAdapter):
    """6. No artificial PAN mapping."""
    text = "My PAN number is ABCDE1234F."
    preds = shared_adapter.predict(text)
    assert "PAN" not in {p.type for p in preds}


def test_7_no_artificial_aadhaar_mapping(shared_adapter: TransformerBaselineAdapter):
    """7. No artificial AADHAAR mapping."""
    text = "My Aadhaar number is 1234 5678 9012."
    preds = shared_adapter.predict(text)
    assert "AADHAAR" not in {p.type for p in preds}


def test_8_no_artificial_phone_mapping(shared_adapter: TransformerBaselineAdapter):
    """8. No artificial PHONE mapping."""
    text = "Please call +91 9876543210 immediately."
    preds = shared_adapter.predict(text)
    assert "PHONE" not in {p.type for p in preds}


def test_9_no_artificial_email_mapping(shared_adapter: TransformerBaselineAdapter):
    """9. No artificial EMAIL mapping."""
    text = "Send an email to support@example.com for help."
    preds = shared_adapter.predict(text)
    assert "EMAIL" not in {p.type for p in preds}


def test_10_no_artificial_upi_id_mapping(shared_adapter: TransformerBaselineAdapter):
    """10. No artificial UPI_ID mapping."""
    text = "Payment received at user@okhdfcbank."
    preds = shared_adapter.predict(text)
    assert "UPI_ID" not in {p.type for p in preds}


def test_11_no_artificial_bank_account_mapping(shared_adapter: TransformerBaselineAdapter):
    """11. No artificial BANK_ACCOUNT mapping."""
    text = "Transfer funds to account 123456789012."
    preds = shared_adapter.predict(text)
    assert "BANK_ACCOUNT" not in {p.type for p in preds}


def test_12_no_artificial_address_mapping(shared_adapter: TransformerBaselineAdapter):
    """12. No artificial ADDRESS mapping."""
    text = "Located at Flat 402, Shanti Heights, MG Road, Pune."
    preds = shared_adapter.predict(text)
    assert "ADDRESS" not in {p.type for p in preds}


def test_13_devanagari_unicode_offsets(shared_adapter: TransformerBaselineAdapter):
    """13. Devanagari Unicode offsets."""
    text = "कल राजेश शर्मा ने नई दिल्ली का दौरा किया।"
    preds = shared_adapter.predict(text)

    for p in preds:
        assert 0 <= p.start < p.end <= len(text)
        assert text[p.start : p.end] == p.text
        assert p.status == "VALID"


def test_14_code_mixed_hindi_english_offsets(shared_adapter: TransformerBaselineAdapter):
    """14. Code-mixed Hindi/English offsets."""
    text = "Arre bhai Vikram Mehta se baat hui kya New Delhi mein?"
    preds = shared_adapter.predict(text)

    for p in preds:
        assert 0 <= p.start < p.end <= len(text)
        assert text[p.start : p.end] == p.text
        assert p.status == "VALID"


def test_15_prediction_validation_through_harness(shared_adapter: TransformerBaselineAdapter):
    """15. Prediction validation through validate_predictions()."""
    text = "Dr. Vikram Mehta and Priya Sharma visited Infosys headquarters in Bangalore."
    preds = shared_adapter.predict(text)

    valid, rejected = validate_predictions(preds, original_text=text)
    assert len(rejected) == 0
    assert len(valid) == len(preds)


def test_16_deterministic_repeated_output(shared_adapter: TransformerBaselineAdapter):
    """16. Deterministic repeated output."""
    text = "Sunita Rao arrived at Bengaluru airport yesterday."
    preds1 = shared_adapter.predict(text)
    preds2 = shared_adapter.predict(text)
    assert preds1 == preds2


def test_17_deterministic_sorting(shared_adapter: TransformerBaselineAdapter):
    """17. Deterministic sorting."""
    text = "Ananya Patel met Vikram Patel in Kolkata on January 15."
    preds = shared_adapter.predict(text)
    for i in range(len(preds) - 1):
        p1, p2 = preds[i], preds[i + 1]
        assert (p1.start, p1.end) <= (p2.start, p2.end)


def test_18_input_text_immutability(shared_adapter: TransformerBaselineAdapter):
    """18. Input text immutability."""
    text = "Original immutable string with Rajesh Sharma."
    text_copy = str(text)
    _ = shared_adapter.predict(text)
    assert text == text_copy


def test_19_every_offset_satisfies_text_slicing(shared_adapter: TransformerBaselineAdapter):
    """19. Every offset satisfies text[start:end] == predicted span."""
    corpus_samples = [
        "Amit Kumar visited Connaught Place in New Delhi.",
        "डॉ. Rajesh Sharma का ईमेल rajesh@example.com है।",
        "Pooja Nair lives in Koramangala, Bangalore.",
    ]
    for s in corpus_samples:
        for p in shared_adapter.predict(s):
            assert s[p.start : p.end] == p.text


def test_20_empty_clean_text_handling(shared_adapter: TransformerBaselineAdapter):
    """20. Empty/clean text handling."""
    assert shared_adapter.predict("") == []
    assert shared_adapter.predict("   \n\t  ") == []
