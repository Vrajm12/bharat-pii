# Annotation Guidelines v0.11

> **Repository path:** `annotation/guidelines.md`
> **Status:** FROZEN — supersedes v0.10 (see `annotation/CHANGELOG.md`)
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

**ADDRESS's Devanagari form is not cached on the base instance** *(v0.9, resolves
OQ-021)*. Only PERSON gets a stored, base-instance-level Devanagari form
(`person_context.name_deva`, §4.5) — `person_context` already exists on every base for
scenario/narrative reasons independent of transliteration, so it has a natural home for
the cached value. ADDRESS has no equivalent side-channel object and none was added;
`schemas/base_instance.schema.json`'s `pii[]` item schema is unchanged
(`{type, base_pii_value, semantic_role}`, no fourth field). ADDRESS's Devanagari form is
generated later, at record-derivation time (T08), directly as `entities[].realized_pii_value`
for `HI_DEVA_PII` — computed from the same transliteration table (§4.7), just not
pre-computed and cached at base-instance creation the way PERSON's is.

### 4.5 Transliteration is a generator responsibility

Devanagari forms are produced by a **deterministic transliteration table**, not by an
LLM, and are recorded in the base instance at creation time. The same name must
transliterate identically in every record. Store the table version in
`generator_version`.

**`generator_version` is now a required field on the base instance itself** *(v0.9,
resolves OQ-020)* — `schemas/base_instance.schema.json` gained `generator_version`,
identical field name and semver pattern (`^[0-9]+\.[0-9]+\.[0-9]+$`) to the same field
already on `schemas/example.schema.json`. No new field name or versioning convention was
invented: one toolchain version number covers PII generation (T03), base-instance
assembly (T04), and the transliteration table (T07) together, consistent with how the
field was already used on derived records.

### 4.6 Indexing convention

All offsets are **Python string indices over Unicode code points** (`str` slicing).
Not bytes. Not grapheme clusters. Not UTF-16 code units.

Every consumer of the dataset must use the same convention. Devanagari matras and the
virama occupy their own index positions; this is intentional and consistent. Add a unit
test asserting `len("राहुल") == 5`.

### 4.7 Transliteration table structure *(added v0.8, resolves OQ-016, OQ-019)*

The "deterministic transliteration table" (§4.5, §8.3) is a **token-level lookup
table**: one entry per Latin token reachable from the frozen T03 PERSON and ADDRESS
generators, each mapped to a single, curated Devanagari string. A multi-token value
(e.g. `"Rahul Sharma"`) is transliterated by looking up and joining each of its
constituent tokens.

Explicitly **not** used, and not permitted, to produce a Devanagari form:

- character-level substitution
- an LLM
- any probabilistic transliteration
- any external general-purpose transliteration algorithm or library

**This is a benchmark-specific deterministic transliteration table, not a
general-purpose Hindi transliteration system.** It covers exactly the closed vocabulary
the frozen T03 generators can produce — nothing more. The table itself, once frozen, is
the transliteration ground truth (§4.4) — not a reference implementation of Hindi
transliteration in general, and not validated against, or expected to match, any
third-party transliteration tool's output.

### 4.8 ADDRESS lexical components *(added v0.8, resolves OQ-017)*

Every lexical (word) component reachable from the frozen `generators/pii/address.py`
vocabulary — building names, road names, city names, and literal words such as `"Flat"`
— must have an explicit table entry (§4.7). **Numeric components (house numbers, PIN
digits) remain unchanged ASCII digits** — they are never transliterated, matching real
Hindi typographic convention of retaining Arabic numerals inside Devanagari text.

The table is scoped strictly to what the frozen generator can actually reach. No
transliteration rule is invented for any ADDRESS form the generator cannot produce.

**Abbreviation/initialism tokens** *(added v0.9, resolves OQ-022)*: the frozen ADDRESS
vocabulary contains two tokens that are not ordinary pronounceable words —
`"ABC"` (`"ABC Apartments"`) and `"MG"` (`"MG Road"`). These are frozen as:

| Token | Devanagari |
|---|---|
| `ABC` | `एबीसी` |
| `MG` | `एमजी` |

**These are benchmark-specific deterministic conventions, not universal transliteration
claims** — there is no single correct way to transliterate an abbreviation, and no claim
is made that `एबीसी`/`एमजी` are "the" correct rendering of these initialisms in general
Hindi usage. They are frozen, versioned entries in this benchmark's table (§4.7) and
nothing more. The frozen ADDRESS vocabulary itself (`_BUILDING_NAMES`, `_ROAD_NAMES`,
`_CITIES` in `generators/pii/address.py`) is unchanged by this decision.

### 4.9 Lookup-miss policy — fail closed *(added v0.8, resolves OQ-018)*

If a token has no table entry, the lookup **fails closed**:

- raise a deterministic lookup error
- the affected candidate is rejected/logged (§15.1, `data/rejected/`), never silently
  accepted
- never guess a transliteration
- never call an LLM
- never call an external transliteration service or library
- never leave the token untranslated and pass the record through anyway

There is no fallback path. A lookup miss means the table is incomplete for the
generator's current vocabulary, which is a defect to fix (extend the table), not a case
to route around at generation time.

### 4.10 T07 / T08 division of responsibility *(added v0.10, resolves OQ-026)*

**T07 (`generators/translit/table.py`) is exclusively responsible for deterministic PII
transliteration** — nothing else. **T08 generates/constructs the carrier-language
sentence** around that PII value; T07 is never responsible for carrier text.

- For `HI_DEVA_PII`, T08 obtains the PERSON/ADDRESS Devanagari PII value from T07
  (`person_context.name_deva`, already computed at T04, or a direct
  `transliterate_value()` call for ADDRESS, which is never cached — OQ-021).
- Non-transliterable PII (PHONE, EMAIL, PAN, AADHAAR, UPI_ID, BANK_ACCOUNT) is never
  altered by T08 in any condition — `realized_pii_value == base_pii_value` always
  (§4.3).
- Carrier vocabulary (`mera`, `naam`, `hai`, and the loanword renderings in §4.11) is
  owned by T08's own template inventory (§4.13), never by T07's table. T07's table
  remains PII-vocabulary-only, as frozen in §4.7 — this division of labor is what keeps
  that framing intact rather than requiring a second, general-purpose transliteration
  system.

### 4.11 Matched-variant invariant — `HI_LATIN_PII` / `HI_DEVA_PII` *(added v0.10)*

**`HI_LATIN_PII` and `HI_DEVA_PII` must use identical carrier text.** Their only
difference is the PII value's script. Concretely: removing the PII substring from each
of the pair's `text` fields must leave byte-identical remainders. This is what makes
E02b (script isolation, PROJECT_SPEC.md §4/RQ2b) a controlled experiment rather than an
uncontrolled comparison — every other variable (carrier wording, register, domain) is
held fixed by construction, not by chance.

### 4.12 `IN_EN` — frozen Indian-English marker inventory *(added v0.10, resolves OQ-023)*

`EN` = standard English with **no** marker from this inventory. `IN_EN` = English with
**at least one**. These are established, legitimate features of the Indian English
variety (Kachru's World Englishes framework; documented in reference works on Indian
English, e.g. Sailaja 2009) — **not incorrect English, not errors, not a lesser
register.** Using them is a dialectal choice, the same way British vs. American
spelling is a dialectal choice, not a correctness question.

| Marker | Usage pattern | Example insertion |
|---|---|---|
| `kindly` | politeness adverb, replaces/supplements "please" | "Kindly note my PAN number is X." |
| `do the needful` | idiom: "take the necessary action" | "Kindly do the needful regarding X." |
| `revert` | verb: "reply/respond" (not its standard-English sense "return to a previous state") | "Please revert with confirmation of X." |
| `prepone` | verb: antonym of "postpone" (an Indian English coinage) | Used when a base's `purpose` involves rescheduling. |
| `please find below/attached` | formal correspondence idiom | "Please find my details below: X." |
| `intimate` | verb: "to inform" | "Please intimate the concerned department of X." |
| `the same` | anaphoric pronoun referring back to a preceding noun | "My PAN number is X; kindly confirm the same." |
| `at the earliest` | idiom: "as soon as possible" | "Please process X at the earliest." |

One marker is assigned deterministically per base (cycling through this table in
`base_id` order) — no randomness, no LLM judgment call about which marker "fits."

### 4.13 `ROM_HI` / `HINGLISH` — frozen loanword and insertion inventories *(added v0.10, resolves OQ-024)*

**`ROM_HI`** = Hindi grammatical structure + Hindi vocabulary + **only** the approved
ordinary-loanword inventory below, Latin script. **`HINGLISH`** = the same Hindi
grammatical structure, with **at least one** deliberate English lexical insertion
**beyond** that inventory. The boundary is a closed-set membership test, not an LLM
judgment call (per instruction) — see §4.14 for the deterministic check this enables.

**Approved ordinary-loanword inventory (`ROM_HI`)** — English-origin words nativized
enough in everyday spoken Hindi that using them is not perceived as code-mixing. Each
has a romanized form (for `ROM_HI`) and, separately, its own conventional Devanagari
spelling (for the `HI_LATIN_PII`/`HI_DEVA_PII` carrier, §4.14) — these are **not** T07
lookups (T07 is PII-only, §4.10); they are carrier-vocabulary constants T08 owns
directly:

