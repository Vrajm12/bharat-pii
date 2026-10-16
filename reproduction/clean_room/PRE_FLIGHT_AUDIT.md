# Clean-Room Reproduction — Pre-Flight Audit

**Phase**: CLEAN_ROOM_REPRODUCTION_V1
**Date**: September 9, 2026
**Audit Status**: PRE-FLIGHT VERIFIED — PROCEED

## 1. Freeze Boundary & Immutability Verification

- **Canonical Artifacts Inspected**: 22 / 22 confirmed present.
- **Cryptographic Snapshot**: Generated in `reproduction/clean_room/HASH_AUDIT_BEFORE.json`.
- **Prohibitions Acknowledged**: Zero retraining, zero parameter changes, zero B7 baseline, zero writes to canonical directories.

## 2. Reproduction Commands Protocol

The clean-room execution will execute the following explicit commands:

```bash
# B5 Clean-Room Reproduction
python scripts/reproduce_b5.py --seed 42 --device -1 --output_dir reproduction/clean_room/b5/seed42
python scripts/reproduce_b5.py --seed 43 --device -1 --output_dir reproduction/clean_room/b5/seed43
python scripts/reproduce_b5.py --seed 44 --device -1 --output_dir reproduction/clean_room/b5/seed44

# B6 Clean-Room Reproduction
python scripts/reproduce_b6.py --seed 42 --device -1 --output_dir reproduction/clean_room/b6/seed42
python scripts/reproduce_b6.py --seed 43 --device -1 --output_dir reproduction/clean_room/b6/seed43
python scripts/reproduce_b6.py --seed 44 --device -1 --output_dir reproduction/clean_room/b6/seed44
```

## 3. Pre-Flight Acceptance Checklist

- [x] Python 3.10 environment loaded and locked.
- [x] Canonical benchmark records intact (964 records, 724 gold entities).
- [x] Checkpoint directories verified for seeds 42, 43, 44.
- [x] Isolated reproduction directory initialized (`reproduction/clean_room/`).
- [x] Initial hash snapshot (`HASH_AUDIT_BEFORE.json`) recorded.
