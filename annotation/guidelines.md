# Annotation Guidelines v0.1

> **Repository path:** `annotation/guidelines.md`
> **Status:** PROPOSED — freeze before any generator code is written
> **Governs:** Indian PII Robustness Benchmark, Pilot v0.1 and all downstream versions
> **Data policy:** SYNTHETIC ONLY. No real PII, ever.

---

## 0. How to use this document

This is the **ground-truth contract** for the benchmark. Every span, every label, and
every accept/reject decision resolves against these rules.

Three standing prohibitions:

1. **Do not invent a rule during generation or annotation.** If a case is not covered
   here, mark it `UNCERTAIN` and send it to adjudication.
2. **Do not silently edit v0.1.** Any change to span boundaries, PII definitions,
   ambiguity handling, script policy, or adversarial validity requires a version
   increment (`v0.2`) and a changelog entry.
3. **Do not simplify a hard example to make annotation easier, and do not construct an
   impossible example to make models fail.** Every record must have a defensible,
   human-interpretable ground truth.

---

## 1. Ground-truth authority hierarchy

When sources conflict, higher wins:

```
1. Base-instance metadata        (the generator declared the semantic role)
2. These annotation guidelines
3. Deterministic generator rules
4. Human adjudication
5. LLM assistance                 (advisory only)
```

An LLM may emit `PASS` / `FAIL` / `UNCERTAIN`. It may **never** create, alter, or
override a ground-truth label, span, or type.

---

## 2. Core annotation principle

Annotate the **smallest span containing the complete PII entity** required to carry
that entity's semantic role. Exclude words that merely *describe* or *introduce* the PII.

```
Input:   My PAN number is ABCDE1234F.

Correct:            ABCDE1234F          → PAN
Wrong:      PAN number ABCDE1234F
Wrong:   My PAN number is ABCDE1234F
```

The label text (`PAN number is`) is **context**, not entity.

---

## 3. Span boundary policy — general

**Exclude:** articles, pronouns, possessive suffixes, labels, verbs, explanatory words,
leading/trailing whitespace, trailing sentence punctuation.

**Include:** characters intrinsic to the PII's own representation — internal hyphens,
internal spaces, `+` country prefixes, `@` and domain in email/UPI, commas *inside* a
contiguous address.

```
Input:   +91-9876543210
PHONE:   +91-9876543210        (hyphen and prefix are intrinsic)

Input:   email me at rahul@example.test.
EMAIL:   rahul@example.test    (trailing period excluded)
```

---

## 4. Script and language policy

> **This section resolves the most serious design risk in the benchmark.**
> Read it before writing any language transformation code.

### 4.1 The problem

The core scientific principle is *same PII, different representation*. But the Hindi
condition (L3) uses Devanagari, and two categories — **PERSON** and **ADDRESS** — can be
written in either script. If a name silently becomes `राहुल शर्मा` in L3, the PII value
itself changed and base linkage breaks. If it silently stays `Rahul Sharma`, L3 becomes
artificially easy for Latin-script detectors and **script becomes a hidden confound in
exactly the two categories hypothesis H2 depends on.**

### 4.2 The resolution — split L3

The six language conditions become **seven realizations**:

| Code | Condition | Carrier script | PERSON/ADDRESS script |
|---|---|---|---|
| `EN` | Standard English | Latin | Latin |
| `IN_EN` | Indian English | Latin | Latin |
| `HI_LATIN_PII` | Hindi, Latin-script name | Devanagari | Latin |
| `HI_DEVA_PII` | Hindi, Devanagari name | Devanagari | Devanagari |
| `ROM_HI` | Romanized Hindi | Latin | Latin |
| `HINGLISH` | Hindi-English code-mixed | Latin | Latin |
| `INFORMAL_HINGLISH` | WhatsApp-style Hinglish | Latin | Latin |

`HI_LATIN_PII` and `HI_DEVA_PII` are generated from the **same base instance** and differ
in exactly one variable: the script of the PII itself. This converts a confound into a
measurable experiment (`E02b — script isolation`).

### 4.3 Which categories are affected

