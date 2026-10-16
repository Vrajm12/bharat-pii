"""T13/B4: Multilingual Transformer Baseline Adapter (PROJECT_SPEC.md §19 B4, §20.5, §20.6).

Implements the zero-shot multilingual transformer baseline using XLM-RoBERTa
fine-tuned for high-resource multilingual Named Entity Recognition:
Model: Davlan/xlm-roberta-base-ner-hrl (revision: 253f557bd8249b8515114cfd7f71974fe5fa4d2f).

Taxonomy mapping policy (PROJECT_SPEC.md §20.5, resolving OQ-032):
- PER / PERSON -> PERSON
- LOC / ORG / DATE / MISC -> preserved raw as out-of-taxonomy labels with status "VALID".
- Unsupported Indian PII types (PAN, AADHAAR, PHONE, EMAIL, UPI_ID, BANK_ACCOUNT, ADDRESS)
  produce zero artificial predictions.
- Extracts character-for-character Python Unicode code-point offsets against the exact source text.
"""

from __future__ import annotations

import importlib.metadata
from typing import Any, ClassVar

from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

from benchmark.schema import Prediction

from .base import BaselineAdapter


class TransformerBaselineAdapter(BaselineAdapter):
    """Multilingual Transformer NER Baseline Detector (B4)."""

    DEFAULT_MODEL_NAME: str = "Davlan/xlm-roberta-base-ner-hrl"

    TYPE_MAP: ClassVar[dict[str, str]] = {
        "PER": "PERSON",
        "PERSON": "PERSON",
    }

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        device: int | str = -1,
        pipeline_instance: Any | None = None,
    ) -> None:
        self.model_name = model_name

        if pipeline_instance is not None:
            self.nlp = pipeline_instance
        else:
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForTokenClassification.from_pretrained(self.model_name)
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

        clean_model_name = self.model_name.replace("/", "_")
        self._system_version = f"{transformers_ver}_{clean_model_name}"

    @property
    def system_name(self) -> str:
        return "transformer"

    @property
    def system_version(self) -> str:
        return self._system_version

    def predict(self, text: str) -> list[Prediction]:
        """Run Transformer Token Classification on input text and return validated Prediction objects.

        Strictly preserves native Python Unicode code-point character offsets.
        """
        if not text or not text.strip():
            return []

        results = self.nlp(text)
        predictions: list[Prediction] = []

        for res in results:
            raw_entity_group = res.get("entity_group") or res.get("entity", "")
            mapped_type = self.TYPE_MAP.get(raw_entity_group, raw_entity_group)

            start = int(res["start"])
            end = int(res["end"])
            score = float(res.get("score", 1.0))

            predictions.append(
                Prediction(
                    type=mapped_type,
                    start=start,
                    end=end,
                    text=text[start:end],
                    confidence=score,
                )
            )

        # Sort deterministically by (start, end, type, -confidence)
        predictions.sort(
            key=lambda p: (p.start, p.end, p.type, -p.confidence if p.confidence is not None else 0.0)
        )
        return predictions
