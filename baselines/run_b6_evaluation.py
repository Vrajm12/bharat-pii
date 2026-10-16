"""Formal B6 Benchmark Evaluation & Failure Decomposition Script.

Executes B6 (Linear-Chain CRF Transformer) on the locked canonical 964-record
benchmark corpus across seeds [42, 43, 44].
Generates:
- Prediction files under predictions/experiments/b6/
- Evaluation reports under reports/experiments/b6/
- 11 detailed failure analysis JSON artifacts under reports/experiments/b6/
- Verifies exact partition invariant: F1 + F2 + F3 + TP_exact == 724
- Computes multi-seed mean +/- SD and paired comparisons against canonical B5.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import shutil
from typing import Any
from collections import Counter, defaultdict

from transformers import AutoTokenizer, XLMRobertaModel

from baselines.transformer_b6 import TransformerB6CRFAdapter
from baselines.sv03_analysis import (
    classify_boundary_error,
    classify_false_positive,
    create_redacted_context,
)
from benchmark.evaluator import EvaluationResult, Evaluator
from benchmark.runner import load_canonical_benchmark_records, run_experiment
from benchmark.schema import GoldEntity, Match, MatchingResult, Prediction
from benchmark.stats import (
    aggregate_by_decoy_class,
    aggregate_by_difficulty,
    aggregate_by_language,
    aggregate_by_perturbation_family,
    aggregate_by_pii_type,
    aggregate_results,
)

ROOT = Path(__file__).resolve().parent.parent

CANONICAL_HASHES = [
    ("data/raw/base_instances.jsonl", "7006b0c9227d93541d2b71f702407ecc"),
    ("data/raw/hard_negative_bases.jsonl", "b36c6c106548d18ff7083fd00532cb07"),
    ("data/generated/language_realizations.jsonl", "0cb046740507eb9111a214b24b680483"),
    ("data/generated/hard_negative_realizations.jsonl", "ae5537eec4129822e3d97b05170b4fea"),
    ("data/generated/adversarial_realizations.jsonl", "1b678b9597737c85197acf80ab56878d"),
    ("annotation/review_template.csv", "78c5767f2f8fede2021ff344aaddc32c"),
    ("predictions/regex_1.0.0_v0.18.jsonl", "8913ac633854a36948a3445e4be0594d"),
    ("reports/evaluation_regex_1.0.0_v0.18.json", "2958f77985fcc70d704c123e9e952ebd"),
    ("predictions/spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.jsonl", "6c74bd4ec742a1f0c6b8024200937fb5"),
    ("reports/evaluation_spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.json", "a9745314b2e71df861ea71af15a9dd1a"),
    ("predictions/presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.jsonl", "2c661403efa963275be5f2559a1577b9"),
    ("reports/evaluation_presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.json", "4831393231e3d15dc674166dcaaaa2b9"),
    ("predictions/transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.jsonl", "3f53b646fb9f95414bef8b972d2277b1"),
    ("reports/evaluation_transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.json", "dfe7e6b93e15ca266b29121977b1809e"),
    ("predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.jsonl", "e589c2a3daa96e8a3963d95fecb89012"),
    ("predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.jsonl", "e589c2a3daa96e8a3963d95fecb89012"),
    ("predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.jsonl", "e11d924839cdddebd59104624f667357"),
    ("predictions/transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.jsonl", "a0b17f4b93251463319d0dc1409514bf"),
    ("reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.json", "d3a9f9da8e848c7cafb9cf43299b9439"),
    ("reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.json", "06ca5638e48dc492c016166d8b1d12a2"),
    ("reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.json", "cfb422de399fa7cb13dec4e30f7b29e1"),
    ("reports/evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.json", "90a0a0c9bb83dd4d2f456b6e0f508753"),
]

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


def verify_canonical_hashes() -> None:
    print("Verifying 22 canonical locked hashes before B6 evaluation...")
    for rel_path, expected_md5 in CANONICAL_HASHES:
        p = ROOT / rel_path
        if not p.exists():
            raise FileNotFoundError(f"Missing canonical file: {p}")
        with open(p, "rb") as f:
            h = hashlib.md5(f.read()).hexdigest()
        if h != expected_md5:
            raise ValueError(f"MD5 mismatch on {rel_path}: {h} != {expected_md5}")
    print("All 22 canonical locked hashes verified MATCH.")


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


def run_b6_evaluation():
    verify_canonical_hashes()

    records = load_canonical_benchmark_records()
    print(f"Loaded {len(records)} canonical records.")

    seeds = [42, 43, 44]
    pred_dir = ROOT / "predictions" / "experiments" / "b6"
    rep_dir = ROOT / "reports" / "experiments" / "b6"
    pred_dir.mkdir(parents=True, exist_ok=True)
    rep_dir.mkdir(parents=True, exist_ok=True)

    reports_by_seed: dict[int, dict[str, Any]] = {}
    preds_by_seed: dict[int, dict[str, list[Prediction]]] = {}

    print("Loading shared base encoder and tokenizer once for all B6 seeds...")
    shared_tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")
    shared_encoder = XLMRobertaModel.from_pretrained("xlm-roberta-base")
    shared_encoder.eval()

    for seed in seeds:
        print(f"\n================ Running B6 Benchmark for Seed {seed} ================")
        checkpoint_dir = ROOT / "checkpoints" / "b6" / f"b6_transformer_crf_seed{seed}"
        if not checkpoint_dir.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_dir}")

        adapter = TransformerB6CRFAdapter(
            model_name_or_path=checkpoint_dir,
            seed=seed,
            encoder_model=shared_encoder,
            tokenizer=shared_tokenizer,
        )
        adapter._system_version = f"5.16.1_xlm_roberta_base_indian_crf_seed{seed}"

        report = run_experiment(
            adapter=adapter,
            records=records,
            dataset_version="0.18",
            save_artifacts=True,
            predictions_dir=pred_dir,
            reports_dir=rep_dir,
        )

        reports_by_seed[seed] = report
        m = report["metrics_overall"]

        inv = m["f1_missed"] + m["f2_wrong_span"] + m["f3_wrong_type"] + m["tp_exact"]
        assert inv == m["n_gold"] == 724, f"Partition invariant failed for seed {seed}: {inv} != 724"
        assert report["n_predictions_rejected"] == 0, f"Rejected predictions found for seed {seed}: {report['n_predictions_rejected']}"

        print(f"Seed {seed} complete: M3 F1 = {m['m3_f1']*100:.2f}%, M4 Exact F1 = {m['m4_exact_f1']*100:.2f}%, Precision = {m['m1_precision']*100:.2f}%, Recall = {m['m2_recall']*100:.2f}%, TP_exact = {m['tp_exact']}, Preds = {m['n_predictions']}")

        pred_file = pred_dir / f"transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed{seed}_v0.18.jsonl"
        preds_by_seed[seed] = load_preds_by_vid(pred_file)

    # Copy Seed 42 as primary B6 artifact
    shutil.copy2(
        pred_dir / "transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed42_v0.18.jsonl",
        pred_dir / "transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.jsonl",
    )
    shutil.copy2(
        rep_dir / "evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed42_v0.18.json",
        rep_dir / "evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.json",
    )

    # Aggregate Multi-Seed Metrics
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

    # Load Canonical B5 reports for paired comparisons
    b5_reports_by_seed = {
        s: json.loads((ROOT / "reports" / f"evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed{s}_v0.18.json").read_text(encoding="utf-8"))
        for s in seeds
    }
    b5_multi_seed_metrics = {
        k: compute_mean_sd([b5_reports_by_seed[s]["metrics_overall"][k] for s in seeds])
        for k in metric_keys
    }

    # Multi-Seed Error Decomposition
    evaluator = Evaluator()
    record_dict = {r["variant_id"]: r for r in records}

    # Compute boundary and FP breakdowns per seed
    boundary_counts_by_seed: dict[int, Counter] = {}
    fp_counts_by_seed: dict[int, Counter] = {}
    type_metrics_by_seed: dict[int, dict[str, Any]] = {}
    lang_metrics_by_seed: dict[int, dict[str, Any]] = {}
    pert_metrics_by_seed: dict[int, dict[str, Any]] = {}
    diff_metrics_by_seed: dict[int, dict[str, Any]] = {}
    hn_metrics_by_seed: dict[int, dict[str, Any]] = {}

    eval_results_by_seed: dict[int, list[EvaluationResult]] = {}

    for seed in seeds:
        res_list = evaluator.evaluate_batch(records, preds_by_seed[seed])
        eval_results_by_seed[seed] = res_list

        b_counter = Counter()
        fp_counter = Counter()

        for ev in res_list:
            rec = record_dict[ev.variant_id]
            text = rec.get("text", "")
            all_gold = [GoldEntity(**g) for g in rec.get("gold_entities", [])]

            for m in ev.matching_result.matches:
                if m.status == Match.WRONG_SPAN and m.gold is not None and m.pred is not None:
                    cat = classify_boundary_error(m.gold, m.pred, text)
                    b_counter[cat] += 1

            for p in ev.matching_result.false_positives:
                cat = classify_false_positive(p, rec, all_gold)
                fp_counter[cat] += 1

        boundary_counts_by_seed[seed] = b_counter
        fp_counts_by_seed[seed] = fp_counter

        type_metrics_by_seed[seed] = aggregate_by_pii_type(res_list)
        lang_metrics_by_seed[seed] = aggregate_by_language(res_list)
        pert_metrics_by_seed[seed] = aggregate_by_perturbation_family(res_list)
        diff_metrics_by_seed[seed] = aggregate_by_difficulty(res_list)
        hn_metrics_by_seed[seed] = aggregate_by_decoy_class(res_list)

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

    # 4. Type Analysis
    type_analysis = {}
    for t in TARGET_TYPES:
        type_analysis[t] = {
            "m1_precision": compute_mean_sd([type_metrics_by_seed[s].get(t, {}).get("m1_precision", 0.0) for s in seeds]),
            "m2_recall": compute_mean_sd([type_metrics_by_seed[s].get(t, {}).get("m2_recall", 0.0) for s in seeds]),
            "m3_f1": compute_mean_sd([type_metrics_by_seed[s].get(t, {}).get("m3_f1", 0.0) for s in seeds]),
            "m4_exact_f1": compute_mean_sd([type_metrics_by_seed[s].get(t, {}).get("m4_exact_f1", 0.0) for s in seeds]),
            "tp_exact": compute_mean_sd([type_metrics_by_seed[s].get(t, {}).get("tp_exact", 0) for s in seeds]),
            "f2_wrong_span": compute_mean_sd([type_metrics_by_seed[s].get(t, {}).get("f2_wrong_span", 0) for s in seeds]),
            "f4_false_positive": compute_mean_sd([type_metrics_by_seed[s].get(t, {}).get("f4_false_positive", 0) for s in seeds]),
        }
    with open(rep_dir / "b6_type_analysis.json", "w", encoding="utf-8") as f:
        json.dump(type_analysis, f, indent=2)

    # 5. Language Analysis
    lang_analysis = {}
    sample_langs = list(lang_metrics_by_seed[42].keys())
    for lang in sample_langs:
        lang_analysis[lang] = {
            "m3_f1": compute_mean_sd([lang_metrics_by_seed[s].get(lang, {}).get("m3_f1", 0.0) for s in seeds]),
            "m4_exact_f1": compute_mean_sd([lang_metrics_by_seed[s].get(lang, {}).get("m4_exact_f1", 0.0) for s in seeds]),
            "tp_exact": compute_mean_sd([lang_metrics_by_seed[s].get(lang, {}).get("tp_exact", 0) for s in seeds]),
            "f2_wrong_span": compute_mean_sd([lang_metrics_by_seed[s].get(lang, {}).get("f2_wrong_span", 0) for s in seeds]),
        }
    with open(rep_dir / "b6_language_analysis.json", "w", encoding="utf-8") as f:
        json.dump(lang_analysis, f, indent=2)

    # 6. Perturbation Analysis
    pert_analysis = {}
    sample_perts = list(pert_metrics_by_seed[42].keys())
    for p in sample_perts:
        pert_analysis[p] = {
            "m3_f1": compute_mean_sd([pert_metrics_by_seed[s].get(p, {}).get("m3_f1", 0.0) for s in seeds]),
            "m4_exact_f1": compute_mean_sd([pert_metrics_by_seed[s].get(p, {}).get("m4_exact_f1", 0.0) for s in seeds]),
            "tp_exact": compute_mean_sd([pert_metrics_by_seed[s].get(p, {}).get("tp_exact", 0) for s in seeds]),
            "f2_wrong_span": compute_mean_sd([pert_metrics_by_seed[s].get(p, {}).get("f2_wrong_span", 0) for s in seeds]),
        }
    with open(rep_dir / "b6_perturbation_analysis.json", "w", encoding="utf-8") as f:
        json.dump(pert_analysis, f, indent=2)

    # 7. Difficulty Analysis
    diff_analysis = {}
    for d in ["easy", "medium", "hard", "adversarial"]:
        diff_analysis[d] = {
            "m3_f1": compute_mean_sd([diff_metrics_by_seed[s].get(d, {}).get("m3_f1", 0.0) for s in seeds]),
            "m4_exact_f1": compute_mean_sd([diff_metrics_by_seed[s].get(d, {}).get("m4_exact_f1", 0.0) for s in seeds]),
            "tp_exact": compute_mean_sd([diff_metrics_by_seed[s].get(d, {}).get("tp_exact", 0) for s in seeds]),
            "f2_wrong_span": compute_mean_sd([diff_metrics_by_seed[s].get(d, {}).get("f2_wrong_span", 0) for s in seeds]),
        }
    with open(rep_dir / "b6_difficulty_analysis.json", "w", encoding="utf-8") as f:
        json.dump(diff_analysis, f, indent=2)

    # 8. Hard Negative Analysis
    hn_analysis = {}
    for k in hn_metrics_by_seed[42].keys():
        hn_analysis[k] = {
            "m6_fpr": compute_mean_sd([hn_metrics_by_seed[s].get(k, {}).get("m6_fpr", 0.0) for s in seeds]),
            "f4_false_positive": compute_mean_sd([hn_metrics_by_seed[s].get(k, {}).get("f4_false_positive", 0) for s in seeds]),
        }
    with open(rep_dir / "b6_hard_negative_analysis.json", "w", encoding="utf-8") as f:
        json.dump(hn_analysis, f, indent=2)

    # 9. B5 vs B6 Error Transitions (seed 42 primary)
    b5_preds_seed42 = load_preds_by_vid(ROOT / "predictions" / "transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.jsonl")
    b5_eval_seed42 = evaluator.evaluate_batch(records, b5_preds_seed42)
    b6_eval_seed42 = eval_results_by_seed[42]

    # Map gold entity outcomes
    def map_gold_outcomes(eval_list: list[EvaluationResult]) -> dict[tuple[str, int, int, str], str]:
        outcomes = {}
        for ev in eval_list:
            for m in ev.matching_result.matches:
                if m.gold is not None:
                    key = (ev.variant_id, m.gold.start, m.gold.end, m.gold.type)
                    if m.status == Match.EXACT:
                        outcomes[key] = "TP_EXACT"
                    elif m.status == Match.WRONG_SPAN:
                        outcomes[key] = "WRONG_SPAN"
                    elif m.status == Match.WRONG_TYPE:
                        outcomes[key] = "WRONG_TYPE"
            for g in ev.matching_result.misses:
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
        rec = record_dict[ev.variant_id]
        text = rec.get("text", "")
        pert = rec.get("perturbation_family") or "none"
        all_gold = [GoldEntity(**g) for g in rec.get("gold_entities", [])]

        for m in ev.matching_result.matches:
            if m.status == Match.WRONG_SPAN and m.gold is not None and m.pred is not None:
                cat = classify_boundary_error(m.gold, m.pred, text)
                b_by_pert[pert][cat] += 1

        for p in ev.matching_result.false_positives:
            cat = classify_false_positive(p, rec, all_gold)
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
        rec = record_dict[ev.variant_id]
        text = rec.get("text", "")
        all_gold = [GoldEntity(**g) for g in rec.get("gold_entities", [])]

        for m in ev.matching_result.matches:
            if m.status == Match.WRONG_SPAN and m.gold is not None and m.pred is not None:
                b_cat = classify_boundary_error(m.gold, m.pred, text)
                if b_cat in cases_collected and cases_collected[b_cat] < 2:
                    rep_cases.append({
                        "category": b_cat,
                        "variant_id": ev.variant_id,
                        "gold_type": m.gold.type,
                        "pred_type": m.pred.type,
                        "gold_length": m.gold.end - m.gold.start,
                        "pred_length": m.pred.end - m.pred.start,
                        "redacted_gold_context": create_redacted_context(text, m.gold.start, m.gold.end),
                    })
                    cases_collected[b_cat] += 1

        for p in ev.matching_result.false_positives:
            fp_cat = classify_false_positive(p, rec, all_gold)
            if fp_cat in cases_collected and cases_collected[fp_cat] < 2:
                rep_cases.append({
                    "category": fp_cat,
                    "variant_id": ev.variant_id,
                    "pred_type": p.type,
                    "pred_length": p.end - p.start,
                    "confidence": p.confidence,
                    "redacted_context": create_redacted_context(text, p.start, p.end),
                })
                cases_collected[fp_cat] += 1

    with open(rep_dir / "b6_representative_cases.json", "w", encoding="utf-8") as f:
        json.dump(rep_cases, f, indent=2)

    print("\nAll 11 B6 experimental analysis and failure artifacts successfully written to reports/experiments/b6/")


if __name__ == "__main__":
    run_b6_evaluation()