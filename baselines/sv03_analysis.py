"""SV-03 Systematic Error Analysis and Failure Mechanism Study.

Orchestrates Phases 1 through 11:
- Phase 1: Error Accounting and Invariant Verification
- Phase 2: PII Type Error Analysis
- Phase 3: Boundary Error Classification (B1-B10)
- Phase 4: False Positive Clustering (FP1-FP12)
- Phase 5: Hard-Negative Granular Analysis
- Phase 6: Language / Realization Sensitivity
- Phase 7: Perturbation Sensitivity (A1-A5)
- Phase 8: Difficulty Analysis
- Phase 9: B5 vs SV-02 Error Transition
- Phase 10: Multi-Dimensional Error Interactions
- Phase 11: Deterministic Representative Case Selection (Zero raw PII)
"""

from __future__ import annotations

import json
import re
import string
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from benchmark.evaluator import EvaluationResult, Evaluator
from benchmark.runner import load_canonical_benchmark_records
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
REPORTS_DIR = ROOT / "reports" / "experiments" / "sv03"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

SEEDS = [42, 43, 44]

MODEL_PREDICTION_PATHS = {
    "b5": {
        42: ROOT / "predictions" / "transformer_adapted_5.16.1_xlm_roberta_base_indian_seed42_v0.18.jsonl",
        43: ROOT / "predictions" / "transformer_adapted_5.16.1_xlm_roberta_base_indian_seed43_v0.18.jsonl",
        44: ROOT / "predictions" / "transformer_adapted_5.16.1_xlm_roberta_base_indian_seed44_v0.18.jsonl",
    },
    "sv02_hn": {
        42: ROOT / "predictions" / "experiments" / "sv02" / "sv02_b5_hard_negative_5.16.1_seed42_v0.18.jsonl",
        43: ROOT / "predictions" / "experiments" / "sv02" / "sv02_b5_hard_negative_5.16.1_seed43_v0.18.jsonl",
        44: ROOT / "predictions" / "experiments" / "sv02" / "sv02_b5_hard_negative_5.16.1_seed44_v0.18.jsonl",
    },
}

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


def load_predictions_by_variant(path: Path) -> dict[str, list[Prediction]]:
    """Load predictions from jsonl file grouped by variant_id."""
    preds_by_vid: dict[str, list[Prediction]] = defaultdict(list)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            p = Prediction.from_dict(data)
            preds_by_vid[p.variant_id or ""].append(p)
    return preds_by_vid


# ----------------------------------------------------------------------
# Boundary Error Classifier (B1 - B10)
# ----------------------------------------------------------------------
def classify_boundary_error(gold: GoldEntity, pred: Prediction, text: str) -> str:
    """Classify an F2 (WRONG_SPAN with correct type) into B1..B10."""
    g_start, g_end = gold.start, gold.end
    p_start, p_end = pred.start, pred.end

    g_text = text[g_start:g_end]
    p_text = text[p_start:p_end]

    # B1: Leading or trailing punctuation captured
    leading_captured = p_start < g_start and all(c in string.punctuation or c.isspace() for c in text[p_start:g_start])
    trailing_captured = p_end > g_end and all(c in string.punctuation or c.isspace() for c in text[g_end:p_end])
    if (leading_captured or trailing_captured) and (p_start <= g_start and p_end >= g_end):
        return "B1_PUNCTUATION_CAPTURED"

    # B2: Whitespace / grouping mismatch
    # E.g. Pred or gold has spaces stripped/added, or boundary cut directly at an internal space
    if g_text.replace(" ", "") == p_text.replace(" ", ""):
        return "B2_WHITESPACE_GROUPING_MISMATCH"
    if (g_start == p_start and p_end < g_end and text[p_end:g_end].startswith(" ")) or \
       (g_end == p_end and p_start > g_start and text[g_start:p_start].endswith(" ")):
        return "B2_WHITESPACE_GROUPING_MISMATCH"

    # B6: Delimiter-induced split (cut off at @, -, /, ., etc.)
    delimiters = {"@", "-", "/", ".", "_"}
    if p_start == g_start and p_end < g_end and text[p_end] in delimiters:
        return "B6_DELIMITER_INDUCED_SPLIT"
    if p_end == g_end and p_start > g_start and text[p_start - 1] in delimiters:
        return "B6_DELIMITER_INDUCED_SPLIT"

    # B3: Partial structured identifier (sub-token truncation of alphanumeric/numeric)
    if (p_start >= g_start and p_end <= g_end) and gold.type in ("PAN", "AADHAAR", "BANK_ACCOUNT", "PHONE", "UPI_ID"):
        return "B3_PARTIAL_STRUCTURED_IDENTIFIER"

    # B4: Surrounding lexical carrier token captured
    if p_start < g_start and any(c.isalpha() for c in text[p_start:g_start]):
        return "B4_SURROUNDING_LEXICAL_TOKEN_CAPTURED"
    if p_end > g_end and any(c.isalpha() for c in text[g_end:p_end]):
        return "B4_SURROUNDING_LEXICAL_TOKEN_CAPTURED"

    # B7: Adjacent token merge
    if p_start < g_start and p_end > g_end:
        return "B7_ADJACENT_TOKEN_MERGE"

    # B8: Entity extension beyond gold span
    if (p_start < g_start or p_end > g_end) and (p_start <= g_start and p_end >= g_end):
        return "B8_ENTITY_EXTENSION"

    # B9: Entity truncation
    if p_start >= g_start and p_end <= g_end:
        return "B9_ENTITY_TRUNCATION"

    return "B10_OTHER"


