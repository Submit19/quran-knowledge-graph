---
type: research
status: done
priority: 80
tags: [research/retrieval, research/neo4j, research/vector-search]
source: data/research_neo4j_crawl/01_vector_graphrag.md
date_added: 2026-05-10
---

# Vector Indexes + GraphRAG Library (Neo4j Docs Crawl)

## TL;DR
- `neo4j-graphrag-python` `HybridRetriever` / `HybridCypherRetriever` exactly models what `chat.py` already does by hand — adopt as the retriever layer, not a rewrite.
- `SentenceTransformerEmbeddings(model="BAAI/bge-m3")` works as-is; no re-embedding needed.
- Pre-filtering changed materially in Neo4j 2026.01: on older versions `filters` bypass the HNSW index (brute-force). On 2026.01+ filters route in-index.
- `genai.vector.encode()` supports OpenAI / Azure / Vertex / Bedrock only — BGE-M3 cannot move into Cypher; Python pipeline stays.
- `effective_search_ratio` overfetch knob (default 1 → use 3–5) improves HNSW recall for 1024-dim quantized indexes at negligible cost.

## Key findings
- **Import fix**: switch `SET v.embedding_m3 = $vec` to `CALL db.create.setNodeVectorProperty(v, 'embedding_m3', $vec)` for space-efficient storage.
- **New SEARCH clause** (Cypher 2026.01+) replaces deprecated `db.index.vector.queryNodes`; migration worthwhile once Neo4j Desktop upgrades.
- **Multi-label index** `FOR (n:Verse|Token|Lemma)` is a future option for cross-grain semantic search; not needed yet at current scale.
- **No documented `ef_search` knob** — recall is set at construction time via `ef_construction` (default 100). At 25–50K vectors, defaults are fine.
- **JVM SIMD flag** `--add-modules=jdk.incubator.vector` available for Neo4j Desktop; worth enabling for index speed.
- `HybridCypherRetriever` with a custom `retrieval_query` can return verse + Token + Lemma + Root in one round-trip, eliminating our current two-call pattern.

## Action verdict
- ✅ Adopt — spike `quran_graph/retrievers.py` wrapping `HybridRetriever` / `HybridCypherRetriever` for our 4 vector + 2 fulltext indexes.
  **Promoted as:** `from_neo4j_crawl_adopt_graphrag_retrievers` (priority 80)
- ✅ Adopt — switch import scripts to `db.create.setNodeVectorProperty`.
  **Promoted as:** `from_neo4j_crawl_use_setNodeVectorProperty` (priority 50)
- ✅ Adopt — add `effective_search_ratio` (default 3) to search tools.
  **Promoted as:** `from_neo4j_crawl_overfetch_knob` (priority 55)
- ✅ Adopt — add `tool_filtered_semantic_search` using `vector.similarity.cosine` for surah-scoped queries.
  **Promoted as:** `from_neo4j_crawl_filtered_vector_tool` (priority 70)
- 🔬 Research deeper — Text2Cypher retriever quality on the QKG schema; check GraphAcademy course Module 03.
- 🔬 Research deeper — confirm Neo4j Desktop version (`CALL dbms.components()`) to know if in-index filtering is available.
  **Promoted as:** `from_neo4j_crawl_check_neo4j_version` (priority 85)

## Cross-references
- [[agentic-patterns-neo4j]] — retriever layer feeds the agent loop described there
- [[cypher-perf-gds]] — index presence affects retriever performance
- [[bge-m3-dense-vs-colbert]] — embedding model compatibility with the retriever
- Source: `repo://data/research_neo4j_crawl/01_vector_graphrag.md`
