"""Generate B6 Post-Hoc Analysis Artifacts and Error Decomposition.

Loads the completed B6 prediction and evaluation report artifacts across seeds [42, 43, 44]
and produces all 11 failure decomposition and comparison JSON artifacts under reports/experiments/b6/.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any
from collections import Counter, defaultdict

from baselines.sv03_analysis import (
    classify_boundary_error,
    classify_false_positive,
    create_redacted_context,
)
from benchmark.evaluator import EvaluationResult, Evaluator
from benchmark.runner import load_canonical_benchmark_records
from benchmark.schema import GoldEntity, Match, Prediction

ROOT = Path(__file__).resolve().parent.parent

TARGET_TYPES = [
    "AADHAAR",
    "ADDRESS",
    "BANK_ACCOUNT",
    "EMAIL",
    "PAN",
    "PERSON",
    "PHONE",
    "UPI_ID",
]


def compute_mean_sd(values: list[float]) -> dict[str, Any]:
    n = len(values)
    mean = sum(values) / n
    if n > 1:
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        sd = math.sqrt(variance)
    else:
        sd = 0.0
    return {"mean": mean, "sd": sd, "values": values}


def load_preds_by_vid(path: Path) -> dict[str, list[Prediction]]:
    preds_by_vid: dict[str, list[Prediction]] = defaultdict(list)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            p = Prediction.from_dict(json.loads(line))
            preds_by_vid[p.variant_id or ""].append(p)
    return preds_by_vid


def main():
    records = load_canonical_benchmark_records()
    print(f"Loaded {len(records)} canonical records.")

    seeds = [42, 43, 44]
    pred_dir = ROOT / "predictions" / "experiments" / "b6"
    rep_dir = ROOT / "reports" / "experiments" / "b6"
    rep_dir.mkdir(parents=True, exist_ok=True)

    reports_by_seed = {}
    preds_by_seed = {}

    for seed in seeds:
        rep_path = rep_dir / f"evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed{seed}_v0.18.json"
        with open(rep_path, "r", encoding="utf-8") as f:
            reports_by_seed[seed] = json.load(f)

        pred_path = pred_dir / f"transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed{seed}_v0.18.jsonl"
        preds_by_seed[seed] = load_preds_by_vid(pred_path)

    # Invariant verification
    for seed in seeds:
        m = reports_by_seed[seed]["metrics_overall"]
        inv = m["f1_missed"] + m["f2_wrong_span"] + m["f3_wrong_type"] + m["tp_exact"]
        assert inv == 724, f"Seed {seed} invariant failed: {inv} != 724"
        assert reports_by_seed[seed]["n_predictions_rejected"] == 0

    metric_keys = [
        "m1_precision",
        "m2_recall",
        "m3_f1",
        "m4_exact_f1",
        "m5_type_accuracy",
        "m6_fpr",
        "tp_type",
        "tp_exact",
        "n_predictions",
        "f1_missed",
        "f2_wrong_span",
        "f3_wrong_type",
        "f4_false_pos",
    ]

    multi_seed_metrics = {
        k: compute_mean_sd([reports_by_seed[s]["metrics_overall"][k] for s in seeds])
        for k in metric_keys
    }

    # Load B5 Canonical Reports
    b5_reports_by_seed = {
        s: json.loads((ROOT / "reports" / f"evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed{s}_v0.18.json").read_text(encoding="utf-8"))
        for s in seeds
    }
    b5_multi_seed_metrics = {
        k: compute_mean_sd([b5_reports_by_seed[s]["metrics_overall"][k] for s in seeds])
        for k in metric_keys
    }

    evaluator = Evaluator()

    boundary_counts_by_seed: dict[int, Counter] = {}
    fp_counts_by_seed: dict[int, Counter] = {}
    eval_results_by_seed: dict[int, list[EvaluationResult]] = {}

    for seed in seeds:
        res_list = evaluator.evaluate_batch(records, preds_by_seed[seed])
        eval_results_by_seed[seed] = res_list

        b_counter = Counter()
        fp_counter = Counter()

        for res in res_list:
            rec = res.record_metadata
            text = rec.get("text", "")
            golds = [m.gold for m in res.matching_result.matches] + res.matching_result.unmatched_gold

            for m in res.matching_result.matches:
                if m.is_type_match and not m.is_exact_span:
                    cat = classify_boundary_error(m.gold, m.prediction, text)
                    b_counter[cat] += 1

            for pred in res.matching_result.unmatched_predictions:
                cat = classify_false_positive(pred, rec, golds)
                fp_counter[cat] += 1

        boundary_counts_by_seed[seed] = b_counter
        fp_counts_by_seed[seed] = fp_counter

    # 1. Error Summary
    b6_summary = {
        "model": "B6_CRF",
        "seeds": seeds,
        "n_records": 964,
        "n_gold": 724,
        "metrics_mean_sd": multi_seed_metrics,
        "b5_comparison": {
            k: {
                "b5_mean": b5_multi_seed_metrics[k]["mean"],
                "b6_mean": multi_seed_metrics[k]["mean"],
                "delta": multi_seed_metrics[k]["mean"] - b5_multi_seed_metrics[k]["mean"],
                "delta_pct": ((multi_seed_metrics[k]["mean"] - b5_multi_seed_metrics[k]["mean"]) / b5_multi_seed_metrics[k]["mean"] * 100) if b5_multi_seed_metrics[k]["mean"] else 0.0,
            }
            for k in metric_keys
        },
    }
    with open(rep_dir / "b6_error_summary.json", "w", encoding="utf-8") as f:
        json.dump(b6_summary, f, indent=2)

    # 2. Boundary Analysis
    all_b_cats = [
        "B1_PUNCTUATION_CAPTURED",
        "B2_WHITESPACE_GROUPING_MISMATCH",
        "B3_PARTIAL_STRUCTURED_IDENTIFIER",
        "B4_SURROUNDING_LEXICAL_TOKEN_CAPTURED",
        "B6_DELIMITER_INDUCED_SPLIT",
        "B7_ADJACENT_TOKEN_MERGE",
        "B8_ENTITY_EXTENSION",
        "B9_ENTITY_TRUNCATION",
        "B10_OTHER",
    ]
    boundary_analysis = {
        cat: compute_mean_sd([boundary_counts_by_seed[s][cat] for s in seeds])
        for cat in all_b_cats
    }
    with open(rep_dir / "b6_boundary_analysis.json", "w", encoding="utf-8") as f:
        json.dump(boundary_analysis, f, indent=2)

    # 3. False Positive Analysis
    all_fp_cats = [
        "FP1_NUMERIC_PATTERN_OVERMATCH",
        "FP2_ALPHANUMERIC_PATTERN_OVERMATCH",
        "FP3_EMAIL_LIKE_STRING",
        "FP4_UPI_LIKE_HANDLE",
        "FP5_PHONE_LIKE_SEQUENCE",
        "FP6_ADDRESS_LIKE_CONTEXT",
        "FP7_PERSON_NAME_LIKE_CONTEXT",
        "FP8_CONTEXTUAL_SEMANTIC_OVERPREDICTION",
        "FP9_PARTIAL_SUBSTRING_EXTRACTION",
        "FP10_PUNCTUATION_DELIMITER_ARTIFACT",
        "FP11_HARD_NEGATIVE_DISTRACTOR",
        "FP12_OTHER",
    ]
    fp_analysis = {
        cat: compute_mean_sd([fp_counts_by_seed[s][cat] for s in seeds])
        for cat in all_fp_cats
    }
    with open(rep_dir / "b6_false_positive_analysis.json", "w", encoding="utf-8") as f:
        json.dump(fp_analysis, f, indent=2)

    # 4. Type Analysis (from report metrics_by_pii_type)
    type_analysis = {}
    for t in TARGET_TYPES:
        type_analysis[t] = {
            "m1_precision": compute_mean_sd([reports_by_seed[s]["metrics_by_pii_type"].get(t, {}).get("m1_precision", 0.0) for s in seeds]),
            "m2_recall": compute_mean_sd([reports_by_seed[s]["metrics_by_pii_type"].get(t, {}).get("m2_recall", 0.0) for s in seeds]),
            "m3_f1": compute_mean_sd([reports_by_seed[s]["metrics_by_pii_type"].get(t, {}).get("m3_f1", 0.0) for s in seeds]),
            "m4_exact_f1": compute_mean_sd([reports_by_seed[s]["metrics_by_pii_type"].get(t, {}).get("m4_exact_f1", 0.0) for s in seeds]),
            "tp_exact": compute_mean_sd([reports_by_seed[s]["metrics_by_pii_type"].get(t, {}).get("tp_exact", 0) for s in seeds]),
            "f2_wrong_span": compute_mean_sd([reports_by_seed[s]["metrics_by_pii_type"].get(t, {}).get("f2_wrong_span", 0) for s in seeds]),
            "f4_false_pos": compute_mean_sd([reports_by_seed[s]["metrics_by_pii_type"].get(t, {}).get("f4_false_pos", 0) for s in seeds]),
        }
    with open(rep_dir / "b6_type_analysis.json", "w", encoding="utf-8") as f:
        json.dump(type_analysis, f, indent=2)

    # 5. Language Analysis
    lang_analysis = {}
    sample_langs = list(reports_by_seed[42]["metrics_by_language"].keys())
    for lang in sample_langs:
        lang_analysis[lang] = {
            "m3_f1": compute_mean_sd([reports_by_seed[s]["metrics_by_language"].get(lang, {}).get("m3_f1", 0.0) for s in seeds]),
            "m4_exact_f1": compute_mean_sd([reports_by_seed[s]["metrics_by_language"].get(lang, {}).get("m4_exact_f1", 0.0) for s in seeds]),
            "tp_exact": compute_mean_sd([reports_by_seed[s]["metrics_by_language"].get(lang, {}).get("tp_exact", 0) for s in seeds]),
            "f2_wrong_span": compute_mean_sd([reports_by_seed[s]["metrics_by_language"].get(lang, {}).get("f2_wrong_span", 0) for s in seeds]),
        }
    with open(rep_dir / "b6_language_analysis.json", "w", encoding="utf-8") as f:
        json.dump(lang_analysis, f, indent=2)

    # 6. Perturbation Analysis
    pert_analysis = {}
    sample_perts = list(reports_by_seed[42]["metrics_by_perturbation_family"].keys())
    for p in sample_perts:
        pert_analysis[p] = {
            "m3_f1": compute_mean_sd([reports_by_seed[s]["metrics_by_perturbation_family"].get(p, {}).get("m3_f1", 0.0) for s in seeds]),
            "m4_exact_f1": compute_mean_sd([reports_by_seed[s]["metrics_by_perturbation_family"].get(p, {}).get("m4_exact_f1", 0.0) for s in seeds]),
            "tp_exact": compute_mean_sd([reports_by_seed[s]["metrics_by_perturbation_family"].get(p, {}).get("tp_exact", 0) for s in seeds]),
            "f2_wrong_span": compute_mean_sd([reports_by_seed[s]["metrics_by_perturbation_family"].get(p, {}).get("f2_wrong_span", 0) for s in seeds]),
        }
    with open(rep_dir / "b6_perturbation_analysis.json", "w", encoding="utf-8") as f:
        json.dump(pert_analysis, f, indent=2)

    # 7. Difficulty Analysis
    diff_analysis = {}
    sample_diffs = list(reports_by_seed[42]["metrics_by_difficulty"].keys())
    for d in sample_diffs:
        diff_analysis[d] = {
            "m3_f1": compute_mean_sd([reports_by_seed[s]["metrics_by_difficulty"].get(d, {}).get("m3_f1", 0.0) for s in seeds]),
            "m4_exact_f1": compute_mean_sd([reports_by_seed[s]["metrics_by_difficulty"].get(d, {}).get("m4_exact_f1", 0.0) for s in seeds]),
            "tp_exact": compute_mean_sd([reports_by_seed[s]["metrics_by_difficulty"].get(d, {}).get("tp_exact", 0) for s in seeds]),
            "f2_wrong_span": compute_mean_sd([reports_by_seed[s]["metrics_by_difficulty"].get(d, {}).get("f2_wrong_span", 0) for s in seeds]),
        }
    with open(rep_dir / "b6_difficulty_analysis.json", "w", encoding="utf-8") as f:
        json.dump(diff_analysis, f, indent=2)

    # 8. Hard Negative Analysis
    hn_analysis = {}
    sample_hns = list(reports_by_seed[42]["metrics_by_decoy_class"].keys())
    for k in sample_hns:
        hn_analysis[k] = {
            "m6_fpr": compute_mean_sd([reports_by_seed[s]["metrics_by_decoy_class"].get(k, {}).get("m6_fpr", 0.0) for s in seeds]),
            "f4_false_pos": compute_mean_sd([reports_by_seed[s]["metrics_by_decoy_class"].get(k, {}).get("f4_false_pos", 0) for s in seeds]),
        }
    with open(rep_dir / "b6_hard_negative_analysis.json", "w", encoding="utf-8") as f:
        json.dump(hn_analysis, f, indent=2)

    # 9. B5 vs B6 Error Transitions (seed 42 primary)
    b5_preds_seed42 = load_preds_by_vid(ROOT / "predictions" / "transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.jsonl")
    b5_eval_seed42 = evaluator.evaluate_batch(records, b5_preds_seed42)
    b6_eval_seed42 = eval_results_by_seed[42]

    def map_gold_outcomes(eval_list: list[EvaluationResult]) -> dict[tuple[str, int, int, str], str]:
        outcomes = {}
        for ev in eval_list:
            for m in ev.matching_result.matches:
                if m.gold is not None:
                    key = (ev.variant_id, m.gold.start, m.gold.end, m.gold.type)
                    if m.is_exact_span and m.is_type_match:
                        outcomes[key] = "TP_EXACT"
                    elif m.is_type_match and not m.is_exact_span:
                        outcomes[key] = "WRONG_SPAN"
                    elif not m.is_type_match:
                        outcomes[key] = "WRONG_TYPE"
            for g in ev.matching_result.unmatched_gold:
                key = (ev.variant_id, g.start, g.end, g.type)
                outcomes[key] = "MISSED"
        return outcomes

    b5_outcomes = map_gold_outcomes(b5_eval_seed42)
    b6_outcomes = map_gold_outcomes(b6_eval_seed42)

    transition_matrix = defaultdict(int)
    for key, b5_state in b5_outcomes.items():
        b6_state = b6_outcomes.get(key, "MISSED")
        transition_matrix[f"{b5_state} -> {b6_state}"] += 1

    with open(rep_dir / "b6_b5_vs_b6_transition.json", "w", encoding="utf-8") as f:
        json.dump(dict(transition_matrix), f, indent=2)

    # 10. Multi-dimensional error interactions (seed 42)
    b_by_pert = defaultdict(Counter)
    fp_by_type = defaultdict(Counter)

    for ev in b6_eval_seed42:
        rec = ev.record_metadata
        text = rec.get("text", "")
        pert = rec.get("perturbation", {}).get("family", "NONE") if isinstance(rec.get("perturbation"), dict) else (rec.get("perturbation_family") or "NONE")
        golds = [m.gold for m in ev.matching_result.matches] + ev.matching_result.unmatched_gold

        for m in ev.matching_result.matches:
            if m.is_type_match and not m.is_exact_span:
                cat = classify_boundary_error(m.gold, m.prediction, text)
                b_by_pert[pert][cat] += 1

        for p in ev.matching_result.unmatched_predictions:
            cat = classify_false_positive(p, rec, golds)
            fp_by_type[p.type][cat] += 1

    interactions = {
        "boundary_by_perturbation": {p: dict(c) for p, c in b_by_pert.items()},
        "fp_by_predicted_type": {t: dict(c) for t, c in fp_by_type.items()},
    }
    with open(rep_dir / "b6_error_interactions.json", "w", encoding="utf-8") as f:
        json.dump(interactions, f, indent=2)

    # 11. Deterministic Representative Cases (Strictly Redacted)
    rep_cases = []
    case_types = ["B3_PARTIAL_STRUCTURED_IDENTIFIER", "B2_WHITESPACE_GROUPING_MISMATCH", "FP9_PARTIAL_SUBSTRING_EXTRACTION", "FP11_HARD_NEGATIVE_DISTRACTOR"]
    cases_collected = {c: 0 for c in case_types}

    for ev in b6_eval_seed42:
        rec = ev.record_metadata
        text = rec.get("text", "")
        golds = [m.gold for m in ev.matching_result.matches] + ev.matching_result.unmatched_gold

        for m in ev.matching_result.matches:
            if m.is_type_match and not m.is_exact_span:
                b_cat = classify_boundary_error(m.gold, m.prediction, text)
                if b_cat in cases_collected and cases_collected[b_cat] < 2:
                    rep_cases.append({
                        "category": b_cat,
                        "variant_id": ev.variant_id,
                        "gold_type": m.gold.type,
                        "pred_type": m.prediction.type,
                        "gold_length": m.gold.end - m.gold.start,
                        "pred_length": m.prediction.end - m.prediction.start,
                        "redacted_gold_context": create_redacted_context(text, m.gold.start, m.gold.end),
                    })
                    cases_collected[b_cat] += 1

        for p in ev.matching_result.unmatched_predictions:
            fp_cat = classify_false_positive(p, rec, golds)
            if fp_cat in cases_collected and cases_collected[fp_cat] < 2:
                rep_cases.append({
                    "category": fp_cat,
                    "variant_id": ev.variant_id,
                    "pred_type": p.type,
                    "pred_length": p.end - p.start,
                    "confidence": round(p.confidence, 4) if p.confidence is not None else 1.0,
                    "redacted_context": create_redacted_context(text, p.start, p.end),
                })
                cases_collected[fp_cat] += 1

    with open(rep_dir / "b6_representative_cases.json", "w", encoding="utf-8") as f:
        json.dump(rep_cases, f, indent=2)

    print("\nAll 11 B6 experimental analysis and failure artifacts successfully written to reports/experiments/b6/")


if __name__ == "__main__":
    main()