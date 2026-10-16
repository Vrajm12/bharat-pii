# Annotation Guidelines Changelog

## v0.18 — FROZEN — resolves OQ-049 (T12 adversarial perturbation specification)

**Change:** freezes the complete specification for the 100 adversarial variants ($A_1$–$A_5$)
(§14.5–§14.8, decision 50), resolved by explicit human decision following a 2-stage adversarial
methodology audit (`annotation/open_questions.md`).

- **Base Selection (§14.5):** 20 positive bases selected deterministically as the lowest
  permanent `base_id`s within each category (3 each for `PAN`, `AADHAAR`, `UPI_ID`, `BANK_ACCOUNT`;
  2 each for `PERSON`, `ADDRESS`, `PHONE`, `EMAIL`).
- **Carrier Text Baseline (§14.6):** All 100 adversarial records are derived from the base's
  canonical English text (`base.canonical_text`), isolating perturbation effects from code-mixing
  confounds (Experiment E05).
- **Deterministic Perturbation Specifications (§14.7):**
  - **$A_1$ SPACING:** `" ".join(c for c in v)` for single-token values; single space intra-word and
    double space inter-word for multi-word values (`PERSON`, `ADDRESS`).
  - **$A_2$ PUNCTUATION:** Fixed per-type structural delimiters (`PAN` 5-4-1, `AADHAAR`/`BANK_ACCOUNT` 4-4-4,
    `PHONE` 5-5, `PERSON` hyphen, `EMAIL` local hyphen before digits `sneha-8298@...`,
    `UPI_ID` 5-5 local phone hyphen `99965-07527@...`, `ADDRESS` slash).
  - **$A_3$ LABEL_OBFUSCATION:** Exact carrier prefix obfuscation mapping (`My P.A.N. No.: `, `My N.A.M.E: `, etc.),
    preserving PII value byte-identically.
  - **$A_4$ INFORMAL_ABBREVIATION:** Exact carrier prefix informal abbreviation mapping (`pan no: `, `name: `, etc.),
    preserving PII value byte-identically.
  - **$A_5$ CHARACTER_VARIATION:** Casing for alphanumeric/text (`PAN`, `PERSON`, `ADDRESS` lowercase;
    `EMAIL`, `UPI_ID` uppercase); **M2 Single-Character OCR Substitution** for numeric types (`PHONE`,
    `AADHAAR`, `BANK_ACCOUNT`) using visual homoglyphs `{'0': 'O', '1': 'l', '5': 'S', '8': 'B'}` on the
    first matching digit (exactly one character mutated per numeric entity).
- **Metadata Contract (§14.8):** `variant_id = "{base_id}_EN_{family}_01"`, `difficulty: "ADVERSARIAL"`,
  `perturbation.severity: 1`.

**Why:** establishes a rigorous, scientifically defensible, and 100% deterministic generation
specification. Replaces synthetic 10-digit leetspeak with realistic single-character OCR homoglyphs
($M_2$) and resolves email/UPI punctuation mechanics without altering underlying identifier identity.

**What this does not do:** does not modify any existing dataset file; does not create generator
implementation files (implementation is a separate, subsequent step); does not create benchmark or
evaluator code.

**Records affected:** none. No adversarial record exists yet. The existing 100 positive bases, 20
hard-negative bases, 624 positive realizations, and 120 hard-negative realizations are untouched.

**Also updated:** `PROJECT_SPEC.md` `guidelines_version` pointer (header + §35), `configs/pilot.yaml`,
`tests/fixtures/example.valid.json` bumped to `0.18`.

---

## v0.17 — FROZEN — resolves OQ-047 (hard-negative Hindi/Hinglish realization inventory)

**Change:** freezes the lexical content OQ-047's audit found missing — a closed,
benchmark-specific inventory (§13.13, decision 49), not a general-purpose translation
system, resolved as a human decision after two audit passes found no candidate
supported by existing evidence alone (`annotation/open_questions.md`).

- **Four new concept words:** "order," "reference code" (compound), "station,"
  "contact" — each explicitly labeled as newly frozen, distinct from the words this
  entry reuses unchanged ("mera," "hai" §4.10; "number," "account" §4.13; "ke paas"
  §7.2).
- **One new `ROM_HI`/Devanagari carrier template per constructible decoy class**
  (`NUMERIC_SHAPE`, `ALNUM_SHAPE`, `NAME_AS_PLACE`, `HANDLE_SHAPE`, `PARTIAL_PII`).
  `PARTIAL_PII`'s template uses zero new words but is itself frozen for the first time
  — reusing already-frozen words does not make an unstated sentence-assembly principle
  already frozen, the distinction the prior audit specifically raised.
- **`HINGLISH`/`INFORMAL_HINGLISH` construction requires no additional vocabulary at
  all** — confirmed by direct execution that `generators/language/templates.py`'s
  `HINGLISH_PATTERNS` are pure, PII-type-independent string operations, reused
  unchanged.

**Why:** two full audit passes (`OQ-047`, this project's design-report-then-decision-
memo pattern) established that Candidates A (existing generic vocabulary), B (reuse an
existing PII carrier), C (mechanical translation), and E (collapsing conditions) are
each either unsupported by existing evidence or explicitly excluded by the non-PII
constraint (`HANDLE_SHAPE` reusing EMAIL's carrier was rejected specifically because it
would falsely assert the distractor is an email). Candidate D — freeze new content — was
therefore the only remaining path, and is adopted here exactly as scoped in the audit,
not expanded beyond it.