| Category | Script behaviour |
|---|---|
| PERSON | Transliterable — L3a/L3b split applies |
| ADDRESS | Transliterable — L3a/L3b split applies |
| PHONE | Digits; stays Latin/ASCII in all conditions |
| EMAIL | Stays ASCII in all conditions |
| UPI_ID | Stays ASCII in all conditions |
| PAN | Stays Latin/ASCII in all conditions |
| AADHAAR | Digits; stays ASCII in all conditions |
| BANK_ACCOUNT | Digits; stays ASCII in all conditions |

For the six non-transliterable categories, `HI_LATIN_PII` and `HI_DEVA_PII` are
**identical** and only one is generated. Record `hi_variant_collapsed: true` so the
variant count reconciles.

### 4.4 Required schema consequence

Every entity carries **both** values:

```json
{
  "type": "PERSON",
  "base_pii_value": "Rahul Sharma",
  "realized_pii_value": "राहुल शर्मा",
  "pii_script": "DEVANAGARI",
  "start": 5,
  "end": 16,
  "occurrence_index": 0
}
```

- `base_pii_value` — canonical form from the base instance. **Never changes across
  variants.** This is what links every realization back to `base_id`.
- `realized_pii_value` — the exact substring in *this* text. This is what the span
  validator checks.
- `pii_script` — `LATIN` | `DEVANAGARI` | `MIXED` | `NUMERIC`.

The span validator asserts `text[start:end] == realized_pii_value`. It must **not**
compare against `base_pii_value`.

### 4.5 Transliteration is a generator responsibility

Devanagari forms are produced by a **deterministic transliteration table**, not by an
LLM, and are recorded in the base instance at creation time. The same name must
transliterate identically in every record. Store the table version in
`generator_version`.

### 4.6 Indexing convention

All offsets are **Python string indices over Unicode code points** (`str` slicing).
Not bytes. Not grapheme clusters. Not UTF-16 code units.

Every consumer of the dataset must use the same convention. Devanagari matras and the
virama occupy their own index positions; this is intentional and consistent. Add a unit
test asserting `len("राहुल") == 5`.

---

## 5. PERSON

### 5.1 Definition

A person's name, where context indicates it refers to a person.

```
Input:   mera naam Rahul Sharma hai
PERSON:  Rahul Sharma
```

### 5.2 Titles and honorifics — EXCLUDED

Excluded in v0.1, both English and Indic:

`Mr` · `Mrs` · `Ms` · `Dr` · `Shri` · `Smt` · `Sir` · `Madam` ·
`ji` · `bhai` · `bhaiya` · `didi` · `sahab` · `saab` · `bhaisaab` · `jee` ·
`श्री` · `श्रीमती` · `जी`

```
Input:   Rahul ji ka PAN chahiye
PERSON:  Rahul                    (not "Rahul ji")

Input:   Mr Rahul Sharma
PERSON:  Rahul Sharma
```

> Rationale: honorifics attach productively in Hinglish and would otherwise create
> systematic span disagreement across exactly the conditions being measured.

### 5.3 Initials

```
Input:   R Sharma called yesterday.
PERSON:  R Sharma

Input:   S. Raghavan is the account holder.
PERSON:  S. Raghavan
```

The period after an initial is **internal** to the name and included. A terminal
sentence period is not.

### 5.4 Possessives

```
Input:   Rahul's PAN is ABCDE1234F.
PERSON:  Rahul                     (suffix "'s" excluded)
PAN:     ABCDE1234F
```

For Hindi possessive particles (`ka` / `ki` / `ke` / `का` / `की` / `के`), the particle
is a separate token and always excluded.

```
Input:   Rahul ka number 9876543210 hai
PERSON:  Rahul
PHONE:   9876543210
```

---

## 6. PERSON vs LOCATION — semantic role decides

Surface morphology **never** decides. The base instance declares the role; the text must
support it.

```
Input:   Rahul Nagar is near the station.
Base declares: synthetic locality
Result:  NOT_TARGET_PII (surface type LOCATION)

Input:   Rahul Nagar called me yesterday.
Base declares: synthetic person
Result:  Rahul Nagar → PERSON
```

`LOCATION` is **outside** the v0.1 taxonomy. Do not create a `LOCATION` label. Record it
in the `distractors` array (§13) with `surface_type: "LOCATION"`.

