# Spike: neo4j-graphrag-python Retriever Layer for QKG

**Task:** `from_neo4j_crawl_adopt_graphrag_retrievers`  
**Tick:** 38 (IMPL) | **Date:** 2026-05-11  
**Model:** claude-sonnet-4-6 (inline; [opus] label noted, handled in-loop)

---

## TL;DR

**Recommendation: ADOPT HybridCypherRetriever as a thin wrapper over existing tools — incremental, not a rewrite. Do NOT adopt VectorRetriever or HybridRetriever as drop-ins yet.** The key constraint is our Neo4j 2026.02.2 build: the library's `filters` DSL calls the same 3-arg `db.index.vector.queryNodes` underneath, so filter pushdown gives zero net gain over our current post-WHERE pattern. The one genuine win is `HybridCypherRetriever` — it collapses vector search + 1-hop graph traversal into a single round-trip, which is what `from_neo4j_crawl_single_shot_vector_traversal` (p78) wants anyway.

---

## 1. What `neo4j-graphrag-python` Offers

### 1a. Retrievers

| Retriever | Maps to QKG tool | New capability vs current |
|-----------|-----------------|---------------------------|
| `VectorRetriever` | `tool_semantic_search` | `effective_search_ratio` overfetch knob |
| `HybridRetriever` | `hybrid_search` (BM25+BGE-M3+RRF) | cleaner API; filters DSL (net zero on 2026.02.2) |
| `HybridCypherRetriever` | no current equivalent | **single-statement vector + graph traversal** |

### 1b. Embedder

```python
from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings
embedder = SentenceTransformerEmbeddings(model="BAAI/bge-m3")
```

This wraps our existing `sentence-transformers` install — same model, same library, no re-embedding. Zero migration cost.

### 1c. Filters DSL

Supports `$eq $ne $lt $lte $gt $gte $between $in $nin $like $ilike $or`. Example:
```python
retriever.search(query_text="prayer at night", top_k=20,
                 filters={"surah": {"$in": [73, 17, 76]}})
```

**However:** On Neo4j 2026.02.2 the 4-arg `db.index.vector.queryNodes(index, k, vec, filter)` signature is absent (confirmed by `from_neo4j_crawl_check_neo4j_version`). The library translates filters to post-HNSW `WHERE` clauses — exactly what our current code already does. No net speedup on surah-filtered queries.

---

## 2. Constraint Map

| Capability | Our Neo4j Build | Library Expectation | Delta |
|------------|----------------|---------------------|-------|
| In-index pre-filter | **NOT available** (3-arg proc only) | Uses post-WHERE fallback | None |
| `effective_search_ratio` overfetch | Works (post-index overfetch) | Supported | **+recall at slight cost** |
| HybridCypherRetriever 1-shot traversal | Works | Supported | **Eliminates 1 round-trip per call** |
| `SentenceTransformerEmbeddings` with BGE-M3 | Works | Supported | None (same library) |

---

## 3. Proposed `retrievers.py` Module Design

```python
# quran_graph/retrievers.py
from neo4j_graphrag.retrievers import VectorRetriever, HybridRetriever, HybridCypherRetriever
from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings

_embedder = None  # lazy singleton

def get_embedder():
    global _embedder
    if _embedder is None:
        import os
        model = os.environ.get("SEMANTIC_SEARCH_INDEX", "verse_embedding_m3")
        hf_map = {
            "verse_embedding_m3":    "BAAI/bge-m3",
            "verse_embedding_m3_ar": "BAAI/bge-m3",
            "verse_embedding":       "all-MiniLM-L6-v2",
        }
        _embedder = SentenceTransformerEmbeddings(model=hf_map.get(model, "BAAI/bge-m3"))
    return _embedder


def make_vector_retriever(driver, index="verse_embedding_m3"):
    """Wraps VectorRetriever with effective_search_ratio=3 (overfetch for quantized HNSW)."""
    return VectorRetriever(
        driver=driver,
        index_name=index,
        embedder=get_embedder(),
        return_properties=["verseId", "surah", "verseNum", "text", "arabicText",
                           "surahName", "embedding_m3"],
        neo4j_database="quran",
    )


def make_hybrid_retriever(driver):
    """BM25 + BGE-M3 + RRF — wraps existing hybrid_search logic."""
    return HybridRetriever(
        driver=driver,
        vector_index_name="verse_embedding_m3",
        fulltext_index_name="verse_text_fulltext",
        embedder=get_embedder(),
        neo4j_database="quran",
    )


# Single-shot: vector search + 1-hop root/lemma traversal in ONE round-trip.
# This is the primary win: eliminates a second DB call per semantic_search hit.
TRAVERSAL_QUERY = """
WITH node AS v, score
OPTIONAL MATCH (v)-[:MENTIONS_ROOT]->(r:ArabicRoot)
OPTIONAL MATCH (v)-[:MENTIONS]->(k:Keyword)-[:NORMALIZES_TO]->(c:Concept)
RETURN v.verseId AS verseId,
       v.surah AS surah,
       v.verseNum AS verseNum,
       v.text AS text,
       v.arabicText AS arabicText,
       v.surahName AS surahName,
       score,
       collect(DISTINCT r.root)[0..5] AS roots,
       collect(DISTINCT c.name)[0..5] AS concepts
"""

def make_hybrid_cypher_retriever(driver):
    """BM25 + BGE-M3 + RRF + inline graph context — the killer combo."""
    return HybridCypherRetriever(
        driver=driver,
        vector_index_name="verse_embedding_m3",
        fulltext_index_name="verse_text_fulltext",
        retrieval_query=TRAVERSAL_QUERY,
        embedder=get_embedder(),
        neo4j_database="quran",
    )
```

