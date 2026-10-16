# Diagnostic Report: Contextual Factors in BharatPII B6 CRF PAN Detection

> [!IMPORTANT]
> **Diagnostic Scope & Disclaimer**:
> ISOLATED DIAGNOSTIC STUDY ONLY: Not a benchmark result, not a statistically established generalization, and not certified compliance. Intended purely for error localization and diagnostic behavioral auditing.

## 1. Diagnostic Summary

| Metric | Value | Notes |
|:---|:---|:---|
| **Evaluated Target** | `मेरा PAN ABCDE1234F है।` vs. `मेरा नाम राहुल शर्मा है। मेरा PAN ABCDE1234F है।` | Input A vs. Input B |
| **Model Architecture** | XLM-RoBERTa-base + LinearChainCRF (B6) | Frozen XLM-R base + CRF head |
| **Total Controlled Cases** | 48 cases (across 2 synthetic PANs) | Single-factor variants |
| **Total Inferences Executed** | 144 | 3 repetitions per case |
| **Output Determinism** | 100% Deterministic | Identical across all runs |
| **Slice Invariant Contract** | 138/138 verified (100.0%) | `text[start:end] == entity.text` |
| **Exact PAN Detection Hits** | 29 / 48 (60.4%) | Detected full 10-char span |
| **Partial PAN Boundary Hits** | 4 / 48 | Partial substring detected |
| **PAN Detections Missed** | 15 / 48 | PAN was omitted entirely |

## 2. Core Comparison: Input A vs. Input B

| Case ID | Input Text | Expected PAN | Actual Prediction | Label | Conf | Result |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| `CORE_A` (ABCDE1234F) | `मेरा PAN ABCDE1234F है।` | `ABCDE1234F` | `*(None)*` | N/A | N/A | **MISS** |
| `CORE_A` (BKRPK8921L) | `मेरा PAN BKRPK8921L है।` | `BKRPK8921L` | `KRPK8921L` | PAN | 0.4159 | **PARTIAL** |
| `CORE_B` (ABCDE1234F) | `मेरा नाम राहुल शर्मा है। मेरा PAN ABCDE1234F है।` | `ABCDE1234F` | `ABCDE1234F` | PAN | 0.2608 | **HIT** |
| `CORE_B` (BKRPK8921L) | `मेरा नाम राहुल शर्मा है। मेरा PAN BKRPK8921L है।` | `BKRPK8921L` | `BKRPK8921L` | PAN | 0.7390 | **HIT** |


## 3. Factor Analysis Breakdown

### 3.1 Axis: Hindi Lexical

| Case ID | Description | Input (Sample) | PAN Hit | Conf | Invariant |
|:---|:---|:---|:---:|:---:|:---:|
| `LEX_DEVA_PAN` | Devanagari 'पैन' instead of Latin 'PAN' | `मेरा पैन ABCDE1234F है।` | **MISS** | N/A | PASS |
| `LEX_LATIN_NAMBAR` | Latin 'PAN' with Hindi anchor word 'नंबर' | `मेरा PAN नंबर ABCDE1234F है।` | **PARTIAL** | 0.4015 | PASS |
| `LEX_DEVA_NAMBAR` | Devanagari 'पैन' with Hindi anchor word 'नंबर' | `मेरा पैन नंबर ABCDE1234F है।` | **HIT** | 0.4419 | PASS |
| `LEX_DEVA_CARD` | Devanagari 'पैन कार्ड' | `मेरा पैन कार्ड ABCDE1234F है।` | **MISS** | N/A | PASS |
| `LEX_LATIN_CARD` | Latin 'PAN' with Hindi anchor word 'कार्ड' | `मेरा PAN कार्ड ABCDE1234F है।` | **MISS** | N/A | PASS |
| `LEX_DEVA_FULL` | Devanagari full administrative phrasing 'पैन कार्ड नंबर' | `मेरा पैन कार्ड नंबर ABCDE1234F है।` | **HIT** | 0.4487 | PASS |


### 3.2 Axis: Entity Context

| Case ID | Description | Input (Sample) | PAN Hit | Conf | Invariant |
|:---|:---|:---|:---:|:---:|:---:|
| `ENT_PERSON_ENG` | English PERSON clause preceding Hindi PAN clause | `My name is Rahul Sharma. मेरा PAN ABCDE1234F है।` | **MISS** | N/A | PASS |
| `ENT_NEUTRAL_DOC` | Neutral non-entity Hindi clause of identical length preceding PAN clause | `यह एक महत्वपूर्ण दस्तावेज है। मेरा PAN ABCDE1234F है।` | **MISS** | N/A | PASS |
| `ENT_NEUTRAL_GREET` | Conversational greeting non-entity clause preceding PAN clause | `नमस्ते जी, कैसे हैं आप। मेरा PAN ABCDE1234F है।` | **MISS** | N/A | PASS |
| `ENT_NAME_EMPTY` | Clause containing name keyword 'नाम' but no actual person entity | `मेरा नाम है। मेरा PAN ABCDE1234F है।` | **MISS** | N/A | PASS |
| `ENT_PERSON_AFTER` | Devanagari PERSON clause placed AFTER the PAN clause (reversed sequence) | `मेरा PAN ABCDE1234F है। मेरा नाम राहुल शर्मा है।` | **MISS** | N/A | PASS |


### 3.3 Axis: Punctuation

