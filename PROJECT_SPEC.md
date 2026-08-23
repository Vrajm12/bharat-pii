# Robust Indian PII Detection & De-identification
## Research Design, Benchmark, Model and Application Specification

> **Version:** 1.1
> **Status:** RESEARCH DESIGN / IMPLEMENTATION SPECIFICATION
> **Supersedes:** v1.0 (six language conditions; no C4 scoring protocol; no distractor schema)
> **Companion contract:** `annotation/guidelines.md` v0.1 — **higher authority on all label, span, script and type questions**
> **Data policy:** SYNTHETIC AND PUBLIC DATA ONLY. Real PII strictly prohibited.
> **Current milestone:** Pilot v0.1 — 100 base instances
> **Do NOT generate the 4,000-base production dataset yet.**

---

## 0. How to read this document

| Document | Authority over |
|---|---|
| `annotation/guidelines.md` | What counts as PII, span boundaries, types, script policy, ambiguity handling |
| `PROJECT_SPEC.md` (this file) | Research design, scope, dataset architecture, experiments, milestones |
| `configs/*.yaml` | Run parameters |
| `CLAUDE.md` | How the implementation is carried out |

Where this document and `guidelines.md` appear to conflict, **guidelines.md wins** and the
conflict is logged in `annotation/open_questions.md`.

### Changes in v1.1

1. Six language conditions become **seven realizations** — Hindi splits by PII script
   (guidelines §4). Adds experiment **E02b**.
2. Context level **C4 UNLABELLED** gets a defined scoring protocol and is separated from
   headline metrics (guidelines §12.4).
3. Record schema gains `base_pii_value` / `realized_pii_value`, `pii_script`,
   `occurrence_index`, `distractors[]`, `perturbation.target`, `guidelines_version`.
4. Identifier policy reworded: **benchmark-safe synthetic**, not "provably invalid".
5. Adds **statistical treatment** requirements (§23) — previously absent.
6. Adds **Presidio configuration disclosure** requirement (§20.3).
7. Adds **real-carrier-text anchor** for the naturalistic test set (§19.3).
8. Adds **publication mapping and fallback** (§32).
9. Adds **experiment priority tiers** (§24.3) for scope control.

---

# PART I — RESEARCH POSITION

## 1. Executive summary

### 1.1 What this project is

A controlled measurement study of **PII detector robustness under Indian linguistic
variation**, followed by a targeted adaptation experiment, followed by a practical
de-identification tool built on whichever approach the measurements favour.

### 1.2 What this project is not

> "Build an Indian PII detector."

That has been done. So has Indian PII dataset construction, multilingual PII annotation
at scale, code-mixed de-identification, and few-shot cross-lingual transfer. The
contribution is not the artefact — it is the **controlled comparison**.

### 1.3 The contribution, stated precisely

> Take the same synthetic Indian PII, express it under systematically varied linguistic,
> script, contextual, formatting and adversarial conditions, hold everything else
> constant, and measure how existing detection systems degrade. Categorise the failures.
> Then test whether limited Indian-specific adaptation recovers the loss, and how much
> data that takes.

The dataset is an **instrument**. Its value is its control, not its size.

---

## 2. What the literature already establishes

Eight papers were reviewed. Collectively they establish that the following already exist:

| Established | Evidence |
|---|---|
| General PII detection and benchmarking | PII-Bench (2,842 samples, 7 categories / 55 subcategories, human ceiling, synthetic→real validation) |
| Large Indian-language NER resources | HiNER (~108K Hindi sentences, 11 entity types) |
| Indian PII detection systems | Sheela et al. (Aadhaar/PAN/voter ID regex + spaCy + BERT hybrid) |
| Synthetic Indian PII datasets | Sheela et al. (2,000+ instances) |
| India in multilingual PII evaluation | *Unmasking* (17K semi-synthetic, 16 PII types, India/UK/US, UPI-vs-email confusion identified) |
| Hindi-India PII annotation at scale | Centific (13 locales, ~336 locale-specific types, 40K+ samples, Aadhaar→NATIONAL_ID, PAN→TAX_NUMBER) |
| Code-mixed de-identification | Amin et al. (Spanish–Catalan clinical, BioNLP 2022) |
| Few-shot cross-lingual transfer for de-identification | Amin et al. (zero-shot 73.7 → 91.2 F1; ~50 target examples ≈ hundreds from scratch) |
| Failure of existing systems under stress | *Unmasking*: 28% of predictions detected nothing; **67% detected the entity but misclassified its type**; Presidio misclassification exceeding 90% in contextual/adversarial conditions |

### 2.1 Forbidden novelty claims

Never write, in the report, the paper, or the README:

- "Nobody has built an Indian PII detector."
- "No Indian PII dataset exists."
- "Nobody has studied multilingual PII."
- "Nobody has studied code-mixed de-identification."
- "Few-shot de-identification is novel."
- "PAN/Aadhaar detection has never been studied."
- "Synthetic PII generation is novel."

Each is refuted by a paper already in the review. Making any of them is the fastest route
to rejection.

---

## 3. Research gap

The components exist individually. No reviewed study combines all of the following in one
controlled framework:

