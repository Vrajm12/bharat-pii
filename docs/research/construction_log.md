# Benchmark Construction Research Log

## Purpose

This document is the provenance record for the construction of the Indian PII
Robustness Benchmark's Pilot v0.1, covering task T01 through the current T10
governance-and-implementation state. It exists to support three things a
research paper eventually needs and a chat transcript cannot provide on its
own: **reproducibility** (what was generated, under which seed, from which
frozen rule, in which order), **auditability** (which decisions were made
deliberately versus inferred, and on what evidence), and **methodology**
(the construction process itself — specification-gated generation, fail-closed
validation, deterministic transliteration — is a paper-relevant property of
this benchmark, not just an implementation detail).

This log is a documentation-only artifact. It does not modify, regenerate, or
reinterpret any code, schema, dataset, guideline, or test file. Where a claim
below could not be independently confirmed from repository evidence, it is
marked as such rather than presented as fact.

### Note on evidence basis (read before trusting any specific number below)

`git log --oneline --all` currently shows exactly two commits:

```
f03fed2 T02: record schemas
fcdcbf5 T01: repository skeleton
```

Every task from **T03 onward exists only as uncommitted working-tree changes
and untracked files** — there is no git commit boundary per task, and `git
status` shows the entire T03–T10 body of work as modified/untracked against
the T02 commit. This means:

- File **existence and current content** (generators, validators, tests,
  schemas, `annotation/guidelines.md`, `annotation/CHANGELOG.md`,
  `annotation/open_questions.md`, `data/raw/*.jsonl`,
  `data/generated/*.jsonl`) is directly verifiable from the filesystem today,
  and is treated as primary evidence throughout this log.
- **Per-task cumulative test counts at the historical moment each task was
  declared complete** (e.g. "183 tests after T05," "386 after T09") are not
  independently re-derivable from git, because no commit exists at those
  moments. Where such figures appear below, they are drawn from this
  project's own session records (the CHANGELOG/open-questions narrative and
  prior validation reports written *during* construction), not from a git
  diff against a prior tagged state. They are flagged as session-narrative
  figures, distinct from the counts in the "Reproducibility Summary," which
  are re-verified against the repository as it exists right now.
- `annotation/CHANGELOG.md` and `annotation/open_questions.md` **are**
  contemporaneous, incrementally-written documents (each version/OQ entry was
  added at the time of its own resolution, per this project's governance
  protocol) and are treated as strong evidence for decision chronology, even
  though they are not git-committed.

## Current State

As of this document's creation:

| Metric | Value | Verified |
|---|---|---|
| Base instances (`data/raw/base_instances.jsonl`) | 100 | yes — line count |
| Derived language-realization records (`data/generated/language_realizations.jsonl`) | 624 | yes — line count |
| Combined base + derived record count | 724 | yes — 100 + 624 |
| `annotation/guidelines.md` version | v0.13 | yes — §22 |
| `PROJECT_SPEC.md` version | v1.2 | yes — header, §35 |
| Total passing tests (`pytest -q`, full repo) | 514 | yes — run twice, identical, this session |
| T01–T09 | complete | yes — files + CHANGELOG entries exist |
| T10 governance (OQ-035, OQ-036, OQ-037) | complete | yes — guidelines.md §13.5–§13.7, all three OQs marked RESOLVED |
| T10 implementation (`validators/semantic.py`) | complete | yes — file exists, 98 passing tests, 624/624 records validate with 0 issues |
| Evaluation/baseline layer (`benchmark/`, `baselines/`, M1–M6) | **not authorized, not built** | confirmed — no such directories exist; OQ-034 explicitly found this out of scope for Pilot v0.1 |
| Language (Layer 4), duplicate, and human-review validators | **not built** | confirmed — no such files exist |

**Correction against this document's own request text:** the request that
produced this log stated the current state as "T10 semantic implementation
not yet completed" and "416 tests after OQ-037 governance resolution." Neither
matches the repository as it exists now: `validators/semantic.py` and
`tests/test_semantic_validator.py` exist, and the full suite currently passes
**514** tests (416 + 98 new). This discrepancy is reported here rather than
silently resolved, per this document's own instructions: the request text
describes the state as of the end of the OQ-037 governance turn; the T10
semantic validator was implemented in the session turn immediately after
that, before this construction log was requested.

---

## T01 — Repository Skeleton

1. **Task identifier and title:** T01 — repository skeleton.
2. **Objective:** create the directory layout PROJECT_SPEC.md §58 specifies, and write `configs/pilot.yaml` per §59.
3. **Governing specification at that point:** `annotation/guidelines.md` v0.1 (frozen, no prior revisions), `PROJECT_SPEC.md` (initial version).
4. **Inputs/dependencies:** none — first task.
5. **Investigation performed:** guidelines.md §4.2 was found to already specify **seven** language realizations, superseding PROJECT_SPEC.md's older six-condition list — the spec was read as predating that revision, per governing-document authority order (guidelines.md > PROJECT_SPEC.md).
6. **Open questions encountered:** none logged at this stage.
7. **Decisions made:** use the seven-realization list from guidelines.md, not PROJECT_SPEC.md's six, in `configs/pilot.yaml`.
8. **Guideline/PROJECT_SPEC version affected:** none bumped; v0.1/initial baseline.
9. **Files created:** repository directory skeleton per §58; `configs/pilot.yaml`.
10. **Files modified:** none (first commit).
11. **Files explicitly left untouched:** schemas, generators, data — explicitly out of scope for T01.
12. **Dataset impact:** none.
13. **Tests added:** none.
14. **Test counts/results:** n/a.
15. **Independent validation performed:** none applicable at this stage.
16. **Determinism/reproducibility evidence:** n/a — no generation yet.
17. **Preserved/superseded artifacts:** none.
18. **Known limitations:** none recorded.
19. **Why the task was considered complete:** directory skeleton and config matched §58/§59 exactly, per explicit scope instruction to create nothing beyond that.
20. **What became unblocked afterward:** T02 (schemas).

**Git evidence:** commit `fcdcbf5 T01: repository skeleton`.

---

## T02 — Record Schemas

1. **Task identifier and title:** T02 — `schemas/base_instance.schema.json` and `schemas/example.schema.json` (JSON Schema draft 2020-12).
2. **Objective:** define the structural schemas for base instances and derived records; create `annotation/open_questions.md` and `annotation/CHANGELOG.md`.
3. **Governing specification:** guidelines.md v0.1, PROJECT_SPEC.md §12–§17 (record schema).
4. **Inputs/dependencies:** T01's skeleton.
5. **Investigation performed:** cross-referenced PROJECT_SPEC.md's `validation{}` object (§15, six validation layers including "5 Duplicate") against guidelines.md §17's v0.1 worked example, which showed only five `validation{}` keys — a genuine discrepancy between the two governing documents.
6. **Open questions encountered:** **OQ-001** (`validation{}`: 5 or 6 keys?), **OQ-002** (do hard-negative bases use `base_instance.schema.json`?) — both logged rather than resolved silently, per this project's founding rule (CLAUDE.md §3: do not pick the sensible option and continue).
7. **Decisions made (this task):** schemas built with the schema's scope explicitly limited to *structure*, not cross-field logic — a rule that persisted through every later validator (`base_kind`, spans, semantic).
8. **Guideline/PROJECT_SPEC version affected:** none yet — OQ-001/002 resolved in later versions (v0.2, v0.3).
9. **Files created:** `schemas/base_instance.schema.json`, `schemas/example.schema.json`, `annotation/open_questions.md` (header only), `annotation/CHANGELOG.md` (v0.1 entry: "guidelines v0.1 frozen").
10. **Files modified:** none besides the two schema files' own creation.
11. **Files explicitly left untouched:** generators, validators, data.
12. **Dataset impact:** none — no base instances exist yet.
13. **Tests added:** `tests/test_schemas.py` (4 tests, current pytest collection).
14. **Test counts/results:** 4 tests, all passing (verified today).
15. **Independent validation performed:** none beyond schema self-consistency at this stage.
16. **Determinism/reproducibility evidence:** n/a — no generation yet.
17. **Preserved/superseded artifacts:** none.
18. **Known limitations:** OQ-001 and OQ-002 open at task close — explicitly reported as evidence, not resolved, per instruction ("report evidence only, do not resolve" for this turn).
19. **Why the task was considered complete:** both schemas written to spec; the two discovered discrepancies were logged, not silently patched.
20. **What became unblocked afterward:** OQ-001/OQ-002/OQ-003 resolution (v0.2, v0.3), then T03.

**Git evidence:** commit `f03fed2 T02: record schemas` — the last commit in the repository's git history. All subsequent work (T03–T10) is uncommitted.

---

## T03 — Eight PII Generators

