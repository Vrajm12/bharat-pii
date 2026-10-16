# Open Questions

> Log of cases where `guidelines.md` or `PROJECT_SPEC.md` was ambiguous, underspecified,
> or internally inconsistent, encountered during implementation. Per `CLAUDE.md` §3: do
> not silently resolve these by picking the sensible option. Record the case, the rule
> that failed, and candidate resolutions, then continue only where the governing
> documents already define a resolution procedure (e.g. PROJECT_SPEC.md §0's
> "guidelines.md wins, logged here" rule); otherwise stop and wait.

---

## OQ-001 — `validation{}` object: 5 keys or 6? — **RESOLVED (v0.2)**

**Encountered:** T02, building `schemas/example.schema.json` from guidelines.md §17.

**Record:** `annotation/guidelines.md` §17's worked example schema.

**Rule that failed:** PROJECT_SPEC.md §15 ("Validation layers") lists **six** layers —
Structural, Span, Semantic, Language/script, Duplicate, Human — each meant to carry a
status. But guidelines.md §17's worked-example `validation{}` object has only **five**
keys: `structural`, `span`, `semantic`, `language`, `human`. There is no `duplicate` key
anywhere in the example, and no `script` key separate from `language`.

**Resolution applied for T02 (not silent — logged here per PROJECT_SPEC.md §0):**
`schemas/example.schema.json` follows guidelines.md's worked example exactly (5 keys:
`structural`, `span`, `semantic`, `language`, `human`), because PROJECT_SPEC.md §0 itself
states the conflict-resolution procedure for this exact document pair: *"Where this
document and guidelines.md appear to conflict, guidelines.md wins and the conflict is
logged in annotation/open_questions.md."* This is that log entry.

**Candidate resolutions for guidelines.md v0.2:**
1. Add a `duplicate` key to the `validation{}` object (6 keys total), matching
   PROJECT_SPEC.md §15's table exactly.
2. Keep 5 keys and treat duplicate detection as a pre-acceptance gate that never reaches
   a per-record status field (e.g. duplicates are filtered before a record is assigned a
   `variant_id` at all, so there is nothing to store a status against).
3. Fold `duplicate` status into `validation_status` directly (e.g.
   `validation_status: REJECTED` with a `DUPLICATE` rejection reason) rather than giving
   it a slot in the per-layer `validation{}` object.

**Status:** RESOLVED, 2026-08-23, by explicit user decision. Resolution 1 chosen: the
`validation{}` object now carries **six** keys — `structural`, `span`, `semantic`,
`language`, `duplicate`, `human` — matching PROJECT_SPEC.md §15 exactly. The six-layer
definition in PROJECT_SPEC.md §15 was correct and unchanged; guidelines.md was the
document with the gap.

**Implemented:**
- `annotation/guidelines.md` → v0.2 (supersedes v0.1). §17 example gained `"duplicate":
  "PENDING"`; §21 gained decision 15 (six-key rule, frozen); §22 version block updated.
  See `annotation/CHANGELOG.md` v0.2 entry for the full diff and rationale.
- `schemas/example.schema.json` → `validation.duplicate` added as a required property,
  `$ref`ing the existing `validation_layer_status` enum (no new enum values needed).
- `tests/fixtures/example.valid.json` → gained `"duplicate": "PENDING"`; both schema
  tests re-run and pass.

