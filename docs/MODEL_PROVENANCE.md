# Model Provenance and Specification
**Document Identifier**: `DOCS-MODEL-PROVENANCE-V1.0`  
**Benchmark Version**: `0.18`  
**Status**: APPROVED  
**Date**: September 9, 2026  

---

## 1. Baseline B4: Zero-Shot Multilingual Transformer

- **Upstream Model Identifier**: `Davlan/xlm-roberta-base-ner-hrl`
- **Model Card URL**: `https://huggingface.co/Davlan/xlm-roberta-base-ner-hrl`
- **Specific Git Commit / Revision**: `253f557bd8249b8515114cfd7f71974fe5fa4d2f`
- **Base Architecture**: XLM-RoBERTa Base (12 layers, 768 hidden size, 12 attention heads, ~278M parameters).
- **Pretrained Target**: High-resource named entity recognition across 10 languages (PER, ORG, LOC, DATE).
- **Taxonomy Mapping to Indian PII**:
  - `PER` $\to$ `PERSON`
  - `LOC` $\to$ `ADDRESS`
  - All other Indian PII types (`AADHAAR`, `PAN`, `PHONE`, `EMAIL`, `UPI_ID`, `BANK_ACCOUNT`) have no direct correspondence in Davlan's schema and yield zero zero-shot recall.
- **Upstream License**:
  > **License Verification Status**: *License requires verification from the upstream model/package metadata before public release.*

---

## 2. Baseline B5: Indian-Adapted XLM-RoBERTa (Token Classification)

- **System Identifier**: `5.16.1_xlm_roberta_base_indian_v0.18`
- **Base Foundation Model**: `xlm-roberta-base`
- **Tokenizer**: `XLMRobertaTokenizerFast` (SentencePiece vocabulary of 250,002 tokens).
- **Architecture**: XLM-RoBERTa encoder + linear classification head (768 hidden units $\to$ 17 logits) with independent softmax decoding per sub-word token.
- **Label Schema (17 IOB2 Tags)**:
  `O`, `B-PERSON`, `I-PERSON`, `B-PAN`, `I-PAN`, `B-AADHAAR`, `I-AADHAAR`, `B-PHONE`, `I-PHONE`, `B-EMAIL`, `I-EMAIL`, `B-UPI_ID`, `I-UPI_ID`, `B-BANK_ACCOUNT`, `I-BANK_ACCOUNT`, `B-ADDRESS`, `I-ADDRESS`.
- **Adaptation Corpus**:
  - Training: `data/adaptation/train_instances.jsonl` (200 unique base instances expanded to 1,000 augmented sequences via language and perturbation operators).
  - Validation: `data/adaptation/val_instances.jsonl` (50 unique base instances expanded to 250 augmented sequences).
  - *Leakage Control*: 0% overlap between adaptation base instances and canonical test benchmark base instances (empirically audited in SV-01).
- **Adaptation Seeds**: `42`, `43`, `44`.
- **Hyperparameters**:
  - Learning rate: $3 \times 10^{-5}$
  - Optimizer: AdamW ($\beta_1 = 0.9, \beta_2 = 0.999, \epsilon = 1 \times 10^{-8}$, weight decay $= 0.01$)
  - Batch size: 16
  - Epochs: 5
  - Max sequence length: 256 tokens
  - Warmup ratio: 0.1 with linear decay
- **Checkpoint Locations**:
  - `checkpoints/b5_transformer_adapted_seed42/`
  - `checkpoints/b5_transformer_adapted_seed43/`
  - `checkpoints/b5_transformer_adapted_seed44/`
- **Upstream License**:
  > **License Verification Status**: *License requires verification from the upstream model/package metadata before public release.*

---

## 3. Baseline B6: Indian-Adapted XLM-RoBERTa + Linear Chain CRF

- **System Identifier**: `5.16.1_xlm_roberta_base_indian_crf_v0.18`
- **Base Foundation Model**: `xlm-roberta-base`
- **Architecture**: XLM-RoBERTa encoder + Linear Projection (768 hidden units $\to$ 17 emission scores) + First-Order Linear Chain Conditional Random Field (CRF) with 17 learnable transition parameters and exact Viterbi sequence decoding.
- **Label Schema (17 IOB2 Tags)**: Same 17 tags as B5.
- **Transition Constraints Enforced**:
  - Disallows illegal $O \to I\text{-TYPE}$ transitions.
  - Disallows illegal cross-type boundary transitions ($B\text{-TYPE}_1 \to I\text{-TYPE}_2$).
  - Learns strong structural priors for multi-token structured identifiers (Aadhaar, PAN, UPI ID).
- **Adaptation Seeds**: `42`, `43`, `44`.
- **Hyperparameters**:
  - Encoder learning rate: $2 \times 10^{-5}$
  - CRF transition matrix learning rate: $1 \times 10^{-3}$
  - Optimizer: AdamW
  - Batch size: 16
  - Epochs: 5
  - Max sequence length: 256 tokens
- **Checkpoint Locations**:
  - `checkpoints/b6/b6_transformer_crf_seed42/`
  - `checkpoints/b6/b6_transformer_crf_seed43/`
  - `checkpoints/b6/b6_transformer_crf_seed44/`
- **Upstream License**:
  > **License Verification Status**: *License requires verification from the upstream model/package metadata before public release.*

---

## 4. Upstream Artifact Verification Checklist

Prior to public release of model binary weights:
- [ ] Upstream `Davlan/xlm-roberta-base-ner-hrl` license terms must be confirmed from repository author.
- [ ] Facebook AI / Meta `xlm-roberta-base` open license terms must be verified against Hugging Face Model Hub metadata.
- [ ] Checkpoint weight files (`model.safetensors` or `pytorch_model.bin`) must be hosted on an approved academic model repository (e.g., Hugging Face Hub / Zenodo) with signed SHA-256 release checksums.