If the generated sentence does not clearly support the declared role, the example is
`UNCERTAIN` — do not rescue it by changing the role.

---

## 7. ADDRESS

### 7.1 Definition

Information identifying a physical residence or destination. May include: flat/house
number, building, street/road, locality, landmark, city, district, state, PIN code.

```
Input:    My address is Flat 302, ABC Apartments, Baner Road, Pune.
ADDRESS:  Flat 302, ABC Apartments, Baner Road, Pune
```

`My address is` is excluded.

### 7.2 Positional prepositions — INCLUDED

When a preposition is grammatically part of the location expression, it is **inside** the
span. Removing it changes the location referred to.

**Included when address-internal:**
English — `near` · `behind` · `opposite` · `next to` · `beside` · `in front of` ·
`above` · `below`
Hinglish/Romanized — `ke paas` · `ke peeche` · `ke saamne` · `ke bagal mein` ·
`ke upar` · `ke neeche`
Devanagari — `के पास` · `के पीछे` · `के सामने` · `के बगल में`

```
Input:    I stay near the old bus stand.
ADDRESS:  near the old bus stand           (verb "I stay" excluded)

Input:    main old bus stand ke paas rehta hu
ADDRESS:  old bus stand ke paas            (postposition trails in Hindi word order)
```

> Note the asymmetry: English prepositions **precede** the landmark, Hindi postpositions
> **follow** it. The span must capture whichever side carries the relation.

### 7.3 One span or several — the mechanical test

Judgment calls cause annotator drift. Use this rule:

> **Contiguous address components separated only by commas, whitespace, or
> address-internal prepositions/postpositions (§7.2) form ONE span.
> Any intervening non-address token splits the span.**

```
Input:    Flat 302, ABC Apartments, near the temple, Baner Pune 411045
ADDRESS:  Flat 302, ABC Apartments, near the temple, Baner Pune 411045   (one span)

Input:    I live in Flat 302, and the building is ABC Apartments near Baner Road.
          ("and the building is" is an intervening non-address clause)
ADDRESS 1: Flat 302
ADDRESS 2: ABC Apartments near Baner Road                                (two spans)
```

The generator declares the intended structure in
`base_instance.address_structure` (`SINGLE` | `SPLIT`), and the validator asserts the
realized annotation matches. A mismatch is `SEMANTIC_MISMATCH`, not a judgment call.

### 7.4 PIN code

A PIN code **inside** a contiguous address is part of the ADDRESS span. A bare PIN code
alone is `NOT_TARGET_PII` in v0.1 (it is not individually identifying).

---

## 8. PHONE

Annotate the complete number representation including intrinsic formatting.

```
9876543210
+91 9876543210
+91-9876543210
98765 43210
```

All four are complete PHONE spans. Surrounding words (`mera mobile number`) are excluded.

```
Input:   mera mobile number 9876543210 hai
PHONE:   9876543210
```

---

## 9. EMAIL

Complete address, trailing sentence punctuation excluded.

```
Input:   email me at rahul@example.test.
EMAIL:   rahul@example.test
```

Benchmark domains are restricted to reserved TLDs: `.test` · `.invalid` · `.example`.
Never generate an address at a real domain.

---

## 10. UPI_ID, and UPI vs EMAIL

### 10.1 Type is decided by semantic context, never by string shape

`something@something` is not automatically either type. This ambiguity is a deliberate
research target.

```
Input:   Email me at rahul123@example.test.
EMAIL:   rahul123@example.test

Input:   My UPI ID is rahul123@provider.
UPI_ID:  rahul123@provider

Input:   UPI pe rahul123@provider bhej dena.
UPI_ID:  rahul123@provider
```

### 10.2 Bare handle with no context — see §12.4

A bare `rahul123@provider` with no disambiguating context is **not** `UNCERTAIN` when it
originates from a declared base instance. It is context level `C4 UNLABELLED` and is
scored under the separate C4 protocol. See §12.4.

---

## 11. Structured identifiers — PAN, AADHAAR, BANK_ACCOUNT

### 11.1 Span = identifier value only

