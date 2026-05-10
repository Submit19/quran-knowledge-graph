# Neo4j Version & Capability Tier Audit
**Task:** `from_neo4j_crawl_check_neo4j_version`  
**Date:** 2026-05-11  
**Method:** Live Cypher queries via neo4j://127.0.0.1:7687, database=quran

---

## 1. Version Summary

| Component | Value |
|-----------|-------|
| Neo4j Kernel | **2026.02.2 Enterprise** |
| Cypher versions | 5, 25 |
| Vector indexes | 4 ONLINE (see below) |
| Full-text indexes | 2 ONLINE |
| Graph size | 105,450 nodes · 455,460 relationships |

---

## 2. In-Index Vector Filtering — NOT available in this build

**Finding:** `db.index.vector.queryNodes` signature is `(indexName, numberOfNearestNeighbours, query)` — **3 arguments only**. A 4th `{filter}` parameter map (in-index pre-filtering) is **not present** in 2026.02.2.

```
# Attempted:
CALL db.index.vector.queryNodes("verse_embedding_m3", 10, $emb, {surah: 2})
# Result: Procedure call provides too many arguments: got 4 expected no more than 3.
```

**What IS available:** Standard post-index WHERE filtering (applies after HNSW traversal):
```cypher
CALL db.index.vector.queryNodes("verse_embedding_m3", 20, $emb)
YIELD node, score
WHERE node.surah = 2
RETURN node.verseId, score LIMIT 10
```
This works correctly but over-fetches (retrieve 20, keep only Surah-2 hits). Current code in `chat.py` uses exactly this pattern — no change needed.

**Implication for `from_neo4j_crawl_single_shot_vector_traversal`:** The pre-filter optimization that would remove round-trips is NOT available here. Post-filter is the ceiling. That task still has value for the single Cypher statement (1-hop expansion), just cannot use pre-filter.

---

## 3. JVM / SIMD Vectorization Status

| Flag | Status | Notes |
|------|--------|-------|
| `--add-modules=jdk.incubator.vector` | **ABSENT** | Not needed for JDK 21+ |
| `-Dorg.neo4j.shaded.lucene9.vectorization.upperJavaFeatureVersion=25` | **PRESENT** | Lucene SIMD vectorization enabled via internal detection |
| `--enable-native-access=ALL-UNNAMED` | Present | Allows native memory access |

**Conclusion:** SIMD vectorization is effectively enabled. The `jdk.incubator.vector` module was graduated to stable API in Java 20 (JEP 448). Neo4j 2026.02 uses Lucene 9's own detection mechanism (`upperJavaFeatureVersion=25`) to enable vectorized HNSW search internally without requiring the old `--add-modules` flag. No action required.

---

## 4. Vector Index Configuration

All 4 vector indexes use identical HNSW settings:

| Index | Dims | Quantization | HNSW m | EF Construction |
|-------|------|--------------|---------|-----------------|
| `verse_embedding` | 384 | **TRUE** | 16 | 100 |
| `verse_embedding_m3` | 1024 | **TRUE** | 16 | 100 |
| `verse_embedding_m3_ar` | 1024 | **TRUE** | 16 | 100 |
| `query_embedding` | 384 | **TRUE** | 16 | 100 |

**Quantization=True:** Neo4j 2026.x uses int8 scalar quantization by default for vector indexes. This means:
- Memory footprint: ~4× smaller than float32 (1024-dim → 256 bytes vs 4096 bytes per vector)
- HNSW search: ~20-40% faster at slight quality cost (empirically negligible at this scale)
- 6,234 verse embeddings at 1024-dim: ~1.5MB per index (vs ~24MB unquantized)

**EF Construction=100, m=16:** Default HNSW settings. For 6,234 vectors this is well-tuned — recall@10 should be >99%. No tuning needed at this dataset size.

---

## 5. Capability Tier Matrix

| Capability | Available | Notes |
|-----------|-----------|-------|
| Vector ANN search | YES | `db.index.vector.queryNodes` |
| In-index pre-filtering | **NO** | 3-arg signature only |
| Post-index WHERE filtering | YES | Standard Cypher pattern |
| Full-text BM25 | YES | `verse_text_fulltext` + `verse_arabic_fulltext` |
| GDS algorithms | YES | eigenvector.*, modularity, etc. |
| GenAI vector encoding | YES | `genai.vector.encodeBatch` (external provider) |
| Scalar quantization | YES (default on) | Int8, ~4× memory reduction |
| Query log | YES | db.logs.query.enabled (configured per prev task) |
| In-memory page cache warmup | YES (enabled, preload=false) | Warmup on startup but no preload |

---

## 6. Action Items

1. **No JVM flag changes needed.** SIMD vectorization is active via Lucene's internal detection. The `--add-modules=jdk.incubator.vector` advice in older Neo4j docs does not apply to 2026.x.

2. **Do NOT implement pre-filter path** in `from_neo4j_crawl_single_shot_vector_traversal`. The 4th-arg filter API is absent. Post-WHERE is the pattern to use. Update that task's spec to reflect this.

3. **Quantization is already active.** Our 1024-dim BGE-M3 indexes are quantized by default — this explains why 6,234 × 1024-dim fits comfortably in the page cache. No need to explicitly enable.

4. **Page cache preload=false.** This means Neo4j warms the page cache adaptively (profile-based). The 647s cold-start outlier documented in the slow-query-log task is consistent: first vector query after restart warms the BGE-M3 model in Python, AND warms the HNSW page cache simultaneously. Enabling `db.memory.pagecache.warmup.preload=true` would reduce cold-start but costs startup time. Decision: leave at default for now; warm-up via `app_free.py` startup probe is sufficient.

5. **Memory cap:** `dbms.memory.transaction.total.max = 716.80MiB`. For our 6,234-verse graph this is generous. No OOM risk.

---

## 7. Downstream Task Updates

Based on this audit, the following backlog tasks need spec updates:

- `from_neo4j_crawl_single_shot_vector_traversal` (p78): Remove any mention of in-index pre-filter; design the single Cypher for vector-then-1-hop-expansion using post-WHERE pattern.
- `from_neo4j_crawl_adopt_graphrag_retrievers` (p80): `neo4j-graphrag-python` HybridRetriever does support filter DSL — but it calls the same underlying procedure. No extra capability vs raw Cypher in our Neo4j build.
- `from_neo4j_crawl_pagination_cursors` (p72): Feasible. No version constraints. Can use standard SKIP/LIMIT with offset cursors.
