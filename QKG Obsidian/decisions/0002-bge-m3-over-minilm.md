---
type: decision
adr: 0002
status: accepted
date: 2026-04-28
tags: [decision, retrieval, embeddings]
supersedes: none
---

# ADR-0002 — Use BGE-M3 over MiniLM for vector embeddings

## Status
Accepted (2026-04-28). Active.

## Context
The initial embedding model was `all-MiniLM-L6-v2` (384d, English-only), chosen for speed and size. As Arabic query support and cross-lingual retrieval became goals, MiniLM's monolingual nature became a hard constraint: Arabic queries land in essentially random positions in MiniLM's embedding space. `EVAL_QRCD_REPORT.md` documents a formal A/B on the QRCD Arabic QA benchmark (22 unique questions). Alternatives considered: `BAAI/bge-m3` (1024d, multilingual, off-the-shelf) and `BAAI/bge-m3` Arabic-index variant.

## Decision
Replace `all-MiniLM-L6-v2` with `BAAI/bge-m3` (English corpus) as the primary semantic search index (`verse_embedding_m3`, 1024d cosine). Keep the legacy MiniLM index live as a fallback, switchable via `SEMANTIC_SEARCH_INDEX` env var.

## Consequences
- **Positive:** MAP@10 on QRCD rises from 0.028 → 0.139 (5×); MRR rises from 0.073 → 0.418. BGE-M3-EN beats BGE-M3-AR on our corpus because Khalifa's translation includes parenthetical clarifications that bridge Arabic queries to English verse text.
- **Negative:** Model is 1024d vs 384d — ~4× larger index on disk; BGE-M3 cold-start in Python takes ~18 s on first query (confirmed by slow-query-log analysis in commit `3cb4066`). Hot calls are cached.
- **Neutral:** Still well below fine-tuned AraBERT baseline (MAP@10 ≈ 0.36); gap is domain adaptation, not architecture. Fine-tuning BGE-M3 on QRCD pairs is the planned next step.

## Cross-references
- Source evidence: `repo://EVAL_QRCD_REPORT.md`, `repo://CLAUDE.md` (headline benchmark numbers)
- Related: [[0003-multilingual-reranker]], [[0004-skip-colbert]]
