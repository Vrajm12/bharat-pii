"""Training script for Baseline B6 (Span-Aware / Linear-Chain CRF Transformer).

Governed by PROJECT_SPEC.md §§19-24, §21.2 (Multi-seed), §22.1 (Split discipline).
Trains linear emission layer + linear-chain CRF on disjoint synthetic adaptation dataset
(data/adaptation/train.jsonl, 1000 samples) with zero overlap with the benchmark test set.
Pre-extracts multilingual representations from xlm-roberta-base and trains
across seeds [42, 43, 44].
"""

from __future__ import annotations

import json
from pathlib import Path
import random
import torch
from torch.utils.data import DataLoader, TensorDataset
from transformers import AutoTokenizer, XLMRobertaModel

from baselines.transformer_b6 import (
    LABEL_LIST,
    LABEL2ID,
    ID2LABEL,
    TransformerB6CRFHead,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ADAPT_DIR = REPO_ROOT / "data" / "adaptation"
TRAIN_PATH = ADAPT_DIR / "train.jsonl"
VAL_PATH = ADAPT_DIR / "val.jsonl"
CHECKPOINT_DIR = REPO_ROOT / "checkpoints" / "b6"

MODEL_NAME = "xlm-roberta-base"


def load_and_tokenize(data_path: Path, tokenizer: AutoTokenizer, max_length: int = 128):
    input_ids_list = []
    attention_mask_list = []
    labels_list = []

    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            text = record["text"]
            entities = record.get("entities", [])

            encoding = tokenizer(
                text,
                max_length=max_length,
                padding="max_length",
                truncation=True,
                return_offsets_mapping=True,
                return_tensors="pt",
            )

            input_ids = encoding["input_ids"].squeeze(0)
            attention_mask = encoding["attention_mask"].squeeze(0)
            offset_mapping = encoding["offset_mapping"].squeeze(0)

            labels = torch.full((max_length,), -100, dtype=torch.long)
            for token_idx, (start, end) in enumerate(offset_mapping):
                if start == end:
                    continue
                labels[token_idx] = LABEL2ID["O"]
                for ent in entities:
                    ent_start, ent_end = ent["start"], ent["end"]
                    ent_type = ent["type"]
                    if start >= ent_start and end <= ent_end:
                        if start == ent_start:
                            labels[token_idx] = LABEL2ID[f"B-{ent_type}"]
                        else:
                            labels[token_idx] = LABEL2ID[f"I-{ent_type}"]
                        break

            input_ids_list.append(input_ids)
            attention_mask_list.append(attention_mask)
            labels_list.append(labels)

    return (
        torch.stack(input_ids_list),
        torch.stack(attention_mask_list),
        torch.stack(labels_list),
    )


def extract_features(model: XLMRobertaModel, input_ids: torch.Tensor, attention_mask: torch.Tensor, batch_size: int = 32):
    model.eval()
    dataset = TensorDataset(input_ids, attention_mask)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    features = []

    with torch.no_grad():
        for b_ids, b_mask in loader:
            out = model(input_ids=b_ids, attention_mask=b_mask)
            features.append(out.last_hidden_state)

    return torch.cat(features, dim=0)


def set_seed(seed: int):
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def train_and_save_all_seeds(seeds: list[int] = [42, 43, 44], epochs: int = 15, lr: float = 3e-3):
    print("Loading base tokenizer and model for feature extraction...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    base_encoder = XLMRobertaModel.from_pretrained(MODEL_NAME)

    print("Tokenizing disjoint adaptation dataset...")
    train_ids, train_mask, train_labels = load_and_tokenize(TRAIN_PATH, tokenizer)
    val_ids, val_mask, val_labels = load_and_tokenize(VAL_PATH, tokenizer)

    print(f"Extracting XLM-R embeddings for {len(train_ids)} train and {len(val_ids)} val samples...")
    train_feat = extract_features(base_encoder, train_ids, train_mask)
    val_feat = extract_features(base_encoder, val_ids, val_mask)

    # Slice off index 0 (<s> token) so sequence begins at the first word token
    train_sub_feat = train_feat[:, 1:, :]
    train_sub_labels = train_labels[:, 1:]
    train_crf_mask = (train_sub_labels != -100)
    train_clean_labels = train_sub_labels.clone()
    train_clean_labels[~train_crf_mask] = 0

    val_sub_feat = val_feat[:, 1:, :]
    val_sub_labels = val_labels[:, 1:]
    val_crf_mask = (val_sub_labels != -100)
    val_clean_labels = val_sub_labels.clone()
    val_clean_labels[~val_crf_mask] = 0

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    for seed in seeds:
        print(f"\n--- Training B6 Seed {seed} ---")
        set_seed(seed)
        output_dir = CHECKPOINT_DIR / f"b6_transformer_crf_seed{seed}"
        output_dir.mkdir(parents=True, exist_ok=True)

        head = TransformerB6CRFHead(hidden_size=768, num_tags=len(LABEL_LIST), dropout_p=0.1)
        optimizer = torch.optim.AdamW(head.parameters(), lr=lr, weight_decay=1e-4)

        train_ds = TensorDataset(train_sub_feat, train_clean_labels, train_crf_mask)
        train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)

        final_train_loss = 0.0
        final_val_loss = 0.0

        for epoch in range(epochs):
            head.train()
            total_loss = 0.0
            for feats, lbls, msk in train_loader:
                optimizer.zero_grad()
                loss, _ = head(feats, tags=lbls, mask=msk)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

            avg_train_loss = total_loss / len(train_loader)
            if (epoch + 1) % 5 == 0 or epoch == epochs - 1:
                head.eval()
                with torch.no_grad():
                    v_loss, _ = head(val_sub_feat, tags=val_clean_labels, mask=val_crf_mask)
                    val_loss = v_loss.item()
                final_train_loss = avg_train_loss
                final_val_loss = val_loss
                print(f"Epoch {epoch+1:02d}/{epochs} - Train Loss: {avg_train_loss:.4f} - Val Loss: {val_loss:.4f}")

        # Save trained CRF head weights and tokenizer
        torch.save(head.state_dict(), output_dir / "b6_crf_head.pt")
        tokenizer.save_pretrained(output_dir)

        meta = {
            "system_name": "transformer_crf",
            "base_model": MODEL_NAME,
            "seed": seed,
            "epochs": epochs,
            "learning_rate": lr,
            "train_samples": len(train_ids),
            "val_samples": len(val_ids),
            "labels": LABEL_LIST,
            "train_final_loss": final_train_loss,
            "val_final_loss": final_val_loss,
        }
        with open(output_dir / "training_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        print(f"Seed {seed}: Checkpoint saved to {output_dir}")

    print("\nAll required B6 CRF adaptation seeds trained and saved successfully.")


if __name__ == "__main__":
    train_and_save_all_seeds()