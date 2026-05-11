# Fine-tune BGE-M3 Dense on QRCD — Implementation Plan

_Produced by ralph IMPL tick 53 · 2026-05-12 · Task: from_research_finetune_bge_m3_qrcd_

---

## Goal

Close the gap between our QRCD MAP@10 baseline (0.139) and the literature ceiling (AraBERT fine-tuned: ~0.36).
Research synthesis (`data/research_bge_m3_dense_vs_colbert.md`) confirms the gap is **domain adaptation**, not architecture.
Fine-tuning BGE-M3 dense on Quranic/QRCD query-passage pairs is the highest-leverage single intervention.

---

## Evidence basis

| Source | Key finding |
|--------|-------------|
| BGE-M3 paper (arxiv 2402.03216v3) | MIRACL Arabic dense 78.4 vs multi-vec 79.6 — +1.2 nDCG; gap is small |
| Arabic RAG study (arxiv 2506.06339) | BGE-M3 dense scored **82.72 on Quran Tafseer** corpus — already domain-strong |
| QRCD SOTA (arxiv 2508.06971) | MAP@10=0.3128 via CamelBERT-tafseer fine-tune; **no BGE-M3 used** |
| CustomIR (arxiv 2510.21729) | Unsupervised dense fine-tune shows +2.3 Recall@10; Arabic-specific tuning +5-10% |
| Synthesis 2026-05-12 | "Domain adaptation is THE direct path to closing the literature gap" |

---

## Training data construction

### Source 1: QRCD passage-question pairs (primary)
- QRCD v1.1 dataset: ~1,093 unique passages from Quran with 1,337 question-answer pairs
- Download: https://arabicnlp.pro/alue/tasks/qrcd (CC BY-SA 4.0)
- Format: `(question, positive_passage, negative_passages)`
- Negatives: BM25 hard negatives from same surah section (in-surah negatives are harder)

### Source 2: Tafsir Q&A pairs (secondary)
- Ibn Kathir tafsir aligned to verse IDs — verse text as passage, interpretive question as query
- ~2,000 synthetic pairs via: `claude-haiku-4-5 → "Generate a question whose answer is in this verse: {verse}"` 
- Filter by embedding cosine similarity < 0.9 to deduplicate trivial paraphrases

### Source 3: Existing answer_cache.json (augmentation)
- 1,500+ cached queries → extract (query, cited_verse_texts) as (question, positive_passage) pairs
- Estimated yield: ~800 usable pairs after deduplication at cosine 0.95

### Total training corpus target
- ~3,000-4,000 (question, positive, negative) triplets
- Train/val/test split: 80/10/10

---

## Fine-tuning procedure

### Setup
```bash
pip install FlagEmbedding>=1.2.0 transformers accelerate bitsandbytes
# Optional: wandb for loss tracking
```

### Script skeleton: `finetune_bge_m3_qrcd.py`
```python
from FlagEmbedding import FlagModel
from FlagEmbedding.baai_general_embedding.finetune.run import DataTrainingArguments, ModelArguments, train

# Training args — conservative for CPU/single-GPU
training_args = {
    "model_name_or_path": "BAAI/bge-m3",
    "train_data": "data/finetune_triplets_qrcd.jsonl",
    "output_dir": "ckpts/bge-m3-qrcd-v1",
    "num_train_epochs": 3,
    "per_device_train_batch_size": 8,    # reduce to 4 if OOM
    "learning_rate": 2e-5,
    "warmup_ratio": 0.1,
    "fp16": True,                         # use bf16 if A100
    "gradient_accumulation_steps": 4,     # effective batch 32
    "temperature": 0.02,                  # InfoNCE temperature
    "query_max_len": 64,
    "passage_max_len": 256,
    "train_group_size": 8,               # 1 positive + 7 negatives per query
    "negatives_cross_device": True,       # cross-batch hard negatives
    "save_steps": 500,
    "eval_steps": 500,
    "load_best_model_at_end": True,
    "metric_for_best_model": "eval_loss",
}
```