1. Indian-specific fine-grained PII types
2. Hindi–English code-mixing
3. Romanized Hindi
4. **Script isolated as a variable** (same name, Latin vs Devanagari)
5. Informal Indian conversational register
6. Contextual / implicit / unlabelled PII
7. Controlled formatting variation
8. Adversarial perturbation
9. Independently constructed, frozen evaluation
10. Subsequent Indian-specific few-shot adaptation measured as recovery

### 3.1 Gap statement — use this wording

> Existing research has separately investigated Indian PII detection, multilingual PII
> dataset construction, code-mixed de-identification, few-shot cross-lingual transfer and
> adversarial robustness. However, the robustness of PII detection systems under
> **controlled** Indian linguistic variation — Hindi–English code-mixing, Romanized Hindi,
> script variation, informal formatting, contextual ambiguity and adversarial
> perturbation — remains **insufficiently characterized** through an independently
> constructed, fine-grained evaluation framework.

Use **"insufficiently characterized"**. Never "never studied" — an absolute negative
cannot be proven and one counter-citation destroys it.

---

## 4. Research questions

### RQ1 — Primary

> How does the performance of existing PII detection systems change when identical Indian
> PII is expressed under different linguistic, script, contextual, formatting and
> adversarial conditions?

### RQ2 — Linguistic degradation

Which realizations cause the largest degradation, across
`EN` → `IN_EN` → `HI_LATIN_PII` → `HI_DEVA_PII` → `ROM_HI` → `HINGLISH` → `INFORMAL_HINGLISH`?

### RQ2b — Script isolation *(new in v1.1)*

Holding language and content constant, how much degradation is attributable to **script**
alone? Compares `HI_LATIN_PII` against `HI_DEVA_PII` for PERSON and ADDRESS.

### RQ3 — PII-category difficulty

Do context-heavy categories (PERSON, ADDRESS) and structured identifiers (PHONE, EMAIL,
PAN, AADHAAR, UPI_ID, BANK_ACCOUNT) show different robustness profiles?

### RQ4 — Context

Does implicit PII produce lower performance than explicitly labelled PII, across C1 → C3?

### RQ4b — Ambiguity behaviour *(new in v1.1)*

Under C4 UNLABELLED, do systems abstain or guess? How does the guess distribution differ
across systems and across languages?

### RQ5 — Failure modes

What is the dominant failure mode — missing PII, wrong span, or wrong type? *(Unmasking's
67% misclassification figure suggests type, not detection. Our benchmark can test that
independently.)*

### RQ6 — Few-shot recovery

Can limited Indian-specific training data recover performance lost under Indian
linguistic variation, and how many examples per category are required?

### RQ7 — Cross-condition generalization *(optional)*

Does training on one Indian linguistic condition transfer to others?

---

## 5. Hypotheses

All hypotheses. All falsifiable. **Never manufacture results to match them.**

**H1 — Linguistic degradation.** Performance decreases moving from standard English
toward code-mixed and Romanized forms.
Expected ordering: `EN` > `IN_EN` > `HI_LATIN_PII` > `ROM_HI` > `HINGLISH` > `INFORMAL_HINGLISH`.

**H1b — Script effect.** `HI_DEVA_PII` shows greater degradation than `HI_LATIN_PII` for
PERSON and ADDRESS, and no difference for the six identifier categories.

**H2 — Category difference.** PERSON and ADDRESS degrade more than PAN, AADHAAR, PHONE.

**H3 — Context difficulty.** C3 IMPLICIT is harder than C1 EXPLICIT.

**H4 — Adaptation.** Limited Indian-specific fine-tuning significantly improves
performance on Indian linguistic variants.

**H5 — Generalization** *(secondary, droppable)*. Gains from one condition do not
transfer equally to all others.

**H6 — Misclassification dominance** *(new in v1.1)*. Type errors outnumber detection
misses, replicating *Unmasking*'s finding on an India-controlled benchmark.

---

## 6. Core scientific principle

> **Same PII. Different representation. Everything else held constant.**

```
                        BASE INSTANCE
                              |
                   PII = synthetic value
                   type, role, scenario fixed
                              |
        +---------+-----------+-----------+---------+
        |         |           |           |         |
       EN      IN_EN    HI_LATIN_PII   ROM_HI   HINGLISH ...
        |         |           |           |         |
        +---------+-----------+-----------+---------+
                              |
                    SAME GROUND TRUTH
                 (base_pii_value invariant)
```

Variants are **derived from the canonical form**, never independently generated. Asking an
LLM separately for "an English PAN sentence" and "a Hinglish PAN sentence" produces two
uncontrolled samples and destroys the comparison.

What may change across variants: surface wording, script of transliterable entities,
formatting. What must not: PII identity, PII type, semantic role, scenario, base linkage.

---

# PART II — BENCHMARK DESIGN

## 7. PII taxonomy — exactly eight categories

| Type | Class | Research role |
|---|---|---|
| `PERSON` | Context-heavy | Indian name morphology; script-transliterable |
| `ADDRESS` | Context-heavy | Indian address structure, landmark-relative; script-transliterable |
| `PHONE` | Structured | Indian formatting variation |
| `EMAIL` | Structured | Baseline; UPI confusion partner |
| `PAN` | Structured, India-specific | Alphanumeric identifier |
| `AADHAAR` | Structured, India-specific | National-ID category |
| `UPI_ID` | Structured, India-specific | **Shape-collides with EMAIL** — context-dependent typing |
| `BANK_ACCOUNT` | Structured | Numeric; collides with order/reference numbers |