```
Input:      My PAN is ABCDE1234F.
PAN:        ABCDE1234F

Input:      P A N: ABCDE1234F
PAN:        ABCDE1234F           ("P A N" is obfuscated LABEL text, not entity)

Input:      My Aadhaar number is <AADHAAR_VALUE>.
AADHAAR:    <AADHAAR_VALUE>

Input:      My bank account number is <ACCOUNT_VALUE>.
BANK_ACCOUNT: <ACCOUNT_VALUE>
```

> **Critical distinction:** perturbing the *label* (§14, A3) never changes the span.
> Perturbing the *value* (§14, A1/A2/A5) always does. See §14.2.

### 11.2 Numeric shape alone never assigns a type

```
Input:   My order reference is 123456789012.
Result:  NOT_TARGET_PII — logged as a distractor with surface_type BANK_ACCOUNT
```

This rule is what makes false-positive measurement meaningful.

### 11.3 Synthetic identifier policy

All identifier values are **benchmark-safe**: structurally conforming to the documented
format so that detection difficulty is realistic, but generated so as not to represent
issued real-world credentials. Where a format has publicly documented reserved,
test, or never-issued ranges, generators draw from those ranges. Where no such range is
documented, values are synthetic-by-construction and are never checked against, derived
from, or matched to any real record.

The benchmark does **not** validate whether an identifier was actually issued. That is
explicitly out of scope, and the README must say so.

Every record carries `"synthetic": true`.

If any generated value is ever found to correspond to a real identifier: remove it,
invalidate every affected record, regenerate, and log the incident internally.

---

## 12. Context levels

| Code | Level | Description |
|---|---|---|
| `C1` | EXPLICIT | PII type directly named — `My PAN number is X.` |
| `C2` | SEMI_EXPLICIT | Short label cue — `PAN: X` |
| `C3` | IMPLICIT | Role implied, type unnamed — `I need to submit X for tax verification.` |
| `C4` | UNLABELLED | Bare value, little or no cue — `X` |

### 12.1–12.3 C1–C3

Standard annotation and scoring. Ground truth is human-verifiable from the text alone.

### 12.4 C4 UNLABELLED — special protocol

> **This resolves the collision between the C4 design condition and the
> "bare string is UNCERTAIN" rule. Both were right; they need separating.**

**Ground truth exists.** The base instance declares the semantic role, so the record has
a definite type. C4 is a designed condition (~8 pilot bases, ~600 production bases), and
a designed condition cannot have undefined ground truth.

**But it is not human-verifiable from text alone.** A reviewer looking only at
`ABCDE1234F` cannot confirm it is a PAN rather than a reference code.

Therefore:

**Annotation.** Type comes from base metadata. Span is the full bare value.

**Human review.** The reviewer sees the base metadata and validates **span correctness
and naturalness only**. The reviewer does **not** validate type and does **not** mark
C4 records `UNCERTAIN` on the grounds of missing context — that is the condition, not a
defect.

**Scoring — mandatory separation.** C4 is reported as its own track, never pooled into
headline recall/F1 with C1–C3.

- Under C4, a detector that finds the span but assigns the wrong type is **not** counted
  as a type error in the main results. No system can be expected to type an unlabelled
  string correctly.
- C4 is reported as an **ambiguity probe**: what does each system *guess*, and how does
  the guess distribution differ across systems and languages? A system that abstains and
  a system that confidently guesses wrong are different behaviours, and C4 is the only
  condition that exposes that.

**Genuinely unresolvable cases.** If the base instance itself does not declare a
semantic role, the record is invalid and rejected as `MISSING_SEMANTIC_ROLE`. It is not
`UNCERTAIN`.

---

## 13. Multi-PII, repeated PII, and hard negatives

### 13.1 Multi-PII — one span per entity

```
Input:  mera naam Rahul Sharma hai, mera PAN ABCDE1234F hai aur phone 9876543210 hai.

PERSON:  Rahul Sharma
PAN:     ABCDE1234F
PHONE:   9876543210
```

Never merge into one giant span.

### 13.2 Repeated PII — `occurrence_index` is mandatory

Each occurrence is annotated separately and indexed by order of appearance, starting
at 0, **per (type, base_pii_value) pair**.

