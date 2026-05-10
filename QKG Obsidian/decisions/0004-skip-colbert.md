---
type: decision
adr: 0004
status: accepted
date: 2026-05-10
tags: [decision, retrieval, embeddings]
supersedes: none
---

# ADR-0004 — Skip ColBERT mode for BGE-M3

## Status
Accepted (2026-05-10). Active.

## Context
BGE-M3 supports three retrieval modes: dense (single vector), sparse (BM25-like), and multi-vector (ColBERT-style MaxSim). ColBERT-mode offers late-interaction scoring by comparing query tokens against document tokens. After adopting BGE-M3 dense (ADR-0002), the question arose whether adding ColBERT mode would close the gap to fine-tuned baselines (MAP@10 0.139 vs 0.36). A dedicated research tick (`bge_m3_dense_vs_colbert`, commit `7a376e0`, 2026-05-10) evaluated published benchmarks and implementation trade-offs.

## Decision
Do not implement ColBERT mode for BGE-M3. Retain dense retrieval + cross-encoder rerank as the retrieval stack. Revisit only if fine-tuned dense plateaus below MAP@10 = 0.25 or the cross-encoder reranker is removed for cost reasons.

## Consequences
- **Positive:** Avoids ~1 GB of ColBERT token vector storage (vs ~25 MB dense); avoids Python-side MaxSim infrastructure (Neo4j 2026.01 has no native multi-vector index). No added query latency path.
- **Negative:** Leaves a theoretical +1.2 nDCG@10 (MIRACL Arabic) on the table. The actual gap on Quranic Arabic may differ but has not been measured.
- **Neutral:** The `bge-reranker-v2-m3` cross-encoder already provides late-interaction-like fine-grained scoring on the top-K candidate set, making a separate ColBERT pass largely redundant. The remaining retrieval gap is domain adaptation (fine-tuning), not architecture.

## Cross-references
- Source evidence: `repo://data/research_bge_m3_dense_vs_colbert.md`
- Related: [[0002-bge-m3-over-minilm]], [[0003-multilingual-reranker]]
