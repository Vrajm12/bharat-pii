#!/usr/bin/env python3
"""
Generate Master Results Tables, Breakdown CSVs, and Comparison Reports
for the Indian PII Robustness Benchmark Final Scientific Freeze.
"""

import json
import os
import csv
from pathlib import Path

BASE_DIR = Path("n:/PROJECTS/indian-pii-robust")
REPORTS_DIR = BASE_DIR / "reports"
FINAL_DIR = REPORTS_DIR / "final"
FINAL_DIR.mkdir(parents=True, exist_ok=True)

# 1. Load baseline reports
b1_path = REPORTS_DIR / "evaluation_regex_1.0.0_v0.18.json"
b2_path = REPORTS_DIR / "evaluation_spacy_3.8.16_en_core_web_sm_3.8.0_v0.18.json"
b3_path = REPORTS_DIR / "evaluation_presidio_2.2.364_en_core_web_sm_in_enabled_v0.18.json"
b4_path = REPORTS_DIR / "evaluation_transformer_5.16.1_Davlan_xlm-roberta-base-ner-hrl_v0.18.json"
b5_agg_path = REPORTS_DIR / "evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_v0.18.json"
b6_agg_path = REPORTS_DIR / "experiments" / "b6" / "b6_error_summary.json"
b6_eval_agg_path = REPORTS_DIR / "experiments" / "b6" / "evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_v0.18.json"

with open(b1_path, "r", encoding="utf-8") as f:
    b1_data = json.load(f)
with open(b2_path, "r", encoding="utf-8") as f:
    b2_data = json.load(f)
with open(b3_path, "r", encoding="utf-8") as f:
    b3_data = json.load(f)
with open(b4_path, "r", encoding="utf-8") as f:
    b4_data = json.load(f)
with open(b5_agg_path, "r", encoding="utf-8") as f:
    b5_data = json.load(f)
with open(b6_agg_path, "r", encoding="utf-8") as f:
    b6_summary = json.load(f)

# Also load individual seed reports for B5 and B6
b5_seeds = {}
for s in [42, 43, 44]:
    p = REPORTS_DIR / f"evaluation_transformer_adapted_5.16.1_xlm_roberta_base_indian_seed{s}_v0.18.json"
    with open(p, "r", encoding="utf-8") as f:
        b5_seeds[s] = json.load(f)

b6_seeds = {}
for s in [42, 43, 44]:
    p = REPORTS_DIR / "experiments" / "b6" / f"evaluation_transformer_crf_5.16.1_xlm_roberta_base_indian_crf_seed{s}_v0.18.json"
    with open(p, "r", encoding="utf-8") as f:
        b6_seeds[s] = json.load(f)

print("All baseline JSON reports successfully loaded.")

