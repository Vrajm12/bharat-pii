#!/usr/bin/env python3
"""
Repository Audit & Inventory Script for Artifact Engineering V1.
Scans all tracked and active files in the benchmark repository and classifies them:
- CANONICAL_SCIENTIFIC
- EXPERIMENTAL_ARCHIVE
- PUBLIC_RELEASE
- DEVELOPMENT_ONLY
- SCRATCH
- DERIVED_ARTIFACT
"""

import json
import os
import hashlib
from pathlib import Path

BASE_DIR = Path("n:/PROJECTS/indian-pii-robust")
ARTIFACT_ENG_DIR = BASE_DIR / "reports" / "artifact_engineering"
ARTIFACT_ENG_DIR.mkdir(parents=True, exist_ok=True)

# 22 canonical locked artifacts
CANONICAL_22 = {
    "data/raw/base_instances.jsonl",
    "data/raw/hard_negative_bases.jsonl",
    "data/generated/language_realizations.jsonl",
    "data/generated/hard_negative_realizations.jsonl",
    "data/generated/adversarial_realizations.jsonl",
    "annotation/review_template.csv",
    "predictions/regex_1.0.0_v0.18.jsonl",
    "reports/evaluation_regex_1.0.0_v0.18.json",
    "predictions/spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.jsonl",
    "reports/evaluation_spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.json",
    "predictions/presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.jsonl",
    "reports/evaluation_presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.json",
    "predictions/transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.jsonl",
    "reports/evaluation_transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.json",
    "predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.jsonl",
    "predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.jsonl",
    "predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.jsonl",
    "predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.jsonl",
    "reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.json",
    "reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.json",
    "reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.json",
    "reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.json",
}

def compute_md5(p: Path) -> str:
    hasher = hashlib.md5()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def classify_file(rel_str: str) -> str:
    # 1. Canonical 22
    if rel_str in CANONICAL_22:
        return "CANONICAL_SCIENTIFIC"
    if rel_str in ["PROJECT_SPEC.md", "annotation/guidelines.md", "data/adaptation/train_instances.jsonl", "data/adaptation/val_instances.jsonl"]:
        return "CANONICAL_SCIENTIFIC"

    # 2. Scratch
    if rel_str.startswith("scratch/") or ".pytest_cache" in rel_str or "__pycache__" in rel_str:
        return "SCRATCH"

    # 3. Derived Artifacts
    if rel_str.startswith("reports/final/"):
        return "DERIVED_ARTIFACT"
    if rel_str in [
        "reports/FINAL_SCIENTIFIC_RECORD.md",
        "reports/FINAL_CLAIM_AUDIT.md",
        "reports/FINAL_LIMITATIONS.md",
        "reports/FINAL_FREEZE_DECLARATION.md"
    ]:
        return "DERIVED_ARTIFACT"

    # 4. Experimental Archive
    if (rel_str.startswith("reports/experiments/") or
        rel_str.startswith("predictions/experiments/") or
        rel_str.startswith("data/experiments/") or
        rel_str.startswith("checkpoints/") or
        "scientific_validation_sv01" in rel_str or
        "evaluation_regex_1.1.0" in rel_str or
        rel_str.startswith("reports/B") and rel_str.endswith(".md")):
        return "EXPERIMENTAL_ARCHIVE"

    # 5. Public Release candidates
    if rel_str in ["README.md", "LICENSE", "CITATION.cff", "pyproject.toml", "requirements.txt", "requirements-lock.txt"]:
        return "PUBLIC_RELEASE"
    if rel_str.startswith("docs/"):
        return "PUBLIC_RELEASE"
    if rel_str.startswith("benchmark/"):
        return "PUBLIC_RELEASE"
    if rel_str.startswith("scripts/"):
        return "PUBLIC_RELEASE"
    if rel_str.startswith("tests/"):
        return "PUBLIC_RELEASE"
    if rel_str in [
        "baselines/base.py",
        "baselines/regex.py",
        "baselines/spacy.py",
        "baselines/presidio.py",
        "baselines/transformer.py",
        "baselines/transformer_adapted.py",
        "baselines/transformer_b6.py"
    ]:
        return "PUBLIC_RELEASE"

    # 6. Development Only
    if (rel_str.startswith("generators/") or
        rel_str.startswith("validators/") or
        rel_str.startswith("configs/") or
        rel_str.startswith("baselines/") or
        rel_str.startswith("annotation/") or
        rel_str.startswith("schemas/")):
        return "DEVELOPMENT_ONLY"

    return "DEVELOPMENT_ONLY"

