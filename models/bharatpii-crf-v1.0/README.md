# BharatPII-CRF v1.0 Model Directory

This directory contains configuration, vocabulary, tokenizer assets, and integrity checksums for the `BharatPII-CRF` release model.

## Model Files Inventory
- `config.json`: XLM-RoBERTa encoder and CRF head model architecture configuration.
- `label_map.json`: 17-class IOB2 tag mapping for 8 Indian PII categories.
- `model_metadata.json`: Model version, training parameters, parameter accounting, and benchmark performance metrics.
- `MODEL_CARD.md`: Comprehensive model card documenting architectural details, training regime, parameter counts, and intended use.
- `tokenizer.json`: Pre-trained Hugging Face fast tokenizer definition.
- `sentencepiece.bpe.model`: SentencePiece vocabulary and BPE model.
- `tokenizer_config.json`: Tokenizer configuration and special token mappings.
- `special_tokens_map.json`: Special tokens definition.
- `SHA256SUMS.txt`: Authoritative cryptographic SHA-256 checksums for all release artifacts.

## Note on Model Weights (`model.safetensors`)
In accordance with package design and repository storage practices, model weights (`model.safetensors`, ~1.11 GB) are distributed separately from the source code repository.

To run offline inference locally:
1. Place `model.safetensors` into this directory (`models/bharatpii-crf-v1.0/model.safetensors`).
2. Verify file integrity using `SHA256SUMS.txt`:
   ```bash
   # Linux / macOS
   sha256sum -c SHA256SUMS.txt
   
   # Windows (PowerShell)
   Get-FileHash models/bharatpii-crf-v1.0/model.safetensors -Algorithm SHA256
   # Expected: 2b2196763d59a179786dcb2a5772a73786261dd14203ae84d24e2c8f9d52463c
   ```
3. Initialize the model in Python:
   ```python
   from bharatpii import BharatPII
   model = BharatPII.from_pretrained("models/bharatpii-crf-v1.0", verify_checksums=True)
   ```