| English concept | Romanized (`ROM_HI`) | Devanagari carrier form |
|---|---|---|
| number | `number` | `नंबर` |
| mobile | `mobile` | `मोबाइल` |
| email | `email` | `ईमेल` |
| bank | `bank` | `बैंक` |
| account | `account` | `अकाउंट` |
| address | `address` | `एड्रेस` |
| PAN | `PAN` | `PAN` *(acronym — stays Latin even in Devanagari carrier, per guidelines.md's own worked example, §16: "मेरा PAN नंबर ABCDE1234F है।")* |
| UPI | `UPI` | `UPI` *(acronym — same rule)* |

`Aadhaar` is **not** in this inventory — it is not an English loanword at all;
`आधार`/"Aadhaar" is Hindi-origin vocabulary, used directly in both scripts.

**HINGLISH insertion inventory** — a small, frozen set of additional English-origin
words/phrases whose presence (beyond the ordinary-loanword inventory above) marks a
sentence as `HINGLISH` rather than `ROM_HI`:

`please` · `sir` / `ma'am` · `confirm` · `actually` · `check` · `sorry` · `thanks` /
`thank you` · `okay` / `ok` · `problem` · `update`

### 4.14 `INFORMAL_HINGLISH` — frozen informal-marker categories *(added v0.10, resolves OQ-025)*

`INFORMAL_HINGLISH` retains the `HINGLISH` mixing requirement (§4.13) **and**
additionally requires **at least one** marker from any of the categories below. This is
not an arbitrary count — it mirrors `IN_EN`'s and `HINGLISH`'s own "at least one from a
frozen set" pattern (§4.12, §4.13), the same threshold already adopted for the other
two register/mixing boundaries in this document, applied consistently rather than
invented fresh.

| Category | Examples |
|---|---|
| Abbreviation | `u`, `ur`, `pls`, `plz`, `thx`, `msg` |
| Casual particle | `yaar`, `bro`, `na`, `toh`, `arre` |
| Informal copula/verb contraction | `h` (for `hai`), `hu` (for `hoon`) |
| Typographic register | all-lowercase sentence, minimal terminal punctuation |

### 4.15 `pii_script` determination rule *(added v0.11, resolves OQ-013)*

`pii_script` describes the **actual script composition of the realized PII span** —
never inferred from the PII type name, never assigned merely because a span contains
digits. Determine it by looking at the realized characters themselves:

| Type | Condition | `pii_script` |
|---|---|---|
| PERSON, ADDRESS | `EN`, `IN_EN`, `ROM_HI`, `HINGLISH`, `INFORMAL_HINGLISH`, `HI_LATIN_PII` | `LATIN` |
| PERSON, ADDRESS | `HI_DEVA_PII` | `DEVANAGARI` |
| PHONE | all conditions | `NUMERIC` |
| AADHAAR | all conditions | `NUMERIC` |
| BANK_ACCOUNT | all conditions | `NUMERIC` |
| PAN | all conditions | `LATIN` |
| EMAIL | all conditions | `LATIN` |
| UPI_ID | all conditions | `MIXED` |

**Worked examples:**

```
PHONE:              9876543210                    -> NUMERIC
PAN:                FZZFN0256Z                     -> LATIN
UPI_ID:             9876543210@mail.test           -> MIXED
PERSON (HI_DEVA_PII): स्नेहा शर्मा                   -> DEVANAGARI
```

`UPI_ID`'s realized span combines a numeric local part with a Latin domain
(`9876543210@mail.test`) — the span as a whole is not purely numeric or purely Latin, so
`MIXED` describes it correctly. `PAN` and `EMAIL` contain letters (and, for PAN, digits
too) but no non-Latin script, so `LATIN` is the correct umbrella — there is no separate
"alphanumeric" enum value, and none is introduced here.

### 4.16 `variant_id` — clean (unperturbed) record format *(added v0.11, resolves OQ-014)*

Clean records (no perturbation applied) use:

```
{base_id}_{language}
```

```
PERSON_001_EN
PERSON_001_IN_EN
PERSON_001_HI_LATIN_PII
PERSON_001_HI_DEVA_PII
PERSON_001_ROM_HI
PERSON_001_HINGLISH
PERSON_001_INFORMAL_HINGLISH
```

No perturbation suffix (`_A1_01` etc.) is appended to a clean record's `variant_id`. For
a clean record: `perturbation.family = "NONE"`, `perturbation.type = "NONE"`,
`perturbation.target = "NONE"`.

§17's original worked example, `"PAN_001_HINGLISH_A1_01"`, is explicitly a **perturbed**
record's ID (`perturbation.family: "A1"`) and does not define, and was never intended to
define, the clean-record format — see §17 for a clean-record example added alongside it.

### 4.17 T08 context freeze — `context: "EXPLICIT"` *(added v0.11)*

Every clean record T08 produces carries `context: "EXPLICIT"`. This is **not** a
redesign of the C1–C4 context allocation specified elsewhere (PROJECT_SPEC.md §9.1) —
that allocation governs a separate, later stage of the pipeline and is unchanged by this
decision.

Reasoning: T08's record count is fixed at 624 = (24 transliterable bases × 7
realizations) + (76 non-transliterable bases × 6 realizations) — arithmetic that only
holds if each base produces exactly one record per language condition, with no further
multiplication by context level. The seven language conditions are T08's experimental
variable; introducing C1–C4 variation within T08 would add a second, uncontrolled
dimension. Every T08 carrier template (§4.10–§4.14) is already written in the explicit
register ("My PAN number is X.", "mera PAN number X hai.") — so `EXPLICIT` is not an
arbitrary default, it is what these templates already are.

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

### 8.1 Benchmark-synthetic base representation *(added v0.7, resolves OQ-008)*

The **base representation** (`base_pii_value` — before any language or formatting
realization) is frozen as:

```
^[6789][0-9]{9}$
```

10 digits, first digit 6–9, no formatting. This is the canonical form
`generators/pii/phone.py` produces and `validators/structural.py` (T05, PROJECT_SPEC.md
§15 layer 1) checks.

This does **not** change the annotation rule above. `+91`, spaces, and hyphens remain
valid *intrinsic formatting of a PHONE span in realized text* — a later
realization/perturbation-layer concern (§14), not a base-representation concern. The
base representation has no formatting at all; a realized span may add it. T05 checks
only the unformatted base representation.

---

## 9. EMAIL

Complete address, trailing sentence punctuation excluded.

```
Input:   email me at rahul@example.test.
EMAIL:   rahul@example.test
```

Benchmark domains are restricted to reserved TLDs: `.test` · `.invalid` · `.example`.
Never generate an address at a real domain.

### 9.1 T05 structural grammar *(added v0.7, resolves OQ-009, OQ-011)*

The T05 structural check (PROJECT_SPEC.md §15 layer 1) for EMAIL is:

- exactly one `@`
- a non-empty local part
- a domain ending in exactly one of `.test`, `.invalid`, `.example`, matched as an
  **exact lowercase string** — no case normalization is performed; `.TEST`, `.Test`,
  etc. fail.

This is **not** full RFC 5321/5322 email validation, and no additional local-part
character restrictions are imposed beyond "non-empty" — the benchmark does not need,
and must not invent, a stricter local-part grammar than this.

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

### 10.3 BENCHMARK_SYNTHETIC pilot representation — UPI_ID *(added v0.5, resolves OQ-006)*

Neither governing document specifies a domain/provider-suffix safety rule for UPI_ID —
unlike EMAIL, which is explicitly restricted to reserved TLDs (§9). For the pilot,
UPI_ID is defined as an explicit **BENCHMARK_SYNTHETIC** representation, one fixed
grammar (Grammar 3 of three proposed in OQ-006):

```
<10-digit-synthetic-phone>@mail.test

e.g. 9876543210@mail.test
```

- The local part is a 10-digit value shaped like a synthetic Indian phone number (first
  digit 6–9, same convention as §8's PHONE examples) — one of the most common real-world
  UPI VPA patterns — but is never a real phone number.
- `mail.test` is a fixed, benchmark-safe domain on the same RFC 2606 reserved TLD
  (`.test`) that EMAIL already uses (§9). No real PSP handle or domain (`@paytm`,
  `@ybl`, `@oksbi`, or similar) is used or resembled.
- **Purpose:** this grammar is deliberately dotted, unlike a real UPI PSP suffix (which
  is always a single undotted token), so that it creates controlled surface-form
  collision with EMAIL — the property PROJECT_SPEC.md §7 explicitly designs UPI_ID to
  have ("Shape-collides with EMAIL — context-dependent typing"). This is **not** a claim
  about universal official UPI formatting; it is a deliberate benchmark construct so
  that contextual typing (§10.1) can be evaluated.
- No government/payment checksum or validation logic is applied or claimed. The value is
  not intended to represent an issued or NPCI-registered UPI handle.
- This is the **only** UPI_ID local-part/domain grammar in the pilot — no variants.

Generated by `generators/pii/upi_id.py`.

### 10.4 Domain case sensitivity *(added v0.7, resolves OQ-011)*

The frozen `mail.test` domain (§10.3) is matched as an **exact lowercase string** — no
case normalization. `@Mail.Test` or `@MAIL.TEST` are structurally invalid.

A value such as `9876543210@paytm` is structurally invalid **because it does not match
the frozen grammar** `<10-digit-phone>@mail.test` — not because `paytm` happens to
resemble a real PSP handle. Real-PSP avoidance (§10.3's own rationale for choosing
`mail.test` in the first place) explains why the grammar was *designed* this way; it is
not itself something the structural validator checks. The validator only ever checks
grammar conformance.

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

### 11.4 BENCHMARK_SYNTHETIC pilot representation — AADHAAR, BANK_ACCOUNT *(added v0.4, resolves OQ-004/OQ-005)*

Neither AADHAAR nor BANK_ACCOUNT has a real-world format established anywhere in this
document or PROJECT_SPEC.md — §4.3's table states only "Digits" for both, and every
worked example in §11.1 uses a placeholder (`<AADHAAR_VALUE>`, `<ACCOUNT_VALUE>`), never a
concrete value. For the pilot, both are defined as explicit **BENCHMARK_SYNTHETIC**
representations — deliberate, documented choices for controlled experiments, **not**
claims about official or universal real-world Indian identifier formats:

| Type | Pilot representation | What this is explicitly NOT |
|---|---|---|
| `AADHAAR` | Exactly 12 decimal digits, uniform random across all 12 positions (no leading-digit exclusion). | Not the official UIDAI Aadhaar format. No Verhoeff checksum or issuance-range validation is applied or claimed. |
| `BANK_ACCOUNT` | Exactly 12 decimal digits, uniform random. | Not claimed to be the universal length or format of Indian bank accounts, which vary by bank (roughly 9–18 digits in reality). |

The purpose of both representations is **recognition of identifier-shaped PII in
context** — testing whether a detector notices and correctly types a 12-digit value
given its surrounding text — not validation of real government or bank credentials.
Both are synthetic-by-construction per §11.3's fallback (no documented reserved/test
range exists for either type), generated by `generators/pii/aadhaar.py` and
`generators/pii/bank_account.py` respectively.

### 11.5 PAN structural casing *(added v0.7, resolves OQ-010)*