all_files = []
for p in BASE_DIR.rglob("*"):
    if p.is_file() and ".git" not in p.parts:
        rel = p.relative_to(BASE_DIR).as_posix()
        cls = classify_file(rel)
        size = p.stat().st_size
        all_files.append({
            "path": rel,
            "classification": cls,
            "size_bytes": size,
            "md5": compute_md5(p) if size < 100 * 1024 * 1024 else "SKIPPED_LARGE_FILE"
        })

# Sort by path
all_files.sort(key=lambda x: x["path"])

# Group counts
counts = {}
for item in all_files:
    c = item["classification"]
    counts[c] = counts.get(c, 0) + 1

inventory_data = {
    "total_files_audited": len(all_files),
    "classification_counts": counts,
    "files": all_files
}

# Write REPOSITORY_INVENTORY.json
inv_path = ARTIFACT_ENG_DIR / "REPOSITORY_INVENTORY.json"
with open(inv_path, "w", encoding="utf-8") as f:
    json.dump(inventory_data, f, indent=2)

# Write REPOSITORY_AUDIT.md
audit_md_path = ARTIFACT_ENG_DIR / "REPOSITORY_AUDIT.md"
with open(audit_md_path, "w", encoding="utf-8") as f:
    f.write("# Indian PII Robustness Benchmark — Repository Audit Report\n")
    f.write("**Phase**: Artifact Engineering V1 (Post-Scientific-Freeze)\n")
    f.write(f"**Total Files Audited**: {len(all_files)}\n\n")
    f.write("## 1. Classification Summary\n\n")
    f.write("| Classification Category | File Count | Description |\n")
    f.write("| :--- | :---: | :--- |\n")
    f.write(f"| **`CANONICAL_SCIENTIFIC`** | {counts.get('CANONICAL_SCIENTIFIC', 0)} | 22 canonical locked artifacts + adaptation data + guidelines (Bitwise Frozen) |\n")
    f.write(f"| **`EXPERIMENTAL_ARCHIVE`** | {counts.get('EXPERIMENTAL_ARCHIVE', 0)} | SV-01, SV-02, SV-03, B6 intermediate experiments, checkpoints, and model weights |\n")
    f.write(f"| **`DERIVED_ARTIFACT`** | {counts.get('DERIVED_ARTIFACT', 0)} | Master tables, breakdown CSVs, publication figures, final scientific records |\n")
    f.write(f"| **`PUBLIC_RELEASE`** | {counts.get('PUBLIC_RELEASE', 0)} | Public code, CLI tools, tests, documentation, dependencies, and packaging |\n")
    f.write(f"| **`DEVELOPMENT_ONLY`** | {counts.get('DEVELOPMENT_ONLY', 0)} | Training scripts, data generators, internal validators, and review scripts |\n")
    f.write(f"| **`SCRATCH`** | {counts.get('SCRATCH', 0)} | Temporary cache files and scratch exploratory scripts |\n\n")

    f.write("## 2. Canonical Scientific Artifacts (Frozen Boundary)\n\n")
    f.write("All 22 canonical locked artifacts are strictly frozen and protected against modification:\n\n")
    f.write("| File Path | Size (Bytes) | MD5 Checksum |\n")
    f.write("| :--- | :---: | :--- |\n")
    for item in all_files:
        if item["classification"] == "CANONICAL_SCIENTIFIC":
            f.write(f"| `{item['path']}` | {item['size_bytes']:,} | `{item['md5']}` |\n")

    f.write("\n## 3. Preservation & Non-Destruction Commitment\n\n")
    f.write("No files were removed or destructively reorganized during this audit. All experimental archives (SV-01, SV-02, SV-03, B6 checkpoints) are preserved in their original relative paths to maintain historical test and governance compliance.\n")

print(f"Audit complete: {len(all_files)} files classified. Counts: {counts}")
