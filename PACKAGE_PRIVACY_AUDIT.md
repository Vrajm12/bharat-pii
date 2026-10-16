# Package Privacy and Security Audit: BharatPII

**Package Name**: `bharatpii` (v1.0.0)  
**Date**: 2026-09-12  
**Audit Status**: PASS  

---

## 1. Executive Summary
This audit inspects the `bharatpii` library and built distribution artifacts for privacy risks, telemetry, unintended data leaks, credentials, and network behavior.

---

## 2. Telemetry and Network Call Verification
- **Network Requests**: The package performs **zero** HTTP, HTTPS, gRPC, or socket connections during import, initialization, inference, or batch processing.
- **Local / Offline Guarantee**: The model loader `BharatPII.from_pretrained(model_path)` explicitly operates on local paths with `local_files_only=True` for the tokenizer and direct file loading for `model.safetensors`.
- **Telemetry**: Zero tracking analytics, telemetry beacons, user analytics, or usage counters exist in the codebase.

---

## 3. Data Logging & Privacy Policies
- **Input Text Logging**: Input strings are never logged to console, disk, syslog, or external sinks by default.
- **CLI Behavior**: The CLI prints output strictly to `stdout` or the user-specified `--output` file. No hidden audit or debug logs are persisted.
- **Error Messages**: Exception messages report structural errors (missing keys, offset mismatches, missing files) without printing raw input texts.

---

## 4. Wheel Content & Leakage Inspection
The wheel artifact `dist/bharatpii-1.0.0-py3-none-any.whl` (15,029 bytes) was extracted and audited:
- **No Benchmark Data**: Zero `.jsonl`, `.csv`, or gold entity annotations are bundled inside the wheel.
- **No Test Data**: Unit test corpora, gold test instances, and adversarial realizations are excluded via package discovery filters.
- **No Model Weights**: The 1.11 GB model weights are distributed separately; no weights are embedded in the wheel.
- **No Credentials / Keys**: Grep audit across all package sources confirms zero API keys, tokens, passwords, or personal credentials.

---

## 5. Training & Benchmark Data Privacy
- **Synthetic Data**: All data used to train and benchmark the underlying model (`BharatPII-CRF`) was synthetically generated using rule-based grammars, anonymized gazetteers, and algorithmic checksum validators (Verhoeff, Luhn).
- **No Real Citizen Data**: Zero real citizen Aadhaar, PAN, bank account, or phone records were utilized at any stage.

---

## 6. Audit Verdict
**STATUS: PASS**  
The `bharatpii` library satisfies all local inference, privacy preservation, and software security requirements.
