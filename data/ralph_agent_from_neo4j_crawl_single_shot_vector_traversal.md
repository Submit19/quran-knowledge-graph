# Design Document: Single-Shot Vector + Graph Traversal
## Task: `from_neo4j_crawl_single_shot_vector_traversal`
*Produced at tick 59 IMPL | 2026-05-12*

---

## Executive Summary

**The premise of this task has already been implemented.** `tool_semantic_search` in `chat.py` already uses the VectorCypherRetriever pattern — a single Cypher statement that calls `db.index.vector.queryNodes()` and enriches results with three OPTIONAL MATCH expansions in the same round-trip. There is no second DB call to eliminate.

This document: (1) confirms the current implementation, (2) identifies what *is* still a two-phase pattern in `tool_hybrid_search`, (3) proposes a follow-up optimization, and (4) surfaces the one remaining latency opportunity.

---

## Current Implementation: `tool_semantic_search`

**Location:** `chat.py` lines 557–622

The function is a textbook VectorCypherRetriever:

```cypher
CALL db.index.vector.queryNodes($index, $k, $vec)
YIELD node, score
WHERE node.verseId IS NOT NULL
WITH node, score ORDER BY score DESC
OPTIONAL MATCH (node)-[:RELATED_TO]-(related:Verse)
WITH node, score, collect(DISTINCT related.reference)[0..5] AS related_verses
OPTIONAL MATCH (node)-[:MENTIONS_ROOT]->(root:ArabicRoot)
WITH node, score, related_verses,
     collect(DISTINCT root.root)[0..5] AS arabic_roots
OPTIONAL MATCH (node)-[typed:SUPPORTS|ELABORATES|QUALIFIES|CONTRASTS|REPEATS]-(te:Verse)
WITH node, score, related_verses, arabic_roots,
     [x IN collect(DISTINCT {type: type(typed), target: te.reference})
      WHERE x.type IS NOT NULL AND x.target IS NOT NULL][0..5] AS typed_edges
RETURN node.verseId AS verseId, node.surahName AS surahName,
       node.surah AS surah, node.text AS text, score,
       related_verses, arabic_roots, typed_edges
```

**DB calls:** 1 (the Cypher above).  
**Python-side enrichment loop:** None — Python only formats the flat results.  
**Conclusion:** already optimal for a pure vector retrieval path.

### Edge Types Currently Expanded

- `RELATED_TO` — verse-to-verse keyword co-occurrence (top 5 references)
- `MENTIONS_ROOT` — verse-to-ArabicRoot morphology (top 5 roots)
- `SUPPORTS | ELABORATES | QUALIFIES | CONTRASTS | REPEATS` — typed semantic edges (top 5)

All three expansions are bounded with `[0..5]` slices.

---

## Remaining Two-Phase Pattern: `tool_hybrid_search`

`tool_hybrid_search` (lines 1216–1330) necessarily makes **3 DB round-trips**:

1. `db.index.fulltext.queryNodes` — BM25 lexical candidates (top ~100)
2. `db.index.vector.queryNodes` — dense candidates (top ~100)
3. `UNWIND $ids + OPTIONAL MATCH` — graph enrichment on the RRF-fused top-K

Round-trips 1 and 2 cannot be merged because Neo4j does not support `CALL ... UNION CALL ...` for two different index types in a single statement (fulltext and vector indexes require separate `CALL` clauses). RRF fusion must happen in Python after receiving both ranked lists.

Round-trip 3 is the enrichment call, which is identical in structure to `tool_semantic_search`'s inline expansion. This is the **one genuine latency opportunity** in the hybrid path.

---

## Optimization Opportunity: Inline Enrichment for `hybrid_search`

### Current pattern (hybrid_search)

```
DB call 1 → BM25 top-100 (returns verseId + score)
DB call 2 → dense top-100 (returns verseId + score)
Python: RRF fusion → top_ids list
DB call 3 → UNWIND top_ids + OPTIONAL MATCH enrichment
```

### Proposed pattern

Calls 1 and 2 cannot be merged. But the enrichment (call 3) can be eliminated by fetching enrichment data together with each ranking call and caching per-verse:

```cypher
-- Call 1 (BM25 + enrichment)
CALL db.index.fulltext.queryNodes($idx, $q) YIELD node, score
WHERE node.verseId IS NOT NULL
WITH node, score ORDER BY score DESC LIMIT $n
OPTIONAL MATCH (node)-[:RELATED_TO]-(related:Verse)
WITH node, score, collect(DISTINCT related.reference)[0..5] AS related_verses
OPTIONAL MATCH (node)-[:MENTIONS_ROOT]->(root:ArabicRoot)
WITH node, score, related_verses,
     collect(DISTINCT root.root)[0..5] AS arabic_roots
OPTIONAL MATCH (node)-[typed:SUPPORTS|ELABORATES|QUALIFIES|CONTRASTS|REPEATS]-(te:Verse)
WITH node, score, related_verses, arabic_roots,
     [x IN collect(DISTINCT {type: type(typed), target: te.reference})
      WHERE x.type IS NOT NULL AND x.target IS NOT NULL][0..5] AS typed_edges
RETURN node.verseId AS verseId, node.surahName AS surahName,
       node.surah AS surah, node.text AS text, score,
       related_verses, arabic_roots, typed_edges

-- Call 2 (dense + enrichment) — same structure with vector call
CALL db.index.vector.queryNodes($idx, $n, $vec) YIELD node, score
...same OPTIONAL MATCH chain...
```

