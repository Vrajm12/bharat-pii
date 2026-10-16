# Changelog

All notable changes to the `bharatpii` library will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-12

### Added
- Initial public release of `bharatpii`, the official Python library for BharatPII-CRF.
- High-level `BharatPII` interface with `from_pretrained()`, `predict()`, and `predict_batch()`.
- Safe weight loading via `safetensors.torch.load_file` supporting unified `model.safetensors` (204 tensors).
- Exact Viterbi sequence decoding with linear-chain Conditional Random Field (CRF).
- Structured output types: `Entity` and `PredictionResult` with verified character offset slice invariants.
- Support for 8 Indian PII categories across 17 canonical IOB2 labels.
- Support for 7 language/script conditions including Indian English, Devanagari Hindi, Latin transliteration, and code-mixed Hinglish.
- Command-line interface (`bharatpii`) with `--text`, `--input`, `--output`, and `--info` flags.
- Complete offline operation with bundled SentencePiece BPE tokenizer.
- Zero-mismatch canonical parity verification against the 964-record benchmark corpus.
