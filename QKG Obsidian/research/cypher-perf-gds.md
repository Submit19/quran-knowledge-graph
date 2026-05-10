---
type: research
status: done
priority: 90
tags: [research/neo4j, research/performance, research/gds, research/cypher]
source: data/research_neo4j_crawl/03_cypher_gds_perf.md
date_added: 2026-05-10
---

# Cypher Performance, Indexing, and GDS for QKG

## TL;DR
- Enable slow-query logging immediately (`db.logs.query.enabled=INFO`, `threshold=500ms`) — flying blind on the 647s `semantic_search` outlier without `query.log`.
- We are likely missing critical indexes: composite `(Verse.surah, Verse.ayah)`, relationship-property indexes on `MENTIONS.from_tfidf` / `to_tfidf`, and full-text indexes with an Arabic analyzer.
- Always parameterize Cypher — f-string literals skip the plan cache and pay parse cost on every call.
- Vector + 1-hop traversal can be a single Cypher statement; we may be doing two unnecessary round trips per semantic search.
- Replace Louvain with Leiden for community detection (one-line change; fixes disconnected-community bug).
- FastRP 128-d structural embeddings on a Verse-Concept-Lemma-Root projection are the most promising GDS retrieval augmentation signal (documented "product recommendations via kNN + FastRP" pattern).

## Key findings
- **647s outlier root cause**: likely `AllNodesScan` + `CartesianProduct` / `Eager` operators on cold cache in the post-vector TF-IDF expansion, not the vector index itself. Run `PROFILE` after capturing query in `query.log`.
- **Operator hierarchy**: `NodeIndexSeek` → `NodeByLabelScan` → `AllNodesScan` (worst). Any `CartesianProduct` is a red flag. Read execution plans bottom-up.
- **Single-round-trip hybrid pattern** (see source for full Cypher): `CALL db.index.vector.queryNodes(...) YIELD node, score ... OPTIONAL MATCH (node)-[:MENTIONS]->(k) ...` — eliminates second Python→Neo4j call.
- **Leiden** vs Louvain: `gds.louvain.write → gds.leiden.write`, same projection. Leiden's key fix: periodically breaks down poorly-connected communities. Our 16-cluster / 0.5324 modularity result should improve.
- **SLLPA** (overlapping communities) may surface multi-theme verses better than hard Louvain partitions — Quranic concepts naturally cross verse and surah boundaries.
- **APOC**: `apoc.periodic.iterate(..., {batchSize:1000})` is the right primitive for schema migrations (re-embedding, edge type renames). `apoc.text.sorensenDiceSimilarity` for Arabic transliteration fuzzy match.
- **HippoRAG postmortem hint**: PPR failed likely due to (a) 200K-edge noisy projection, (b) damping 0.85, (c) equal source weights. Re-run with narrowed Verse+Concept+Lemma projection + tf-idf weights + lower damping.

## Action verdict
- ✅ Adopt — enable slow-query logging in `neo4j.conf`.
  **Promoted as:** `from_neo4j_crawl_enable_slow_query_log` (priority 90)
- ✅ Adopt — audit `SHOW INDEXES` and create missing range + fulltext indexes.
  **Promoted as:** `from_neo4j_crawl_audit_indexes` (priority 88)
- ✅ Adopt — refactor `tool_semantic_search` to single-shot vector + traversal Cypher.
  **Promoted as:** `from_neo4j_crawl_single_shot_vector_traversal` (priority 78)
- ✅ Adopt — create Arabic fulltext index (`fulltext.analyzer: 'arabic'`).
  **Promoted as:** `from_neo4j_crawl_arabic_fulltext_index` (priority 75)
- ✅ Adopt — run parameterization audit on all Cypher in `chat.py`.
  **Promoted as:** `from_neo4j_crawl_004_parameterize_audit` (P1)
- 🔬 Research deeper — FastRP 128-d structural embeddings A/B vs BGE-only on QRCD.
  **Promoted as:** `from_neo4j_crawl_007_fastrp_structural_embeddings` (P2)
- 🔬 Research deeper — Leiden vs Louvain comparison on existing projection.
  **Promoted as:** `from_neo4j_crawl_006_swap_louvain_for_leiden` (P2)

## Cross-references
- [[vector-graphrag-neo4j-docs]] — vector index specifics (HNSW tuning, quantization)
- [[hipporag-negative-result]] — PPR negative result; GDS re-run advice here
- [[eval-qrcd-report]] — QRCD numbers that GDS improvements should improve
- Source: `repo://data/research_neo4j_crawl/03_cypher_gds_perf.md`