# Construct master records
master_rows = [
    {
        "baseline_id": "B1",
        "system_name": "Regex (Canonical)",
        "version": "1.0.0",
        "mode": "Single-run (Deterministic)",
        "seeds": "N/A",
        "m1_precision": b1_data["metrics_overall"]["m1_precision"],
        "m1_sd": 0.0,
        "m2_recall": b1_data["metrics_overall"]["m2_recall"],
        "m2_sd": 0.0,
        "m3_f1": b1_data["metrics_overall"]["m3_f1"],
        "m3_sd": 0.0,
        "m4_exact_f1": b1_data["metrics_overall"]["m4_exact_f1"],
        "m4_sd": 0.0,
        "m5_type_accuracy": b1_data["metrics_overall"]["m5_type_accuracy"],
        "m5_sd": 0.0,
        "m6_fpr": b1_data["metrics_overall"]["m6_fpr"],
        "m6_sd": 0.0,
        "tp_exact": float(b1_data["metrics_overall"]["tp_exact"]),
        "tp_exact_sd": 0.0,
        "tp_type": float(b1_data["metrics_overall"]["tp_type"]),
        "tp_type_sd": 0.0,
        "f1_missed": float(b1_data["metrics_overall"]["f1_missed"]),
        "f1_missed_sd": 0.0,
        "f2_wrong_span": float(b1_data["metrics_overall"]["f2_wrong_span"]),
        "f2_wrong_span_sd": 0.0,
        "f3_wrong_type": float(b1_data["metrics_overall"]["f3_wrong_type"]),
        "f3_wrong_type_sd": 0.0,
        "f4_false_pos": float(b1_data["metrics_overall"]["f4_false_pos"]),
        "f4_false_pos_sd": 0.0,
    },
    {
        "baseline_id": "B2",
        "system_name": "spaCy en_core_web_sm",
        "version": "3.8.16",
        "mode": "Single-run (Pretrained)",
        "seeds": "N/A",
        "m1_precision": b2_data["metrics_overall"]["m1_precision"],
        "m1_sd": 0.0,
        "m2_recall": b2_data["metrics_overall"]["m2_recall"],
        "m2_sd": 0.0,
        "m3_f1": b2_data["metrics_overall"]["m3_f1"],
        "m3_sd": 0.0,
        "m4_exact_f1": b2_data["metrics_overall"]["m4_exact_f1"],
        "m4_sd": 0.0,
        "m5_type_accuracy": b2_data["metrics_overall"]["m5_type_accuracy"],
        "m5_sd": 0.0,
        "m6_fpr": b2_data["metrics_overall"]["m6_fpr"],
        "m6_sd": 0.0,
        "tp_exact": float(b2_data["metrics_overall"]["tp_exact"]),
        "tp_exact_sd": 0.0,
        "tp_type": float(b2_data["metrics_overall"]["tp_type"]),
        "tp_type_sd": 0.0,
        "f1_missed": float(b2_data["metrics_overall"]["f1_missed"]),
        "f1_missed_sd": 0.0,
        "f2_wrong_span": float(b2_data["metrics_overall"]["f2_wrong_span"]),
        "f2_wrong_span_sd": 0.0,
        "f3_wrong_type": float(b2_data["metrics_overall"]["f3_wrong_type"]),
        "f3_wrong_type_sd": 0.0,
        "f4_false_pos": float(b2_data["metrics_overall"]["f4_false_pos"]),
        "f4_false_pos_sd": 0.0,
    },
    {
        "baseline_id": "B3",
        "system_name": "Microsoft Presidio (IN enabled)",
        "version": "2.2.364",
        "mode": "Single-run (Hybrid Rules+spaCy)",
        "seeds": "N/A",
        "m1_precision": b3_data["metrics_overall"]["m1_precision"],
        "m1_sd": 0.0,
        "m2_recall": b3_data["metrics_overall"]["m2_recall"],
        "m2_sd": 0.0,
        "m3_f1": b3_data["metrics_overall"]["m3_f1"],
        "m3_sd": 0.0,
        "m4_exact_f1": b3_data["metrics_overall"]["m4_exact_f1"],
        "m4_sd": 0.0,
        "m5_type_accuracy": b3_data["metrics_overall"]["m5_type_accuracy"],
        "m5_sd": 0.0,
        "m6_fpr": b3_data["metrics_overall"]["m6_fpr"],
        "m6_sd": 0.0,
        "tp_exact": float(b3_data["metrics_overall"]["tp_exact"]),
        "tp_exact_sd": 0.0,
        "tp_type": float(b3_data["metrics_overall"]["tp_type"]),
        "tp_type_sd": 0.0,
        "f1_missed": float(b3_data["metrics_overall"]["f1_missed"]),
        "f1_missed_sd": 0.0,
        "f2_wrong_span": float(b3_data["metrics_overall"]["f2_wrong_span"]),
        "f2_wrong_span_sd": 0.0,
        "f3_wrong_type": float(b3_data["metrics_overall"]["f3_wrong_type"]),
        "f3_wrong_type_sd": 0.0,
        "f4_false_pos": float(b3_data["metrics_overall"]["f4_false_pos"]),
        "f4_false_pos_sd": 0.0,
    },
    {
        "baseline_id": "B4",
        "system_name": "XLM-RoBERTa Zero-Shot NER",
        "version": "5.16.1_Davlan",
        "mode": "Single-run (Pretrained Zero-shot)",
        "seeds": "N/A",
        "m1_precision": b4_data["metrics_overall"]["m1_precision"],
        "m1_sd": 0.0,
        "m2_recall": b4_data["metrics_overall"]["m2_recall"],
        "m2_sd": 0.0,
        "m3_f1": b4_data["metrics_overall"]["m3_f1"],
        "m3_sd": 0.0,
        "m4_exact_f1": b4_data["metrics_overall"]["m4_exact_f1"],
        "m4_sd": 0.0,
        "m5_type_accuracy": b4_data["metrics_overall"]["m5_type_accuracy"],
        "m5_sd": 0.0,
        "m6_fpr": b4_data["metrics_overall"]["m6_fpr"],
        "m6_sd": 0.0,
        "tp_exact": float(b4_data["metrics_overall"]["tp_exact"]),
        "tp_exact_sd": 0.0,
        "tp_type": float(b4_data["metrics_overall"]["tp_type"]),
        "tp_type_sd": 0.0,
        "f1_missed": float(b4_data["metrics_overall"]["f1_missed"]),
        "f1_missed_sd": 0.0,
        "f2_wrong_span": float(b4_data["metrics_overall"]["f2_wrong_span"]),
        "f2_wrong_span_sd": 0.0,
        "f3_wrong_type": float(b4_data["metrics_overall"]["f3_wrong_type"]),
        "f3_wrong_type_sd": 0.0,
        "f4_false_pos": float(b4_data["metrics_overall"]["f4_false_pos"]),
        "f4_false_pos_sd": 0.0,
    },
    {
        "baseline_id": "B5",
        "system_name": "Indian-Adapted XLM-RoBERTa",
        "version": "5.16.1_xlm_roberta_base_indian",
        "mode": "Mean ± SD (3 seeds)",
        "seeds": "42, 43, 44",
        "m1_precision": b5_data["metrics_overall_mean_sd"]["m1_precision"]["mean"],
        "m1_sd": b5_data["metrics_overall_mean_sd"]["m1_precision"]["sd"],
        "m2_recall": b5_data["metrics_overall_mean_sd"]["m2_recall"]["mean"],
        "m2_sd": b5_data["metrics_overall_mean_sd"]["m2_recall"]["sd"],
        "m3_f1": b5_data["metrics_overall_mean_sd"]["m3_f1"]["mean"],
        "m3_sd": b5_data["metrics_overall_mean_sd"]["m3_f1"]["sd"],
        "m4_exact_f1": b5_data["metrics_overall_mean_sd"]["m4_exact_f1"]["mean"],
        "m4_sd": b5_data["metrics_overall_mean_sd"]["m4_exact_f1"]["sd"],
        "m5_type_accuracy": b5_data["metrics_overall_mean_sd"]["m5_type_accuracy"]["mean"],
        "m5_sd": b5_data["metrics_overall_mean_sd"]["m5_type_accuracy"]["sd"],
        "m6_fpr": b5_data["metrics_overall_mean_sd"]["m6_fpr"]["mean"],
        "m6_sd": b5_data["metrics_overall_mean_sd"]["m6_fpr"]["sd"],
        "tp_exact": (456.0 + 460.0 + 450.0) / 3.0,
        "tp_exact_sd": 4.1096,
        "tp_type": (706.0 + 705.0 + 705.0) / 3.0,
        "tp_type_sd": 0.4714,
        "f1_missed": (1.0 + 1.0 + 1.0) / 3.0,
        "f1_missed_sd": 0.0,
        "f2_wrong_span": (250.0 + 245.0 + 255.0) / 3.0,
        "f2_wrong_span_sd": 4.0825,
        "f3_wrong_type": (17.0 + 18.0 + 18.0) / 3.0,
        "f3_wrong_type_sd": 0.4714,
        "f4_false_pos": (915.0 + 900.0 + 923.0) / 3.0,
        "f4_false_pos_sd": 9.5336,
    },
    {
        "baseline_id": "B6",
        "system_name": "Indian-Adapted XLM-RoBERTa + Linear CRF",
        "version": "5.16.1_xlm_roberta_base_indian_crf",
        "mode": "Mean ± SD (3 seeds)",
        "seeds": "42, 43, 44",
        "m1_precision": b6_summary["metrics_mean_sd"]["m1_precision"]["mean"],
        "m1_sd": b6_summary["metrics_mean_sd"]["m1_precision"]["sd"],
        "m2_recall": b6_summary["metrics_mean_sd"]["m2_recall"]["mean"],
        "m2_sd": b6_summary["metrics_mean_sd"]["m2_recall"]["sd"],
        "m3_f1": b6_summary["metrics_mean_sd"]["m3_f1"]["mean"],
        "m3_sd": b6_summary["metrics_mean_sd"]["m3_f1"]["sd"],
        "m4_exact_f1": b6_summary["metrics_mean_sd"]["m4_exact_f1"]["mean"],
        "m4_sd": b6_summary["metrics_mean_sd"]["m4_exact_f1"]["sd"],
        "m5_type_accuracy": b6_summary["metrics_mean_sd"]["m5_type_accuracy"]["mean"],
        "m5_sd": b6_summary["metrics_mean_sd"]["m5_type_accuracy"]["sd"],
        "m6_fpr": b6_summary["metrics_mean_sd"]["m6_fpr"]["mean"],
        "m6_sd": b6_summary["metrics_mean_sd"]["m6_fpr"]["sd"],
        "tp_exact": (601.0 + 592.0 + 596.0) / 3.0,
        "tp_exact_sd": 3.6818,
        "tp_type": (677.0 + 672.0 + 675.0) / 3.0,
        "tp_type_sd": 2.0548,
        "f1_missed": (7.0 + 9.0 + 7.0) / 3.0,
        "f1_missed_sd": 0.9428,
        "f2_wrong_span": (76.0 + 80.0 + 79.0) / 3.0,
        "f2_wrong_span_sd": 1.6997,
        "f3_wrong_type": (40.0 + 43.0 + 42.0) / 3.0,
        "f3_wrong_type_sd": 1.2472,
        "f4_false_pos": (356.0 + 352.0 + 347.0) / 3.0,
        "f4_false_pos_sd": 3.7417,
    },
]

