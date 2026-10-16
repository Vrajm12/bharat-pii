"""Neural model components and weight loading for BharatPII-CRF."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import torch
import torch.nn as nn
from safetensors.torch import load_file
from transformers import XLMRobertaConfig, XLMRobertaModel


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

    def decode(self, emissions: torch.Tensor, mask: torch.Tensor | None = None) -> list[list[int]]:
        """Exact Viterbi sequence decoding."""
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


class BharatPIICRFHead(nn.Module):
    """Task-specific classification and sequence decoding head."""

    def __init__(self, hidden_size: int = 768, num_tags: int = 17, dropout_p: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout_p)
        self.classifier = nn.Linear(hidden_size, num_tags)
        self.crf = LinearChainCRF(num_tags)

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        return self.classifier(hidden_states)

    def decode(self, hidden_states: torch.Tensor, mask: torch.Tensor | None = None) -> list[list[int]]:
        emissions = self.classifier(hidden_states)
        return self.crf.decode(emissions, mask)


class BharatPIIModel(nn.Module):
    """Unified BharatPII-CRF model combining XLM-RoBERTa encoder and CRF head."""

    def __init__(self, encoder: XLMRobertaModel, head: BharatPIICRFHead, config: dict[str, Any]):
        super().__init__()
        self.encoder = encoder
        self.head = head
        self.config = config

    @property
    def total_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters())

    @property
    def encoder_parameters(self) -> int:
        return sum(p.numel() for p in self.encoder.parameters())

    @property
    def trainable_head_parameters(self) -> int:
        return sum(p.numel() for p in self.head.parameters())

    @classmethod
    def load_from_directory(cls, model_dir: str | Path, device: torch.device) -> BharatPIIModel:
        model_path = Path(model_dir)
        if not model_path.exists():
            raise FileNotFoundError(f"Model directory not found: {model_path}")

        weights_file = model_path / "model.safetensors"
        if not weights_file.exists():
            raise FileNotFoundError(f"Required model weights missing: {weights_file}")

        config_file = model_path / "config.json"
        if not config_file.exists():
            raise FileNotFoundError(f"Required model configuration missing: {config_file}")

        with open(config_file, "r", encoding="utf-8") as f:
            raw_config = json.load(f)

        state_dict = load_file(weights_file)
        if len(state_dict) != 204:
            raise ValueError(f"Expected 204 tensors in model.safetensors, found {len(state_dict)}")

        encoder_sd = {k: v for k, v in state_dict.items() if k.startswith("roberta.")}
        head_sd = {k: v for k, v in state_dict.items() if not k.startswith("roberta.")}

        if len(encoder_sd) != 199:
            raise ValueError(f"Expected 199 encoder tensors, found {len(encoder_sd)}")
        if len(head_sd) != 5:
            raise ValueError(f"Expected 5 head tensors, found {len(head_sd)}")

        xlm_config = XLMRobertaConfig.from_pretrained(model_path)
        encoder = XLMRobertaModel(xlm_config)
        stripped_enc_sd = {k[len("roberta."):]: v for k, v in encoder_sd.items()}
        encoder.load_state_dict(stripped_enc_sd, strict=True)
        encoder.to(device)
        encoder.eval()

        num_labels = raw_config.get("num_labels", 17)
        hidden_size = raw_config.get("hidden_size", 768)
        head = BharatPIICRFHead(hidden_size=hidden_size, num_tags=num_labels)
        head.load_state_dict(head_sd, strict=True)
        head.to(device)
        head.eval()

        return cls(encoder=encoder, head=head, config=raw_config)