```
Input:  My PAN is ABCDE1234F. Please use ABCDE1234F for verification.

[
  { "type": "PAN", "realized_pii_value": "ABCDE1234F",
    "start": 10, "end": 20, "occurrence_index": 0 },
  { "type": "PAN", "realized_pii_value": "ABCDE1234F",
    "start": 33, "end": 43, "occurrence_index": 1 }
]
```

The span validator resolves occurrences by walking all matches in order and selecting
index *n*. It must **never** use a bare `str.find()`, which always returns the first
match and silently mislabels every repeat.

Required unit test: a text with three identical values yields three entities with
`occurrence_index` 0, 1, 2 and three distinct, non-overlapping spans.

### 13.3 Hard negatives — `entities: []` plus `distractors`

A hard negative contains a substring that *resembles* PII but is declared non-PII by
context. It has an **empty** `entities` array and a populated `distractors` array.

```json
{
  "base_id": "NEG_007",
  "text": "The order number is 9876543210.",
  "entities": [],
  "distractors": [
    {
      "text": "9876543210",
      "start": 20,
      "end": 30,
      "surface_type": "PHONE",
      "actual_role": "ORDER_REFERENCE",
      "decoy_class": "NUMERIC_SHAPE"
    }
  ],
  "synthetic": true
}
```

**`decoy_class`** — required, one of:

| Class | Meaning | Example |
|---|---|---|
| `NUMERIC_SHAPE` | Digit string resembling phone/account/Aadhaar | order number `9876543210` |
| `ALNUM_SHAPE` | Alphanumeric resembling PAN | reference code `ABCDE1234G` |
| `NAME_AS_PLACE` | Person-like name used as locality | `Rahul Nagar is near the station.` |
| `HANDLE_SHAPE` | `x@y` where role is neither email nor UPI | a support ticket handle |
| `ORG_AS_PERSON` | Organisation name resembling a person | a firm named after a founder |
| `PARTIAL_PII` | Truncated/masked value no longer identifying | `XXXX XXXX 4321` |

Without `decoy_class` you can measure *that* a false positive happened but not *which
decoy category* caused it — and the per-decoy-class breakdown is one of the strongest
results this benchmark can produce.

`distractors` may also appear on **positive** records that contain both real PII and a
decoy. This is encouraged for the `HARD` difficulty tier.

---

## 14. Adversarial variants

### 14.1 Families

| Code | Family | Target | Changes span? |
|---|---|---|---|
| `A1` | SPACING | value | **Yes** |
| `A2` | PUNCTUATION | value | **Yes** |
| `A3` | LABEL_OBFUSCATION | label | No |
| `A4` | INFORMAL_ABBREVIATION | label | No |
| `A5` | CHARACTER_VARIATION | value | **Yes** |

### 14.2 Span rule for value-level perturbations

> **This closes the gap that would otherwise break the span validator on every
> adversarial example.**

**When a perturbation alters the identifier itself, the span is the full perturbed
string exactly as it appears in the text.**

```
A1 SPACING
Input:  My PAN is A B C D E 1 2 3 4 F.
PAN:    A B C D E 1 2 3 4 F
        base_pii_value      = "ABCDE1234F"
        realized_pii_value  = "A B C D E 1 2 3 4 F"

A2 PUNCTUATION
Input:  PAN:-ABCDE1234F!!!
PAN:    ABCDE1234F
        (":-" and "!!!" are label/decoration, outside the value — span unchanged)

Input:  My PAN is ABCDE-1234-F.
PAN:    ABCDE-1234-F
        (hyphens are inside the value — span includes them)

A5 CHARACTER_VARIATION
Input:  my pan is abcde1234f
PAN:    abcde1234f
```

Contrast with label-level perturbations, where the span is untouched:

```
A3 LABEL_OBFUSCATION
Input:  P.A.N: ABCDE1234F
PAN:    ABCDE1234F

A4 INFORMAL_ABBREVIATION
Input:  mera pan no ABCDE1234F h
PAN:    ABCDE1234F
```

The generator records which family it applied, so the validator knows whether to expect
`realized_pii_value == base_pii_value` (A3, A4) or `!=` (A1, A2, A5).

