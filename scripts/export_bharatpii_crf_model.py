"""Export canonical B6 model to official distributable release directory: models/bharatpii-crf-v1.0/

Combines frozen XLM-RoBERTa-base encoder weights (199 tensors) and canonical
B6 CRF head weights (5 tensors) into a single model.safetensors (204 tensors,
278,057,044 parameters), generates config.json, copies tokenizer files, creates
label_map.json, model_metadata.json, MODEL_CARD.md, and generates SHA256SUMS.txt.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
import torch
from safetensors.torch import load_file, save_file

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "models" / "bharatpii-crf-v1.0"
CHECKPOINT_B6 = REPO_ROOT / "checkpoints" / "b6" / "b6_transformer_crf_seed42"

CACHE_DIR = Path(r"C:\Users\VEERAJ\.cache\huggingface\hub\models--xlm-roberta-base\snapshots\e73636d4f797dec63c3081bb6ed5c7b0bb3f2089")

LABEL_LIST = [
    "O",
    "B-PERSON",
    "I-PERSON",
    "B-PAN",
    "I-PAN",
    "B-AADHAAR",
    "I-AADHAAR",
    "B-PHONE",
    "I-PHONE",
    "B-EMAIL",
    "I-EMAIL",
    "B-UPI_ID",
    "I-UPI_ID",
    "B-BANK_ACCOUNT",
    "I-BANK_ACCOUNT",
    "B-ADDRESS",
    "I-ADDRESS",
]
LABEL2ID = {lbl: i for i, lbl in enumerate(LABEL_LIST)}
ID2LABEL = {i: lbl for i, lbl in enumerate(LABEL_LIST)}


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def export_model():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Target directory: {OUTPUT_DIR}")

    # 1. Weights: XLM-R base + B6 CRF Head
    print("Loading base safetensors weights...")
    base_sf = CACHE_DIR / "model.safetensors"
    base_dict = load_file(base_sf)
    roberta_dict = {k: v for k, v in base_dict.items() if k.startswith("roberta.")}
    assert len(roberta_dict) == 199, f"Expected 199 roberta tensors, got {len(roberta_dict)}"

    print("Loading B6 CRF head checkpoint...")
    head_pt = CHECKPOINT_B6 / "b6_crf_head.pt"
    head_dict = torch.load(head_pt, map_location="cpu")
    assert len(head_dict) == 5, f"Expected 5 head tensors, got {len(head_dict)}"

    combined_dict = {}
    combined_dict.update(roberta_dict)
    combined_dict.update(head_dict)
    assert len(combined_dict) == 204, f"Expected 204 combined tensors, got {len(combined_dict)}"

    total_params = sum(t.numel() for t in combined_dict.values())
    encoder_params = sum(t.numel() for t in roberta_dict.values())
    head_params = sum(t.numel() for t in head_dict.values())
    print(f"Total Parameters: {total_params}")
    print(f"Encoder Parameters: {encoder_params}")
    print(f"CRF Head Parameters: {head_params}")
    assert total_params == 278057044
    assert encoder_params == 278043648
    assert head_params == 13396

    out_safetensors = OUTPUT_DIR / "model.safetensors"
    save_file(combined_dict, out_safetensors)
    print(f"Saved model.safetensors: {out_safetensors.stat().st_size} bytes")

    # 2. config.json
    config_dict = {
        "architectures": ["BharatPIICRFForTokenClassification"],
        "attention_probs_dropout_prob": 0.1,
        "bos_token_id": 0,
        "classifier_dropout": 0.1,
        "decoder": "linear-chain CRF",
        "eos_token_id": 2,
        "hidden_act": "gelu",
        "hidden_dropout_prob": 0.1,
        "hidden_size": 768,
        "id2label": ID2LABEL,
        "initializer_range": 0.02,
        "intermediate_size": 3072,
        "label2id": LABEL2ID,
        "layer_norm_eps": 1e-05,
        "max_position_embeddings": 514,
        "model_type": "xlm-roberta",
        "num_attention_heads": 12,
        "num_hidden_layers": 12,
        "num_labels": 17,
        "pad_token_id": 1,
        "position_embedding_type": "absolute",
        "torch_dtype": "float32",
        "transformers_version": "5.16.1",
        "type_vocab_size": 1,
        "use_cache": True,
        "vocab_size": 250002,
    }
    config_file = OUTPUT_DIR / "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2)
    print(f"Saved config.json: {config_file.stat().st_size} bytes")

    # 3. label_map.json
    label_map_file = OUTPUT_DIR / "label_map.json"
    with open(label_map_file, "w", encoding="utf-8") as f:
        json.dump(ID2LABEL, f, indent=2)
    print(f"Saved label_map.json: {label_map_file.stat().st_size} bytes")

    # 4. Tokenizer files
    shutil.copy2(CHECKPOINT_B6 / "tokenizer.json", OUTPUT_DIR / "tokenizer.json")
    shutil.copy2(CHECKPOINT_B6 / "tokenizer_config.json", OUTPUT_DIR / "tokenizer_config.json")
    shutil.copy2(CACHE_DIR / "sentencepiece.bpe.model", OUTPUT_DIR / "sentencepiece.bpe.model")

    special_tokens_dict = {
        "bos_token": "<s>",
        "cls_token": "<s>",
        "eos_token": "</s>",
        "mask_token": "<mask>",
        "pad_token": "<pad>",
        "sep_token": "</s>",
        "unk_token": "<unk>",
    }
    with open(OUTPUT_DIR / "special_tokens_map.json", "w", encoding="utf-8") as f:
        json.dump(special_tokens_dict, f, indent=2)
    print("Saved tokenizer files.")

    # 5. model_metadata.json
    model_metadata = {
        "model_name": "BharatPII-CRF",
        "model_version": "1.0.0",
        "system_name": "transformer_crf",
        "system_version": "5.16.1_xlm_roberta_base_indian_crf_v0.18",
        "base_model": "XLM-RoBERTa-base",
        "task": "Indian multilingual PII detection",
        "decoder": "linear-chain CRF",
        "label_scheme": "IOB2",
        "num_labels": 17,
        "pii_types": [
            "PERSON",
            "PAN",
            "AADHAAR",
            "PHONE",
            "EMAIL",
            "UPI_ID",
            "BANK_ACCOUNT",
            "ADDRESS",
        ],
        "canonical_seeds": [42, 43, 44],
        "canonical_primary_seed": 42,
        "framework": "PyTorch",
        "transformers_version": "5.16.1",
        "canonical_checkpoint_source": "checkpoints/b6/b6_transformer_crf_seed42",
        "parameters": {
            "total_parameters": 278057044,
            "trainable_parameters_b6_adaptation": 13396,
            "encoder_parameters": 278043648,
            "crf_head_parameters": 13396,
        },
        "tensor_count": 204,
        "format": "safetensors",
        "torch_dtype": "float32",
        "benchmark": {
            "n_records_evaluated": 964,
            "gold_entities": 724,
            "predictions_count": 1073,
            "tp_exact": 601,
            "tp_type": 677,
            "f1_missed": 7,
            "f2_wrong_span": 76,
            "f3_wrong_type": 40,
            "f4_false_positive": 356,
            "m1_precision": 0.6309412861136999,
            "m2_recall": 0.9350828729281768,
            "m3_type_f1": 0.753478018920423,
            "m4_exact_f1": 0.6688925987757373,
            "m5_accuracy": 0.9442119944211994,
            "m6_fpr": 0.3317800559179869,
        },
        "license": "Research Only - Academic / Derivative of XLM-RoBERTa (MIT)",
        "intended_use": "Research evaluation of Indian PII extraction and sequence-constrained decoding",
        "out_of_scope_use": "Automated standalone production redaction of sensitive citizen data without human oversight",
    }
    with open(OUTPUT_DIR / "model_metadata.json", "w", encoding="utf-8") as f:
        json.dump(model_metadata, f, indent=2)
    print("Saved model_metadata.json.")

    # 6. MODEL_CARD.md
    model_card_content = """# BharatPII-CRF Model Card