PAN's structural representation is frozen as uppercase-only:

```
^[A-Z]{5}[0-9]{4}[A-Z]$
```

Lowercase (e.g. `abcde1234f`) is structurally invalid in the base representation. No
checksum, issuance, or category-code (4th-character) validation is performed or
implied.

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

### 13.4 Base-level discriminator — `base_kind` *(added v0.3, resolves OQ-003)*

Every base instance declares `base_kind`, exactly one of:

| Value | Meaning |
|---|---|
| `POSITIVE` | The base declares genuine target PII. |
| `HARD_NEGATIVE` | The base declares no target PII — only a decoy context. |

This is an **explicit data-model decision**, not an inference. Specifically:

- **`base_kind == POSITIVE`** requires `pii` to contain **at least one** target PII
  object (single-PII or multi-PII bases alike, PROJECT_SPEC.md §12.2).
- **`base_kind == HARD_NEGATIVE`** requires `pii` to be an **empty array** (`[]`).
- **Distractor information belongs to the derived record**, never to the base instance.
  A hard-negative base instance carries no `distractors` field at all — `distractors[]`
  is populated only when the base is realized into a record (§13.3). This is why
  `schemas/base_instance.schema.json` does not, and must not, gain a `distractors`
  property.
- **`base_id` naming conventions must NOT be used to infer `base_kind`.** A `NEG_`
  prefix (as in the illustrative `NEG_007`, §13.3) is a human-readable convention only.
  `base_kind` is the sole discriminator a generator or validator may branch on.

This invariant is **cross-field** (it relates two different fields of the same base
instance) and is therefore enforced by `validators/base_kind.py`, not by
`schemas/base_instance.schema.json` — consistent with the schema's structure-only scope.
`base_kind` enum membership itself (`POSITIVE` / `HARD_NEGATIVE`, nothing else) *is*
structural and is enforced by the schema.

### 13.5 `semantic_role` describes the PII, not the scenario *(added v0.6, resolves OQ-007)*

`semantic_role` (PROJECT_SPEC.md §12.1, on each `pii[]` entry of a base instance)
describes the **role the PII value itself plays** — what kind of identifier or value it
is. It is **type-fixed**: one value per PII type, independent of `scenario.domain` and
`scenario.purpose`.

`scenario.domain` and `scenario.purpose` carry the **contextual use** of that PII — the
setting the base instance is placed in. The two are deliberately separate axes:

```
semantic_role      -> what the PII value IS        (fixed per type)
scenario.domain    -> what SETTING it appears in    (varies per base)
scenario.purpose   -> why it's needed in that setting (varies per domain)
```

A `PERSON` value's role does not change because the base's domain is
`employment_hr` versus `healthcare_administration` versus `banking_payments` — the same
person's name can appear as an employee, a patient, a delivery recipient, an account
holder, or someone mentioned in casual conversation, without the *role of the PII value*
changing. The frozen role for PERSON is therefore deliberately domain-neutral:

| Type | `semantic_role` |
|---|---|
| `PERSON` | `PERSON_NAME` |
| `ADDRESS` | `DELIVERY_ADDRESS` |
| `PHONE` | `CONTACT_NUMBER` |
| `EMAIL` | `CONTACT_EMAIL` |
| `PAN` | `TAX_IDENTIFIER` |
| `AADHAAR` | `NATIONAL_ID_IDENTIFIER` |
| `UPI_ID` | `PAYMENT_IDENTIFIER` |
| `BANK_ACCOUNT` | `PAYMENT_ACCOUNT_IDENTIFIER` |

*(`PERSON_NAME` supersedes `ACCOUNT_HOLDER_NAME`, frozen in the T04 generation run and
found, on data review, to falsely imply every PERSON base involves an account
relationship — it does not.)* Do not read any of these values as claiming anything about
what relationship the PII has to the scenario; that is
`scenario.domain`/`scenario.purpose`'s job, not `semantic_role`'s.

*(Added v0.12, resolves OQ-035.)* The other seven rows were already in effect —
approved as part of T04's design freeze and unchanged since, and independently confirmed
against all 100 records of `data/raw/base_instances.jsonl` (one `semantic_role` value per
type, matching this table exactly, no unexpected values) — but had never been written
into this table; only the `PERSON` row was, because it was the only one that changed via
OQ-007. This addition ratifies the existing dataset's values; it does not change any of
them, and no record was regenerated to produce this edit.

### 13.6 Deterministic semantic-use contract for `EN` — canonical-text equality
*(added v0.12, resolves OQ-036)*

Layer 3 (§15: "Sentence uses the value in the declared role") needs ground truth that
does not depend on parsing free text. Two mechanisms were considered and rejected:

- **Keyword/label matching** ("does a role-indicative word appear near the span") is a
  heuristic invented for the occasion — not derived from anything already frozen.
- **Reusing the T08 carrier templates** (§4.10–§4.14) as a validation oracle would make
  the generator's own private construction logic double as ground truth for checking the
  generator's own output — circular, and explicitly out of bounds.

One mechanism requires no new invention: PROJECT_SPEC.md §12.1 already defines a base
instance as *"a semantic record: the synthetic PII, its declared type and role, ... and
one canonical English sentence"* — grouping `canonical_text` into the *same* semantic
record as `semantic_role`, not treating it as a downstream generation artifact. And by
construction, T08's `EN` condition performs no transformation: for every one of the 100
records checked, `record.text` for `language == "EN"` is **byte-identical** to its source
base's `canonical_text`. This equality was already true; nothing about its meaning is
being changed here, only stated as a validation rule.

**The frozen contract:** for a record with `language == "EN"`, `context == "EXPLICIT"`,
and `perturbation.family == "NONE"` (i.e. an unperturbed clean T08 `EN` record — the only
kind that currently exists), ground truth for "the sentence asserts the declared role" is:

```
record.text == base.canonical_text   (exact string equality)
```

A match is `PASS`. A mismatch is `SEMANTIC_MISMATCH` — logged as a single failure bucket,
not sub-classified. This equality check cannot, by itself, distinguish *"the sentence uses
the value in the wrong role"* from *"the sentence contains the value but never asserts a
role at all"* — both would show as inequality. Only reason-coding at that finer grain
would require the text-content parsing this decision deliberately avoids.

**What this contract does not cover, and is not silently assumed to cover:**

- The other six language conditions (`IN_EN`, `HI_LATIN_PII`, `HI_DEVA_PII`, `ROM_HI`,
  `HINGLISH`, `INFORMAL_HINGLISH`) have no canonical-text equivalent to check against —
  no deterministic, non-heuristic, non-generator-internal text-content oracle exists for
  them under this decision. Layer 3 validation of "declared role is asserted in the
  sentence" for these six conditions is `NOT_APPLICABLE`, not silently `PASS`. Logged
  separately as OQ-037 (`annotation/open_questions.md`) rather than folded into this
  entry, since closing it requires its own new governance content (a per-language marker
  taxonomy), not a formalization of something already agreed.
- Adversarially perturbed `EN` records (`perturbation.family != "NONE"`) are excluded on
  purpose — perturbation intentionally changes formatting/spacing and would break exact
  equality by design, not because the role usage became wrong.