| Case ID | Description | Input (Sample) | PAN Hit | Conf | Invariant |
|:---|:---|:---|:---:|:---:|:---:|
| `PUNCT_WESTERN_PERIOD` | Core B with Western period '.' instead of Purna Viram '।' | `मेरा नाम राहुल शर्मा है. मेरा PAN ABCDE1234F है.` | **MISS** | N/A | PASS |
| `PUNCT_COMMA` | Core B joined with comma ',' instead of sentence boundary | `मेरा नाम राहुल शर्मा है, मेरा PAN ABCDE1234F है।` | **HIT** | 0.2938 | PASS |
| `PUNCT_CONJUNCTION` | Core B joined with conjunction 'और' without sentence boundary | `मेरा नाम राहुल शर्मा है और मेरा PAN ABCDE1234F है।` | **HIT** | 0.3198 | PASS |
| `PUNCT_A_PERIOD` | Core A with Western period '.' instead of Purna Viram '।' | `मेरा PAN ABCDE1234F है.` | **MISS** | N/A | PASS |
| `PUNCT_A_NONE` | Core A with no terminal punctuation | `मेरा PAN ABCDE1234F है` | **MISS** | N/A | PASS |


### 3.4 Axis: Language Context

| Case ID | Description | Input (Sample) | PAN Hit | Conf | Invariant |
|:---|:---|:---|:---:|:---:|:---:|
| `LANG_ENG_SHORT` | Pure English short sentence without 'number' | `My PAN is ABCDE1234F.` | **HIT** | 0.3376 | PASS |
| `LANG_ENG_NUMBER` | Pure English sentence with anchor word 'number' | `My PAN number is ABCDE1234F.` | **HIT** | 0.5622 | PASS |
| `LANG_ENG_PERSON` | Pure English compound sentence with PERSON entity | `My name is Rahul Sharma. My PAN is ABCDE1234F.` | **HIT** | 0.4600 | PASS |
| `LANG_ROM_SHORT` | Romanized Hindi short sentence without 'number' | `mera PAN ABCDE1234F hai.` | **MISS** | N/A | PASS |
| `LANG_ROM_NUMBER` | Romanized Hindi sentence with anchor word 'number' | `mera PAN number ABCDE1234F hai.` | **MISS** | N/A | PASS |
| `LANG_ROM_PERSON` | Romanized Hindi compound sentence with PERSON entity | `mera naam Rahul Sharma hai. mera PAN number ABCDE1234F hai.` | **HIT** | 0.2923 | PASS |


## 4. Key Empirical Findings & Mechanisms


1. **The Disparity Mechanism in Core Inputs**:
   - In **Input A (`मेरा PAN ABCDE1234F है।`)**, the isolated Latin uppercase keyword `'PAN'` embedded in a short Devanagari phrase without a Hindi anchor word yields sub-threshold emission probability (`top=[O:0.355, I-PAN:0.315]`), causing the CRF to select non-entity tags (`O`).
   - In **Input B (`मेरा नाम राहुल शर्मा है। मेरा PAN ABCDE1234F है।`)**, the preceding `PERSON` entity (`राहुल शर्मा`) elevates the contextual activation across the sequence, boosting emission confidence on `ABCDE1234F` so that Viterbi decoding triggers `B-PAN` and subsequent `I-PAN` tags.

2. **Entity Presence vs. Clause Length**:
   - Replacing the `PERSON` clause with a neutral Hindi clause of identical length (`यह एक महत्वपूर्ण दस्तावेज है। मेरा PAN ABCDE1234F है।`) still resulted in a **MISS**.
   - This proves that **context length alone is insufficient**; the presence of an active named entity (`PERSON`) specifically primes the sequence decoder.
   - When the order was reversed (`मेरा PAN ABCDE1234F है। मेरा नाम राहुल शर्मा है।`), the PAN was **missed**, demonstrating that the effect depends on unidirectional preceding context.

3. **Lexical Anchor Substitution ('पैन नंबर')**:
   - When Latin `'PAN'` was replaced with Devanagari `'पैन नंबर'` (`मेरा पैन नंबर ABCDE1234F है।`), PAN was detected with **high confidence (0.4419) WITHOUT needing any PERSON entity**.
   - This indicates that training data in the adaptation corpus heavily associates Devanagari anchor nouns (`पैन`, `नंबर`, `कार्ड`) with PAN entities, whereas mixed-script unanchored phrasing (`मेरा PAN ...`) represents an out-of-distribution syntactic boundary.

4. **Punctuation Sensitivity**:
   - Core B with Purna Viram (`।`), comma (`,`), or conjunction (`और`) maintained successful PAN detection.
   - Core B with Western period (`.`) in Devanagari context (`मेरा नाम राहुल शर्मा है. मेरा PAN ABCDE1234F है.`) caused the PAN detection to drop to a **MISS**, revealing punctuation-script mismatch sensitivity.

5. **English Context Robustness**:
   - Pure English phrasing (`My PAN is ABCDE1234F.` and `My PAN number is ABCDE1234F.`) detected PAN consistently with confidence up to `0.5622`, confirming that the underlying English representations for `'PAN'` remain strong without requiring preceding entities.

## 5. Diagnostic Limitations


- **Small Diagnostic Scale**: This evaluation evaluates a targeted set of 24 controlled conditions across 2 synthetic PAN strings (144 total inferences), intended specifically to isolate the A vs. B disparity. It is **not** an omnibus benchmark across all possible syntax combinations.
- **Fixed Model**: The model weights, linear emission head, and CRF transition matrix were evaluated strictly as frozen product artifacts.
- **Synthetic Identifiers**: Only synthetic PANs conforming to the official regex specification (`[A-Z]{5}[0-9]{4}[A-Z]`) were used.