**What this does not do:** does not touch `ORG_AS_PERSON` (remains deferred, quota 0);
does not change the six-realization count (§13.11); does not create or modify any
schema, validator, or generator file — Phase 2 implementation remains a separate, later
step, the same relationship §13.8's `canonical_text` templates had to T04 before any
generator read them.

**Records affected:** none. No hard-negative derived record exists yet.

**Also updated:** `PROJECT_SPEC.md` `guidelines_version` pointer (header + §35),
`configs/pilot.yaml`, `tests/fixtures/example.valid.json` bumped to `0.17`.
`tests/test_t11_phase2_governance.py` extended with tests proving the frozen table,
the A/B labeling, and that Phase 2 still has not been implemented.

**OQ-048 (distractor-span validation) is unaffected — still unresolved.** This entry
governs carrier *content*, not whether `validators/spans.py`'s formal contract should
be extended to check distractor spans; that remains a separate question.

---

## v0.16 — FROZEN — resolves OQ-046 (hard-negative construction ground-truth architecture)

**Change:** a schema/architecture gap found while auditing T11 Phase 1 (base-instance
generation) before writing any generator code — closed by explicit human decision
(PATH 1, approved), not invented.

- **New optional field, `hard_negative_decoy`** (§13.12, decision 48), on
  `schemas/base_instance.schema.json`: construction-level ground truth for a
  `HARD_NEGATIVE` base's single decoy (`decoy_class`, `value`, `surface_type`,
  `actual_role`). Not added to the schema's top-level `required` array — the 100
  existing `POSITIVE` bases remain valid and byte-identical without it.
- **New cross-field invariant** in `validators/base_kind.py`
  (`check_base_kind_hard_negative_decoy_invariant`): `POSITIVE` requires the field
  absent or null; `HARD_NEGATIVE` requires it present and populated. Deliberately kept
  out of the schema (no `if`/`then`) for consistency with the base_kind/`pii`
  invariant's own precedent (decision 16), not because JSON Schema cannot express it.

**Why:** `pii[]` must stay empty for `HARD_NEGATIVE` (decision 16, unchanged) and
`entities[]`/`distractors[]` must stay derived-record-only (§13.4, unchanged) — but
that left literally nowhere on the base instance to persist which decoy_class/value/
role/surface_type a given base was constructed with, unlike positive bases, where
`pii[]` already serves that role. Re-deriving this from `base_id` + RNG replay at
derived-record-generation time was considered and rejected: it would make hard-negative
derivation depend on exactly replaying the base generator's RNG sequence, a coupling no
other `base_kind` has (T08 reads only `base.pii[]`, never re-runs T04's generator).

**Records affected:** none. No hard-negative base instance exists yet — this closes a
schema/architecture gap discovered during design, before Phase 1 generation. The 100
existing `POSITIVE` bases are unaffected: the new field is optional, and none of them
carry it.

**Also updated:** `PROJECT_SPEC.md` `guidelines_version` pointer (header + §35),
`configs/pilot.yaml`, `tests/fixtures/example.valid.json` bumped to `0.16`.
`tests/test_schemas.py` and `tests/test_base_kind_invariant.py` extended with 11 new
tests proving: existing positive bases remain valid without the field; a valid
`HARD_NEGATIVE` base with the field is valid; a `HARD_NEGATIVE` base without it is
rejected by the new validator invariant (not the schema); invalid `decoy_class`,
missing `value`/`surface_type`/`actual_role`, and extra fields are all rejected;
`pii: []` remains mandatory for `HARD_NEGATIVE`; and `entities`/`distractors` remain
rejected as unknown properties on the base instance.

---

## v0.15 — FROZEN — resolves OQ-044; resolves OQ-042 for `HANDLE_SHAPE` (`ORG_AS_PERSON` deferred, not resolved)

**Change:** the two remaining T11 blockers, resolved by explicit human decision after a
final governance audit found neither uniquely determined by the frozen text alone
(`annotation/open_questions.md`, `docs/research/construction_log.md`).

- **OQ-042, `HANDLE_SHAPE` (§13.8, decision 45):** frozen as EMAIL's own
  `_LOCAL_PART_WORDS`/`_DOMAIN_LABELS` construction (`generators/pii/email.py`) with
  the reserved TLD omitted — verified to fail both EMAIL's and UPI_ID's frozen
  structural regexes, and to leave both types' own generation rules completely
  unchanged.
- **OQ-042, `ORG_AS_PERSON` (§13.8, decision 46):** deferred from Pilot v0.1, not
  resolved constructively — no concrete worked value or construction pattern exists
  anywhere in either governing document, confirmed by two independent repository-wide
  audits, and none was invented. Its 3-base quota allocation is redistributed (OQ-043's
  table, updated in place, not reopened) to `NUMERIC_SHAPE`, `ALNUM_SHAPE`, and
  `NAME_AS_PLACE` (§13.9) so the pilot's 20 hard-negative bases remain fully accounted
  for. The original six-decoy-class design intent is preserved as recorded history;
  Pilot v0.1's actual set covers five.
- **OQ-044 (§13.11, decision 47):** hard-negative derived records use six
  realizations — `EN`, `IN_EN`, `ROM_HI`, `HINGLISH`, `INFORMAL_HINGLISH`, and one
  collapsed Hindi realization — a deliberate, explicitly-labeled extension of §8.1's
  PII-script-isolation rationale to bases with no PII value at all, not a claim that
  §8.1's text already named hard negatives. 20 × 6 = 120 hard-negative derived records.

**Why:** both gaps survived a design report, an initial governance pass, and a final
repository-wide evidence audit without converging on a uniquely-determined answer — at
that point, per this project's own established protocol (OQ-004–011's pattern of
presenting evidence-grounded candidates for explicit human choice rather than picking
one silently), the decision was escalated to the user and made explicitly. Neither
decision is presented as "the specification already said this" — both are recorded as
what they are: a human choice made from a set of evidence-audited candidates, not a
formalization of something already implicit.

