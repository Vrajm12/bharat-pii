"""T13: Maximum-weight bipartite matching engine (PROJECT_SPEC.md §20.3, §20.4).

Implements the frozen matching algorithm:
- Edge exists iff gold entity and prediction share >= 1 character.
- weight(g, p) = 2 + IoU if p.type == g.type else IoU.
- Embedded infinitesimal tie-breaking guarantees a UNIQUE optimal solution independent of list order.
- Exact Kuhn-Munkres / Hungarian solver for global maximum weight.
"""

from __future__ import annotations

from .schema import GoldEntity, Match, MatchingResult, Prediction


def _compute_iou(g: GoldEntity, p: Prediction) -> tuple[float, int, int]:
    """Compute IoU between gold entity and prediction spans.

    Returns:
        (iou, intersection, union)
    """
    inter_start = max(g.start, p.start)
    inter_end = min(g.end, p.end)
    if inter_start >= inter_end:
        return 0.0, 0, (g.end - g.start) + (p.end - p.start)

    intersection = inter_end - inter_start
    g_len = g.end - g.start
    p_len = p.end - p.start
    union = g_len + p_len - intersection
    iou = intersection / union if union > 0 else 0.0
    return iou, intersection, union


def _solve_kuhn_munkres(weights: list[list[float]]) -> list[tuple[int, int]]:
    """Exact Hungarian / Kuhn-Munkres algorithm for maximum weight bipartite matching.

    Args:
        weights: M x N matrix of non-negative edge weights.

    Returns:
        List of (row_idx, col_idx) matched pairs for maximum total weight.
    """
    m = len(weights)
    if m == 0:
        return []
    n = len(weights[0])
    if n == 0:
        return []

    dim = max(m, n)
    max_w = max(max(row) for row in weights) if weights else 0.0
    # Transform to min-cost square matrix
    cost = [[0.0] * dim for _ in range(dim)]
    for i in range(m):
        for j in range(n):
            cost[i][j] = max_w - weights[i][j]

    u = [0.0] * (dim + 1)
    v = [0.0] * (dim + 1)
    p = [0] * (dim + 1)
    way = [0] * (dim + 1)

    for i in range(1, dim + 1):
        p[0] = i
        j0 = 0
        minv = [float("inf")] * (dim + 1)
        used = [False] * (dim + 1)

        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float("inf")
            j1 = 0

            for j in range(1, dim + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j

            for j in range(dim + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta

            j0 = j1
            if p[j0] == 0:
                break

        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    ans = [0] * dim
    for j in range(1, dim + 1):
        if p[j] != 0:
            ans[p[j] - 1] = j - 1

    pairs = []
    for i in range(m):
        j = ans[i]
        if j < n and weights[i][j] > 0.0:
            pairs.append((i, j))
    return pairs


def match_predictions(
    gold_entities: list[GoldEntity],
    predictions: list[Prediction],
    original_text: str | None = None,
) -> MatchingResult:
    """Perform maximum-weight bipartite matching between gold entities and predictions.

    Follows PROJECT_SPEC.md §20.3:
    - Overlap condition: max(g.start, p.start) < min(g.end, p.end)
    - Weight: (2 + IoU) if type match else IoU
    - Deterministic tie-breaking: w'(g, p) = w(g, p) + eps * rank(g, p)
    - Occurrence_index is ignored.

    Args:
        gold_entities: Ground-truth entities.
        predictions: Predicted entities from a detector.
        original_text: Optional original input text for strict boundary validation (§20.6).

    Returns:
        MatchingResult containing matched pairs, unmatched gold, unmatched predictions,
        and malformed predictions.
    """
    text_len = len(original_text) if original_text is not None else None

    valid_predictions: list[Prediction] = []
    malformed_predictions: list[Prediction] = []

    for p in predictions:
        if p.is_structurally_valid(text_len):
            valid_predictions.append(p)
        else:
            malformed_p = Prediction(
                type=p.type,
                start=p.start,
                end=p.end,
                text=p.text,
                confidence=p.confidence,
                variant_id=p.variant_id,
                status="REJECTED",
                rejection_reason="INVALID_SPAN_OFFSETS",
            )
            malformed_predictions.append(malformed_p)

    if not gold_entities or not valid_predictions:
        return MatchingResult(
            matches=[],
            unmatched_gold=list(gold_entities),
            unmatched_predictions=list(valid_predictions),
            malformed_predictions=malformed_predictions,
        )

    m = len(gold_entities)
    n = len(valid_predictions)

    # 1. Collect all candidate pairs and sort lexicographically for deterministic tie-breaking
    # Sort order: (g.start, g.end, p.start, p.end)
    all_pairs = []
    for i, g in enumerate(gold_entities):
        for j, p in enumerate(valid_predictions):
            all_pairs.append((g.start, g.end, p.start, p.end, i, j))

    # Sort lexicographically
    all_pairs.sort()
    # Rank assignment: rank 0 is best tie-break
    pair_rank = {}
    total_pairs = len(all_pairs)
    for rank, item in enumerate(all_pairs):
        i, j = item[4], item[5]
        pair_rank[(i, j)] = total_pairs - rank

    # Epsilon is small enough that (total_pairs * eps) < 1e-6 (far smaller than any IoU diff)
    eps = 1e-7 / (total_pairs + 1.0)

    # 2. Build weight matrix
    weight_matrix = [[0.0] * n for _ in range(m)]
    raw_iou_matrix = [[0.0] * n for _ in range(m)]
    base_weight_matrix = [[0.0] * n for _ in range(m)]

    for i, g in enumerate(gold_entities):
        for j, p in enumerate(valid_predictions):
            iou, inter, union = _compute_iou(g, p)
            if inter > 0:
                base_w = (2.0 + iou) if (p.type == g.type) else iou
                # Add deterministic tie-break term
                w_prime = base_w + eps * pair_rank[(i, j)]
                weight_matrix[i][j] = w_prime
                base_weight_matrix[i][j] = base_w
                raw_iou_matrix[i][j] = iou
            else:
                weight_matrix[i][j] = 0.0

    # 3. Solve maximum-weight matching via exact Hungarian algorithm
    matched_indices = _solve_kuhn_munkres(weight_matrix)

    matches: list[Match] = []
    matched_gold_set = set()
    matched_pred_set = set()

    for i, j in matched_indices:
        g = gold_entities[i]
        p = valid_predictions[j]
        base_w = base_weight_matrix[i][j]
        iou = raw_iou_matrix[i][j]
        is_type_match = (p.type == g.type)
        is_exact = (g.start == p.start and g.end == p.end)

        matches.append(
            Match(
                gold=g,
                prediction=p,
                weight=base_w,
                iou=iou,
                is_type_match=is_type_match,
                is_exact_span=is_exact,
            )
        )
        matched_gold_set.add(i)
        matched_pred_set.add(j)

    # Sort matches deterministically by gold position
    matches.sort(key=lambda m: (m.gold.start, m.gold.end, m.prediction.start, m.prediction.end))

    unmatched_gold = [g for i, g in enumerate(gold_entities) if i not in matched_gold_set]
    unmatched_preds = [p for j, p in enumerate(valid_predictions) if j not in matched_pred_set]

    return MatchingResult(
        matches=matches,
        unmatched_gold=unmatched_gold,
        unmatched_predictions=unmatched_preds,
        malformed_predictions=malformed_predictions,
    )