Depth over breadth. Do **not** expand to 20–30 categories. `PASSPORT`,
`DRIVING_LICENSE`, `VEHICLE_REGISTRATION`, `IFSC` are deferred and require explicit
approval.

---

## 8. Language realizations — seven

Per `guidelines.md` §4.2. The Hindi condition splits by PII script.

| Code | Condition | Carrier script | PERSON/ADDRESS script |
|---|---|---|---|
| `EN` | Standard English | Latin | Latin |
| `IN_EN` | Indian English | Latin | Latin |
| `HI_LATIN_PII` | Hindi, Latin-script PII | Devanagari | Latin |
| `HI_DEVA_PII` | Hindi, Devanagari PII | Devanagari | Devanagari |
| `ROM_HI` | Romanized Hindi | Latin | Latin |
| `HINGLISH` | Hindi–English code-mixed | Latin | Latin |
| `INFORMAL_HINGLISH` | WhatsApp-register Hinglish | Latin | Latin |

### 8.1 Collapse rule

For the six non-transliterable categories, `HI_LATIN_PII` and `HI_DEVA_PII` are identical.
Generate **one** record and set `hi_variant_collapsed: true`.

| Categories | Realizations generated |
|---|---|
| PERSON, ADDRESS | 7 |
| PHONE, EMAIL, PAN, AADHAAR, UPI_ID, BANK_ACCOUNT | 6 |

### 8.2 Variant arithmetic

**Pilot (100 bases: 24 transliterable, 76 non-transliterable)**

```
24 × 7 = 168
76 × 6 = 456
        -----
        624 clean positive variants
```

**Production (4,000 bases: 1,000 transliterable, 3,000 non-transliterable)**

```
1,000 × 7 =  7,000
3,000 × 6 = 18,000
            ------
            25,000 clean positive variants
```

### 8.3 Transliteration

Devanagari forms come from a **deterministic transliteration table**, never an LLM, and
are fixed at base-instance creation. The same name must transliterate identically
everywhere. Table version recorded in `generator_version`.

---

## 9. Context levels — four

| Code | Level | Example |
|---|---|---|
| `C1` | EXPLICIT | `My PAN number is X.` |
| `C2` | SEMI_EXPLICIT | `PAN: X` |
| `C3` | IMPLICIT | `I need to submit X for tax verification.` |
| `C4` | UNLABELLED | `X` |

### 9.1 Allocation

| Context | Pilot (per 12-base cat / 13-base cat) | Production (per 500-base cat) |
|---|---|---|
| C1 | 6 / 6 | 200 |
| C2 | 3 / 3 | 125 |
| C3 | 2 / 3 | 100 |
| C4 | 1 / 1 | 75 |

Balanced and documented, never randomised blindly.

### 9.2 C4 scoring protocol — mandatory separation

Per `guidelines.md` §12.4. C4 has ground truth (the base declares the role) but is not
human-verifiable from text alone.

- **Human review** validates span and naturalness only. Type is `N-A`.
- **Scoring** is a separate track. C4 is **never pooled** into headline recall/F1.
- A wrong type under C4 is **not** counted as a type error in main results.
- C4 is reported as an **ambiguity probe** (RQ4b): abstention vs confident-wrong guessing
  is a real behavioural distinction and C4 is the only condition that exposes it.
- A base instance with no declared semantic role is rejected as `MISSING_SEMANTIC_ROLE`,
  not marked `UNCERTAIN`.

---

## 10. Perturbation families — five

Per `guidelines.md` §14.

| Code | Family | Target | Span moves? |
|---|---|---|---|
| `A1` | SPACING | VALUE | **Yes** |
| `A2` | PUNCTUATION | VALUE | **Yes** |
| `A3` | LABEL_OBFUSCATION | LABEL | No |
| `A4` | INFORMAL_ABBREVIATION | LABEL | No |
| `A5` | CHARACTER_VARIATION | VALUE | **Yes** |

`perturbation.target` must be consistent with the family, and tells the span validator
whether to expect `realized_pii_value == base_pii_value`.

**Recoverability ceiling.** If a perturbation makes the PII unrecognisable to a competent
human reader, mark `INVALID_ADVERSARIAL` and exclude from the positive benchmark. Never
force an annotation to preserve dataset size.

---

## 11. Data policy

**No real PII.** No scraped names, numbers, addresses, chats, screenshots, credentials,
customer support logs, or private messages.

**Permitted:** synthetic names, addresses, identifiers; generated conversations; publicly
documented formats; public non-sensitive linguistic resources where licensing permits.

**Every record carries `"synthetic": true`.**

### 11.1 Identifier safety — benchmark-safe synthetic

Identifier values are **structurally conforming** so detection difficulty is realistic,
and **generated so as not to represent issued credentials**. Where a format has publicly
documented reserved, test, or never-issued ranges, generators draw from those ranges.
Where none is documented, values are synthetic-by-construction and are never checked
against, derived from, or matched to any real record.

Do **not** claim values are "provably invalid" — for some formats we can only guarantee
synthetic generation, not mathematical impossibility of collision. Overclaiming here is
worse than the honest statement.

The benchmark does **not** validate whether an identifier was issued. Out of scope, and
the README must say so.

Email domains restricted to `.test`, `.invalid`, `.example`.

### 11.2 Incident procedure

