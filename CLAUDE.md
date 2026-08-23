# CLAUDE.md

> Read this file in full at the start of every session, before touching any code.

---

## 1. What this repository is

An **experimental research benchmark**, not a product.

We measure how existing PII detection systems degrade when the *same* Indian PII is
expressed under controlled linguistic, contextual, formatting, and adversarial variation
— then test whether limited Indian-specific adaptation recovers the loss.

The dataset is the instrument. If the instrument is inconsistent, every downstream
result is void. Treat generation and validation code with the care you would give to
measurement equipment, not to a feature.

---

## 2. Governing documents and authority order

```
1. annotation/guidelines.md   ← ground-truth contract. Highest authority on labels/spans.
2. PROJECT_SPEC.md            ← research design, scope, milestones, experiments.
3. configs/*.yaml             ← run parameters.
4. This file                  ← how you work.
```

Your own judgement ranks **below all four**.

---

## 3. Prime directive

> **Do not improve the research design.**

If you encounter something ambiguous, underspecified, inefficient, or apparently wrong
in `guidelines.md` or `PROJECT_SPEC.md`:

1. **Stop.**
2. Append the case to `annotation/open_questions.md` with the record, the rule that
   failed, and 2–3 candidate resolutions.
3. Report it and wait.

Do **not** pick the sensible option and continue. Do **not** "temporarily" work around
it. A quiet fix to a boundary rule silently invalidates every record generated before
and after it, and the damage is usually invisible until analysis.

Ambiguity is a finding, not an obstacle.

---

## 4. Current milestone

**Pilot v0.1 — exactly 100 base instances.**

Nothing beyond this is authorised.

### Explicitly forbidden right now

- Generating the 4,000-base production dataset
- Training or fine-tuning any model
- Building the API, web UI, or demo
- Adding PII categories beyond the eight in the spec
- Adding language conditions beyond the seven realizations in `guidelines.md` §4.2
- Calling any external service with real user data
- Downloading, scraping, or ingesting any real PII

---

## 5. Data policy — non-negotiable

- **No real PII.** No scraped names, numbers, addresses, chats, or documents.
- Every record carries `"synthetic": true`.
- Identifiers are **benchmark-safe**: format-conforming so detection difficulty is
  realistic, generated so as not to represent issued credentials. Draw from documented
  reserved/test ranges where they exist; otherwise synthetic-by-construction, never
  matched against any real record.
- Email domains restricted to `.test`, `.invalid`, `.example`.
- If a generated value is ever found to correspond to a real identifier: remove it,
  invalidate affected records, regenerate, log the incident.

---

## 6. How you work

**One task at a time.** Take the numbered task you were given. Complete it. Report.
Stop. Do not begin the next task because it seems obvious.

**Commit per task.** `git commit` at the end of each numbered task, message prefixed
with the task ID (`T04: generate 100 base instances`). Never amend or rebase away
history.

**Tests before scale.** Every generator, transformer, and validator ships with unit
tests in the same task. No test, no task completion.

**Never overwrite datasets silently.** Increment the version and write a new file.
`pilot_v0.1.jsonl`, `pilot_v0.2.jsonl`. Deleting or rewriting a generated dataset in
place is a build failure.

**Never delete rejected records.** They go to `data/rejected/` with reason, validator,
and generator version. The rejection log is itself a research artifact — it tells us
what the generator cannot produce.

**Report numbers, not adjectives.** "412 of 600 passed span validation; 188 failed,
171 of them `SPAN_MISMATCH` on Devanagari records" — not "mostly working."

---

## 7. Technical invariants

| Rule | Why |
|---|---|
| Python; JSONL for all dataset records | Tooling compatibility |
| Offsets are **Python Unicode code-point indices** (`str` slicing) | One convention everywhere; Devanagari breaks otherwise |
| Never resolve repeated entities with bare `str.find()` | Always returns the first match; use `occurrence_index` |
| Span validator asserts `text[start:end] == realized_pii_value` | Never compare against `base_pii_value` |
| Deterministic seed (42) for all non-LLM randomness | Reproducibility |
| Record `generator_version`, `guidelines_version`, `config_version`, `seed` on every record | Provenance |
| Split by `base_id` only | Variant-level splitting leaks |
| The leakage test **fails the build**, it does not warn | Silent leakage invalidates every result |

---

## 8. LLM usage boundary

An LLM may **generate or paraphrase natural language**, and may emit an advisory
`PASS` / `FAIL` / `UNCERTAIN` during semantic validation.

An LLM may **never**:

- decide a PII type
- decide a span boundary
- compute character offsets
- invent an identifier format
- accept a record into the benchmark

Ground truth originates from the structured generator and `guidelines.md`. LLM output is
validated against ground truth, never the reverse.

If an LLM is used in a run, record `model_name`, `prompt_version`, and generation
parameters.

---

## 9. Stop conditions

Halt and report immediately if:

- A `guidelines.md` rule does not cover a case you hit
- A validator's pass rate falls below the §67 quality gate
- You need a schema field that does not exist
- Two rules appear to conflict
- A task would require generating beyond 100 bases
- You are about to write a workaround you would not want in the final paper

Stopping early costs one message. Continuing on a bad assumption costs a regeneration.

---

## 10. Pilot quality gates (from PROJECT_SPEC.md §67)

Do not propose scaling to production until:

```
structural validity      >= 99%
exact span correctness   >= 98%
semantic correctness     >= 95%
language correctness     >= 90%
human naturalness        >= 85%
```

These are engineering acceptance gates for the generator. They are **not** scientific
results and must never be reported as such.

If a gate fails: diagnose, fix the generator, regenerate, revalidate. Do not drop the
failing records to clear the gate.
