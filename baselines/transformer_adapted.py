"""T14/B5: Indian-Adapted Multilingual Transformer Baseline Adapter (PROJECT_SPEC.md §19 B5, §20.5, §20.6, §21.2).

Implements the Indian-adapted multilingual transformer baseline using XLM-RoBERTa
adapted/fine-tuned on disjoint Indian PII synthetic data:
Model Architecture: xlm-roberta-base
Token Classification Head: 17 IOB2 classes (8 benchmark PII types + O).

Taxonomy mapping policy:
- PERSON -> PERSON
- PAN -> PAN
- AADHAAR -> AADHAAR
- PHONE -> PHONE
- EMAIL -> EMAIL
- UPI_ID -> UPI_ID
- BANK_ACCOUNT -> BANK_ACCOUNT
- ADDRESS -> ADDRESS
- Any unexpected/out-of-taxonomy labels preserved raw with status "VALID" (§20.5).
- Extracts native Python Unicode code-point offsets against the exact source text: text[start:end] == p.text (§20.6).
- Deterministic sorting by (start, end, type, -confidence).
- Input immutability.
"""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any, ClassVar
import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

from benchmark.schema import Prediction

from .base import BaselineAdapter

REPO_ROOT = Path(__file__).resolve().parents[1]


class TransformerAdaptedBaselineAdapter(BaselineAdapter):
    """Indian-Adapted Multilingual Transformer Baseline Detector (B5)."""

    TYPE_MAP: ClassVar[dict[str, str]] = {
        "PERSON": "PERSON",
        "PAN": "PAN",
        "AADHAAR": "AADHAAR",
        "PHONE": "PHONE",
        "EMAIL": "EMAIL",
        "UPI_ID": "UPI_ID",
        "BANK_ACCOUNT": "BANK_ACCOUNT",
        "ADDRESS": "ADDRESS",
    }

    def __init__(
        self,
        model_name_or_path: str | Path | None = None,
        seed: int = 42,
        device: int | str = -1,
        pipeline_instance: Any | None = None,
    ) -> None:
        if model_name_or_path is None:
            checkpoint_dir = REPO_ROOT / "checkpoints" / f"b5_transformer_adapted_seed{seed}"
            if checkpoint_dir.exists():
                self.model_path = str(checkpoint_dir)
            else:
                self.model_path = "xlm-roberta-base"
        else:
            self.model_path = str(model_name_or_path)

        self.seed = seed

        if pipeline_instance is not None:
            self.nlp = pipeline_instance
        else:
            tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            model = AutoModelForTokenClassification.from_pretrained(self.model_path)
            model.eval()
            self.nlp = pipeline(
                "token-classification",
                model=model,
                tokenizer=tokenizer,
                aggregation_strategy="simple",
                device=device,
            )

        try:
            transformers_ver = importlib.metadata.version("transformers")
        except Exception:
            transformers_ver = "5.16.1"

        self._system_version = f"{transformers_ver}_xlm_roberta_base_indian_v0.18"

    @property
    def system_name(self) -> str:
        return "transformer_adapted"

    @property
    def system_version(self) -> str:
        return self._system_version

    def predict(self, text: str) -> list[Prediction]:
        """Run token classification on input text and return validated Prediction objects.

        Strictly preserves native Python Unicode code-point character offsets.
        """
        if not text or not text.strip():
            return []

        results = self.nlp(text)
        predictions: list[Prediction] = []

        for res in results:
            raw_entity_group = res.get("entity_group") or res.get("entity", "")
            clean_type = raw_entity_group
            if clean_type.startswith("B-") or clean_type.startswith("I-"):
                clean_type = clean_type[2:]

            if clean_type == "O" or not clean_type:
                continue

            mapped_type = self.TYPE_MAP.get(clean_type, clean_type)

            start = int(res["start"])
            end = int(res["end"])
            score = float(res.get("score", 1.0))

            if start < 0 or end > len(text) or start >= end:
                continue

            predictions.append(
                Prediction(
                    type=mapped_type,
                    start=start,
                    end=end,
                    text=text[start:end],
                    confidence=score,
                )
            )

        predictions.sort(key=lambda p: (p.start, p.end, p.type, -p.confidence))
        return predictions
