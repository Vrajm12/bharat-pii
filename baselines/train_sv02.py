"""Training script for SV-02 Experimental Variants.

Trains:
1. b5_hard_negative (seeds 42, 43, 44)
2. b5_positive_matched (seeds 42, 43, 44)
3. b5_format_diversity (seeds 42, 43, 44)

Maintains identical architecture, loss, optimizer, and hyperparameters as canonical B5.
"""

from __future__ import annotations

import json
from pathlib import Path
import random
import sys
import time

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from transformers import AutoModelForTokenClassification, AutoTokenizer, XLMRobertaModel

SV02_DATA_DIR = REPO_ROOT / "data" / "experiments" / "sv02"
CHECKPOINT_DIR = REPO_ROOT / "checkpoints" / "sv02"

MODEL_NAME = "xlm-roberta-base"

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


def train_variant(variant_name: str, seeds: list[int] = [42, 43, 44], epochs: int = 15, lr: float = 3e-3):
    print(f"\n=======================================================")
    print(f"STARTING TRAINING FOR VARIANT: {variant_name}")
    print(f"=======================================================")
    
    data_dir = SV02_DATA_DIR / variant_name
    train_path = data_dir / "train.jsonl"
    val_path = data_dir / "val.jsonl"
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    base_encoder = XLMRobertaModel.from_pretrained(MODEL_NAME)

    print(f"Tokenizing {variant_name} dataset...")
    train_ids, train_mask, train_labels = load_and_tokenize(train_path, tokenizer)
    val_ids, val_mask, val_labels = load_and_tokenize(val_path, tokenizer)

    print(f"Extracting XLM-R embeddings for {len(train_ids)} train and {len(val_ids)} val samples...")
    train_feat = extract_features(base_encoder, train_ids, train_mask)
    val_feat = extract_features(base_encoder, val_ids, val_mask)

    loss_fn = nn.CrossEntropyLoss(ignore_index=-100)

    for seed in seeds:
        print(f"\n--- Training {variant_name} | Seed {seed} ---")
        start_t = time.time()
        set_seed(seed)
        output_dir = CHECKPOINT_DIR / f"{variant_name}_seed{seed}"
        output_dir.mkdir(parents=True, exist_ok=True)

        full_model = AutoModelForTokenClassification.from_pretrained(
            MODEL_NAME,
            num_labels=len(LABEL_LIST),
            id2label=ID2LABEL,
            label2id=LABEL2ID,
        )

        head = nn.Sequential(
            nn.Dropout(0.1),
            nn.Linear(768, len(LABEL_LIST)),
        )
        optimizer = torch.optim.AdamW(head.parameters(), lr=lr, weight_decay=1e-4)

        train_ds = TensorDataset(train_feat, train_labels)
        train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)

        for epoch in range(epochs):
            head.train()
            total_loss = 0.0
            for feats, lbls in train_loader:
                optimizer.zero_grad()
                logits = head(feats)
                loss = loss_fn(logits.view(-1, len(LABEL_LIST)), lbls.view(-1))
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

            if (epoch + 1) % 5 == 0 or epoch == epochs - 1:
                head.eval()
                with torch.no_grad():
                    val_logits = head(val_feat)
                    val_loss = loss_fn(val_logits.view(-1, len(LABEL_LIST)), val_labels.view(-1)).item()
                print(f"Epoch {epoch+1:02d}/{epochs} - Train Loss: {total_loss/len(train_loader):.4f} - Val Loss: {val_loss:.4f}")

        # Inject trained head weights into full AutoModelForTokenClassification
        full_model.classifier.weight.data.copy_(head[1].weight.data)
        full_model.classifier.bias.data.copy_(head[1].bias.data)

        # Save model and tokenizer checkpoint
        full_model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)

        duration = round(time.time() - start_t, 2)
        meta = {
            "variant": variant_name,
            "base_model": MODEL_NAME,
            "seed": seed,
            "epochs": epochs,
            "learning_rate": lr,
            "weight_decay": 1e-4,
            "batch_size": 32,
            "train_samples": len(train_ids),
            "val_samples": len(val_ids),
            "labels": LABEL_LIST,
            "training_duration_seconds": duration,
        }
        with open(output_dir / "training_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        print(f"Saved: {output_dir} (Duration: {duration}s)")


def train_all():
    variants = ["b5_hard_negative", "b5_positive_matched", "b5_format_diversity"]
    for var in variants:
        train_variant(var, seeds=[42, 43, 44])
    print("\n=== ALL SV-02 VARIANTS TRAINED SUCCESSFULLY ===")


if __name__ == "__main__":
    train_all()