# ----------------------------------------------------------------------
# False Positive Classifier (FP1 - FP12)
# ----------------------------------------------------------------------
def classify_false_positive(
    pred: Prediction,
    record: dict[str, Any],
    all_gold: list[GoldEntity],
) -> str:
    """Classify an unmatched prediction (F4) into FP1..FP12."""
    text = record.get("text", "")
    p_text = text[pred.start : pred.end]
    p_type = pred.type

    # FP11: Hard-negative distractor hit
    distractors = record.get("distractors", [])
    for d in distractors:
        d_start = d.get("start")
        d_end = d.get("end")
        if d_start is not None and d_end is not None:
            if max(pred.start, d_start) < min(pred.end, d_end):
                return "FP11_HARD_NEGATIVE_DISTRACTOR"

    # FP10: Punctuation / delimiter artifact
    if len(p_text.strip()) <= 1 or all(c in string.punctuation for c in p_text.strip()):
        return "FP10_PUNCTUATION_DELIMITER_ARTIFACT"

    # FP9: Partial substring of a gold entity
    for g in all_gold:
        if max(pred.start, g.start) < min(pred.end, g.end):
            return "FP9_PARTIAL_SUBSTRING_EXTRACTION"

    # FP4: UPI-like handle
    if p_type == "UPI_ID" or ("@" in p_text and any(h in p_text for h in ["ok", "axis", "icici", "sbi", "hdfc", "paytm", "ybl", "upi"])):
        return "FP4_UPI_LIKE_HANDLE"

    # FP3: Email-like string
    if p_type == "EMAIL" or ("@" in p_text and "." in p_text):
        return "FP3_EMAIL_LIKE_STRING"

    # FP5: Phone-like sequence
    digits_only = re.sub(r"\D", "", p_text)
    if p_type == "PHONE" or (len(digits_only) == 10 and digits_only[0] in "6789"):
        return "FP5_PHONE_LIKE_SEQUENCE"

    # FP1: Numeric-pattern overmatch
    if p_type in ("AADHAAR", "BANK_ACCOUNT") or digits_only == p_text.replace(" ", ""):
        if len(digits_only) >= 4:
            return "FP1_NUMERIC_PATTERN_OVERMATCH"

    # FP2: Alphanumeric-pattern overmatch
    if p_type == "PAN" or (any(c.isalpha() for c in p_text) and any(c.isdigit() for c in p_text)):
        return "FP2_ALPHANUMERIC_PATTERN_OVERMATCH"

    # FP6: Address-like context
    if p_type == "ADDRESS" or any(w in p_text.lower() for w in ["road", "street", "nagar", "marg", "society", "enclave", "colony"]):
        return "FP6_ADDRESS_LIKE_CONTEXT"

    # FP7: Person-name-like context
    if p_type == "PERSON" or (p_text.istitle() and not any(c.isdigit() for c in p_text)):
        return "FP7_PERSON_NAME_LIKE_CONTEXT"

    # FP8: Contextual semantic overprediction
    if any(c.isalpha() for c in p_text):
        return "FP8_CONTEXTUAL_SEMANTIC_OVERPREDICTION"

    return "FP12_OTHER"


# ----------------------------------------------------------------------
# Context Redaction Helper (Strictly Redacted - Zero Raw PII)
# ----------------------------------------------------------------------
def create_redacted_context(text: str, start: int, end: int, window: int = 25) -> str:
    """Create a redacted context window showing surrounding text without exposing raw PII."""
    prefix_start = max(0, start - window)
    suffix_end = min(len(text), end + window)

    prefix = text[prefix_start:start]
    suffix = text[end:suffix_end]

    if prefix_start > 0:
        prefix = "..." + prefix
    if suffix_end < len(text):
        suffix = suffix + "..."

    return f"{prefix}[REDACTED_PII]{suffix}"


