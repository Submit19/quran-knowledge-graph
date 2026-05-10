# Neo4j ecosystem crawl — INDEX

Methodical deep-coverage crawl of the three official Neo4j surfaces:
- https://neo4j.com/docs/
- https://graphacademy.neo4j.com/
- https://neo4j.com/resources/

**Scope (honest):** these sites have 10K+ pages combined. Recursive crawl of
every link is impractical. Instead, we identified the highest-value slices
relevant to QKG (Quran Knowledge Graph project) and crawled those deeply
via parallel subagents. Lower-priority pages are tracked in `research_backlog.yaml`
for the recurring loop to pick up over time.

## QKG context (what we're optimizing for)

| QKG component | Neo4j feature it depends on |
|---|---|
| 4 vector indexes (verse_embedding, _m3, _m3_ar, query_embedding) | Vector Search Indexes, GenAI plugin |
| Hybrid retrieval (BM25 + BGE-M3 + RRF) | Vector + full-text (`verse_text_fulltext`, `verse_arabic_fulltext`) |
| 21 agentic tools in chat.py | Cypher tool patterns, MCP server design |
| Reasoning memory (Query/Trace/ToolCall/RETRIEVED) | Context Graphs / agent memory patterns |
| Concept ER layer (Porter-stem) | Entity resolution, deduplication patterns |
| Modularity 0.5324, 16 communities | GDS Louvain / Leiden / community detection |
| Typed edges (SUPPORTS, ELABORATES, etc.) | Schema constraints, relationship patterns |
| HippoRAG PPR (negative result) | GDS Personalized PageRank |
| Cross-encoder rerank (BAAI/bge-reranker-v2-m3) | External — but pairs with vector search |

## Findings files (populated by crawl agents)

- `01_vector_graphrag.md` — Vector indexes, GenAI plugin, neo4j-graphrag-python, embeddings tutorials
- `02_agentic_patterns.md` — Context graphs, MCP tools, Aura agents, agent memory patterns
- `03_cypher_gds_perf.md` — Cypher optimization, indexes/constraints, GDS algorithms
- `99_followups.md` — Pages we didn't crawl deeply but should (queued in research_backlog.yaml)

## Process

Each finding entry follows this shape:

```
### <Title> (<URL>)

**Relevance to QKG:** <how it maps to our code/data>
**Key takeaway:** <1-3 sentences>
**Action:** <concrete patch / no-op / new task / research deeper>
**Promoted to ralph_backlog?:** Yes (id) / No
```

## Crawl summary table

| date | file | pages crawled | top finding |
|------|------|---------------|-------------|
| 2026-05-10 | `01_vector_graphrag.md` | 11 | Adopt `neo4j-graphrag-python` `HybridRetriever` — accepts BGE-M3, gives us filters DSL + overfetch knob we don't have |
| 2026-05-10 | `02_agentic_patterns.md` | 7+ | Our reasoning trace schema is missing `:ReasoningStep`; `neo4j-labs/agent-memory` does ~80% of `reasoning_memory.py` already |
| 2026-05-10 | `03_cypher_gds_perf.md` | 22 | The 647s `semantic_search` outlier is most likely cold-cache disk reads in the post-vector traversal — turn on slow-query log immediately, swap Louvain→Leiden, try FastRP+KNN |

## 25 actionable tasks proposed

Top 8 promoted directly into `ralph_backlog.yaml` (prefixed `from_neo4j_crawl_*`).
Remaining 17 captured in `data/research_neo4j_crawl/all_proposals.md` for review.

## 22 new research threads added to `research_backlog.yaml`

Spans: Cypher 25 features, multi-label vector indexes, Text2Cypher quality, page-cache sizing,
plan stability, vector recall@K, GDS lifecycle, 2026.04 SEARCH-syntax migration, Neo4j Agent Skills,
agent-memory library adoption, Aura cost model, KG-construction with LLMs, and more.

## Sources (all URLs crawled)

See `Sources` section in each `0X_*.md` file.
