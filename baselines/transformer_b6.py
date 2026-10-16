"""Task B6: Span-Aware / Sequence-Constrained Indian PII Decoding (CRF).

Implements the Indian-adapted multilingual transformer baseline equipped with
a linear-chain Conditional Random Field (CRF) sequence decoding head:
- Base Architecture: xlm-roberta-base
- Linear Emission Layer: 768 -> 17 classes
- Linear-Chain CRF: 17x17 transition matrix + start/end transitions
- Exact Viterbi decoding for sequence-constrained span prediction
- Native Python Unicode code-point offsets: text[start:end] == p.text
- Deterministic sorting by (start, end, type, -confidence)
"""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any, ClassVar
import torch
import torch.nn as nn
from transformers import AutoTokenizer, XLMRobertaModel

from benchmark.schema import Prediction
from .base import BaselineAdapter

REPO_ROOT = Path(__file__).resolve().parents[1]

LABEL_LIST = [
    "O",
    "B-PERSON",
    "I-PERSON",
    "B-PAN",
    "I-PAN",
    "B-AADHAAR",
    "I-AADHAAR",
    "B-PHONE",
    "I-PHONE",
    "B-EMAIL",
    "I-EMAIL",
    "B-UPI_ID",
    "I-UPI_ID",
    "B-BANK_ACCOUNT",
    "I-BANK_ACCOUNT",
    "B-ADDRESS",
    "I-ADDRESS",
]
LABEL2ID = {lbl: i for i, lbl in enumerate(LABEL_LIST)}
ID2LABEL = {i: lbl for i, lbl in enumerate(LABEL_LIST)}