**Not touched (out of this task's explicit scope — guideline/schema/open-question only):**
`PROJECT_SPEC.md`'s header (line 7, "Companion contract: annotation/guidelines.md v0.1")
and its status board (§34, "Annotation guidelines | v0.1 — FROZEN") now point to a
superseded version number. `configs/pilot.yaml`'s `guidelines_version: "0.1"` is likewise
now stale. Flagged to the user in the T02-follow-up report rather than edited silently.

---

## OQ-002 — Do hard-negative bases use `base_instance.schema.json`? — **RESOLVED (v0.3)**

**Encountered:** T02, deciding `pii[]` minItems on `schemas/base_instance.schema.json`.

**Record:** PROJECT_SPEC.md §12.2 (20 hard-negative bases, "not part of the 100") and
guidelines.md §13.3 (hard-negative example, `base_id: "NEG_007"`).

**Rule that failed:** PROJECT_SPEC.md §12.1 defines a base instance as "the synthetic
PII, its declared type and role, the person/scenario context, and one canonical English
sentence" — implying `pii[]` is non-empty and `person_context` / `scenario` /
`canonical_text` are populated. But guidelines.md §13.3's `NEG_007` example is shaped
like a **record** (`text`, `entities: []`, `distractors[]`, `synthetic`), not like a base
instance — it has no `pii[]`, `person_context`, `scenario`, or `canonical_text` at all.

It is unclear whether:
- a hard-negative "base" is a `base_instance` object with `pii: []` (and some other field
  carrying the decoy content that would normally live in `canonical_text`), or
- hard-negative bases skip `base_instance.schema.json` entirely and are authored directly
  as records via a distinct (not-yet-specified) schema.

**Resolution applied for T02:** `pii[]` is left permissive (`minItems: 0`) so the schema
does not reject either interpretation. This is a structural accommodation, not a
decision — `validators/` cannot yet enforce "a positive base must have pii.length >= 1"
because it isn't known whether that rule should apply to hard-negative bases at all.

**Candidate resolutions:**
1. Hard-negative bases are `base_instance` objects with `pii: []`, `person_context`
   possibly null, and `canonical_text` holding the decoy-containing sentence directly.
2. Hard-negative bases get their own minimal schema (e.g.
   `schemas/hard_negative_base.schema.json`) since they don't carry PII, person context,
   or a semantic role in the same sense.
3. `NEG_007` in guidelines.md §13.3 is illustrative shorthand for the **record**, not
   proof that hard negatives skip the base-instance stage — the actual base instance
   backing it was simply omitted from that example for brevity.

**Status:** RESOLVED, 2026-08-23. Candidate resolution 1 confirmed and implemented via
OQ-003: hard-negative bases are `base_instance` objects with `pii: []` and
`base_kind: HARD_NEGATIVE`. The `NEG_007` example in guidelines.md §13.3 is a **derived
record**, not itself a base instance (candidate 3 above was the correct reading of that
example — no base_instance content was omitted from it for brevity; it simply is not one).
See guidelines.md §13.4 and OQ-003 for the full discriminator rule.

---

## OQ-003 — Is an explicit `base_kind` field needed to distinguish POSITIVE from HARD_NEGATIVE bases? — **RESOLVED (v0.3)**

**Encountered:** T02 follow-up, while investigating whether OQ-002's proposed resolution
(hard-negative bases carry `pii: []` on the base) can be implemented without inventing new
structure.

**Question:** Once a hard-negative base is allowed to have `pii: []`, how does anything —
a human, a generator, a validator — tell it apart from a genuine error (a positive base
that was supposed to declare PII but doesn't)? A discriminator field, conventionally named
something like `base_kind` (`POSITIVE` | `HARD_NEGATIVE`), would let a validator assert
`base_kind == POSITIVE ⟹ len(pii) >= 1` and `base_kind == HARD_NEGATIVE ⟹ len(pii) == 0`
as a structural-adjacent check.

**Search performed:** grepped the full repository (`PROJECT_SPEC.md`, `annotation/guidelines.md`,
and everything committed so far) for `base_kind`, `base_type`, `record_type`,
`is_hard_negative`, `HARD_NEGATIVE` (as a field/enum value), and `record_kind`.
**No matches anywhere.** Neither governing document defines any such field.

Both documents refer to "hard-negative bases" only descriptively / quantitatively:

> PROJECT_SPEC.md §12.2: "**20 hard-negative bases** (not part of the 100)"
> PROJECT_SPEC.md §12.2 table: "Hard-negative variants | ~60"
> PROJECT_SPEC.md §31 (T11): "20 hard negatives with distractors (all 6 decoy classes)"
> guidelines.md §21 decision 11: "**Hard negatives carry `distractors` with `decoy_class`.**"

That last line is the closest thing to a discriminator either document defines — and it
describes a signal on the **derived record** (non-empty `distractors` + empty `entities`),
not a field on the **base instance**. The only other implicit signal in either document is
the `base_id` naming convention itself — positive bases use a type prefix (`PAN_001`,
`PERSON_001`, ...) and the one hard-negative example uses `NEG_007` — but this is never
stated as a rule anywhere; it is an inference from two examples, and `base_id`'s format is
a `pattern` in the schema, not an `enum` a validator could branch on cleanly.

**Conclusion: `base_kind` is not defined anywhere in the governing documents. Adding it
would be a new design decision, not a documented requirement.** Per the user's explicit
instruction, this is being reported as OQ-003 rather than added to the schema
automatically.

**Candidate resolutions:**
1. Add `base_kind: POSITIVE | HARD_NEGATIVE` as a new required field on
   `base_instance.schema.json`, and encode `base_kind == POSITIVE ⟹ pii.length >= 1` /
   `base_kind == HARD_NEGATIVE ⟹ pii.length == 0` as a validator rule (not schema-enforced,
   per the structure-only scope rule from T02).
2. No new field — rely on `pii.length == 0` itself as the discriminator (a base *is*
   hard-negative iff its `pii` array is empty), with no separate label. Simpler, but means
   "hard negative" is inferred rather than declared, and a genuine data bug (positive base
   that failed to populate `pii`) would be silently indistinguishable from an intentional
   hard negative.
3. No new field — rely on the `base_id` prefix convention (`NEG_*` vs. category prefixes)
   as the discriminator, formalized as an explicit rule in guidelines.md if adopted. Fragile
   if base-ID conventions ever change, and ties a structural distinction to a string
   pattern rather than a typed field.

**Status:** RESOLVED, 2026-08-23, by explicit user decision. Candidate resolution 1
chosen: `base_kind: POSITIVE | HARD_NEGATIVE` added as a required field on
`base_instance.schema.json`. The invariant is enforced by `validators/base_kind.py`
(cross-field, not schema-enforced, per the T02 scope rule), never by `base_id` naming.

**Implemented:**
- `annotation/guidelines.md` → v0.3 (supersedes v0.2). New §13.4 defines `base_kind` and
  the invariant; §21 gained decision 16; §22 version block updated. See
  `annotation/CHANGELOG.md` v0.3 entry.
- `schemas/base_instance.schema.json` → `base_kind` added as a required enum property
  (`$defs.base_kind`); `$comment` updated with the cross-field invariant note and OQ-002
  resolution. `distractors` was deliberately **not** added, per instruction.
- `validators/base_kind.py` (new) → `check_base_kind_pii_invariant()` implements the
  cross-field check.
- `tests/test_base_kind_invariant.py` (new) → covers all 5 required cases.
- `tests/fixtures/base_instance.valid.json` gained `"base_kind": "POSITIVE"`.
  `tests/fixtures/base_instance.hard_negative.valid.json` (new) — a valid
  `HARD_NEGATIVE` example (`pii: []`, `person_context: null`).

**Not touched (out of scope per instruction):** `PROJECT_SPEC.md` and `configs/pilot.yaml`
were updated only where required to keep the `guidelines_version` pointer consistent —
see the T02-follow-up report for exactly what changed there, if anything.

---

## OQ-004 — AADHAAR: no digit count or format is specified anywhere — **RESOLVED (v0.4)**

**Encountered:** T03, implementing `generators/pii/aadhaar.py`.

**Record:** Every mention of AADHAAR in both governing documents.

**Rule that failed:** neither document ever gives AADHAAR a concrete shape. The only
constraint stated anywhere is guidelines.md §4.3's table: `AADHAAR | Digits; stays ASCII
in all conditions`. Every worked example uses a placeholder, never a value:

> guidelines.md §11.1: `Input: My Aadhaar number is <AADHAAR_VALUE>. AADHAAR:
> <AADHAAR_VALUE>`
> PROJECT_SPEC.md §12.1: `{ "type": "PAN", "base_pii_value": "<SYNTHETIC>", ... }` (the
> one worked base-instance example is PAN, not AADHAAR, and even PAN's own field there is
> a placeholder, not "ABCDE1234F")

This is qualitatively different from PAN, where guidelines.md commits to a concrete
10-character worked value ("ABCDE1234F") and reuses it dozens of times — that repetition
*is* a specification by demonstration. AADHAAR gets no equivalent. Real Aadhaar numbers
are 12 digits and (per UIDAI's public documentation) never start with 0 or 1, but this
generator does not treat outside knowledge as authoritative when the governing documents
themselves never commit to it, per CLAUDE.md's prime directive.

**Candidate resolutions:**
1. 12 digits, first digit 2-9 (matches the real-world UIDAI convention, and is the
   "format-conforming so detection difficulty is realistic" reading of PROJECT_SPEC.md
   §11.1) — no checksum (Verhoeff) enforcement, since neither document mentions one.
2. 12 digits, uniform random 0-9 including the leading digit (simpler; less
   realistic — a leading 0/1 Aadhaar-shaped number never occurs in reality, so this
   would understate realistic detection difficulty).
3. Something else entirely — the "Digits" constraint in guidelines.md §4.3 is the only
   hard requirement; a different length could be chosen if a reason exists to prefer one.

**Status:** RESOLVED, 2026-08-23, by explicit user decision — a fourth option not among
the three candidates above: 12 decimal digits, uniform random **including** the leading
digit (closer to candidate 2 than candidate 1), explicitly framed as a
**BENCHMARK_SYNTHETIC** representation rather than an attempt to match real UIDAI
issuance rules. No checksum or issuance-range validation. See guidelines.md §11.4 and
`annotation/CHANGELOG.md` v0.4 for the frozen rule.

**Implemented:** `generators/pii/aadhaar.py` (new); `tests/test_generator_aadhaar.py`
(new, 5 tests including one confirming leading 0/1 is a reachable output, per the
"BENCHMARK_SYNTHETIC, not real-format" framing); `generate_aadhaar` added to the shared
parametrized checks in `tests/test_generators_common.py`.

---

## OQ-005 — BANK_ACCOUNT: no digit count or format is specified anywhere — **RESOLVED (v0.4)**

**Encountered:** T03, implementing `generators/pii/bank_account.py`.

**Record:** Every mention of BANK_ACCOUNT in both governing documents.

**Rule that failed:** same pattern as OQ-004 — guidelines.md §4.3's table says only
`BANK_ACCOUNT | Digits; stays ASCII in all conditions`, and every worked example is a
placeholder:

> guidelines.md §11.1: `Input: My bank account number is <ACCOUNT_VALUE>. BANK_ACCOUNT:
> <ACCOUNT_VALUE>`

The one *concrete* 12-digit number appearing anywhere near this type — `123456789012` in
guidelines.md §11.2 — is explicitly the opposite of a BANK_ACCOUNT worked example: it is
an order-reference **hard negative** ("`Result: NOT_TARGET_PII — logged as a distractor
with surface_type BANK_ACCOUNT`"), used specifically to illustrate that numeric shape
alone must never assign a type. Treating its length as "the" BANK_ACCOUNT format would
misread the document's own point.

Unlike AADHAAR, real Indian bank account numbers have **no single standard length** at
all — they vary by bank, typically 9 to 18 digits — so there is no real-world convention
to fall back on either. This is not resolvable without a decision.

**Candidate resolutions:**
1. Pick one fixed length for the pilot (e.g. 11 or 12 digits) for consistency across all
   13 BANK_ACCOUNT bases, documented as an arbitrary-but-fixed choice.
2. Vary the length per generated value within a documented range (e.g. 9-16 digits),
   more realistic to the real-world diversity but adds a length-sampling rule that
   doesn't currently exist anywhere.
3. Look to whichever length OQ-004 settles on for AADHAAR and deliberately choose a
   *different* one for BANK_ACCOUNT, so the two structured-numeric types remain visually
   distinguishable in generated text (relevant to distractor design later, T11).

**Status:** RESOLVED, 2026-08-23, by explicit user decision — candidate resolution 1
chosen (fixed 12-digit length), explicitly reframed as **BENCHMARK_SYNTHETIC**: the pilot
representation is a deliberate, documented benchmark construct — recognizing
account-number-like PII in context — not a claim about the universal length or format of
real Indian bank accounts (which have none). No checksum or issuance validation.
Candidate 3 (deliberately differ from AADHAAR's length) was **not** taken — both AADHAAR
and BANK_ACCOUNT are 12 digits; distinguishing them by shape alone was never the
benchmark's job (guidelines.md §11.2 / §10.1: type is decided by semantic context, never
string shape). See guidelines.md §11.4 and `annotation/CHANGELOG.md` v0.4.

**Implemented:** `generators/pii/bank_account.py` (new);
`tests/test_generator_bank_account.py` (new, 4 tests); `generate_bank_account` added to
the shared parametrized checks in `tests/test_generators_common.py`.

---

## OQ-006 — UPI_ID: no domain/provider-suffix safety rule is specified, unlike EMAIL — **RESOLVED (v0.5)**

**Encountered:** T03, implementing `generators/pii/upi_id.py`.

**Record:** guidelines.md §10 and §4.3; contrast with §9 (EMAIL).

**Rule that failed:** EMAIL gets an explicit, unambiguous, three-times-repeated domain
restriction — CLAUDE.md ("Email domains restricted to .test, .invalid, .example"),
guidelines.md §9 ("Benchmark domains are restricted to reserved TLDs: `.test` ·
`.invalid` · `.example`"), and PROJECT_SPEC.md §11.1 all state the same rule. UPI_ID gets
no equivalent anywhere, despite PROJECT_SPEC.md §7 explicitly flagging it as the one type
that **"Shape-collides with EMAIL"** and needs "context-dependent typing" — exactly the
kind of type where a domain-safety rule would matter most. guidelines.md §10's only
examples use a bare placeholder word, never a real or reserved-looking suffix:

> guidelines.md §10.1: `Input: My UPI ID is rahul123@provider. UPI_ID: rahul123@provider`

Real UPI IDs use actual, currently-active PSP handle suffixes (`@okaxis`, `@ybl`,
`@paytm`, `@oksbi`, and others) with no equivalent of email's RFC 2606 reserved TLDs —
there is no publicly documented "test" or "reserved" PSP suffix. A synthetic username
paired with a **real** PSP suffix carries a small but non-zero chance of resembling (in
shape, not in verified fact) an actually-registered handle, unlike EMAIL's `.test`
domains, which are guaranteed non-resolvable by IANA/RFC 2606 reservation.

**Candidate synthetic grammars proposed 2026-08-23** (superseding the three generic
resolutions above, per explicit user request to propose 2–3 concrete grammars before
implementing):

**Grammar 1 — no-dot, fictional PSP token (real-syntax-faithful).**
`<local>@<fictional-psp-token>`, e.g. `rahul123@fakepay`. No dot in the suffix, matching
how real UPI PSP handles actually look (`@paytm`, `@ybl`, `@oksbi` — single token, never
dotted). `fictional-psp-token` drawn from a pool deliberately avoiding every current
major Indian PSP handle.
- *Realism:* high — matches real UPI's actual dotless single-token suffix shape.
- *Safety:* high — a fictional token cannot match any live NPCI-registered PSP handle,
  so it cannot route a real payment regardless of the local part.
- *Collision with EMAIL:* low — the absence of a dot makes it trivially
  shape-distinguishable from an email address by a naive format check, which cuts
  against PROJECT_SPEC.md §7's explicit design goal for this type: **"Shape-collides
  with EMAIL — context-dependent typing."** This grammar under-serves the specific
  research variable (RQ3, UPI-vs-EMAIL confusion, motivated by *Unmasking*'s own finding)
  that UPI_ID exists in the taxonomy to test.
- *Reproducibility:* high — trivial rng-driven pool selection, same pattern as the other
  seven generators.

**Grammar 2 — dotted, reserved-TLD (EMAIL-shape-collision-faithful).**
`<local>@<label>.<reserved TLD>` — structurally identical to the EMAIL generator,
reusing the same three RFC 2606 TLDs (`.test`/`.invalid`/`.example`), with
UPI-flavored local-part vocabulary.
- *Realism:* medium — real UPI PSP suffixes are never dotted, so this deliberately
  diverges from real UPI syntax. The divergence is in direct service of the benchmark's
  own stated goal, not an accident.
- *Safety:* high — inherits EMAIL's exact RFC 2606 non-resolvability guarantee.
  Additionally, since real PSP tokens are never dotted, this string could never be
  mistaken for a live UPI handle even at the shape level, on top of the TLD reservation.
- *Collision with EMAIL:* high — by construction, this is the same grammar as EMAIL,
  which is exactly what makes UPI-vs-EMAIL confusion measurable at all.
- *Reproducibility:* high.

**Grammar 3 — phone-shaped local + reserved-TLD (hybrid).**
`<10-digit-phone-shaped-local>@<label>.<reserved TLD>` — combines a realistic local part
(a bare phone number as the VPA is one of the single most common real UPI ID patterns)
with Grammar 2's EMAIL-shape-colliding, RFC-2606-safe suffix.
- *Realism:* high for the local part (phone-as-VPA is extremely common in practice),
  medium for the suffix (same deliberate divergence as Grammar 2).
- *Safety:* high — same guarantee as Grammar 2.
- *Collision with EMAIL:* high — same as Grammar 2.
- *Reproducibility:* high.

None of the three ever draws from, or resembles, an actual current major Indian PSP
handle (`okaxis`, `ybl`, `paytm`, `oksbi`, `ibl`, `axl`, and similar are all avoided by
construction in every grammar). Grammars 2 and 3 are the only ones that serve
PROJECT_SPEC.md §7's explicit "shape-collides with EMAIL" design intent; Grammar 1 is the
most realistic to real-world UPI syntax but weakens that specific research variable.

**Status:** RESOLVED, 2026-08-23, by explicit user decision — **Grammar 3** chosen:
`<10-digit-synthetic-phone>@mail.test` (e.g. `9876543210@mail.test`), fixed, no
variants. This is the only grammar combining realistic local-part shape (phone-as-VPA)
with Grammar 2's EMAIL-collision property; Grammar 1 was not chosen because its lack of
a dot would have under-served PROJECT_SPEC.md §7's explicit "shape-collides with EMAIL"
design intent. See guidelines.md §10.3 and `annotation/CHANGELOG.md` v0.5.

**Implemented:** `generators/pii/upi_id.py` (new) — the one fixed grammar, no other
local-part/domain variant. `tests/test_generator_upi_id.py` (new, 7 tests) covers the
fixed shape/domain, absence of any real PSP handle, explicit EMAIL-shape collision, and
determinism. `generate_upi_id` added to the shared parametrized checks in
`tests/test_generators_common.py`.

**T03 is now complete: all 8 generators implemented** (PERSON, ADDRESS, PHONE, EMAIL,
PAN, AADHAAR, BANK_ACCOUNT, UPI_ID).

---

## OQ-007 — `semantic_role` is type-fixed, but some type/domain pairings read as weak — **RESOLVED (v0.6)**

**Encountered:** T04 data review (manual inspection of the 100 generated base
instances), 2026-08-23. Not caught by any mechanical assertion — all 100 records are
schema-valid and pass `check_base_kind_pii_invariant()`; this is a semantic-plausibility
issue, not a structural one.

**Record:** `PROJECT_SPEC.md` §12.1 (the base-instance definition and its one worked
example); `guidelines.md` — `semantic_role` is never mentioned there at all.

**The gap:** `semantic_role` appears in the governing documents in exactly one place —
PROJECT_SPEC.md §12.1's single worked example, `"semantic_role": "TAX_IDENTIFIER"` for a
PAN. Confirmed by grep: `guidelines.md` never uses the string `semantic_role`. Nothing in
either document states whether the field is:

(a) **type-intrinsic** — one fixed value per PII type, describing what *kind* of
    identifier/value this is, independent of scenario (the reading `generators/base_instances.py`
    implements, per your explicit T04 approval), or
(b) **domain-dependent** — varies with `scenario.domain` (e.g. a PERSON might be
    `ACCOUNT_HOLDER_NAME` in banking_payments but `PATIENT_NAME` in
    healthcare_administration), or
(c) **fully contextual** — assigned per base instance with no fixed vocabulary at all.

§12.1's prose is the only lean either way: *"the synthetic PII, its declared type and
role, the person/scenario context"* — role is listed alongside type, structurally
parallel to and separate from "person/scenario context." That reads as weak evidence for
(a), which is what was approved and implemented. Nothing in either document confirms or
rules out (b) or (c).

**What the data review actually found:** `ACCOUNT_HOLDER_NAME` — the frozen PERSON role —
is grepped in exactly two places in the whole repository: `generators/base_instances.py`
(where it's defined) and `data/raw/base_instances.jsonl` (its 12 uses). It does not
appear in `guidelines.md`, `PROJECT_SPEC.md`, or any schema. It was proposed by me in the
T04 design report and approved as part of the frozen semantic_role table — it did not
come from the governing documents, and no other document anywhere corroborates it as the
right label for PERSON.

The specific problem is narrower than "type-fixed roles are wrong": `ACCOUNT_HOLDER_NAME`
carries a banking/service-account connotation that fits some of PERSON's assigned domains
(`delivery_address`, arguably) but not others (`employment_hr`, `healthcare_administration`,
`general_conversation` — none of these involve "an account" at all; an employee isn't an
account holder, a patient isn't an account holder). This is a **label-choice** problem
within the type-fixed design, not necessarily evidence that the design itself (one role
per type, independent of domain) is wrong — a more domain-neutral label (e.g.
`PERSON_NAME`) might resolve it without changing reading (a) to (b) or (c) at all. But
it might also be a symptom of (b) being the intended design and (a) being an
oversimplification — the documents don't say which.

**Candidate resolutions:**
1. Keep semantic_role type-fixed (reading (a)), but replace `ACCOUNT_HOLDER_NAME` with a
   domain-neutral label such as `PERSON_NAME` that fits all four of PERSON's assigned
   domains without implying an account relationship. Smallest change; revises one
   frozen-decision string, not the underlying design.
2. Make semantic_role domain-dependent (reading (b)): PERSON would need up to 4 different
   role values (one per assigned domain) instead of 1. Larger change — every type whose
   domain spread includes a role-mismatched domain would need re-examination, not just
   PERSON.
3. Leave `ACCOUNT_HOLDER_NAME` as-is and accept it as a deliberately generic/umbrella
   label not meant to be read literally per-domain — i.e. treat "weak" as acceptable
   pilot-stage looseness rather than a defect. Cheapest, but leaves ground truth that a
   human reviewer already flagged as questionable baked into 12 permanent, never-reused
   base IDs.

**Status:** RESOLVED, 2026-08-23, by explicit user decision — candidate resolution 1
chosen. `semantic_role` stays type-fixed (design (a) from the analysis above is
confirmed as intended); PERSON's frozen value changes from `ACCOUNT_HOLDER_NAME` to
`PERSON_NAME`. Rationale (user's own wording): `semantic_role` represents the role/type
of the PII itself, while `scenario.domain`/`scenario.purpose` represent the contextual
use of that PII — `PERSON_NAME` is deliberately domain-neutral and is not a claim that
every PERSON is an account holder. See guidelines.md §13.5 and
`annotation/CHANGELOG.md` v0.6.

**Implemented:** `generators/base_instances.py`'s `SEMANTIC_ROLE["PERSON"]` changed to
`"PERSON_NAME"`. No schema change (`semantic_role` was never enum-constrained). No test
or fixture required a change (none hardcoded `ACCOUNT_HOLDER_NAME`; the mapping test
asserts against the constant itself).

**Not yet done, by explicit instruction:** `data/raw/base_instances.jsonl` still carries
`ACCOUNT_HOLDER_NAME` on all 12 PERSON records — the 100 base instances were not
regenerated as part of this resolution. Full 100-record semantic-plausibility audit that
surfaced this (70 GOOD / 18 PLAUSIBLE / 12 WEAK) was reported to the user alongside the
original entry, not reproduced here. Regeneration is a separate, later step.

---

## OQ-008 — PHONE: no base-representation rule was ever frozen in guidelines.md — **RESOLVED (v0.7)**

**Encountered:** T05 structural-validator design report, 2026-08-23. `generators/pii/phone.py`'s
`^[6789][0-9]{9}$` regex was a documented T03 implementation assumption, evidenced by
guidelines.md §8's repeated example values, but never itself elevated to a frozen
guidelines.md decision the way AADHAAR/BANK_ACCOUNT/UPI_ID were (§11.4/§10.3).
Implementing it as a hard T05 validation rule with no governing-document decision
backing it directly would have been exactly the kind of silent codification CLAUDE.md
§3 warns against.

**Status:** RESOLVED, 2026-08-23, by explicit user decision, proposed and resolved in
the same message. `^[6789][0-9]{9}$` frozen as PHONE's base representation
(`base_pii_value` — before any formatting/realization), documented in new guidelines.md
§8.1, explicitly distinguished from §8's pre-existing annotation rule for *realized*
PHONE spans (which still legitimately include `+91`, spaces, and hyphens — a
later/perturbation-layer concern, unaffected). Frozen as decision 20 in §21.

---

## OQ-009 — EMAIL: local-part format was completely unconstrained — **RESOLVED (v0.7)**

**Encountered:** T05 structural-validator design report, 2026-08-23. Guidelines.md §9
freezes EMAIL's TLD restriction explicitly but says nothing about local-part shape,
leaving T05 with no basis to decide how strict a local-part check should be.

**Status:** RESOLVED, 2026-08-23, by explicit user decision. T05 structural grammar
frozen as: exactly one `@`, non-empty local part, domain ending in an exact-lowercase
`.test`/`.invalid`/`.example`. Explicitly not full RFC 5321/5322 validation; no
additional local-part character restrictions invented beyond non-emptiness. Documented
in new guidelines.md §9.1. Frozen as decision 21 in §21.

---

## OQ-010 — PAN: casing was never explicitly specified as a rule — **RESOLVED (v0.7)**

**Encountered:** T05 structural-validator design report, 2026-08-23. Every PAN worked
example in guidelines.md is uppercase, but no document states uppercase is *required* —
leaving it ambiguous whether `abcde1234f` should structurally fail.

**Status:** RESOLVED, 2026-08-23, by explicit user decision. PAN's structural
representation frozen as uppercase-only, `^[A-Z]{5}[0-9]{4}[A-Z]$` — lowercase is
structurally invalid. No checksum, issuance, or category-code (4th-character semantics)
validation performed or implied. Documented in new guidelines.md §11.5. Frozen as
decision 22 in §21.

---

## OQ-011 — EMAIL/UPI_ID: domain case sensitivity, and UPI_ID's structural-failure reasoning — **RESOLVED (v0.7)**

**Encountered:** T05 structural-validator design report, 2026-08-23. Neither document
addresses whether reserved TLDs / the fixed `mail.test` domain should be matched
case-sensitively. Separately, the design report's own UPI_ID reasoning risked
conflating two different things: "fails the frozen grammar" (a structural fact) versus
"resembles a real PSP handle" (§10.3's design *rationale* for choosing that grammar,
not a validation criterion in itself).

**Status:** RESOLVED, 2026-08-23, by explicit user decision. EMAIL and UPI_ID reserved
domains matched as exact lowercase strings, never normalized (`@MAIL.TEST` fails).
For UPI_ID specifically: a value such as `9876543210@paytm` is structurally invalid
*because it does not match the frozen grammar* `<10-digit-phone>@mail.test` — the
validator must never describe real-PSP avoidance as the structural reason for failure.
Documented in guidelines.md §9.1 (EMAIL) and new §10.4 (UPI_ID). Frozen as decision 23
in §21.

---

## OQ-012 — No linguistic content definition for any of the seven realizations, only labels + a script table

**Encountered:** T08 design report ("T06" in the request; PROJECT_SPEC.md §31 assigns
T06 to canonical-English generation, already absorbed into T04 — the seven language
realizations are T08's subject matter), 2026-08-23.

**Record:** PROJECT_SPEC.md §8 / guidelines.md §4.2 — the only place all seven
realizations are defined.

**The gap:** both documents define each realization as a *label* plus a row in the
carrier-script/PII-script table (PROJECT_SPEC.md §8, guidelines.md §4.2). Neither
document ever states, in prose, what linguistic content generation actually means for
any of the seven — there is no rule distinguishing:

- `EN` from `IN_EN` ("Indian English" — what makes English text specifically *Indian*
  English, content-wise, beyond carrier script being identical to `EN`?)
- `ROM_HI` from `HINGLISH` (`ROM_HI` = "Romanized Hindi" implies a Hindi sentence
  transliterated to Latin script; `HINGLISH` = "Hindi–English code-mixed" implies an
  actual mix of both languages' words — but this is my inference from the labels, not a
  stated rule)
- `HINGLISH` from `INFORMAL_HINGLISH` ("WhatsApp-register" is a register/tone
  descriptor, not a content rule)

This is the central gap blocking T08 generation: whoever writes the carrier-text
generator for each condition needs an actual content rule, and none exists beyond the
name and the script table.

**Candidate resolutions:**
1. Add a worked example sentence per realization to guidelines.md (the way PAN's format
   is established by repeated examples) — one canonical `PAN_001`-style sentence shown
   in all seven realizations side by side, frozen as the reference.
2. Define each realization by a short prose rule (e.g. "IN_EN: standard English with
   Indian-English discourse markers/lexical items — 'kindly', 'do the needful' — but no
   Hindi vocabulary") and freeze that as a decision.
3. Defer to LLM-assisted paraphrasing per §14.2's "produce Hinglish register variation"
   grant, with only the *script/language label* as ground truth and no further
   deterministic content rule — accept that "what IN_EN sounds like" is inherently a
   fuzzy, human-reviewed judgment (§19's "Language correct? YES/NO"), not a rule T08 can
   encode.

**Status:** PROPOSAL DELIVERED, NOT YET APPROVED, 2026-08-23. A full rigorous
specification for all seven conditions across ten dimensions was produced (T08
language-realization design report) and reported to the user in full — not reproduced
here. Candidate resolution 2 was effectively adopted for the proposal's structure (prose
rules per condition). The three hardest sub-cases were broken out into their own,
narrower open questions rather than left folded into this one: **OQ-023** (EN vs
IN_EN), **OQ-024** (ROM_HI vs HINGLISH), **OQ-025** (HINGLISH vs INFORMAL_HINGLISH). A
fourth, architectural gap surfaced while designing carrier-text generation for the
Hindi-script conditions: **OQ-026** (T07's table is explicitly PII-vocabulary-only, but
generating HI_LATIN_PII/HI_DEVA_PII/ROM_HI carrier text requires transliterating or
generating far more than PII tokens — a mechanism T07 was deliberately scoped not to
provide). This entry stays UNRESOLVED as the parent gap until OQ-023–026 are each
decided. Still blocks T08 implementation and OQ-015.

---

## OQ-013 — `pii_script` enum offers `NUMERIC` but no rule says which types use it — **RESOLVED (v0.11)**

**Encountered:** T08 design report, 2026-08-23.

**Record:** `schemas/example.schema.json`'s `pii_script` enum (`LATIN`, `DEVANAGARI`,
`MIXED`, `NUMERIC` — locked in T02); guidelines.md §4.3's table, which describes PHONE,
EMAIL, PAN, AADHAAR, UPI_ID, and BANK_ACCOUNT as "stays Latin/ASCII in all conditions."

**The gap:** §4.3's own phrasing bundles "Latin" and "ASCII" together as one bucket for
all six non-transliterable types, but the schema's `pii_script` enum offers `NUMERIC` as
a value *distinct from* `LATIN`. Nothing states whether the four purely-numeric types
(PHONE, AADHAAR, BANK_ACCOUNT, and arguably the local-part-digits of UPI_ID) should be
tagged `NUMERIC` while the two alphanumeric types (PAN, EMAIL) get `LATIN`, or whether
`NUMERIC` is simply unused/reserved and everything non-transliterable gets `LATIN` per
§4.3's literal wording. A related, lower-stakes observation: `carrier_script`'s `MIXED`
enum value is also never assigned to any of the seven frozen realizations (all seven are
exactly `LATIN` or `DEVANAGARI`) — possibly reserved for a future condition, not
necessarily a defect, but worth noting alongside this entry.

**Candidate resolutions:**
1. `NUMERIC` for PHONE/AADHAAR/BANK_ACCOUNT (pure digit strings), `LATIN` for
   PAN/EMAIL/UPI_ID (contain letters).
2. `LATIN` for all six, treating `NUMERIC` as reserved/unused in the pilot — matches
   §4.3's literal "Latin/ASCII" bundling most directly.

**Status:** RESOLVED, 2026-08-23, by explicit user decision — candidate resolution 1
chosen, refined: `pii_script` reflects the realized span's actual script composition.
PHONE/AADHAAR/BANK_ACCOUNT → `NUMERIC`; PAN/EMAIL → `LATIN`; UPI_ID → `MIXED` (not
covered by either original candidate — its span mixes a numeric local part and a Latin
domain, `9876543210@mail.test`, so neither pure `NUMERIC` nor pure `LATIN` describes it
correctly). No new enum value. See guidelines.md §4.15, decision 36.

---

## OQ-014 — No worked `variant_id` example exists for a clean (non-perturbed) language realization — **RESOLVED (v0.11)**

**Encountered:** T08 design report, 2026-08-23.

**Record:** guidelines.md §17's one and only worked `variant_id` example:
`"PAN_001_HINGLISH_A1_01"`.

**The gap:** that example is a **perturbed** record (`perturbation.family: "A1"`) — every
segment of the ID after `base_id` is entangled with the perturbation. T08 produces
**624 clean, unperturbed** language-realization records before any perturbation exists
(T12 is later). Removing the `A1_01` segment by inference gives something like
`PAN_001_HINGLISH`, but this is a guess, not a demonstrated pattern — no document shows
a clean-variant ID, and it's unclear whether a trailing sequence number is still
expected (e.g. for the case where more than one clean variant could exist per
base×language, which doesn't currently happen, but the pattern doesn't rule it out).

**Candidate resolutions:**
1. `{base_id}_{language}` for clean variants (e.g. `PAN_001_HINGLISH`), reserving the
   trailing `_{family}_{seq}` suffix only for perturbed records.
2. `{base_id}_{language}_NONE_01` — always include the perturbation segment, using the
   already-frozen `NONE` enum value (`schemas/example.schema.json`'s
   `perturbation_family`/`perturbation_type`/`perturbation_target` all include `NONE`)
   for un-perturbed records, keeping one uniform ID shape across the whole record
   schema.

**Status:** RESOLVED, 2026-08-23, by explicit user decision — candidate resolution 1
chosen: `{base_id}_{language}`, no perturbation suffix. §17 gained a second worked
example (a clean `EN` record) confirming this, alongside the existing perturbed one,
which is now explicitly labeled as defining only the perturbed-record format. See
guidelines.md §4.16, decision 37.

---

## OQ-027 — `context` value for T08 clean records was never stated

**Encountered:** T08 governance-resolution report, 2026-08-23 (surfaced as an
unstated assumption in the immediately preceding T08 report, formalized here).

**Record:** `context` is a required field (`schemas/example.schema.json`) with enum
`EXPLICIT`/`SEMI_EXPLICIT`/`IMPLICIT`/`UNLABELLED`. PROJECT_SPEC.md §9.1 allocates C1–C4
across each PII category's bases, but nothing states what T08's 624 language-realization
records should carry for this field.

**Status:** RESOLVED, 2026-08-23, by explicit user decision. Every T08 clean record
carries `context: "EXPLICIT"`. Not a redesign of §9.1's C1–C4 allocation, which governs
a separate, later pipeline stage. Justified by T08's own locked arithmetic (624 = bases
× languages, which only holds if context is held constant per record) and by every T08
carrier template already being written in the explicit register. See guidelines.md
§4.17, decision 38.

---

## OQ-015 — No specified mechanism for detecting malformed/garbage code-mixed text or confirming genuine code-mixing

**Encountered:** T08 design report, 2026-08-23.

**Record:** PROJECT_SPEC.md §14.2's LLM boundary: *"May: generate and paraphrase natural
language; produce Hinglish register variation; **emit advisory PASS/FAIL/UNCERTAIN in
semantic validation**."* guidelines.md §19's human review sheet: `Language correct?
YES/NO`, `Natural? YES/NO`.

**The gap:** the LLM-advisory grant is textually scoped to **semantic** validation only
— it does not say an LLM may also emit advisory judgments for **language** validation
(PROJECT_SPEC.md §15 layer 4, "Realization matches its declared condition"), which is
the layer that would actually catch a `HINGLISH`-labeled record that came out as plain
English, or a garbled/artificial-sounding code-mixed sentence. Taken literally, the only
mechanism either document actually specifies for this is human review (§19's two
YES/NO questions) — there is no automated heuristic, code-mixing ratio, or language-ID
check specified anywhere for layer 4. This is compounded by OQ-012: without a content
rule for what *correct* HINGLISH looks like, there's no baseline to detect deviation
from.

**Candidate resolutions:**
1. Human review is the sole mechanism for this layer, as the literal text implies —
   T08/T10 do not attempt automated code-mixing detection at all; every HINGLISH/
   INFORMAL_HINGLISH record depends on §19's `Language correct?` question.
2. Extend the LLM-advisory grant explicitly to layer 4 as well (a guidelines.md version
   increment, since §14.2's boundary is a frozen rule), letting an LLM flag suspected
   `LANGUAGE_MISMATCH`/`NATURALNESS_FAILURE` candidates for human adjudication rather
   than requiring a human to review all 624 records with equal scrutiny.
3. Define a minimal deterministic heuristic (e.g. a Hindi-word-list ratio check) as a
   pre-filter, understanding it will be imprecise and is not a replacement for human
   review — closer to a triage signal than a validator.

**Status:** UNRESOLVED. Blocks T10 (language/script validator) more directly than T08
itself, but T08's generation design should account for which failure modes it needs to
anticipate before generation starts.

---

## OQ-016 — "Deterministic transliteration table" — structure is never specified — **RESOLVED (v0.8)**

**Encountered:** T07 design report, 2026-08-23.

**Record:** the entire evidentiary basis for T07 in both governing documents:

> PROJECT_SPEC.md §8.3: *"Devanagari forms come from a **deterministic transliteration
> table**, never an LLM, and are fixed at base-instance creation. The same name must
> transliterate identically everywhere. Table version recorded in `generator_version`."*
>
> guidelines.md §4.5 (near-identical): *"Devanagari forms are produced by a
> **deterministic transliteration table**, not by an LLM, and are recorded in the base
> instance at creation time. The same name must transliterate identically in every
> record. Store the table version in `generator_version`."*

That is the complete specification — two short, near-identical paragraphs, repeated
rather than elaborated. Neither document ever states what structure "table" refers to:
a whole-token lookup (name/component → Devanagari string), a character/syllable mapping
applied algorithmically, or something else. No transliteration scheme (ISO 15919,
ITRANS, IAST) or library is named anywhere in either document — confirmed by a
repository-wide grep.

**Supporting evidence for one reading over the others:** `generators/pii/person.py` and
`generators/pii/address.py` (frozen, T03) draw from small, closed vocabularies — 20
given names + 20 family names for PERSON (40 tokens total), 8 building names + 8 road
names + 8 cities for ADDRESS, plus numeric/literal components ("Flat", house numbers,
PIN digits). A closed vocabulary this size is well within reach of a hand-curated,
whole-token lookup table — and the one concrete requirement either document states,
`len("राहुल") == 5`, requires a *linguistically correct* Devanagari rendering (the real
Hindi spelling of "Rahul": र-ा-ह-ु-ल, 5 code points — not an arbitrary 1:1 character
substitution, which could easily produce a different code-point count via
mishandled matras/conjuncts). Real Indian city names (Pune → पुणे, etc.) also have
conventional Devanagari spellings that aren't reliably derivable by naive phonetic rule
— another point in favor of a curated table over an algorithm.

None of this is stated as a rule, though — it is inference from the frozen generators'
vocabulary size, not a governing-document decision.

**Candidate resolutions:**
1. **Whole-token lookup table**: one entry per Latin token in T03's closed vocabularies
   (person given/family names, address building/road/city names, plus literal words
   like "Flat"), each mapped to a single, curated, correct Devanagari string. Multi-token
   values (e.g. "Rahul Sharma") are transliterated by looking up and joining each token.
   Matches "table" most literally; tightly scoped to what the frozen generators can
   actually produce.
2. **Character/syllable mapping algorithm**: a rule-based function (e.g. modeling
   Devanagari's akshara/conjunct structure) that can transliterate *any* Latin string,
   not just a known vocabulary. More general, but far more implementation risk (getting
   Devanagari conjuncts/matras linguistically right from scratch is nontrivial), and
   less literally supported by "table" as the chosen word.
3. A hybrid: an algorithmic scheme used as a *build-time generation aid* to populate a
   static lookup table (which is then what's actually shipped/versioned/tested) — the
   runtime artifact is still a table either way.

**Status:** RESOLVED, 2026-08-23, by explicit user decision — candidate resolution 1
chosen: token-level lookup table, exactly covering the frozen T03 PERSON/ADDRESS
vocabularies. Character-level substitution, LLM transliteration, probabilistic
transliteration, and external general-purpose transliteration algorithms are all
explicitly excluded. Documented, verbatim as instructed: *"This is a benchmark-specific
deterministic transliteration table, not a general-purpose Hindi transliteration
system."* See guidelines.md §4.7 and `annotation/CHANGELOG.md` v0.8.

---

## OQ-017 — ADDRESS transliteration: abbreviations, numerals, and English loanwords are unaddressed — **RESOLVED (v0.8)**

**Encountered:** T07 design report, 2026-08-23, while inspecting `generators/pii/address.py`'s
actual output vocabulary against guidelines.md §4/§7's transliteration and span rules.

**Record:** guidelines.md §4.3 marks ADDRESS wholesale as "Transliterable," with no
finer-grained rule. `generators/pii/address.py`'s frozen vocabulary includes:

- an abbreviation/initialism as a literal component: `"ABC Apartments"` (`"ABC"` is not
  a pronounceable Hindi word — is it phonetically spelled out letter-by-letter in
  Devanagari, e.g. "ए बी सी", or left in Latin script inside an otherwise-Devanagari
  address?)
- another initialism: `"MG Road"` (`"MG"` = Mahatma Gandhi, conventionally)
- numerals mixed with words: `"Flat {house_no}"` (1–499) and a 6-digit PIN code — real
  Hindi text commonly keeps Arabic numerals (0–9) even in Devanagari script, but neither
  document states whether T07 should convert digits to Devanagari numerals (०–९) or
  leave them as-is
- English loanwords used as literal components: `"Flat"`, `"Apartments"`,
  `"Residency"`, `"Towers"`, `"Enclave"`, `"Society"`, `"Homes"`, `"Heights"`, `"Grove"`,
  `"Valley"`, `"Road"`, `"Street"` — "transliteration" (script change, same word) versus
  "translation" (different Hindi vocabulary, same meaning) is never distinguished for
  these; the document's own terminology ("transliteration," never "translation")
  suggests phonetic script conversion of the same English words is intended, but this is
  inference, not a stated rule.

**Candidate resolutions:**
1. Phonetically transliterate every component, including loanwords and spelled-out
   initialisms, with no special-casing — one uniform rule, simplest to implement and
   test, but may read as unnatural (e.g. spelling out "ए बी सी" for a building name).
2. Leave numerals as Arabic numerals unconditionally (matches real Hindi typographic
   convention); phonetically transliterate everything else including loanwords and
   initialisms.
3. Treat common English loanwords and initialisms as a small carve-out that stays in
   Latin script even within an otherwise-Devanagari address (closer to real informal
   Hindi-English address-writing conventions, but adds a second rule class beyond "pure
   transliteration").

**Status:** RESOLVED, 2026-08-23, by explicit user decision — resolved at the *policy*
level: every reachable lexical component needs an explicit table entry; numeric
components stay unconverted ASCII digits; no rule is invented for unreachable ADDRESS
forms. See guidelines.md §4.8.

**Not fully resolved by this decision:** the policy says *that* every reachable lexical
token needs an entry, not *how* to derive the entry for the two tokens that aren't
ordinary words — `"ABC"` (an abbreviation, `"ABC Apartments"`) and `"MG"` (an
initialism, `"MG Road"`). Spelling out letters phonetically, transliterating as if the
abbreviation were a pronounceable word, and leaving it in Latin script are all different
choices with different table entries, and none was specified. Logged separately as
**OQ-022** rather than left implicit inside this now-resolved entry.

---

## OQ-018 — No fallback is specified for a name/component not present in the table — **RESOLVED (v0.8)**

**Encountered:** T07 design report, 2026-08-23.

**Record:** neither document addresses what happens when a transliteration table (under
reading 1 of OQ-016) is asked to transliterate a token it has no entry for — e.g. if
`generators/pii/person.py`'s or `address.py`'s vocabulary is extended in a future task
without a corresponding table update.

For the *current* frozen T03 generators, this case may never actually arise in practice
if the table is built to exhaustively cover their existing closed vocabularies — but the
document gives no guidance on whether an out-of-table lookup should hard-fail, or
whether some deterministic approximation (e.g. a generic phonetic fallback) is
permitted. The request explicitly asks "what deterministic fallback is allowed, if
any" — the honest answer is that no fallback is specified or authorized anywhere.

**Candidate resolutions:**
1. Hard-fail (raise) on any out-of-table token — no invented fallback, no naive
   approximation. Forces the table to be updated deliberately whenever generator
   vocabulary changes, consistent with CLAUDE.md's "do not invent a rule" default.
2. Permit a documented, explicitly-flagged deterministic fallback (e.g. a generic
   phonetic character-mapping used *only* for unknown tokens, with the record it
   produced logged/flagged for human review) — more resilient to future vocabulary
   growth, but introduces exactly the kind of algorithmic component OQ-016 is still
   deciding whether to allow at all.

**Status:** RESOLVED, 2026-08-23, by explicit user decision — candidate resolution 1
chosen: fail closed. A lookup miss raises a deterministic error; the candidate is
rejected/logged, never silently accepted, guessed, or routed through an LLM/external
service. See guidelines.md §4.9.

---

## OQ-019 — No transliteration library is named, authorized, or prohibited — **RESOLVED (v0.8)**

**Encountered:** T07 design report, 2026-08-23.

**Record:** repository-wide grep for named transliteration schemes/libraries (ISO
15919, ITRANS, IAST, `indic_transliteration`, `aksharamukha`, `unidecode`, etc.) across
both governing documents: no matches. Both documents say only "table," "never an LLM" —
silent on tooling.

**Candidate resolutions:**
1. Hand-author the table entries directly (no external library at all, at build time or
   runtime) — maximizes auditability, zero third-party dependency risk, but requires
   someone to manually verify every Devanagari spelling is linguistically correct for
   ~40+ PERSON tokens and the full ADDRESS component vocabulary (compounded by OQ-017).
2. Use an established transliteration library as a **build-time aid only** (to generate
   candidate table entries for a human to review and freeze), with the shipped/tested
   runtime artifact remaining a static table with no library dependency. Requires naming
   a specific library and getting it approved — this instruction explicitly says not to
   choose one silently.
3. Use a transliteration library as a **runtime dependency**, called deterministically
   (not an LLM) each time a lookup is needed rather than pre-computing a static table.
   Weakest fit to "table" as the literal chosen word in both documents.

**Status:** RESOLVED, 2026-08-23, by explicit user decision — no external transliteration
library, at build time or runtime (rules out candidate resolutions 2 and 3). The frozen
pilot table is itself the transliteration ground truth. See guidelines.md §4.7.

---

## OQ-020 — `schemas/base_instance.schema.json` has no `generator_version` field to record the table version in — **RESOLVED (v0.9)**

**Encountered:** T07 design report, 2026-08-23, while checking exactly which field the
"table version recorded in `generator_version`" requirement (PROJECT_SPEC.md §8.3,
guidelines.md §4.5) refers to.

**Record:** `generator_version` exists only on `schemas/example.schema.json` (the
derived record) — confirmed by grep. `schemas/base_instance.schema.json` (frozen at T02,
extended for `base_kind` at OQ-003) has no `generator_version` field at all.

**The gap:** both documents say the transliteration table version is recorded in
`generator_version` and that Devanagari forms are "fixed at base-instance creation" /
"recorded in the base instance at creation time" (guidelines.md §4.5) — i.e. this
provenance is expected to live on the **base instance**, not only on downstream derived
records. But the base-instance schema currently has nowhere to put it. This is a
genuine schema gap surfaced by T07's own requirements, not an invented one — flagged
rather than fixed, since this design report makes no schema changes.

**Candidate resolutions:**
1. Add `generator_version` (and possibly `name_deva_table_version` specifically, if the
   PII-generator version and the transliteration-table version are meant to be tracked
   independently) as a required field on `schemas/base_instance.schema.json`, mirroring
   the existing field on the record schema.
2. Treat the base instance as provenance-free by design (only derived records carry
   `generator_version`), and read "recorded in the base instance at creation time" as
   describing *when* the transliteration happens, not *where* the version number is
   stored — the version would then only ever appear once records are derived (T08),
   never on the base instance itself.

**Status:** INVESTIGATED, NOT IMPLEMENTED, 2026-08-23. Per explicit instruction, this was
investigated and reported (see the T07 implementation-plan report) but the schema was
**not** modified this round.

**Current `generator_version` semantics (as investigated):** on
`schemas/example.schema.json` it is a required string, pattern
`^[0-9]+\.[0-9]+\.[0-9]+$` (simple semver — `"0.1.0"` in every fixture and every one of
the 100 generated records). PROJECT_SPEC.md §27 groups it with `config_version`,
`guidelines_version`, `seed`, `timestamp`, and `template_version` as provenance "every
run records." §8.3 / §4.5 both say the *transliteration table's* version is recorded in
this same field, not a separate one — there is no evidence anywhere of per-component
version fields (one for PII generators, a different one for the translit table); the
existing convention is a single version number for the whole generation toolchain
snapshot.

**Exact missing field/location:** `schemas/base_instance.schema.json` has no
`generator_version` field at all — confirmed by grep. Every one of the 100 records in
`data/raw/base_instances.jsonl` currently has no provenance field recording which
generator/table version produced it.

**Proposed representation:** add `generator_version` to
`schemas/base_instance.schema.json` as a required field, **reusing the exact same field
name and pattern** already defined on `schemas/example.schema.json`
(`{"type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"}`) — no new field name, no
new versioning convention.

**Why this is consistent with existing versioning:** it doesn't invent anything —
it's the same field, verbatim, applied to the sibling schema it was always described as
belonging to ("recorded in the base instance at creation time," §4.5). A single toolchain
version number already covers PII generation (T03) and would extend naturally to cover
transliteration (T07) and base-instance assembly (T04) under the same umbrella, matching
how the field is already used on records.

**Status:** RESOLVED, 2026-08-23, by explicit user decision. `generator_version` added
to `schemas/base_instance.schema.json` (required, identical field name and pattern to
`schemas/example.schema.json`'s existing field — no new versioning mechanism invented).
`generators/base_instances.py` now emits `generator_version: "0.1.0"` on every record.
See guidelines.md §4.5, decision 28.

---

## OQ-021 — No schema field exists to store ADDRESS's equivalent of `person_context.name_deva` — **RESOLVED (v0.9)**

**Encountered:** T07 implementation-plan report, 2026-08-23, investigating whether ADDRESS
needs an equivalent stored transliteration alongside PERSON's `person_context.name_deva`.

**Record:** guidelines.md §4.3 marks **both** PERSON and ADDRESS "Transliterable —
L3a/L3b split applies," with no distinction between them. §4.5 / PROJECT_SPEC.md §8.3
both say Devanagari forms are "recorded in the base instance at creation time," with no
PERSON-specific carve-out. But `schemas/base_instance.schema.json`'s `pii[]` item schema
only has `{type, base_pii_value, semantic_role}` — no field parallel to
`person_context.name_deva` exists anywhere for storing a pre-computed ADDRESS
transliteration. PERSON's Devanagari form has a home (`person_context.name_deva`)
because `person_context` already exists on every base for narrative/scenario reasons;
ADDRESS has no equivalent side-channel object.

**The gap:** either (a) ADDRESS's Devanagari form is not meant to be pre-computed and
cached at base-instance-creation time the way PERSON's is — despite §4.3/§4.5 treating
the two symmetrically — or (b) there is a missing schema field, parallel to
`name_deva`, that ADDRESS needs and doesn't have.

**Candidate resolutions:**
1. Add a field (e.g. `pii[].base_pii_value_deva`, sibling to `base_pii_value` on the
   same `pii[]` entry, nullable) to `schemas/base_instance.schema.json`, symmetric with
   how PERSON already gets `person_context.name_deva`.
2. Decide the two types are *not* actually symmetric in practice — only PERSON gets a
   base-instance-level cached Devanagari form (via `person_context`, which exists for
   narrative reasons independent of transliteration), and ADDRESS's Devanagari form is
   computed later, at record-derivation time (T08), directly from the table, never
   cached on the base instance at all.

**Status:** RESOLVED, 2026-08-23, by explicit user decision — candidate resolution 2
chosen: no `address_deva`-equivalent field is added. ADDRESS's Devanagari form is
generated later, at record-derivation time (T08), as `entities[].realized_pii_value`,
never cached on the base instance. `person_context.name_deva` remains the only stored
base-level Devanagari field. See guidelines.md §4.4, decision 29.

---

## OQ-022 — No transliteration method specified for ADDRESS abbreviation/initialism tokens (`"ABC"`, `"MG"`) — **RESOLVED (v0.9)**

**Encountered:** T07 implementation-plan report, 2026-08-23, while building the complete
table inventory from `generators/pii/address.py`'s frozen vocabulary.

**Record:** OQ-017's resolution (guidelines.md §4.8): every reachable lexical component
needs an explicit table entry. `generators/pii/address.py`'s frozen vocabulary contains
exactly two tokens that are not ordinary pronounceable words: `"ABC"` (in `"ABC
Apartments"`) and `"MG"` (in `"MG Road"`, conventionally short for Mahatma Gandhi).

**The gap:** OQ-017 settled *that* these need entries, not *how* to derive them. At
least three different, mutually exclusive choices exist: spell out each letter
phonetically (`"ABC"` → "ए बी सी"), transliterate the abbreviation as if it were a
pronounceable word (`"ABC"` → "एबीसी"), or leave it in Latin script inside an otherwise
-Devanagari address. Every other one of the 39 reachable ADDRESS lexical tokens (city
names, and standard English loanwords like "Apartments," "Towers," "Residency") has an
established, conventional Devanagari rendering I'm confident proposing without further
guidance; these two do not, because there is no single convention for transliterating an
abbreviation.

**Candidate resolutions:**
1. Spell out letters phonetically — most literal, but unusual to read for a building
   name.
2. Transliterate as a pronounceable syllable string — reads more naturally as a name but
   is a linguistic judgment call, not a mechanical rule.
3. Carve out an explicit exception: abbreviations/initialisms stay in Latin script even
   inside a Devanagari-carrier address — adds a second rule class to what was framed as
   a uniform table lookup.

**Status:** RESOLVED, 2026-08-23, by explicit user decision. `ABC` → `एबीसी`, `MG` →
`एमजी`, frozen as benchmark-specific deterministic conventions — explicitly documented
as not claims about universal correct transliteration of these abbreviations. Frozen
ADDRESS vocabulary (`generators/pii/address.py`) unchanged. See guidelines.md §4.8,
decision 30. All 39 reachable ADDRESS lexical tokens now have table entries.

---

## OQ-023 — `EN` vs `IN_EN`: no objective boundary for what counts as "Indian English" — **RESOLVED (v0.10)**

**Encountered:** T08 language-realization design report, 2026-08-23.

**Record:** PROJECT_SPEC.md §8 / guidelines.md §4.2 — `EN` = "Standard English",
`IN_EN` = "Indian English." Both share identical carrier/PII script (Latin/Latin). No
document says anything further.

**The gap:** the only proposed distinguishing content is Indian-English discourse
markers/idioms ("kindly," "do the needful," "revert," "please find below," "intimate"
as a verb, present-continuous for stative verbs) layered onto otherwise-standard English
grammar, with **zero Hindi vocabulary** (that boundary is what separates `IN_EN` from
`HINGLISH`, not from `EN`). This is a real, documented feature of the Indian English
variety, not fabricated — but the *line* between "an Indian English idiom" and "just
formal or slightly old-fashioned English used anywhere" is genuinely fuzzy and
subjective. A word like "kindly" is common in Indian English but is not exclusively
Indian; treating any one marker as sufficient or necessary is a judgment call.

**Candidate resolutions:**
1. Freeze a fixed, closed list of Indian-English markers (a small curated set, similar
   in spirit to T07's closed vocabulary) — any `IN_EN` sentence must contain at least
   one marker from the list, and `EN` sentences must contain none. Deterministic and
   testable, but the list itself is an editorial judgment call requiring explicit
   sign-off.
2. Treat `EN` as reusing `canonical_text` verbatim (the base's existing English
   sentence, already deterministic and free), and `IN_EN` as an LLM-paraphrase of it
   with an explicit prompt instruction naming the Indian-English register — accepting
   that the *boundary* is enforced by generation instruction, not by a checkable rule,
   and validated only by human review (§19, "Language correct?").
3. Drop the automated-boundary goal entirely for this pair specifically — treat `IN_EN`
   as inherently a register/fluency judgment no rule can fully pin down, same
   conclusion as OQ-015 reached for Hinglish more broadly.

**Status:** RESOLVED, 2026-08-23, by explicit user decision — candidate resolution 1
chosen: a frozen, closed 8-item marker inventory (`kindly`, `do the needful`, `revert`,
`prepone`, `please find below/attached`, `intimate`, `the same`, `at the earliest`).
`EN` = zero markers; `IN_EN` = at least one. Explicitly documented as legitimate
dialectal features, not incorrect English. See guidelines.md §4.12, decision 33.

---

## OQ-024 — `ROM_HI` vs `HINGLISH`: no rule for whether established English loanwords count as code-mixing — **RESOLVED (v0.10)**

**Encountered:** T08 language-realization design report, 2026-08-23.

**Record:** PROJECT_SPEC.md §8 / guidelines.md §4.2 — `ROM_HI` = "Romanized Hindi"
(implies: Hindi-language sentence, Latin script). `HINGLISH` = "Hindi–English
code-mixed" (implies: an actual blend of Hindi and English words). Both share identical
carrier/PII script (Latin/Latin) — script alone cannot distinguish them.

**The gap:** modern spoken Hindi routinely uses English loanwords for concepts with no
common native equivalent — "number," "mobile," "email," "bank," "account," and
arguably "PAN" itself (an English acronym with no native Hindi expansion in common
use). A `ROM_HI` sentence for a PAN base almost certainly needs *some* of these words.
Neither document says whether using such widely-nativized loanwords still counts as
"pure" Romanized Hindi (i.e. `ROM_HI` permits them), or whether *any* English lexical
item at all tips a sentence into `HINGLISH` territory (i.e. `ROM_HI` must use
Sanskritized/native equivalents like "संख्या" for "number," phonetically written in
Latin script). This is the single hardest linguistic boundary among all seven
conditions — it does not reduce to a script or vocabulary-closed-set rule the way T07's
PII transliteration did.

**Candidate resolutions:**
1. `ROM_HI` may use a small, explicitly frozen allowlist of fully-nativized loanwords
   (e.g. `number`, `mobile`, `email`, `bank`, `account`, `PAN`, `Aadhaar`, `UPI`) and
   otherwise must use Hindi grammar/vocabulary throughout, with no other English content
   words. `HINGLISH` permits freer mixing beyond this allowlist, including English words
   that *do* have common Hindi equivalents.
2. `ROM_HI` must avoid all English content words without exception, using
   Sanskritized/native Hindi even for technical terms — the "purest" reading of
   "Romanized Hindi," but produces sentences less natural/common in real usage.
3. Merge the distinction into a single graded axis (code-mixing density: 0%, low,
   high) rather than a hard binary, and pick threshold values for `ROM_HI` (near 0%,
   allowlist only) vs `HINGLISH` (moderate-to-high) — same substance as resolution 1,
   framed as a spectrum rather than a rule.

**Status:** RESOLVED, 2026-08-23, by explicit user decision — candidate resolution 1
chosen: a frozen 8-item ordinary-loanword inventory (number, mobile, email, bank,
account, address, PAN, UPI — each with a romanized and Devanagari-carrier form) bounds
`ROM_HI`; a separate frozen HINGLISH insertion inventory (please, sir/ma'am, confirm,
actually, check, sorry, thanks, okay, problem, update) defines what counts as "beyond"
it. Explicitly a closed-set membership test — no LLM classifies the boundary. See
guidelines.md §4.13, decision 34. This resolves RQ2's ordering-hypothesis testability
concern raised in the original entry.

---

## OQ-025 — `HINGLISH` vs `INFORMAL_HINGLISH`: no threshold for "informal enough" — **RESOLVED (v0.10)**

**Encountered:** T08 language-realization design report, 2026-08-23.

**Record:** PROJECT_SPEC.md §8 / guidelines.md §4.2 — `HINGLISH` = "Hindi-English
code-mixed," `INFORMAL_HINGLISH` = "WhatsApp-register Hinglish." Same underlying
code-mixing phenomenon; the label names a register/formality difference, not a
vocabulary or script difference.

**The gap:** plausible `INFORMAL_HINGLISH` markers exist (abbreviations like "u," "ur,"
"pls," "thx"; casual particles like "yaar," "bro," "na," "toh"; non-standard/phonetic
spelling; minimal capitalization and punctuation; sentence fragments) — but no document
states how many such markers, or which specific ones, distinguish "informal" from
plain `HINGLISH`. A single stray "yaar" tipping a sentence into a different labeled
condition versus requiring multiple co-occurring markers are different, defensible
policies with no basis to choose between them in the governing documents.

**Candidate resolutions:**
1. Require at least one marker from each of two categories (a lexical/particle marker
   *and* a typographic marker — e.g. lowercase-only or an abbreviation) before a
   sentence qualifies as `INFORMAL_HINGLISH`; `HINGLISH` requires zero from either
   category.
2. Single-marker threshold: any one recognizable informal-register feature is
   sufficient.
3. No rule-based threshold at all — generate `INFORMAL_HINGLISH` via an LLM prompt
   explicitly instructed to produce WhatsApp-register text, and rely on human review
   (§19, "Natural?") rather than an automated boundary check.

**Status:** RESOLVED, 2026-08-23, by explicit user decision — `INFORMAL_HINGLISH` =
`HINGLISH`'s mixing requirement (OQ-024) + at least one marker from four frozen
categories (abbreviation, casual particle, informal copula/contraction, typographic
register). "At least one" is not an arbitrary threshold here — it mirrors the same
pattern already adopted for `IN_EN` (OQ-023) and `HINGLISH` (OQ-024), applied
consistently. See guidelines.md §4.14, decision 35.

---

## OQ-026 — Hindi-script carrier-text generation needs more than T07's table, which was deliberately scoped not to provide it — **RESOLVED (v0.10)**

**Encountered:** T08 language-realization design report, 2026-08-23, while specifying
how `HI_LATIN_PII`/`HI_DEVA_PII`/`ROM_HI` carrier text would actually be produced.

**Record:** guidelines.md §4.7 (T07, OQ-016/OQ-019, frozen v0.8): *"This is a
benchmark-specific deterministic transliteration table, not a general-purpose Hindi
transliteration system"* — 79 entries, covering exactly the PERSON/ADDRESS PII
vocabulary reachable from the frozen T03 generators. No character-level substitution,
no algorithm, no external library.

**The gap:** `HI_LATIN_PII` and `HI_DEVA_PII` need a full Hindi **sentence** around the
PII value (e.g. `"मेरा नाम राहुल शर्मा है।"`, guidelines.md §16's own worked example) —
carrier words like `मेरा` ("my"), `नाम` ("name"), `है` ("is") are not PII, are not in
T07's table, and were never meant to be (T07 is PII-value transliteration only).
`ROM_HI` needs the same Hindi sentence content, just rendered in Latin script instead.
Producing this carrier text requires either (a) generating Hindi sentences directly via
an LLM in whichever script is needed per condition (Devanagari for
`HI_LATIN_PII`/`HI_DEVA_PII`, Latin/romanized for `ROM_HI` and both Hinglish
conditions), with T07's table used only to substitute the transliterated PII value into
that LLM-generated carrier text when the base type is PERSON/ADDRESS — or (b) building
a *second*, much larger general-purpose Hindi transliteration/generation system, which
would directly contradict OQ-016/OQ-019's explicit "not a general-purpose... system"
framing for T07.

Reading (a) seems clearly preferable and consistent with PROJECT_SPEC.md §14.2's
explicit LLM permission ("generate and paraphrase natural language; produce Hinglish
register variation") — but no document states this division of labor (LLM owns carrier
text in the target script/register; T07 owns only the closed PII-value substitution)
explicitly, so it's reported as a finding requiring confirmation, not assumed.

**Candidate resolutions:**
1. Confirm reading (a) as the intended architecture: carrier text is LLM-generated
   directly in the correct script/register per condition; T07's table is invoked only
   to transliterate PERSON/ADDRESS PII values for insertion into that carrier text
   (exactly as T07 already does for `person_context.name_deva`).
2. Build a second, general-purpose Hindi transliteration capability for carrier text
   specifically — understanding this is a materially larger undertaking than T07 and
   revisits the "not a general-purpose system" framing just frozen for T07.

**Status:** RESOLVED, 2026-08-23, by explicit user decision — candidate resolution 1
confirmed: T07 remains exclusively responsible for deterministic PII transliteration;
T08 generates/constructs the carrier-language sentence; for `HI_DEVA_PII`, T08 obtains
PERSON/ADDRESS Devanagari PII from T07; non-transliterable PII is never altered. No
general-purpose Hindi transliteration/generation system was built — candidate 2 was not
taken. See guidelines.md §4.10, decision 31.

---

## Summary: OQ-012's sub-questions, all now resolved

OQ-012 (no linguistic content definition for the seven realizations) remains formally
UNRESOLVED as the parent entry, but every concrete sub-question it spawned is now
resolved: OQ-023 (`EN`/`IN_EN`), OQ-024 (`ROM_HI`/`HINGLISH`), OQ-025
(`HINGLISH`/`INFORMAL_HINGLISH`), OQ-026 (T07/T08 division of labor). The full
resulting specification — carrier templates, deterministic validation rules, human-
review criteria — is in the T08 implementation-specification report, not reproduced
here. T08 generation itself has not started.

---

## OQ-028 — No formal schema for a detector's predicted-entity output — **RESOLVED (PROJECT_SPEC.md v1.2)**

**Encountered:** T09 (evaluation-layer) design report, 2026-08-23.

**Record:** `schemas/example.schema.json` freezes the **ground-truth** entity shape
(`type`, `base_pii_value`, `realized_pii_value`, `pii_script`, `start`, `end`,
`occurrence_index`). PROJECT_SPEC.md §19 names five baselines (regex, spaCy, Presidio,
a multilingual transformer, an Indian-adapted variant of it) but never defines what a
**prediction** looks like, or what common shape all five must be normalized into before
scoring.

**The gap:** each baseline's native output format differs (spaCy `Doc.ents`, Presidio's
`RecognizerResult`, a raw regex match, a transformer's token-classification spans).
Nothing says what the harness-facing common format is, so nothing says what "the same
evaluation code runs against every baseline" actually requires each adapter to produce.

**Candidate resolutions:**
1. A minimal frozen prediction schema: `{type: str, start: int, end: int}` (offsets into
   the *original* input text, code-point indices, matching ground truth's convention) —
   no `occurrence_index` (a detector doesn't know ground truth's occurrence numbering;
   scoring resolves that, see OQ-029), no `realized_pii_value` (redundant with
   `text[start:end]`), optional `confidence`/`score` for future operating-point analysis
   (§24.2).
2. Reuse the full ground-truth entity schema for predictions too, even though several
   fields (`base_pii_value`, `occurrence_index`) don't have an obvious detector-side
   source — simpler symmetry, but fields with no real meaning on the prediction side.

**Status:** RESOLVED, 2026-08-23, by explicit user decision after audit. Frozen in
PROJECT_SPEC.md §20.2 (v1.2): `{type, start, end}` required, `{text, confidence}`
optional, batch-level `system_name`/`system_version`, `variant_id` record linkage,
malformed predictions rejected/logged never silently dropped. Canonical home:
`benchmark/schema.py` (not yet created — this freezes the contract, not the
implementation). Directly extends §24.3's existing application-context detector-output
contract rather than contradicting it.

---

## OQ-029 — `occurrence_index` semantics for scoring (not generation) are unspecified — **RESOLVED (PROJECT_SPEC.md v1.2)**

**Encountered:** T09 design report, 2026-08-23.

**Record:** guidelines.md §13.2 defines `occurrence_index` for **generation/annotation**
(resolve repeated ground-truth values by walking matches in order). No document
addresses what happens at **scoring** time when a detector predicts a span at the
*correct* character position for occurrence 0 of a repeated value, but ground truth
labels that position as occurrence 1 (or vice versa) — or when a detector's single
prediction happens to land on the *wrong* occurrence of a repeated value entirely.

**The gap:** T08's current 624 records all have `occurrence_index: 0` (no template
repeats a PII value within one sentence), so this doesn't yet affect any real score —
but T09's design should specify the rule before multi-PII bases or adversarial variants
(which could repeat values) start being scored.

**Candidate resolutions:**
1. Match predictions to ground-truth entities purely by **span position** (start/end
   overlap), never by `occurrence_index` — a prediction at the exact character offset of
   ground truth's occurrence 1 counts as matching occurrence 1, regardless of what
   "occurrence number" the detector itself has no way of knowing. `occurrence_index`
   remains a ground-truth/generation concept only, invisible to scoring.
2. Some more elaborate occurrence-aware matching that tries to align predicted spans to
   ground-truth occurrences by rank rather than position — more complex, no clear benefit
   over resolution 1, and no document motivates it.

**Status:** RESOLVED, 2026-08-23. Frozen in PROJECT_SPEC.md §20.3 (v1.2):
`occurrence_index` is ground-truth provenance only, never consumed by prediction
matching, which is resolved purely by span geometry (part of the OQ-031 matching
algorithm). Worked example (guidelines.md §13.2's repeated-PAN case) included in §20.3,
demonstrating the resolution is order-independent and correctly handles both full and
partial detection of repeated identical values without ever inspecting
`occurrence_index`.

---

## OQ-030 — What counts as "correctly localized" for M5 (type accuracy)? — **RESOLVED (PROJECT_SPEC.md v1.2)**

**Encountered:** T09 design report, 2026-08-23.

**Record:** PROJECT_SPEC.md §20's metric table: `M5 | Type accuracy | correct type
among correctly localized entities`. §20 also names `M3` (Entity F1, implicitly
lenient/overlap-based) and `M4` (Exact-span F1, explicitly strict) as two different
localization strictness levels, with "Never report M3 alone" because their gap is
itself informative.

**The gap:** M5's own definition uses the word "localized" without saying which of M3's
or M4's strictness it means. Type accuracy computed only among *exact-span* matches
(M4-strict) is a different, smaller, harder number than type accuracy computed among
*any-overlap* matches (M3-lenient) — and the two would support different conclusions
about whether a system's failures are boundary problems or genuine type-confusion
problems (exactly the RQ5/F2-vs-F3 distinction the failure taxonomy exists to make).

**Candidate resolutions:**
1. M5 uses the same strictness as M4 (exact span) — "localized" means "found at exactly
   the right place," the strictest reading.
2. M5 uses the same strictness as M3 (any overlap) — "localized" means "found in
   roughly the right place," a looser reading that surfaces more type-confusion cases.
3. Report M5 under *both* strictness levels, mirroring the M3/M4 "report both, the gap
   is informative" pattern already established for span accuracy.

**Status:** RESOLVED, 2026-08-23, by explicit user decision after audit — candidate
resolution 2 chosen: `M5` uses the same lenient (overlap) localization basis as
`M2`/`M3`, anchored directly in this document's own "M2-vs-M5 measures detect-but-
mislabel" sentence (§20). Frozen in PROJECT_SPEC.md §20.4 (v1.2) with the full
`TP_type`/`TP_exact`/`L` formalization, the identity `M2 = M5 × localization_recall`,
and an explicit proof that `F1`/`F2`/`F3` partition every ground-truth entity without
overlap or gap. An optional `M5_exact` secondary diagnostic (mirroring the `M3`/`M4`
"report both" pattern) was proposed but not required.

---

## OQ-031 — No policy for overlapping or nested predictions from the same detector — **RESOLVED (PROJECT_SPEC.md v1.2)**

**Encountered:** T09 design report, 2026-08-23.

**Record:** no document addresses what happens when a single detector emits two
predictions whose spans overlap or nest for the same input text (e.g. a PERSON
prediction fully containing a shorter prediction of another type, or two predictions
covering the same characters with different types).

**Candidate resolutions:**
1. Score every prediction independently against ground truth (no deduplication) — a
   detector that emits overlapping predictions is simply penalized by the resulting
   false positives, with no special-casing.
2. Deduplicate overlapping same-type predictions before scoring (keep the
   highest-confidence one, if confidence is available); leave overlapping
   different-type predictions untouched (both are independently scorable, since
   different types can legitimately describe different real spans).
3. Reject/flag any detector whose output contains overlaps as a structurally invalid
   submission, forcing every adapter to resolve overlaps upstream.

**Status:** RESOLVED, 2026-08-23, by explicit user decision after audit — maximum-weight
bipartite matching (type-match-biased weight, deterministic lexicographic-perturbation
tie-break), not naive greedy. Frozen in PROJECT_SPEC.md §20.3 (v1.2). Audited against
all eight required scenarios (two predictions competing for one entity; one prediction
spanning two entities; nested predictions; duplicate predictions; globally-tied optimal
assignments; correct-type/low-overlap vs. wrong-type/high-overlap; multiple same-type
entities; repeated identical PII) before freezing — the tie-break was refined during
audit from a simple post-hoc rule (which could break global-optimality guarantees on
ties) to an infinitesimal-perturbation term embedded in the optimization itself.

---

## OQ-032 — Are out-of-taxonomy predicted types penalized or ignored? — **RESOLVED (PROJECT_SPEC.md v1.2)**

**Encountered:** T09 design report, 2026-08-23.

**Record:** the benchmark's taxonomy is exactly eight PII types (guidelines.md,
PROJECT_SPEC.md §7). General-purpose NER baselines (spaCy, a multilingual transformer)
routinely predict entity types outside this set — `ORG`, `GPE`, `DATE`, `MONEY`, etc.

**The gap:** does a predicted `ORG` span count as a false positive (penalizing
precision, M1/M6) the same way a wrongly-predicted `PERSON` span on non-PII text would,
or is it simply outside the benchmark's scope and excluded from scoring entirely
(neither helping nor hurting)? These produce materially different precision numbers for
any baseline that predicts a broad entity-type inventory.

**Candidate resolutions:**
1. Ignore/discard any prediction whose type is not one of the eight before scoring —
   the benchmark only ever asks "how well does this system find *our* PII types,"
   never "does it also avoid predicting other things."
2. Count every out-of-taxonomy prediction as a false positive if its span overlaps any
   character position — the benchmark cares about total noise a system introduces into
   PII-focused output, not just taxonomy-matched noise.
3. Count it as a false positive only if its span overlaps a ground-truth PII span
   specifically (i.e. the detector found *something* there but mislabeled it out of
   taxonomy) — a middle ground between 1 and 2.

**Status:** RESOLVED, 2026-08-23, by explicit user decision after audit — candidate
resolution 2 chosen (§20.5, PROJECT_SPEC.md v1.2): out-of-taxonomy predictions are
**ordinary `F4` FALSE_POSITIVE** under `M1`'s existing definition, counted fully (never
excluded from `M1`/`M6`). **Corrected from this OQ's own T09-design-report proposal**,
which suggested a new `OUT_OF_TAXONOMY` attribution tag — on audit this was found
unnecessary: the existing `decoy_class`-present-or-absent distinction (populated only
when a real `distractors[]` entry is hit, simply absent otherwise) already carries the
same diagnostic information with zero expansion of the F1–F9 taxonomy. Adapters must
report every prediction, never silently discard out-of-taxonomy ones.

---

## OQ-033 — No offset-integrity rule for baseline preprocessing/normalization — **RESOLVED (PROJECT_SPEC.md v1.2)**

**Encountered:** T09 design report, 2026-08-23.

**Record:** guidelines.md §4.6 fixes the offset convention for ground truth (Python
Unicode code-point indices into the exact `text` string). PROJECT_SPEC.md §19.2
requires disclosure discipline for baseline configuration but says nothing about
text preprocessing specifically.

**The gap:** if a baseline internally lowercases, Unicode-normalizes (NFC/NFKC), or
otherwise transforms text before running inference, and returns offsets into *its own*
transformed copy rather than the original input, those offsets will not line up with
ground truth's `text[start:end]` convention — silently corrupting every score for that
baseline without necessarily raising an error.

**Candidate resolutions:**
1. Freeze a rule: every baseline adapter must return offsets into the **original,
   unmodified** input text, regardless of what preprocessing the underlying model does
   internally — the adapter is responsible for mapping any internal offsets back. The
   evaluation harness verifies `original_text[start:end]` is non-empty and sane before
   scoring each prediction, and rejects/logs (never silently coerces) any prediction
   that fails this check.
2. Permit each baseline to report offsets into its own normalized text, with the harness
   maintaining a per-baseline mapping back to original offsets — more flexible, but adds
   a second offset-translation layer that could itself introduce bugs.

**Status:** RESOLVED, 2026-08-23, by explicit user decision — candidate resolution 1
chosen: strict original-text-only offset contract, frozen in PROJECT_SPEC.md §20.6
(v1.2). Adapters must reverse-map any internal normalization/tokenization before
returning offsets; the evaluator performs a hard structural range check and never
normalizes or mutates benchmark text itself. Explicitly justified against Devanagari/
mixed-script records specifically (precomposed vs. decomposed conjunct/matra
representations under NFC/NFKC normalization), not asserted as a generic disclaimer.

---

## OQ-034 — Is evaluation-layer work authorized under the current Pilot v0.1 milestone? — **RESOLVED (investigative finding, no spec change)**

**Encountered:** T09 design report, 2026-08-23.

**Record:** CLAUDE.md: *"Current milestone: Pilot v0.1 — exactly 100 base instances...
Nothing beyond this is authorised."* PROJECT_SPEC.md §31's T01–T14 task list ends with
*"T14 pilot quality report + leakage test → STOP."* The requested evaluation-layer
content (detector I/O formats, baselines B1–B5, metrics M1–M6, experiments E01–E10)
is entirely PROJECT_SPEC.md Part III (§19–23), never assigned a T-number and structurally
positioned *after* the T01–T14 list's explicit stop point.

**The gap:** this report answers the evaluation-layer design questions as requested —
design work doesn't itself violate the milestone gate the way running baselines or
training a model would. But *implementing* any of it (baseline adapters, the scorer,
`benchmark/`/`baselines/` code) is a different milestone's work under the current
governing documents, not something this design report resolves by producing answers.

**Status:** RESOLVED as an investigative finding, 2026-08-23 — **evaluation-layer work
is NOT authorized under the current Pilot v0.1 milestone.** PROJECT_SPEC.md §32's
"Definition of Done — Pilot v0.1" checklist (17 items) was re-read in full: every item
concerns dataset generation and dataset-quality validation; none mentions baselines,
detectors, or M1–M6 evaluation of any kind. The checklist's own closing line —
*"Only then: **APPROVED FOR PRODUCTION SCALE**"* — confirms completing it unlocks
production-scale *generation*, not evaluation. Combined with CLAUDE.md's *"Current
milestone: Pilot v0.1 — exactly 100 base instances... Nothing beyond this is
authorised,"* this is conclusive without needing a new rule.

**Correction to this entry's own earlier framing:** CLAUDE.md's itemized "forbidden
right now" list explicitly names training/fine-tuning but does not explicitly name
baseline *inference* — the prohibition is not as blanket on that specific point as
previously stated. The finding above rests on §32's silence on evaluation as a
completion criterion, not on an explicit inference ban.

**Precision distinction:** the *literal* T09 (PROJECT_SPEC.md §31: "span extractor +
occurrence-aware validator" — i.e. `generators/language/spans.py` plus a dataset-quality
span validator) **is** explicitly authorized — it is item after item in §32's checklist
("exact spans, occurrence-indexed, code-point offsets"; "structural / span / semantic /
language / script validators implemented"). Only the *evaluation-layer* reinterpretation
of "T09" — the subject of this whole OQ thread — is unauthorized.

---

## OQ-035 — 6 of 8 `semantic_role` values are never frozen in a governing document — **RESOLVED (v0.12)**

**Encountered:** T10 (semantic validator) design investigation, 2026-08-24.

**Record:** T10's requirement 1 is "the declared PII type is consistent with the expected
semantic role." Checking that requires an independent, authoritative type→`semantic_role`
table. Searched every governing document for one:

- `annotation/guidelines.md` §13.5 (the section that specifically defines how
  `semantic_role` works, added v0.6 to resolve OQ-007) states the rule ("type-fixed, one
  value per type") and gives exactly **one** row: `PERSON` → `PERSON_NAME`. No other type
  appears in that table or anywhere else in the file.
- `PROJECT_SPEC.md` §12.1 shows exactly **one** illustrative JSON example:
  `{"type": "PAN", ..., "semantic_role": "TAX_IDENTIFIER"}` — a worked example, not a
  ratified table, and covering only one more type.
- `schemas/base_instance.schema.json`'s `pii[]` item deliberately leaves `semantic_role`
  as unconstrained free text (`"type": "string", "minLength": 1`, no enum) — consistent
  with this project's "schema = structure only, cross-field logic = validators" rule
  (established at T02, reused for `base_kind`), i.e. the schema was never meant to be the
  source of truth for this table either.
- `configs/pilot.yaml` and `annotation/CHANGELOG.md` do not mention any of the other 6
  role strings.

The remaining 6 values (`DELIVERY_ADDRESS`, `CONTACT_NUMBER`, `CONTACT_EMAIL`,
`NATIONAL_ID_IDENTIFIER`, `PAYMENT_IDENTIFIER`, `PAYMENT_ACCOUNT_IDENTIFIER`) exist in
exactly one place in the whole repository: `generators/base_instances.py`'s
`SEMANTIC_ROLE` dict — generator *code*, not a governing document.

**The rule that failed:** CLAUDE.md §3's prime directive — do not silently treat
something as frozen spec that was never actually written into a governing document, even
when it is overwhelmingly likely to be correct. Treating generator code as ground truth
inside a *validator* whose whole purpose is to check the generator's output independently
would make that part of the check circular — it could never catch a mismatch that
originated in the generator itself, only in a hand-mutated test record.

**Context supporting the obvious resolution:** this is very likely a paperwork gap, not a
real design disagreement. Per this session's own T04 design-freeze turn, the user
explicitly approved a full 8-type `semantic_role` mapping (including the 6 at issue here)
before T04's generation run — OQ-007 only ever corrected the `PERSON` row afterward, and
whoever wrote the OQ-007 fix into guidelines.md §13.5 evidently updated only the row that
changed, never back-filled the other 7 that were already correct and already approved.

**Candidate resolutions:**
1. Ratify the full 8-type table into `guidelines.md` §13.5 now, using
   `generators/base_instances.py`'s existing `SEMANTIC_ROLE` dict values verbatim (they
   were already approved in the T04 design-freeze turn and have been unchanged and
   unchallenged since T07). Bump `guidelines_version`, log in `annotation/CHANGELOG.md`.
   This is the resolution T10's implementation is written to expect.
2. Ratify a table with different values for one or more of the 6 unfrozen types, if any
   of them are judged as weak as the original `ACCOUNT_HOLDER_NAME` was for `PERSON`.
3. Decline to freeze a table at all, and scope T10's "type consistent with expected role"
   check to `PERSON` only (the one type that *is* frozen), reporting the other 6 types'
   semantic-role check as `NOT_APPLICABLE` rather than `PASS`/`FAIL`.

**Status:** RESOLVED (v0.12), 2026-08-24 — candidate resolution 1 chosen. All eight
`type` → `semantic_role` rows are now written into `annotation/guidelines.md` §13.5
(decision 39, §21). Verified beforehand that these are exactly the values the frozen T04
dataset uses — `python` scan of all 100 records of `data/raw/base_instances.jsonl`
confirmed one `semantic_role` value per type, matching this table exactly, no unexpected
value anywhere in the dataset. No dataset file was changed; this is a documentation
freeze of values already in effect since T04, not a new decision about what those values
should be. `guidelines_version` bumped 0.11 → 0.12; logged in
`annotation/CHANGELOG.md`; version pointers updated in `PROJECT_SPEC.md` (header +
§35), `configs/pilot.yaml`, and `tests/fixtures/example.valid.json`. The 624 already-
generated derived records and `generators/base_instances.py`'s own `guidelines_version`
provenance constants are untouched — they correctly continue to record `"0.11"`, the
version they were actually generated under (guidelines.md §22's own provenance rule).

---

## OQ-036 — No deterministic check exists for "the sentence uses the value in the declared role" — **RESOLVED (v0.12), partially**

**Encountered:** T10 (semantic validator) design investigation, 2026-08-24.

**Record:** `guidelines.md` §15 Layer 3 / `PROJECT_SPEC.md` §15 both define semantic
validation as: *"Sentence uses the value in the declared role."* T10's requirement 2 asks
for exactly this: verify that the realized PII is being used as its declared role
*within the sentence text itself* — not just that the metadata around it is consistent.

**The gap:** no governing document specifies a deterministic, non-heuristic procedure for
reading a sentence and confirming a value is being used in a given role. The two
candidate mechanisms both fall outside what's already frozen:

1. **Keyword/label matching** ("does a role-indicative word like 'PAN' or 'Aadhaar'
   appear near the span") — this is a heuristic invented for the occasion, exactly what
   this task's own instructions say not to do without governance approval
   ("do not compensate with keyword heuristics without governance approval").
2. **Template-conformance matching** (checking the carrier text against the frozen
   carrier templates in `guidelines.md` §4.10–4.14) — those templates were frozen for
   *generation* (T08), not ratified for reuse as a *validation* oracle, and for this
   100%-templated pilot dataset the check would collapse into checking Layer 4
   (language/realization correctness) rather than Layer 3 (semantic role), since each
   type maps to exactly one template family — there is no dataset-internal case where the
   template is right but the role is wrong, or vice versa, so the two layers are not
   distinguishable by construction here.

Everything else T10 was asked to check (requirements 1, 3–9) reduces to metadata
cross-referencing between the record and its source base instance — genuinely
deterministic, not text-content parsing. Requirement 2 is the one exception.

**Candidate resolutions:**
1. Accept that, for this specific 100%-template-generated pilot dataset, requirements 1
   (type↔role, pending OQ-035) and 7 (matched-variant carrier-text identity, already
   checkable) together provide *indirect, structural* evidence of correct role usage by
   construction — and formally scope requirement 2 out of T10 as `NOT_APPLICABLE` for this
   dataset, revisiting it only if a future task introduces non-templated or human/LLM
   authored text where the template-implies-role shortcut no longer holds.
2. Authorize template-conformance matching (mechanism 2 above) as T10's Layer-3 oracle,
   accepting that it overlaps with Layer 4 for this dataset, and note that overlap as a
   design property of a template-only pilot rather than a defect.
3. Authorize a specific, frozen keyword/label list per type (mechanism 1 above) as an
   explicit governance decision, with the list itself added to `guidelines.md`.

**Status:** RESOLVED (v0.12), 2026-08-24, **partially** — neither candidate resolution 1
nor 2 nor 3 above was chosen as originally framed. A fourth option, found during the
governance-resolution turn, was preferred: **formalize an implicit rule that already
existed**, rather than either declining coverage outright (candidate 1) or authorizing a
new heuristic/template reuse (candidates 2/3, both explicitly ruled out by name in the
resolution instructions — no keyword list, no hidden template oracle).

The implicit rule: PROJECT_SPEC.md §12.1 already defines a base instance's
`canonical_text` as part of the *same* semantic record as `semantic_role` and `type`, not
a downstream generation artifact — and T08's `EN` condition was independently confirmed
(all 100 records) to reproduce that field byte-for-byte with no transformation. This was
already true; nothing about its meaning changed by writing it down. `guidelines.md` §13.6
(decision 40, §21) now states it as the frozen ground truth for Layer 3 on unperturbed
`EN` records only: `record.text == base.canonical_text`, exact string equality. A mismatch
is `SEMANTIC_MISMATCH`.

**What remains open:** this contract only yields a two-way PASS/FAIL split for `EN` — it
cannot, by itself, distinguish "value used in the wrong role" from "value present but no
role asserted" (both show as inequality), and it gives no coverage at all for the other
six language conditions (`IN_EN`, `HI_LATIN_PII`, `HI_DEVA_PII`, `ROM_HI`, `HINGLISH`,
`INFORMAL_HINGLISH`) since none of them has a canonical-text equivalent to check against.
Closing that gap needs its own new governance content (e.g. a per-language marker
taxonomy), not a formalization of something already agreed — split out as **OQ-037**
below rather than folded into this entry's resolution.

Metadata-level role consistency (does `base.pii[].semantic_role` match the frozen §13.5
table, independent of any sentence) is unaffected by this scoping — that check, from
OQ-035's resolution, applies to every record regardless of language condition, and is how
"semantic-role metadata inconsistent with the sentence" is still caught for all seven
conditions even where the sentence itself is never parsed.

---

## OQ-037 — No deterministic Layer-3 text-content check exists for the six non-`EN` language conditions — **RESOLVED (v0.13)**

**Encountered:** OQ-036 resolution, T10 governance turn, 2026-08-24.

**Record:** OQ-036 resolved a deterministic Layer 3 ("sentence uses the value in the
declared role") ground truth for unperturbed `EN` records only —
`record.text == base.canonical_text` (guidelines.md §13.6, decision 40) — because `EN` is
the one condition where the derived text is defined to be byte-identical to a field the
base instance already carries as part of its own semantic record. `IN_EN`, `HI_LATIN_PII`,
`HI_DEVA_PII`, `ROM_HI`, `HINGLISH`, and `INFORMAL_HINGLISH` have no such field to compare
against — their text is a genuine transformation of the canonical sentence, and no
governing document freezes what the "declared role, correctly asserted" surface form of
that transformation looks like.

**The gap:** closing this would require freezing new content — e.g. a per-type,
per-language canonical marker/label string, or an equivalent mechanism — sufficient to
recognize correct role assertion in each of the six transformed registers. This is
qualitatively different from OQ-035/036, which formalized decisions already implicit in
approved work; this would be new specification-writing, and is explicitly out of scope
for a "formalize, don't invent" resolution.

**Candidate resolutions:**
1. Leave Layer 3 text-content checking `NOT_APPLICABLE` for these six conditions
   indefinitely at pilot scale — T10 validates them on every other axis (type↔role,
   domain consistency, cross-variant identity, matched-variant invariant, collapsed-record
   equivalence), just not "does the sentence itself assert the role."
2. Freeze a per-type, per-language canonical label inventory (e.g. `"PAN"` /
   `"PAN number"` for `PAN` in every condition, `"पैन"` for `HI_DEVA_PII`, etc.) as a new,
   explicit governance decision, mirroring how §4.12–§4.14 froze marker inventories for
   `IN_EN`/`HINGLISH`/`INFORMAL_HINGLISH` classification — distinct from, and not reusing,
   the T08 carrier templates.
3. Defer the question until production scale, on the reasoning that a 100%-templated
   pilot dataset cannot exercise the failure modes this check exists to catch (every
   record's template already ties type to role by construction), so the check would have
   zero discriminating power over the current 624 records regardless of how it's defined.

**Status:** RESOLVED (v0.13), 2026-08-24. Neither of the three originally-listed candidate
resolutions was chosen as framed. A fourth path, found on closer audit: split the six
conditions into two groups rather than treating them as one problem.

`IN_EN` turned out not to need a new label table at all — §4.12 defines it as `EN` plus a
wrapping marker, never a rewrite, and this was verified directly: `base.canonical_text`
occurs as an exact substring of `record.text` in all 100 `IN_EN` records, zero
exceptions. Ground truth: `base.canonical_text in record.text` — a direct generalization
of OQ-036's `EN` equality from "equals" to "contains."

The remaining five (`ROM_HI`, `HINGLISH`, `INFORMAL_HINGLISH`, `HI_LATIN_PII`,
`HI_DEVA_PII`) genuinely translate the sentence, so canonical-text containment does not
apply — but the words needed to name each type in these registers were found to already
be frozen, scattered across §4.10 (PERSON's `naam`/`नाम`, part of "frozen carrier
vocabulary"), §4.13 (the ROM_HI loanword table, covering ADDRESS/PHONE/EMAIL/PAN/UPI_ID/
BANK_ACCOUNT, plus its own prose naming AADHAAR's `Aadhaar`/`आधार` as intentionally
excluded from that table but still fixed), and §5.1/§16 (PERSON's Devanagari worked
example). None of these words were chosen for this resolution — they were assembled from
existing text into one table (`guidelines.md` §13.7, decision 41) and used as a substring
presence check, case-insensitive for the three Latin-carrier conditions (justified by
§4.14's own frozen "all-lowercase" `INFORMAL_HINGLISH` feature), exact for the two
Devanagari-carrier conditions.

**Verification, not assumption:** ran the complete contract (§13.6's `EN` rule + this
entry's `IN_EN` and five-condition rules) against all 624 frozen records in
`data/generated/language_realizations.jsonl` — zero failures, before any of it was
written into `guidelines.md`.

**Explicitly not circular:** the label table's words are sourced from guidelines.md
content that predates and is independent of `generators/language/templates.py`'s
implementation (§4.10/§4.13 are both `v0.10`, before T08 existed). A generator bug pairing
the wrong label with a declared type — while still producing a well-formed sentence in
every other respect — would still be caught, because the check never consults the
generator's own type→template association, only the record's declared `type` and this
document's word list.

**Honest limit carried forward from OQ-036:** the contract cannot distinguish "value used
in the wrong role" from "value present, role never asserted" — both surface as the same
missing-label result. Resolving that would require sentence-structure parsing, which this
decision deliberately does not attempt.

`guidelines_version` bumped 0.12 → 0.13; logged in `annotation/CHANGELOG.md`; version
pointers updated in `PROJECT_SPEC.md` (header + §35), `configs/pilot.yaml`, and
`tests/fixtures/example.valid.json`. No dataset file was changed or regenerated.
`validators/semantic.py` was not created — this is a governance-only resolution, T10
implementation itself remains a separate, later step.

---

## OQ-038 — No baseline adapter calling-convention interface is frozen anywhere — **RESOLVED (PROJECT_SPEC.md v1.3)**

**Encountered:** T11 evaluation-layer design report, 2026-08-25.

**Record:** `PROJECT_SPEC.md` §20.2 froze the *prediction* a baseline produces; §19 names
which baselines exist (B1–B5) and which files they live in (§25); §24.3 describes a
single-input live-detector flow. Nothing anywhere states how an adapter is *called* —
one input at a time versus batch, a class versus a bare function, where
`system_name`/`system_version` live.

**Verification against candidate resolution 1 (the design report's own proposal):**
checked whether `predict(text) -> list[Prediction]` is *implied* by anything frozen, or
is new policy. Finding: **new policy** — §20.2/§24.3 constrain what a prediction
contains, never how one is produced; §24's single-input flow is consistent with, but
does not require, a single-input adapter method (a batch-only adapter would also be
consistent with it).

**Candidate resolutions (from the design report):**
1. A minimal `predict(text) -> list[Prediction]` interface, `system_name`/
   `system_version` as adapter attributes, batch/`variant_id` handling left to the
   harness.
2. No shared interface — one class per baseline, duck-typed by the harness.
3. A functional interface (`predict_fn: Callable[[str], list[Prediction]]`) registered
   per baseline rather than a class/attribute shape.

**Status:** RESOLVED, 2026-08-25 — candidate resolution 1 chosen as the minimum
defensible option: it is the smallest interface that satisfies §24.3's single-input flow
without presupposing batch specifics, and keeps `variant_id` at the batch level exactly
where §20.2 already put it, rather than pushing it into every adapter implementation.
See `PROJECT_SPEC.md` §20.7 (v1.3). **Freezes the interface shape only** — no
`Prediction`/`BaselineAdapter` class and no concrete adapter file was created; per
OQ-034, implementing any of them remains unauthorized under Pilot v0.1, unchanged by
this entry.

---

## OQ-039 — No persisted prediction-artifact format is specified — **RESOLVED (PROJECT_SPEC.md v1.3)**

**Encountered:** T11 evaluation-layer design report, 2026-08-25.

**Record:** `PROJECT_SPEC.md` §27: *"Every run records: `generator_version`,
`config_version`, `guidelines_version`, `seed`, `timestamp`... store outputs as
artefacts."* This sentence is not scoped to dataset-generation runs specifically — it
sits in a pipeline-wide "Reproducibility and versioning" section. Whether it extends to
evaluation runs, and if so in what file format, was never stated.

**Verification:** that evaluation-run outputs should be persisted **is** implied by
§27's already-general wording — treating this as a new policy point would be
over-cautious given the section names no narrower scope. The **file format** is
genuinely new — §27 does not name one.

**Candidate resolutions:**
1. JSONL, one file per `(system_name, system_version, dataset_version)` triple —
   matching this repository's one existing record-serialization convention (CLAUDE.md:
   "JSONL for all dataset records"; every dataset file already uses it).
2. In-memory only, never persisted — scores computed and discarded per run.
3. Persisted only on request via an explicit flag, not by default.

**Status:** RESOLVED, 2026-08-25 — candidate resolution 1 chosen: introducing a second
serialization format for one specific artifact type, when this repository has used
exactly one (JSONL) for every record-shaped artifact so far, would be unjustified
invention. See `PROJECT_SPEC.md` §20.8 (v1.3). **Freezes the artifact format only** — no
prediction file is generated by this entry; producing one requires running a baseline,
which remains unauthorized under Pilot v0.1 (OQ-034).

---

## OQ-040 — No destination is specified for a malformed-prediction rejection log — **RESOLVED (PROJECT_SPEC.md v1.3)**

**Encountered:** T11 evaluation-layer design report, 2026-08-25.

**Record:** `PROJECT_SPEC.md` §20.2: a malformed prediction is *"rejected and logged by
the harness — never silently dropped, never silently clipped."* `PROJECT_SPEC.md`
§15.1 defines `data/rejected/` as the existing rejection-log convention, but scopes it
explicitly: *"it reveals what the generator cannot produce"* — a dataset-construction
research artefact, not an evaluation-time one.

**Verification:** reusing `data/rejected/` for malformed predictions is **not**
implied by §15.1 — it would extend a mechanism past the exact purpose that section
states for it, conflating "what a generator cannot produce" with "what a detector
adapter got wrong," which are different research questions with different audiences.

**Candidate resolutions:**
1. Reuse `data/rejected/` with a new reason category.
2. A separate, evaluation-scoped location (e.g. an `evaluation/rejected/`-style path).
3. Log the rejection into the same per-run artifact §20.8 already establishes for valid
   predictions, tagged with an explicit rejection reason — no second location invented.

**Status:** RESOLVED, 2026-08-25 — candidate resolution 3 chosen as the minimum
addition: it reuses the persistence mechanism §20.8 just established rather than
inventing either a repurposed or a brand-new location. `data/rejected/` itself is
unchanged — still exclusively the dataset-generation rejection log `PROJECT_SPEC.md`
§15.1 already defines. See `PROJECT_SPEC.md` §20.9 (v1.3).

---

## OQ-041 — No output format is specified for the evaluation-report artifacts — **RESOLVED (PROJECT_SPEC.md v1.3), partially**

**Encountered:** T11 evaluation-layer design report, 2026-08-25.

**Record:** `PROJECT_SPEC.md` §25 names `benchmark/metrics.py`, `failure_analysis.py`,
`stats.py`, and a `reports/` directory, but never states what any of them produce.

**Verification:** genuinely unspecified — no section states a report format, and none
of §20/§21/§23's content implies one over another.

**Candidate resolutions:**
1. Structured JSON per experiment × baseline × condition, plus a Markdown summary for
   human reading (matching CLAUDE.md's "report numbers, not adjectives" discipline).
2. CSV tables only.
3. Both, JSON canonical and Markdown derived.

**Status:** RESOLVED, 2026-08-25, **narrower than any single candidate above** — the
machine-readable format is frozen (one JSON file per experiment × baseline, containing
exactly the already-frozen §20.4/§21/§23 quantities, no new metric invented); whether a
derived human-readable rendering is also produced is explicitly **left undecided**, on
the reasoning that deciding the canonical machine-readable format is sufficient to
unblock any future design work, and a presentation-layer choice does not need to be
frozen in the same decision. See `PROJECT_SPEC.md` §20.10 (v1.3). **Freezes a file
format, not a report** — no file matching it is generated by this entry;
`benchmark/metrics.py` was not created.

---

**Governance note common to OQ-038–041:** none of the four authorizes evaluation-layer
implementation. `PROJECT_SPEC.md` §20.11 (v1.3) states this explicitly, and
`tests/test_t11_evaluation_governance.py` verifies it directly — asserting no
`benchmark/`, `baselines/`, `training/`, `experiments/`, or `application/` file exists —
so OQ-034's finding (evaluation-layer implementation not authorized under Pilot v0.1)
remains intact and independently checked, not merely restated in prose.

---

## OQ-042 — The six frozen decoy classes have a meaning and one worked example each, not a deterministic generation grammar — **RESOLVED (v0.15): `HANDLE_SHAPE` constructively; `ORG_AS_PERSON` by deferral, not construction**

**Encountered:** T11 hard-negative design report, 2026-08-25.

**Record:** `guidelines.md` §13.3's complete evidentiary basis for all six classes:

| Class | Meaning | Example |
|---|---|---|
| `NUMERIC_SHAPE` | Digit string resembling phone/account/Aadhaar | order number `9876543210` |
| `ALNUM_SHAPE` | Alphanumeric resembling PAN | reference code `ABCDE1234G` |
| `NAME_AS_PLACE` | Person-like name used as locality | `Rahul Nagar is near the station.` |
| `HANDLE_SHAPE` | `x@y` where role is neither email nor UPI | a support ticket handle |
| `ORG_AS_PERSON` | Organisation name resembling a person | a firm named after a founder |
| `PARTIAL_PII` | Truncated/masked value no longer identifying | `XXXX XXXX 4321` |

That is the complete specification — one sentence and one example per class, never
elaborated into a rule precise enough to generate more than the one shown instance
deterministically.

**The gap, per class:**
- `NUMERIC_SHAPE` — which digit count(s)/leading-digit pattern(s) qualify as
  "resembling phone/account/Aadhaar"? T05 already froze exact digit grammars for
  PHONE (`^[6789][0-9]{9}$`), AADHAAR/BANK_ACCOUNT (12 digits) — does a decoy have to
  match one of these exactly (a true near-miss) or does any digit string count?
- `ALNUM_SHAPE` — must it match PAN's exact frozen structural grammar
  (`^[A-Z]{5}[0-9]{4}[A-Z]$`), or merely "look alphanumeric"?
- `NAME_AS_PLACE` — is there a frozen place-name-suffix vocabulary (`Nagar`, `Puram`,
  `Colony`, ...) to pair deterministically with T03's frozen PERSON given-name
  vocabulary, the way T07's transliteration table pairs with that same vocabulary for a
  different purpose? None exists.
- `HANDLE_SHAPE` — what benchmark-safe domain/handle grammar produces an `x@y` shape
  that is neither EMAIL's frozen grammar nor UPI_ID's? Unspecified.
- `ORG_AS_PERSON` — is there a frozen organisation-suffix vocabulary (`& Sons`,
  `Enterprises`, `Traders`, ...) analogous to the PERSON/ADDRESS vocabularies T03 froze?
  None exists.
- `PARTIAL_PII` — what masking convention (mask character, grouping, how many trailing
  digits survive) is frozen? The one example (`XXXX XXXX 4321`) implies a convention but
  states none.

**Why this matters:** this is the same shape of gap as OQ-004/005/006/008/009/010 (a
worked example was never treated as sufficient to hard-code a generator against,
without an explicit frozen grammar) — this project's own established precedent is to
stop at exactly this point, not infer a plausible-looking grammar from the one example
shown.

**Candidate resolutions:** analogous to the T03/T05 pattern — for each class, propose
2–3 concrete candidate grammars (e.g. `NUMERIC_SHAPE`: candidate A = digit strings
matching one of PHONE/AADHAAR/BANK_ACCOUNT's exact frozen regex but declared
non-identifying by context; candidate B = any digit run of configurable length, no
format constraint) and freeze one per class by explicit decision, the same way UPI_ID's
grammar was chosen from three candidates at OQ-006.

**Status:** RESOLVED (v0.14), 2026-08-25, **partially**. Four of six classes now have a
frozen construction rule (`guidelines.md` §13.8, decision 42), built entirely by reusing
already-frozen T05 structural formats (PHONE/AADHAAR/BANK_ACCOUNT/PAN) and T03's frozen
PERSON given-name vocabulary — verified against the actual source (`validators/
structural.py`'s regex constants, `generators/pii/person.py`'s `_GIVEN_NAMES` tuple),
not re-typed from memory. `NAME_AS_PLACE`'s `surface_type: "LOCATION"` is not a new
choice — `guidelines.md` §6 already states it explicitly for exactly this
("Rahul Nagar") example.

`HANDLE_SHAPE` and `ORG_AS_PERSON` remain **UNRESOLVED** — confirmed by a repository-wide
search that neither has any concrete worked value anywhere in `guidelines.md` or
`PROJECT_SPEC.md`, only the same one-line description already on file. Freezing a
grammar for either now would invent content with no textual anchor, which this
resolution declined to do rather than silently deciding. **Still blocks generation of
6 of the 20 hard-negative bases** (the `HANDLE_SHAPE` and `ORG_AS_PERSON` allocation from
OQ-043's quota).

**Repository-wide evidence audit performed, 2026-08-25 (no change to the finding
above):** searched every `.md`, `.json`, `.py`, and `.jsonl` file in the repository for
organisation-suffix vocabulary (`Enterprises`, `Traders`, `& Sons`, `Pvt.`, `Ltd.`,
`Corp.`, `Industries`, `founder`, `firm`) and handle/ticket vocabulary (`ticket`,
`handle`, `helpdesk`, `support desk`). Every match traced to either an unrelated
incidental substring (`corp.invalid` is an EMAIL domain component, not organisation
vocabulary) or an already-known UPI_ID "PSP handle" reference (§10.3/§10.4, about
payment-service-provider handles, not `HANDLE_SHAPE`'s support-ticket concept). No
`annotation/review_template.csv` exists yet to check either, though `PROJECT_SPEC.md`
§25 names it in the repository layout. **Confirmed: zero additional evidence exists
anywhere in the repository for either class beyond the one-line table entries already
on file.** The finding above is unchanged, now on a fully audited rather than
best-recollection basis.

**Second, deeper audit pass, 2026-08-25 (final governance audit) — one new candidate
found for `HANDLE_SHAPE`, still not adopted; `ORG_AS_PERSON` unchanged at zero
evidence.**

`generators/pii/email.py` freezes a concrete "x@y" construction pattern:
`_LOCAL_PART_WORDS` (10 lowercased given names) + a random digit suffix, `@`,
`_DOMAIN_LABELS = ("mail", "corp", "webmail", "inbox")`, then a reserved TLD. Verified
mechanically: an EMAIL-shaped local part paired with one of `_DOMAIN_LABELS` **with the
TLD dropped** (e.g. `rahul4521@corp`) fails both `validators/structural.py`'s
`_EMAIL_RE` (requires the `.test`/`.invalid`/`.example` suffix) and `_UPI_ID_RE`
(requires a 10-digit phone-shaped local part) — confirmed by direct regex evaluation,
not asserted. This is a genuinely "x@y where role is neither email nor UPI" value,
built entirely from already-frozen vocabulary.

**Why this is not treated as resolving the class anyway:** every other §13.8 rule
reuses an existing frozen grammar or vocabulary **unmodified** (PHONE/AADHAAR/PAN's
regexes used exactly as specified; `Nagar` and `_GIVEN_NAMES` used exactly as shown).
This candidate instead **modifies** an existing rule — it drops EMAIL's TLD, which
EMAIL's own docstring identifies as the entire safety mechanism ("This is the one PII
type in T03 with a fully specified, zero-ambiguity safety rule" — a rule this candidate
would deliberately not apply). Removing a safety-relevant requirement to manufacture a
new category is a construction decision no document states, even though every
ingredient is reused. It is recorded here as the strongest candidate found for
`HANDLE_SHAPE`, not as a resolution.

`ORG_AS_PERSON`: the same second pass (searching `organization`/`organisation`/
`corporate`/`company`/`username`/`account handle` across every file) found nothing
beyond the same one-line table entry and PAN's docstring explicitly declining to encode
real-PAN holder-category semantics (`generators/pii/pan.py`) — evidence *against*
inventing organisation semantics, not evidence for a construction rule. `ORG_AS_PERSON`
has strictly less to build from than `HANDLE_SHAPE`: no reusable construction pattern
of any kind exists anywhere in the repository.

**Final status for both, this audit (superseded below):** HUMAN DECISION REQUIRED. Not
resolved from repository evidence alone.

**Human decision, 2026-08-25.** Presented as a decision memo (three choices per class,
consequences stated, no choice applied), the user selected:

- **`HANDLE_SHAPE` → A (freeze the current candidate).** Frozen exactly as presented:
  EMAIL's `_LOCAL_PART_WORDS` + digit suffix, paired with an `_DOMAIN_LABELS` word,
  reserved TLD omitted. See `guidelines.md` §13.8 (decision 45, v0.15). Choices B (a
  wholly new invented grammar) and C (remove/defer this class) were presented and not
  selected.
- **`ORG_AS_PERSON` → C (remove/defer this class).** Not resolved constructively — no
  grammar was invented. Explicitly recorded as **deferred from Pilot v0.1**, not as
  "resolved": its 6-class taxonomy membership and original design intent are preserved
  (`guidelines.md` §13.8), but no base of this class is constructed in this pilot. Its
  3-base quota allocation is redistributed to `NUMERIC_SHAPE`/`ALNUM_SHAPE`/
  `NAME_AS_PLACE` (§13.9, decision 46) rather than left unfilled, so the 20-base pilot
  target is still met. Choices A (invent a minimal grammar) and B (partial reuse of T03
  family names + an invented suffix) were presented and not selected.

**Status distinction, as required:** this OQ is marked `RESOLVED` for both classes
because a decision was made for both — but "resolved" does not mean "constructed" for
`ORG_AS_PERSON`. The heading above states this explicitly rather than letting a bare
`RESOLVED` tag imply a grammar exists where none does. `guidelines_version` bumped
0.14 → 0.15; logged in `annotation/CHANGELOG.md`.

---

## OQ-043 — No per-decoy-class distribution/quota is frozen for the 20 hard-negative bases — **RESOLVED (v0.14)**

**Encountered:** T11 hard-negative design report, 2026-08-25.

**Record:** `PROJECT_SPEC.md` §31 ("T11 20 hard negatives with distractors (all 6 decoy
classes)") and §32 ("[ ] 20 hard-negative bases with distractors, all 6 decoy classes
present") both require all six classes to appear *somewhere* among the 20, but neither
states how many of each — unlike T04's explicit per-type quota table (§12.2: PERSON 12,
ADDRESS 12, ..., totaling exactly 100).

**The gap:** 20 does not divide evenly by 6 (20/6 = 3.33). Some classes must have a
different count than others, and nothing states which, or by what principle (equal-ish
distribution with remainder assigned how; weighted toward classes judged more likely to
cause real false positives; one-per-class-then-arbitrary-fill; etc.).

**Candidate resolutions:**
1. As even as possible: four classes at 3, two classes at 4 (or any specific assignment
   of the remainder), chosen without further justification, purely to hit 20.
2. Weight the distribution toward `NUMERIC_SHAPE`/`ALNUM_SHAPE` (the two classes most
   likely to actually fool a regex/structured-identifier baseline, per §19.1's own stated
   expectation that B1 will be strong on structured types) — more decoys where more
   confusion is hypothesized.
3. Treat "all 6 present" as the only hard requirement and leave the exact split as a
   generator implementation detail, not a frozen governance decision at all.

**Status:** RESOLVED (v0.14), 2026-08-25 — candidate resolution 1 chosen, refined: the
remainder is assigned to the first two classes in `guidelines.md` §13.3's own table
order (`NUMERIC_SHAPE`, `ALNUM_SHAPE`), a content-free tie-break rather than a claim
about which classes are more important, matching this document's existing pattern of
order-based determinism elsewhere (§4.12's per-base marker cycling, §20.3's `rank(g,p)`
tie-break). Final split: `NUMERIC_SHAPE` 4, `ALNUM_SHAPE` 4, `NAME_AS_PLACE` 3,
`HANDLE_SHAPE` 3, `ORG_AS_PERSON` 3, `PARTIAL_PII` 3 = 20. See `guidelines.md` §13.9
(decision 43). This quota is frozen independently of OQ-042's construction rules — the
`HANDLE_SHAPE`/`ORG_AS_PERSON` rows have an assigned count but, per OQ-042's partial
resolution, no way to generate it yet.

**Superseded in part, 2026-08-25:** following OQ-042's later resolution deferring
`ORG_AS_PERSON` from Pilot v0.1, this table's `ORG_AS_PERSON` row is redistributed —
`NUMERIC_SHAPE` 4→5, `ALNUM_SHAPE` 4→5, `NAME_AS_PLACE` 3→4, `ORG_AS_PERSON` 3→0 — by
the same table-order tie-break this entry already established, so the 20-base total is
unchanged. See `guidelines.md` §13.9 (v0.15) for the current table; this entry's
original reasoning and split are preserved above as the historical record of how the
quota was first derived.

---

## OQ-044 — No language-condition count is frozen for hard-negative derived records — **RESOLVED (v0.15)**

**Encountered:** T11 hard-negative design report, 2026-08-25.

**Record:** `PROJECT_SPEC.md` §12.2's pilot record-count table lists "Clean positive
variants | ~624" (exact, per §8.2's collapse-rule arithmetic: 24×7 + 76×6 = 624) and,
separately, "Hard-negative variants | ~60" — note the **`~`** on the hard-negative
figure specifically, where the positive-variant figure is stated as an exact, derived
number elsewhere in the same document. The production-scale table (§12.4) similarly
gives "~1,200 hard-negative" against an exact 4,000-base target, and the ratio between
these two approximate figures does not resolve to a clean per-base multiplier either.

**The gap:** nothing states whether hard-negative bases go through all seven language
realizations (matching T08's collapse rule), a subset of them, multiple distractor
placements at a single fixed language, or some other construction entirely. 60 / 20 = 3,
which is *consistent with* "3 of the 7 language conditions," but no rule says which
three, or confirms that reading over an entirely different one (e.g. multiple decoy
variants at one language).

**Why this matters:** this number directly determines both (a) how T11 should be
implemented (does it need its own T08-style language-realization step, and if so for
which subset of conditions?) and (b) the final derived-record count after T11 — which
is therefore **not currently determinable** from the frozen specification, only
approximately bounded by the "~60" estimate.

**Candidate resolutions:**
1. All seven language conditions, matching positives' own treatment exactly (no special
   case for hard negatives) — would yield 20 × 7 = 140 derived records, not ~60.
2. A specific three-condition subset (e.g. `EN`, `HINGLISH`, one Hindi condition) chosen
   to sample the linguistic-degradation axis cheaply without full multiplication —
   consistent with the "~60" estimate at exactly 20×3.
3. One language condition per hard-negative base (20 records total, not ~60), with the
   "~60" figure being a stale or since-revised estimate from an earlier planning pass —
   would require correcting §12.2's own text, not merely picking an interpretation of it.
4. **(Found during the OQ-042/043/045 governance turn, 2026-08-25.)** A hard-negative
   record has `pii: []` — no PII entity, therefore no PII *script* at all. The entire
   reason `HI_LATIN_PII`/`HI_DEVA_PII` are two distinct conditions (§4.2/§8.1) is PII
   script variation; for non-transliterable *positive* types, that variation is
   already collapsed to one record (§8.1's collapse rule). A hard negative satisfies
   the same precondition the collapse rule already exists for — arguably more
   completely, since it has no PII value of any kind, not merely a non-transliterable
   one. Extending the six-realization collapse count to hard negatives would give
   20 × 6 = 120, not ~60. This candidate is *architecturally* well-grounded (it reuses
   an existing rule's own stated rationale rather than inventing a new one) but is
   **not textually stated anywhere** — §8.1 is written in terms of PII-value
   transliterability, never in terms of "a base with no PII entities at all." Treating
   it as automatically implied would still be an interpretive extension, not a
   frozen rule, so it is recorded here as a fourth candidate, not adopted.
5. **(Found during this reconciliation pass, 2026-08-25.)** The "×3" implied by ~60/20
   need not be a *language* multiplier at all — it could equally be 3 distinct decoy
   sentence/placement variants per base at a single fixed language (`EN`, the reference
   condition, §20.1). Nothing rules this out, and nothing supports it either; it exists
   only to show the "~60 ⇒ 3 of 7 languages" reading is not the only way to reach that
   number, which weakens rather than strengthens candidate 2's specific claim.

**Reconciliation against the exact wording of §12.2, §8.1, and the seven-condition
table (2026-08-25):**

- `guidelines.md` §4.1 states the seven-realization split's *entire rationale* in terms
  of PII-value script choice: *"If a name silently becomes राहुल शर्मा, the PII value
  itself changed and base linkage breaks... script becomes a hidden confound."*
  `PROJECT_SPEC.md` §8's own table caption is explicit: *"The Hindi condition splits by
  PII script."* A hard-negative record has `pii: []` — no PII value, therefore no script
  to split by. This is why candidate 4 is well-grounded in *rationale*.
- But §8.1's actual rule is worded as a closed, named list — *"For the six
  non-transliterable **categories**"* — not "for any base with no transliterable PII
  value," and a hard negative belongs to none of the eight named categories at all, so
  the rule's literal scope does not include it either. Rationale and literal wording
  point the same direction but neither actually reaches all the way to hard negatives
  in so many words.
- `PROJECT_SPEC.md` §12.2's own text undercuts treating "~60" as a precise, reverse-
  engineerable target: the very next sentence after the record-count table reads
  *"The controlled unit is **100 bases**. Exact record count may vary,"* and within
  that same table the *adversarial* line is given as an exact figure with its
  derivation shown inline (*"Adversarial variants (20 × 5) | 100"*) while the
  hard-negative line gets neither — no shown derivation, and the same `~` prefix as
  clean-positive's figure, which was itself only an early planning estimate later
  **superseded by §8.2's dedicated, exact "Variant arithmetic" derivation**
  (24×7 + 76×6 = 624). No equivalent dedicated section fixing an exact hard-negative
  figure was ever written. Hard-negative's "~60" is still at the same rough-estimate
  stage positive's "~624" was at *before* §8.2 existed — it was simply never followed up.

**Status:** UNRESOLVED — the reconciliation strengthens the evidentiary record without
converging it. Three live readings remain, none uniquely determined by the frozen text:
7-condition full multiplication (140, no special-casing for hard negatives), 6-condition
collapse-rule extension (120, well-grounded in stated rationale but not literal rule
scope), and something consistent with the stale-looking "~60" estimate (whose own
document flags it as approximate and never gave it the exact-arithmetic treatment
positives eventually got). Per instruction, no candidate is chosen for convenience or
expected dataset size. **Blocks T11 derived-record generation** and blocks stating an
exact final dataset cardinality after T11. Does **not** block T11 base-instance
generation for the four decoy classes OQ-042 already resolved, which needs only
§13.8/§13.9, not this OQ.

**Reconciliation table, final governance audit, 2026-08-25:**

| Interpretation | Derivation | Supporting evidence | Contradicting evidence | Exact or approximate? | Status |
|---|---|---|---|---|---|
| 7-condition full multiplication | 20 × 7 = 140 | Positives get no special case at all; simplest rule ("hard negatives are records like any other, all seven conditions apply uniformly") | §4.1/§8's stated rationale for the split is PII-script variation, which a `pii: []` record has none of; gives 140, not ~60 | Exact, if adopted | Not uniquely supported |
| 6-condition collapse-rule extension | 20 × 6 = 120 | §4.1/§8's own rationale (PII-script variation) is absent for `pii: []`, the same precondition §8.1 already collapses on for non-transliterable *types* | §8.1's rule text is scoped to "the six non-transliterable **categories**" by name — a hard negative belongs to none of the eight named categories, so the literal rule does not reach it | Exact, if adopted | Not uniquely supported |
| ~60 as approximately correct | 20 × 3 (or some other non-language-based construction, e.g. 3 sentence variants at one fixed language) | It is the only number `PROJECT_SPEC.md` actually states | §12.2 itself disclaims the whole table ("exact record count may vary"); gives adversarial's neighboring line an exact, inline-derived figure ("20 × 5") while giving hard-negative neither a derivation nor that treatment; positives' own "~624" was later superseded by §8.2's dedicated exact arithmetic, and no equivalent section was ever written for hard negatives | Approximate, by the document's own framing | Not uniquely supported |

No row is uniquely supported by the frozen text; the middle row is the best-reasoned on
architecture, the bottom row is the only one with a stated number, and neither
consideration is decisive over the other under the instruction not to choose for
convenience. **Final status prior to human decision: HUMAN DECISION REQUIRED. Not
resolved from repository evidence alone.**

**Human decision, 2026-08-25.** Presented as a decision memo (Options A/7-condition,
B/6-condition collapse, C/~60, each with textual evidence, architectural rationale,
contradictions, and paper implications stated), the user selected **B — the
six-condition collapse extension**, 20 × 6 = 120 hard-negative derived records:
`EN`, `IN_EN`, `ROM_HI`, `HINGLISH`, `INFORMAL_HINGLISH`, and one collapsed Hindi
realization (`hi_variant_collapsed: true`, the existing schema field, generated
exactly once because a hard negative has no PII and therefore no PII-script
distinction to express). See `guidelines.md` §13.11 (decision 47, v0.15).

This is recorded as **a deliberate extension of §8.1's rationale to `HARD_NEGATIVE`,
not a claim that §8.1's text already covered it** — §13.11 itself states this
distinction explicitly, per instruction not to pretend the specification already said
this. Option A (140, full seven-condition treatment) and Option C (a construction
consistent with "~60") were presented with their own evidence and rejected, not merely
unselected — both left in the reconciliation table above as the record of what was
considered. `guidelines_version` bumped 0.14 → 0.15; logged in
`annotation/CHANGELOG.md`.

---

## OQ-045 — No `context` (C1–C4) value is frozen for hard-negative derived records — **RESOLVED (v0.14)**

**Encountered:** T11 hard-negative design report, 2026-08-25.

**Record:** `guidelines.md` §4.17 explicitly froze `context: "EXPLICIT"` for every T08
clean **positive** record, with a stated reason (T08's arithmetic only holds if context
is held constant per record, and every T08 carrier template is already written in the
explicit register). No equivalent freeze exists for hard-negative derived records.
`PROJECT_SPEC.md` §9.1 allocates C1–C4 "across each PII category's bases" — a hard
negative has no PII category at all (`pii: []`), so it is unclear whether that
allocation rule applies to it, does not apply at all, or applies to something else
(e.g. how ambiguously the *decoy* is presented, rather than how explicitly a PII type
is named, since there is no PII type to name).

**The gap:** whether every hard-negative record is `EXPLICIT` (mirroring T08's
positive-record freeze), whether hard negatives vary across C1–C4 the way §9.1
describes for positives, or whether a hard negative's `context` value means something
different altogether (there being no PII role to be explicit or implicit *about*) is not
stated anywhere.

**Candidate resolutions:**
1. `context: "EXPLICIT"` uniformly, by direct analogy to §4.17's positive-record freeze
   — simplest, and consistent with the one worked example (`NEG_007`'s "The order
   number is 9876543210." directly names what the decoy purports to be).
2. Vary `context` across hard negatives the same way §9.1 intends for positives,
   reinterpreting "PII category" loosely as "decoy category" for this purpose.
3. `context` is `NOT_APPLICABLE` or a new distinguished value for hard negatives,
   since the C1–C4 scale was defined in terms of PII-role explicitness that a decoy, by
   definition, never has.

**Status:** RESOLVED (v0.14), 2026-08-25 — candidate resolution 1 chosen: `context:
"EXPLICIT"` uniformly for every hard-negative derived record, by direct analogy to
decision 38's identical T08 freeze. Candidates 2 and 3 were rejected on inspection, not
merely passed over: candidate 2 (vary `context` across C1–C4 the way positives do)
would require reinterpreting "PII category" as "decoy category," a redefinition of
§9.1's own terms, not an application of them; candidate 3 (a new `NOT_APPLICABLE`-style
value) would require extending the `context` enum, which is out of scope for a
governance turn that is supposed to reuse existing structure, not add to it. See
`guidelines.md` §13.10 (decision 44).

---

## OQ-046 — No field exists to persist a hard-negative base's construction ground truth — **RESOLVED (v0.16)**

**Encountered:** T11 Phase 1 implementation audit, 2026-08-25 — before any generator
code was written, re-reading `schemas/base_instance.schema.json` against this turn's
own "empty `entities`, non-empty `distractors`" instructions surfaced a genuine
conflict, reported rather than silently resolved either way.

**Record:** `guidelines.md` §13.4 (decision 16) is explicit and absolute: distractor
information belongs to the derived record, never the base instance, and
`schemas/base_instance.schema.json` "does not, and must not, gain a `distractors`
property." `entities[]` was never a base-instance field for any `base_kind` either — it
is exclusively a derived-record (`schemas/example.schema.json`) concept. Both of these
remain true and unchanged by this entry.

**The gap:** for a `POSITIVE` base, `pii[]` is the structured, persisted field every
later derivation step reads. `base_kind == HARD_NEGATIVE` requires `pii == []`
(decision 16) — so nothing on the base instance carried forward *which* decoy_class,
value, `actual_role`, and `surface_type` a given hard-negative base was constructed
with. Without such a field, a later derived-record generator would have no
non-parsing way to know this, and this project has never treated `canonical_text` as a
parseable source of ground truth.

**Candidate resolutions:**
1. Persist construction metadata on the base instance, as a new optional field.
2. Re-derive it from `base_id` + RNG replay at derived-record-generation time, with no
   new field.

**Status:** RESOLVED, 2026-08-25, by explicit human decision — candidate 1 (PATH 1)
chosen; candidate 2 (RNG replay) explicitly rejected, because it would make
hard-negative derivation depend on exactly reproducing the base generator's RNG
sequence, a coupling no other `base_kind` has (T08 reads only `base.pii[]`, never
re-runs T04's generator — making hard negatives work differently for no reason but
avoiding one field was judged the worse inconsistency).

**What was frozen:** `hard_negative_decoy` — optional (absent from
`schemas/base_instance.schema.json`'s top-level `required` array, so the 100 existing
`POSITIVE` bases remain valid and byte-identical without it), object-or-null, exactly
four sub-fields (`decoy_class`, `value`, `surface_type`, `actual_role`) when populated.
`decoy_class`'s enum is duplicated to match `schemas/example.schema.json`'s exactly —
same cross-schema convention as `generator_version` (OQ-020), no cross-file `$ref`,
consistent with every other schema in this repository. The `POSITIVE`/`HARD_NEGATIVE`
presence relationship is enforced by a new function in `validators/base_kind.py`
(`check_base_kind_hard_negative_decoy_invariant`), not by an `if`/`then` in the schema —
JSON Schema 2020-12 could express that conditional; the reason it isn't used here is
architectural consistency with the base_kind/`pii` invariant's own precedent (decision
16: schema = structure only, cross-field logic = validators, no exceptions), not a
technical limitation. See `guidelines.md` §13.12 (decision 48, v0.16).

Neither `pii[]` staying empty nor `entities[]`/`distractors[]` staying
derived-record-only is reopened or changed by this entry. `guidelines_version` bumped
0.15 → 0.16; logged in `annotation/CHANGELOG.md`; version pointers updated in
`PROJECT_SPEC.md` (header + §35), `configs/pilot.yaml`, and
`tests/fixtures/example.valid.json`. The 100 existing `POSITIVE` base instances are
untouched — the new field is optional and none of them carry it.

---

## OQ-047 — No frozen Hindi/Hinglish vocabulary exists for hard-negative decoy carrier-text construction — **RESOLVED (v0.17)**

**Encountered:** T11 Phase 2 pre-implementation audit, 2026-08-25 — before writing any
derived-record generator code, re-reading `generators/language/templates.py` and
`realizations.py` against §13.11's six frozen realizations.

**Record:** `CARRIER_TEMPLATE_ROM_HI` and `CARRIER_TEMPLATE_DEVANAGARI`
(`generators/language/templates.py`) are dictionaries keyed **exclusively by the eight
PII types** (`PERSON`, `ADDRESS`, `PHONE`, `EMAIL`, `PAN`, `AADHAAR`, `UPI_ID`,
`BANK_ACCOUNT`). `realize_rom_hi(pii_type, base_pii_value)` and
`realize_hindi_carrier(pii_type, ...)` do a direct dictionary lookup on `pii_type`.
`realize_hinglish`/`realize_informal_hinglish` both build on top of `realize_rom_hi`'s
output. A hard-negative base has no `pii_type` at all (`pii: []`) — there is no key to
look up, and no entry exists for any decoy-class concept ("order", "reference"/"code",
"masked", "reach"/"contact"/"also") in either template dict, nor in §4.13's ROM_HI
loanword inventory or HINGLISH insertion inventory, nor in §4.14's informal-marker
categories. `EN` and `IN_EN` are unaffected — `realize_en` is a no-op and `IN_EN`'s
markers (§4.12) are generic wrap functions operating on any sentence, not keyed by PII
type — so 2 of the 6 frozen realizations are genuinely constructible; `ROM_HI`,
`HINGLISH`, `INFORMAL_HINGLISH`, and the collapsed Hindi realization (4 of 6) are not,
without inventing new vocabulary.

**Why this is not resolvable by analogy:** §13.8 froze one `canonical_text` (English)
template per constructible decoy class — it does not address Hindi/Hinglish carrier
construction at all. §13.11 froze the realization *count* (six, not seven) — it does
not freeze *content* for the five non-EN/IN_EN conditions either. Reusing the
*closest-matching* PII type's frozen template (e.g. PHONE's "mobile number" for
`NUMERIC_SHAPE`'s "order number") would misrepresent the decoy's own `actual_role` and
requires exactly the unauthorized analogy this audit was instructed not to make.

**Candidate resolutions:**
1. Freeze a minimal Hindi/Hinglish concept-word table for the five constructible decoy
   classes' own label concepts ("order", "reference"/"code", "masked", "contact"/
   "reach"/"also"), mirroring §4.13's existing loanword-table format, and a
   `canonical_text`-equivalent carrier template per class per condition — the same kind
   of decision §13.8 already made for `canonical_text`, extended to five more registers.
2. Scope §13.11's six realizations to `EN`/`IN_EN` only for hard negatives in this
   pilot (a narrower cardinality than currently frozen — would require reopening
   OQ-044's 120-record cardinality decision, not merely adding vocabulary).
3. Accept `EN`/`IN_EN` now, defer `ROM_HI`/`HINGLISH`/`INFORMAL_HINGLISH`/collapsed-Hindi
   generation until candidate 1 is resolved — a partial Phase 2, explicitly labeled
   incomplete rather than silently short of the frozen 120-record target.

**Status:** UNRESOLVED. **Blocks generation of 4 of the 6 frozen realizations for all
20 hard-negative bases** (80 of the frozen 120 target). No vocabulary was invented; no
derived hard-negative record was generated this turn.

**Second, candidate-by-candidate audit, 2026-08-25 (final governance investigation
before Phase 2 implementation) — status unchanged, findings refined.**

A repository-wide search (`guidelines.md`, `PROJECT_SPEC.md`, `docs/research/
construction_log.md`, every generator/validator source file) for hard-negative worked
examples, Hindi/romanized decoy vocabulary, and any PII-type-independent phrase
inventory found one new item: `guidelines.md` §11.2's worked example — *"Input: My
order reference is 123456789012. Result: NOT_TARGET_PII — logged as a distractor with
surface_type BANK_ACCOUNT"* — English-only, reinforcing §13.3's own "order number"
framing but adding no Hindi/Hinglish content. Classified: **existing worked example
(English only)**, not new evidence for the four blocked registers.

**Candidate A — generic hard-negative carrier vocabulary.** Not found as a general
inventory. But auditing each constructible class individually against the *already-
frozen* §4.10 core grammar (`mera`, `hai`) and §4.13 loanword table (`number`/`नंबर`,
`account`/`अकाउंट`, among others) surfaced an uneven picture, not a uniform "blocked" or
"resolved" answer:

- **`PARTIAL_PII`** (`canonical_text`: *"The account number is {value}."*): both content
  words this English sentence needs — "account" and "number" — are *already* frozen
  loanwords (§4.13). A ROM_HI sentence assembled from only these words and the
  already-frozen `mera`/`hai` grammar (`"mera account number {value} hai."`) uses zero
  new vocabulary.
- **`NUMERIC_SHAPE`** (*"The order number is {value}."*): "number" is frozen; "order" is
  not, anywhere.
- **`ALNUM_SHAPE`** (*"The reference code is {value}."*): neither "reference" nor "code"
  is frozen anywhere.
- **`NAME_AS_PLACE`** (*"{name} Nagar is near the station."*): "near" → `ke paas` is
  frozen (§7.2, ADDRESS positional prepositions); "station" is not frozen anywhere,
  under any spelling.
- **`HANDLE_SHAPE`** (*"You can also reach me at {value}."*): no frozen word for
  "reach"/"contact"/"also" exists, and — separately, fatally — the only frozen "x@y"
  register vocabulary is "email"/"ईमेल" (§4.13), which is out of bounds under the
  semantic constraint below.

**Why `PARTIAL_PII`'s near-complete case is still not treated as resolved:** every
*word* it would need is frozen, but the *sentence itself* — "mera account number X
hai" for a decoy — is not shown anywhere as a worked example, and no rule states
"assemble a decoy sentence from `mera` + matching §4.13 loanwords + `hai`" as a general
construction principle. That principle would be *my own inference*, not a reproduction
of something already shown — categorically different from how `NAME_AS_PLACE`'s
construction was resolved in §13.8 (which reused the *literal, already-shown*
combination "Rahul Nagar," not merely words that happened to be individually frozen).
Per this turn's explicit instruction not to convert a plausible phrase into policy
merely because it is linguistically reasonable, `PARTIAL_PII` is reported as the
**strongest candidate**, not adopted as resolved.

**Candidate B — reuse an existing PII carrier.** Explicitly rejected per the semantic
constraint for every class where it was considered. Concretely: `HANDLE_SHAPE`'s value
is x@y-shaped and EMAIL's frozen ROM_HI template ("mera email {value} hai.") is the one
existing x@y-register carrier — but §13.3 defines `HANDLE_SHAPE` precisely as "x@y
where role is neither email nor UPI," so asserting "mera email X hai" for it would
falsely claim the distractor *is* an email, contradicting its own `actual_role`
(`INTERNAL_HANDLE`) and `surface_type` (`EMAIL`, chosen exactly to describe what a
detector might mistake it for, not what it is). Rejected for the same reason for any
other class considered against a same-shaped PII carrier.

**Candidate C — mechanical lexical transformation of the English sentence.** No
general EN→Hindi/Hinglish translation or transformation system exists anywhere in this
repository — T07's transliteration table is explicitly narrow (PII-value tokens only,
guidelines.md §4.7), and T08's own realization functions are template lookups, not a
transformation engine. Rejected: assuming such a system exists is exactly what this
investigation was told not to do.

**Candidate D — freeze a new generic hard-negative language inventory.** The only path
that would fully close this gap. Not written into `guidelines.md` — reported here for
approval only:
- **Proposed vocabulary (new words needed):** "order" (`NUMERIC_SHAPE`), "reference"
  and/or "code" (`ALNUM_SHAPE`), "station" or an equivalent landmark noun
  (`NAME_AS_PLACE`), a non-email-implying word for "handle"/"contact" (`HANDLE_SHAPE`).
  `PARTIAL_PII` needs no new word (see Candidate A), only the assembly-principle
  question above.
- **Affected decoy classes:** all five constructible classes to varying degrees;
  `ORG_AS_PERSON` is out of scope (quota 0, deferred).
- **Proposed carrier structure:** extend §4.13's loanword-table format with a parallel
  "decoy-concept" table (English concept → romanized form → Devanagari form), and one
  `canonical_text`-equivalent template per class per condition, mirroring how §13.8
  froze the EN case.
- **Whether the same carrier can serve multiple classes:** partially — `account` and
  `number` already serve both `BANK_ACCOUNT` (positive) and the proposed `PARTIAL_PII`
  construction; a new "reference"/"code" word could plausibly serve `ALNUM_SHAPE` alone.
- **Whether construction preserves the distractor as non-PII:** yes, if and only if no
  proposed word/template asserts a real PII type's role (the exact test Candidate B
  failed for `HANDLE_SHAPE`) — this must be checked per class, not assumed.
- **Examples per decoy-class category** (illustrative only, not adopted):
  `NUMERIC_SHAPE`: "mera order number {value} hai." / "मेरा ऑर्डर नंबर {value} है।";
  `ALNUM_SHAPE`: "mera reference code {value} hai." / "मेरा रेफरेंस कोड {value} है।";
  `NAME_AS_PLACE`: "{name} Nagar station ke paas hai." / "{name} नगर स्टेशन के पास है।";
  `HANDLE_SHAPE`: no example proposed — no non-PII-implying concept word was found even
  as a candidate; `PARTIAL_PII`: "mera account number {value} hai." / "मेरा अकाउंट नंबर
  {value} है।" (zero new words, per Candidate A).
- **Why not derivable from existing frozen content:** four of five classes need at
  least one word with no frozen equivalent anywhere in this repository; the fifth
  (`PARTIAL_PII`) needs no new word but does need a new *general assembly principle*
  that is not itself stated anywhere.

**Candidate E — collapse conditions.** Not supported. `guidelines.md` §13.11 names
`ROM_HI`, `HINGLISH`, and `INFORMAL_HINGLISH` as three of the six frozen realizations
individually; nothing authorizes merging any of them for `HARD_NEGATIVE` bases the way
`HI_LATIN_PII`/`HI_DEVA_PII` are *explicitly* named as a collapsible pair (§8.1). Per
this turn's own instruction, this interpretation was not adopted absent that explicit
support.

**Status confirmed (at that point): HUMAN DECISION REQUIRED.** No candidate was
supported by existing evidence alone.

**Human decision, 2026-08-25.** Presented as the Candidate D proposal above (exact
vocabulary, affected classes, carrier structure, cross-class reuse, non-PII
preservation check, worked examples per class), the user approved it. Frozen as
`guidelines.md` §13.13 (decision 49, v0.17): four new concept words ("order,"
"reference code," "station," "contact") plus one new `ROM_HI`/Devanagari carrier
template per constructible class, explicitly labeled apart from the already-frozen
words they reuse (`mera`/`hai` §4.10, `number`/`account` §4.13, `ke paas` §7.2).
`HINGLISH`/`INFORMAL_HINGLISH` construction was confirmed (by direct execution against
a non-PII test sentence) to require no vocabulary beyond `ROM_HI`'s own, since
`generators/language/templates.py`'s `HINGLISH_PATTERNS` are pure, PII-type-independent
string operations.

This is recorded as **new policy explicitly frozen now**, not a formalization of
something already implicit — per instruction, no newly-selected word is described as
having been previously frozen. `PARTIAL_PII`'s case is recorded precisely: its two
words were already frozen, but the *sentence-assembly template* is frozen for the
first time by this entry, closing the exact gap the first audit pass identified
(reusing frozen words is not the same as the sentence itself being pre-existing).

`ORG_AS_PERSON` remains deferred (quota 0, unchanged); the six-realization count
(§13.11) is unchanged; no schema, validator, or generator file was created or modified
by this decision. `guidelines_version` bumped 0.16 → 0.17; logged in
`annotation/CHANGELOG.md`.

---

## OQ-048 — No frozen rule requires distractor-span validation, unlike entity-span validation — **UNRESOLVED**

**Encountered:** T11 Phase 2 pre-implementation audit, 2026-08-25.

**Record:** `schemas/example.schema.json`'s `distractors[]` requires `text`, `start`,
`end` per entry, structurally identical in shape to `entities[]`'s span fields. But
nowhere does `guidelines.md` or `PROJECT_SPEC.md` state that `record.text[start:end] ==
distractor.text` must hold, the way §4.4/§14.1 explicitly require it for
`entities[].realized_pii_value`. `validators/spans.py`'s `validate_record_span` checks
only `entities[]`; it has never checked `distractors[]`, for the same reason no
distractor existed to check before this phase.

**Why this is not silently assumed:** the two arrays look structurally parallel, but
"the schema allows it" is not the same as "the specification requires a validator to
check it." Assuming distractor-span validation is already part of T09's contract, and
extending `validators/spans.py` to enforce it, would be inventing a validator
requirement no governing document states.

**What is not blocked by this gap:** the hard-negative derived-record *generator*
itself (once OQ-047 unblocks it) can and should still emit `distractors[]` entries with
genuinely correct spans, computed via the same `find_occurrence` primitive
`generators/language/spans.py` already provides for entities — that is a generation-time
correctness property this project verifies in its own generator tests regardless of
whether a validator also re-checks it later, the same way `assert_dataset_valid` in
both `generators/base_instances.py` and `generators/hard_negatives.py` verify things
their own way. This OQ is only about whether `validators/spans.py`'s **formal contract**
should be extended, not about whether generated data should be correct.

**Candidate resolutions:**
1. Extend `validators/spans.py` to also check `record.text[d.start:d.end] ==
   d.text` for every `distractors[]` entry, mirroring the existing entity-span
   check — a natural, low-risk extension, but a new validator requirement, not a
   frozen one.
2. Leave distractor-span checking to each generator's own tests indefinitely, treating
   `validators/spans.py`'s scope as entities-only by design (T09's own docstring calls
   it "the span extractor + occurrence-aware validator" for PII, not decoys).
3. Freeze an explicit distractor-span validation requirement in `guidelines.md` (e.g.
   as part of §13.8/§13.3) before extending the validator, so the requirement and the
   implementation are both recorded, not just the implementation.

**Status:** UNRESOLVED. Does not block Phase 2 generation (the generator's own tests
independently verify distractor-span correctness for whatever it produces); does block
formally extending `validators/spans.py`'s contract without a decision.

**Second, sub-question-by-sub-question re-audit, 2026-08-25 (status confirmed
unchanged, on stronger evidence):**

- *Can T09's existing span contract be extended to distractors without a new policy
  decision?* No. Re-read `guidelines.md` §4.4 verbatim: *"The span validator asserts
  `text[start:end] == realized_pii_value`. It must not compare against
  `base_pii_value`."* This is written specifically in terms of `realized_pii_value` — a
  field that exists only on `entities[]` items. `distractors[]` items have no
  `realized_pii_value` field at all (their span-adjacent field is `text`). The rule is
  not phrased generically ("any span-bearing field"); it names one specific field.
- *Does the schema already make `{text, start, end}` authoritative enough?* No — the
  schema's own `$comment` states its scope directly: *"No cross-field logic is enforced
  here."* The presence of `text`/`start`/`end` as sibling properties does not, by the
  schema's own declared scope, imply any relationship between them.
- *Do guidelines.md §18 or PROJECT_SPEC.md §15.1 already establish the relevant
  rejection behavior?* No — both establish the rejection-reason *vocabulary* and the
  rejected-record *logging mechanism*, never the substantive question of when a
  distractor span should be considered mismatched in the first place. A reason code
  existing to *describe* a rejection is not the same as a rule requiring one.
- *Does a distractor span mismatch have an existing rejection reason that should be
  reused?* Yes — `SPAN_MISMATCH` fits and is already reused generically (this project's
  own T11 Phase 2 pre-audit turn already applied it to a non-entity case, "HARD_NEGATIVE
  record must not have any entities"). This answers *what to call it if implemented*,
  not *whether it must be implemented*.
- *Would adding distractor validation merely apply an existing invariant to another
  existing span-bearing field?* This is the crux, and re-examining `guidelines.md`
  §4.6 (indexing convention) confirms it does not: §4.6 fixes the offset *units*
  (Python code-point indices) project-wide — genuinely general — but says nothing about
  *matching* a span to a text field. The *matching* invariant exists, stated once, only
  for `entities[].realized_pii_value` (§4.4/§14.1). Generalizing it to `distractors[]`
  would be extending a specific rule by inference, not applying an already-general one.

**Confirmed: OQ-048 requires a genuinely new (if low-risk, natural) validator
requirement — it is not already implied.** Left unresolved, consistent with the first
audit; this pass exists to show the conclusion survives being checked against every
angle this turn specifically asked about, not merely repeated.

---

## OQ-049 — T12 Adversarial Variants Generation Specification — **RESOLVED (v0.18)**

**Encountered:** T12 adversarial variants design phase, 2026-08-27.

**Record:** `PROJECT_SPEC.md` §10 (perturbation families $A_1$–$A_5$) and §12.2 (20 selected
bases × 5 families = 100 records); `guidelines.md` §14 (adversarial variants) and §17
(worked example `PAN_001_HINGLISH_A1_01`).

**The gap:** While the high-level taxonomy ($A_1$–$A_5$) and span-offset invariants were
defined in `guidelines.md` §14, several concrete generation mechanics were unstated:
1. Which exact 20 bases of the 100 positive bases are selected across the 8 PII categories.
2. Which carrier language condition is used as the baseline for perturbation.
3. The exact deterministic transformation algorithm and parameters for each family $A_1$–$A_5$.
4. The exact `variant_id` format and difficulty metadata.

**Status:** RESOLVED, 2026-08-27, by explicit human decision following a 2-stage adversarial
methodology audit:
1. **Base Selection**: 20 positive bases fixed as the lowest permanent `base_id`s within each
   category (3 each for `PAN`, `AADHAAR`, `UPI_ID`, `BANK_ACCOUNT`; 2 each for `PERSON`,
   `ADDRESS`, `PHONE`, `EMAIL`).
2. **Carrier Baseline**: Standard English canonical sentence (`base.canonical_text`) for all
   100 records, isolating perturbation effects from code-mixing confounds ($E05$).
3. **Perturbation Algorithms**:
   - $A_1$ (SPACING): Single space intra-word, double space inter-word.
   - $A_2$ (PUNCTUATION): Fixed structural delimiters (`PAN` 5-4-1, `AADHAAR`/`BANK` 4-4-4,
     `PHONE` 5-5, `PERSON` hyphen, `EMAIL` local hyphen before digits `sneha-8298@...`,
     `UPI_ID` 5-5 local phone hyphen `99965-07527@...`, `ADDRESS` slash).
   - $A_3$ (LABEL_OBFUSCATION): Literal carrier prefix obfuscation (`My P.A.N. No.: `, etc.).
   - $A_4$ (INFORMAL_ABBREVIATION): Literal carrier prefix informal abbreviation (`pan no: `, etc.).
   - $A_5$ (CHARACTER_VARIATION): Casing for alphanumeric/text (`PAN`, `PERSON`, `ADDRESS`
     lowercase; `EMAIL`, `UPI_ID` uppercase); **M2 Single-Character OCR Substitution** for
     numeric types (`PHONE`, `AADHAAR`, `BANK_ACCOUNT`) using visual homoglyphs
     `{'0': 'O', '1': 'l', '5': 'S', '8': 'B'}` on the first matching digit.
4. **Metadata**: `variant_id = "{base_id}_EN_{family}_01"`, `difficulty: "ADVERSARIAL"`,
   `perturbation.severity: 1`.

See `guidelines.md` §14.5–§14.8 (decision 50, v0.18). Logged in `annotation/CHANGELOG.md`.
`guidelines_version` bumped 0.17 → 0.18.
