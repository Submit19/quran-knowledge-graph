---
type: decision
adr: 0009
status: accepted
date: 2026-05-10
tags: [decision, retrieval, architecture]
supersedes: none
---

# ADR-0009 — Hand-roll retrievers vs adopt neo4j-graphrag-python library

## Status
Accepted (2026-05-10). Pending spike — may be superseded.

## Context
`neo4j-graphrag-python` (the official Neo4j GraphRAG Python library) provides `HybridRetriever`, `HybridCypherRetriever`, and `SentenceTransformerEmbeddings` — higher-level abstractions over the exact retrieval patterns `chat.py` already implements by hand (vector index + BM25 fulltext + RRF fusion + metadata filters). Research tick `01_vector_graphrag.md` (2026-05-10) found that `SentenceTransformerEmbeddings` accepts arbitrary HuggingFace model strings including `BAAI/bge-m3`, and the library's RRF implementation (k=60) matches our hand-rolled implementation. The retrievers were hand-rolled before this library was discovered.

## Decision
Retain hand-rolled retrievers for now. The status is PENDING SPIKE: a backlog task (`from_neo4j_crawl_adopt_graphrag_retrievers`, priority 80) is queued to evaluate a thin adoption of the library's `HybridRetriever` as a drop-in for `chat.py`'s `hybrid_search` tool. Decision will be revisited after the spike.

## Consequences
- **Positive (status quo):** Full control over retrieval logic; no additional dependency. Current implementation is well-understood and tested.
- **Negative (status quo):** Missing the library's metadata pre-filtering (`$eq`, `$in`, `$gte`, `$or`, `$like`) that would enable surah/range pre-filters in-index, especially valuable on Neo4j 2026.01+ where filtered vector queries route through the HNSW index.
- **Neutral:** If the spike confirms clean adoption, a future ADR will supersede this one. If spike reveals compatibility gaps, the hand-rolled path is confirmed as correct.

## Cross-references
- Source evidence: `repo://data/research_neo4j_crawl/01_vector_graphrag.md`
- Related: [[0002-bge-m3-over-minilm]], [[0004-skip-colbert]]