Python caches the enrichment keyed by `verseId`. After RRF fusion, it looks up the cached enrichment for the top-K IDs — no third DB call needed.

**Savings:** eliminates 1 DB round-trip per `hybrid_search` call. At a p50 Neo4j driver overhead of ~5–15ms per call, expected saving is ~5–15ms per query using hybrid_search. Tool-call cache (30s TTL) already deduplicates repeated calls, so savings are per-unique-query-per-30s.

**Trade-off:** slightly more data transferred in calls 1 and 2 (enrichment fields on up to 100 verses instead of top_k only). For `top_k=20` with `cand_n=100`, this adds ~80 extra enrichment payloads that get discarded after RRF. The Neo4j driver overhead of the extra OPTIONAL MATCH on 100 rows vs a separate query on 20 rows is query-plan dependent — **measure before committing** (see Eval Protocol below).

---

## Implementation Plan (for the follow-up code-change tick)

**Target:** `chat.py` → `tool_hybrid_search` only. `tool_semantic_search` requires no change.

### Steps

1. **Modify BM25 query** to include the three OPTIONAL MATCH enrichment clauses. Return `related_verses`, `arabic_roots`, `typed_edges` alongside `verseId` and `score`.

2. **Modify dense query** identically.

3. **Build enrichment cache** in Python:
   ```python
   enrichment_cache: dict[str, dict] = {}
   for r in bm25_with_enrichment:
       enrichment_cache[r["id"]] = {
           "surahName": r["surahName"], "surah": r["surah"], "text": r["text"],
           "related_verses": r["related_verses"], "arabic_roots": r["arabic_roots"],
           "typed_edges": r["typed_edges"],
       }
   for r in dense_with_enrichment:
       enrichment_cache.setdefault(r["id"], { ... })  # don't overwrite BM25 data
   ```

4. **Remove the third DB call** (the `UNWIND $ids` block, lines 1288–1303).

5. **Update result assembly** to read from `enrichment_cache` instead of `by_id`.

6. Add a `data/benchmark_hybrid_search_roundtrip.py` micro-benchmark script comparing latency before/after on a representative 20-question set (mix of CONCRETE and BROAD from the 50q bucketed set when that lands).

### Acceptance for follow-up task
- `file_exists data/ralph_agent_from_neo4j_crawl_hybrid_search_inline_enrichment.md` (this doc)
- The actual code change: `chat.py` modified, `python -m py_compile chat.py` passes, benchmark script exists with results showing ≥0ms delta (neutral or positive)

---

## Eval Protocol (for the code-change tick)

1. Run `python eval_v1.py` before and after — compare avg cites and latency (mean/p95 from SSE event timestamps).
2. Run `python eval_qrcd_retrieval.py` — compare MAP@10 on the hybrid backend; any regression fails the gate.
3. Run the micro-benchmark on 20 representative queries, log the p50/p95 latency delta for DB calls.
4. **If p50 delta is negative (slower), revert.** The enrichment-on-100 vs enrichment-on-20 trade-off may not pay off at this scale.

---

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Enrichment on 100 rows in 2 queries is slower than enrichment on 20 rows in 1 query | Medium | Benchmark before merging; gate on latency delta |
| BM25 + dense may return overlapping verses — enrichment_cache handles this but needs dedup logic | Low | `setdefault` pattern handles dedup safely |
| If a verse appears only in BM25 (not dense), its enrichment must be in cache from call 1 — already covered | Low | Both calls fetch enrichment; cache populated from both |
| Future addition of a 4th index type (e.g. Arabic BM25) would require cache merge logic | Low | Pattern is extensible; document as architecture note |

---

## Summary for Backlog

`tool_semantic_search` is already fully optimized (single-shot). The only actionable optimization is removing the third DB call from `tool_hybrid_search` by inlining enrichment into the BM25/dense calls. Expected benefit: ~5–15ms per unique hybrid query. Low risk. Recommend a follow-up `cleanup`-type task at priority ~55 to implement the code change after benchmarking.

**Proposed follow-up task:** `from_neo4j_crawl_hybrid_search_inline_enrichment` (p55, cleanup type) — implement the 2-call pattern described above in `chat.py:tool_hybrid_search`.