### Training JSONL format (`data/finetune_triplets_qrcd.jsonl`)
```json
{"query": "ما هي آيات القرآن التي تذكر الرحمة؟", "pos": ["verse text..."], "neg": ["hard negative verse 1", "hard neg 2", ...]}
```

### Hardware estimate
- RTX 3090 (24GB VRAM): ~4-6 hours for 3 epochs on 4K triplets
- CPU only: ~48 hours (not recommended — use cloud spot instance)
- Recommended: Colab Pro+ A100 or Kaggle T4 (free tier, 2x slower)

---

## Evaluation protocol

### Step 1: Embed all verses with fine-tuned model
```bash
CHECKPOINT=ckpts/bge-m3-qrcd-v1/checkpoint-best
python embed_verses_m3.py --model $CHECKPOINT --index-name verse_embedding_m3_qrcd
```

### Step 2: Run QRCD eval with new index
```bash
SEMANTIC_SEARCH_INDEX=verse_embedding_m3_qrcd python eval_qrcd_retrieval.py \
  --compare-to data/qrcd_retrieval_results.json \
  --output data/qrcd_retrieval_finetuned.json
```

### Step 3: Decision gate
- If MAP@10 >= 0.20 (+44% over 0.139): **ADOPT** — swap default index, retrain cross-encoder on same domain
- If MAP@10 0.15-0.20: **PARTIAL** — use as query-side encoder only, keep base BGE-M3 for document side
- If MAP@10 < 0.15: **REJECT** — investigate training data quality, try longer training or lower LR

### Baseline comparison table
| System | MAP@10 |
|--------|--------|
| all-MiniLM-L6-v2 (legacy) | 0.028 |
| BGE-M3 base (current) | 0.139 |
| **BGE-M3 fine-tuned QRCD (target)** | **0.20-0.30** |
| AraBERT fine-tuned (literature SOTA) | 0.36 |

---

## Risk register

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Catastrophic forgetting of general Arabic | Medium | Keep both indexes; run MIRACL Arabic eval on fine-tuned model |
| Overfitting to 1K QRCD questions | Medium | Augment with Tafsir + cache pairs; early stopping on val loss |
| OOM on single GPU | High | Reduce batch size to 4, enable gradient checkpointing |
| QRCD dataset copyright | Low | CC BY-SA 4.0 licensed; permitted for research fine-tuning |
| Fine-tuned model regression on eval_v1 English queries | Medium | A/B with `verse_embedding_m3` vs `verse_embedding_m3_qrcd` via env var |

---

## Implementation sequence

1. **[Operator]** Download QRCD v1.1 dataset → `data/qrcd_v1.1/`
2. **[Loop]** Run `scripts/build_finetune_data.py` — converts QRCD + cache to JSONL triplets
3. **[Operator]** Launch training on GPU (cloud spot or local RTX)
4. **[Loop]** After training, run `embed_verses_m3.py --model ckpts/bge-m3-qrcd-v1/checkpoint-best`
5. **[Loop]** Run `eval_qrcd_retrieval.py` and `eval_v1.py` with new index — apply decision gate
6. **[Operator]** If adopted: update `.env` `SEMANTIC_SEARCH_INDEX=verse_embedding_m3_qrcd`, commit

---

## Files to create

| File | Purpose |
|------|---------|
| `scripts/build_finetune_data.py` | Convert QRCD + answer_cache → JSONL triplets with BM25 hard negatives |
| `finetune_bge_m3_qrcd.py` | Training entry-point using FlagEmbedding |
| `data/finetune_triplets_qrcd.jsonl` | Training data (generated, gitignored if large) |
| `ckpts/bge-m3-qrcd-v1/` | Model checkpoint (gitignored) |
| `data/qrcd_retrieval_finetuned.json` | Eval results after fine-tune |

---

## Key recommendation

**Start with `scripts/build_finetune_data.py` first** — the training data quality is the variable most likely to determine success or failure. Use the existing `answer_cache.json` (1,500+ cached QA pairs) as the seed; augment with QRCD official dataset; generate synthetic pairs from tafsir. Budget 2-3 hours to audit 50 random triplets before training.

The architecture is already correct (BGE-M3 dense + cross-encoder rerank). This is a pure domain-adaptation bet.