# Write MASTER_RESULTS_TABLE.json
master_json_path = FINAL_DIR / "MASTER_RESULTS_TABLE.json"
with open(master_json_path, "w", encoding="utf-8") as f:
    json.dump({"benchmark": "Indian PII Robustness Benchmark", "version": "0.18", "freeze_stage": "SCIENTIFIC_FREEZE_B6", "baselines": master_rows}, f, indent=2)

# Write MASTER_RESULTS_TABLE.csv
master_csv_path = FINAL_DIR / "MASTER_RESULTS_TABLE.csv"
fieldnames = [
    "baseline_id", "system_name", "version", "mode", "seeds",
    "m1_precision", "m1_sd", "m2_recall", "m2_sd", "m3_f1", "m3_sd",
    "m4_exact_f1", "m4_sd", "m5_type_accuracy", "m5_sd", "m6_fpr", "m6_sd",
    "tp_exact", "tp_exact_sd", "tp_type", "tp_type_sd",
    "f1_missed", "f1_missed_sd", "f2_wrong_span", "f2_wrong_span_sd",
    "f3_wrong_type", "f3_wrong_type_sd", "f4_false_pos", "f4_false_pos_sd"
]
with open(master_csv_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in master_rows:
        writer.writerow(row)

# Write MASTER_RESULTS_TABLE.md
master_md_path = FINAL_DIR / "MASTER_RESULTS_TABLE.md"
with open(master_md_path, "w", encoding="utf-8") as f:
    f.write("# Indian PII Robustness Benchmark — Master Results Table\n\n")
    f.write("**Benchmark Version**: 0.18 | **Canonical Evaluation Records**: 964 | **Total Gold Entities ($N_{gold}$)**: 724\n\n")
    f.write("> **Note on Methodology**: Single-run baselines (B1–B4) are evaluated once on the canonical benchmark (deterministic or pretrained zero-shot). Adapted baselines (B5 and B6) are evaluated across three random adaptation seeds ($S \\in \\{42, 43, 44\\}$) and reported as Mean ± Standard Deviation. Exact boundary evaluation requires character-level span match `(start, end, type)`.\n\n")
    
    f.write("### Primary Performance Metrics\n\n")
    f.write("| ID | Baseline System | Mode | M1 Precision | M2 Recall | M3 F1 (Type-Strict) | M4 Exact F1 | M5 Type Acc | M6 FPR |\n")
    f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
    for r in master_rows:
        if r["mode"].startswith("Single-run"):
            f.write(f"| **{r['baseline_id']}** | {r['system_name']} | {r['mode']} | {r['m1_precision']:.4f} | {r['m2_recall']:.4f} | {r['m3_f1']:.4f} | **{r['m4_exact_f1']:.4f}** | {r['m5_type_accuracy']:.4f} | {r['m6_fpr']:.4f} |\n")
        else:
            f.write(f"| **{r['baseline_id']}** | {r['system_name']} | {r['mode']} | {r['m1_precision']:.4f} ± {r['m1_sd']:.4f} | {r['m2_recall']:.4f} ± {r['m2_sd']:.4f} | {r['m3_f1']:.4f} ± {r['m3_sd']:.4f} | **{r['m4_exact_f1']:.4f} ± {r['m4_sd']:.4f}** | {r['m5_type_accuracy']:.4f} ± {r['m5_sd']:.4f} | {r['m6_fpr']:.4f} ± {r['m6_sd']:.4f} |\n")

    f.write("\n### Error Partition Matrix (Authoritative Invariant: $TP_{exact} + F_1 + F_2 + F_3 = N_{gold} = 724$)\n\n")
    f.write("| ID | Baseline System | $TP_{exact}$ | $TP_{type}$ | $F_1$ Missed | $F_2$ Wrong Span | $F_3$ Wrong Type | $F_4$ False Pos |\n")
    f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
    for r in master_rows:
        if r["mode"].startswith("Single-run"):
            f.write(f"| **{r['baseline_id']}** | {r['system_name']} | {r['tp_exact']:.0f} | {r['tp_type']:.0f} | {r['f1_missed']:.0f} | {r['f2_wrong_span']:.0f} | {r['f3_wrong_type']:.0f} | {r['f4_false_pos']:.0f} |\n")
        else:
            f.write(f"| **{r['baseline_id']}** | {r['system_name']} | {r['tp_exact']:.1f} ± {r['tp_exact_sd']:.1f} | {r['tp_type']:.1f} ± {r['tp_type_sd']:.1f} | {r['f1_missed']:.1f} ± {r['f1_missed_sd']:.1f} | {r['f2_wrong_span']:.1f} ± {r['f2_wrong_span_sd']:.1f} | {r['f3_wrong_type']:.1f} ± {r['f3_wrong_type_sd']:.1f} | {r['f4_false_pos']:.1f} ± {r['f4_false_pos_sd']:.1f} |\n")

print("MASTER_RESULTS_TABLE written in json, csv, and md formats.")

# 2. Generate PER_TYPE_RESULTS.csv
types = ["NAME", "PHONE", "EMAIL", "AADHAAR", "PAN", "PASSPORT", "VOTER_ID", "DRIVING_LICENSE", "UPI_ID"]
per_type_rows = []

for pii_type in sorted(types):
    row = {"pii_type": pii_type}
    # B1
    t_b1 = b1_data.get("metrics_by_type", {}).get(pii_type, {})
    row["b1_tp_exact"] = t_b1.get("tp_exact", 0)
    row["b1_m4_exact_f1"] = t_b1.get("m4_exact_f1", 0.0)
    row["b1_m1_precision"] = t_b1.get("m1_precision", 0.0)
    row["b1_m2_recall"] = t_b1.get("m2_recall", 0.0)
    
    # B4
    t_b4 = b4_data.get("metrics_by_type", {}).get(pii_type, {})
    row["b4_tp_exact"] = t_b4.get("tp_exact", 0)
    row["b4_m4_exact_f1"] = t_b4.get("m4_exact_f1", 0.0)
    row["b4_m1_precision"] = t_b4.get("m1_precision", 0.0)
    row["b4_m2_recall"] = t_b4.get("m2_recall", 0.0)

    # B5 mean
    b5_vals = [b5_seeds[s].get("metrics_by_type", {}).get(pii_type, {}) for s in [42, 43, 44]]
    row["b5_tp_exact_mean"] = sum(v.get("tp_exact", 0) for v in b5_vals) / 3.0
    row["b5_m4_exact_f1_mean"] = sum(v.get("m4_exact_f1", 0.0) for v in b5_vals) / 3.0
    row["b5_m1_precision_mean"] = sum(v.get("m1_precision", 0.0) for v in b5_vals) / 3.0
    row["b5_m2_recall_mean"] = sum(v.get("m2_recall", 0.0) for v in b5_vals) / 3.0

    # B6 mean
    b6_vals = [b6_seeds[s].get("metrics_by_type", {}).get(pii_type, {}) for s in [42, 43, 44]]
    row["b6_tp_exact_mean"] = sum(v.get("tp_exact", 0) for v in b6_vals) / 3.0
    row["b6_m4_exact_f1_mean"] = sum(v.get("m4_exact_f1", 0.0) for v in b6_vals) / 3.0
    row["b6_m1_precision_mean"] = sum(v.get("m1_precision", 0.0) for v in b6_vals) / 3.0
    row["b6_m2_recall_mean"] = sum(v.get("m2_recall", 0.0) for v in b6_vals) / 3.0

    # delta
    row["delta_b6_vs_b5_exact_f1"] = row["b6_m4_exact_f1_mean"] - row["b5_m4_exact_f1_mean"]
    per_type_rows.append(row)

with open(FINAL_DIR / "PER_TYPE_RESULTS.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(per_type_rows[0].keys()))
    writer.writeheader()
    for r in per_type_rows:
        writer.writerow(r)

print("PER_TYPE_RESULTS.csv written.")

# 3. Generate PER_LANGUAGE_RESULTS.csv
langs = ["EN", "HINGLISH", "HI_DEVA_PII", "HI_LATN_PII", "MIXED"]
per_lang_rows = []

for lang in langs:
    row = {"language": lang}
    # B1
    l_b1 = b1_data.get("metrics_by_language", {}).get(lang, {})
    row["b1_m4_exact_f1"] = l_b1.get("m4_exact_f1", 0.0)
    row["b1_m1_precision"] = l_b1.get("m1_precision", 0.0)
    row["b1_m2_recall"] = l_b1.get("m2_recall", 0.0)

    # B4
    l_b4 = b4_data.get("metrics_by_language", {}).get(lang, {})
    row["b4_m4_exact_f1"] = l_b4.get("m4_exact_f1", 0.0)
    row["b4_m1_precision"] = l_b4.get("m1_precision", 0.0)
    row["b4_m2_recall"] = l_b4.get("m2_recall", 0.0)

    # B5 mean
    b5_lvals = [b5_seeds[s].get("metrics_by_language", {}).get(lang, {}) for s in [42, 43, 44]]
    row["b5_m4_exact_f1_mean"] = sum(v.get("m4_exact_f1", 0.0) for v in b5_lvals) / 3.0
    row["b5_m1_precision_mean"] = sum(v.get("m1_precision", 0.0) for v in b5_lvals) / 3.0
    row["b5_m2_recall_mean"] = sum(v.get("m2_recall", 0.0) for v in b5_lvals) / 3.0

    # B6 mean
    b6_lvals = [b6_seeds[s].get("metrics_by_language", {}).get(lang, {}) for s in [42, 43, 44]]
    row["b6_m4_exact_f1_mean"] = sum(v.get("m4_exact_f1", 0.0) for v in b6_lvals) / 3.0
    row["b6_m1_precision_mean"] = sum(v.get("m1_precision", 0.0) for v in b6_lvals) / 3.0
    row["b6_m2_recall_mean"] = sum(v.get("m2_recall", 0.0) for v in b6_lvals) / 3.0

    row["delta_b6_vs_b5_exact_f1"] = row["b6_m4_exact_f1_mean"] - row["b5_m4_exact_f1_mean"]
    per_lang_rows.append(row)

with open(FINAL_DIR / "PER_LANGUAGE_RESULTS.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(per_lang_rows[0].keys()))
    writer.writeheader()
    for r in per_lang_rows:
        writer.writerow(r)

print("PER_LANGUAGE_RESULTS.csv written.")

# 4. Generate PERTURBATION_RESULTS.csv
pert_b6_path = REPORTS_DIR / "experiments" / "b6" / "b6_perturbation_analysis.json"
pert_sv03_path = REPORTS_DIR / "experiments" / "sv03" / "sv03_perturbation_analysis.json"
with open(pert_b6_path, "r", encoding="utf-8") as f:
    pert_b6 = json.load(f)
with open(pert_sv03_path, "r", encoding="utf-8") as f:
    pert_sv03 = json.load(f)

pert_rows = []
all_pert_types = ["clean", "a1_whitespace", "a2_phonetic", "a3_ocr", "a4_script_mix", "a5_delimiters"]
for p in all_pert_types:
    b5_info = pert_sv03.get("b5_perturbations", {}).get(p, {})
    b6_info = pert_b6.get("b6_perturbations", {}).get(p, {})
    
    b5_exact_f1 = b5_info.get("m4_exact_f1_mean", b5_info.get("exact_f1", 0.0))
    b6_exact_f1 = b6_info.get("m4_exact_f1_mean", b6_info.get("exact_f1", 0.0))
    b5_prec = b5_info.get("m1_precision_mean", b5_info.get("precision", 0.0))
    b6_prec = b6_info.get("m1_precision_mean", b6_info.get("precision", 0.0))
    b5_rec = b5_info.get("m2_recall_mean", b5_info.get("recall", 0.0))
    b6_rec = b6_info.get("m2_recall_mean", b6_info.get("recall", 0.0))

    pert_rows.append({
        "perturbation_type": p,
        "b5_m4_exact_f1": b5_exact_f1,
        "b6_m4_exact_f1": b6_exact_f1,
        "delta_m4": b6_exact_f1 - b5_exact_f1,
        "b5_precision": b5_prec,
        "b6_precision": b6_prec,
        "b5_recall": b5_rec,
        "b6_recall": b6_rec,
    })

with open(FINAL_DIR / "PERTURBATION_RESULTS.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(pert_rows[0].keys()))
    writer.writeheader()
    for r in pert_rows:
        writer.writerow(r)

print("PERTURBATION_RESULTS.csv written.")

# 5. Generate DIFFICULTY_RESULTS.csv
diff_b6_path = REPORTS_DIR / "experiments" / "b6" / "b6_difficulty_analysis.json"
diff_sv03_path = REPORTS_DIR / "experiments" / "sv03" / "sv03_difficulty_analysis.json"
with open(diff_b6_path, "r", encoding="utf-8") as f:
    diff_b6 = json.load(f)
with open(diff_sv03_path, "r", encoding="utf-8") as f:
    diff_sv03 = json.load(f)

diff_rows = []
for d in ["EASY", "MEDIUM", "HARD"]:
    b5_d = diff_sv03.get("b5_difficulty", {}).get(d, {})
    b6_d = diff_b6.get("b6_difficulty", {}).get(d, {})
    diff_rows.append({
        "difficulty_tier": d,
        "b5_m4_exact_f1": b5_d.get("exact_f1", b5_d.get("m4_exact_f1", 0.0)),
        "b6_m4_exact_f1": b6_d.get("exact_f1", b6_d.get("m4_exact_f1", 0.0)),
        "b5_m1_precision": b5_d.get("precision", b5_d.get("m1_precision", 0.0)),
        "b6_m1_precision": b6_d.get("precision", b6_d.get("m1_precision", 0.0)),
        "b5_m2_recall": b5_d.get("recall", b5_d.get("m2_recall", 0.0)),
        "b6_m2_recall": b6_d.get("recall", b6_d.get("m2_recall", 0.0)),
    })

with open(FINAL_DIR / "DIFFICULTY_RESULTS.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(diff_rows[0].keys()))
    writer.writeheader()
    for r in diff_rows:
        writer.writerow(r)

print("DIFFICULTY_RESULTS.csv written.")

# 6. Generate SV02_ABLATION_TABLE.csv
sv02_master_path = REPORTS_DIR / "experiments" / "sv02" / "sv02_master_evaluation.json"
with open(sv02_master_path, "r", encoding="utf-8") as f:
    sv02_master = json.load(f)

sv02_rows = []
for var_name, var_info in sv02_master.get("variants", {}).items():
    s = var_info.get("summary", {})
    sv02_rows.append({
        "variant": var_name,
        "m1_precision_mean": s.get("m1_precision_mean", 0.0),
        "m1_precision_std": s.get("m1_precision_std", 0.0),
        "m2_recall_mean": s.get("m2_recall_mean", 0.0),
        "m2_recall_std": s.get("m2_recall_std", 0.0),
        "m3_f1_type_mean": s.get("m3_f1_type_mean", 0.0),
        "m3_f1_type_std": s.get("m3_f1_type_std", 0.0),
        "m4_f1_exact_mean": s.get("m4_f1_exact_mean", 0.0),
        "m4_f1_exact_std": s.get("m4_f1_exact_std", 0.0),
        "m5_type_accuracy_mean": s.get("m5_type_accuracy_mean", 0.0),
        "m5_type_accuracy_std": s.get("m5_type_accuracy_std", 0.0),
        "m6_fpr_mean": s.get("m6_fpr_mean", 0.0),
        "m6_fpr_std": s.get("m6_fpr_std", 0.0),
        "hard_negative_fpr_mean": s.get("hard_negative_fpr_mean", 0.0),
        "adversarial_f1_mean": s.get("adversarial_f1_mean", 0.0)
    })

with open(FINAL_DIR / "SV02_ABLATION_TABLE.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(sv02_rows[0].keys()))
    writer.writeheader()
    for r in sv02_rows:
        writer.writerow(r)

print("SV02_ABLATION_TABLE.csv written.")

# 7. Generate SV03_ERROR_TABLE.csv
sv03_rows = [
    {
        "error_category": "F1_missed_entities",
        "b5_mean": (1.0 + 1.0 + 1.0) / 3.0,
        "b6_mean": (7.0 + 9.0 + 7.0) / 3.0,
        "delta": (7.0 + 9.0 + 7.0) / 3.0 - (1.0 + 1.0 + 1.0) / 3.0,
        "description": "Gold entities completely undetected"
    },
    {
        "error_category": "F2_boundary_errors",
        "b5_mean": (250.0 + 245.0 + 255.0) / 3.0,
        "b6_mean": (76.0 + 80.0 + 79.0) / 3.0,
        "delta": (76.0 + 80.0 + 79.0) / 3.0 - (250.0 + 245.0 + 255.0) / 3.0,
        "description": "Detected correct type but span boundaries mismatched"
    },
    {
        "error_category": "B3_structured_truncation",
        "b5_mean": 179.0,
        "b6_mean": 25.0,
        "delta": -154.0,
        "description": "Structured identifiers (Aadhaar/PAN/Phone) truncated mid-sequence"
    },
    {
        "error_category": "F3_wrong_type",
        "b5_mean": (17.0 + 18.0 + 18.0) / 3.0,
        "b6_mean": (40.0 + 43.0 + 42.0) / 3.0,
        "delta": (40.0 + 43.0 + 42.0) / 3.0 - (17.0 + 18.0 + 18.0) / 3.0,
        "description": "Localized span but misclassified entity type"
    },
    {
        "error_category": "F4_false_positives",
        "b5_mean": (915.0 + 900.0 + 923.0) / 3.0,
        "b6_mean": (356.0 + 352.0 + 347.0) / 3.0,
        "delta": (356.0 + 352.0 + 347.0) / 3.0 - (915.0 + 900.0 + 923.0) / 3.0,
        "description": "Spurious prediction with no matching gold entity"
    },
    {
        "error_category": "FP9_duplicate_subspans",
        "b5_mean": 351.3,
        "b6_mean": 32.0,
        "delta": -319.3,
        "description": "Spurious partial sub-tokens extracted as standalone entities"
    }
]

with open(FINAL_DIR / "SV03_ERROR_TABLE.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(sv03_rows[0].keys()))
    writer.writeheader()
    for r in sv03_rows:
        writer.writerow(r)

print("SV03_ERROR_TABLE.csv written.")

# 8. Generate B1_B6_COMPARISON.md
b1_b6_md_path = FINAL_DIR / "B1_B6_COMPARISON.md"
with open(b1_b6_md_path, "w", encoding="utf-8") as f:
    f.write("# Comprehensive Baseline Comparison: B1 through B6\n\n")
    f.write("## 1. Executive Summary of Benchmark Progression\n\n")
    f.write("The Indian PII Robustness Benchmark systematically evaluates six distinct paradigm baselines across 964 canonical records containing 724 gold standard Indian PII entities under linguistic diversity (English, Hinglish, Hindi Devanagari, Hindi Latin, and Code-Mixed) and realistic synthetic perturbations (whitespace insertion, phonetic distortion, OCR noise, script mixing, and delimiter noise).\n\n")
    f.write("Across iterations B1 to B6, the benchmark uncovered critical failure modes in off-the-shelf and zero-shot architectures, resolved structural boundary degradation through transition-constrained decoding, and quantitatively mapped the residual frontiers of Indian PII extraction.\n\n")
    
    f.write("## 2. Baseline Architecture Overview\n\n")
    f.write("1. **B1 Regex (v1.0.0, locked canonical)**: Hand-engineered regular expressions for structured Indian PII (Aadhaar, PAN, Phone, Email). Rigid, high precision on clean canonical patterns ($M_1 = 0.6478$, exact $F_1 = 0.5773$), but completely fails on unstructured entities (Name) and perturbed inputs.\n")
    f.write("2. **B2 spaCy (`en_core_web_sm` v3.8.16)**: Off-the-shelf English statistical/neural pipeline. Severe domain mismatch ($M_1 = 0.0315$, $M_4 = 0.0330$), producing 883 false positives and failing to recognize Indic entity syntaxes.\n")
    f.write("3. **B3 Microsoft Presidio (v2.2.364 with IN recognizers)**: Standard industrial hybrid framework combining rules and spaCy context. Modest recall ($M_2 = 0.2956$) but severe over-extraction ($M_6 = 0.7539$, 2,105 false positives), demonstrating that standard global PII toolkits cannot be safely deployed without deep Indic domain adaptation.\n")
    f.write("4. **B4 Zero-Shot XLM-RoBERTa (`Davlan/xlm-roberta-base-ner-hrl`)**: Pretrained massively multilingual model. Cross-lingual zero-shot transfer yields poor recall ($M_2 = 0.1298$, $M_4 = 0.1444$) due to lack of exposure to Indian identifier schemas.\n")
    f.write("5. **B5 Indian-Adapted XLM-RoBERTa (v5.16.1)**: Fine-tuned on Indian PII adaptation corpus with independent linear classification head. Achieves near-perfect entity localization recall ($M_2 = 0.9742 \\pm 0.0008$, type-strict $F_1 = 0.5978 \\pm 0.0024$), but suffers severe exact-boundary collapse ($M_4 = 0.3860 \\pm 0.0050$) caused by independent token decoding, yielding 250.0 boundary truncation errors and 912.7 false positives.\n")
    f.write("6. **B6 Indian-Adapted XLM-RoBERTa + Linear CRF (v5.16.1)**: Adds a first-order Linear Chain CRF decoding layer enforcing BIO sequence transition validity. Resolves the boundary collapse: $M_4$ exact $F_1$ rises by **+0.2795** (+72.4% relative, reaching $0.6654 \\pm 0.0034$), precision surges to $0.6315 \\pm 0.0021$, boundary errors drop by 68.7% (to 78.3), and duplicate sub-token extractions drop by 90.9%.\n\n")

    f.write("## 3. Comparative Metric Synthesis\n\n")
    f.write("| Baseline | Paradigm | M1 Prec | M2 Rec | M3 F1 (Type) | M4 Exact F1 | M6 FPR | $TP_{exact}$ | $F_2$ (Boundary) | $F_4$ (FP) |\n")
    f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
    for r in master_rows:
        mode_str = "Single-run" if r["mode"].startswith("Single-run") else "3-seed Mean"
        f.write(f"| **{r['baseline_id']}** {r['system_name']} | {mode_str} | {r['m1_precision']:.4f} | {r['m2_recall']:.4f} | {r['m3_f1']:.4f} | **{r['m4_exact_f1']:.4f}** | {r['m6_fpr']:.4f} | {r['tp_exact']:.1f} | {r['f2_wrong_span']:.1f} | {r['f4_false_pos']:.1f} |\n")

    f.write("\n## 4. Key Scientific Transitions & Lessons\n\n")
    f.write("- **Domain Adaptation is Indispensable**: Pretrained zero-shot models (B4) achieve only 0.1444 exact F1. Task adaptation (B5) lifts recall from 0.1298 to 0.9742.\n")
    f.write("- **Independent Token Heads Cause Boundary Collapse**: In B5, lack of transition constraints allowed sub-word tokens to be omitted or emitted spuriously ($FP_9 = 351.3$), crippling exact boundary precision.\n")
    f.write("- **Sequence-Constrained Decoding Solves Boundary Truncation**: B6's CRF layer eliminates illegal transition states ($O \\to I$, cross-type boundaries), restoring 151 boundary error entities to exact True Positives (in seed 42) and dropping false positives from 912.7 to 351.7.\n")
    f.write("- **Persistent Frontiers**: Both B5 and B6 retain elevated FPR on held-out hard negative decoy numbers (random 12-digit and 10-digit non-PII strings) and experience boundary degradation under A1 whitespace perturbation, defining the primary technical agenda for future work.\n")

print("B1_B6_COMPARISON.md written.")

# 9. Generate FINAL_METRIC_DEFINITIONS.md
metric_def_path = FINAL_DIR / "FINAL_METRIC_DEFINITIONS.md"
with open(metric_def_path, "w", encoding="utf-8") as f:
    f.write("# Authoritative Metric Definitions and Mathematical Formulations\n\n")
    f.write("This document formalizes the canonical evaluation definitions and mathematical guarantees used uniformly across all baselines (B1–B6) in the Indian PII Robustness Benchmark.\n\n")
    f.write("## 1. Core Sets and Primitives\n\n")
    f.write("Let $D$ be the benchmark corpus consisting of $N = 964$ records. For each record $r \\in D$, let:\n")
    f.write("- $G_r = \\{(s_i, e_i, t_i)\\}$ be the set of gold standard PII entities, where $s_i$ is the 0-indexed start character offset, $e_i$ is the end character offset (exclusive), and $t_i \\in \\mathcal{T}$ is the PII entity type.\n")
    f.write("- $P_r = \\{(\\hat{s}_j, \\hat{e}_j, \\hat{t}_j)\\}$ be the set of predicted entities generated by the model.\n")
    f.write("- Total gold entities: $N_{gold} = \\sum_{r \\in D} |G_r| = 724$.\n")
    f.write("- Total predicted entities: $N_{pred} = \\sum_{r \\in D} |P_r|$.\n\n")
    f.write("Entity types $\\mathcal{T}$ comprise 9 Indian PII categories: `NAME`, `PHONE`, `EMAIL`, `AADHAAR`, `PAN`, `PASSPORT`, `VOTER_ID`, `DRIVING_LICENSE`, and `UPI_ID`.\n\n")
    f.write("## 2. Match Classifications\n\n")
    f.write("For each record, bipartite matching is performed between gold entities $g \\in G_r$ and predicted entities $p \\in P_r$:\n\n")
    f.write("1. **Exact Match ($TP_{exact}$)**:\n")
    f.write("   $$\\hat{s}_j = s_i \\quad \\land \\quad \\hat{e}_j = e_i \\quad \\land \\quad \\hat{t}_j = t_i$$\n")
    f.write("   The prediction exactly matches the gold start offset, end offset, and entity type.\n\n")
    f.write("2. **Type-Strict Match ($TP_{type}$)**:\n")
    f.write("   $$\\hat{t}_j = t_i \\quad \\land \\quad \\max(s_i, \\hat{s}_j) < \\min(e_i, \\hat{e}_j)$$\n")
    f.write("   The prediction has the correct entity type and has non-zero character overlap with the gold span. By construction: $TP_{type} = TP_{exact} + F_2$.\n\n")
    f.write("3. **Error Partitions**:\n")
    f.write("   - **$F_1$ Missed (False Negative)**: A gold entity $g \\in G_r$ with zero character overlap with any prediction in $P_r$.\n")
    f.write("   - **$F_2$ Wrong Span (Boundary Error)**: A gold entity $g \\in G_r$ that overlaps with a prediction having $\\hat{t}_j = t_i$, but where $(\\hat{s}_j, \\hat{e}_j) \\neq (s_i, e_i)$.\n")
    f.write("   - **$F_3$ Wrong Type (Classification Error)**: A gold entity $g \\in G_r$ that overlaps with a prediction where $\\hat{t}_j \\neq t_i$.\n")
    f.write("   - **$F_4$ False Positive**: A predicted entity $p \\in P_r$ that has zero overlap with any gold entity, or excess spurious predictions over the matched gold entity.\n\n")
    f.write("## 3. Mathematical Invariants\n\n")
    f.write("The benchmark guarantees the following mathematical identity for every baseline and seed:\n\n")
    f.write("$$TP_{exact} + F_1 + F_2 + F_3 = N_{gold} = 724$$\n\n")
    f.write("$$TP_{type} = TP_{exact} + F_2$$\n\n")
    f.write("$$N_{pred} = TP_{type} + F_3 + F_4$$\n\n")
    f.write("## 4. Formal Metric Definitions\n\n")
    f.write("1. **M1 Precision (Type-Strict)**:\n")
    f.write("   $$M_1 = \\frac{TP_{type}}{N_{pred}} = \\frac{TP_{type}}{TP_{type} + F_3 + F_4}$$\n\n")
    f.write("2. **M2 Recall (Type-Strict)**:\n")
    f.write("   $$M_2 = \\frac{TP_{type}}{N_{gold}} = \\frac{TP_{type}}{TP_{exact} + F_1 + F_2 + F_3}$$\n\n")
    f.write("3. **M3 F1 Score (Type-Strict)**:\n")
    f.write("   $$M_3 = \\frac{2 \\cdot M_1 \\cdot M_2}{M_1 + M_2} = \\frac{2 \\cdot TP_{type}}{N_{pred} + N_{gold}}$$\n\n")
    f.write("4. **M4 Exact F1 Score**:\n")
    f.write("   $$P_{exact} = \\frac{TP_{exact}}{N_{pred}}, \\quad R_{exact} = \\frac{TP_{exact}}{N_{gold}}$$\n")
    f.write("   $$M_4 = \\frac{2 \\cdot P_{exact} \\cdot R_{exact}}{P_{exact} + R_{exact}} = \\frac{2 \\cdot TP_{exact}}{N_{pred} + N_{gold}}$$\n\n")
    f.write("5. **M5 Type Accuracy**:\n")
    f.write("   $$M_5 = \\frac{TP_{type}}{TP_{type} + F_3} = \\frac{TP_{type}}{\\text{Localized Predictions}}$$\n\n")
    f.write("6. **M6 False Positive Rate (Entity-level)**:\n")
    f.write("   $$M_6 = \\frac{F_4}{N_{pred}}$$\n\n")
    f.write("7. **Hard-Negative Record-Level Decoy FPR**:\n")
    f.write("   $$FPR_{HN} = \\frac{\\sum_{r \\in D_{HN}} \\mathbb{I}(|P_r| > 0)}{|D_{HN}|}$$\n")
    f.write("   where $D_{HN}$ is the set of 50 pure hard-negative records containing no genuine PII.\n")

print("FINAL_METRIC_DEFINITIONS.md written.")
print("ALL MASTER TABLES SUCCESSFULLY CREATED.")