If a generated value is found to correspond to real PII: remove it, invalidate every
affected record, regenerate, log the incident internally.

---

## 12. Dataset architecture

### 12.1 The base instance

A base instance is **not a sentence**. It is a semantic record: the synthetic PII, its
declared type and role, the person/scenario context, and one canonical English sentence.
Everything else is derived.

```json
{
  "base_id": "PAN_001",
  "pii": [
    { "type": "PAN", "base_pii_value": "<SYNTHETIC>", "semantic_role": "TAX_IDENTIFIER" }
  ],
  "person_context": { "name": "<SYNTHETIC_NAME>", "name_deva": "<TRANSLITERATED>" },
  "scenario": { "domain": "account_verification", "purpose": "identity_verification" },
  "address_structure": null,
  "canonical_text": "My PAN number is <SYNTHETIC>.",
  "synthetic": true
}
```

### 12.2 Pilot v0.1 — current milestone

**Exactly 100 positive base instances.**

| Type | Bases |
|---|---|
| PERSON | 12 |
| ADDRESS | 12 |
| PHONE | 12 |
| EMAIL | 12 |
| PAN | 13 |
| AADHAAR | 13 |
| UPI_ID | 13 |
| BANK_ACCOUNT | 13 |
| **Total** | **100** |

IDs are permanent (`PERSON_001`, `PAN_001`, …) and **never reused**.

Plus, separately:

- **20 multi-PII bases** (12 × 2 entities, 6 × 3, 2 × 4)
- **20 hard-negative bases** (not part of the 100)
- **20 of the 100** selected for adversarial perturbation

| Component | Records |
|---|---|
| Clean positive variants | ~624 |
| Hard-negative variants | ~60 |
| Adversarial variants (20 × 5) | 100 |
| **Pilot total** | **~784** |

The controlled unit is **100 bases**. Exact record count may vary.

### 12.3 Scenario distribution (pilot)

| Domain | Bases |
|---|---|
| Banking / payments | 25 |
| Customer support | 20 |
| Delivery / address | 15 |
| Account verification | 15 |
| Telecom | 10 |
| Employment / HR | 5 |
| Healthcare administration | 5 |
| General conversation | 5 |

Synthetic scenarios only.

### 12.4 Production target

4,000 bases (8 × 500) → ~25,000 clean + ~2,000 adversarial + ~1,200 hard-negative
≈ **28,200 records**.

**4,000 is a budget, not a law.** If the pilot shows PAN and AADHAAR are trivial for every
system while PERSON and ADDRESS are hard, reallocate toward the hard categories. The pilot
determines the final distribution.

---

## 13. Record schema

Defined in `annotation/guidelines.md` §17. Reproduced here only as a field inventory —
**guidelines.md is authoritative**.

`base_id` · `variant_id` · `text` · `entities[]` · `distractors[]` · `language` ·
`carrier_script` · `context` · `domain` · `perturbation{family,type,severity,target}` ·
`difficulty` · `address_structure` · `hi_variant_collapsed` · `synthetic` ·
`generator_version` · `guidelines_version` · `template_id` · `seed` · `validation{}` ·
`validation_status` · `review_status` · `split`

Each entity: `type` · `base_pii_value` · `realized_pii_value` · `pii_script` · `start` ·
`end` · `occurrence_index`

Each distractor: `text` · `start` · `end` · `surface_type` · `actual_role` · `decoy_class`

`decoy_class` ∈ {`NUMERIC_SHAPE`, `ALNUM_SHAPE`, `NAME_AS_PLACE`, `HANDLE_SHAPE`,
`ORG_AS_PERSON`, `PARTIAL_PII`}.

### 13.1 Difficulty derivation

Derived from metadata, never hand-assigned:

| Level | Condition |
|---|---|
| `EASY` | C1 + clean + `EN`/`IN_EN` |
| `MEDIUM` | code-mixed OR C2/C3 OR formatting variation |
| `HARD` | multi-PII + code-mixing + distractor present |
| `ADVERSARIAL` | any perturbation applied |

---

## 14. Generation pipeline

```
 1. Generate synthetic PII (benchmark-safe)
 2. Build base semantic record (+ transliteration)
 3. Canonical English sentence
 4. Verify PII occurs in canonical text
 5. Derive language realizations (6 or 7)
 6. Apply context level
 7. Apply adversarial perturbation (selected bases)
 8. Recompute exact spans, occurrence-indexed
 9. Structural validation
10. Span validation
11. Semantic validation
12. Language + script validation
13. Duplicate detection
14. Human review
15. ACCEPT / REJECT
```

### 14.1 Span computation — hard rules

- Offsets are **Python Unicode code-point indices** (`str` slicing). Not bytes, not
  UTF-16, not graphemes. One convention everywhere.
- Validator asserts `text[start:end] == realized_pii_value`. **Never** compare against
  `base_pii_value`.
- Repeated values resolve by walking all matches in order and selecting
  `occurrence_index`. **Never** use bare `str.find()`.
- Never obtain offsets from an LLM.

### 14.2 LLM boundary

**May:** generate and paraphrase natural language; produce Hinglish register variation;
emit advisory `PASS`/`FAIL`/`UNCERTAIN` in semantic validation.

**May never:** decide a PII type; decide a span; compute offsets; invent an identifier
format; accept a record into the benchmark.