## Model Details
- **Model Name**: BharatPII-CRF
- **Model Version**: 1.0.0
- **System Name**: `transformer_crf`
- **System Version**: `5.16.1_xlm_roberta_base_indian_crf_v0.18`
- **Base Architecture**: XLM-RoBERTa-base (`xlm-roberta-base`)
- **Decoder Architecture**: Linear-chain Conditional Random Field (CRF) with Viterbi sequence decoding
- **Primary Canonical Seed**: 42 (Canonical seeds evaluated: 42, 43, 44)
- **Framework**: PyTorch (>=2.0.0), Hugging Face Transformers (5.16.1), `safetensors`
- **Format**: `safetensors` (float32)

---

## Parameter Breakdown
| Component | Tensors | Parameter Count | Trainable in B6 Adaptation | Notes |
|:---|:---:|:---:|:---:|:---|
| **Encoder (`xlm-roberta-base`)** | 199 | 278,043,648 | No (Frozen) | 12 layers, 768 hidden, 12 attention heads |
| **Linear Emission Layer** | 2 | 13,073 | Yes | 768 -> 17 classes (`weight`: 13,056, `bias`: 17) |
| **LinearChainCRF Decoder** | 3 | 323 | Yes | `transitions`: 289, `start`: 17, `end`: 17 |
| **CRF Head Subtotal** | 5 | 13,396 | Yes | Head module (`TransformerB6CRFHead`) |
| **Total Model** | **204** | **278,057,044** | **13,396** | Full model parameter set |

---

