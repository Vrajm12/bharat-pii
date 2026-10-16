"""Data structures and types for BharatPII."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Entity:
    """A detected PII entity within a text span."""

    text: str
    start: int
    end: int
    label: str
    score: float | None = None

    def __post_init__(self):
        if self.start < 0:
            raise ValueError(f"start offset must be >= 0, got {self.start}")
        if self.end <= self.start:
            raise ValueError(f"end offset must be > start offset, got start={self.start}, end={self.end}")

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "text": self.text,
            "start": self.start,
            "end": self.end,
            "label": self.label,
        }
        if self.score is not None:
            d["score"] = round(self.score, 4)
        return d


@dataclass(frozen=True)
class PredictionResult:
    """Result of PII extraction on a single input text."""

    text: str
    entities: list[Entity]

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "entities": [e.to_dict() for e in self.entities],
        }

    def __len__(self) -> int:
        return len(self.entities)

    def __iter__(self):
        return iter(self.entities)

    def __getitem__(self, index: int) -> Entity:
        return self.entities[index]