Record `model_name`, `prompt_version`, generation parameters for any LLM-assisted run.

---

## 15. Validation layers

| Layer | Checks |
|---|---|
| 1 Structural | Value conforms to its synthetic format schema |
| 2 Span | `text[start:end]` exactly equals `realized_pii_value`; occurrence index correct |
| 3 Semantic | Sentence uses the value in the declared role |
| 4 Language / script | Realization matches its declared condition; `pii_script` correct |
| 5 Duplicate | Exact, normalized, and near-duplicate — scoped so legitimate controlled variants survive |
| 6 Human | Span, type, language, script, meaning, naturalness, recoverability |

Statuses: `PASS` · `FAIL` · `UNCERTAIN` · `NOT_APPLICABLE`.
`UNCERTAIN` always goes to human adjudication.

### 15.1 Rejection log

Rejected records go to `data/rejected/` with reason, validator, and generator version.
**Never delete silently.** The rejection log is a research artefact: it reveals what the
generator cannot produce, which is itself a finding about synthetic Hinglish generation.

Reasons: `INVALID_PII_FORMAT` · `PII_NOT_FOUND` · `SPAN_MISMATCH` · `OCCURRENCE_MISMATCH` ·
`SEMANTIC_MISMATCH` · `ROLE_UNSUPPORTED_BY_TEXT` · `MISSING_SEMANTIC_ROLE` ·
`LANGUAGE_MISMATCH` · `SCRIPT_MISMATCH` · `NATURALNESS_FAILURE` · `INVALID_ADVERSARIAL` ·
`DUPLICATE` · `UNSAFE_REAL_PII_RISK`

---

## 16. Pilot quality gates

Proceed to production **only** if:

```
structural validity     >= 99%
exact span correctness  >= 98%
semantic correctness    >= 95%
language/script correct >= 90%
human naturalness       >= 85%
```

These are **engineering acceptance gates for the generator**. They are not scientific
findings and must never be reported as such.

On failure: diagnose → fix generator → regenerate → revalidate. **Never drop failing
records to clear a gate.**

### 16.1 Inter-annotator agreement

A sampled subset is reviewed independently by two reviewers. Report Cohen's κ. Adjudicate
disagreements; never silently pick one reviewer. A disagreement that exposes a missing
rule triggers a `guidelines.md` version increment.

---

## 17. Splits and leakage

| Split | Bases | % |
|---|---|---|
| Train | 2,400 | 60 |
| Validation | 800 | 20 |
| Test | 800 | 20 |

**Split by `base_id` only.** Every variant of a base — every language, every context,
every perturbation, every paraphrase — inherits its base's split.

### 17.1 Leakage test

```
for each base_id:
    assert len(set(splits_of_all_variants(base_id))) == 1
```

This test **fails the build**. It does not warn. Silent leakage invalidates every result
in the project.

### 17.2 Frozen test set

The test set is frozen **before** model development. The following loop is prohibited:

```
train → observe failure → add similar example to training → retrain
```

---

## 18. Test set structure

| Set | Bases | Purpose |
|---|---|---|
| Test A — Controlled | ~600 | Isolate one variable at a time |
| Test B — Naturalistic | ~200 | Do controlled findings survive realistic text? |

### 18.1 Test B construction

Independently generated after the controlled schema is frozen. Must avoid the controlled
templates (`My PAN is X.`). Should resemble support chats, account-update requests,
complaints, payment queries, delivery messages. All content synthetic.

### 18.2 Real-carrier anchor *(new in v1.1)*

A synthetic benchmark validated only against itself is a weak defence. PII-Bench answered
this with `PII-Real` and rank correlation.

Our equivalent, without touching real PII:

> Take **carrier text** from public code-mixed corpora where licensing permits
> (e.g. LinCE, GLUECoS, public Hinglish code-mixed datasets) and inject **synthetic**
> PII into it.

Real linguistic distribution + synthetic identifiers = no real PII, but genuine Hinglish
that our generator did not author. Report **rank correlation** between system rankings on
the synthetic benchmark and on the real-carrier set. High correlation is the strongest
single defence of the benchmark's validity.

This is a **Tier 2** deliverable (§24.3) — highly desirable, droppable under time
pressure.

---

# PART III — EXPERIMENTS

## 19. Baselines

| ID | System | Role |
|---|---|---|
| `B1` | Regex / rules | Structured identifier ceiling |
| `B2` | spaCy NER | General NLP baseline |
| `B3` | Microsoft Presidio | Production framework baseline |
| `B4` | Multilingual transformer (XLM-R or an Indic-focused model) | Zero-shot neural baseline |
| `B5` | Same architecture as B4, Indian-adapted | Adaptation comparison |

Choose **one** model for B4. Do not implement ten.

### 19.1 Expectations are not results

Regex is *expected* to be strong on PAN/AADHAAR/PHONE/EMAIL and weak on PERSON/ADDRESS and
implicit context. Record this as a hypothesis, not a finding.

### 19.2 Presidio configuration disclosure — mandatory

> Recent Presidio releases ship India-specific recognizers (`IN_PAN`, `IN_AADHAAR`,
> `IN_VEHICLE_REGISTRATION`, `IN_VOTER`, `IN_PASSPORT`).

If Presidio is benchmarked with a default English configuration and reported as failing on
Indian PII, a reviewer will correctly reject the finding.

Required:

