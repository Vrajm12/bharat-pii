"""Verify canonical file hashes before and after PAPER_PACKAGE_V1_REVIEW phase."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEFORE_PATH = ROOT / "reports/paper_package/HASH_SNAPSHOT_BEFORE.json"
AFTER_PATH = ROOT / "reports/paper_package/HASH_SNAPSHOT_AFTER.json"


def main():
    print("=" * 75)
    print("   CANONICAL ARTIFACT CRYPTOGRAPHIC INTEGRITY AUDIT")
    print("=" * 75)

    with open(BEFORE_PATH, "r", encoding="utf-8") as f:
        before_payload = json.load(f)

    before_artifacts = before_payload["artifacts"]
    after_artifacts = {}
    all_match = True
    mismatches = []

    for rel_path, expected_info in before_artifacts.items():
        file_path = ROOT / rel_path
        if not file_path.exists():
            print(f"FAILED (MISSING): {rel_path}")
            all_match = False
            mismatches.append((rel_path, "MISSING", expected_info))
            continue

        content = file_path.read_bytes()
        actual_size = len(content)
        actual_md5 = hashlib.md5(content).hexdigest()
        actual_sha256 = hashlib.sha256(content).hexdigest()

        after_artifacts[rel_path] = {
            "size_bytes": actual_size,
            "md5": actual_md5,
            "sha256": actual_sha256,
        }

        size_match = (actual_size == expected_info["size_bytes"])
        md5_match = (actual_md5 == expected_info["md5"])
        sha256_match = (actual_sha256 == expected_info["sha256"])

        if size_match and md5_match and sha256_match:
            print(f"MATCH: {rel_path} ({actual_size} bytes, SHA256: {actual_sha256[:12]}...)")
        else:
            print(f"FAILED (HASH MISMATCH): {rel_path}")
            print(f"  Expected: {expected_info}")
            print(f"  Actual:   {after_artifacts[rel_path]}")
            all_match = False
            mismatches.append((rel_path, "HASH_MISMATCH", after_artifacts[rel_path]))

    after_payload = {
        "audit_phase": "PAPER_PACKAGE_POST_FLIGHT",
        "total_canonical_artifacts": len(after_artifacts),
        "all_match": all_match,
        "artifacts": after_artifacts,
    }

    with open(AFTER_PATH, "w", encoding="utf-8") as f:
        json.dump(after_payload, f, indent=2)

    print("=" * 75)
    if all_match:
        print("VERDICT: PASS — 100% BITWISE CANONICAL REPOSITORY INTEGRITY PRESERVED")
        print(f"Total Canonical Files Audited: {len(after_artifacts)} / {len(before_artifacts)}")
        print(f"Snapshot written to: {AFTER_PATH}")
    else:
        print("VERDICT: FAIL — CANONICAL FILE DRIFT DETECTED!")
        print(f"Mismatches: {len(mismatches)}")
        for m in mismatches:
            print(f"  - {m}")
    print("=" * 75)

    if not all_match:
        raise RuntimeError("Canonical file hash check failed!")


if __name__ == "__main__":
    main()