**What this does not do:** does not invent an `ORG_AS_PERSON` grammar to hit "all 6
classes" (a live option that was explicitly rejected); does not adopt the
literally-largest candidate (140, full seven-condition treatment) or the
smallest-and-only-numerically-attested one (~60) for OQ-044, choosing instead the
reading best grounded in existing architectural rationale even though it required an
explicit extension beyond §8.1's literal wording.

**Not touched:** `PROJECT_SPEC.md` beyond its `guidelines_version` pointer. §32's
Definition-of-Done checklist item ("all 6 decoy classes present") is now in tension
with `ORG_AS_PERSON`'s deferral — flagged, not silently corrected, since only the
`guidelines_version` pointer was in scope for this revision.

**Records affected:** none. No hard-negative base instance or derived record exists yet
— this is governance only. The existing 100 positive bases and 624 positive derived
records are untouched.

**Also updated:** `PROJECT_SPEC.md` `guidelines_version` pointer (header + §35),
`configs/pilot.yaml`, `tests/fixtures/example.valid.json` bumped to `0.15`.
`tests/test_t11_hard_negative_governance.py` extended with tests proving each new
decision, the `ORG_AS_PERSON` non-invention, the 20×6=120 arithmetic, and that no
implementation code exists.

---

## v0.14 — FROZEN — resolves OQ-043, OQ-045; partially resolves OQ-042; T11 partially unblocked

**Change:**