1. Record the exact Presidio version and the full enabled recognizer registry.
2. Report **both** configurations — default, and India-recognizers-enabled.
3. Any claim about Presidio must name the configuration it applies to.

The same disclosure discipline applies to spaCy model variants (`sm` / `lg` / `trf`) —
HybridPII's results were compromised by an undetected model-loading failure.

---

## 20. Metrics

| ID | Metric | Definition |
|---|---|---|
| `M1` | Entity precision | correct predicted / all predicted |
| `M2` | Entity recall | correct detected / all ground truth |
| `M3` | Entity F1 | harmonic mean |
| `M4` | Exact-span F1 | requires exact boundary match |
| `M5` | Type accuracy | correct type among correctly localized entities |
| `M6` | False-positive rate | non-PII predicted as PII; **broken down by `decoy_class`** |

Never report M3 alone. The M3-vs-M4 gap measures boundary error; the M2-vs-M5 gap measures
the detect-but-mislabel failure that *Unmasking* found dominant.

### 20.1 Primary research metric — robustness drop

```
robustness_drop(condition) = F1(reference condition) − F1(condition)
```

Reference is `EN`. Report **both** absolute performance and relative degradation: a system
can have lower absolute F1 and better robustness, and that distinction is a result.

---

## 21. Statistical treatment *(new in v1.1)*

Without this, "Hinglish costs 14 recall points" is an anecdote.

**Required:**

1. **Bootstrap confidence intervals** — resample the test set (≥1,000 iterations), report
   95% CI on every headline metric and on every robustness drop.
2. **Multiple seeds** — every fine-tuned model trained with ≥3 seeds; report mean ± SD.
   Single-seed fine-tuning results are not reportable.
3. **Paired comparison** — conditions share base instances, so use paired tests
   (bootstrap or Wilcoxon signed-rank), not unpaired.
4. **Multiple-comparison correction** — 7 languages × 4 contexts × 8 categories is a large
   comparison family. Apply Holm–Bonferroni or report FDR.
5. **No claim of a difference whose CI crosses zero.** Report it as "no measurable
   difference," which is itself a finding.

---

## 22. Experiment matrix

| ID | Experiment | Question |
|---|---|---|
| `E01` | Baseline on clean Indian PII | How do systems perform before stress? |
| `E02` | Language variation | Which realizations degrade most? |
| `E02b` | **Script isolation** | How much degradation is script alone? |
| `E03` | Context difficulty (C1–C3) | Does implicitness reduce performance? |
| `E03b` | **C4 ambiguity probe** | Abstain or guess wrong? |
| `E04` | Formatting sensitivity | How brittle are representations? |
| `E05` | Adversarial | Which perturbations break systems? |
| `E06` | PII-category analysis | Which types are most vulnerable? |
| `E07` | Failure analysis | Why are predictions wrong? |
| `E08` | Few-shot adaptation | How much Indian data is needed? |
| `E09` | Cross-condition generalization | Concepts or surface patterns? |
| `E10` | Naturalistic + real-carrier validation | Do findings survive realistic text? |

### 22.1 Few-shot design (E08)

Train sizes: **0, 25, 50, 100, 250, 500 per category.** Validation and test fixed; only
the training subset varies. Plot F1 / recall / robustness against training size — the
learning curve is the deliverable, not a single number.

Amin et al. found ~50 target examples after source pretraining approached the performance
of hundreds trained from scratch. Whether that holds for Indian code-mixed general-domain
text is an open question this experiment answers.

**Leakage rule:** if `PAN_0142` is in test, **no** variant of it — no language, no
perturbation, no paraphrase — may appear in training.

### 22.2 Priority tiers — scope control

Ten experiments × 5 baselines × 7 languages × 4 contexts is more than a final-year project
can complete well. Cut in this order:

| Tier | Experiments | Status |
|---|---|---|
| **Tier 1 — core** | E01, E02, E03, E06, E07, E08 | Must complete. Sufficient for both papers. |
| **Tier 2 — strong additions** | E02b, E03b, E10 (incl. real-carrier anchor) | Complete if time allows. E02b is the cheapest and most distinctive. |
| **Tier 3 — droppable** | E04, E05, E09 | Cut first. |

E02b is Tier 2 but costs almost nothing once the L3a/L3b split exists — do it before E04
or E05.

---

## 23. Failure taxonomy

| ID | Mode |
|---|---|
| `F1` | MISSED_PII — entity not detected |
| `F2` | WRONG_SPAN — partial or over-extended boundary |
| `F3` | WRONG_TYPE — correct span, wrong category |
| `F4` | FALSE_POSITIVE — non-PII predicted as PII (tag with `decoy_class`) |
| `F5` | CONTEXT_FAILURE — attributable to implicit/ambiguous context |
| `F6` | LINGUISTIC_FAILURE — attributable to Hindi / Romanized / code-mixed form |
| `F7` | FORMATTING_FAILURE — attributable to spacing/punctuation |
| `F8` | ADVERSARIAL_FAILURE — under deliberate perturbation |

`F9` — SCRIPT_FAILURE *(new in v1.1)*: attributable specifically to Devanagari
realization, isolable only via the E02b pair.

One prediction may carry multiple tags where justified.

---

# PART IV — APPLICATION

## 24. Scope

The application is the **practical artefact**, not the research contribution. Build it
last, on whichever approach the experiments favour.