1. **Task identifier and title:** T03 — deterministic generators for the eight PII taxonomy types.
2. **Objective:** implement `generators/pii/{person,address,phone,email,pan,aadhaar,bank_account,upi_id}.py`, each `generate_X(rng: random.Random) -> GeneratedPII`, no global randomness.
3. **Governing specification:** guidelines.md §5–§11 (per-type definitions), PROJECT_SPEC.md §7 (taxonomy).
4. **Inputs/dependencies:** T02's schemas (for shape conformance).
5. **Investigation performed:** for AADHAAR, BANK_ACCOUNT, UPI_ID, neither governing document specified a concrete digit count, format, or grammar — confirmed by direct reading of §4.3/§7/§10/§11, which gave only placeholder-style worked examples, never a concrete synthetic value or explicit rule.
6. **Open questions encountered:** **OQ-004** (AADHAAR format unspecified), **OQ-005** (BANK_ACCOUNT format unspecified), **OQ-006** (UPI_ID domain/grammar unspecified, unlike EMAIL which already had a `.test`/`.invalid`/`.example` rule).
7. **Decisions made:** AADHAAR and BANK_ACCOUNT frozen as **BENCHMARK_SYNTHETIC** — 12 uniform-random decimal digits each, explicitly not claimed as the official/universal real-world format (guidelines.md §11.4, decision 17, v0.4). UPI_ID frozen to one fixed grammar — `<10-digit-synthetic-phone>@mail.test`, "Grammar 3" of three candidates the user was shown, chosen specifically because it creates a controlled EMAIL-shape collision by design (guidelines.md §10.3, decision 18, v0.5).
8. **Guideline/PROJECT_SPEC version affected:** v0.4 (OQ-004, OQ-005), v0.5 (OQ-006 — the version bump for this entry was authorized as a narrow version-reference fix from v0.3, per the CHANGELOG's own note).
9. **Files created:** `generators/pii/__init__.py`, `_common.py`, `person.py`, `address.py`, `phone.py`, `email.py`, `pan.py`, `aadhaar.py`, `bank_account.py`, `upi_id.py`.
10. **Files modified:** `annotation/guidelines.md` (§11.4, §10.3), `annotation/CHANGELOG.md`, `annotation/open_questions.md`, `PROJECT_SPEC.md`/`configs/pilot.yaml` version pointers.
11. **Files explicitly left untouched:** schemas (no schema change was required by any of OQ-004/005/006's resolutions), `data/` (no base instances existed yet).
12. **Dataset impact:** none — T03 produces generator functions only, not records.
13. **Tests added:** `tests/test_generator_person.py` (5), `test_generator_address.py` (5), `test_generator_phone.py` (5), `test_generator_email.py` (6), `test_generator_pan.py` (5), `test_generator_aadhaar.py` (5), `test_generator_bank_account.py` (4), `test_generator_upi_id.py` (8), `test_generators_common.py` (35, shared parametrized checks: `base_kind`/`base_id` independence, determinism, return shape, across all 8 generators).
14. **Test counts/results:** 78 tests total for T03 (5+5+5+6+5+5+4+8+35), all passing (verified today via `pytest --collect-only` per file, summed and cross-checked against the full-suite total).
15. **Independent validation performed:** `tests/test_generators_common.py`'s shared parametrized suite independently re-runs the same invariants (determinism, no `base_kind`/`base_id` parameters) across all eight generators rather than trusting each generator's own bespoke tests alone.
16. **Determinism/reproducibility evidence:** every generator takes an explicit `random.Random` instance, never the global `random` module — verified by the shared test suite's determinism checks (same seed → identical output).
17. **Preserved/superseded artifacts:** none at this task boundary.
18. **Known limitations:** AADHAAR/BANK_ACCOUNT carry no checksum or issuance-range validation (explicitly out of scope, not an oversight — stated directly in guidelines.md §11.4). UPI_ID's local part is phone-shaped but is never a real phone number.
19. **Why the task was considered complete:** all eight generators implemented, all three blocking format ambiguities (OQ-004/005/006) resolved by explicit user decision rather than inferred, "T03 is now complete: all 8 generators implemented" per `annotation/CHANGELOG.md`'s own v0.5 entry.
20. **What became unblocked afterward:** T04 (100 base instances).

---

## T04 — 100 Base Instances (including the OQ-007 regeneration)

1. **Task identifier and title:** T04 — generate exactly 100 positive base instances.
2. **Objective:** produce `data/raw/base_instances.jsonl` per PROJECT_SPEC.md §12.2's per-type quota (PERSON 12, ADDRESS 12, PHONE 12, EMAIL 12, PAN 13, AADHAAR 13, UPI_ID 13, BANK_ACCOUNT 13 = 100).
3. **Governing specification:** guidelines.md v0.6 at generation time (post OQ-007's resolution — see below), PROJECT_SPEC.md §12.1–§12.3.
4. **Inputs/dependencies:** T03's eight generators.
5. **Investigation performed:** a full manual data-review pass across all 100 generated records cross-tabulated `pii_type × semantic_role × domain × purpose` for semantic plausibility, prior to declaring the task done. This surfaced a genuine design weakness: PERSON's originally-approved role, `ACCOUNT_HOLDER_NAME`, read as false for `employment_hr`/`healthcare_administration`/`general_conversation` domains (9 of 12 PERSON records) — the name is not always an account holder.
6. **Open questions encountered:** **OQ-007** (`semantic_role` type-fixed, but PERSON's specific value read as domain-implausible for most of its own domain distribution).
7. **Decisions made:** `semantic_role["PERSON"]` changed from `ACCOUNT_HOLDER_NAME` to **`PERSON_NAME`** — domain-neutral, chosen over making the role vary by domain (which would have broken the "type-fixed" principle) or accepting the mismatch as pilot looseness.
8. **Guideline/PROJECT_SPEC version affected:** v0.6 (new §13.5, decision 19).
9. **Files created:** `generators/base_instances.py`, `data/raw/base_instances.jsonl` (the working dataset, regenerated — see below), `data/raw/README.md`.
10. **Files modified:** `annotation/guidelines.md` (§13.5), CHANGELOG, open_questions.md.
11. **Files explicitly left untouched:** T03's generator files (the PII generators themselves were not changed — only `generators/base_instances.py`'s `SEMANTIC_ROLE` mapping).
12. **Dataset impact — major milestone, in order:**
    - **T04 initial generation:** 100 base instances generated with `SEMANTIC_ROLE["PERSON"] = "ACCOUNT_HOLDER_NAME"`.
    - **Preservation, not overwrite:** on discovering OQ-007, the pre-fix dataset was moved aside as `data/raw/base_instances.pre_oq007.jsonl` rather than deleted — per this project's "never overwrite a dataset silently" rule (CLAUDE.md §6).
    - **Regenerated T04 dataset:** all 100 base instances regenerated with `PERSON_NAME`, written to `data/raw/base_instances.jsonl`.
    - (A second preservation event, `data/raw/base_instances.pre_t07.jsonl`, belongs to T07 below, not T04 — see that section.)
13. **Tests added:** `tests/test_generate_base_instances.py` (17 tests).
14. **Test counts/results:** 17 tests, all passing (verified today).
15. **Independent validation performed:** the manual cross-tabulation review described above (role/domain/purpose plausibility across all 100 records) is itself a form of independent, non-mechanical validation distinct from schema/generator unit tests — it is what surfaced OQ-007 in the first place.
16. **Determinism/reproducibility evidence:** seed 42, fixed per-type quota, deterministic generator composition — `assert_dataset_valid()` re-checked after regeneration.
17. **Preserved/superseded artifacts:** `data/raw/base_instances.pre_oq007.jsonl` (superseded, preserved, documented in `data/raw/README.md`).
18. **Known limitations:** the uniqueness/hygiene rule for base values is generator-level, not independently re-validated by a separate uniqueness validator module.
19. **Why the task was considered complete:** exactly 100 POSITIVE, single-PII base instances generated, passing `assert_dataset_valid`, with the one semantic weakness found by manual review (OQ-007) resolved and the dataset regenerated rather than left inconsistent with the newly-frozen rule.
20. **What became unblocked afterward:** T05 (structural validator), and later T07 (transliteration, which required a second regeneration of the same file — see next section).

---

## T05 — Structural Validator (Layer 1)

1. **Task identifier and title:** T05 — `validators/structural.py`, Layer 1 (format) validation.
2. **Objective:** implement `validate_base_instance_structural()` and `check_structural_value()` against frozen per-type regexes, independent of the generators (proved via mock-based testing, per the design report's own architecture decision).
3. **Governing specification:** guidelines.md v0.6 at design time.
4. **Inputs/dependencies:** T03's generators (for what shapes need validating), T04's dataset (for what to run it against).
5. **Investigation performed:** PHONE, EMAIL, PAN, and the EMAIL/UPI_ID domain-case-sensitivity question were all found to lack an explicit frozen structural rule strong enough to hard-code a validator against — each type's "format" existed only as a worked example, never a stated regex/grammar.
6. **Open questions encountered:** **OQ-008** (PHONE base representation unfrozen), **OQ-009** (EMAIL local-part format unconstrained), **OQ-010** (PAN casing unspecified), **OQ-011** (EMAIL/UPI_ID domain case sensitivity, and the honesty of UPI_ID's stated failure reasoning).
7. **Decisions made:** PHONE frozen to `^[6789][0-9]{9}$` (§8.1); EMAIL frozen to exactly one `@`, non-empty local part, domain ending in exact-lowercase `.test`/`.invalid`/`.example` (§9.1); PAN frozen to uppercase-only `^[A-Z]{5}[0-9]{4}[A-Z]$` (§11.5); reserved domains matched as exact lowercase strings, never normalized, and UPI_ID structural failure is framed as "fails the frozen grammar," never "resembles a real PSP handle" (§9.1 addendum, §10.4).
8. **Guideline/PROJECT_SPEC version affected:** v0.7 (all four resolved in one batch, decisions 20–23).
9. **Files created:** `validators/structural.py`.
10. **Files modified:** `annotation/guidelines.md` (§8.1, §9.1, §11.5, §10.4), CHANGELOG, open_questions.md, `PROJECT_SPEC.md`/`configs/pilot.yaml` version pointers (v0.6 → v0.7).
11. **Files explicitly left untouched:** generators (structural.py never calls any generator — proved by a mock-based test that the module has no generator import dependency), the dataset itself (structural rules, not content, were what changed).
12. **Dataset impact:** none directly — this task validates the existing T04 dataset, it does not regenerate it.
13. **Tests added:** `tests/test_structural_validator.py` (81 tests).
14. **Test counts/results:** 81 tests, all passing (verified today).
15. **Independent validation performed:** the module's independence from the generators was itself explicitly tested (mock-based proof that `validators/structural.py` never imports or calls `generators/pii/*`), establishing the "validator has its own frozen regex, does not call the generator" pattern reused by every later validator (`spans.py`, `semantic.py`).
16. **Determinism/reproducibility evidence:** pure regex matching, no randomness.
17. **Preserved/superseded artifacts:** none.
18. **Known limitations:** none of the four frozen regexes attempt real-world checksum/issuance validation (AADHAAR Verhoeff, PAN category-code, etc.) — explicitly out of scope, consistent with the BENCHMARK_SYNTHETIC framing established at T03.
19. **Why the task was considered complete:** all four blocking structural ambiguities resolved by explicit decision, validator implemented and proven independent of the generators, 81 tests passing.
20. **What became unblocked afterward:** T07 (transliteration table) — per the project's explicit task ordering, T07 was required before T08, not after.

---

## T07 — Deterministic Transliteration Table

1. **Task identifier and title:** T07 — `generators/translit/table.py`, deterministic PII transliteration.
2. **Objective:** a token-level Latin→Devanagari lookup table covering the complete frozen T03 PERSON and ADDRESS vocabularies, plus `person_context.name_deva` population on the existing 100 bases.
3. **Governing specification:** guidelines.md v0.7 at design time; the entire evidentiary basis for T07 was two near-identical one-paragraph statements in guidelines.md §4.5 and PROJECT_SPEC.md §8.3 ("Devanagari forms come from a deterministic transliteration table, never an LLM").
4. **Inputs/dependencies:** T03's frozen PERSON (`_GIVEN_NAMES`/`_FAMILY_NAMES`, 20 each) and ADDRESS (`_BUILDING_NAMES`/`_ROAD_NAMES`/`_CITIES`, 8 each) vocabularies; T04's dataset (for `name_deva` population).
5. **Investigation performed:** neither governing document specified whether "table" meant a whole-token lookup, a character/syllable algorithmic mapping, or something else; no rule existed for ADDRESS-specific tokens (abbreviations, numerals, English loanwords like "MG Road"); no fallback was specified for a lookup miss; no transliteration scheme or library was named, authorized, or prohibited.
6. **Open questions encountered:** **OQ-016** (table structure unspecified), **OQ-017** (ADDRESS abbreviations/numerals/loanwords unaddressed), **OQ-018** (no lookup-miss fallback specified), **OQ-019** (no library named/authorized/prohibited). Later, at implementation: **OQ-020** (no `generator_version` field existed on `schemas/base_instance.schema.json` to record the table version in), **OQ-021** (no schema field exists for ADDRESS's Devanagari equivalent of `name_deva` — investigated and confirmed as an intentional gap, not filled), **OQ-022** (no transliteration convention existed for acronyms/initialisms like `"ABC"`, `"MG"`).
7. **Decisions made:** the table is a **token-level lookup only** — one entry per Latin token reachable from the frozen T03 vocabularies, no character-level substitution, no LLM, no probabilistic method, no external general-purpose transliteration tool (§4.7, decision 24). ADDRESS numerals stay unconverted ASCII; every reachable lexical component needs an explicit entry (§4.8, decision 25). A lookup miss **fails closed** — `TransliterationError`, never a guess (§4.9, decision 26). No external library, ever (§4.7/§4.9, decision 27). `generator_version` added as a required field on `base_instance.schema.json`, matching the record schema's existing field exactly (§4.5, decision 28). ADDRESS's Devanagari form is confirmed **never cached** at the base level — generated fresh at record-derivation time (§4.4, decision 29). `"ABC"` → `"एबीसी"` and `"MG"` → `"एमजी"` frozen as explicit benchmark-specific conventions, not universal-transliteration claims (§4.8, decision 30).
8. **Guideline/PROJECT_SPEC version affected:** v0.8 (OQ-016–019), v0.9 (OQ-020–022, T07 implemented).
9. **Files created:** `generators/translit/__init__.py`, `generators/translit/table.py` (79 entries — 40 PERSON tokens + 39 ADDRESS lexical tokens), `tests/test_translit_table.py`.
10. **Files modified:** `schemas/base_instance.schema.json` (added `generator_version`), `annotation/guidelines.md` (§4.5, §4.7–§4.9), `generators/base_instances.py` (now emits `generator_version`), `data/raw/base_instances.jsonl` (see dataset impact below), `tests/fixtures/base_instance*.json` (gained `generator_version`).
11. **Files explicitly left untouched:** the frozen ADDRESS lexical vocabulary in `generators/pii/address.py` itself (T07 consumes it, does not change it); every other field on the 100 base instances besides `name_deva` and `generator_version`.
12. **Dataset impact — second preservation-and-regeneration event:**
    - Before populating `name_deva`, the then-current dataset (post-OQ-007, pre-T07) was preserved as `data/raw/base_instances.pre_t07.jsonl` rather than overwritten in place.
    - `data/raw/base_instances.jsonl` was then regenerated: `person_context.name_deva` populated for all 100 bases (previously `null` on every one), and `generator_version: "0.1.0"` added (previously absent). A before/after diff confirmed these were the *only* two fields that changed.
13. **Tests added:** `tests/test_translit_table.py` — 107 tests. This test file also independently, mechanically verifies that the table's PERSON and ADDRESS entries fully cover T03's frozen vocabularies, rather than trusting a manually-maintained duplicate list.
14. **Test counts/results:** 107 tests, all passing (verified today).
15. **Independent validation performed:** coverage of T03's complete vocabulary was verified programmatically against the actual generator-module constants (not a separately hand-typed duplicate), so a future vocabulary change in T03 would surface as a T07 test failure rather than a silent gap.
16. **Determinism/reproducibility evidence:** pure dict lookup, fails closed on any miss; the same name transliterates identically everywhere by construction (no per-call randomness).
17. **Preserved/superseded artifacts:** `data/raw/base_instances.pre_t07.jsonl` (superseded, preserved, documented in `data/raw/README.md`).
18. **Known limitations:** `"ABC"`/`"MG"` conventions are explicitly benchmark-specific, not claims about correct general Hindi transliteration of arbitrary acronyms; the table would fail closed (reject, not guess) on any PERSON/ADDRESS token outside T03's frozen vocabulary — by design, not an oversight.
19. **Why the task was considered complete:** all four T07-design OQs and all three T07-implementation OQs resolved by explicit decision; full T03 vocabulary coverage mechanically verified; dataset regenerated with only the two intended fields changed, old version preserved.
20. **What became unblocked afterward:** T08 (seven language realizations), which explicitly depends on T07's transliteration for the `HI_DEVA_PII` condition.

---

## T08 — Seven Language Realizations (624 records)

1. **Task identifier and title:** T08 — generate the seven language-condition derived records for all 100 base instances.
2. **Objective:** produce `data/generated/language_realizations.jsonl`, one record per (base, language) pair, per guidelines.md §8's collapse rule.
3. **Governing specification:** guidelines.md v0.10/v0.11 at generation time (built up through this task's own governance cycle — see below).
4. **Inputs/dependencies:** T04's 100 bases, T07's transliteration table, T05's structural expectations.
5. **Investigation performed:** an extensive content-definition gap was found — both governing documents defined each of the seven realizations as a *label* plus a script-table row, but never stated, in prose, what linguistic content generation actually means for any of them (what makes `IN_EN` specifically Indian English; how `ROM_HI` differs from `HINGLISH`; what "WhatsApp register" means operationally for `INFORMAL_HINGLISH`).
6. **Open questions encountered (this task's governance cycle):** **OQ-012** (parent gap: no linguistic content definition for any of the seven conditions — logged, and **remains UNRESOLVED as a general question**, though its three hardest sub-cases were broken out and resolved individually), **OQ-013** (`pii_script`'s `NUMERIC` enum value — which types use it — resolved), **OQ-014** (no worked clean, unperturbed `variant_id` example existed — resolved), **OQ-015** (no mechanism specified for detecting malformed/garbage code-mixed text — logged, **remains UNRESOLVED**, explicitly deferred to a future language/script validator, not built in this pilot), **OQ-023** (`EN` vs `IN_EN` boundary — resolved via a frozen 8-item Indian-English marker inventory), **OQ-024** (`ROM_HI` vs `HINGLISH` boundary — resolved via a frozen loanword inventory plus a frozen insertion inventory, closed-set membership test), **OQ-025** (`HINGLISH` vs `INFORMAL_HINGLISH` — resolved via a frozen four-category informal-marker requirement), **OQ-026** (T07 was PII-vocabulary-only; carrier-sentence construction needed its own mechanism — resolved by explicitly assigning carrier-sentence construction to T08, never expanding T07 into a general-purpose system), **OQ-027** (T08's `context` value was unstated — resolved as `EXPLICIT` for every clean T08 record, explicitly not a redesign of PROJECT_SPEC §9.1's separate C1–C4 allocation).
7. **Decisions made:** the matched-variant invariant (`HI_LATIN_PII`/`HI_DEVA_PII` must share byte-identical carrier text, differing only in PII script, §4.11); the frozen `IN_EN` marker inventory (§4.12); the frozen `ROM_HI` loanword and `HINGLISH` insertion inventories (§4.13); the frozen `INFORMAL_HINGLISH` marker categories (§4.14); the collapse rule for the six non-transliterable types (`HI_LATIN_PII`/`HI_DEVA_PII` identical, generate one record, `hi_variant_collapsed: true`); `pii_script`'s per-type/per-condition determination rule (§4.15); the clean `variant_id` format `{base_id}_{language}` (§4.16); `context: "EXPLICIT"` for every clean record (§4.17).
8. **Guideline/PROJECT_SPEC version affected:** v0.10 (OQ-023–026), v0.11 (OQ-013, OQ-014, OQ-027; T08 implemented).
9. **Files created:** `generators/language/__init__.py`, `spans.py`, `metadata.py`, `templates.py`, `realizations.py`, `records.py`; `data/generated/language_realizations.jsonl` (new file — no prior version existed, so no preservation event was needed here).
10. **Files modified:** `annotation/guidelines.md` (§4.10–§4.17), CHANGELOG, open_questions.md, `PROJECT_SPEC.md`/`configs/pilot.yaml` version pointers, `tests/fixtures/example.valid.json`.
11. **Files explicitly left untouched:** `data/raw/base_instances.jsonl` (T08 reads bases, never rewrites them), T07's table (T08 calls it, never modifies it).
12. **Dataset impact — major milestone:** `data/generated/language_realizations.jsonl` created with **624 records**: 24 transliterable bases (PERSON, ADDRESS) × 7 realizations = 168, plus 76 non-transliterable bases × 6 realizations (collapsed Hindi condition) = 456; 168 + 456 = 624, matching PROJECT_SPEC.md §8.2's pilot arithmetic exactly.
13. **Tests added:** `tests/test_t08_language_realizations.py` (52 tests), `tests/test_t08_governance.py` (16 tests, proving the OQ-013/014/027 decisions against the schema and worked examples independently of the generator).
14. **Test counts/results:** 68 tests total for T08, all passing (verified today).
15. **Independent validation performed:** the matched-variant invariant (identical carrier text outside the PII span) was directly tested for every transliterable base; the collapse-rule record counts (168 + 456 = 624) were asserted, not merely assumed.
16. **Determinism/reproducibility evidence:** one marker/insertion/informal-category is assigned deterministically per base (cycling through the frozen inventories in `base_id` order) — explicitly "no randomness, no LLM judgment call about which marker fits" (§4.12).
17. **Preserved/superseded artifacts:** none for this file (first write); the two `data/raw/base_instances.*` preservation events belong to earlier tasks (T04, T07).
18. **Known limitations — carried forward explicitly, not silently dropped:** OQ-012 (no general content-definition rule beyond the resolved sub-cases) and OQ-015 (no automated code-mixing/garbage-text detection mechanism) remain **UNRESOLVED** in `annotation/open_questions.md` as of this log. Both are explicitly scoped to a future language/script validator (Layer 4), which does not exist yet.
19. **Why the task was considered complete:** all generation-blocking ambiguities (OQ-013, OQ-014, OQ-023–027) resolved by explicit decision; 624/624 records generated matching the frozen arithmetic; the two remaining OQs (012, 015) were explicitly determined to block a *different, later* layer (T10's originally-scoped Layer 4, never built), not T08's own generation.
20. **What became unblocked afterward:** T09 (span validator).

---

## T09 — Span Validator (Layer 2)

1. **Task identifier and title:** T09 (literal) — `validators/spans.py`, occurrence-aware span extraction and validation, distinct from the evaluation-layer reinterpretation of "T09" investigated and found unauthorized (see OQ-034 below).
2. **Objective:** independently re-derive the expected PII occurrence for every T08 record and compare it against what the record declares — `text[start:end] == realized_pii_value`, occurrence resolved by walking all matches, never a bare `str.find()`.
3. **Governing specification:** guidelines.md v0.11 (unchanged by this task — a genuinely mechanical validator, not a new ambiguity).
4. **Inputs/dependencies:** `generators/language/spans.py`'s `find_all_occurrences`/`find_occurrence` (reused, not duplicated), `generators/translit/table.py`'s `transliterate_value` (reused as the sole Devanagari oracle), T08's 624 records, T04's 100 bases.
5. **Investigation performed:** none required beyond confirming the span contract was already fully specified (guidelines.md §13.2's occurrence-walking rule, §14.1's span-boundary rules) — no new open question was needed for this task.
6. **Open questions encountered:** none new. (The "T09 evaluation layer" tangent that preceded this task's literal implementation produced OQ-028 through OQ-034 — documented separately below, since those OQs concern a different, unauthorized body of work, not this validator.)
7. **Decisions made:** none new — this task applied already-frozen rules rather than resolving new ambiguity.
8. **Guideline/PROJECT_SPEC version affected:** none — guidelines.md remained at v0.11 through this task.
9. **Files created:** `validators/spans.py`, `tests/test_span_validator.py`.
10. **Files modified:** none besides the two new files above.
11. **Files explicitly left untouched:** `data/raw/base_instances.jsonl`, `data/generated/language_realizations.jsonl` (validated, never rewritten), T04/T05/T07/T08 code.
12. **Dataset impact:** none — read-only validation.
13. **Tests added:** `tests/test_span_validator.py` (27 tests).
14. **Test counts/results:** 27 tests, all passing (verified today). Session-narrative figure (not independently git-verifiable): full repository suite reported at **386 passing** immediately after this task, in this session's own validation report.
15. **Independent validation performed — the task's own core deliverable:** all 624 records independently reloaded from disk and validated in a fresh process; **0 issues found**; re-run confirmed deterministic (identical results across two independent runs).
16. **Determinism/reproducibility evidence:** the oracle (`expected_realized_value`) is a pure function of `(language, type, base_pii_value)`; two independent validation runs produced identical `total_records`/`valid_records`/`issues`.
17. **Preserved/superseded artifacts:** none.
18. **Known limitations:** none specific to this validator; it is scoped to span/occurrence correctness only, explicitly not semantic-role or language/script correctness (those are later layers).
19. **Why the task was considered complete:** by-condition breakdown reported (EN/IN_EN/ROM_HI/HINGLISH/INFORMAL_HINGLISH/HI_LATIN_PII all 100, HI_DEVA_PII 24; by type: PERSON/ADDRESS 84 each, PHONE/EMAIL 72 each, PAN/AADHAAR/UPI_ID/BANK_ACCOUNT 78 each), 0 issues, deterministic across repeated runs.
20. **What became unblocked afterward:** T10 (semantic validator) — but only after a lengthy governance detour (OQ-028–034) determined that the evaluation-layer reinterpretation of "T09"/"T10" was not what should be built next.

### Digression: the evaluation-layer governance cycle (OQ-028–034) — not a task, an investigation

Before the literal T09 was implemented, a design report was produced for what "T09" could mean as an **evaluation/scoring layer** (detector prediction contracts, baselines B1–B5, metrics M1–M6). This surfaced six scoring-methodology open questions, each investigated and resolved **as PROJECT_SPEC.md content only** (§20.2–§20.6, PROJECT_SPEC.md v1.2), never as implemented code:

- **OQ-028** — no formal schema existed for a detector's predicted-entity output. Resolved: a `type`/`start`/`end` required contract, `text`/`confidence` optional, `variant_id` for batch linkage, malformed predictions rejected and logged, never silently dropped or clipped (§20.2).
- **OQ-029** — `occurrence_index` semantics for *scoring* (not generation) were unspecified. Resolved as part of the same v1.2 batch.
- **OQ-030** — no definition existed for "correctly localized" under M5 (type accuracy). Resolved.
- **OQ-031** — no policy existed for overlapping/nested predictions from the same detector. Resolved — and during this project's own self-audit, an earlier proposed tie-break rule was found under-specified for globally-tied optimal matchings and corrected to an infinitesimal-perturbation term embedded in the weight function, so global optimality and determinism hold simultaneously.
- **OQ-032** — whether out-of-taxonomy predicted types are penalized or ignored. Resolved — and a self-audit found an earlier proposal (a new `OUT_OF_TAXONOMY` attribution tag) would have violated the "preserve the taxonomy unless explicit evidence justifies changing it" rule; corrected to reuse the existing `decoy_class` presence/absence mechanism instead, adding zero new taxonomy elements.
- **OQ-033** — no offset-integrity rule existed for baseline preprocessing/normalization. Resolved.
- **OQ-034** — a distinct, milestone-level question: *is evaluation-layer work authorized under the current Pilot v0.1 milestone at all?* Investigated and answered **no** — PROJECT_SPEC.md §32's 17-item "Definition of Done — Pilot v0.1" checklist concerns dataset generation and dataset-quality validation exclusively; it never mentions baselines, detectors, or M1–M6. Combined with CLAUDE.md's explicit "Current milestone: Pilot v0.1... Nothing beyond this is authorised," this was conclusive without inventing a new rule. **The literal T09 (span extractor + occurrence-aware validator) was explicitly found to remain authorized** — only the evaluation-layer reinterpretation was not.

**Outcome:** PROJECT_SPEC.md v1.2 exists and documents a complete, self-consistent evaluation methodology, but **no line of evaluation code was ever written** — `benchmark/`, `baselines/`, and any M1–M6 implementation remain unauthorized and unbuilt as of this log. This is a specification-only version bump, deliberately not accompanied by implementation, and this document records that distinction rather than letting "PROJECT_SPEC.md v1.2 exists" be read as "the evaluation layer exists."

---

## T10 — Semantic Validator (Layer 3): Governance, then Implementation

This task proceeded in two clearly separated phases, each gated on the other by explicit instruction: no implementation before governance.

### Phase A — Governance (OQ-035, OQ-036, OQ-037)

1. **Task identifier and title:** T10 governance — resolving the specification gaps blocking a Layer 3 (semantic) validator.
2. **Objective:** determine whether the frozen specification gives deterministic rules sufficient to validate "the sentence uses the value in the declared role" (guidelines.md §15) for all eight PII types across all seven language conditions, before writing any validator code.
3. **Governing specification:** guidelines.md v0.11 at investigation start.
4. **Inputs/dependencies:** T04's bases, T08's 624 records, T09's validated spans, guidelines.md §13.5 (as it existed, incompletely, before this phase).
5. **Investigation performed — the central finding of this phase:** the frozen specification was **not** sufficient, in two independent ways:
   - Only 1 of 8 `semantic_role` values (`PERSON`) was ever written into guidelines.md's own §13.5 table; the other 7 existed only in `generators/base_instances.py`'s code, never ratified in a governing document — using them as validator ground truth would have been circular.
   - No mechanism existed anywhere for verifying "the sentence asserts the declared role" in the text itself, for any of the seven language conditions. Two candidate mechanisms (an invented keyword list; reusing the T08 carrier templates as an oracle) were both explicitly rejected — the first as unfrozen invention, the second as circular (a check that could never fail for anything the generator actually produces).
6. **Open questions encountered:** **OQ-035** (6 of 8 `semantic_role` values unfrozen), **OQ-036** (no deterministic semantic-use check exists at all), **OQ-037** (the narrower residual gap after OQ-036: the other six language conditions, beyond `EN`, still lacked a contract).
7. **Decisions made:**
   - **OQ-035:** the complete eight-type mapping was ratified into `guidelines.md` §13.5 — verified first, not assumed: all 100 real base instances scanned, confirmed to already use exactly these 8 values, one per type, no stray values. This documents values already in effect since T04; it changes none of them.
   - **OQ-036:** for `EN` records only (`context == "EXPLICIT"`, `perturbation.family == "NONE"`), ground truth is exact equality `record.text == base.canonical_text` — formalizing a fact already true by construction (verified: 100/100 `EN` records already matched exactly), not a new invention.
   - **OQ-037:** `IN_EN` gets **containment**, `base.canonical_text in record.text` (verified: 100/100). The remaining five conditions (`ROM_HI`, `HINGLISH`, `INFORMAL_HINGLISH`, `HI_LATIN_PII`, `HI_DEVA_PII`) get a frozen per-type label-word table (§13.7), assembled — not invented — from words already frozen elsewhere in guidelines.md (§4.10's PERSON carrier vocabulary, §4.13's loanword table and its Aadhaar note, §5.1/§16's worked examples). Verified against **all 624 records**, zero failures, before being written into the governing document.
8. **Guideline/PROJECT_SPEC version affected:** v0.12 (OQ-035, OQ-036), v0.13 (OQ-037).
9. **Files created:** `tests/test_t10_governance.py` (30 tests, proving the governance decisions themselves — not the eventual validator).
10. **Files modified:** `annotation/guidelines.md` (§13.5, new §13.6, new §13.7), `annotation/CHANGELOG.md`, `annotation/open_questions.md`, `PROJECT_SPEC.md` (version pointers, and a pre-existing stale `guidelines_version: 0.1` pointer in §35 was corrected in passing), `configs/pilot.yaml`, `tests/fixtures/example.valid.json`.
11. **Files explicitly left untouched:** `data/raw/base_instances.jsonl`, `data/generated/language_realizations.jsonl` (both read-only throughout this phase), all T04/T05/T07/T08/T09 code, all schema files (verified: `semantic_role` remains unconstrained free text on the schema — the type-fixed constraint is validator-level cross-field logic, not a schema enum, consistent with the T02 scope rule).
12. **Dataset impact:** none — governance and documentation only, explicitly verified against the dataset without modifying it.
13. **Tests added:** `tests/test_t10_governance.py` — 30 tests.
14. **Test counts/results:** 30 tests, all passing. Full suite reported at 403 (after OQ-035/036) and then 416 (after OQ-037) in this session's own validation reports.
15. **Independent validation performed:** every proposed rule was checked against the real 100 bases and/or 624 records **before** being written into `guidelines.md` — not asserted first and verified after.
16. **Determinism/reproducibility evidence:** full suite run twice after each governance sub-step, identical pass counts both times.
17. **Preserved/superseded artifacts:** none — no dataset regeneration was needed at any point in this phase.
18. **Known limitations, explicitly recorded rather than hidden:** neither the OQ-036 nor the OQ-037 contract can distinguish "value used in the wrong role" from "value present, role never asserted" — both surface as the same kind of miss. Finer discrimination would require sentence-structure parsing, which both decisions explicitly decline to attempt.
19. **Why the task was considered complete:** all three blocking gaps resolved with evidence shown, not silently assumed; the underlying honesty constraint ("do not invent a keyword list, do not reuse the generator as an oracle") was upheld throughout rather than relaxed under the pressure of three sequential resolution requests.
20. **What became unblocked afterward:** T10 Phase B (implementation).

### Phase B — Implementation

1. **Task identifier and title:** T10 implementation — `validators/semantic.py`.
2. **Objective:** implement the Layer 3 validator using exactly the governance contracts from Phase A, independent of the generators, reusing T09/T07's existing oracle functions rather than duplicating their algorithms.
3. **Governing specification:** guidelines.md v0.13 (§13.5–§13.7), fully resolved.
4. **Inputs/dependencies:** `validators/spans.py`'s `expected_realized_value` (reused, not duplicated — this is how T07's transliteration selection logic is consumed without being reimplemented), the frozen §13.5/§13.7 tables (copied as independent constants, never imported from generator code).
5. **Investigation performed:** none new — Phase A had already closed every specification gap; this phase was pure implementation against a frozen contract.
6. **Open questions encountered:** none.
7. **Decisions made (implementation-level, not governance):** four separated layers (metadata/type-role; base/derived linkage; semantic identity; condition-specific Layer-3 contract), plus two cross-record checks (`HI_LATIN_PII`/`HI_DEVA_PII` matched-pair semantics; collapsed-Hindi semantics) — architecture chosen to mirror `validators/spans.py`'s established shape (`SemanticValidationIssue` dataclass, `validate_dataset()` orchestrator) for consistency rather than inventing a new validator shape.
8. **Guideline/PROJECT_SPEC version affected:** none — pure implementation of an already-frozen contract.
9. **Files created:** `validators/semantic.py`, `tests/test_semantic_validator.py`.
10. **Files modified:** none.
11. **Files explicitly left untouched:** both dataset files (confirmed via MD5 checksum before/after), all schemas, all guidelines/spec/config files, `generators/base_instances.py`, `generators/language/templates.py` (neither is imported by `validators/semantic.py` — proven by an AST-based static-inspection test, not just a manual claim).
12. **Dataset impact:** none.
13. **Tests added:** `tests/test_semantic_validator.py` — 98 tests (pytest-collected count; parametrization expands the underlying 41 `def test_` functions in the source file).
14. **Test counts/results:** 98 tests, all passing. Full repository suite: **514 passing**, run twice, identical both times.
15. **Independent validation performed:** all 100 bases and 624 derived records reloaded independently from disk in a fresh process and validated — **0 issues, 624/624 valid** — broken down by language (EN 100, IN_EN 100, ROM_HI 100, HINGLISH 100, INFORMAL_HINGLISH 100, HI_LATIN_PII 100, HI_DEVA_PII 24), by PII type (PERSON/ADDRESS 84 each, PHONE/EMAIL 72 each, PAN/AADHAAR/UPI_ID/BANK_ACCOUNT 78 each), and by `semantic_role` (one-to-one with the type breakdown, per the frozen §13.5 mapping).
16. **Determinism/reproducibility evidence:** `validate_dataset()` run twice independently on freshly-reloaded data — identical `total_records`, `valid_records`, and issue count both times; the full test suite run twice back-to-back, 514/514 both times.
17. **Preserved/superseded artifacts:** none — no dataset regeneration in this phase.
18. **Known limitations — inherited directly from Phase A's governance decisions, not new to this phase:** the validator cannot distinguish "wrong role" from "role never asserted" (both are `SEMANTIC_MISMATCH`/`ROLE_UNSUPPORTED_BY_TEXT`); Layer 4 (language/script), duplicate validation, and human review remain unbuilt.
19. **Why the task was considered complete:** implementation matches the frozen contract exactly, reuses rather than duplicates T09/T07's primitives, proven independent of generator code both by design and by static inspection, 0 issues on the full real dataset, deterministic.
20. **What became unblocked afterward:** nothing yet formally requested — the evaluation/baseline layer remains unauthorized per OQ-034's finding, and Layer 4/duplicate/human-review validators have not been scoped as tasks.

---

## T11 — Final Governance Audit for OQ-042/OQ-044

Between this entry and T10's completion, a separate design-and-governance thread ran
for T11 (`PROJECT_SPEC.md` §31's literal T11: "20 hard negatives with distractors, all
6 decoy classes"). It produced a T11 design report, resolved OQ-042 (partially),
OQ-043, and OQ-045 (`guidelines.md` v0.14, §13.8–§13.10), and left OQ-042's remaining
two decoy classes (`HANDLE_SHAPE`, `ORG_AS_PERSON`) and OQ-044 (hard-negative
language-condition count) open. This entry records the **final** audit pass on those
two remaining blockers — supersedes the "Current Open Questions" section above for
these two items specifically; that section is left as the historical snapshot it was
written as, not edited in place.

**Evidence reviewed:** a full repository-wide search (every `.md`/`.json`/`.py`/`.jsonl`
file) for organisation-suffix vocabulary, handle/ticket vocabulary, `username`,
`account handle`, `corp`, `20 × 5`/`20x5`, and `collapse`/`collapsed`, in addition to a
close re-reading of `PROJECT_SPEC.md` §§8, 8.1, 12.2 and `guidelines.md` §4.1's stated
rationale for the seven-realization split.

**What was resolved:** nothing new. Both remain open, now on a fully audited rather
than best-effort basis:

- **OQ-042 (`HANDLE_SHAPE`/`ORG_AS_PERSON`):** one new, concrete candidate was found for
  `HANDLE_SHAPE` — `generators/pii/email.py`'s own local-part construction
  (`_LOCAL_PART_WORDS` + digit suffix) paired with one of its `_DOMAIN_LABELS` but with
  the reserved TLD dropped, verified by direct regex evaluation to fail both `_EMAIL_RE`
  and `_UPI_ID_RE`. Not adopted: it modifies an existing frozen rule (removes the exact
  component EMAIL's own docstring calls its "zero-ambiguity safety rule") rather than
  reusing one unmodified, unlike every already-resolved §13.8 class. `ORG_AS_PERSON`
  remains at zero reusable construction material of any kind.
- **OQ-044 (language-condition count):** reconciled into an explicit three-row
  evidence table (`annotation/open_questions.md`) — 140 (7-condition, no special case),
  120 (6-condition, grounded in §4.1's own PII-script rationale but not in §8.1's
  literal category-scoped wording), and a construction consistent with the document's
  own approximate "~60" (which it itself disclaims, and which — unlike the adversarial
  line right next to it — was never given the exact-derivation treatment positives'
  own once-approximate figure eventually got in §8.2). No row is uniquely supported.

**What remains a human decision:** both, in full. A construction rule for `HANDLE_SHAPE`
(the EMAIL-without-TLD candidate, or something else) and for `ORG_AS_PERSON` (no
candidate found at all); and which of the three OQ-044 readings — or a fourth not yet
considered — is correct.

**Why T11 implementation is still not unblocked:** 6 of 20 hard-negative bases
(`HANDLE_SHAPE` + `ORG_AS_PERSON`'s allocation) cannot be constructed without a human
choosing a construction rule; and no hard-negative *derived* record of any decoy class
can be generated until OQ-044 fixes a language-condition count, since that number
determines how many records exist per base at all. Base-level construction for the
other 14 (four already-resolved classes) remains unblocked, as established in the prior
governance turn.

**No governance edit was made to `guidelines.md` or `PROJECT_SPEC.md` this turn** — per
the explicit instruction governing this audit, a strengthened evidence trail is not the
same as a resolution, and none was manufactured to close the gap. Only
`annotation/open_questions.md` was updated, with the audit trail above.

---

## T11 — Human Decision Resolution for OQ-042/OQ-044

The audit above ended with two genuinely undetermined gaps, each presented back to the
user as a decision memo — the strongest repository-grounded candidate(s) for each,
labeled 2–3 discrete choices with their consequences, and an explicit recommendation
withheld from being treated as authorization. The user then made three selections.

**The three selected decisions:**

1. **OQ-042 / `HANDLE_SHAPE` → Option A.** Freeze the strongest candidate found in the
   audit: `generators/pii/email.py`'s own `_LOCAL_PART_WORDS` + digit-suffix
   construction, paired with an existing `_DOMAIN_LABELS` word, with the reserved TLD
   omitted (`guidelines.md` §13.8, decision 45, v0.15).
2. **OQ-042 / `ORG_AS_PERSON` → Option C.** Remove/defer this class from Pilot v0.1
   rather than invent a grammar for it. Its 3-base quota allocation is redistributed to
   `NUMERIC_SHAPE` (+1), `ALNUM_SHAPE` (+1), `NAME_AS_PLACE` (+1) — §13.9, decision 46 —
   so the pilot's 20-base hard-negative total is preserved.
3. **OQ-044 → Option B.** Hard-negative derived records use six realizations —
   `EN`, `IN_EN`, `ROM_HI`, `HINGLISH`, `INFORMAL_HINGLISH`, and one collapsed Hindi
   realization — extending §8.1's existing collapse-rule rationale to the
   `HARD_NEGATIVE` case (§13.11, decision 47, v0.15).

**Alternatives rejected, not merely unselected:**

- `HANDLE_SHAPE` Option B (define a wholly new grammar from nothing) and Option C
  (remove/defer the class) were both presented with their consequences and not chosen.
- `ORG_AS_PERSON` Option A (invent a minimal grammar) and Option B (reuse T03's
  family-name vocabulary plus a still-invented suffix list) were both presented and not
  chosen — the deciding factor was that this project has consistently declined to
  invent vocabulary with no textual anchor (OQ-004–011, OQ-035–041, and the other five
  §13.8 classes, each of which reuses an existing rule unmodified).
- OQ-044 Option A (140 records, full seven-condition treatment, no special case) and
  Option C (a construction consistent with the historical "~60" estimate) were both
  presented with textual evidence and contradictions and not chosen.

**Why `HANDLE_SHAPE` A was chosen:** it was the only candidate, of the two "build it"
options, that reused an existing frozen construction wholesale rather than inventing a
new one from nothing — and it is mechanically verified to fail both EMAIL's and
UPI_ID's frozen structural regexes, so it is a genuine, not merely asserted, member of
"x@y where role is neither email nor UPI" (guidelines.md §13.3).

**Why `ORG_AS_PERSON` was deferred instead of invented:** unlike every other decoy
class in this taxonomy, two independent repository-wide audits found zero reusable
construction material for it — not even a modifiable existing rule, the weaker
standard `HANDLE_SHAPE` still met. Freezing a grammar for it would have required
inventing organisation-name vocabulary with no anchor anywhere in either governing
document, which this project's own discipline has never done for any other type or
class when the same situation arose.

**Why OQ-044 B was chosen:** among three readings none of which is uniquely determined
by the frozen text, six-condition collapse is the only one grounded in an *existing*
architectural rationale (§4.1/§8.1's own stated reason for splitting Hindi-script
conditions — PII-script variation, which a `pii: []` record has none of) rather than
either accepting known content redundancy (the seven-condition option would generate a
byte-identical `HI_LATIN_PII`/`HI_DEVA_PII` pair) or adopting an estimate the source
document itself disclaims as approximate and never gave the exact-derivation treatment
its neighboring lines received. This is recorded, per instruction, as a **deliberate
extension** of §8.1's rationale — not a claim that §8.1's text already named hard
negatives.

**Resulting planned cardinalities (not yet generated):**

| Metric | Value |
|---|---|
| Existing positive bases | 100 |
| New hard-negative bases | 20 |
| **Total bases** | **120** |
| Existing positive derived records | 624 |
| Hard-negative derived records (20 × 6) | 120 |
| **Total derived records** | **744** |
| **Combined base + derived records** | **864** |

**No implementation or dataset generation occurred in this turn.** No
`generators/hard_negatives.py` was created; `validators/spans.py` and
`validators/semantic.py` are unmodified; `data/raw/base_instances.jsonl` (100 records)
and `data/generated/language_realizations.jsonl` (624 records) are byte-for-byte
unchanged from before this turn. The cardinalities above are a frozen *plan*, verified
by `tests/test_t11_hard_negative_governance.py`'s arithmetic checks, not a report of
data that exists on disk.

**Noted, not corrected this turn:** `PROJECT_SPEC.md` §32's Definition-of-Done
checklist item — *"20 hard-negative bases with distractors, all 6 decoy classes
present"* — is now in tension with `ORG_AS_PERSON`'s deferral (five of six classes will
exist, not six). This turn's scope was limited to the `guidelines_version` pointer in
`PROJECT_SPEC.md`, per explicit instruction not to modify its methodology text
unnecessarily; the checklist wording itself was left as encountered.

---

## T11 — Hard-Negative Construction Ground-Truth Architecture

Governance was frozen at v0.15; the next turn attempted T11 Phase 1 (base-instance
generation only) and, before writing any generator code, found a genuine architecture
gap rather than proceeding to implement. This entry records how that gap was resolved.

**The original conflict.** Phase 1's own instructions asked every generated
hard-negative *base* to carry "empty `entities`" and "non-empty `distractors`." Neither
field exists on `schemas/base_instance.schema.json`, and per `guidelines.md` §13.4
(decision 16, frozen since v0.3), neither ever should: *"Distractor information belongs
to the derived record, never the base instance... `schemas/base_instance.schema.json`
does not, and must not, gain a `distractors` property."* `entities[]` was never a
base-instance field for any `base_kind` either — it is exclusively a derived-record
(`schemas/example.schema.json`) concept. §13.3's sentence describing a hard negative as
having "an empty `entities` array and a populated `distractors` array" describes the
eventual *derived record*, not the base — exactly parallel to how a positive base has
`pii[]`, not `entities[]`.

**Why `entities`/`distractors` cannot belong to the base.** Restated, not relitigated:
this was already decided at T02 (OQ-002/OQ-003) and reaffirmed at T11's own OQ-042/043
turns. `additionalProperties: false` on the base schema already excludes both fields
structurally; nothing about persisting construction metadata changes this.

**Why `pii[]` remains empty.** Also unchanged: `base_kind == HARD_NEGATIVE` requires
`pii == []` (decision 16) — definitional to what a hard negative is, not a candidate
for renegotiation.

**The two considered architectures**, once the deeper gap (nowhere to persist *which*
decoy a given hard-negative base was built with) was identified:

1. **Persist construction metadata on the base instance** — a new, optional field,
   mirroring how `pii[]` already serves this role for positive bases.
2. **Re-derive it from `base_id` + RNG replay** at derived-record-generation time, with
   no new field at all.

**Why persisted metadata was selected.** Path 1 was explicitly approved by the user.
RNG replay (Path 2) was rejected because it would make hard-negative derivation depend
on exactly reproducing the base generator's own RNG sequence — a coupling no other
`base_kind` has. Positive-base derivation (T08) reads only `base.pii[]`; it never
re-runs T04's generator. Making hard negatives work on a fundamentally different
principle than every other base_kind, solely to avoid adding one field, was judged the
worse inconsistency.

**The exact resulting base/derived relationship.** `hard_negative_decoy` — optional
(absent from the schema's top-level `required` array, so the 100 existing `POSITIVE`
bases stay valid and byte-identical without it), object-or-null on the base instance,
exactly four sub-fields when populated: `decoy_class` (enum duplicated from
`schemas/example.schema.json`, not `$ref`'d across files, matching the
`generator_version` precedent), `value`, `surface_type`, `actual_role`. Presence versus
`base_kind` is a cross-field rule in `validators/base_kind.py`
(`check_base_kind_hard_negative_decoy_invariant`), not an `if`/`then` in the schema —
JSON Schema 2020-12 could express that conditional; it isn't used here purely for
consistency with the base_kind/`pii` invariant's own precedent, which was deliberately
kept out of the schema for the same reason. A future Phase 2 derived-record generator
reads `base.hard_negative_decoy` and materializes it into exactly one `distractors[]`
entry per derived record, computing `start`/`end` against that record's own carrier
text via the existing occurrence-finding primitive — `entities` stays `[]` throughout.

**Governance:** logged and resolved as OQ-046 (`annotation/open_questions.md`), frozen
in `guidelines.md` §13.12 (decision 48), version bumped 0.15 → 0.16. New tests in
`tests/test_schemas.py`, `tests/test_base_kind_invariant.py`, and two new governance
files prove the schema shape, the cross-field invariant, and that no implementation
boundary was crossed — no `generators/hard_negatives.py`, no hard-negative base
instance on disk, the 100 existing `POSITIVE` bases and 624 existing derived records
unchanged. Phase 1 (base generation) itself has not yet been implemented; this turn was
architecture and schema only.

---

## T11 — Hard-Negative Realization Inventory (OQ-047 Resolution)

Phase 1 (20 hard-negative bases) was subsequently implemented and verified (separate
entry not duplicated here — see the T11 Phase 1 test/implementation record). Before
Phase 2 (derived-record generation), a pre-implementation audit found that T08's
PII-type-keyed carrier templates (`generators/language/templates.py`) cannot construct
`ROM_HI`/`HINGLISH`/`INFORMAL_HINGLISH`/the collapsed Hindi realization for hard
negatives, since a hard negative has no `pii_type` to key the lookup on. Two full audit
passes (design report, then a candidate-by-candidate re-audit against Candidates
A–E) found no existing evidence sufficient to construct these four realizations
without new content, for four of the five constructible decoy classes; `PARTIAL_PII`
needed no new *words* but did need a new *sentence-assembly template*, since reusing
already-frozen words is not the same as the sentence itself being pre-existing.

**Human decision:** approved the audit's Candidate D proposal — freeze a small, closed,
benchmark-specific lexical inventory, explicitly not a general-purpose Hindi translation
system (`guidelines.md` §13.13, decision 49, v0.17).

**Exact new content, labeled apart from what it reuses:**

| Item | Status |
|---|---|
| `mera` ("my"), `hai` ("is") | already frozen, §4.10 |
| `number`/`नंबर`, `account`/`अकाउंट` | already frozen, §4.13 |
| `ke paas`/`के पास` ("near") | already frozen, §7.2 |
| `order`/`ऑर्डर` | **new, frozen now** |
| `reference code`/`रेफरेंस कोड` (compound) | **new, frozen now** |
| `station`/`स्टेशन` | **new, frozen now** |
| `contact`/`कॉन्टैक्ट` | **new, frozen now** |

One `ROM_HI`/Devanagari carrier template per constructible class was frozen alongside
the words — `NUMERIC_SHAPE`: "mera order number {value} hai."; `ALNUM_SHAPE`: "mera
reference code {value} hai."; `NAME_AS_PLACE`: "{value} station ke paas hai.";
`HANDLE_SHAPE`: "mera contact {value} hai."; `PARTIAL_PII`: "mera account number
{value} hai." (zero new words, but the template itself is newly frozen).
`HINGLISH`/`INFORMAL_HINGLISH` construction was confirmed, by direct execution against
a non-PII test sentence, to need no vocabulary beyond `ROM_HI`'s own — the existing
`HINGLISH_PATTERNS` are pure string operations.

**Why `HANDLE_SHAPE` did not simply reuse EMAIL's frozen carrier:** doing so ("mera
email {value} hai.") would have falsely asserted the distractor is a genuine email,
directly contradicting its own definition ("x@y where role is neither email nor UPI,"
§13.3) and its `actual_role`/`surface_type` fields. This was Candidate B, rejected in
the audit and not revisited here.

**What remains unresolved:** OQ-048 (whether `validators/spans.py` should be extended
to check `distractors[]` spans) is unaffected — this decision governs carrier content,
not validator scope. No schema, validator, or generator file was created or modified.
Phase 2 implementation (the actual derived-record generator) has still not started.

---

## T11 — Phase 2 Implementation (120 Hard-Negative Derived Records)

With OQ-047 resolved (`guidelines.md` §13.13, v0.17), Phase 2 was implemented exactly
against that frozen specification. OQ-048 was left untouched, as instructed — no
`validators/spans.py` contract change was made for distractors; this turn's own span
correctness proof is a construction-time verification, not a validator extension.

**Implementation.** A new module, `generators/language/hard_negative_records.py`,
assembles the six frozen realizations (`EN`, `IN_EN`, `ROM_HI`, `HINGLISH`,
`INFORMAL_HINGLISH`, and one collapsed Hindi realization labeled `HI_LATIN_PII`, never
`HI_DEVA_PII`) for each of the 20 `HARD_NEGATIVE` bases. It reuses, unmodified:
`generators/language/metadata.py`'s `CONTEXT`, `NONE_PERTURBATION`, `variant_id`,
`carrier_script`, `difficulty`, `record_domain`; `generators/language/templates.py`'s
`IN_EN_MARKERS` and `HINGLISH_PATTERNS`; `generators/language/spans.py`'s
`find_occurrence`. It does not reuse `CARRIER_TEMPLATE_ROM_HI`/
`CARRIER_TEMPLATE_DEVANAGARI` or `realizations.py`'s PII-keyed realize functions, since
those are keyed by `pii_type`, which a hard negative does not have — this was the exact
gap OQ-047 closed with a parallel, `decoy_class`-keyed carrier table
(`HARD_NEGATIVE_CARRIER_ROM_HI`/`HARD_NEGATIVE_CARRIER_DEVANAGARI`) reproducing §13.13's
table verbatim. `generators/language/realizations.py` (T08, positive-PII only) was not
modified; the INFORMAL_HINGLISH carve-out-transform-reinsert mechanism was mirrored as a
parallel function rather than imported, so no cross-module coupling to a private T08
symbol was introduced.

**Output location.** `data/generated/hard_negative_realizations.jsonl` — a separate file
from `data/generated/language_realizations.jsonl` (the 624 positive records), mirroring
Phase 1's own precedent of keeping hard-negative artifacts additional to, never merged
into, the positive dataset (PROJECT_SPEC.md §12.2's "not part of the 100" framing
applied identically to the derived-record layer). This is a disclosed implementation
choice, not a filename either governing document names explicitly; no ambiguity was
judged to exist given the direct Phase 1 precedent, so no OQ was logged for it.

**Tests first.** `tests/test_generate_hard_negative_records.py` (47 tests) was written
and run against the generator before any file was written to
`data/generated/`, covering: exact record/per-base/per-language counts, absence of
`HI_DEVA_PII`, `entities == []`, exactly one distractor with metadata copied verbatim
from `base.hard_negative_decoy`, distractor span correctness and containment, base
linkage and `base_kind` (via the linked base), `variant_id` format/uniqueness, `context`/
`perturbation`, schema validity, the frozen quota's language×decoy-class matrix,
absence of `ORG_AS_PERSON`, determinism (in-memory and fresh-subprocess), preservation of
both existing positive datasets, exact §13.13 carrier-text matches per class, and value
non-mutation by HINGLISH/INFORMAL_HINGLISH — plus a regression test that
`generators/language/records.py`'s positive pipeline still reproduces the existing 624
canonical records byte-for-byte.

**Generation protocol followed.** Generated 120 records to a temporary path; reloaded
and independently validated in a fresh process (schema, counts, linkage, distractor
metadata/spans, determinism); regenerated independently and confirmed byte-identical
after normalizing for Windows' `Path.write_text` CRLF translation (the initial raw-bytes
comparison in this turn's own ad hoc verification script produced a false-positive
mismatch for exactly this reason — logged here rather than silently discarded, since it
is the kind of thing a future session could rediscover and misdiagnose as real
nondeterminism); confirmed both `data/raw/base_instances.jsonl` (MD5
`7006b0c9227d93541d2b71f702407ecc`) and `data/raw/hard_negative_bases.jsonl` (MD5
`b36c6c106548d18ff7083fd00532cb07`) unchanged; wrote the canonical file (no prior file
existed, confirmed before writing); reloaded and independently re-validated the
canonical file from disk; ran the full suite twice (690 passed both times).

**Generated data.** 120 records: 20 per language condition (6 conditions × 20 bases);
by decoy class, `NUMERIC_SHAPE` 30, `ALNUM_SHAPE` 30, `NAME_AS_PLACE` 24, `HANDLE_SHAPE`
18, `PARTIAL_PII` 18 (each five/five/four/three/three base quota × 6 realizations);
`ORG_AS_PERSON` absent, as frozen.

**Final cardinality.** 120 bases (100 positive + 20 hard-negative) = 120; 744 derived
records (624 positive + 120 hard-negative); 864 combined (120 + 744).

**Boundary respected.** OQ-048 remains unresolved — not touched, not silently answered
by this turn's own construction-time span checks. No positive dataset, T04/T05/T07
behavior, or T08 positive-realization behavior was modified. No evaluation/M1–M6 work,
no `benchmark/`/`baselines/` code, no T12 work was started.

---

## Open-Question Chronology — Why Ambiguous Formats Were Never Invented

Across T01–T10, this project's single consistent behavior was: **when a governing document did not fully specify something, stop and log it rather than pick the sensible-looking answer** (CLAUDE.md §3). The table below is the complete chronology; "why not invented" is explicit for the cases the request specifically named.

| OQ | Subject | Status | Resolved in |
|---|---|---|---|
| OQ-001 | `validation{}`: 5 or 6 keys | RESOLVED | v0.2 |
| OQ-002 | Do hard-negative bases use `base_instance.schema.json`? | RESOLVED | v0.3 |
| OQ-003 | Explicit `base_kind` discriminator needed? | RESOLVED | v0.3 |
| OQ-004 | AADHAAR format unspecified | RESOLVED | v0.4 |
| OQ-005 | BANK_ACCOUNT format unspecified | RESOLVED | v0.4 |
| OQ-006 | UPI_ID grammar/domain unspecified | RESOLVED | v0.5 |
| OQ-007 | PERSON `semantic_role` domain-implausible | RESOLVED | v0.6 |
| OQ-008 | PHONE base representation unfrozen | RESOLVED | v0.7 |
| OQ-009 | EMAIL local-part format unconstrained | RESOLVED | v0.7 |
| OQ-010 | PAN casing unspecified | RESOLVED | v0.7 |
| OQ-011 | EMAIL/UPI_ID domain case sensitivity | RESOLVED | v0.7 |
| OQ-012 | No linguistic content rule for the 7 realizations | **UNRESOLVED** (parent gap; sub-cases below resolved) | — |
| OQ-013 | `pii_script` `NUMERIC` usage unclear | RESOLVED | v0.11 |
| OQ-014 | No clean `variant_id` worked example | RESOLVED | v0.11 |
| OQ-015 | No malformed-code-mixing detection mechanism | **UNRESOLVED** | — |
| OQ-016 | Transliteration table structure unspecified | RESOLVED | v0.8 |
| OQ-017 | ADDRESS abbreviations/numerals/loanwords unaddressed | RESOLVED | v0.8 |
| OQ-018 | No transliteration lookup-miss fallback | RESOLVED | v0.8 |
| OQ-019 | No library named/authorized/prohibited | RESOLVED | v0.8 |
| OQ-020 | No `generator_version` field on base schema | RESOLVED | v0.9 |
| OQ-021 | No ADDRESS-Devanagari base-level field | RESOLVED (confirmed as intentional gap) | v0.9 |
| OQ-022 | No convention for ADDRESS acronyms | RESOLVED | v0.9 |
| OQ-023 | `EN` vs `IN_EN` boundary | RESOLVED | v0.10 |
| OQ-024 | `ROM_HI` vs `HINGLISH` boundary | RESOLVED | v0.10 |
| OQ-025 | `HINGLISH` vs `INFORMAL_HINGLISH` threshold | RESOLVED | v0.10 |
| OQ-026 | Hindi carrier-text generation mechanism | RESOLVED | v0.10 |
| OQ-027 | T08 `context` value unstated | RESOLVED | v0.11 |
| OQ-028 | Detector prediction schema (evaluation layer) | RESOLVED (spec only) | PROJECT_SPEC v1.2 |
| OQ-029 | `occurrence_index` scoring semantics | RESOLVED (spec only) | PROJECT_SPEC v1.2 |
| OQ-030 | M5 "correctly localized" definition | RESOLVED (spec only) | PROJECT_SPEC v1.2 |
| OQ-031 | Overlapping/nested prediction policy | RESOLVED (spec only) | PROJECT_SPEC v1.2 |
| OQ-032 | Out-of-taxonomy prediction penalty | RESOLVED (spec only) | PROJECT_SPEC v1.2 |
| OQ-033 | Baseline offset-integrity rule | RESOLVED (spec only) | PROJECT_SPEC v1.2 |
| OQ-034 | Is evaluation-layer work authorized now? | RESOLVED — **no** | investigative finding, no spec change |
| OQ-035 | 6 of 8 `semantic_role` values unfrozen | RESOLVED | v0.12 |
| OQ-036 | No deterministic semantic-use check (any condition) | RESOLVED (EN only) | v0.12 |
| OQ-037 | No deterministic semantic-use check (6 remaining conditions) | RESOLVED | v0.13 |

**Why ambiguous generator formats were not invented, as a general pattern:** in every one of OQ-004/005/006/008/009/010/011 (the generator- and validator-format questions), the same shape of gap recurred — a governing document referenced a PII type's "format" only through a placeholder-style worked example, never a concrete grammar. The project's response was never to infer a plausible-looking regex and move on; it was to log the exact missing rule, propose 2–3 concrete candidate resolutions grounded in what the surrounding design already implied (e.g. UPI_ID's candidates were shaped by PROJECT_SPEC §7's own stated EMAIL-collision design goal), and wait for an explicit choice. This is documented per-OQ above and in `annotation/open_questions.md` itself, which remains the primary source for the full evidentiary text of each entry.

---

## Current Open Questions

Two entries in `annotation/open_questions.md` are genuinely unresolved as of this log (confirmed by reading their `Status:` lines directly, not inferred from the header formatting alone — OQ-027's header omits a status suffix but its body confirms RESOLVED, a minor formatting inconsistency in the source document itself, noted here rather than silently corrected):

- **OQ-012** — no general linguistic content-definition rule exists for the seven language realizations beyond the three specific sub-boundaries (OQ-023/024/025) that were carved out and resolved. **Impact:** does not block anything already built (T08 generated correctly using the resolved sub-cases); would matter if a future task tried to add an eighth language condition or reduce reliance on the closed-set marker inventories.
- **OQ-015** — no automated mechanism exists for detecting malformed or garbage code-mixed text, or confirming genuine (versus artificial-looking) code-mixing. **Impact:** blocks a Layer 4 (language/script) validator, which does not exist yet and was never in scope for T09 or T10. Currently, the only mechanism either governing document specifies for this failure mode is human review (guidelines.md §19).

No other OQ in the log is open. OQ-034 is RESOLVED as an investigative finding (evaluation-layer work is not authorized under the current milestone) rather than as a specification change — it is not a pending decision, it is a closed determination.

---

## Reproducibility Summary

- **Seeds:** deterministic seed `42` used throughout for all non-LLM randomness (`generators/base_instances.py`); every PII generator takes an explicit `random.Random` instance, never the global `random` module (verified by `tests/test_generators_common.py`'s shared determinism checks).
- **Deterministic generation:** the transliteration table (T07) is a closed, fail-closed lookup — no LLM, no probabilistic method, ever, for any PII value. Carrier-sentence marker/insertion selection (T08) is assigned deterministically per base by cycling through frozen inventories in `base_id` order — never randomly, never by LLM judgment.
- **Preserved artifacts (never silently overwritten):**
  - `data/raw/base_instances.pre_oq007.jsonl` — the dataset before the PERSON `semantic_role` correction.
  - `data/raw/base_instances.pre_t07.jsonl` — the dataset before `name_deva`/`generator_version` population.
  - Both are documented in `data/raw/README.md`.
- **Dataset counts (directly verified from the files on disk today):**
  - 100 base instances (`data/raw/base_instances.jsonl`).
  - 624 derived language-realization records (`data/generated/language_realizations.jsonl`) — 168 from 24 transliterable bases × 7 conditions, 456 from 76 non-transliterable bases × 6 conditions (collapsed Hindi).
  - 724 combined base + derived records.
- **Validation counts (directly verified today, independent fresh-process reload):**
  - T09 (span, Layer 2): 624/624 valid, 0 issues.
  - T10 (semantic, Layer 3): 624/624 valid, 0 issues, across all language/type/role breakdowns.
  - Both validators re-run twice independently with identical results (determinism proof).
- **Test suite:** 514 tests passing, verified today via two independent full-suite runs with identical results. Per-file counts (pytest-collected, summed to 514 and cross-checked): schemas 4, base_kind invariant 4, eight PII generators + shared checks 78, base-instance generation 17, structural validator 81, transliteration table 107, T08 language realizations + governance 68, span validator 27, T10 governance 30, T10 semantic validator 98.
- **What is NOT yet built, confirmed by absence:** no `benchmark/` or `baselines/` directory exists; no M1–M6 metric implementation exists; no Layer 4 (language/script), duplicate, or human-review validator exists. PROJECT_SPEC.md v1.2's evaluation-layer sections (§20.2–§20.6) are specification text only.
- **Version state:** `annotation/guidelines.md` v0.13 (supersedes v0.12); `PROJECT_SPEC.md` v1.2 (supersedes v1.1); every version transition is documented in `annotation/CHANGELOG.md` (guidelines) or PROJECT_SPEC.md's own §0 "Changes in vX.Y" list (spec), per this project's dual-versioning convention.

---

## Paper-Relevant Methodological Contributions

These are objective properties of how this benchmark was constructed, not claims about its downstream research value:

- **Specification-gated generation.** No generator or validator was implemented against an ambiguous rule. Every genuine gap in the governing specification (37 numbered instances) was logged with the exact rule that failed and 2–3 concrete candidate resolutions before any code was written against it. Two gaps (OQ-012, OQ-015) remain open rather than closed by inference, and are reported as open in this log rather than silently treated as resolved.
- **Fail-closed ambiguity handling.** Every deterministic component in this pipeline (transliteration lookup, structural regexes, span occurrence resolution, semantic label checks) is designed to reject or raise on an unrecognized case rather than guess, interpolate, or silently pass a best-effort value through.
- **Deterministic transliteration as a controlled variable.** Devanagari PII forms are produced by a fixed, versioned, token-level lookup table rather than a general algorithm or LLM — the same input token transliterates identically in every record, by construction, which is what makes the `HI_LATIN_PII`/`HI_DEVA_PII` script-isolation comparison (PROJECT_SPEC.md's RQ2b) a controlled experiment rather than confounded by transliteration variance.
- **Independent, non-duplicating validation layers.** Structural (T05), span (T09), and semantic (T10) validation are three separate modules, each independent of the generators that produced the data they check, and each reusing lower-layer primitives (T10 reuses T09's oracle function; T09 reuses T08's occurrence-walking utility) rather than re-deriving the same logic three times. This separation is what let each layer be audited and version-controlled independently.
- **Provenance preservation over silent mutation.** Every regeneration of the base-instance dataset (post-OQ-007, post-T07) preserved the prior version under an explicit `pre_<reason>` filename with a documented reason, rather than being overwritten in place — the rejected/superseded state is itself retained as evidence of what the generator produced before a rule changed.
- **Controlled language realization via closed-set membership, not classification.** The boundaries between `EN`/`IN_EN`, `ROM_HI`/`HINGLISH`, and `HINGLISH`/`INFORMAL_HINGLISH` are each defined as a closed-set membership test against a frozen, enumerable inventory (marker words, loanwords, informal categories) — a deterministic, auditable boundary, not an LLM-judged or fuzzy one, even though the surface content itself may be paraphrased.
- **A validation contract's own limitations documented alongside the contract.** Both the OQ-036 (`EN`) and OQ-037 (six-condition) semantic-use contracts explicitly state what they cannot detect (distinguishing "wrong role" from "role never asserted") in the same governing-document section that defines what they can detect — the coarseness of the check is part of its frozen specification, not an implementation footnote discovered later.
- **A governance record that survives its own errors.** The evaluation-layer self-audit (OQ-031, OQ-032) is preserved in this log and in `annotation/open_questions.md` even though it documents this project correcting its *own* prior proposals — the audit trail includes the mistakes that were caught, not only the decisions that were right the first time.

---

## T12 — Adversarial Perturbation Implementation

**Specification Version:** `annotation/guidelines.md` **v0.18** (resolves **OQ-049**; companion contract `PROJECT_SPEC.md` v1.3).

**Scope and Governance:**
- **Selected Bases (20):** Fixed deterministically as the lowest permanent `base_id`s in `data/raw/base_instances.jsonl`:
  `PERSON_001`, `PERSON_002`, `ADDRESS_001`, `ADDRESS_002`, `PHONE_001`, `PHONE_002`, `EMAIL_001`, `EMAIL_002` (2 each for 12-base types);
  `PAN_001`, `PAN_002`, `PAN_003`, `AADHAAR_001`, `AADHAAR_002`, `AADHAAR_003`, `UPI_ID_001`, `UPI_ID_002`, `UPI_ID_003`, `BANK_ACCOUNT_001`, `BANK_ACCOUNT_002`, `BANK_ACCOUNT_003` (3 each for 13-base types).
- **Carrier Baseline:** Standard English canonical carrier text (`base.canonical_text`) exclusively, isolating perturbation robustness ($E05$) from multilingual/code-mixing confounds ($E02$).
- **Five Perturbation Families ($A_1$–$A_5$):**
  1. **$A_1$ SPACING** (`target: VALUE`, `severity: 1`): `" ".join(c for c in v)` for single-token; intra-word single space and inter-word double space for multi-word (`PERSON`, `ADDRESS`).
  2. **$A_2$ PUNCTUATION** (`target: VALUE`, `severity: 1`): Fixed per-type structural delimiters (`PAN` 5-4-1, `AADHAAR`/`BANK_ACCOUNT` 4-4-4, `PHONE` 5-5, `PERSON` hyphen, `EMAIL` local hyphen before digits `sneha-8298@...`, `UPI_ID` 5-5 local phone hyphen `99965-07527@...`, `ADDRESS` slash).
  3. **$A_3$ LABEL_OBFUSCATION** (`target: LABEL`, `severity: 1`): Literal prefix obfuscation (`My P.A.N. No.: `, `My N.A.M.E: `, etc.), holding PII value byte-identical.
  4. **$A_4$ INFORMAL_ABBREVIATION** (`target: LABEL`, `severity: 1`): Literal prefix abbreviation (`pan no: `, `name: `, etc.), holding PII value byte-identical.
  5. **$A_5$ CHARACTER_VARIATION** (`target: VALUE`, `severity: 1`): Casing for alphanumeric/text (`PAN`, `PERSON`, `ADDRESS` lower; `EMAIL`, `UPI_ID` upper); **M2 Single-Character OCR Substitution** for numeric types (`PHONE`, `AADHAAR`, `BANK_ACCOUNT`) using visual homoglyphs `{'0': 'O', '1': 'l', '5': 'S', '8': 'B'}` on the first matching digit (exactly one character mutated per numeric entity).

**Implementation Architecture:**
- `generators/perturbations/spacing.py`: Pure deterministic $A_1$ transform.
- `generators/perturbations/punctuation.py`: Pure deterministic $A_2$ transform.
- `generators/perturbations/label_obfuscation.py`: Pure deterministic $A_3$ transform.
- `generators/perturbations/abbreviation.py`: Pure deterministic $A_4$ transform.
- `generators/perturbations/char_variation.py`: Pure deterministic $A_5$ transform.
- `generators/perturbations/__init__.py`: Package export.
- `generators/language/adversarial_records.py`: Orchestrator assembling 100 adversarial records with occurrence-aware span extraction (`find_occurrence`).

**Test-First Process & Validation:**
- Pre-generation governance tests in `tests/test_t12_adversarial_governance.py` (10 tests).
- Pre-generation unit tests in `tests/test_generate_adversarial_records.py` (15 tests).
- Generated initially to temporary files; verified across two independent runs for zero nondeterminism.
- Validated against `schemas/example.schema.json` (100/100 pass, 0 errors).
- Validated span integrity `text[start:end] == realized_pii_value` (100/100 pass, 0 mismatches).
- Canonical dataset written to `data/generated/adversarial_realizations.jsonl`.
- Reloaded in fresh process and verified independently.

**Dataset Cardinality & Provenance Hashes:**
- `data/raw/base_instances.jsonl`: 100 records, MD5 `7006b0c9227d93541d2b71f702407ecc` (Unmutated).
- `data/raw/hard_negative_bases.jsonl`: 20 records, MD5 `b36c6c106548d18ff7083fd00532cb07` (Unmutated).
- `data/generated/language_realizations.jsonl`: 624 records, MD5 `0cb046740507eb9111a214b24b680483` (Unmutated).
- `data/generated/hard_negative_realizations.jsonl`: 120 records, MD5 `ae5537eec4129822e3d97b05170b4fea` (Unmutated).
- `data/generated/adversarial_realizations.jsonl`: **100 records**, MD5 `1b678b9597737c85197acf80ab56878d` (New canonical artifact).
- **Combined Benchmark Corpus Cardinality:** 100 positive bases + 20 hard-negative bases + 624 clean realizations + 120 hard-negative realizations + 100 adversarial realizations = **964 total records** (844 derived records).

**Test Suite Verification:**
- `pytest` suite: **715 passed in 1.58s** across two consecutive runs.

**Strict Boundary at T12:**
- T12 completed the benchmark corpus generation.

---

## T13 / E01 — Benchmark Experiment E01: Structured Regex Baseline

**Specification Version:** `annotation/guidelines.md` **v0.18**; companion contract `PROJECT_SPEC.md` §§19–24 (v1.3).

**Scope and Implementation:**
- `baselines/regex.py`: Concrete `RegexBaselineAdapter` (B1, v1.0.0) focusing purely on canonical structural formats for Indian PII:
  - `PAN`: `\b[A-Z]{5}[0-9]{4}[A-Z]\b`
  - `AADHAAR`: Spaced 4-4-4 and unspaced 12-digit formats
  - `PHONE`: Indian 10-digit mobile with optional `+91` prefix and 5+5 split
  - `EMAIL`: RFC 5322 syntax (evaluated after UPI precedence)
  - `UPI_ID`: Synthetic VPA handles and major PSP handle domains
  - `BANK_ACCOUNT`: Contextual 9–18 digit account sequences
  - Free-text `PERSON` and `ADDRESS` have no heuristic keyword guessing rules, demonstrating the structural ceiling baseline per §19.1.
- `benchmark/runner.py`: Deterministic experiment orchestrator (`load_canonical_benchmark_records`, `run_experiment`).

**Formal Benchmark Results (E01 Regex Baseline):**
- **Corpus Evaluated:** 964 total instances (724 gold PII entities, 140 non-PII hard-negative instances).
- **Total Predictions Emitted:** 582 (0 rejected, 100% structurally valid).
- **Headline Performance Metrics:**
  - $M_1$ Precision: **64.78%** ($377 / 582$)
  - $M_2$ Recall: **52.07%** ($377 / 724$)
  - $M_3$ Type-Strict $F_1$: **57.73%**
  - $M_4$ Exact-Boundary $F_1$: **57.73%** ($377 \text{ TP}_{\text{exact}}$)
  - $M_5$ Type Accuracy: **84.91%** ($377 / 444$)
  - $M_6$ False Positive Rate: **23.71%** ($138 / 582$)
- **Primary Error Partition:** $F_1$ Missed = 280, $F_2$ Wrong Span = 0, $F_3$ Wrong Type = 67, $F_4$ False Positive = 138 ($280 + 0 + 67 + 377 \equiv 724$).
- **Artifacts Persisted & Frozen:**
  - `predictions/regex_1.0.0_v0.18.jsonl` (MD5: `8913ac633854a36948a3445e4be0594d`)
  - `reports/evaluation_regex_1.0.0_v0.18.json` (MD5: `2958f77985fcc70d704c123e9e952ebd`)
- **Full Test Suite Status:** 859 passing tests.

---

## T13 / B2 — Benchmark Experiment B2: General NLP Baseline (spaCy NER)

**Specification Version:** `annotation/guidelines.md` **v0.18**; companion contract `PROJECT_SPEC.md` §§19–24 (v1.3).

**Scope and Implementation:**
- `baselines/spacy.py`: `SpacyBaselineAdapter` (B2, `system_name="spacy"`, `system_version="3.8.16_en_core_web_sm_3.8.0"`).
  - Uses standard off-the-shelf English pretrained NER model (`en_core_web_sm`, OntoNotes 5.0 18-label inventory).
  - Mapping policy (§20.5, resolving OQ-032): Direct 1-to-1 map `PERSON` $\rightarrow$ `PERSON`. All other 17 OntoNotes labels (`ORG`, `GPE`, `LOC`, `DATE`, `CARDINAL`, etc.) are preserved as raw type strings with status `"VALID"`.
  - Unsupported Indian PII formats produce zero artificial predictions.
- `tests/test_baselines_spacy.py`: 10 unit tests for adapter contract, metadata, offsets, and input immutability.
- `tests/test_b2_reproducibility.py`: 2 regression tests verifying deterministic predictions and exact metric replication.

**Formal Benchmark Results (B2 spaCy NER Baseline):**
- **Corpus Evaluated:** 964 total instances (724 gold PII entities, 140 non-PII hard-negative instances).
- **Total Predictions Emitted:** 1398 (0 rejected, 100% structurally valid).
- **Headline Performance Metrics:**
  - $M_1$ Precision: **3.15%** ($44 / 1398$)
  - $M_2$ Recall: **6.08%** ($44 / 724$)
  - $M_3$ Type-Strict $F_1$: **4.15%**
  - $M_4$ Exact-Boundary $F_1$: **3.30%** ($35 \text{ TP}_{\text{exact}}$)
  - $M_5$ Type Accuracy: **8.54%** ($44 / 515$)
  - $M_6$ False Positive Rate: **63.16%** ($883 / 1398$)
- **Primary Error Partition:** $F_1$ Missed = 209, $F_2$ Wrong Span = 9, $F_3$ Wrong Type = 471, $F_4$ False Positive = 883 ($209 + 9 + 471 + 35 \equiv 724$).
- **Key Findings:**
  - `PERSON` detection: $F_1 = 42.31\%$ (Prec: 38.60%, Rec: 46.81%), recovering 44 of 94 names.
  - Zero detection ($0.00\% \text{ } F_1$) on all 7 structured Indian PII types (`PAN`, `AADHAAR`, `PHONE`, `EMAIL`, `UPI_ID`, `BANK_ACCOUNT`, `ADDRESS`).
  - High out-of-taxonomy false positives ($F_4 = 883$) due to standard OntoNotes entities (`CARDINAL`, `DATE`, `ORG`, `GPE`).
- **Artifacts Persisted & Frozen:**
  - `predictions/spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.jsonl` (MD5: `6c74bd4ec742a1f0c6b8024200937fb5`)
  - `reports/evaluation_spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.json` (MD5: `a9745314b2e71df861ea71af15a9dd1a`)
- **Full Test Suite Status:** 871 passing tests.

---

## T13 / B3 — Benchmark Experiment B3: Production Framework Baseline (Microsoft Presidio)

**Specification Version:** `annotation/guidelines.md` **v0.18**; companion contract `PROJECT_SPEC.md` §§19–24 (v1.3).

**Scope and Implementation:**
- `baselines/presidio.py`: `PresidioBaselineAdapter` (B3, `system_name="presidio"`, `system_version="2.2.364_en_core_web_sm_in_enabled"`).
  - Uses standard off-the-shelf Presidio `AnalyzerEngine` initialized with `spacy` (`en_core_web_sm`) and enabled India country recognizers (`InPanRecognizer`, `InAadhaarRecognizer`, `InPassportRecognizer`, `InVehicleRegistrationRecognizer`, `InVoterRecognizer`, `InGstinRecognizer`).
  - Mapping policy (§20.5, resolving OQ-032): `PERSON` $\rightarrow$ `PERSON`, `IN_PAN` $\rightarrow$ `PAN`, `IN_AADHAAR` $\rightarrow$ `AADHAAR`, `PHONE_NUMBER` $\rightarrow$ `PHONE`, `EMAIL_ADDRESS` $\rightarrow$ `EMAIL`. All other Presidio labels (`ORGANIZATION`, `LOCATION`, `DATE_TIME`, `URL`, `UK_NHS`, `US_BANK_NUMBER`, etc.) are preserved raw with status `"VALID"`.
  - Unsupported Indian PII formats (`UPI_ID`, `BANK_ACCOUNT`, `ADDRESS`) have zero custom recognizers or artificial guesses.
- `tests/test_baselines_presidio.py`: 14 unit tests for adapter contract, metadata, in-taxonomy detection, out-of-taxonomy preservation, offsets, and input immutability.
- `tests/test_b3_reproducibility.py`: 2 regression tests verifying deterministic predictions and exact metric replication.

**Formal Benchmark Results (B3 Microsoft Presidio Baseline):**
- **Corpus Evaluated:** 964 total instances (724 gold PII entities, 140 non-PII hard-negative instances).
- **Total Predictions Emitted:** 2,792 (0 rejected, 100% structurally valid).
- **Headline Performance Metrics:**
  - $M_1$ Precision: **7.66%** ($214 / 2792$)
  - $M_2$ Recall: **29.56%** ($214 / 724$)
  - $M_3$ Type-Strict $F_1$: **12.17%**
  - $M_4$ Exact-Boundary $F_1$: **11.49%** ($202 \text{ TP}_{\text{exact}}$)
  - $M_5$ Type Accuracy: **31.15%** ($214 / 687$)
  - $M_6$ False Positive Rate: **75.39%** ($2105 / 2792$)
- **Primary Error Partition:** $F_1$ Missed = 37, $F_2$ Wrong Span = 12, $F_3$ Wrong Type = 473, $F_4$ False Positive = 2,105 ($37 + 12 + 473 + 202 \equiv 724$).
- **Key Findings:**
  - `PAN`: $F_1 = 56.07\%$ (Prec: 39.47%, Rec: 96.77%), recovering 90 of 93 PANs via `InPanRecognizer`.
  - `PHONE`: $F_1 = 31.43\%$ (Prec: 18.74%, Rec: 97.56%), recovering 80 of 82 phone numbers via `PhoneRecognizer`.
  - `PERSON`: $F_1 = 42.93\%$ (Prec: 39.64%, Rec: 46.81%), recovering 44 of 94 names via spaCy NER.
  - Zero detection ($0.00\% \text{ } F_1$) on `UPI_ID`, `BANK_ACCOUNT`, `ADDRESS`, `AADHAAR` (Verhoeff checksum rejected synthetic UIDs; spaced Aadhaar numbers tagged as `DATE_TIME`/`CARDINAL`).
- **Artifacts Persisted & Frozen:**
  - `predictions/presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.jsonl` (MD5: `2c661403efa963275be5f2559a1577b9`)
  - `reports/evaluation_presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.json` (MD5: `4831393231e3d15dc674166dcaaaa2b9`)
- **Full Test Suite Status:** 887 passing tests.

---

## T13 / B4 — Benchmark Experiment B4: Zero-Shot Multilingual Transformer Baseline (XLM-RoBERTa)

**Specification Version:** `annotation/guidelines.md` **v0.18**; companion contract `PROJECT_SPEC.md` §§19–24 (v1.3).

**Scope and Implementation:**
- `baselines/transformer.py`: `TransformerBaselineAdapter` (B4, `system_name="transformer"`, `system_version="5.16.1_Davlan_xlm-roberta-base-ner-hrl"`).
  - Evaluates the single audited multilingual model: `Davlan/xlm-roberta-base-ner-hrl` (revision `253f557bd8249b8515114cfd7f71974fe5fa4d2f`) using `transformers==5.16.1` and `torch==2.13.0`.
  - Aggregation: Hugging Face `token-classification` pipeline with `aggregation_strategy="simple"`.
  - Mapping policy (§20.5, resolving OQ-032): `PER` / `PERSON` $\rightarrow$ `PERSON`. All other emitted labels (`LOC`, `ORG`, `DATE`, `MISC`) are preserved raw with status `"VALID"`.
  - Unsupported Indian PII formats (`PAN`, `AADHAAR`, `PHONE`, `EMAIL`, `UPI_ID`, `BANK_ACCOUNT`, `ADDRESS`) produce zero artificial predictions or post-hoc heuristics.
- `tests/test_baselines_transformer.py`: 11 unit tests for adapter contract, metadata, Devanagari script extraction, out-of-taxonomy preservation, offsets, and input immutability.
- `tests/test_b4_reproducibility.py`: 2 regression tests verifying deterministic predictions and exact metric replication.

**Formal Benchmark Results (B4 Multilingual Transformer Baseline):**
- **Corpus Evaluated:** 964 total instances (724 gold PII entities, 140 non-PII hard-negative instances).
- **Total Predictions Emitted:** 467 (0 rejected, 100% structurally valid).
- **Headline Performance Metrics:**
  - $M_1$ Precision: **20.13%** ($94 / 467$)
  - $M_2$ Recall: **12.98%** ($94 / 724$)
  - $M_3$ Type-Strict $F_1$: **15.79%**
  - $M_4$ Exact-Boundary $F_1$: **14.44%** ($86 \text{ TP}_{\text{exact}}$)
  - $M_5$ Type Accuracy: **50.81%** ($94 / 185$)
  - $M_6$ False Positive Rate: **60.39%** ($282 / 467$)
- **Primary Error Partition:** $F_1$ Missed = 539, $F_2$ Wrong Span = 8, $F_3$ Wrong Type = 91, $F_4$ False Positive = 282 ($539 + 8 + 91 + 86 \equiv 724$).
- **Key Findings:**
  - `PERSON`: $F_1 = 90.82\%$ (Prec: 83.19%, Rec: 100.00%), recovering **94 of 94 names** across English and Hindi.
  - Script Robustness: XLM-RoBERTa is the **first baseline** to successfully detect Devanagari names natively in `HI_DEVA_PII` ($F_1 = 29.27\%$, Recall = 50.00%).
  - Zero detection ($0.00\% \text{ } F_1$) on structured Indian PII types (`PAN`, `AADHAAR`, `PHONE`, `EMAIL`, `UPI_ID`, `BANK_ACCOUNT`) due to lack of domain-specific entity heads.
  - Addresses detected as `LOC` ($F_3 = 91$), correctly scored as wrong type against the `ADDRESS` gold class.
- **Artifacts Persisted & Frozen:**
  - `predictions/transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.jsonl` (MD5: `3f53b646fb9f95414bef8b972d2277b1`)
  - `reports/evaluation_transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.json` (MD5: `dfe7e6b93e15ca266b29121977b1809e`)
- **Full Test Suite Status:** 900 passing tests.
