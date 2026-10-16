"""T13/B2: spaCy NER Baseline Adapter (PROJECT_SPEC.md §19 B2, §19.2, §20.5, §20.6).

Implements the general-purpose spaCy NLP baseline detector.
Uses standard off-the-shelf pretrained spaCy NER pipeline (e.g. en_core_web_sm).

Mapping policy (PROJECT_SPEC.md §20.5, resolving OQ-032):
- PERSON -> PERSON
- Out-of-taxonomy labels (ORG, GPE, LOC, DATE, CARDINAL, etc.) are emitted with their
  raw type strings and evaluated as standard F4 false positives / F3 type misclassifications.
- Unsupported PII types produce no artificial predictions.
"""

from __future__ import annotations

import spacy
from spacy.language import Language

from benchmark.schema import Prediction

from .base import BaselineAdapter


class SpacyBaselineAdapter(BaselineAdapter):
    """General-purpose spaCy NER Baseline Detector (B2)."""

    def __init__(self, model_name: str = "en_core_web_sm", nlp: Language | None = None) -> None:
        self.model_name = model_name
        self.nlp = nlp if nlp is not None else spacy.load(model_name)
        model_version = self.nlp.meta.get("version", "unknown")
        self._system_version = f"{spacy.__version__}_{self.model_name}_{model_version}"

    @property
    def system_name(self) -> str:
        return "spacy"

    @property
    def system_version(self) -> str:
        return self._system_version

    def predict(self, text: str) -> list[Prediction]:
        """Run spaCy pipeline on input text and return validated Prediction objects.

        Strictly preserves Python Unicode code-point character offsets.
        """
        doc = self.nlp(text)
        predictions: list[Prediction] = []

        for ent in doc.ents:
            # Map PERSON to benchmark taxonomy type; preserve all out-of-taxonomy labels as-is
            ent_type = ent.label_
            predictions.append(
                Prediction(
                    type=ent_type,
                    start=ent.start_char,
                    end=ent.end_char,
                    text=ent.text,
                    confidence=1.0,
                )
            )

        # Sort deterministically by (start, end, type)
        predictions.sort(key=lambda p: (p.start, p.end, p.type))
        return predictions
