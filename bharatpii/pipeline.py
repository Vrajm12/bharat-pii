"""High-level BharatPII inference engine."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
import torch

from .labels import DEFAULT_ID2LABEL, load_label_map
from .model import BharatPIIModel
from .tokenizer import BharatPIITokenizer
from .types import Entity, PredictionResult
from .version import __version__


class BharatPII:
    """Official high-level interface for Indian PII detection with BharatPII-CRF."""

    def __init__(
        self,
        model: BharatPIIModel,
        tokenizer: BharatPIITokenizer,
        id2label: dict[int, str],
        model_dir: Path,
        device: torch.device,
    ):
        self._model = model
        self._tokenizer = tokenizer
        self._id2label = id2label
        self._model_dir = model_dir
        self._device = device

    @property
    def device(self) -> torch.device:
        return self._device

    @property
    def labels(self) -> dict[int, str]:
        return dict(self._id2label)

    @property
    def total_parameters(self) -> int:
        return self._model.total_parameters

    @property
    def encoder_parameters(self) -> int:
        return self._model.encoder_parameters

    @property
    def trainable_head_parameters(self) -> int:
        return self._model.trainable_head_parameters

    @classmethod
    def from_pretrained(
        cls,
        model_path: str | Path,
        device: str | int | torch.device | None = None,
        verify_checksums: bool = False,
    ) -> BharatPII:
        """Load BharatPII-CRF from a local release directory."""
        path = Path(model_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Model directory does not exist: {path}")

        if verify_checksums:
            cls._verify_checksums(path)

        if device is None:
            dev = torch.device("cpu")
        elif isinstance(device, torch.device):
            dev = device
        elif isinstance(device, str):
            dev = torch.device(device)
        elif isinstance(device, int):
            dev = torch.device(f"cuda:{device}" if device >= 0 and torch.cuda.is_available() else "cpu")
        else:
            dev = torch.device("cpu")

        id2label, _ = load_label_map(path)
        tokenizer = BharatPIITokenizer.load_from_directory(path)
        model = BharatPIIModel.load_from_directory(path, device=dev)

        return cls(
            model=model,
            tokenizer=tokenizer,
            id2label=id2label,
            model_dir=path,
            device=dev,
        )

    @staticmethod
    def _verify_checksums(model_dir: Path):
        sums_file = model_dir / "SHA256SUMS.txt"
        if not sums_file.exists():
            raise FileNotFoundError(f"SHA256SUMS.txt not found in {model_dir}")

        with open(sums_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                exp_sha, fname = line.strip().split(maxsplit=1)
                fpath = model_dir / fname
                if not fpath.exists():
                    raise FileNotFoundError(f"Release file missing: {fname}")
                hasher = hashlib.sha256()
                with open(fpath, "rb") as bf:
                    while chunk := bf.read(1024 * 1024):
                        hasher.update(chunk)
                act_sha = hasher.hexdigest()
                if act_sha != exp_sha:
                    raise ValueError(f"Checksum mismatch for {fname}: expected {exp_sha}, got {act_sha}")

    def info(self) -> dict[str, Any]:
        """Return model metadata, parameter counts, and release provenance."""
        meta_file = self._model_dir / "model_metadata.json"
        metadata = {}
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

        return {
            "package_version": __version__,
            "model_name": metadata.get("model_name", "BharatPII-CRF"),
            "model_version": metadata.get("model_version", "1.0.0"),
            "model_directory": str(self._model_dir),
            "device": str(self._device),
            "total_parameters": self.total_parameters,
            "encoder_parameters": self.encoder_parameters,
            "trainable_head_parameters": self.trainable_head_parameters,
            "num_labels": len(self._id2label),
            "labels": self._id2label,
            "base_model": metadata.get("base_model", "XLM-RoBERTa-base"),
            "decoder": metadata.get("decoder", "linear-chain CRF"),
            "offline_mode": True,
        }

    def predict(self, text: str) -> PredictionResult:
        """Extract Indian PII entities from a single text string."""
        if not text or not text.strip():
            return PredictionResult(text=text, entities=[])

        encoding = self._tokenizer.encode(text)
        input_ids = encoding["input_ids"].to(self._device)
        attention_mask = encoding["attention_mask"].to(self._device)
        offset_mapping = encoding["offset_mapping"][0].tolist()

        valid_indices = [i for i, (s, e) in enumerate(offset_mapping) if s < e]
        if not valid_indices:
            return PredictionResult(text=text, entities=[])

        with torch.no_grad():
            encoder_out = self._model.encoder(input_ids=input_ids, attention_mask=attention_mask)
            hidden_states = encoder_out.last_hidden_state

            valid_idx_tensor = torch.tensor(valid_indices, dtype=torch.long, device=self._device)
            sub_hidden = hidden_states[:, valid_idx_tensor, :]

            emissions = self._model.head.classifier(sub_hidden)
            mask = torch.ones((1, len(valid_indices)), dtype=torch.bool, device=self._device)
            best_tags = self._model.head.crf.decode(emissions, mask)[0]
            emissions_softmax = torch.softmax(emissions[0], dim=-1)

        entities: list[Entity] = []
        current_entity: tuple[str, int, int, list[float]] | None = None

        for k, tag_id in enumerate(best_tags):
            tag_name = self._id2label[tag_id]
            s, e = offset_mapping[valid_indices[k]]
            token_conf = emissions_softmax[k, tag_id].item()

            if tag_name.startswith("B-"):
                if current_entity is not None:
                    ent_type, ent_s, ent_e, confs = current_entity
                    avg_score = sum(confs) / len(confs) if confs else 1.0
                    entities.append(
                        Entity(
                            text=text[ent_s:ent_e],
                            start=ent_s,
                            end=ent_e,
                            label=ent_type,
                            score=avg_score,
                        )
                    )
                current_entity = (tag_name[2:], s, e, [token_conf])
            elif tag_name.startswith("I-"):
                ent_type_tag = tag_name[2:]
                if current_entity is not None and current_entity[0] == ent_type_tag:
                    ent_type, ent_s, ent_e, confs = current_entity
                    current_entity = (ent_type, ent_s, e, confs + [token_conf])
                else:
                    if current_entity is not None:
                        ent_type, ent_s, ent_e, confs = current_entity
                        avg_score = sum(confs) / len(confs) if confs else 1.0
                        entities.append(
                            Entity(
                                text=text[ent_s:ent_e],
                                start=ent_s,
                                end=ent_e,
                                label=ent_type,
                                score=avg_score,
                            )
                        )
                    current_entity = (ent_type_tag, s, e, [token_conf])
            else:
                if current_entity is not None:
                    ent_type, ent_s, ent_e, confs = current_entity
                    avg_score = sum(confs) / len(confs) if confs else 1.0
                    entities.append(
                        Entity(
                            text=text[ent_s:ent_e],
                            start=ent_s,
                            end=ent_e,
                            label=ent_type,
                            score=avg_score,
                        )
                    )
                    current_entity = None

        if current_entity is not None:
            ent_type, ent_s, ent_e, confs = current_entity
            avg_score = sum(confs) / len(confs) if confs else 1.0
            entities.append(
                Entity(
                    text=text[ent_s:ent_e],
                    start=ent_s,
                    end=ent_e,
                    label=ent_type,
                    score=avg_score,
                )
            )

        entities.sort(key=lambda x: (x.start, x.end, x.label, -(x.score or 0.0)))
        return PredictionResult(text=text, entities=entities)

    def predict_batch(self, texts: list[str]) -> list[PredictionResult]:
        """Extract Indian PII entities across a batch of texts deterministically."""
        return [self.predict(t) for t in texts]
