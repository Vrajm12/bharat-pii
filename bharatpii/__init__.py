"""BharatPII: Official Python package for multilingual Indian PII detection."""

from .pipeline import BharatPII
from .types import Entity, PredictionResult
from .version import __version__

__all__ = ["BharatPII", "Entity", "PredictionResult", "__version__"]