# ----------------------------------------------------------------------
# Evaluator Pipeline for a Specific Model Seed
# ----------------------------------------------------------------------
def evaluate_model_seed(
    records: list[dict[str, Any]],
    preds_path: Path,
) -> dict[str, Any]:
    """Evaluate one model seed and collect all raw matches, metrics, and failures."""
    preds_by_vid = load_predictions_by_variant(preds_path)
    evaluator = Evaluator()

    record_evals: list[EvaluationResult] = evaluator.evaluate_batch(records, preds_by_vid)

    # Invariants and counts derived strictly from the evaluator result objects
    total_gold = sum(r.metrics.n_gold for r in record_evals)
    total_preds = sum(r.metrics.n_predictions for r in record_evals)
    tp_type = sum(r.metrics.tp_type for r in record_evals)
    tp_exact = sum(r.metrics.tp_exact for r in record_evals)
    f1_missed = sum(r.metrics.f1_missed for r in record_evals)
    f2_wrong_span = sum(r.metrics.f2_wrong_span for r in record_evals)
    f3_wrong_type = sum(r.metrics.f3_wrong_type for r in record_evals)
    f4_false_pos = sum(r.metrics.f4_false_pos for r in record_evals)

    # Micro-aggregated pooled metrics
    pooled_metrics = aggregate_results(record_evals)

    # Invariant checks
    inv1 = (f1_missed + f2_wrong_span + f3_wrong_type + tp_exact == total_gold)
    inv2 = (tp_type == tp_exact + f2_wrong_span)
    inv3 = (total_preds == tp_type + f3_wrong_type + f4_false_pos)

    # By-slice canonical aggregations
    by_lang = aggregate_by_language(record_evals)
    by_type = aggregate_by_pii_type(record_evals)
    by_fam = aggregate_by_perturbation_family(record_evals)
    by_diff = aggregate_by_difficulty(record_evals)
    by_decoy = aggregate_by_decoy_class(record_evals)

    return {
        "total_gold": total_gold,
        "total_preds": total_preds,
        "tp_type": tp_type,
        "tp_exact": tp_exact,
        "f1_missed": f1_missed,
        "f2_wrong_span": f2_wrong_span,
        "f3_wrong_type": f3_wrong_type,
        "f4_false_pos": f4_false_pos,
        "m1_precision": pooled_metrics.m1_precision,
        "m2_recall": pooled_metrics.m2_recall,
        "m3_f1": pooled_metrics.m3_f1,
        "m4_exact_f1": pooled_metrics.m4_exact_f1,
        "m5_type_acc": pooled_metrics.m5_type_accuracy,
        "m6_fpr": pooled_metrics.m6_fpr,
        "invariants": {
            "f1_f2_f3_tpexact_eq_ngold": inv1,
            "tptype_eq_tpexact_plus_f2": inv2,
            "npred_eq_tptype_f3_f4": inv3,
        },
        "by_language": by_lang,
        "by_pii_type": by_type,
        "by_perturbation_family": by_fam,
        "by_difficulty": by_diff,
        "by_decoy_class": by_decoy,
        "record_evals": record_evals,
    }