## Intended Use & Scope
- **Intended Use**: Academic and empirical evaluation of Indian PII detection, sequence-constrained decoding, and structural robustness across multilingual, code-mixed, and adversarial text.
- **Out-of-Scope Use**:
  - Direct unattended production redaction of sensitive citizen records without human-in-the-loop review.
  - Legal compliance certification (e.g., claiming automated compliance with India's DPDPA 2023).
  - High-stakes automated financial or judicial data redaction.

---

## Supported PII Categories (8 Types, 17 IOB2 Labels)
The model detects 8 Indian PII categories in IOB2 tagging format:
1. `PERSON`: Indian personal names across multiple ethnicities and naming conventions.
2. `PAN`: 10-character alphanumeric Permanent Account Number.
3. `AADHAAR`: 12-digit Indian national identity number.
4. `PHONE`: 10-digit Indian mobile and landline telephone numbers.
5. `EMAIL`: Email addresses.
6. `UPI_ID`: Unified Payments Interface Virtual Payment Addresses (VPAs).
7. `BANK_ACCOUNT`: Indian bank account numbers (9-18 digits).
8. `ADDRESS`: Indian street, locality, city, state, and PIN code physical addresses.

### Label Space
`0: O`, `1: B-PERSON`, `2: I-PERSON`, `3: B-PAN`, `4: I-PAN`, `5: B-AADHAAR`, `6: I-AADHAAR`, `7: B-PHONE`, `8: I-PHONE`, `9: B-EMAIL`, `10: I-EMAIL`, `11: B-UPI_ID`, `12: I-UPI_ID`, `13: B-BANK_ACCOUNT`, `14: I-BANK_ACCOUNT`, `15: B-ADDRESS`, `16: I-ADDRESS`.

---

## Supported Linguistic & Script Coverage
Evaluated across 7 language/script variants established in the canonical benchmark:
1. `EN`: Indian English formal.
2. `IN_EN`: Indian English bureaucratic and regional phrasing.
3. `HI_LATIN_PII`: Hindi written in Latin script with transliterated PII.
4. `HI_DEVA_PII`: Hindi written in Devanagari script with Devanagari-script PII.
5. `ROM_HI`: Romanized colloquial Hindi.
6. `HINGLISH`: Code-switched Hindi-English.
7. `INFORMAL_HINGLISH`: Informal conversational Hinglish with SMS abbreviations.

---

## Canonical Benchmark Performance (Seed 42 / v0.18)
Evaluated against the frozen 964-record canonical benchmark corpus (724 gold entities, 140 non-PII hard-negative decoy instances):
- **Exact Precision ($M_1$)**: 63.09%
- **Exact Recall ($M_2$)**: 93.51%
- **Type-Strict $F_1$ ($M_3$)**: 75.35%
- **Exact-Span $F_1$ ($M_4$)**: 66.89%
- **Instance Accuracy ($M_5$)**: 94.42%
- **False Positive Rate ($M_6$)**: 33.18%
- **Error Partition Breakdown**:
  - $TP_{\text{exact}}$: 601
  - $F_1$ (missed entities): 7
  - $F_2$ (boundary/span errors): 76
  - $F_3$ (type confusion): 40
  - $F_4$ (spurious false positives): 356
  - Invariant: $TP_{\text{exact}} + F_1 + F_2 + F_3 = 601 + 7 + 76 + 40 = 724$.

---

## Failure Modes & Limitations
1. **False Positives on Decoys ($F_4 = 356$)**: The high recall objective ($93.51\%$) results in over-triggering on contextually ambiguous alphanumeric strings (e.g., transaction references resembling account numbers or PANs).
2. **Boundary Precision ($F_2 = 76$)**: While CRF decoding reduces span fragmentation compared to unconstrained softmax ($F_2$ reduced from 243 in B5 to 76 in B6), multi-token addresses and romanized names with honorifics still experience boundary shifts.
3. **Synthetic Training Distribution**: Trained on rule-synthesized Indic contexts and hard negatives. Real-world noisy scans, OCR degradation, or heavy vernacular slang may induce out-of-distribution degradation.

---

## Output Contract
Inference produces span predictions with exact native Python Unicode slice indices:
`text[start:end] == predicted_text`
Each entity dictionary contains:
- `text`: Extracted entity substring.
- `start`: 0-indexed start character offset in raw text.
- `end`: 0-indexed end character offset (exclusive).
- `type`: Entity label (`PERSON`, `PAN`, etc.).
- `confidence`: Average token-level emission probability across the entity span (note: this is token emission confidence, not calibrated sequence posterior).

---

## Governance & Safety Notice
This model artifact is part of a research reproduction suite. No actual citizen PII was used in the training or evaluation of this model; all benchmark and adaptation data consists of synthetically generated instances adhering to Indian syntactic specifications and anonymized templates.
"""
    with open(OUTPUT_DIR / "MODEL_CARD.md", "w", encoding="utf-8") as f:
        f.write(model_card_content)
    print("Saved MODEL_CARD.md.")

    # 7. SHA256SUMS.txt
    print("Generating SHA256SUMS.txt...")
    manifest_lines = []
    for file_path in sorted(OUTPUT_DIR.iterdir()):
        if file_path.name == "SHA256SUMS.txt":
            continue
        sha = compute_sha256(file_path)
        manifest_lines.append(f"{sha}  {file_path.name}")

    manifest_content = "\n".join(manifest_lines) + "\n"
    with open(OUTPUT_DIR / "SHA256SUMS.txt", "w", encoding="utf-8") as f:
        f.write(manifest_content)
    print("Saved SHA256SUMS.txt.")
    print("Export completed successfully!")


if __name__ == "__main__":
    export_model()
