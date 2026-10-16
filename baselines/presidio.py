"""T13/B3: Microsoft Presidio Baseline Adapter (PROJECT_SPEC.md §19 B3, §19.2, §20.5, §20.6).

Implements the Microsoft Presidio production framework baseline.
Uses standard off-the-shelf Presidio AnalyzerEngine with spaCy (en_core_web_sm)
and enabled India-specific predefined recognizers (InPanRecognizer, InAadhaarRecognizer,
InPassportRecognizer, InVehicleRegistrationRecognizer, InVoterRecognizer, InGstinRecognizer).

Mapping policy (PROJECT_SPEC.md §20.5, resolving OQ-032):
- PERSON -> PERSON
- IN_PAN -> PAN
- IN_AADHAAR -> AADHAAR
- PHONE_NUMBER -> PHONE
- EMAIL_ADDRESS -> EMAIL
- Out-of-taxonomy labels (ORGANIZATION, LOCATION, DATE_TIME, URL, UK_NHS, etc.) are emitted
  with their raw type strings and evaluated as standard F4 false positives / F3 type errors.
- Unsupported PII types (UPI_ID, BANK_ACCOUNT, ADDRESS) produce zero artificial predictions.
"""

from __future__ import annotations

import importlib.metadata
from typing import ClassVar

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.predefined_recognizers import (
    InAadhaarRecognizer,
    InGstinRecognizer,
    InPanRecognizer,
    InPassportRecognizer,
    InVehicleRegistrationRecognizer,
    InVoterRecognizer,
)

from benchmark.schema import Prediction

from .base import BaselineAdapter


class PresidioBaselineAdapter(BaselineAdapter):
    """Microsoft Presidio Baseline Detector (B3) with India recognizers enabled."""

    TYPE_MAP: ClassVar[dict[str, str]] = {
        "PERSON": "PERSON",
        "IN_PAN": "PAN",
        "IN_AADHAAR": "AADHAAR",
        "PHONE_NUMBER": "PHONE",
        "EMAIL_ADDRESS": "EMAIL",
    }

    def __init__(
        self,
        nlp_model_name: str = "en_core_web_sm",
        analyzer: AnalyzerEngine | None = None,
        language: str = "en",
    ) -> None:
        self.nlp_model_name = nlp_model_name
        self.language = language

        if analyzer is not None:
            self.analyzer = analyzer
        else:
            provider = NlpEngineProvider(
                nlp_configuration={
                    "nlp_engine_name": "spacy",
                    "models": [{"lang_code": "en", "model_name": self.nlp_model_name}],
                }
            )
            nlp_engine = provider.create_engine()
            self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)

            # Enable standard India predefined country recognizers (§19.2)
            india_recognizers = [
                InAadhaarRecognizer(),
                InPanRecognizer(),
                InPassportRecognizer(),
                InVehicleRegistrationRecognizer(),
                InVoterRecognizer(),
                InGstinRecognizer(),
            ]
            for r in india_recognizers:
                self.analyzer.registry.add_recognizer(r)

        try:
            pkg_version = importlib.metadata.version("presidio-analyzer")
        except Exception:
            pkg_version = "2.2.364"

        self._system_version = f"{pkg_version}_{self.nlp_model_name}_in_enabled"

    @property
    def system_name(self) -> str:
        return "presidio"

    @property
    def system_version(self) -> str:
        return self._system_version

    def predict(self, text: str) -> list[Prediction]:
        """Run Presidio Analyzer on input text and return validated Prediction objects.

        Strictly preserves native Python Unicode code-point character offsets.
        """
        results = self.analyzer.analyze(text=text, language=self.language)
        predictions: list[Prediction] = []

        for res in results:
            # Map entity type if in taxonomy; preserve raw label if out-of-taxonomy (§20.5)
            mapped_type = self.TYPE_MAP.get(res.entity_type, res.entity_type)
            predictions.append(
                Prediction(
                    type=mapped_type,
                    start=res.start,
                    end=res.end,
                    text=text[res.start : res.end],
                    confidence=float(res.score),
                )
            )

        # Sort deterministically by (start, end, type, -confidence)
        predictions.sort(key=lambda p: (p.start, p.end, p.type, -p.confidence if p.confidence is not None else 0.0))
        return predictions