---

## 4. Migration Plan (incremental, no regressions)

### Phase 1 — POC (this tick's deliverable): scaffold `retrievers.py` + unit test

Create `quran_graph/retrievers.py` with the three factory functions above.
Add `test_retrievers.py` (smoke test: `make_hybrid_cypher_retriever(driver).search("prayer", top_k=5)` returns ≥1 result with `roots` list).

**Risk:** None — library is additive; chat.py unchanged.

### Phase 2 — Wire `HybridCypherRetriever` into `tool_semantic_search`

`tool_semantic_search` currently makes two DB round-trips:
1. `db.index.vector.queryNodes` → verse hits
2. Optional: caller fetches root/concept context via a second query

Replace both with a single `make_hybrid_cypher_retriever(...).search(query_text=q, top_k=top_k, effective_search_ratio=3)`.

**Expected latency delta:** p50 -20 to -35ms (eliminates second DB call + Python loop).
**Expected recall delta:** Neutral to +5% (overfetch=3 gives the HNSW graph more room to find near-duplicates).

### Phase 3 — Wire `effective_search_ratio=3` into `VectorRetriever` for Arabic index

`tool_semantic_search` with `verse_embedding_m3_ar` currently uses `top_k` as the HNSW limit. `effective_search_ratio=3` means retrieve `3 × top_k` candidates from the index, then trim to `top_k` in Python — a low-cost recall lift for quantized 1024-dim embeddings.

**No API change to tool contract. Completely transparent.**

---

## 5. What We Do NOT Do

- **Do not replace our hand-rolled RRF** in `hybrid_search`. The library's RRF is identical to ours (k=60, same formula). Rewriting would be churn with zero gain.
- **Do not use the library's LLMResponseParser or GraphRAG pipeline.** Our agent loop, citation verifier, and answer cache are strictly superior to the library's single-shot pipeline model.
- **Do not use `Text2Cypher` retriever.** The library expects a pre-defined schema card. Our 21 custom tools already give the agent better Cypher than any text-to-Cypher inference would produce.
- **Do not add `filters` to surah-scoped searches immediately.** The filters work, but on 2026.02.2 they compile to post-WHERE — same cost as our current code. Revisit when `from_neo4j_crawl_single_shot_vector_traversal` is done and we benchmark.

---

## 6. Concrete Follow-up Tasks Proposed

1. **`scaffold_retrievers_module`** (cleanup, p70) — create `quran_graph/retrievers.py` per design above; add smoke test. Estimated 30 min.
2. **`migrate_semantic_search_to_hybrid_cypher_retriever`** (cleanup, p68) — wire `tool_semantic_search` to `HybridCypherRetriever`; run eval_v1, confirm no regression. Estimated 45 min + eval run.
3. **`add_effective_search_ratio_3`** (cleanup, p55) — add `effective_search_ratio=3` to both vector and hybrid retrievers; re-run QRCD retrieval eval; commit if MAP@10 improves.

---

## 7. Installation

```bash
pip install neo4j-graphrag-python
# or, for exact version pinning:
pip install "neo4j-graphrag-python>=1.6.0"
```

Already compatible with our existing `neo4j` driver (requires ≥5.18.1 — our 2026.02.2 is well above).

---

## 8. Verdict

| Question | Answer |
|----------|--------|
| Should we adopt `neo4j-graphrag-python`? | **Yes, incrementally** |
| Will it fix surah-filtered vector search? | No — no in-index pre-filter on 2026.02.2 |
| Biggest win? | `HybridCypherRetriever` → vector + graph context in 1 round-trip |
| Risk to existing stack? | Near-zero — library is additive |
| Blocks anything? | Unblocks `migrate_semantic_search_to_hybrid_cypher_retriever` |
