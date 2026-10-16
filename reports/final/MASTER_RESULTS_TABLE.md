# Indian PII Robustness Benchmark — Master Results Table

**Benchmark Version**: 0.18 | **Canonical Evaluation Records**: 964 | **Total Gold Entities ($N_{gold}$)**: 724

> **Note on Methodology**: Single-run baselines (B1–B4) are evaluated once on the canonical benchmark (deterministic or pretrained zero-shot). Adapted baselines (B5 and B6) are evaluated across three random adaptation seeds ($S \in \{42, 43, 44\}$) and reported as Mean ± Standard Deviation. Exact boundary evaluation requires character-level span match `(start, end, type)`.

### Primary Performance Metrics

| ID | Baseline System | Mode | M1 Precision | M2 Recall | M3 F1 (Type-Strict) | M4 Exact F1 | M5 Type Acc | M6 FPR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **B1** | Regex (Canonical) | Single-run (Deterministic) | 0.6478 | 0.5207 | 0.5773 | **0.5773** | 0.8491 | 0.2371 |
| **B2** | spaCy en_core_web_sm | Single-run (Pretrained) | 0.0315 | 0.0608 | 0.0415 | **0.0330** | 0.0854 | 0.6316 |
| **B3** | Microsoft Presidio (IN enabled) | Single-run (Hybrid Rules+spaCy) | 0.0766 | 0.2956 | 0.1217 | **0.1149** | 0.3115 | 0.7539 |
| **B4** | XLM-RoBERTa Zero-Shot NER | Single-run (Pretrained Zero-shot) | 0.2013 | 0.1298 | 0.1579 | **0.1444** | 0.5081 | 0.6039 |
| **B5** | Indian-Adapted XLM-RoBERTa | Mean ± SD (3 seeds) | 0.4312 ± 0.0030 | 0.9742 ± 0.0008 | 0.5978 ± 0.0029 | **0.3860 ± 0.0061** | 0.9756 ± 0.0008 | 0.5580 ± 0.0032 |
| **B6** | Indian-Adapted XLM-RoBERTa + Linear CRF | Mean ± SD (3 seeds) | 0.6315 ± 0.0021 | 0.9319 ± 0.0035 | 0.7528 ± 0.0022 | **0.6654 ± 0.0034** | 0.9414 ± 0.0028 | 0.3292 ± 0.0025 |

### Error Partition Matrix (Authoritative Invariant: $TP_{exact} + F_1 + F_2 + F_3 = N_{gold} = 724$)

| ID | Baseline System | $TP_{exact}$ | $TP_{type}$ | $F_1$ Missed | $F_2$ Wrong Span | $F_3$ Wrong Type | $F_4$ False Pos |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **B1** | Regex (Canonical) | 377 | 377 | 280 | 0 | 67 | 138 |
| **B2** | spaCy en_core_web_sm | 35 | 44 | 209 | 9 | 471 | 883 |
| **B3** | Microsoft Presidio (IN enabled) | 202 | 214 | 37 | 12 | 473 | 2105 |
| **B4** | XLM-RoBERTa Zero-Shot NER | 86 | 94 | 539 | 8 | 91 | 282 |
| **B5** | Indian-Adapted XLM-RoBERTa | 455.3 ± 4.1 | 705.3 ± 0.5 | 1.0 ± 0.0 | 250.0 ± 4.1 | 17.7 ± 0.5 | 912.7 ± 9.5 |
| **B6** | Indian-Adapted XLM-RoBERTa + Linear CRF | 596.3 ± 3.7 | 674.7 ± 2.1 | 7.7 ± 0.9 | 78.3 ± 1.7 | 41.7 ± 1.2 | 351.7 ± 3.7 |
