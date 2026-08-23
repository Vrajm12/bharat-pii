# Open Questions

> Log of cases where `guidelines.md` or `PROJECT_SPEC.md` was ambiguous, underspecified,
> or internally inconsistent, encountered during implementation. Per `CLAUDE.md` §3: do
> not silently resolve these by picking the sensible option. Record the case, the rule
> that failed, and candidate resolutions, then continue only where the governing
> documents already define a resolution procedure (e.g. PROJECT_SPEC.md §0's
> "guidelines.md wins, logged here" rule); otherwise stop and wait.

---

## OQ-001 — `validation{}` object: 5 keys or 6?

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

**Status:** UNRESOLVED. Affects `validators/duplicates.py` (later task) and the
`data/rejected/` log schema. Needs a decision before T09/T10 (span/semantic/language
validators) are implemented, since those tasks will need to know whether `validators/`
writes a `duplicate` key into `validation{}` or handles duplicates out-of-band.

---

## OQ-002 — Do hard-negative bases use `base_instance.schema.json`?

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

**Status:** UNRESOLVED. Needed before T04 (generate 100 bases) and T11 (20 hard negatives
with distractors, all 6 decoy classes).
