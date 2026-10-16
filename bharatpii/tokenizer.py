"""Offline tokenizer loading and span offset mapping."""

from __future__ import annotations

from pathlib import Path
from transformers import AutoTokenizer, PreTrainedTokenizerFast


class BharatPIITokenizer:
    """Wrapper for offline tokenization and character offset alignment."""

    def __init__(self, tokenizer: PreTrainedTokenizerFast):
        self._tokenizer = tokenizer

    @property
    def tokenizer(self) -> PreTrainedTokenizerFast:
        return self._tokenizer

    @classmethod
    def load_from_directory(cls, model_dir: str | Path) -> BharatPIITokenizer:
        path = Path(model_dir)
        tok_file = path / "tokenizer.json"
        if not tok_file.exists():
            raise FileNotFoundError(f"Missing tokenizer file: {tok_file}")

        tokenizer = AutoTokenizer.from_pretrained(str(path), local_files_only=True)
        return cls(tokenizer)

    def encode(self, text: str):
        return self._tokenizer(
            text,
            return_offsets_mapping=True,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