class LinearChainCRF(nn.Module):
    """Linear-chain Conditional Random Field layer for sequence labeling."""

    def __init__(self, num_tags: int):
        super().__init__()
        self.num_tags = num_tags
        self.transitions = nn.Parameter(torch.empty(num_tags, num_tags))
        self.start_transitions = nn.Parameter(torch.empty(num_tags))
        self.end_transitions = nn.Parameter(torch.empty(num_tags))
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.uniform_(self.transitions, -0.1, 0.1)
        nn.init.uniform_(self.start_transitions, -0.1, 0.1)
        nn.init.uniform_(self.end_transitions, -0.1, 0.1)

    def forward_alg(self, emissions: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len, num_tags = emissions.shape
        forward_var = self.start_transitions.unsqueeze(0) + emissions[:, 0]

        for t in range(1, seq_len):
            next_tag_var = forward_var.unsqueeze(2) + self.transitions.unsqueeze(0)
            next_var = torch.logsumexp(next_tag_var, dim=1) + emissions[:, t]
            m = mask[:, t].unsqueeze(1)
            forward_var = torch.where(m, next_var, forward_var)

        terminal_var = forward_var + self.end_transitions.unsqueeze(0)
        return torch.logsumexp(terminal_var, dim=1)

    def score_sentence(self, emissions: torch.Tensor, tags: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len, _ = emissions.shape
        score = self.start_transitions[tags[:, 0]] + emissions[:, 0].gather(1, tags[:, 0].unsqueeze(1)).squeeze(1)

        for t in range(1, seq_len):
            curr_tag = tags[:, t]
            prev_tag = tags[:, t - 1]
            trans_score = self.transitions[prev_tag, curr_tag]
            emit_score = emissions[:, t].gather(1, curr_tag.unsqueeze(1)).squeeze(1)
            step_score = (trans_score + emit_score) * mask[:, t].float()
            score = score + step_score

        seq_lens = mask.sum(dim=1).long()
        last_indices = (seq_lens - 1).clamp(min=0)
        last_tags = tags.gather(1, last_indices.unsqueeze(1)).squeeze(1)
        score = score + self.end_transitions[last_tags]
        return score

    def loss(self, emissions: torch.Tensor, tags: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        log_z = self.forward_alg(emissions, mask)
        score = self.score_sentence(emissions, tags, mask)
        return (log_z - score).mean()

    def decode(self, emissions: torch.Tensor, mask: torch.Tensor | None = None) -> list[list[int]]:
        batch_size, seq_len, num_tags = emissions.shape
        if mask is None:
            mask = torch.ones((batch_size, seq_len), dtype=torch.bool, device=emissions.device)

        best_paths: list[list[int]] = []
        for b in range(batch_size):
            seq_len_b = int(mask[b].sum().item())
            if seq_len_b == 0:
                best_paths.append([])
                continue

            viterbi_var = self.start_transitions + emissions[b, 0]
            backpointers: list[torch.Tensor] = []

            for t in range(1, seq_len_b):
                broadcast = viterbi_var.unsqueeze(1) + self.transitions
                max_val, best_prev = torch.max(broadcast, dim=0)
                viterbi_var = max_val + emissions[b, t]
                backpointers.append(best_prev)

            viterbi_var = viterbi_var + self.end_transitions
            best_tag = torch.argmax(viterbi_var).item()
            best_path = [best_tag]

            for bp in reversed(backpointers):
                best_tag = bp[best_tag].item()
                best_path.append(best_tag)

            best_path.reverse()
            best_paths.append(best_path)

        return best_paths


class TransformerB6CRFHead(nn.Module):
    def __init__(self, hidden_size: int = 768, num_tags: int = len(LABEL_LIST), dropout_p: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout_p)
        self.classifier = nn.Linear(hidden_size, num_tags)
        self.crf = LinearChainCRF(num_tags)

    def forward(self, hidden_states: torch.Tensor, tags: torch.Tensor | None = None, mask: torch.Tensor | None = None):
        emissions = self.classifier(self.dropout(hidden_states))
        if tags is not None and mask is not None:
            loss = self.crf.loss(emissions, tags, mask)
            return loss, emissions
        return emissions

    def decode(self, hidden_states: torch.Tensor, mask: torch.Tensor | None = None) -> list[list[int]]:
        emissions = self.classifier(hidden_states)
        return self.crf.decode(emissions, mask)


class TransformerB6CRFAdapter(BaselineAdapter):
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
        encoder_model: XLMRobertaModel | None = None,
        head_model: TransformerB6CRFHead | None = None,
        tokenizer: AutoTokenizer | None = None,
    ) -> None:
        if model_name_or_path is None:
            checkpoint_dir = REPO_ROOT / "checkpoints" / "b6" / f"b6_transformer_crf_seed{seed}"
            if checkpoint_dir.exists():
                self.model_path = str(checkpoint_dir)
            else:
                self.model_path = "xlm-roberta-base"
        else:
            self.model_path = str(model_name_or_path)

        self.seed = seed
        self.device = torch.device(
            "cuda" if (device == "cuda" or (isinstance(device, int) and device >= 0 and torch.cuda.is_available())) else "cpu"
        )

        if tokenizer is not None:
            self.tokenizer = tokenizer
        else:
            tok_source = self.model_path if (Path(self.model_path) / "tokenizer_config.json").exists() else "xlm-roberta-base"
            self.tokenizer = AutoTokenizer.from_pretrained(tok_source)

        if encoder_model is not None:
            self.encoder = encoder_model
        else:
            has_weights = (Path(self.model_path) / "model.safetensors").exists() or (Path(self.model_path) / "pytorch_model.bin").exists()
            enc_source = self.model_path if has_weights else "xlm-roberta-base"
            self.encoder = XLMRobertaModel.from_pretrained(enc_source)

        self.encoder.to(self.device)
        self.encoder.eval()

        if head_model is not None:
            self.head = head_model
        else:
            self.head = TransformerB6CRFHead(hidden_size=768, num_tags=len(LABEL_LIST))
            head_weights_path = Path(self.model_path) / "b6_crf_head.pt"
            if head_weights_path.exists():
                state_dict = torch.load(head_weights_path, map_location=self.device)
                self.head.load_state_dict(state_dict)
            elif (Path(self.model_path) / "model.safetensors").exists():
                from safetensors.torch import load_file
                full_sd = load_file(Path(self.model_path) / "model.safetensors")
                head_sd = {k: v for k, v in full_sd.items() if not k.startswith("roberta.")}
                if head_sd:
                    self.head.load_state_dict(head_sd)

        self.head.to(self.device)
        self.head.eval()

        try:
            transformers_ver = importlib.metadata.version("transformers")
        except Exception:
            transformers_ver = "5.16.1"

        self._system_version = f"{transformers_ver}_xlm_roberta_base_indian_crf_v0.18"

    @property
    def system_name(self) -> str:
        return "transformer_crf"

    @property
    def system_version(self) -> str:
        return self._system_version

    def predict(self, text: str) -> list[Prediction]:
        if not text or not text.strip():
            return []

        encoding = self.tokenizer(
            text,
            return_offsets_mapping=True,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )

        input_ids = encoding["input_ids"].to(self.device)
        attention_mask = encoding["attention_mask"].to(self.device)
        offset_mapping = encoding["offset_mapping"][0].tolist()

        valid_indices = [i for i, (s, e) in enumerate(offset_mapping) if s < e]
        if not valid_indices:
            return []

        with torch.no_grad():
            encoder_out = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
            hidden_states = encoder_out.last_hidden_state

            valid_idx_tensor = torch.tensor(valid_indices, dtype=torch.long, device=self.device)
            sub_hidden = hidden_states[:, valid_idx_tensor, :]

            emissions = self.head.classifier(sub_hidden)
            mask = torch.ones((1, len(valid_indices)), dtype=torch.bool, device=self.device)
            best_tags = self.head.crf.decode(emissions, mask)[0]
            emissions_softmax = torch.softmax(emissions[0], dim=-1)

        predictions: list[Prediction] = []
        current_entity: tuple[str, int, int, list[float]] | None = None

        for k, tag_id in enumerate(best_tags):
            tag_name = ID2LABEL[tag_id]
            s, e = offset_mapping[valid_indices[k]]
            token_conf = emissions_softmax[k, tag_id].item()

            if tag_name.startswith("B-"):
                if current_entity is not None:
                    ent_type, ent_s, ent_e, confs = current_entity
                    predictions.append(
                        Prediction(
                            type=self.TYPE_MAP.get(ent_type, ent_type),
                            start=ent_s,
                            end=ent_e,
                            text=text[ent_s:ent_e],
                            confidence=sum(confs) / len(confs),
                        )
                    )
                ent_type = tag_name[2:]
                current_entity = (ent_type, s, e, [token_conf])
            elif tag_name.startswith("I-"):
                ent_type = tag_name[2:]
                if current_entity is not None and current_entity[0] == ent_type:
                    _, ent_s, _, confs = current_entity
                    confs.append(token_conf)
                    current_entity = (ent_type, ent_s, e, confs)
                else:
                    if current_entity is not None:
                        ent_type_prev, ent_s, ent_e, confs = current_entity
                        predictions.append(
                            Prediction(
                                type=self.TYPE_MAP.get(ent_type_prev, ent_type_prev),
                                start=ent_s,
                                end=ent_e,
                                text=text[ent_s:ent_e],
                                confidence=sum(confs) / len(confs),
                            )
                        )
                    current_entity = (ent_type, s, e, [token_conf])
            else:
                if current_entity is not None:
                    ent_type, ent_s, ent_e, confs = current_entity
                    predictions.append(
                        Prediction(
                            type=self.TYPE_MAP.get(ent_type, ent_type),
                            start=ent_s,
                            end=ent_e,
                            text=text[ent_s:ent_e],
                            confidence=sum(confs) / len(confs),
                        )
                    )
                    current_entity = None

        if current_entity is not None:
            ent_type, ent_s, ent_e, confs = current_entity
            predictions.append(
                Prediction(
                    type=self.TYPE_MAP.get(ent_type, ent_type),
                    start=ent_s,
                    end=ent_e,
                    text=text[ent_s:ent_e],
                    confidence=sum(confs) / len(confs),
                )
            )

        valid_preds: list[Prediction] = []
        for p in predictions:
            if 0 <= p.start < p.end <= len(text) and text[p.start : p.end] == p.text:
                valid_preds.append(p)

        valid_preds.sort(key=lambda p: (p.start, p.end, p.type, -p.confidence))
        return valid_preds