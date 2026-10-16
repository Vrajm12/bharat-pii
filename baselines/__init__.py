"""T13: Baseline adapters and prediction validation (PROJECT_SPEC.md §19, §20.7)."""

from .base import BaselineAdapter, validate_predictions
from .presidio import PresidioBaselineAdapter
from .regex import RegexBaselineAdapter
from .spacy import SpacyBaselineAdapter
from .transformer import TransformerBaselineAdapter
from .transformer_adapted import TransformerAdaptedBaselineAdapter

__all__ = [
    "BaselineAdapter",
    "validate_predictions",
    "RegexBaselineAdapter",
    "SpacyBaselineAdapter",
    "PresidioBaselineAdapter",
    "TransformerBaselineAdapter",
    "TransformerAdaptedBaselineAdapter",
]