- Metadata-level role consistency — whether `base.pii[].semantic_role` itself matches the
  frozen §13.5 table, independent of what any sentence says — is a **separate** check
  (§13.5's table, resolving OQ-035), not part of this contract. That check applies to
  every record regardless of language condition, and is how *"semantic-role metadata
  inconsistent with the sentence"* is caught even when the sentence itself is never
  parsed.

### 13.7 Deterministic semantic-use contract for `IN_EN` and the five Hindi-register
conditions *(added v0.13, resolves OQ-037)*

§13.6 covered `EN` only. Two further mechanisms close the remaining six conditions —
neither is the T08 carrier-template dictionary, and neither is a keyword list invented
for this occasion.

**`IN_EN` — canonical-text containment.** §4.12 defines `IN_EN` as `EN` plus at least one
marker from a frozen inventory; the markers wrap or append to the sentence, they do not
rewrite it. Verified against all 100 `IN_EN` records: `base.canonical_text` occurs as an
**exact substring** of `record.text` in every one, with zero exceptions — the same
already-true-by-construction fact §13.6 formalized for `EN`, extended from equality to
containment because `IN_EN` is `EN` plus material, not `EN` transformed. Ground truth:

```
base.canonical_text in record.text
```

A miss is `SEMANTIC_MISMATCH` (the assertion the base declares is not even present as
written, not merely under-labeled).

**`ROM_HI` / `HINGLISH` / `INFORMAL_HINGLISH` / `HI_LATIN_PII` / `HI_DEVA_PII` — frozen
label-word presence.** These five genuinely translate the sentence; canonical-text
containment does not apply. But every word needed to name each type in these registers is
**already frozen elsewhere in this document** — this section assembles them into one
table for validation use; it does not choose any of them:

| Type | Romanized label (`ROM_HI`/`HINGLISH`/`INFORMAL_HINGLISH`) | Devanagari label (`HI_LATIN_PII`/`HI_DEVA_PII` carrier) | Source |
|---|---|---|---|
| `PERSON` | `naam` | `नाम` | §4.10 (frozen carrier vocabulary: `mera`, `naam`, `hai`); §5.1/§16 worked examples |
| `ADDRESS` | `address` | `एड्रेस` | §4.13 loanword table |
| `PHONE` | `mobile` | `मोबाइल` | §4.13 loanword table |
| `EMAIL` | `email` | `ईमेल` | §4.13 loanword table |
| `PAN` | `PAN` | `PAN` | §4.13 loanword table (stays Latin in Devanagari carrier per its own note) |
| `AADHAAR` | `Aadhaar` | `आधार` | §4.13 prose (explicitly excluded from the loanword table as Hindi-origin, not English-origin, but explicitly named) |
| `UPI_ID` | `UPI` | `UPI` | §4.13 loanword table (stays Latin) |
| `BANK_ACCOUNT` | `account` | `अकाउंट` | §4.13 loanword table |

Ground truth for the Latin-carrier trio (case-insensitive — §4.14 already freezes
"all-lowercase sentence" as a legitimate `INFORMAL_HINGLISH` feature, so casing cannot be
part of the check):

```
LABEL[type].lower() in record.text.lower()          -- ROM_HI, HINGLISH, INFORMAL_HINGLISH
```

Ground truth for the Devanagari-carrier pair (exact substring — Devanagari has no case):

```
DEVANAGARI_LABEL[type] in record.text                -- HI_LATIN_PII, HI_DEVA_PII
```

A miss is `ROLE_UNSUPPORTED_BY_TEXT` — this reason code has existed in §18's vocabulary
since v0.1 and names exactly this failure ("the text does not support the declared
role"); it had no validator implementation until this decision.

**Verified against every one of the 624 frozen records** (all seven conditions,
combining §13.6's `EN` rule, this section's `IN_EN` and five-condition rules): zero
failures.

**Why this is not the same thing as reusing the T08 carrier templates.** The templates
(§4.10–§4.14, `generators/language/templates.py`) are whole-sentence constructions,
private to T08, and checking a record against its *own* generator's template would be
circular — it could never fail for anything the generator actually produces, only for a
hand-mutated record. This table is different in kind: it names a single word per type,
sourced from content that was frozen independently of, and before, T08's implementation
(§4.10, §4.13's loanword table predates T08 per its `v0.10` marking), and a generator bug
that paired the wrong label with a type — while still producing an otherwise well-formed
sentence — would be caught by this check, because the check does not consult the
generator's own type→template association at all, only guidelines.md's word list and the
record's own declared `type`. The check also does not know or care about sentence
structure, marker insertion, word order, or informal transforms — it is not a template
match.

**Answering the audit questions this decision was resolved against:**

1. *Proposition asserted:* the record's text names the base's declared PII type, in the
   word this document already freezes for that (type, register) pair.
2. *Equivalence to `canonical_text`:* each label is the documented register-appropriate
   counterpart of the type-naming word `canonical_text` itself uses in English (verified:
   every `canonical_text` skeleton, value removed, is byte-identical across every base of
   a given type, e.g. `"My PAN number is <value>."` for all 13 `PAN` bases).
3. *Role involvement:* the expected label is looked up from `base.pii[0].type`; by
   §13.5/OQ-035, `type` fixes `semantic_role` — so a label match is only meaningful
   relative to the declared type, and a corrupted `type` field looks up the wrong label
   and fails to find it.
4. *Independence from carrier wording:* the check is substring presence of one word,
   blind to everything else in the sentence — the actual source of variation across
   `IN_EN`/`HINGLISH`/`INFORMAL_HINGLISH` (markers, insertions, informal transforms).
5. *Rejecting a wrong-role sentence:* a record whose text uses a different type's label
   instead of its own declared type's label fails to find the expected label —
   `ROLE_UNSUPPORTED_BY_TEXT`.
6. *Rejecting "PII present, role unasserted":* bare-value text with no label word at all
   fails the same way. **This contract cannot distinguish case 5 from case 6** — both are
   absence of the expected label — the same coarseness §13.6 already accepted for `EN`.
   Finer discrimination would require parsing sentence structure, which this decision
   does not attempt.
7. *Deterministic, no LLM/model:* substring containment and case-folding only.
8. *Transliterable vs non-transliterable alike:* `PERSON`/`ADDRESS` use the same
   mechanism as the six non-transliterable types — only the looked-up word differs.
9. *`HI_LATIN_PII`/`HI_DEVA_PII` matched invariant:* both carry byte-identical carrier
   text (§4.11), including the same Devanagari label — the check yields the same
   pass/fail outcome for both members of the pair, reinforcing rather than conflicting
   with the invariant.
10. *Collapsed Hindi representation:* verified directly — the single collapsed
    `HI_LATIN_PII` record for each of the 76 non-transliterable bases carries Devanagari
    carrier text exactly like the 24 transliterable bases' pairs, so the same Devanagari
    label lookup applies without special-casing.

### 13.8 Hard-negative decoy-class construction rules — five of six, one deferred
*(added v0.14, extended v0.15, resolves OQ-042 for `HANDLE_SHAPE`; `ORG_AS_PERSON`
deferred, not resolved)*

§13.3's table gives each decoy class a meaning and, for five of the six, exactly one
concrete worked value, sentence, or reusable generator construction. This section
freezes a deterministic construction rule for those five **by reusing formats and
vocabulary already frozen elsewhere in this document** — no new PII format, no new name
list, no new suffix list is invented.

| Class | Value shape (reused, not new) | `actual_role` | `surface_type` | `canonical_text` template |
|---|---|---|---|---|
| `NUMERIC_SHAPE` | PHONE's frozen `^[6789][0-9]{9}$` **or** AADHAAR/BANK_ACCOUNT's frozen 12-digit format (§8.1/§11.4) | `ORDER_REFERENCE` (§13.3's own worked value, reused verbatim) | `PHONE`, `AADHAAR`, or `BANK_ACCOUNT` (matching whichever shape was drawn) | `"The order number is {value}."` (§13.3's own worked sentence, reused verbatim) |
| `ALNUM_SHAPE` | PAN's frozen `^[A-Z]{5}[0-9]{4}[A-Z]$` (§11.5) | `REFERENCE_CODE` (the phrase this document already uses twice for exactly this case — §13.3's table and §12.4's C4 worked example) | `PAN` | `"The reference code is {value}."` (same one-sentence pattern `NUMERIC_SHAPE` already establishes, role phrase substituted) |
| `NAME_AS_PLACE` | a T03 frozen PERSON given name (`generators/pii/person.py`'s `_GIVEN_NAMES`) + the exact suffix `" Nagar"` — the literal worked example is `"Rahul Nagar"`, `"Rahul"` being `_GIVEN_NAMES`'s first entry | `LOCALITY` (§6: *"Base declares: synthetic locality"*) | `LOCATION` (§6, explicit: *"Record it in the `distractors` array (§13) with `surface_type: "LOCATION"`."* — not a new choice, an existing cross-reference) | `"{name} Nagar is near the station."` (§6's and §13.3's identical worked sentence, name substituted) |
| `HANDLE_SHAPE` | EMAIL's frozen local-part construction (`generators/pii/email.py`'s `_LOCAL_PART_WORDS` + a random digit suffix) paired with one of EMAIL's frozen `_DOMAIN_LABELS`, **with the reserved TLD omitted** — e.g. `rahul4521@corp`. Verified: this fails EMAIL's own frozen `_EMAIL_RE` (no `.test`/`.invalid`/`.example` suffix) and UPI_ID's frozen `_UPI_ID_RE` (local part is not phone-shaped), so it is genuinely "x@y where role is neither email nor UPI" (§13.3) | `INTERNAL_HANDLE` | `EMAIL` (a naive detector may still guess EMAIL from the `x@y` shape despite the missing TLD — that guess is exactly the confusion this class exists to measure) | `"You can also reach me at {value}."` |
| `PARTIAL_PII` | AADHAAR/BANK_ACCOUNT's frozen 12-digit format, first 8 digits masked as `"XXXX XXXX "` (space-grouped in 4s), last 4 digits shown — reproduces §13.3's own worked value `"XXXX XXXX 4321"` exactly | `MASKED_IDENTIFIER` | `AADHAAR` or `BANK_ACCOUNT` (matching whichever 12-digit shape underlies the masked value) | `"The account number is {value}."` (same one-sentence pattern, role phrase substituted) |

**`HANDLE_SHAPE` reuses `generators/pii/email.py`'s existing frozen vocabulary as the
sole source of truth** — `_LOCAL_PART_WORDS` and `_DOMAIN_LABELS` are read directly from
that module by any future generator implementing this rule; they are not duplicated or
re-declared here. **This is a benchmark-specific hard-negative *construction*, and does
not change EMAIL's own structural rule** (`validators/structural.py`'s `_EMAIL_RE`,
guidelines.md §9.1) in any way — a `HANDLE_SHAPE` value is explicitly required to *fail*
that rule, not redefine it. The one genuinely new decision this freezes (distinct from
the four already-resolved classes, which each reuse an existing rule unmodified) is
omitting the TLD that EMAIL's own docstring calls its safety mechanism; this omission is
scoped to `HANDLE_SHAPE` decoy construction only and carries no implication for EMAIL
generation itself.

**Multiple instances per class** (needed to fill §13.9's quota) are produced by varying
the underlying frozen value (a different digit string, a different `_GIVEN_NAMES` or
`_LOCAL_PART_WORDS`/`_DOMAIN_LABELS` entry) — never by varying the shape, role, or
template above.

**`ORG_AS_PERSON` is deferred from Pilot v0.1, not resolved.** The six-decoy-class
design intent is preserved as the originally-stated scope (`PROJECT_SPEC.md` §31/§32,
§13.3's own table) — this entry does not retract that intent. But unlike every other
class, §13.3's table gives `ORG_AS_PERSON` only a natural-language description (*"a firm
named after a founder"*) with **no** concrete worked value, sentence, or reusable
generator construction anywhere in either governing document, and two independent
repository-wide audits (`annotation/open_questions.md`, OQ-042) found nothing to build
one from. Freezing a specific grammar would require inventing organisation-name
vocabulary with no textual anchor — exactly what this project's discipline (OQ-004
through OQ-011, OQ-035–041) has consistently refused to do. Rather than fabricate one,
`ORG_AS_PERSON` is explicitly excluded from Pilot v0.1's 20 hard-negative bases (§13.9);
its 6-class taxonomy membership is unchanged, and a future pilot revision may
reintroduce it if concrete construction evidence emerges. **Scope consequence for the
paper:** Pilot v0.1's hard-negative set — and therefore its `decoy_class` breakdown of
M6 — covers five of the six decoy classes named in the original design, not six; this
must be stated as a limitation, not implied to be complete.

**Carrier-sentence register variation (T08-equivalent step) is out of scope here.** This
section freezes one `canonical_text` template per resolved class — the base-instance-level
sentence, exactly analogous to what T04 froze per PII type before T08 later froze how
that sentence varies across the seven language conditions. How a hard-negative's decoy
sentence varies by language condition is §13.11's question, not this one.

### 13.9 Hard-negative decoy-class distribution *(added v0.14, resolves OQ-043; redistributed v0.15 following `ORG_AS_PERSON`'s deferral)*

20 hard-negative bases, originally all 6 decoy classes present (`PROJECT_SPEC.md`
§31/§32), do not divide evenly (20 / 6 = 3.33). The remainder was assigned to the first
classes in §13.3's own table order — a content-free tie-break, not a judgment about
which classes matter more, consistent with this document's existing pattern of
order-based determinism (e.g. §4.12's marker assigned by cycling `base_id` order;
§20.3's `rank(g,p)` tie-break by fixed positional order).

Following §13.8's decision to defer `ORG_AS_PERSON` from Pilot v0.1, its 3-base
allocation is **redistributed**, by the same table-order tie-break, to the three
classes preceding it in §13.3's table that had not already received the original
remainder: `NUMERIC_SHAPE`, `ALNUM_SHAPE`, `NAME_AS_PLACE` each gain one base. This
keeps the total at the frozen 20 hard-negative bases without inventing a new
distribution principle.

| Class | Count | Status |
|---|---|---|
| `NUMERIC_SHAPE` | 5 | constructible (§13.8) |
| `ALNUM_SHAPE` | 5 | constructible (§13.8) |
| `NAME_AS_PLACE` | 4 | constructible (§13.8) |
| `HANDLE_SHAPE` | 3 | constructible (§13.8, v0.15) |
| `ORG_AS_PERSON` | 0 | **deferred, excluded from Pilot v0.1** (§13.8, OQ-042) |
| `PARTIAL_PII` | 3 | constructible (§13.8) |
| **Total constructed** | **20** | |

This table is frozen independently of §13.8's construction rules: it fixes *how many*
bases exist per class, not *how* to build them. Every row is now backed by a
construction rule except `ORG_AS_PERSON`, which is deliberately not built at all in
this pilot rather than assigned a rule it has no evidence to support.

### 13.10 Hard-negative `context` value *(added v0.14, resolves OQ-045)*

Every hard-negative derived record carries `context: "EXPLICIT"`, by direct analogy to
§4.17's identical freeze for T08's positive clean records. Not a redesign of
`PROJECT_SPEC.md` §9.1's C1–C4 allocation, which is defined in terms of how explicitly a
**PII role** is asserted — a hard negative has no PII role at all, only a decoy role, so
varying `context` in the C1–C4 sense would require inventing a new, parallel
explicitness scale for decoys that is not stated anywhere. `EXPLICIT` is not merely the
simplest choice: it is the only one that does not require that invention, and it matches
the one existing worked example (`NEG_007`'s *"The order number is 9876543210."*
directly names what the decoy purports to be, the definition of `EXPLICIT`, §9's own C1
row).

### 13.11 Hard-negative language-condition count — six realizations *(added v0.15, resolves OQ-044)*

**Frozen:** every hard-negative base produces exactly **six** derived realizations:

```
EN
IN_EN
ROM_HI
HINGLISH
INFORMAL_HINGLISH
one collapsed Hindi realization
```

The collapsed Hindi realization is generated **exactly once**, using the existing
`hi_variant_collapsed: true` schema field (`schemas/example.schema.json`) — the same
field §8.1 already defines, not a new one. A hard-negative base has `pii: []`: no PII
entity, therefore no PII-script axis at all for `HI_LATIN_PII` and `HI_DEVA_PII` to
differ on. Generating both would produce two byte-identical records — no information
gained, only redundancy.

**This is a deliberate extension of §8.1's rationale to the `HARD_NEGATIVE` case, not a
claim that §8.1 literally named hard negatives.** §8.1's own text is scoped to "the six
non-transliterable **categories**" by name, a closed list that does not include
`HARD_NEGATIVE` — a hard negative belongs to none of the eight named PII categories at
all. What is reused is §8.1's *stated reason* for collapsing (§4.1: the split exists
solely to isolate PII-script variation), which applies to a record with no PII value at
least as strongly as it applies to a non-transliterable PII type. This was chosen over
two competing readings, recorded and rejected in `annotation/open_questions.md`
(OQ-044): full seven-condition treatment (would generate the identical-content pair
above, contradicting the reason the split exists) and a construction consistent with
`PROJECT_SPEC.md` §12.2's approximate "~60" figure (that figure is self-disclaimed by
its own document — *"Exact record count may vary"* — was never given the dedicated
exact-derivation treatment positives' own once-approximate figure eventually got in
§8.2, and requires an additional, unevidenced choice — which 3, or which construction —
that neither candidate could ground in the frozen text).

**Cardinality:** 20 hard-negative bases × 6 realizations = **120 hard-negative derived
records**, for every base whose decoy class has a frozen construction rule (§13.8) —
today, 20 of 20, since `ORG_AS_PERSON` was reallocated to zero bases (§13.9) rather than
left partially unconstructed.

### 13.12 Hard-negative construction ground truth — `hard_negative_decoy`
*(added v0.16, resolves OQ-046)*

Implementing §13.8–§13.11 surfaced a genuine architecture gap, not a policy question:
**there was nowhere to persist a hard-negative base's own decoy metadata.**

**Why `pii[]` stays empty.** Unchanged, restated for context: `base_kind ==
HARD_NEGATIVE` requires `pii == []` (§13.4, decision 16) — this is definitional, not
renegotiated here. A hard negative declares no target PII; that is what makes it a hard
negative.

**Why `entities[]`/`distractors[]` stay derived-record-only.** Also unchanged: §13.4
already states, explicitly and absolutely, that distractor information belongs to the
derived record, never the base instance, and that `schemas/base_instance.schema.json`
"does not, and must not, gain a `distractors` property." `entities[]` was never a
base-instance field for *any* `base_kind` — it is exclusively a derived-record
(`schemas/example.schema.json`) concept, the direct analogue of how `pii[]` is the
base-level field and `entities[]` is what a positive base's PII becomes once realized
into a record. Neither of these rules is touched by this section.

**Why persisted decoy metadata is necessary anyway.** For a positive base, `pii[]` is
the structured, persisted field every later derivation step (T08) reads — it never
reconstructs a base's PII from scratch. A hard-negative base has no equivalent: with
`pii` frozen at `[]`, there was no field anywhere carrying forward *which* decoy_class,
value, `actual_role`, and `surface_type` a given `base_id` was constructed with. Without
one, a later derived-record generator would have no non-parsing way to know this —
and this project has never treated `canonical_text` as a parseable source of ground
truth (T09/T10's entire design exists to avoid exactly that).

**Why RNG replay was rejected as an alternative.** Re-deriving decoy metadata from
`base_id` + seed at derived-record-generation time, instead of persisting it, was
considered and rejected: it would make hard-negative derivation depend on exactly
reproducing the base generator's own RNG sequence, a coupling positive-base derivation
(T08) does not have — T08 reads only `base.pii[]`, never re-runs T04's generator. Making
hard negatives work differently from every other base_kind, for no reason other than
avoiding one new field, was judged a worse inconsistency than the field itself.

**The field, minimal:** `hard_negative_decoy` — optional (not in
`schemas/base_instance.schema.json`'s top-level `required` array, so the 100 existing
`POSITIVE` bases remain valid and byte-identical without it), object-or-null, exactly
four sub-fields when populated:

```
decoy_class    -- schemas/base_instance.schema.json's own decoy_class $def,
                  duplicated to match schemas/example.schema.json's decoy_class
                  enum exactly (same cross-schema duplication convention as
                  generator_version, OQ-020) -- no cross-file $ref, consistent
                  with every other schema in this repository
value          -- the decoy's realized value (e.g. "9876543210", "rahul4521@corp")
surface_type   -- free string, matching §13.8's per-class frozen values
actual_role    -- free string, matching §13.8's per-class frozen values
```

**Cross-field relationship (validators, not schema):** `base_kind == POSITIVE` requires
`hard_negative_decoy` absent or null; `base_kind == HARD_NEGATIVE` requires it present
and populated. This is enforced by `validators/base_kind.py`'s
`check_base_kind_hard_negative_decoy_invariant`, a new function alongside the existing
`check_base_kind_pii_invariant`, not by an `if`/`then` conditional in the schema. JSON
Schema 2020-12 *could* express this conditional — that is not the limitation. The
limitation is architectural consistency: the base_kind/`pii` cardinality invariant
(decision 16) was deliberately kept out of the schema and placed in `validators/`,
precisely so that "schema = structure only, cross-field logic = validators" stays one
rule with no exceptions. Adding an `if`/`then` here to save one small validator function
would break that rule for the first time since it was established at T02.

**How Phase 2 will use this field (design note, not an implementation commitment):** a
future derived-record generator reads `base.hard_negative_decoy` for a `HARD_NEGATIVE`
base and materializes it into exactly one `distractors[]` entry per derived record —
`text`/`start`/`end` computed against that record's own carrier text (by the same
occurrence-finding primitive `generators/language/spans.py` already provides, never a
bare `str.find()`), `surface_type`/`actual_role`/`decoy_class` copied verbatim from the
persisted field. `entities` remains `[]` on every such record, per §13.3. This
architecture is recorded here so Phase 2 has a target to implement against; Phase 2
itself is out of scope for this decision.

### 13.13 Hard-negative realization inventory — a benchmark-specific deterministic
lexical inventory, not a general-purpose Hindi translation system *(added v0.17,
resolves OQ-047)*

§13.8 could construct only `EN`/`IN_EN` for the five constructible decoy classes;
`ROM_HI`/`HINGLISH`/`INFORMAL_HINGLISH`/the collapsed Hindi realization required
concept words (`OQ-047`'s audit: "order," "reference"/"code," "station,"
"contact"/"reach") that exist nowhere in `§4.13`'s loanword table or anywhere else in
this document. This section freezes exactly those words and nothing more — a small,
closed, benchmark-specific inventory, explicitly **not** a general-purpose Hindi
translation or transliteration system, the same framing `§4.7` already established for
T07's PII table.

**Lexical inventory:**

| Concept | Romanized (`ROM_HI`/`HINGLISH`/`INFORMAL_HINGLISH`) | Devanagari (collapsed Hindi) | Status |
|---|---|---|---|
| my | `mera` | — | A — already frozen, §4.10 |
| is (copula) | `hai` | है | A — already frozen, §4.10/§4.14 |
| number | `number` | नंबर | A — already frozen, §4.13 |
| account | `account` | अकाउंट | A — already frozen, §4.13 |
| near (postposition) | `ke paas` | के पास | A — already frozen, §7.2 |
| **order** | `order` | **ऑर्डर** | **B — new policy, frozen now** |
| **reference code** (compound, not decomposed) | `reference code` | **रेफरेंस कोड** | **B — new policy, frozen now** |
| **station** | `station` | **स्टेशन** | **B — new policy, frozen now** |
| **contact** | `contact` | **कॉन्टैक्ट** | **B — new policy, frozen now** |

No item labeled A is redefined or reinterpreted here — each is cited to the section
that already froze it. Every item labeled B is being frozen for the first time by this
entry; none was previously implied, and none is claimed to be linguistically
authoritative Hindi beyond this benchmark's own controlled use, mirroring `§4.8`'s own
disclaimer for `ABC`/`MG`.

**Carrier grammar per constructible decoy class** — one `ROM_HI` template, its
Devanagari counterpart (shared with the collapsed Hindi realization, `§4.11`'s
matched-variant principle applied to a record with no PII-script axis at all), all
built only from the inventory above plus `{value}` (`hard_negative_decoy.value`,
substituted as one opaque, never-transliterated slot — see the value-preservation rule
below):

| Decoy class | English concept (§13.8) | `ROM_HI` carrier | Devanagari carrier |
|---|---|---|---|
| `NUMERIC_SHAPE` | order number | `mera order number {value} hai.` | `मेरा ऑर्डर नंबर {value} है।` |
| `ALNUM_SHAPE` | reference code | `mera reference code {value} hai.` | `मेरा रेफरेंस कोड {value} है।` |
| `NAME_AS_PLACE` | locality near a landmark | `{value} station ke paas hai.` | `{value} स्टेशन के पास है।` |
| `HANDLE_SHAPE` | non-email contact string | `mera contact {value} hai.` | `मेरा कॉन्टैक्ट {value} है।` |
| `PARTIAL_PII` | masked account-like number | `mera account number {value} hai.` | `मेरा अकाउंट नंबर {value} है।` |

`PARTIAL_PII`'s carrier uses **zero** words from the new inventory — both "account" and
"number" are already frozen (§4.13) — but the *template itself* (assembling `mera` +
those two loanwords + `hai`, matching §13.8's own English "The account number is
{value}." concept) is frozen here for the first time, since no prior entry stated a
general assembly principle and reusing pre-existing words is not the same as the
sentence being pre-existing (the distinction the OQ-047 audit raised and did not
resolve on its own).

**Per-condition construction, all six realizations:**

- **`EN`** — `canonical_text` unchanged, exactly as §13.8 already froze per class. No
  new content.
- **`IN_EN`** — `canonical_text` wrapped with one marker from the existing, generic
  §4.12 `IN_EN` inventory (`kindly`, `do the needful`, `revert`, `prepone`, `please find
  below/attached`, `intimate`, `the same`, `at the earliest`), cycled deterministically
  by the base's position in `NEG_{NNN}` order — the same wrap functions already frozen
  for positives, which operate on any sentence and were never PII-type-specific. No new
  content.
- **`ROM_HI`** — the frozen carrier template above, `{value}` substituted verbatim.
- **`HINGLISH`** — the `ROM_HI` sentence with one pattern from the existing, generic
  §4.13 `HINGLISH_PATTERNS` (`generators/language/templates.py`) applied unchanged —
  confirmed by direct execution against a non-PII test sentence that both patterns
  (`Sir, {sentence}` / `{sentence}, please confirm.`) are pure string operations,
  identical in kind to what T08 already applies to PII-bearing sentences. **No new
  vocabulary beyond `ROM_HI`'s own.**
- **`INFORMAL_HINGLISH`** — built from the `HINGLISH` sentence exactly as
  `realize_informal_hinglish` already does for positives: the `{value}` substring is
  located by position and carved out *before* any transform; only the surrounding
  carrier fragments are lowercased and copula-contracted (§4.14's existing
  `hai`→`h`/`hoon`→`hu` map) and one existing §4.14 casual particle is appended; `value`
  is reinserted byte-for-byte; the span contract is re-verified after reassembly,
  failing closed (matching `generators/language/realizations.py`'s existing
  `SpanResolutionError` discipline) if reinsertion did not preserve `value` exactly. **No
  new vocabulary beyond `ROM_HI`'s own.**
- **Collapsed Hindi realization** — one record, labeled `HI_LATIN_PII` with
  `hi_variant_collapsed: true`, matching T08's own established label for records with no
  PII-script axis (§13.11's own reasoning: "labeled `HI_LATIN_PII`... because
  `pii_script`... is never `DEVANAGARI`" — a hard negative has no `pii_script` at all,
  the same precondition applied more completely). Carrier text is the Devanagari
  template above; `{value}` is substituted **without transliteration, in its original
  script**, mirroring §4.13's own precedent that `PAN`/`UPI` "stay Latin even in
  Devanagari carrier" — there is no hard-negative equivalent of T07's transliteration
  table, and none is created by this entry.

**Span location and occurrence:** the single distractor's `start`/`end` are located in
the realized carrier text using `generators/language/spans.py`'s existing
`find_occurrence` primitive — the same occurrence-walking function T08 already uses,
never a bare `str.find()`. `distractors[]` items have no `occurrence_index` field
(`schemas/example.schema.json`), unlike `entities[]` — a hard-negative record has
exactly one distractor, so occurrence selection is always "the first (and only)
occurrence of `value`," not a new mechanism.

**Punctuation and spacing:** preserved by construction, not by a new rule — every step
above is either a fixed-template substitution, a fixed wrap/prefix/suffix operation on
a complete sentence, or a carve-out-transform-reinsert sequence that never touches the
`{value}` substring's own characters. This is the identical discipline
`generators/language/realizations.py` already implements and verifies for positive PII;
nothing new is introduced here beyond substituting `hard_negative_decoy.value` for
`base_pii_value` as the substring being preserved.

**Non-PII preservation, checked per class:** `entities` remains `[]` on every
realization, unconditionally (§13.3, unchanged). No carrier template above reuses a
PII-type's own frozen template in a way that would falsely assert the distractor is
that PII type — `PARTIAL_PII`'s reuse of "account"/"number" continues the *same*
account-like framing §13.8 already froze at the English level (`"The account number is
{value}."`), not a new semantic claim; `HANDLE_SHAPE` deliberately does **not** reuse
EMAIL's frozen "mera email {value} hai." template (rejected in the OQ-047 audit,
Candidate B) — its own new word, "contact," names a role EMAIL's own vocabulary does not
claim. `hard_negative_decoy.value`, `surface_type`, `actual_role`, and `decoy_class` are
unchanged by this entry — this section governs surrounding carrier text only.

**What this does not authorize:** `ORG_AS_PERSON` remains deferred, quota 0 (§13.8/§13.9,
unchanged); the six-realization count is unchanged (§13.11); no schema, validator, or
generator file is created or modified by this entry — it freezes content for a future
Phase 2 implementation to consume, the same way §13.8 froze `canonical_text` templates
before any generator read them.

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

### 14.5 Pilot Base Selection (20 Bases) *(added v0.18, resolves OQ-049)*

The 20 positive bases selected for adversarial derivation are deterministically fixed
as the lowest permanent `base_id`s within each category from `data/raw/base_instances.jsonl`:

| PII Type | Pilot Pool Size | Quota | Selected `base_id`s |
|---|---|---|---|
| `PERSON` | 12 | 2 | `PERSON_001`, `PERSON_002` |
| `ADDRESS` | 12 | 2 | `ADDRESS_001`, `ADDRESS_002` |
| `PHONE` | 12 | 2 | `PHONE_001`, `PHONE_002` |
| `EMAIL` | 12 | 2 | `EMAIL_001`, `EMAIL_002` |
| `PAN` | 13 | 3 | `PAN_001`, `PAN_002`, `PAN_003` |
| `AADHAAR` | 13 | 3 | `AADHAAR_001`, `AADHAAR_002`, `AADHAAR_003` |
| `UPI_ID` | 13 | 3 | `UPI_ID_001`, `UPI_ID_002`, `UPI_ID_003` |
| `BANK_ACCOUNT` | 13 | 3 | `BANK_ACCOUNT_001`, `BANK_ACCOUNT_002`, `BANK_ACCOUNT_003` |
| **Total** | **100** | **20** | **20 bases total** |

### 14.6 Carrier Text Baseline *(added v0.18, resolves OQ-049)*

All 100 adversarial records are derived from the base's canonical English sentence
(`base.canonical_text`), isolating perturbation effects from linguistic code-mixing
confounds (Experiment E05).

### 14.7 Deterministic Transformation Specifications *(added v0.18, resolves OQ-049)*

Every transformation is strictly deterministic, non-random, and reproducible from the
base record alone with zero implementation discretion.

#### 14.7.1 A1 — SPACING (Severity 1, Target: VALUE)

- **Single-token values** (`PAN`, `AADHAAR`, `PHONE`, `EMAIL`, `UPI_ID`, `BANK_ACCOUNT`):
  `" ".join(c for c in base_pii_value)`
- **Multi-word values** (`PERSON`, `ADDRESS`):
  `"  ".join(" ".join(c for c in token) for token in base_pii_value.split(" "))`
  *(Single space between characters within a word; double space between words).*
- **Carrier assembly**: Replace `base_pii_value` in `base.canonical_text` with `realized_pii_value`.
- **Span behavior**: Span expands; offsets recomputed via occurrence walking.

#### 14.7.2 A2 — PUNCTUATION (Severity 1, Target: VALUE)

Inserts internal punctuation delimiters at fixed structural boundaries:
- `PAN`: `v[:5] + "-" + v[5:9] + "-" + v[9:]` (5-4-1 hyphenation)
- `AADHAAR`: `v[:4] + "-" + v[4:8] + "-" + v[8:]` (4-4-4 hyphenation)
- `PHONE`: `v[:5] + "-" + v[5:]` (5-5 hyphenation)
- `BANK_ACCOUNT`: `v[:4] + "-" + v[4:8] + "-" + v[8:]` (4-4-4 hyphenation)
- `PERSON`: `v.replace(" ", "-")` (word boundary hyphenation)
- `EMAIL`: `local[:-4] + "-" + local[-4:] + "@" + domain` (local-part hyphenation before numeric run)
- `UPI_ID`: `local[:5] + "-" + local[5:] + "@" + domain` (5-5 local phone VPA hyphenation)
- `ADDRESS`: `v.replace(", ", " / ")` (slash-delimited segments)
- **Carrier assembly**: Replace `base_pii_value` in `base.canonical_text` with `realized_pii_value`.

#### 14.7.3 A3 — LABEL_OBFUSCATION (Severity 1, Target: LABEL)

Replaces the exact carrier label prefix in `base.canonical_text`, holding `realized_pii_value == base_pii_value` byte-identical:
- `PERSON`: `"My name is "` → `"My N.A.M.E: "`
- `ADDRESS`: `"My address is "` → `"My A.D.D.R.E.S.S: "`
- `PHONE`: `"My phone number is "` → `"My P.H.O.N.E. No.: "`
- `EMAIL`: `"Email me at "` → `"E.M.A.I.L: "`
- `PAN`: `"My PAN number is "` → `"My P.A.N. No.: "`
- `AADHAAR`: `"My Aadhaar number is "` → `"My A.A.D.H.A.A.R. No.: "`
- `UPI_ID`: `"My UPI ID is "` → `"My U.P.I. I.D.: "`
- `BANK_ACCOUNT`: `"My bank account number is "` → `"My B.A.N.K. A/C No.: "`

#### 14.7.4 A4 — INFORMAL_ABBREVIATION (Severity 1, Target: LABEL)

Replaces the exact carrier label prefix in `base.canonical_text`, holding `realized_pii_value == base_pii_value` byte-identical:
- `PERSON`: `"My name is "` → `"name: "`
- `ADDRESS`: `"My address is "` → `"addr: "`
- `PHONE`: `"My phone number is "` → `"ph no: "`
- `EMAIL`: `"Email me at "` → `"mail: "`
- `PAN`: `"My PAN number is "` → `"pan no: "`
- `AADHAAR`: `"My Aadhaar number is "` → `"aadhaar no: "`
- `UPI_ID`: `"My UPI ID is "` → `"upi: "`
- `BANK_ACCOUNT`: `"My bank account number is "` → `"acct no: "`

#### 14.7.5 A5 — CHARACTER_VARIATION (Severity 1, Target: VALUE)

- **Alphanumeric & Text types** (`PAN`, `PERSON`, `ADDRESS`):
  `base_pii_value.lower()`
- **Email & UPI handles** (`EMAIL`, `UPI_ID`):
  `base_pii_value.upper()`
- **Numeric types** (`PHONE`, `AADHAAR`, `BANK_ACCOUNT`) — **M2 Single-Character OCR Substitution**:
  Scan the numeric string left-to-right. Replace **only the first occurrence** of a digit matching the OCR visual confusion map:
  `{'0': 'O', '1': 'l', '5': 'S', '8': 'B'}`
  Leave all remaining digits unchanged (exactly one character mutated per numeric entity).
- **Carrier assembly**: Replace `base_pii_value` in `base.canonical_text` with `realized_pii_value`.

### 14.8 Metadata and Naming Convention *(added v0.18, resolves OQ-049)*

- `variant_id`: `"{base_id}_EN_{family}_01"` (e.g. `PAN_001_EN_A1_01`, `PERSON_001_EN_A3_01`).
- `difficulty`: `"ADVERSARIAL"`.
- `perturbation`: `{"family": "{family}", "type": "{type}", "severity": 1, "target": "{target}"}`.
- `distractors`: `[]`.
- `language`: `"EN"`, `carrier_script`: `"LATIN"`, `context`: `"EXPLICIT"`.

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
  "guidelines_version": "0.11",
  "template_id": "HINGLISH_PAN_03",
  "seed": 42,

  "validation": {
    "structural": "PENDING",
    "span": "PENDING",
    "semantic": "PENDING",
    "language": "PENDING",
    "duplicate": "PENDING",
    "human": "PENDING"
  },
  "validation_status": "PENDING",
  "review_status": "PENDING",
  "split": null
}
```

The example above is a **perturbed** record — its `variant_id` (`PAN_001_HINGLISH_A1_01`)
and non-`NONE` `perturbation` block only apply to perturbed records (§4.16). A **clean
(unperturbed)** record, same base, `EN` condition, looks like this instead:

```json
{
  "base_id": "PAN_001",
  "variant_id": "PAN_001_EN",

  "text": "My PAN number is ABCDE1234F.",

  "entities": [
    {
      "type": "PAN",
      "base_pii_value": "ABCDE1234F",
      "realized_pii_value": "ABCDE1234F",
      "pii_script": "LATIN",
      "start": 17,
      "end": 27,
      "occurrence_index": 0
    }
  ],

  "distractors": [],

  "language": "EN",
  "carrier_script": "LATIN",
  "context": "EXPLICIT",
  "domain": "ACCOUNT_VERIFICATION",

  "perturbation": {
    "family": "NONE",
    "type": "NONE",
    "severity": 0,
    "target": "NONE"
  },

  "difficulty": "EASY",
  "address_structure": null,
  "hi_variant_collapsed": false,

  "synthetic": true,

  "generator_version": "0.1.0",
  "guidelines_version": "0.11",
  "template_id": "EN_PAN_TEMPLATE",
  "seed": 42,

  "validation": {
    "structural": "PENDING",
    "span": "PENDING",
    "semantic": "PENDING",
    "language": "PENDING",
    "duplicate": "PENDING",
    "human": "PENDING"
  },
  "validation_status": "PENDING",
  "review_status": "PENDING",
  "split": null
}
```

Note `variant_id` has no perturbation suffix, `perturbation` is all `NONE`, and
`difficulty` is `EASY` (§13.1: `C1` + clean + `EN`/`IN_EN`) rather than `ADVERSARIAL`.

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

## 21. Frozen decisions (v0.1–v0.11)

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
15. **`validation{}` carries six per-layer status keys** — `structural`, `span`,
    `semantic`, `language`, `duplicate`, `human` — matching PROJECT_SPEC.md §15's six
    validation layers exactly. *(v0.2, resolves OQ-001: the v0.1 worked example omitted
    `duplicate`.)*
16. **Every base instance declares `base_kind`** (`POSITIVE` | `HARD_NEGATIVE`, §13.4).
    `POSITIVE` requires `pii` non-empty; `HARD_NEGATIVE` requires `pii == []`.
    `base_id` naming conventions must never be used to infer `base_kind`. Distractor
    information stays on the derived record, never the base instance. *(v0.3, resolves
    OQ-003.)*
17. **AADHAAR and BANK_ACCOUNT pilot representations are BENCHMARK_SYNTHETIC** (§11.4):
    exactly 12 decimal digits each, uniform random, no checksum or issuance-range
    validation. Explicitly **not** claimed as the official or universal real-world format
    for either type. *(v0.4, resolves OQ-004 and OQ-005.)*
18. **UPI_ID pilot representation is BENCHMARK_SYNTHETIC, one fixed grammar** (§10.3):
    `<10-digit-synthetic-phone>@mail.test`. Deliberately dotted (unlike a real,
    undotted PSP suffix) to create controlled surface-form collision with EMAIL, per
    PROJECT_SPEC.md §7's design intent. No real PSP handle or domain is used. No
    checksum or payment-validation logic. *(v0.5, resolves OQ-006.)*
19. **`semantic_role` is type-fixed and describes the PII value itself; `scenario.domain`
    / `scenario.purpose` carry contextual use** (§13.5). PERSON's frozen role is
    `PERSON_NAME`, not `ACCOUNT_HOLDER_NAME` — domain-neutral, so it doesn't imply an
    account relationship for every PERSON base regardless of scenario. *(v0.6, resolves
    OQ-007.)*
20. **PHONE's base representation is frozen** as `^[6789][0-9]{9}$` — 10 digits, first
    digit 6–9, no formatting (§8.1). Formatted spans (`+91`, spacing, hyphens) remain a
    realization/perturbation-layer concern, unaffected by this. *(v0.7, resolves
    OQ-008.)*
21. **EMAIL's T05 structural grammar is frozen** (§9.1): exactly one `@`, non-empty
    local part, domain ending in an exact-lowercase `.test`/`.invalid`/`.example`. Not
    full RFC validation; no additional local-part restrictions. *(v0.7, resolves
    OQ-009.)*
22. **PAN's structural representation is uppercase-only** — `^[A-Z]{5}[0-9]{4}[A-Z]$`
    (§11.5). Lowercase is structurally invalid. No checksum/issuance/category
    validation. *(v0.7, resolves OQ-010.)*
23. **EMAIL and UPI_ID reserved domains are matched as exact lowercase strings, never
    normalized** (§9.1, §10.4). A value failing UPI_ID's grammar (e.g.
    `9876543210@paytm`) is structurally invalid *because it doesn't match the frozen
    grammar* — never described as invalid because it resembles a real PSP handle.
    *(v0.7, resolves OQ-011.)*
24. **The transliteration table is a token-level lookup, not an algorithm** — no
    character-level substitution, no LLM, no probabilistic method, no external
    general-purpose transliteration tool (§4.7). Benchmark-specific ground truth, not a
    general Hindi transliteration system. *(v0.8, resolves OQ-016.)*
25. **Every ADDRESS lexical component reachable from the frozen generator needs an
    explicit table entry; numerals stay ASCII, unconverted** (§4.8). No rule is invented
    for unreachable ADDRESS forms. *(v0.8, resolves OQ-017.)*
26. **A transliteration lookup miss fails closed** — deterministic error, reject/log,
    never guess, never call an LLM or external service, never pass the token through
    untranslated (§4.9). *(v0.8, resolves OQ-018.)*
27. **No external transliteration library is used for T07, at build time or runtime.**
    The frozen pilot table is itself the transliteration ground truth (§4.7). *(v0.8,
    resolves OQ-019.)*
28. **`generator_version` is a required field on the base instance schema** (§4.5),
    identical name/pattern to the record schema's existing field — one toolchain
    version covering PII generation, base-instance assembly, and the transliteration
    table. *(v0.9, resolves OQ-020.)*
29. **ADDRESS's Devanagari form is never cached on the base instance** (§4.4) — no
    `address_deva`-equivalent field exists; only `person_context.name_deva` is stored at
    base-instance level. ADDRESS's Devanagari form is generated later, at
    record-derivation time, as `realized_pii_value`. *(v0.9, resolves OQ-021.)*
30. **`ABC` → `एबीसी` and `MG` → `एमजी` are frozen, benchmark-specific transliteration
    conventions** (§4.8) — not claims about universal correct transliteration of these
    abbreviations. *(v0.9, resolves OQ-022.)*
31. **T07 owns PII transliteration only; T08 owns carrier-sentence construction**
    (§4.10). No general-purpose Hindi transliteration system is built. *(v0.10,
    resolves OQ-026.)*
32. **`HI_LATIN_PII` and `HI_DEVA_PII` must use byte-identical carrier text** (§4.11) —
    the only permitted difference is the PII value's script. *(v0.10.)*
33. **`IN_EN` requires at least one marker from a frozen 8-item Indian-English
    inventory** (§4.12); `EN` requires zero. These are legitimate dialectal features,
    not errors. *(v0.10, resolves OQ-023.)*
34. **`ROM_HI` is restricted to a frozen 8-item ordinary-loanword inventory;
    `HINGLISH` requires at least one insertion beyond it, from a frozen insertion
    inventory** (§4.13) — a closed-set membership test, not an LLM classification.
    *(v0.10, resolves OQ-024.)*
35. **`INFORMAL_HINGLISH` requires `HINGLISH`'s mixing plus at least one marker from
    four frozen informal-register categories** (§4.14). *(v0.10, resolves OQ-025.)*
36. **`pii_script` is determined from the realized span's actual script composition,
    never from the PII type name** (§4.15): PERSON/ADDRESS follow condition (`LATIN`
    except `DEVANAGARI` under `HI_DEVA_PII`); PHONE/AADHAAR/BANK_ACCOUNT are `NUMERIC`;
    PAN/EMAIL are `LATIN`; UPI_ID is `MIXED` (numeric local part + Latin domain). No new
    enum value introduced. *(v0.11, resolves OQ-013.)*
37. **Clean (unperturbed) `variant_id` format is `{base_id}_{language}`, no
    perturbation suffix** (§4.16); clean records carry `perturbation.family/type/target
    = "NONE"`. §17's existing `PAN_001_HINGLISH_A1_01` example is specifically a
    perturbed-record ID and does not define the clean-record format — §17 now shows
    both. *(v0.11, resolves OQ-014.)*
38. **Every T08 clean record carries `context: "EXPLICIT"`** (§4.17) — not a redesign
    of the C1–C4 allocation in PROJECT_SPEC.md §9.1, which governs a separate, later
    pipeline stage. *(v0.11, resolves OQ-027.)*
39. **The complete eight-type `semantic_role` mapping is frozen** (§13.5): `PERSON` →
    `PERSON_NAME`, `ADDRESS` → `DELIVERY_ADDRESS`, `PHONE` → `CONTACT_NUMBER`, `EMAIL` →
    `CONTACT_EMAIL`, `PAN` → `TAX_IDENTIFIER`, `AADHAAR` → `NATIONAL_ID_IDENTIFIER`,
    `UPI_ID` → `PAYMENT_IDENTIFIER`, `BANK_ACCOUNT` → `PAYMENT_ACCOUNT_IDENTIFIER`.
    Ratifies values already in effect since T04; changes none of them. *(v0.12, resolves
    OQ-035.)*
40. **Layer 3 semantic-use ground truth for unperturbed `EN` records is exact equality
    between `record.text` and the source base's `canonical_text`** (§13.6) — no keyword
    list, no LLM judge, no reuse of the T08 carrier templates as a hidden oracle. Covers
    only `language == "EN"`, `context == "EXPLICIT"`, `perturbation.family == "NONE"`;
    the other six language conditions remain unresolved for text-content-level Layer 3
    checking (OQ-037). *(v0.12, resolves OQ-036.)*
41. **Layer 3 semantic-use ground truth for the remaining six conditions is frozen**
    (§13.7): `IN_EN` requires `base.canonical_text` as a substring of `record.text`;
    `ROM_HI`/`HINGLISH`/`INFORMAL_HINGLISH`/`HI_LATIN_PII`/`HI_DEVA_PII` require presence
    of a frozen, already-documented per-type label word (Romanized or Devanagari, by
    register) drawn from §4.10/§4.13, assembled into one table for validation use, not
    newly chosen. Verified against all 624 frozen records, zero failures. A miss is
    `SEMANTIC_MISMATCH` (`IN_EN`) or `ROLE_UNSUPPORTED_BY_TEXT` (the other five) — the
    latter reason code's first validator implementation. Does not reuse the T08 carrier
    templates or the generator's type→template association as an oracle. *(v0.13,
    resolves OQ-037.)*
42. **Four of the six hard-negative decoy classes get a frozen construction rule**
    (§13.8) — `NUMERIC_SHAPE`, `ALNUM_SHAPE`, `PARTIAL_PII` reuse T05's frozen PHONE/
    AADHAAR/BANK_ACCOUNT/PAN structural formats; `NAME_AS_PLACE` reuses T03's frozen
    PERSON given-name vocabulary plus the one exact suffix (`Nagar`) already shown in
    both §6 and §13.3's worked examples. `HANDLE_SHAPE` and `ORG_AS_PERSON` are
    explicitly left unresolved — neither has any concrete worked value in either
    governing document to construct a rule from. *(v0.14, partially resolves OQ-042.)*
43. **The 20 hard-negative bases split 4/4/3/3/3/3 across the six decoy classes**
    (§13.9), remainder assigned by §13.3's own table order — a content-free tie-break,
    not a claim about which classes matter more. *(v0.14, resolves OQ-043.)*
44. **Every hard-negative derived record carries `context: "EXPLICIT"`** (§13.10), by
    direct analogy to decision 38's identical T08 positive-record freeze — not a
    redesign of PROJECT_SPEC.md §9.1's C1–C4 allocation, which is defined in terms of
    PII-role explicitness a decoy does not have. *(v0.14, resolves OQ-045.)*
45. **`HANDLE_SHAPE` is frozen as EMAIL's own `_LOCAL_PART_WORDS`/`_DOMAIN_LABELS`
    construction with the reserved TLD omitted** (§13.8) — genuinely fails both
    EMAIL's and UPI_ID's frozen structural regexes; does not change either type's own
    generation rule. *(v0.15, resolves OQ-042 for this class.)*
46. **`ORG_AS_PERSON` is deferred from Pilot v0.1, not resolved** (§13.8) — no
    concrete worked value or construction pattern exists anywhere in either governing
    document, and none is invented. Its 3-base allocation is redistributed, by the
    same table-order tie-break decision 43 already established, to `NUMERIC_SHAPE`
    (+1), `ALNUM_SHAPE` (+1), `NAME_AS_PLACE` (+1) (§13.9). The six-decoy-class design
    intent is preserved as history; Pilot v0.1's actual hard-negative set covers five.
    *(v0.15, OQ-042's remaining half — explicitly not a constructive resolution.)*
47. **Hard-negative derived records use six realizations, not seven** (§13.11): `EN`,
    `IN_EN`, `ROM_HI`, `HINGLISH`, `INFORMAL_HINGLISH`, and one collapsed Hindi
    realization — a deliberate extension of §8.1's PII-script-isolation rationale to
    `HARD_NEGATIVE` bases (which have no PII value and therefore no script axis at
    all), not a claim that §8.1's own text names hard negatives. 20 bases × 6 = 120
    hard-negative derived records. *(v0.15, resolves OQ-044.)*
48. **`hard_negative_decoy` is added to `schemas/base_instance.schema.json` as an
    optional field** (§13.12): construction-level ground truth for a `HARD_NEGATIVE`
    base's single decoy (`decoy_class`, `value`, `surface_type`, `actual_role`), not
    in the schema's top-level `required` array so the 100 existing `POSITIVE` bases
    remain valid and unchanged. Its presence-versus-base_kind relationship is a
    cross-field rule enforced by `validators/base_kind.py`, not by the schema, for
    consistency with the base_kind/`pii` invariant's own precedent (decision 16) —
    not because JSON Schema 2020-12 is incapable of expressing it. Does not change
    `pii[]` staying empty or `entities[]`/`distractors[]` staying derived-record-only.
    *(v0.16, resolves OQ-046.)*
49. **A closed, benchmark-specific Hindi/Hinglish lexical inventory is frozen for
    hard-negative carrier construction** (§13.13): four new concept words ("order,"
    "reference code," "station," "contact") plus one new per-class carrier template
    each, explicitly labeled apart from the words already frozen elsewhere ("mera,"
    "hai," "number," "account," "ke paas") that these templates reuse. `HINGLISH`/
    `INFORMAL_HINGLISH` construction reuses the existing, generic §4.13/§4.14
    transformation mechanisms unchanged — no additional vocabulary beyond `ROM_HI`'s
    own. Not a general-purpose Hindi translation system — a small, closed inventory
    scoped exactly to the five constructible decoy classes. *(v0.17, resolves
    OQ-047.)*
50. **The complete T12 adversarial perturbation specification is frozen** (§14.5–§14.8):
    20 positive bases selected deterministically (lowest `base_id`s: 3 each for `PAN`,
    `AADHAAR`, `UPI_ID`, `BANK_ACCOUNT`; 2 each for `PERSON`, `ADDRESS`, `PHONE`, `EMAIL`);
    all 100 variants derived from standard English canonical carrier text (`base.canonical_text`);
    exact deterministic transformation algorithms frozen for $A_1$ (intra-word single, inter-word double space),
    $A_2$ (fixed per-type delimiters including `EMAIL` local hyphenation and `UPI_ID` 5-5 hyphenation),
    $A_3$ (exact prefix obfuscation mapping), $A_4$ (exact informal prefix abbreviation mapping),
    and $A_5$ (casing for alphanumeric/text; M2 single-character OCR substitution `{'0': 'O', '1': 'l', '5': 'S', '8': 'B'}` for numeric types);
    metadata format `{base_id}_EN_{family}_01`, `difficulty: "ADVERSARIAL"`. *(v0.18, resolves OQ-049.)*

---

## 22. Version

```
guidelines_version: 0.18
supersedes:        0.17
changelog:         annotation/CHANGELOG.md
```

Any change to span boundaries, PII definitions, ambiguity handling, script policy,
context-level scoring, or adversarial validity **requires a version increment**.

Records store the `guidelines_version` under which they were annotated. Records
annotated under different versions must not be pooled in a single experiment without an
explicit re-validation pass.
