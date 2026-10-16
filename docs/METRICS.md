# Authoritative Benchmark Metric Definitions & Invariants
**Document Identifier**: `DOCS-METRICS-V1.0`  
**Benchmark Version**: `0.18`  
**Status**: APPROVED  
**Date**: September 9, 2026  

---

## 1. Mathematical Foundations & Matching Protocol

Let $D$ be the benchmark corpus consisting of $N = 964$ records. For each record $r \in D$:
- $G_r = \{(s_i, e_i, t_i)\}$ is the set of gold standard PII entities, where $s_i$ is the character start offset, $e_i$ is the character end offset, and $t_i \in \mathcal{T}$ is the PII type.
- $P_r = \{(\hat{s}_j, \hat{e}_j, \hat{t}_j)\}$ is the set of predicted entities emitted by the evaluated model.
- $N_{gold} = \sum_{r \in D} |G_r| = 724$ (total benchmark gold entities).
- $N_{pred} = \sum_{r \in D} |P_r|$ (total predictions emitted by the model).

For each record, maximum-weight bipartite matching is performed between gold entities $g \in G_r$ and predicted entities $p \in P_r$ based on character intersection.

---

## 2. Match Classifications

1. **Exact Match ($TP_{exact}$)**:
   $$\hat{s}_j = s_i \quad \land \quad \hat{e}_j = e_i \quad \land \quad \hat{t}_j = t_i$$
   The prediction matches the gold span start, end, and entity type identically.

2. **Type-Strict Match ($TP_{type}$)**:
   $$\hat{t}_j = t_i \quad \land \quad \max(s_i, \hat{s}_j) < \min(e_i, \hat{e}_j)$$
   The prediction has the correct entity type and non-zero character overlap with the gold entity.

3. **Localized Match**:
   $$\max(s_i, \hat{s}_j) < \min(e_i, \hat{e}_j)$$
   Any non-zero character overlap between prediction and gold entity regardless of type agreement.

---

## 3. Exhaustive Error Partitions

Every gold entity and every prediction is uniquely partitioned into one of the following mutually exclusive error categories:

- **$F_1$ Missed Entities (False Negative)**: A gold entity $g \in G_r$ with zero character overlap with any prediction in $P_r$.
- **$F_2$ Wrong Span (Boundary Error)**: A gold entity $g \in G_r$ that overlaps with a prediction having correct type ($\hat{t}_j = t_i$), but mismatched character boundaries ($(\hat{s}_j, \hat{e}_j) \neq (s_i, e_i)$).
- **$F_3$ Wrong Type (Classification Error)**: A gold entity $g \in G_r$ that overlaps with a prediction of the wrong entity type ($\hat{t}_j \neq t_i$).
- **$F_4$ False Positives (Spurious Extractions)**: A prediction $p \in P_r$ that has zero overlap with any gold entity, or excess redundant predictions overlapping an already matched gold entity.

---

## 4. Non-Negotiable Mathematical Invariants

The benchmark guarantees the following identities across all evaluations:

1. **Gold Partition Invariant**:
   $$TP_{exact} + F_1 + F_2 + F_3 = N_{gold} = 724$$

2. **Type-Strict Decomposition**:
   $$TP_{type} = TP_{exact} + F_2$$

3. **Prediction Accounting Invariant**:
   $$N_{pred} = TP_{type} + F_3 + F_4$$

---

## 5. Formal Metric Formulations

### 5.1 Primary Rate Metrics ($M_1$ through $M_6$)

| Metric Identifier | Mathematical Definition | Interpretation |
| :--- | :--- | :--- |
| **$M_1$ Precision (Type-Strict)** | $\frac{TP_{type}}{N_{pred}} = \frac{TP_{type}}{TP_{type} + F_3 + F_4}$ | Proportion of emitted predictions that correctly localize and identify a PII type. |
| **$M_2$ Recall (Type-Strict)** | $\frac{TP_{type}}{N_{gold}} = \frac{TP_{type}}{TP_{exact} + F_1 + F_2 + F_3}$ | Proportion of gold standard PII entities successfully detected with correct type. |
| **$M_3$ F1 Score (Type-Strict)** | $\frac{2 \cdot M_1 \cdot M_2}{M_1 + M_2} = \frac{2 \cdot TP_{type}}{N_{pred} + N_{gold}}$ | Harmonic mean of Type-Strict Precision and Recall. |
| **$M_4$ Exact F1 Score** | $\frac{2 \cdot P_{exact} \cdot R_{exact}}{P_{exact} + R_{exact}} = \frac{2 \cdot TP_{exact}}{N_{pred} + N_{gold}}$ | Harmonic mean requiring exact character span boundary and type match. |
| **$M_5$ Type Accuracy** | $\frac{TP_{type}}{TP_{type} + F_3} = \frac{TP_{type}}{\text{Localized Matches}}$ | Conditional classification accuracy given that an entity was localized. |
| **$M_6$ False Positive Rate** | $\frac{F_4}{N_{pred}}$ | Fraction of all emitted predictions that are completely spurious. |

### 5.2 Hard-Negative Decoy False Positive Rate
For the subset of $N_{HN} = 50$ pure hard-negative records containing zero gold entities:
$$FPR_{HN} = \frac{\sum_{r \in D_{HN}} \mathbb{I}(|P_r| > 0)}{N_{HN}}$$
A system achieves $FPR_{HN} = 0.0$ only if it successfully suppresses predictions on all decoy records.