### 14.3 Recoverability ceiling

If a perturbation renders the intended PII unrecognisable to a competent human reader,
the example is marked `INVALID_ADVERSARIAL` and excluded from the standard positive
benchmark. It may be retained in a separate diagnostic pool.

Never force an annotation to preserve dataset size.

### 14.4 Metadata

```json
"perturbation": { "family": "A1", "type": "SPACING", "severity": 1, "target": "VALUE" }
```

`target` is `VALUE` or `LABEL`, and must be consistent with §14.1.

---

## 15. Punctuation and whitespace summary

| Situation | Rule |
|---|---|
| Terminal sentence punctuation | Excluded |
| Punctuation intrinsic to value (`+91-...`, `ABCDE-1234-F`) | Included |
| Punctuation from a label (`PAN:-`) | Excluded |
| Initial's period (`S. Raghavan`) | Included |
| Leading/trailing whitespace | Excluded |
| Internal whitespace intrinsic to value (`+91 9876543210`, A1 spacing) | Included |
| Commas inside a contiguous address | Included |
| Devanagari danda `।` at sentence end | Excluded |

---

## 16. Language conditions — annotation invariants

Code-mixing, romanization, and informal spelling **outside** the entity never change
entity boundaries or types.

```
mera naam Rahul Sharma hai            → PERSON: Rahul Sharma
bhai mera PAN ABCDE1234F hai          → PAN:    ABCDE1234F
mera pan no ABCDE1234F h              → PAN:    ABCDE1234F
मेरा PAN नंबर ABCDE1234F है।            → PAN:    ABCDE1234F
मेरा नाम राहुल शर्मा है।                  → PERSON: राहुल शर्मा  (pii_script: DEVANAGARI)
```

The last two are the L3a/L3b pair from §4 — same base, one variable changed.

---

## 17. Required example schema (v0.1)

```json
{
  "base_id": "PAN_001",
  "variant_id": "PAN_001_HINGLISH_A1_01",

  "text": "bhai mera PAN A B C D E 1 2 3 4 F hai",

  "entities": [
    {
      "type": "PAN",
      "base_pii_value": "ABCDE1234F",
      "realized_pii_value": "A B C D E 1 2 3 4 F",
      "pii_script": "LATIN",
      "start": 14,
      "end": 33,
      "occurrence_index": 0
    }
  ],

  "distractors": [],

  "language": "HINGLISH",
  "carrier_script": "LATIN",
  "context": "EXPLICIT",
  "domain": "ACCOUNT_VERIFICATION",

  "perturbation": {
    "family": "A1",
    "type": "SPACING",
    "severity": 1,
    "target": "VALUE"
  },

  "difficulty": "ADVERSARIAL",
  "address_structure": null,
  "hi_variant_collapsed": false,

  "synthetic": true,

  "generator_version": "0.1.0",
  "guidelines_version": "0.1",
  "template_id": "HINGLISH_PAN_03",
  "seed": 42,

  "validation": {
    "structural": "PENDING",
    "span": "PENDING",
    "semantic": "PENDING",
    "language": "PENDING",
    "human": "PENDING"
  },
  "validation_status": "PENDING",
  "review_status": "PENDING",
  "split": null
}
```

### Fields added in this revision (vs. the initial draft)

| Field | Why it exists |
|---|---|
| `base_pii_value` / `realized_pii_value` | Preserves base linkage when script or formatting changes (§4.4, §14.2) |
| `pii_script` | Makes script an isolable variable instead of a confound (§4) |
| `occurrence_index` | Deterministic resolution of repeated values (§13.2) |
| `distractors[]` + `decoy_class` | Per-decoy-class false-positive analysis (§13.3) |
| `perturbation.target` | Tells the validator whether the span should have moved (§14.2) |
| `carrier_script` | Distinguishes sentence script from entity script |
| `address_structure` | Makes the one-span/several-spans rule checkable (§7.3) |
| `hi_variant_collapsed` | Reconciles variant counts when L3a == L3b (§4.3) |
| `guidelines_version` | Records which contract produced this record |

---

## 18. Validation status values

