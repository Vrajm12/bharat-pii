"""SV-02 Benchmark Evaluation Script.

Evaluates trained SV-02 checkpoints against the locked canonical 964-record benchmark.
Uses the canonical benchmark runner and evaluator.
Persists prediction and evaluation report artifacts in SV-02 isolated namespaces.
Computes summary metrics (mean +- SD) across seeds [42, 43, 44] for each variant.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
from transformers import pipeline

from baselines.transformer_adapted import TransformerAdaptedBaselineAdapter
from benchmark.runner import load_canonical_benchmark_records, run_experiment

PREDICTIONS_DIR = REPO_ROOT / "predictions" / "experiments" / "sv02"
REPORTS_DIR = REPO_ROOT / "reports" / "experiments" / "sv02"
CHECKPOINTS_DIR = REPO_ROOT / "checkpoints" / "sv02"


class SV02Adapter(TransformerAdaptedBaselineAdapter):
    """Adapter for SV-02 ablation variants."""

    def __init__(self, checkpoint_path: Path, variant_name: str, seed: int):
        nlp = pipeline(
            "token-classification",
            model=str(checkpoint_path),
            tokenizer=str(checkpoint_path),
            aggregation_strategy="simple",
            device=-1,
        )
        super().__init__(model_name_or_path=checkpoint_path, seed=seed, pipeline_instance=nlp)
        self._custom_system_name = f"sv02_{variant_name}"
        self._custom_system_version = f"5.16.1_seed{seed}"

    @property
    def system_name(self) -> str:
        return self._custom_system_name

    @property
    def system_version(self) -> str:
        return self._custom_system_version


def evaluate_all():
    print("=== STARTING SV-02 FORMAL BENCHMARK EVALUATIONS ===")
    records = load_canonical_benchmark_records()
    print(f"Loaded {len(records)} canonical records.")

    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    variants = ["b5_hard_negative", "b5_positive_matched", "b5_format_diversity"]
    master_results = {}

    for var in variants:
        seed_reports = []
        for seed in [42, 43, 44]:
            ckpt_path = CHECKPOINTS_DIR / f"{var}_seed{seed}"
            if not ckpt_path.exists():
                raise FileNotFoundError(f"Missing checkpoint: {ckpt_path}")

            print(f"\n--- Evaluating {var} (Seed {seed}) ---")
            t0 = time.time()
            adapter = SV02Adapter(checkpoint_path=ckpt_path, variant_name=var, seed=seed)
            report = run_experiment(
                adapter=adapter,
                records=records,
                dataset_version="0.18",
                save_artifacts=True,
                predictions_dir=PREDICTIONS_DIR,
                reports_dir=REPORTS_DIR,
            )
            elapsed = time.time() - t0
            print(f"Completed in {elapsed:.2f}s.")
            m = report["metrics_overall"]
            print(f"  Precision: {m['m1_precision']:.4f}, Recall: {m['m2_recall']:.4f}, F1 Type: {m['m3_f1']:.4f}, FPR: {m['m6_fpr']:.4f}")
            seed_reports.append(report)

        # Aggregate across seeds
        m1 = [r["metrics_overall"]["m1_precision"] for r in seed_reports]
        m2 = [r["metrics_overall"]["m2_recall"] for r in seed_reports]
        m3 = [r["metrics_overall"]["m3_f1"] for r in seed_reports]
        m4 = [r["metrics_overall"]["m4_exact_f1"] for r in seed_reports]
        m5 = [r["metrics_overall"]["m5_type_accuracy"] for r in seed_reports]
        m6 = [r["metrics_overall"]["m6_fpr"] for r in seed_reports]

        # Hard-negative FPR (from metrics_by_base_kind -> HARD_NEGATIVE)
        hn_fprs = [r["metrics_by_base_kind"]["HARD_NEGATIVE"]["m6_fpr"] for r in seed_reports]

        # Adversarial F1 (micro mean over perturbation families)
        adv_f1s = []
        for r in seed_reports:
            pert_fams = [k for k in r["metrics_by_perturbation_family"] if k not in ("NONE", None)]
            tp_sum = sum(r["metrics_by_perturbation_family"][f]["tp_type"] for f in pert_fams)
            fp_sum = sum(r["metrics_by_perturbation_family"][f]["f4_false_pos"] for f in pert_fams)
            fn_sum = sum(
                r["metrics_by_perturbation_family"][f]["f1_missed"]
                + r["metrics_by_perturbation_family"][f]["f2_wrong_span"]
                + r["metrics_by_perturbation_family"][f]["f3_wrong_type"]
                for f in pert_fams
            )
            p = tp_sum / (tp_sum + fp_sum) if (tp_sum + fp_sum) > 0 else 0.0
            rec = tp_sum / (tp_sum + fn_sum) if (tp_sum + fn_sum) > 0 else 0.0
            adv_f1 = (2 * p * rec) / (p + rec) if (p + rec) > 0 else 0.0
            adv_f1s.append(adv_f1)

        summary = {
            "m1_precision_mean": round(float(np.mean(m1)), 4),
            "m1_precision_std": round(float(np.std(m1)), 4),
            "m2_recall_mean": round(float(np.mean(m2)), 4),
            "m2_recall_std": round(float(np.std(m2)), 4),
            "m3_f1_type_mean": round(float(np.mean(m3)), 4),
            "m3_f1_type_std": round(float(np.std(m3)), 4),
            "m4_f1_exact_mean": round(float(np.mean(m4)), 4),
            "m4_f1_exact_std": round(float(np.std(m4)), 4),
            "m5_type_accuracy_mean": round(float(np.mean(m5)), 4),
            "m5_type_accuracy_std": round(float(np.std(m5)), 4),
            "m6_fpr_mean": round(float(np.mean(m6)), 4),
            "m6_fpr_std": round(float(np.std(m6)), 4),
            "hard_negative_fpr_mean": round(float(np.mean(hn_fprs)), 4),
            "hard_negative_fpr_std": round(float(np.std(hn_fprs)), 4),
            "adversarial_f1_mean": round(float(np.mean(adv_f1s)), 4),
            "adversarial_f1_std": round(float(np.std(adv_f1s)), 4),
        }

        agg_report = {
            "variant": var,
            "seeds": [42, 43, 44],
            "summary": summary,
            "seed_evaluations": seed_reports,
        }

        agg_path = REPORTS_DIR / f"evaluation_{var}_aggregated.json"
        with open(agg_path, "w", encoding="utf-8") as f:
            json.dump(agg_report, f, indent=2)

        master_results[var] = agg_report
        print(f"\nVariant {var} Aggregate:")
        print(f"  M1 Precision: {summary['m1_precision_mean']} +- {summary['m1_precision_std']}")
        print(f"  M2 Recall:    {summary['m2_recall_mean']} +- {summary['m2_recall_std']}")
        print(f"  M3 Type F1:   {summary['m3_f1_type_mean']} +- {summary['m3_f1_type_std']}")
        print(f"  M6 FPR:       {summary['m6_fpr_mean']} +- {summary['m6_fpr_std']}")
        print(f"  HN FPR:       {summary['hard_negative_fpr_mean']} +- {summary['hard_negative_fpr_std']}")
        print(f"  Adv F1:       {summary['adversarial_f1_mean']} +- {summary['adversarial_f1_std']}")

    master_path = REPORTS_DIR / "sv02_master_evaluation.json"
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "benchmark": "Indian PII Robustness Benchmark",
                "task": "SV-02",
                "variants": master_results,
            },
            f,
            indent=2,
        )

    print("\n=== ALL SV-02 EVALUATIONS COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    evaluate_all()