```
Input → preprocessing → detection → span/type → confidence
      → entity merge → de-identification → sanitized text
```

```
IN:   bhai mera naam Rahul Sharma hai, mera PAN <PAN> hai. Call me at <PHONE>.
OUT:  bhai mera naam [PERSON_1] hai, mera PAN [PAN_1] hai. Call me at [PHONE_1].
```

### 24.1 Modes

| Mode | Output |
|---|---|
| MASK | `[PAN]` |
| TYPE-PRESERVING MASK | `[PAN_1]`, `[PERSON_1]` |
| REDACTION | `[REDACTED]` |

Type-preserving placeholders are preferred for LLM workflows — they retain structure.

### 24.2 Operating points

HybridPII's genuinely useful idea: expose the precision–recall trade-off as a product
feature rather than picking one point.

| Mode | Optimizes |
|---|---|
| Compliance | Recall |
| Balanced | F1 |
| Conservative | Precision |

### 24.3 Constraints

- Detector output preserves `type`, `text`, `start`, `end`, `confidence`.
- High confidence never implies "safe" — expose uncertainty in the UI.
- The demo must **not** send raw user input to an external LLM. Keep processing local.

---

# PART V — EXECUTION

## 25. Repository layout

```
indian-pii-robust/
├── CLAUDE.md
├── PROJECT_SPEC.md
├── README.md
├── LICENSE
├── .gitignore
│
├── configs/            pilot.yaml, production.yaml, pii_types.yaml
├── schemas/            base_instance.schema.json, example.schema.json
│
├── annotation/
│   ├── guidelines.md
│   ├── open_questions.md
│   ├── CHANGELOG.md
│   └── review_template.csv
│
├── data/
│   ├── raw/            base_instances.jsonl
│   ├── generated/      per-condition jsonl
│   ├── validated/      pilot_v0.1.jsonl
│   ├── rejected/
│   ├── annotations/
│   └── frozen/         test_v1.0.jsonl
│
├── generators/
│   ├── pii/            person, address, phone, email, pan, aadhaar, upi, bank_account
│   ├── contexts/       banking, support, delivery, verification, telecom, hr, health, general
│   ├── language/       english, indian_english, hindi, roman_hindi, hinglish, informal
│   ├── translit/       deterministic table + tests
│   └── perturbations/  spacing, punctuation, label_obfuscation, abbreviation, char_variation
│
├── validators/         structural, spans, semantic, language, script, duplicates
├── benchmark/          split.py, metrics.py, failure_analysis.py, stats.py
├── baselines/          regex, spacy, presidio, transformer
├── training/           train.py, evaluate.py, few_shot.py
├── experiments/        E01_baseline … E10_naturalistic
├── application/        api, detector, ui
├── reports/            pilot, benchmark, experiments
└── tests/
```

## 26. Configuration

No hard-coded parameters. Example `configs/pilot.yaml`:

```yaml
project:
  name: indian-pii-robust
  version: "0.1"
  guidelines_version: "0.1"

data:
  pilot_base_count: 100
  production_base_target: 4000

pii_types:
  PERSON: 12
  ADDRESS: 12
  PHONE: 12
  EMAIL: 12
  PAN: 13
  AADHAAR: 13
  UPI_ID: 13
  BANK_ACCOUNT: 13

transliterable_types: [PERSON, ADDRESS]

languages:
  - EN
  - IN_EN
  - HI_LATIN_PII
  - HI_DEVA_PII
  - ROM_HI
  - HINGLISH
  - INFORMAL_HINGLISH

contexts:   [EXPLICIT, SEMI_EXPLICIT, IMPLICIT, UNLABELLED]
perturbations: [A1, A2, A3, A4, A5]

validation:
  min_structural: 0.99
  min_span:       0.98
  min_semantic:   0.95
  min_language:   0.90
  min_naturalness: 0.85

split:      { train: 0.60, validation: 0.20, test: 0.20 }
random_seed: 42
```

## 27. Reproducibility and versioning

Every run records: `generator_version`, `config_version`, `guidelines_version`, `seed`,
`timestamp`, `template_version`, and — if an LLM was used — `model_name`,
`prompt_version`, generation parameters.

Fixed seed (42) for all non-LLM randomness. LLM generation is **not** assumed
deterministic; store outputs as artefacts.

Dataset versions: `pilot_v0.1` → `pilot_v0.2` → `benchmark_v1.0`. **Never silently
overwrite.** Increment, document the reason, retain the changelog.

Records annotated under different `guidelines_version` values must not be pooled in one
experiment without an explicit re-validation pass.

## 28. Required unit tests

| Area | Test |
|---|---|
| PII generators | Values satisfy their synthetic schemas |
| Transliteration | Deterministic; `len("राहुल") == 5` |
| Span extraction | Sentence start / middle / end; adjacent punctuation; **repeated entity** (3 identical values → indices 0,1,2, distinct spans); Devanagari surroundings |
| Span validator | `text[start:end] == realized_pii_value`, never `base_pii_value` |
| Language transforms | PII identity preserved; base linkage intact; metadata correct |
| Collapse rule | Non-transliterable types produce 6 variants with `hi_variant_collapsed: true` |
| Perturbations | Deterministic; `target` consistent with family; span moves iff `target == VALUE` |
| **Split logic** | **No base_id spans two splits — this test fails the build** |