- **OQ-042, partial (§13.8, decision 42):** four of the six hard-negative decoy classes
  (`NUMERIC_SHAPE`, `ALNUM_SHAPE`, `NAME_AS_PLACE`, `PARTIAL_PII`) get a deterministic
  construction rule — value shape, `actual_role`, `surface_type`, and a `canonical_text`
  template each — built entirely by reusing formats and vocabulary already frozen
  elsewhere (T05's PHONE/AADHAAR/BANK_ACCOUNT/PAN regexes; T03's PERSON given-name list;
  §6's explicit `surface_type: "LOCATION"` cross-reference for the "Rahul Nagar" case).
  No new PII format, name list, or suffix list was invented. `HANDLE_SHAPE` and
  `ORG_AS_PERSON` remain explicitly unresolved — §13.3's table gives them only a
  description, never a concrete worked value, so no rule could be derived without
  inventing one.
- **OQ-043 (§13.9, decision 43):** the 20 hard-negative bases split 4/4/3/3/3/3 across
  the six classes, remainder assigned by §13.3's own table order.
- **OQ-045 (§13.10, decision 44):** every hard-negative derived record carries
  `context: "EXPLICIT"`, by direct analogy to decision 38's T08 freeze.

**Why:** T11 (hard negatives) needed all three before any base instance could be
generated. OQ-042 could only be partially closed — `HANDLE_SHAPE`/`ORG_AS_PERSON` have
no textual anchor to build a rule from, and this project's own established discipline
(OQ-004–011, OQ-035–041) does not treat a bare class name and one-line description as
license to invent a format. OQ-043 and OQ-045 had no such obstacle and are fully closed.

**Not resolved by this revision:** **OQ-044** (hard-negative language-condition count,
and therefore the exact derived-record count after T11) remains **unresolved** — this
turn's own investigation found a *third* plausible reading beyond the two already on
file (a "no PII script axis" argument for extending the six-realization collapse rule to
hard negatives, yielding 120 records rather than the ~60 estimate or a 3-condition
subset), which deepens rather than resolves the ambiguity. No number was picked.

**Records affected:** none. No hard-negative base instances or derived records exist yet
— this is governance only, verified against the actual frozen T03/T05 formats and
vocabulary it reuses, not the 100/624 existing dataset files, which this revision does
not touch.

**Also updated:** `PROJECT_SPEC.md` `guidelines_version` pointer (header + §35),
`configs/pilot.yaml`, `tests/fixtures/example.valid.json` bumped to `0.14`.
`tests/test_t11_hard_negative_governance.py` (new) proves each frozen rule against the
actual T03/T05 source it claims to reuse, and proves `generators/hard_negatives.py`,
`validators/spans.py`, and the dataset files remain untouched.

---

## v0.13 — FROZEN — resolves OQ-037; unblocks T10 for all seven language conditions

**Change:**

- **OQ-037 (new §13.7, decision 41):** Layer 3 ground truth for the six conditions
  §13.6 left open. `IN_EN` gets canonical-text **containment** (generalizing §13.6's `EN`
  equality, since `IN_EN` = `EN` plus wrapping material, never a rewrite — verified: all
  100 `IN_EN` records contain `base.canonical_text` verbatim). The remaining five
  (`ROM_HI`, `HINGLISH`, `INFORMAL_HINGLISH`, `HI_LATIN_PII`, `HI_DEVA_PII`) get a frozen
  per-type label-word table, assembled from words already frozen elsewhere in this
  document (§4.10's carrier vocabulary, §4.13's loanword table and its Aadhaar note,
  §5.1/§16's PERSON worked examples) — no new word chosen, only compiled for a new
  validation purpose. Verified against all 624 frozen records: zero failures.

**Why:** T10 needed ground truth for every one of the seven conditions, not `EN` alone.
The two rejected mechanisms — re-using the T08 carrier templates as an oracle, and an
ad-hoc keyword list invented for this decision — were both explicitly out of bounds
(circularity in the first case, unfrozen invention in the second). The label table
avoids both: its words predate and are independent of T08's implementation, and a
generator bug that mismatched type↔label would still be caught by it, proving the check
is not merely testing self-consistency.

**What this does not do:** neither mechanism can distinguish "value used in the wrong
role" from "value present, role never asserted" — both surface as the same miss. Finer
discrimination would require sentence-structure parsing, which this decision does not
attempt, matching the same coarseness already accepted for `EN` in v0.12.

**Schema verified, not changed:** no new field. No schema file was modified this round.

---

## v0.12 — FROZEN — resolves OQ-035, OQ-036; unblocks T10

**Change:**

- **OQ-035 (§13.5, decision 39):** the complete eight-type `semantic_role` mapping is now
  written into the table — previously only `PERSON` appeared (the row OQ-007 changed).
  The other seven values were already in effect since T04's design freeze and are
  unchanged by this entry; it ratifies documentation, not the dataset. Verified against
  all 100 records of `data/raw/base_instances.jsonl`: exactly one `semantic_role` value
  per type, matching this table, no unexpected values.
- **OQ-036 (new §13.6, decision 40):** Layer 3 ("sentence uses the value in the declared
  role") gets a deterministic ground truth for unperturbed `EN` records only — exact
  equality between `record.text` and the source base's `canonical_text`, formalizing an
  equality that was already true by construction (verified against all 100 `EN` records,
  zero mismatches), not a new invention. Explicitly does **not** cover the other six
  language conditions, and explicitly does **not** reuse the T08 carrier templates or any
  keyword/label list as an oracle. The uncovered six conditions are logged as new OQ-037,
  left open.

**Why:** T10 (semantic validator) needs both before implementation can start. OQ-035 was
blocking because a validator checking type↔role consistency needs an independent,
non-generator-code table to check against. OQ-036 was blocking because "sentence uses the
value in its role" has no deterministic reading without either inventing a keyword
heuristic or covertly reusing the generator's own templates — both explicitly
disallowed. Neither gap is closed by picking the sensible-looking answer silently; both
are resolved here as recorded governance decisions with their evidence shown.

**Schema verified, not changed:** `semantic_role` remains free-form (`"type": "string",
"minLength": 1`, no enum) on `schemas/base_instance.schema.json`'s `pii[]` item — the
type-fixed constraint is cross-field logic (base's `type` field constrains what
`semantic_role` should be), enforced by a validator, not the schema, consistent with the
schema's structure-only scope established at T02. No schema file was modified this round.

---

## v0.11 — FROZEN — resolves OQ-013, OQ-014, OQ-027; unblocks T08

**Change:**

- **OQ-013 (§4.15, decision 36):** `pii_script` is determined from the realized span's
  actual script composition, never the PII type name. PERSON/ADDRESS follow condition
  (`LATIN`, `DEVANAGARI` only under `HI_DEVA_PII`); PHONE/AADHAAR/BANK_ACCOUNT →
  `NUMERIC`; PAN/EMAIL → `LATIN`; UPI_ID → `MIXED` (numeric local part + Latin domain).
  Worked examples added for all four non-trivial cases. No new enum value.
- **OQ-014 (§4.16, decision 37):** clean-record `variant_id` format frozen as
  `{base_id}_{language}`, no perturbation suffix; clean records carry
  `perturbation.family/type/target = "NONE"`. §17 gained a second worked example (a
  clean `EN` record) alongside the existing perturbed one, which is now explicitly
  labeled as defining only the perturbed-record format.
- **OQ-027 (new, §4.17, decision 38):** every T08 clean record carries `context:
  "EXPLICIT"`. Explicitly not a redesign of PROJECT_SPEC.md §9.1's C1–C4 allocation,
  which governs a separate, later pipeline stage.

**Why:** OQ-013 and OQ-014 were logged three turns ago (T08 design report) and never
resolved; both name required schema fields with no determinable value, blocking any
valid derived record from being constructed. OQ-027 is newly logged and resolved in the
same turn — the context-level gap was surfaced as an implicit assumption in the prior
turn's report, not previously a numbered open question.

**Schema verified, not changed:** `pii_script`'s enum already contains
`LATIN`/`DEVANAGARI`/`MIXED`/`NUMERIC`; `variant_id`'s pattern already accepts every
clean-record ID form; `context`'s enum already contains `EXPLICIT`; `perturbation`'s
three enums already contain `NONE`. No schema file was modified this round — none of
these decisions required it.

**Records affected:** none. `data/raw/base_instances.jsonl` and T04/T05/T07 are
untouched — this entry is governance only.

**Also updated:** `PROJECT_SPEC.md` and `configs/pilot.yaml` `guidelines_version`
pointers corrected from `0.10` to `0.11`. `tests/fixtures/example.valid.json` bumped.
New governance-verification tests added (not the T08 generator itself) — see the T08
governance-resolution report.

---

## v0.10 — FROZEN — resolves OQ-023, OQ-024, OQ-025, OQ-026

**Change:** freezes the T08 language-realization specification — new §4.10–§4.14:

- **OQ-026 (§4.10, decision 31):** T07 owns PII transliteration exclusively; T08 owns
  carrier-sentence construction. For `HI_DEVA_PII`, T08 obtains PERSON/ADDRESS
  Devanagari values from T07. No general-purpose Hindi transliteration/generation
  system is built.
- **New matched-variant invariant (§4.11, decision 32):** `HI_LATIN_PII` and
  `HI_DEVA_PII` must use byte-identical carrier text — the only difference is PII
  script. Makes E02b (script isolation) a controlled comparison by construction.
- **OQ-023 (§4.12, decision 33):** frozen 8-item Indian-English marker inventory
  (`kindly`, `do the needful`, `revert`, `prepone`, `please find below/attached`,
  `intimate`, `the same`, `at the earliest`). `IN_EN` requires ≥1; `EN` requires 0.
  Explicitly documented as legitimate dialectal features, not errors.
- **OQ-024 (§4.13, decision 34):** frozen 8-item ordinary-loanword inventory for
  `ROM_HI` (number/mobile/email/bank/account/address/PAN/UPI, each with a romanized and
  a Devanagari-carrier form) and a separate frozen HINGLISH insertion inventory
  (please/sir/confirm/actually/check/sorry/thanks/okay/problem/update). `ROM_HI` is
  restricted to the loanword inventory; `HINGLISH` requires ≥1 insertion beyond it — a
  closed-set membership test, not an LLM classification.
- **OQ-025 (§4.14, decision 35):** `INFORMAL_HINGLISH` = `HINGLISH`'s mixing + ≥1 marker
  from four frozen categories (abbreviation, casual particle, informal
  copula/contraction, typographic register).

**Why:** resolves OQ-023–026 (`annotation/open_questions.md`), each an explicit user
decision building on the T08 design report's proposal. The "at least one from a frozen
set" threshold is applied consistently across `IN_EN`, `HINGLISH`, and
`INFORMAL_HINGLISH` rather than three independently invented rules.

**Records affected:** none. The 624 language-realization records are not generated by
this entry — governance and specification only.

**Also updated:** `PROJECT_SPEC.md` and `configs/pilot.yaml` `guidelines_version`
pointers corrected from `0.9` to `0.10`. See the T08 implementation-specification report
for the full carrier-template architecture, deterministic validation rules, and human-
review criteria built on these inventories.

---

## v0.9 — FROZEN — resolves OQ-020, OQ-021, OQ-022; T07 implemented

**Change:**

- **OQ-020 (§4.5, new decision 28):** `generator_version` added as a required field to
  `schemas/base_instance.schema.json` — identical field name and semver pattern
  (`^[0-9]+\.[0-9]+\.[0-9]+$`) to the same field already on `schemas/example.schema.json`.
  No new field name or versioning convention invented.
- **OQ-021 (§4.4, new decision 29):** confirmed, not implemented — no
  `address_deva`/ADDRESS-equivalent field was added anywhere. `person_context.name_deva`
  remains the only stored base-level Devanagari field. ADDRESS's Devanagari form is
  generated later, at record-derivation time (T08), as `realized_pii_value`.
- **OQ-022 (§4.8, new decision 30):** `ABC` → `एबीसी` and `MG` → `एमजी` frozen as
  benchmark-specific deterministic table entries — explicitly documented as not claims
  about universal correct transliteration of these abbreviations. The frozen ADDRESS
  vocabulary (`generators/pii/address.py`) is unchanged.

**T07 implemented:** `generators/translit/table.py` (new) — a 79-entry token-level
lookup table (40 PERSON tokens + 39 ADDRESS lexical tokens), `transliterate_token()`
(single-token lookup, fails closed via `TransliterationError` on miss) and
`transliterate_value()` (tokenizes a full value on letter-runs/digit-runs/other-runs,
transliterates letter tokens only, passes digits and punctuation/spacing through
unchanged). No character-level substitution, no LLM, no probabilistic method, no
external library — matches §4.7–§4.9 exactly.

**Records affected:** `data/raw/base_instances.jsonl` — `person_context.name_deva`
populated for all 100 bases (previously `null` on all of them) and `generator_version:
"0.1.0"` added (previously absent, now required by the updated schema). No other field
changed; see the T07 implementation report for the full before/after diff.

**Also updated:** `PROJECT_SPEC.md` and `configs/pilot.yaml` `guidelines_version`
pointers corrected from `0.8` to `0.9`. `tests/fixtures/base_instance*.json` gained
`generator_version`. `generators/base_instances.py` now emits `generator_version` on
every record it assembles.

---

## v0.8 — FROZEN — resolves OQ-016, OQ-017, OQ-018, OQ-019

**Change:** freezes the T07 transliteration-table design, resolved in one batch by
explicit user decision:

- **OQ-016 (new §4.7):** the table is a **token-level lookup** — one entry per Latin
  token reachable from the frozen T03 PERSON/ADDRESS generators, joined per value. No
  character-level substitution, no LLM, no probabilistic method, no external
  general-purpose transliteration tool. Explicitly documented as *"a benchmark-specific
  deterministic transliteration table, not a general-purpose Hindi transliteration
  system."*
- **OQ-017 (new §4.8):** every ADDRESS lexical component reachable from the frozen
  generator needs an explicit table entry; numeric components (house numbers, PIN
  digits) stay unconverted ASCII digits; no rule invented for unreachable ADDRESS forms.
- **OQ-018 (new §4.9):** a lookup miss **fails closed** — deterministic error,
  reject/log, never guess, never LLM, never external service, never silent passthrough.
- **OQ-019:** no external transliteration library, at build time or runtime. The frozen
  table is itself the transliteration ground truth.

**Why:** these were the central blocking gaps identified in the T07 design report — the
governing documents said only "deterministic transliteration table," with no structural
definition, ADDRESS-specific handling, miss policy, or tooling stance. All four resolved
by explicit user decision rather than invented.

**Records affected:** none. `data/raw/base_instances.jsonl` untouched — `name_deva`
remains `null` on all 100 bases (populating it is a separate step, not part of this
governance update; see the T07 implementation-plan report for the investigation into
whether that constitutes modifying frozen T04 data).

**Not resolved by this entry:** OQ-020 (whether/how to add `generator_version` to
`schemas/base_instance.schema.json`) remains under investigation, reported but not
decided — no schema change was made. Two new open questions were logged: OQ-021 (no
schema field exists to store ADDRESS's equivalent of `name_deva`) and OQ-022 (no
transliteration method specified for the two ADDRESS abbreviation/initialism tokens,
`"ABC"` and `"MG"`).

**Also updated:** `PROJECT_SPEC.md` and `configs/pilot.yaml` `guidelines_version`
pointers corrected from `0.7` to `0.8`.

---

## v0.7 — FROZEN — resolves OQ-008, OQ-009, OQ-010, OQ-011

**Change:** freezes four T05-blocking ambiguities identified in the T05 structural-
validator design report, all resolved in one batch by explicit user decision:

- **OQ-008 (PHONE, new §8.1):** base representation (`base_pii_value`) frozen as
  `^[6789][0-9]{9}$` — no formatting. Formatted spans (`+91`, spacing, hyphens) remain
  the existing §8 annotation rule for realized text, unaffected — the two are
  explicitly distinguished so this doesn't read as a contradiction.
- **OQ-009 (EMAIL, new §9.1):** T05 structural grammar frozen — exactly one `@`,
  non-empty local part, domain ending in an exact-lowercase `.test`/`.invalid`/`.example`.
  Explicitly not full RFC 5321/5322 validation; no invented local-part restrictions.
- **OQ-010 (PAN, new §11.5):** structural representation frozen as uppercase-only,
  `^[A-Z]{5}[0-9]{4}[A-Z]$`. Lowercase is structurally invalid. No
  checksum/issuance/category-code validation.
- **OQ-011 (EMAIL/UPI_ID domain case, new §9.1 addendum + §10.4):** reserved domains
  matched as exact lowercase strings, never normalized. A UPI_ID value like
  `9876543210@paytm` is structurally invalid **because it fails the frozen grammar**,
  never described as invalid for resembling a real PSP handle — that distinction is
  frozen explicitly to keep the validator's stated reasoning honest.

**Why:** these were flagged as open ambiguities in the T05 design report (none had
governing-document backing strong enough to implement a hard validation rule from
directly) rather than invented silently. All four are narrow, implementation-adjacent
freezes — none change any already-frozen decision (1–19), none touch the six validation
layers, none touch `base_kind` or `semantic_role`.

**Records affected:** none — these are structural-validator rules, not base-instance
content. `data/raw/base_instances.jsonl` is unaffected.

**Also updated:** `PROJECT_SPEC.md` and `configs/pilot.yaml` `guidelines_version`
pointers corrected from `0.6` to `0.7`. `annotation/open_questions.md` gained OQ-008
through OQ-011, all logged RESOLVED (proposed and resolved in the same decision, unlike
earlier OQs that were logged unresolved and resolved later).

---

## v0.6 — FROZEN — resolves OQ-007

**Change:** new §13.5 establishes that `semantic_role` describes the role/type of the
PII value itself and is type-fixed (one value per PII type), while `scenario.domain`
and `scenario.purpose` carry the contextual use of that PII — the two are separate axes
and neither determines the other. Frozen as decision 19 in §21.

PERSON's frozen `semantic_role` changes from `ACCOUNT_HOLDER_NAME` to **`PERSON_NAME`**
— domain-neutral, so the same value correctly describes a PERSON base whether its
`scenario.domain` is `employment_hr`, `healthcare_administration`, `delivery_address`,
`banking_payments`, or `general_conversation`, without implying an account relationship
that doesn't exist in most of those domains.

**Why:** resolves OQ-007 (`annotation/open_questions.md`). A T04 data-review pass found
that `ACCOUNT_HOLDER_NAME` — approved as PERSON's frozen role in the T04 generation
design, since neither governing document specifies `semantic_role` for any type other
than PAN's one worked example — carries a banking/account connotation that doesn't fit
9 of the 12 generated PERSON records (only `delivery_address`, arguably, has any
account-adjacent reading; `employment_hr`, `healthcare_administration`, and
`general_conversation` do not). Candidate resolution 1 (label-only fix, keeping
`semantic_role` type-fixed) was chosen over making the role domain-dependent
(resolution 2) or accepting the mismatch as pilot-stage looseness (resolution 3).

**Records affected:** the 100 base instances in `data/raw/base_instances.jsonl` still
carry the superseded `ACCOUNT_HOLDER_NAME` value — this changelog entry updates the
generator and the governing documents only. The dataset itself is regenerated in a
separate, later step, not as part of this change.

**Also updated:** `generators/base_instances.py`'s `SEMANTIC_ROLE["PERSON"]` changed to
`"PERSON_NAME"`. No schema change — `semantic_role` was never enum-constrained
(`schemas/base_instance.schema.json` types it as a free string,
`{"type": "string", "minLength": 1}`), so no value change here requires a schema edit.
No test or fixture hardcoded `ACCOUNT_HOLDER_NAME` (verified by grep) — the one test that
checks the mapping (`test_all_records_use_frozen_semantic_role_mapping`) asserts against
the `SEMANTIC_ROLE` constant itself, so it tracks this change automatically.
`annotation/open_questions.md` OQ-007 marked RESOLVED.

`PROJECT_SPEC.md` and `configs/pilot.yaml` `guidelines_version` pointers corrected from
`0.5` to `0.6`.

---

## v0.5 — FROZEN — resolves OQ-006

**Change:** new §10.3 defines UPI_ID's pilot representation as an explicit
**BENCHMARK_SYNTHETIC** decision (frozen as decision 18 in §21) — one fixed grammar,
Grammar 3 of the three proposed in OQ-006:

```
<10-digit-synthetic-phone>@mail.test
e.g. 9876543210@mail.test
```

- Local part: 10 digits, first digit 6–9 (same convention as PHONE), shaped like a
  synthetic Indian phone number — a common real-world UPI VPA pattern — but never a
  real phone number.
- Domain: fixed `mail.test`, the same RFC 2606 reserved TLD (`.test`) EMAIL already
  uses. No real PSP handle or domain is used or resembled.
- Deliberately dotted (unlike a real, always-undotted PSP suffix) so the value creates
  controlled surface-form collision with EMAIL — the property PROJECT_SPEC.md §7
  explicitly designs UPI_ID to have, so that contextual typing (§10.1) is measurable.
- Not a claim about universal official UPI formatting. No checksum or
  payment-validation logic.

**Why:** resolves OQ-006 (`annotation/open_questions.md`). Of three candidate grammars
proposed (no-dot/fictional-PSP; dotted/reserved-TLD; phone-shaped-local +
dotted/reserved-TLD), Grammar 3 was chosen by explicit user decision — it is the only
one combining realistic local-part shape with the EMAIL-collision property the
benchmark's own design requires.

**Records affected:** none. No records or base instances exist yet (T04 has not run).

**Also updated:** `generators/pii/upi_id.py` (new) implements the fixed grammar — no
other UPI_ID local-part or domain variant exists. `tests/test_generator_upi_id.py` (new)
covers the fixed shape, domain, absence of any real PSP handle, EMAIL-shape collision,
and determinism. `generate_upi_id` added to the shared parametrized checks in
`tests/test_generators_common.py`. `annotation/open_questions.md` OQ-006 marked
RESOLVED. **T03 is now complete: all 8 generators implemented.**

`PROJECT_SPEC.md` and `configs/pilot.yaml` `guidelines_version` pointers corrected from
`0.3` to `0.5` (narrow version-reference fix, explicitly authorized this round).

---

## v0.4 — FROZEN — resolves OQ-004, OQ-005

**Change:** new §11.4 defines AADHAAR and BANK_ACCOUNT pilot representations as explicit
**BENCHMARK_SYNTHETIC** decisions (frozen as decision 17 in §21):

- `AADHAAR`: exactly 12 decimal digits, uniform random across all 12 positions (no
  leading-digit exclusion). No UIDAI checksum (Verhoeff) or issuance-range validation is
  applied or claimed.
- `BANK_ACCOUNT`: exactly 12 decimal digits, uniform random. Explicitly **not** claimed
  to be the universal length or format of Indian bank accounts, which vary by bank in
  reality (roughly 9–18 digits).

**Why:** resolves OQ-004 and OQ-005 (`annotation/open_questions.md`). Neither type had
any real-world format established anywhere in either governing document — §4.3's table
says only "Digits" for both, and every worked example uses a placeholder value, never a
concrete one. This is an explicit user data-model decision, not an implementation
inference: both representations are documented as benchmark-only constructs for
recognizing identifier-shaped PII in context, not as claims about official or universal
real-world identifier formats. No government checksum or issuance-range validation is
required or implied for either type.

**Records affected:** none. No records or base instances exist yet (T04 has not run).

**Also updated:** `generators/pii/aadhaar.py` and `generators/pii/bank_account.py` (new)
implement the two representations. `tests/test_generator_aadhaar.py` and
`tests/test_generator_bank_account.py` (new) cover format, type tag, schema conformance,
and determinism; `tests/test_generators_common.py` extended to include both in the
shared parametrized checks (base_kind/base_id independence, determinism, return shape).
`annotation/open_questions.md` OQ-004 and OQ-005 marked RESOLVED.

**Not touched this round (out of explicit scope):** `PROJECT_SPEC.md` and
`configs/pilot.yaml` still point to `guidelines_version: 0.3` — this update was scoped
to guidelines/open_questions/changelog only, so those two pointers are now stale again.
Flagged in the T03-follow-up report rather than fixed silently.

OQ-006 (UPI_ID) remains **unresolved** — candidate synthetic grammars were proposed for
approval but no representation was chosen or implemented this round.

---

## v0.3 — FROZEN — resolves OQ-003

**Change:** every base instance now declares `base_kind`, exactly one of `POSITIVE` |
`HARD_NEGATIVE` (new §13.4; frozen as decision 16 in §21). Invariant:

- `base_kind == POSITIVE` ⟹ `pii` contains at least one entry.
- `base_kind == HARD_NEGATIVE` ⟹ `pii` is `[]`.
- Distractor information for a hard-negative case belongs to the **derived record**
  (`distractors[]`, §13.3), never to the base instance.
- `base_id` naming conventions (e.g. a `NEG_` prefix) must **never** be used to infer
  `base_kind` — the field is the sole, explicit discriminator.

`base_kind` enum membership is structural (schema-enforced). The pii-cardinality
invariant is cross-field and is enforced by `validators/base_kind.py`, not by
`schemas/base_instance.schema.json`, consistent with the T02 structure-only scope rule.

**Why:** resolves OQ-003 (`annotation/open_questions.md`). Neither governing document
previously defined any base-level discriminator between positive and hard-negative
bases — confirmed by an explicit grep of both documents finding no `base_kind` /
`base_type` / `is_hard_negative` field anywhere. This is an explicit user data-model
decision, not an implementation inference, and it explicitly rejects inferring the
distinction from `base_id` naming or from `pii` emptiness alone.

**Six validation layers are unchanged** (still the v0.2 set: `structural`, `span`,
`semantic`, `language`, `duplicate`, `human`). **`distractors` was deliberately NOT
added** to `base_instance.schema.json` — it stays derived-record-only.

**Records affected:** none. No records or base instances exist yet (T04 has not run).

**Also updated:** `schemas/base_instance.schema.json` gained `base_kind` as a required
enum property (`$defs.base_kind`), `$comment` updated. `validators/base_kind.py` (new)
implements the cross-field invariant. `tests/test_base_kind_invariant.py` (new) covers
all 5 required cases. `tests/fixtures/base_instance.valid.json` gained
`"base_kind": "POSITIVE"`. `tests/fixtures/base_instance.hard_negative.valid.json` (new)
is a valid `HARD_NEGATIVE` example. `annotation/open_questions.md` OQ-003 marked
RESOLVED; OQ-002 marked RESOLVED (its proposed direction — hard negatives are
`base_instance` objects with `pii: []` — is now implemented via `base_kind`).

---

## v0.2 — FROZEN — resolves OQ-001

**Change:** `validation{}` (§17 worked example, and every derived record) now carries
**six** per-layer status keys instead of five: `structural`, `span`, `semantic`,
`language`, `duplicate`, `human`. Each uses the existing status enum
`PASS | FAIL | UNCERTAIN | NOT_APPLICABLE | PENDING`. `validation_status` remains the
single overall record status and is unaffected.

**Why:** PROJECT_SPEC.md §15 has always defined six validation layers, including
"5 Duplicate." The v0.1 worked example in §17 only showed five keys and omitted
`duplicate` — a discrepancy between the two governing documents, logged as
`annotation/open_questions.md` OQ-001 and resolved by explicit user decision rather than
picked silently. See OQ-001 for the exact source-text evidence from both documents.

**Six-layer definition itself is unchanged** — PROJECT_SPEC.md §15 was already correct
and required no edit.

**Records affected:** none. No records exist yet under v0.1 (pilot generation has not
started — T02 was schemas only), so no re-validation pass is required per §20 step 4.

**Also updated for consistency:** §21 gained decision 15 (the six-key rule, frozen);
`schemas/example.schema.json`'s `validation` object gained the `duplicate` property
(required); `tests/fixtures/example.valid.json` gained `"duplicate": "PENDING"`.

---

## v0.1 — FROZEN

`annotation/guidelines.md` v0.1 frozen as the ground-truth contract for the Indian PII
Robustness Benchmark, Pilot v0.1 and all downstream versions. Highest authority on
labels, spans, script policy, and ambiguity handling (PROJECT_SPEC.md §0).
