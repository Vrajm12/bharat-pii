"""T12: Adversarial perturbation transform functions (guidelines.md v0.18)."""

from .abbreviation import A4_ABBREVIATION_MAP, realize_abbreviation
from .char_variation import (
    OCR_HOMOGLYPH_MAP,
    apply_char_variation,
    realize_char_variation,
)
from .label_obfuscation import A3_LABEL_MAP, realize_label_obfuscation
from .punctuation import apply_punctuation, realize_punctuation
from .spacing import apply_spacing, realize_spacing

__all__ = [
    "apply_spacing",
    "realize_spacing",
    "apply_punctuation",
    "realize_punctuation",
    "A3_LABEL_MAP",
    "realize_label_obfuscation",
    "A4_ABBREVIATION_MAP",
    "realize_abbreviation",
    "OCR_HOMOGLYPH_MAP",
    "apply_char_variation",
    "realize_char_variation",
]