## 29. Ethics statement (README requirement)

The README must state:

- No real personal data was intentionally collected, stored, or used for dataset
  generation or model training.
- All identifier values are synthetic and benchmark-safe; the benchmark does not validate
  whether any identifier was issued.
- Nothing is published that constitutes scraped PII, private conversation data,
  credentials, or real identifiers.
- The incident procedure in §11.2.

---

## 30. Publication mapping

The supervisor's requirement: **two journal-level papers, each using a different
algorithm, the second showing better results than the first.**

| Paper | Content | Algorithm |
|---|---|---|
| **Paper 1** | Benchmark construction + baseline evaluation + failure taxonomy (E01, E02, E03, E06, E07) | Existing systems: regex / spaCy / Presidio / zero-shot transformer |
| **Paper 2** | Indian adaptation and recovery (E08, + E02b/E10 if available) | Fine-tuned Indian-adapted model |

### 30.1 Fallback if H4 fails

The spec's honesty clause permits "fine-tuning doesn't help." That conflicts with a
requirement that Paper 2 beat Paper 1. Prepare the fallback **now**, not after the
experiment:

> If few-shot fine-tuning does not beat the hybrid baseline on overall F1, retarget
> Paper 2 at the **misclassification problem** — a hybrid of regex detection plus a
> context-based type classifier, evaluated on the M2-vs-M5 gap.

Rationale: *Unmasking* found 67% of cases were detected-but-mistyped. Type classification
conditioned on context is a much easier target than end-to-end detection, so a second
algorithm aimed at it is very likely to show a clear improvement — while remaining an
honest scientific result rather than a manufactured one.

Neither path requires falsifying anything.

---

## 31. Implementation order

**Milestone 1 — Pilot v0.1 (current).**

```
T01 repository skeleton + configs
T02 JSON schemas from guidelines §17
T03 8 PII generators + unit tests
T04 generate exactly 100 bases
T05 structural validator
T06 canonical English per base
T07 deterministic transliteration table + tests   ← before T08, always
T08 seven language realizations (with collapse rule)
T09 span extractor + occurrence-aware validator
T10 semantic + language/script validators
T11 20 hard negatives with distractors (all 6 decoy classes)
T12 100 adversarial variants
T13 human-review CSV
T14 pilot quality report + leakage test
    → STOP
```

**After pilot review only:**

```
generator refinement → guidelines v0.2 if needed → 4,000-base production
→ base-level split → freeze test set → baseline evaluation (E01–E03, E06)
→ failure analysis (E07) → few-shot (E08) → Tier 2 experiments
→ best model → application
```

## 32. Definition of done — Pilot v0.1

```
[ ] 100 base instances, permanent IDs, all 8 categories
[ ] all values synthetic and benchmark-safe
[ ] scenario metadata + canonical text on every base
[ ] transliteration table deterministic and tested
[ ] 6 or 7 realizations per base per collapse rule
[ ] exact spans, occurrence-indexed, code-point offsets
[ ] context labels allocated per §9.1
[ ] 20 multi-PII bases
[ ] 20 hard-negative bases with distractors, all 6 decoy classes present
[ ] 100 adversarial variants, target field consistent
[ ] structural / span / semantic / language / script validators implemented
[ ] duplicate detection scoped so controlled variants survive
[ ] rejected records logged with reason
[ ] human-review sheet generated
[ ] pilot quality report generated
[ ] leakage test passes (and fails the build when violated)
[ ] dataset, generator, config, guidelines versions and seed recorded
[ ] no real PII used
```

Only then: **APPROVED FOR PRODUCTION SCALE.**

---

## 33. Claims discipline

Before results exist, write:

> "We evaluate Presidio on our Indian benchmark."

Not:

> "Presidio fails on Indian data."

After results exist, write:

> "Presidio, configured with India-specific recognizers enabled (v X.Y.Z), achieved
> recall of R (95% CI [a, b]) on condition Y."

Likewise: *"We hypothesize that code-mixing may reduce detection performance and test this
experimentally"* — never *"Hinglish breaks PII detection."*

### 33.1 All four outcomes are publishable

| Outcome | Response |
|---|---|
| Existing systems fail significantly | Demonstrate and explain |
| Existing systems are robust | Report it; the hypothesis was wrong |
| Only specific types/conditions fail | Likely the **strongest** result |
| Fine-tuning doesn't help | Valid finding; trigger §30.1 fallback |

Never manipulate the dataset, the split, or the model to force an expected result.

---

## 34. Status board

| Item | Status |
|---|---|
| Literature discovery | COMPLETE |
| Literature synthesis | COMPLETE |
| Research gap | PROVISIONALLY DEFINED |
| Research questions | DEFINED |
| Hypotheses | DEFINED |
| Experimental design | DEFINED |
| Benchmark design | DEFINED |
| Annotation guidelines | v0.1 — FROZEN |
| Pilot specification | DEFINED |
| Pilot implementation | **NOT STARTED ← current objective** |
| Production dataset | NOT STARTED |
| Model training | NOT STARTED |
| Application | NOT STARTED |

**Immediate objective: Pilot v0.1. 100 base instances. Not the model. Not the
application. Not 28,000 records.**

---

## 35. Version

```
spec_version:        1.1
guidelines_version:  0.1
supersedes:          1.0
changelog:           see §0
```