| Status | Meaning | Action |
|---|---|---|
| `PASS` | Satisfies the rule | Continue |
| `FAIL` | Violates the rule | Reject, log reason |
| `UNCERTAIN` | Not resolvable under v0.1 | Human adjudication |
| `NOT_APPLICABLE` | Rule does not apply (e.g. type check under C4) | Continue |

Rejection reasons (extend as needed, never silently):

```
INVALID_PII_FORMAT
PII_NOT_FOUND
SPAN_MISMATCH
OCCURRENCE_MISMATCH
SEMANTIC_MISMATCH
ROLE_UNSUPPORTED_BY_TEXT
MISSING_SEMANTIC_ROLE
LANGUAGE_MISMATCH
SCRIPT_MISMATCH
NATURALNESS_FAILURE
INVALID_ADVERSARIAL
DUPLICATE
UNSAFE_REAL_PII_RISK
```

Rejected records are written to `data/rejected/` with the reason, the validator that
fired, and the generator version. **Never delete silently** — the rejection log is itself
a finding about what the generator struggles to produce.

---

## 19. Human review sheet

The reviewer sees:

| Field | Value |
|---|---|
| Text | *(generated text)* |
| Declared PII type | PAN |
| Marked span | *(highlighted)* |
| Language / carrier script | HINGLISH / LATIN |
| PII script | LATIN |
| Context level | EXPLICIT |
| Perturbation | A1 SPACING (target: VALUE) |

And answers:

```
Span correct?         YES / NO
Type correct?         YES / NO / N-A (C4)
Language correct?     YES / NO
Script correct?       YES / NO
Meaning preserved?    YES / NO
Natural?              YES / NO
Human-recoverable?    YES / NO   (adversarial only)
```

Any critical `NO` rejects the record. Under C4, `Type correct?` is `N-A` and never
rejects (§12.4).

### 19.1 Inter-annotator agreement

A sampled subset is reviewed independently by two reviewers. Report Cohen's κ on
categorical decisions. Disagreements go to adjudication — never silently pick one
reviewer. If a disagreement exposes a missing rule, that triggers a guidelines version
increment, not an ad-hoc decision.

---

## 20. Ambiguity policy

If an example cannot be confidently resolved under these rules:

```
validation_status = UNCERTAIN
```

Do not guess. Do not silently adjust. Send to adjudication.

If the ambiguity reveals a genuine gap in this document:

1. Record the case in `annotation/open_questions.md`
2. Draft the rule
3. Increment to `v0.2` with a changelog entry
4. Re-validate any records affected by the new rule
5. **Never edit v0.1 in place**

---

## 21. Frozen decisions (v0.1)

These are settled. Changing any of them requires a version increment and re-validation.

1. **Labels are context, not entity.** `PAN number is` is never inside the span.
2. **Titles and honorifics excluded** — English and Indic alike, including `ji` and `bhai`.
3. **Address prepositions/postpositions included** when grammatically part of the
   location expression; verbs excluded.
4. **Address span count is mechanical** — contiguity test in §7.3, declared in metadata.
5. **UPI vs EMAIL by semantic context**, never by string shape.
6. **PERSON vs place by semantic role**, never by surface morphology.
7. **Hindi splits into L3a / L3b** for PERSON and ADDRESS; script is a measured variable.
8. **Every entity carries `base_pii_value` and `realized_pii_value`.**
9. **C4 UNLABELLED has ground truth but is scored separately** as an ambiguity probe.
10. **Value-level perturbations move the span; label-level perturbations do not.**
11. **Hard negatives carry `distractors` with `decoy_class`.**
12. **Offsets are Python Unicode code-point indices.** One convention, everywhere.
13. **Identifiers are benchmark-safe synthetic**, not claimed provably-unissued.
14. **LLMs advise; they never own ground truth.**

---

## 22. Version

```
guidelines_version: 0.1
supersedes:        (none)
changelog:         annotation/CHANGELOG.md
```

Any change to span boundaries, PII definitions, ambiguity handling, script policy,
context-level scoring, or adversarial validity **requires a version increment**.

Records store the `guidelines_version` under which they were annotated. Records
annotated under different versions must not be pooled in a single experiment without an
explicit re-validation pass.