def execute_sv03_analysis():
    print("=== STARTING SV-03 ERROR ANALYSIS PIPELINE ===")
    records = load_canonical_benchmark_records()
    print(f"Loaded {len(records)} canonical benchmark records.")

    # 1. Run evaluation for B5 and SV-02 across seeds
    model_evals: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)
    for model_name, seed_paths in MODEL_PREDICTION_PATHS.items():
        for seed, path in seed_paths.items():
            print(f"Evaluating {model_name} (seed {seed})...")
            model_evals[model_name][seed] = evaluate_model_seed(records, path)

    # ------------------------------------------------------------------
    # Phase 1: Error Accounting Summary
    # ------------------------------------------------------------------
    print("Generating Phase 1: Error Accounting...")
    phase1_summary: dict[str, Any] = {}
    for model_name in ["b5", "sv02_hn"]:
        phase1_summary[model_name] = {
            "seeds": {},
            "aggregate_mean_sd": {},
        }
        for seed in SEEDS:
            res = model_evals[model_name][seed]
            phase1_summary[model_name]["seeds"][seed] = {
                "n_gold": res["total_gold"],
                "n_pred": res["total_preds"],
                "tp_type": res["tp_type"],
                "tp_exact": res["tp_exact"],
                "f1_missed": res["f1_missed"],
                "f2_wrong_span": res["f2_wrong_span"],
                "f3_wrong_type": res["f3_wrong_type"],
                "f4_false_pos": res["f4_false_pos"],
                "m1_precision": res["m1_precision"],
                "m2_recall": res["m2_recall"],
                "m3_f1": res["m3_f1"],
                "m4_exact_f1": res["m4_exact_f1"],
                "m5_type_acc": res["m5_type_acc"],
                "m6_fpr": res["m6_fpr"],
                "invariants": res["invariants"],
            }

        # Calculate mean +- sd
        keys = ["n_gold", "n_pred", "tp_type", "tp_exact", "f1_missed", "f2_wrong_span", "f3_wrong_type", "f4_false_pos", "m1_precision", "m2_recall", "m3_f1", "m4_exact_f1", "m5_type_acc", "m6_fpr"]
        for k in keys:
            vals = [phase1_summary[model_name]["seeds"][s][k] for s in SEEDS]
            mean_v = sum(vals) / len(vals)
            sd_v = (sum((x - mean_v) ** 2 for x in vals) / len(vals)) ** 0.5
            phase1_summary[model_name]["aggregate_mean_sd"][k] = {
                "mean": round(mean_v, 4),
                "sd": round(sd_v, 4),
            }

    with open(REPORTS_DIR / "sv03_error_summary.json", "w") as f:
        json.dump(phase1_summary, f, indent=2)

    # ------------------------------------------------------------------
    # Phase 2: PII Type Error Analysis
    # ------------------------------------------------------------------
    print("Generating Phase 2: PII Type Error Analysis...")
    phase2_type_analysis: dict[str, Any] = {}
    for model_name in ["b5", "sv02_hn"]:
        phase2_type_analysis[model_name] = {}
        for t in TARGET_TYPES:
            vals = [model_evals[model_name][seed]["by_pii_type"][t] for seed in SEEDS]
            phase2_type_analysis[model_name][t] = {
                "gold_count": round(sum(v.n_gold for v in vals) / len(vals), 2),
                "pred_count": round(sum(v.n_predictions for v in vals) / len(vals), 2),
                "tp_type": round(sum(v.tp_type for v in vals) / len(vals), 2),
                "tp_exact": round(sum(v.tp_exact for v in vals) / len(vals), 2),
                "f1_missed": round(sum(v.f1_missed for v in vals) / len(vals), 2),
                "f2_wrong_span": round(sum(v.f2_wrong_span for v in vals) / len(vals), 2),
                "f3_wrong_type": round(sum(v.f3_wrong_type for v in vals) / len(vals), 2),
                "f4_false_pos": round(sum(v.f4_false_pos for v in vals) / len(vals), 2),
                "precision": round(sum(v.m1_precision for v in vals) / len(vals), 4),
                "recall": round(sum(v.m2_recall for v in vals) / len(vals), 4),
                "f1_type": round(sum(v.m3_f1 for v in vals) / len(vals), 4),
                "f1_exact": round(sum(v.m4_exact_f1 for v in vals) / len(vals), 4),
                "type_accuracy": round(sum(v.m5_type_accuracy for v in vals) / len(vals), 4),
                "fpr": round(sum(v.m6_fpr for v in vals) / len(vals), 4),
            }

        # Compute rankings
        types_by_exact_f1 = sorted(TARGET_TYPES, key=lambda t: phase2_type_analysis[model_name][t]["f1_exact"])
        types_by_fp_burden = sorted(TARGET_TYPES, key=lambda t: phase2_type_analysis[model_name][t]["f4_false_pos"], reverse=True)
        types_by_boundary_burden = sorted(TARGET_TYPES, key=lambda t: phase2_type_analysis[model_name][t]["f2_wrong_span"], reverse=True)
        types_by_type_f1 = sorted(TARGET_TYPES, key=lambda t: phase2_type_analysis[model_name][t]["f1_type"])

        phase2_type_analysis[model_name]["rankings"] = {
            "rank_by_lowest_exact_f1": types_by_exact_f1,
            "rank_by_highest_false_positive_burden": types_by_fp_burden,
            "rank_by_highest_boundary_error_burden": types_by_boundary_burden,
            "rank_by_lowest_type_strict_f1": types_by_type_f1,
        }

    with open(REPORTS_DIR / "sv03_type_analysis.json", "w") as f:
        json.dump(phase2_type_analysis, f, indent=2)

    # ------------------------------------------------------------------
    # Phase 3: Boundary Error Classification (B1 - B10)
    # ------------------------------------------------------------------
    print("Generating Phase 3: Boundary Error Classification...")
    phase3_boundary: dict[str, Any] = {}
    for model_name in ["b5", "sv02_hn"]:
        phase3_boundary[model_name] = {
            "categories_overall": Counter(),
            "by_pii_type": defaultdict(Counter),
            "by_language": defaultdict(Counter),
            "by_perturbation": defaultdict(Counter),
            "by_difficulty": defaultdict(Counter),
            "total_f2_analyzed": 0,
        }

        for seed in SEEDS:
            evals = model_evals[model_name][seed]["record_evals"]
            for res in evals:
                rec = res.record_metadata
                text = rec.get("text", "")
                lang = rec.get("language", "EN")
                diff = rec.get("difficulty", "EASY")
                fam = rec.get("perturbation", {}).get("family", "NONE")

                for m in res.matching_result.matches:
                    if m.is_type_match and not m.is_exact_span:
                        cat = classify_boundary_error(m.gold, m.prediction, text)
                        phase3_boundary[model_name]["categories_overall"][cat] += 1
                        phase3_boundary[model_name]["by_pii_type"][m.gold.type][cat] += 1
                        phase3_boundary[model_name]["by_language"][lang][cat] += 1
                        phase3_boundary[model_name]["by_perturbation"][fam][cat] += 1
                        phase3_boundary[model_name]["by_difficulty"][diff][cat] += 1
                        phase3_boundary[model_name]["total_f2_analyzed"] += 1

        total_f2 = phase3_boundary[model_name]["total_f2_analyzed"] / len(SEEDS)
        norm_cats = {}
        for c, count in phase3_boundary[model_name]["categories_overall"].items():
            mean_c = count / len(SEEDS)
            norm_cats[c] = {
                "mean_count": round(mean_c, 2),
                "percentage_of_f2": round((mean_c / total_f2) * 100, 2) if total_f2 > 0 else 0.0,
            }
        phase3_boundary[model_name]["categories_overall"] = norm_cats
        phase3_boundary[model_name]["total_f2_mean"] = round(total_f2, 2)
        del phase3_boundary[model_name]["total_f2_analyzed"]

        for dim in ["by_pii_type", "by_language", "by_perturbation", "by_difficulty"]:
            d_dict = {}
            for k, counter in phase3_boundary[model_name][dim].items():
                d_dict[k] = {c: round(v / len(SEEDS), 2) for c, v in counter.items()}
            phase3_boundary[model_name][dim] = d_dict

    with open(REPORTS_DIR / "sv03_boundary_analysis.json", "w") as f:
        json.dump(phase3_boundary, f, indent=2)

    # ------------------------------------------------------------------
    # Phase 4: False Positive Analysis (FP1 - FP12)
    # ------------------------------------------------------------------
    print("Generating Phase 4: False Positive Analysis...")
    phase4_fp: dict[str, Any] = {}
    for model_name in ["b5", "sv02_hn"]:
        phase4_fp[model_name] = {
            "categories_overall": Counter(),
            "by_predicted_type": defaultdict(Counter),
            "by_language": defaultdict(Counter),
            "by_perturbation": defaultdict(Counter),
            "by_difficulty": defaultdict(Counter),
            "total_f4_analyzed": 0,
        }

        for seed in SEEDS:
            evals = model_evals[model_name][seed]["record_evals"]
            for res in evals:
                rec = res.record_metadata
                lang = rec.get("language", "EN")
                diff = rec.get("difficulty", "EASY")
                fam = rec.get("perturbation", {}).get("family", "NONE")
                golds = [m.gold for m in res.matching_result.matches] + res.matching_result.unmatched_gold

                for pred in res.matching_result.unmatched_predictions:
                    cat = classify_false_positive(pred, rec, golds)
                    phase4_fp[model_name]["categories_overall"][cat] += 1
                    phase4_fp[model_name]["by_predicted_type"][pred.type][cat] += 1
                    phase4_fp[model_name]["by_language"][lang][cat] += 1
                    phase4_fp[model_name]["by_perturbation"][fam][cat] += 1
                    phase4_fp[model_name]["by_difficulty"][diff][cat] += 1
                    phase4_fp[model_name]["total_f4_analyzed"] += 1

        total_f4 = phase4_fp[model_name]["total_f4_analyzed"] / len(SEEDS)
        norm_cats = {}
        for c, count in phase4_fp[model_name]["categories_overall"].items():
            mean_c = count / len(SEEDS)
            norm_cats[c] = {
                "mean_count": round(mean_c, 2),
                "percentage_of_f4": round((mean_c / total_f4) * 100, 2) if total_f4 > 0 else 0.0,
            }
        phase4_fp[model_name]["categories_overall"] = norm_cats
        phase4_fp[model_name]["total_f4_mean"] = round(total_f4, 2)
        del phase4_fp[model_name]["total_f4_analyzed"]

        for dim in ["by_predicted_type", "by_language", "by_perturbation", "by_difficulty"]:
            d_dict = {}
            for k, counter in phase4_fp[model_name][dim].items():
                d_dict[k] = {c: round(v / len(SEEDS), 2) for c, v in counter.items()}
            phase4_fp[model_name][dim] = d_dict

    with open(REPORTS_DIR / "sv03_false_positive_analysis.json", "w") as f:
        json.dump(phase4_fp, f, indent=2)

    # ------------------------------------------------------------------
    # Phase 5: Hard-Negative Analysis
    # ------------------------------------------------------------------
    print("Generating Phase 5: Hard-Negative Granular Analysis...")
    phase5_hn: dict[str, Any] = {}
    for model_name in ["b5", "sv02_hn"]:
        phase5_hn[model_name] = {
            "by_decoy_class": defaultdict(lambda: {
                "record_count": 0,
                "prediction_count": 0,
                "records_with_fp": 0,
                "predicted_types": Counter(),
                "mean_span_length": 0.0,
                "span_lengths": [],
            }),
            "total_hn_records": 0,
            "total_hn_predictions": 0,
            "total_hn_records_with_fp": 0,
            "overall_predicted_types": Counter(),
        }

        for seed in SEEDS:
            evals = model_evals[model_name][seed]["record_evals"]
            for res in evals:
                rec = res.record_metadata
                is_hn = (rec.get("base_kind") == "HARD_NEGATIVE" or rec.get("base_id", "").startswith("NEG_") or rec.get("variant_id", "").startswith("NEG_"))
                if not is_hn:
                    continue

                decoy_cls = (rec.get("distractors", [{}])[0].get("decoy_class") if rec.get("distractors") else None) or rec.get("hard_negative_decoy", {}).get("decoy_class") or "UNKNOWN"
                preds = res.matching_result.unmatched_predictions

                cls_data = phase5_hn[model_name]["by_decoy_class"][decoy_cls]
                if seed == 42:
                    cls_data["record_count"] += 1
                    phase5_hn[model_name]["total_hn_records"] += 1

                if len(preds) > 0:
                    cls_data["records_with_fp"] += 1
                    phase5_hn[model_name]["total_hn_records_with_fp"] += 1

                for p in preds:
                    cls_data["prediction_count"] += 1
                    cls_data["predicted_types"][p.type] += 1
                    cls_data["span_lengths"].append(p.end - p.start)
                    phase5_hn[model_name]["total_hn_predictions"] += 1
                    phase5_hn[model_name]["overall_predicted_types"][p.type] += 1

        phase5_hn[model_name]["total_hn_predictions"] = round(phase5_hn[model_name]["total_hn_predictions"] / len(SEEDS), 2)
        phase5_hn[model_name]["total_hn_records_with_fp"] = round(phase5_hn[model_name]["total_hn_records_with_fp"] / len(SEEDS), 2)
        for t, count in phase5_hn[model_name]["overall_predicted_types"].items():
            phase5_hn[model_name]["overall_predicted_types"][t] = round(count / len(SEEDS), 2)

        out_decoy = {}
        for dcls, ddata in phase5_hn[model_name]["by_decoy_class"].items():
            lens = ddata["span_lengths"]
            out_decoy[dcls] = {
                "record_count": ddata["record_count"],
                "prediction_count_mean": round(ddata["prediction_count"] / len(SEEDS), 2),
                "records_with_fp_mean": round(ddata["records_with_fp"] / len(SEEDS), 2),
                "fp_rate": round(ddata["records_with_fp"] / (ddata["record_count"] * len(SEEDS)), 4) if ddata["record_count"] > 0 else 0.0,
                "mean_span_length": round(sum(lens) / len(lens), 2) if lens else 0.0,
                "predicted_types": {t: round(cnt / len(SEEDS), 2) for t, cnt in ddata["predicted_types"].items()},
            }
        phase5_hn[model_name]["by_decoy_class"] = out_decoy

    with open(REPORTS_DIR / "sv03_hard_negative_analysis.json", "w") as f:
        json.dump(phase5_hn, f, indent=2)

    # ------------------------------------------------------------------
    # Phase 6: Language / Realization Sensitivity
    # ------------------------------------------------------------------
    print("Generating Phase 6: Language Sensitivity...")
    phase6_lang: dict[str, Any] = {}
    languages = ["EN", "IN_EN", "ROM_HI", "HINGLISH", "INFORMAL_HINGLISH", "HI_LATIN_PII", "HI_DEVA_PII"]
    for model_name in ["b5", "sv02_hn"]:
        phase6_lang[model_name] = {}
        for lang in languages:
            vals = [model_evals[model_name][seed]["by_language"][lang] for seed in SEEDS]
            phase6_lang[model_name][lang] = {
                "gold_count": round(sum(v.n_gold for v in vals) / len(vals), 2),
                "pred_count": round(sum(v.n_predictions for v in vals) / len(vals), 2),
                "tp_type": round(sum(v.tp_type for v in vals) / len(vals), 2),
                "tp_exact": round(sum(v.tp_exact for v in vals) / len(vals), 2),
                "f2_wrong_span": round(sum(v.f2_wrong_span for v in vals) / len(vals), 2),
                "f4_false_pos": round(sum(v.f4_false_pos for v in vals) / len(vals), 2),
                "precision": round(sum(v.m1_precision for v in vals) / len(vals), 4),
                "recall": round(sum(v.m2_recall for v in vals) / len(vals), 4),
                "f1_type": round(sum(v.m3_f1 for v in vals) / len(vals), 4),
                "f1_exact": round(sum(v.m4_exact_f1 for v in vals) / len(vals), 4),
                "fpr": round(sum(v.m6_fpr for v in vals) / len(vals), 4),
            }

    with open(REPORTS_DIR / "sv03_language_analysis.json", "w") as f:
        json.dump(phase6_lang, f, indent=2)

    # ------------------------------------------------------------------
    # Phase 7: Perturbation Sensitivity (A1 - A5, NONE)
    # ------------------------------------------------------------------
    print("Generating Phase 7: Perturbation Sensitivity...")
    phase7_perturbation: dict[str, Any] = {}
    fams = ["NONE", "A1", "A2", "A3", "A4", "A5"]
    for model_name in ["b5", "sv02_hn"]:
        phase7_perturbation[model_name] = {}
        for fam in fams:
            vals = [model_evals[model_name][seed]["by_perturbation_family"][fam] for seed in SEEDS]
            phase7_perturbation[model_name][fam] = {
                "gold_count": round(sum(v.n_gold for v in vals) / len(vals), 2),
                "pred_count": round(sum(v.n_predictions for v in vals) / len(vals), 2),
                "tp_type": round(sum(v.tp_type for v in vals) / len(vals), 2),
                "tp_exact": round(sum(v.tp_exact for v in vals) / len(vals), 2),
                "f1_missed": round(sum(v.f1_missed for v in vals) / len(vals), 2),
                "f2_wrong_span": round(sum(v.f2_wrong_span for v in vals) / len(vals), 2),
                "f3_wrong_type": round(sum(v.f3_wrong_type for v in vals) / len(vals), 2),
                "f4_false_pos": round(sum(v.f4_false_pos for v in vals) / len(vals), 2),
                "precision": round(sum(v.m1_precision for v in vals) / len(vals), 4),
                "recall": round(sum(v.m2_recall for v in vals) / len(vals), 4),
                "f1_type": round(sum(v.m3_f1 for v in vals) / len(vals), 4),
                "f1_exact": round(sum(v.m4_exact_f1 for v in vals) / len(vals), 4),
                "fpr": round(sum(v.m6_fpr for v in vals) / len(vals), 4),
            }

    with open(REPORTS_DIR / "sv03_perturbation_analysis.json", "w") as f:
        json.dump(phase7_perturbation, f, indent=2)

    # ------------------------------------------------------------------
    # Phase 8: Difficulty Progression (EASY, MEDIUM, ADVERSARIAL)
    # ------------------------------------------------------------------
    print("Generating Phase 8: Difficulty Analysis...")
    phase8_difficulty: dict[str, Any] = {}
    diffs = ["EASY", "MEDIUM", "ADVERSARIAL"]
    for model_name in ["b5", "sv02_hn"]:
        phase8_difficulty[model_name] = {}
        for diff in diffs:
            vals = [model_evals[model_name][seed]["by_difficulty"][diff] for seed in SEEDS]
            phase8_difficulty[model_name][diff] = {
                "gold_count": round(sum(v.n_gold for v in vals) / len(vals), 2),
                "pred_count": round(sum(v.n_predictions for v in vals) / len(vals), 2),
                "tp_type": round(sum(v.tp_type for v in vals) / len(vals), 2),
                "tp_exact": round(sum(v.tp_exact for v in vals) / len(vals), 2),
                "f1_missed": round(sum(v.f1_missed for v in vals) / len(vals), 2),
                "f2_wrong_span": round(sum(v.f2_wrong_span for v in vals) / len(vals), 2),
                "f3_wrong_type": round(sum(v.f3_wrong_type for v in vals) / len(vals), 2),
                "f4_false_pos": round(sum(v.f4_false_pos for v in vals) / len(vals), 2),
                "precision": round(sum(v.m1_precision for v in vals) / len(vals), 4),
                "recall": round(sum(v.m2_recall for v in vals) / len(vals), 4),
                "f1_type": round(sum(v.m3_f1 for v in vals) / len(vals), 4),
                "f1_exact": round(sum(v.m4_exact_f1 for v in vals) / len(vals), 4),
                "fpr": round(sum(v.m6_fpr for v in vals) / len(vals), 4),
            }

    with open(REPORTS_DIR / "sv03_difficulty_analysis.json", "w") as f:
        json.dump(phase8_difficulty, f, indent=2)

    # ------------------------------------------------------------------
    # Phase 9: B5 vs SV-02 Error Transition
    # ------------------------------------------------------------------
    print("Generating Phase 9: B5 vs SV-02 Error Transition...")
    b5_evals_42 = {res.variant_id: res for res in model_evals["b5"][42]["record_evals"]}
    sv02_evals_42 = {res.variant_id: res for res in model_evals["sv02_hn"][42]["record_evals"]}

    transition_counts = Counter()
    transition_by_kind = defaultdict(Counter)
    transition_by_diff = defaultdict(Counter)
    record_transitions = {}

    for rec in records:
        vid = rec["variant_id"]
        b5_res = b5_evals_42[vid]
        sv02_res = sv02_evals_42[vid]

        b5_errors = b5_res.metrics.f1_missed + b5_res.metrics.f2_wrong_span + b5_res.metrics.f3_wrong_type + b5_res.metrics.f4_false_pos
        sv02_errors = sv02_res.metrics.f1_missed + sv02_res.metrics.f2_wrong_span + sv02_res.metrics.f3_wrong_type + sv02_res.metrics.f4_false_pos

        b5_tp_exact = b5_res.metrics.tp_exact
        sv02_tp_exact = sv02_res.metrics.tp_exact

        b5_tp_type = b5_res.metrics.tp_type
        sv02_tp_type = sv02_res.metrics.tp_type

        # Transition classification
        if sv02_errors < b5_errors or (sv02_errors == b5_errors and sv02_tp_exact > b5_tp_exact):
            cls = "IMPROVED"
        elif sv02_errors > b5_errors or (sv02_errors == b5_errors and sv02_tp_exact < b5_tp_exact):
            cls = "REGRESSED"
        elif sv02_errors == b5_errors and sv02_tp_exact == b5_tp_exact and sv02_tp_type == b5_tp_type:
            cls = "UNCHANGED"
        else:
            cls = "MIXED"

        transition_counts[cls] += 1
        kind = rec.get("base_kind", "POSITIVE")
        diff = rec.get("difficulty", "EASY")
        transition_by_kind[kind][cls] += 1
        transition_by_diff[diff][cls] += 1

        record_transitions[vid] = {
            "classification": cls,
            "b5_errors": b5_errors,
            "sv02_errors": sv02_errors,
            "b5_tp_exact": b5_tp_exact,
            "sv02_tp_exact": sv02_tp_exact,
        }

    phase9_transition = {
        "transition_summary": {k: {"count": cnt, "percentage": round((cnt / len(records)) * 100, 2)} for k, cnt in transition_counts.items()},
        "transition_by_base_kind": {k: dict(v) for k, v in transition_by_kind.items()},
        "transition_by_difficulty": {k: dict(v) for k, v in transition_by_diff.items()},
        "aggregate_deltas": {
            "f1_missed_delta": round(phase1_summary["sv02_hn"]["aggregate_mean_sd"]["f1_missed"]["mean"] - phase1_summary["b5"]["aggregate_mean_sd"]["f1_missed"]["mean"], 2),
            "f2_wrong_span_delta": round(phase1_summary["sv02_hn"]["aggregate_mean_sd"]["f2_wrong_span"]["mean"] - phase1_summary["b5"]["aggregate_mean_sd"]["f2_wrong_span"]["mean"], 2),
            "f3_wrong_type_delta": round(phase1_summary["sv02_hn"]["aggregate_mean_sd"]["f3_wrong_type"]["mean"] - phase1_summary["b5"]["aggregate_mean_sd"]["f3_wrong_type"]["mean"], 2),
            "f4_false_pos_delta": round(phase1_summary["sv02_hn"]["aggregate_mean_sd"]["f4_false_pos"]["mean"] - phase1_summary["b5"]["aggregate_mean_sd"]["f4_false_pos"]["mean"], 2),
            "n_pred_delta": round(phase1_summary["sv02_hn"]["aggregate_mean_sd"]["n_pred"]["mean"] - phase1_summary["b5"]["aggregate_mean_sd"]["n_pred"]["mean"], 2),
            "precision_delta": round(phase1_summary["sv02_hn"]["aggregate_mean_sd"]["m1_precision"]["mean"] - phase1_summary["b5"]["aggregate_mean_sd"]["m1_precision"]["mean"], 4),
            "recall_delta": round(phase1_summary["sv02_hn"]["aggregate_mean_sd"]["m2_recall"]["mean"] - phase1_summary["b5"]["aggregate_mean_sd"]["m2_recall"]["mean"], 4),
            "f1_type_delta": round(phase1_summary["sv02_hn"]["aggregate_mean_sd"]["m3_f1"]["mean"] - phase1_summary["b5"]["aggregate_mean_sd"]["m3_f1"]["mean"], 4),
            "fpr_delta": round(phase1_summary["sv02_hn"]["aggregate_mean_sd"]["m6_fpr"]["mean"] - phase1_summary["b5"]["aggregate_mean_sd"]["m6_fpr"]["mean"], 4),
        }
    }

    with open(REPORTS_DIR / "sv03_b5_vs_sv02_transition.json", "w") as f:
        json.dump(phase9_transition, f, indent=2)

    # ------------------------------------------------------------------
    # Phase 10: Multi-Dimensional Error Interactions
    # ------------------------------------------------------------------
    print("Generating Phase 10: Multi-Dimensional Interactions...")
    interactions: dict[str, Any] = {
        "type_by_boundary_category": phase3_boundary["sv02_hn"]["by_pii_type"],
        "type_by_fp_category": phase4_fp["sv02_hn"]["by_predicted_type"],
        "language_by_boundary_category": phase3_boundary["sv02_hn"]["by_language"],
        "perturbation_by_boundary_category": phase3_boundary["sv02_hn"]["by_perturbation"],
        "decoy_class_by_predicted_type": {
            dcls: ddata["predicted_types"] for dcls, ddata in phase5_hn["sv02_hn"]["by_decoy_class"].items()
        },
    }
    with open(REPORTS_DIR / "sv03_error_interactions.json", "w") as f:
        json.dump(interactions, f, indent=2)

    # ------------------------------------------------------------------
    # Phase 11: Deterministic Representative Cases (Zero Raw PII)
    # ------------------------------------------------------------------
    print("Generating Phase 11: Representative Cases...")
    rep_cases = []
    # Deterministic selection from seed 42
    evals_42 = model_evals["sv02_hn"][42]["record_evals"]

    # Pick 1 representative for major boundary categories and false-positive categories
    seen_cats = set()
    for res in evals_42:
        rec = res.record_metadata
        text = rec.get("text", "")
        vid = rec["variant_id"]
        bid = rec.get("base_id", vid)

        # 1. Boundary cases
        for m in res.matching_result.matches:
            if m.is_type_match and not m.is_exact_span:
                cat = classify_boundary_error(m.gold, m.prediction, text)
                if cat not in seen_cats and cat in ("B2_WHITESPACE_GROUPING_MISMATCH", "B6_DELIMITER_INDUCED_SPLIT", "B3_PARTIAL_STRUCTURED_IDENTIFIER", "B1_PUNCTUATION_CAPTURED", "B4_SURROUNDING_LEXICAL_TOKEN_CAPTURED"):
                    seen_cats.add(cat)
                    redacted = create_redacted_context(text, min(m.gold.start, m.prediction.start), max(m.gold.end, m.prediction.end))
                    rep_cases.append({
                        "mechanism": cat,
                        "record_id": vid,
                        "base_id": bid,
                        "gold_type": m.gold.type,
                        "predicted_type": m.prediction.type,
                        "gold_span_length": m.gold.end - m.gold.start,
                        "predicted_span_length": m.prediction.end - m.prediction.start,
                        "gold_offsets": [m.gold.start, m.gold.end],
                        "predicted_offsets": [m.prediction.start, m.prediction.end],
                        "redacted_context": redacted,
                    })

        # 2. False positive cases
        golds = [m.gold for m in res.matching_result.matches] + res.matching_result.unmatched_gold
        for p in res.matching_result.unmatched_predictions:
            cat = classify_false_positive(p, rec, golds)
            if cat not in seen_cats and cat in ("FP1_NUMERIC_PATTERN_OVERMATCH", "FP2_ALPHANUMERIC_PATTERN_OVERMATCH", "FP4_UPI_LIKE_HANDLE", "FP11_HARD_NEGATIVE_DISTRACTOR", "FP6_ADDRESS_LIKE_CONTEXT"):
                seen_cats.add(cat)
                redacted = create_redacted_context(text, p.start, p.end)
                rep_cases.append({
                    "mechanism": cat,
                    "record_id": vid,
                    "base_id": bid,
                    "gold_type": "NONE",
                    "predicted_type": p.type,
                    "gold_span_length": 0,
                    "predicted_span_length": p.end - p.start,
                    "gold_offsets": None,
                    "predicted_offsets": [p.start, p.end],
                    "redacted_context": redacted,
                })

    with open(REPORTS_DIR / "sv03_representative_cases.json", "w") as f:
        json.dump(rep_cases, f, indent=2)

    print("=== ALL SV-03 DATA ARTIFACTS GENERATED SUCCESSFULLY ===")


if __name__ == "__main__":
    execute_sv03_analysis()
