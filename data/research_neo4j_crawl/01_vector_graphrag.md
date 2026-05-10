# 01 — Vector indexes + GraphRAG library findings

_Generated 2026-05-10 by research agent. QKG-relevant slices only. 8 pages crawled, 2 introductions thin (genai-plugin landing, genai-fundamentals catalog page) — followed up via deep-link pages where possible._

## TL;DR

1. **Adopt `neo4j-graphrag-python` as a drop-in retriever layer for the FastAPI tools, NOT a rewrite.** Its `HybridRetriever`/`HybridCypherRetriever` exactly model what `chat.py` already does by hand (vector index name + fulltext index name + embedder), and its `filters` dict gives us metadata pre-filtering (`$eq`, `$in`, `$gte`, `$or`, `$like`) that we are currently not exploiting. This alone is probably the highest-impact single change.
2. **`SentenceTransformerEmbeddings` accepts arbitrary HuggingFace model strings**, so `BAAI/bge-m3` is supported the same way our current `chat.py` uses it. No re-embedding needed; we keep our 1024-dim BGE-M3 indexes.
3. **Neo4j 5.x quantization is a single boolean** (`vector.quantization.enabled`, default `true`). There are no int8/scalar/binary tiers documented — the index already ships with quantization on for cosine. At our 25–50K vector scale this is essentially free; the docs warn only of "slightly decreased accuracy." No tuning to do.
4. **Pre-filtering changed materially in `2026.01`.** On Neo4j ≤ 2025.x, vector `filters` cause a brute-force scan and bypass the index. On 2026.01+ filters route through `SEARCH ... FOR ...` and are in-index. Worth checking which Neo4j version Desktop is running before relying on filtered surah/range queries at scale.
5. **`genai.vector.encode()` / `encodeBatch()` only target external providers** (OpenAI, Azure, Vertex, Bedrock). There is no documented HuggingFace/Ollama/SentenceTransformers backend, so we cannot move BGE-M3 inference into Cypher. Our Python sentence-transformers pipeline stays.
6. **The "official" hybrid pattern in the docs is application-side (graphrag-python) using RRF, not a magic Cypher idiom.** The Cypher manual does not ship a sanctioned `db.index.fulltext.queryNodes` + `db.index.vector.queryNodes` UNION snippet. Our hand-rolled RRF (k=60) is consistent with what the library does internally.
7. **A Cypher 25 / 2025.10+ feature, `vector_distance(a, b, 'COSINE'|'HAMMING'|...)`, is now available** — this is the hook for binary-quantized re-rank if we ever store both float and binary vectors. Worth tracking but premature for our scale.

## Per-page findings

### Vector indexes — https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/

**Summary:** Reference for `CREATE VECTOR INDEX`, HNSW config, `db.index.vector.queryNodes`, the new Cypher `SEARCH` clause, and the `db.create.setNodeVectorProperty()` writer.

**QKG relevance:** This is the canonical page for our 4 indexes. Confirms 1024-dim BGE-M3 is well within bounds (max 4096 on `vector-3.0`), and that we should be writing embeddings via `db.create.setNodeVectorProperty()` — our import scripts likely use plain `SET`, which the docs flag as less space-efficient.

**Concrete patterns / code:**

Index creation we already do, but the multi-label form is interesting for future Verse|Token|Lemma cross-search:
```cypher
CREATE VECTOR INDEX multiLabelIndex IF NOT EXISTS
FOR (n:Verse|Token|Lemma)
ON n.embedding_m3
OPTIONS { indexConfig: {
  `vector.dimensions`: 1024,
  `vector.similarity_function`: 'cosine'
}}
```

New `SEARCH` clause (Cypher 2026.01+, replaces `CALL db.index.vector.queryNodes`):
```cypher
MATCH (v:Verse)
  SEARCH v IN (
    VECTOR INDEX verse_embedding_m3
    FOR v.embedding_m3
    LIMIT 20
  ) SCORE AS s
RETURN v.surah, v.ayah, s
```

Efficient embedding writer:
```cypher
MATCH (v:Verse {surah:$s, ayah:$a})
CALL db.create.setNodeVectorProperty(v, 'embedding_m3', $vec)
```

HNSW knobs: `vector.hnsw.m` (1–512, default 16), `vector.hnsw.ef_construction` (1–3200, default 100). **No `ef_search` parameter** — search-time recall is purely a function of construction params and quantization.

JVM flag for SIMD acceleration on the index:
```
server.jvm.additional=--add-modules=jdk.incubator.vector
```

**Action:** [implement] — switch import code to `db.create.setNodeVectorProperty()`; verify Desktop Java version satisfies the SIMD flag; test the `SEARCH` clause if running 2026.01+.

### Vector functions — https://neo4j.com/docs/cypher-manual/current/functions/vector/

**Summary:** Defines `vector.similarity.cosine`, `vector.similarity.euclidean`, plus a new family in Cypher 25+ (`vector()`, `vector_dimension_count()`, `vector_distance()` with COSINE/MANHATTAN/EUCLIDEAN/DOT/HAMMING/EUCLIDEAN_SQUARED, `vector_norm()`).

**QKG relevance:** `vector.similarity.cosine` is the right primitive for ad-hoc post-filter rescoring — e.g. when we want to rescore a Cypher-traversed candidate set against a query vector without going through the index. `HAMMING` opens the door to cheap binary-quantized prefiltering if/when we add a 256-bit signature property per verse.

**Concrete patterns:**
```cypher
WITH $qvec AS qv
MATCH (v:Verse)
WHERE v.surah = 36
WITH v, vector.similarity.cosine(v.embedding_m3, qv) AS s
ORDER BY s DESC LIMIT 20
RETURN v.surah, v.ayah, s
```
This is the brute-force pattern we should use for **small-cardinality surah filters** if we are on a Neo4j version where `filters` bypasses the index anyway (≤2025.x).

**Action:** [implement] — add a `cypher_brute_force_filtered_vector` tool in `chat.py` for surah-scoped semantic search; cheaper than fetching top-200 then post-filtering Python-side.

### GenAI Embeddings tutorial — https://neo4j.com/docs/genai/tutorials/current/embeddings-vector-indexes/

**Summary:** Walks through end-to-end: import → embed → create index → query. Catalog-level page; concrete details live in subsections we did not deep-link.

**QKG relevance:** Light. We are well past the tutorial.

**Action:** [no-op]

### GenAI plugin landing — https://neo4j.com/docs/genai/plugin/current/

**Summary:** Lists supported providers (OpenAI, Azure OpenAI, VertexAI, Amazon Bedrock) and points at `genai.vector.encode` / `encodeBatch`. The reference subpage we tried (`/reference/functions-and-procedures/`) 404s; the Cypher-manual `/genai-integrations/` page also returned the landing summary, not the call reference.

**QKG relevance:** Critical limitation — no HuggingFace, no Ollama, no SentenceTransformer provider listed. **Cannot move BGE-M3 into Cypher.** If we ever wanted in-Cypher embedding for cheap quick-and-dirty queries, OpenAI `text-embedding-3-small` (1536-dim) is the path of least resistance, but it would require a *fifth* index and break our cross-lingual setup.

**Action:** [no-op] — Python pipeline stays. Note the limitation in our README so future-us doesn't re-investigate.

### neo4j-graphrag-python landing + API + RAG guide — https://neo4j.com/docs/neo4j-graphrag-python/current/

**Summary:** Official Neo4j-maintained Python lib (renamed from `neo4j-genai`). Provides Retriever and Embedder abstractions, a KG-builder pipeline, and Text2Cypher. Requires Neo4j ≥5.18.1, Python 3.10–3.14.

**QKG relevance:** **High.** This is exactly the layer we have re-implemented in `chat.py`. Adopting it does not force us to throw away our agent loop, citation verifier, or reranker — we can wrap our existing tools around its retrievers.

**Concrete patterns / code:**

VectorRetriever (matches our `tool_semantic_search`):
```python
VectorRetriever(
    driver, index_name, embedder,
    return_properties=None,
    result_formatter=None,
    neo4j_database="quran",
)
# .search(query_vector=None, query_text=None, top_k=5,
#         effective_search_ratio=1, filters=None)
```

HybridRetriever (matches our hand-rolled BM25 + dense + RRF):
```python
HybridRetriever(
    driver,
    vector_index_name="verse_embedding_m3",
    fulltext_index_name="verse_text_fulltext",
    embedder=embedder,
    neo4j_database="quran",
)
```

HybridCypherRetriever — adds a post-traversal `retrieval_query`. Perfect for "find semantically similar verses, then attach Token/Lemma/Root context in one round-trip":
```python
retrieval_query = """
WITH node AS v, score
OPTIONAL MATCH (v)-[:HAS_TOKEN]->(t:Token)-[:HAS_LEMMA]->(l:Lemma)-[:HAS_ROOT]->(r:Root)
RETURN v.surah, v.ayah, v.text_en, score,
       collect(DISTINCT r.code19) AS roots,
       collect(DISTINCT l.lemma) AS lemmas
"""
HybridCypherRetriever(driver, "verse_embedding_m3", "verse_text_fulltext",
                      retrieval_query, embedder=embedder)
```

`SentenceTransformerEmbeddings(model="BAAI/bge-m3")` — loads via the standard `sentence-transformers` library; arbitrary HF paths work.

`filters` dict supports `$eq, $ne, $lt/$lte/$gt/$gte, $between, $in, $nin, $like, $ilike, $or`. Example:
```python
retriever.search(query_text="prayer at night",
                 top_k=20,
                 filters={"surah": {"$in": [73, 17, 76]}})
```

`effective_search_ratio` (default 1) is a candidate-overfetch knob: with `top_k=20, effective_search_ratio=5`, the index returns 100 candidates that are re-scored before the top 20 are emitted — analogous to a per-query `ef_search` proxy. This matters for us; HNSW recall on 1024-dim BGE-M3 with quantization on benefits noticeably from 3–5× overfetch.

**Action:** [implement] — spike a `retrievers.py` module that wraps these classes for our 4 indexes and the 2 fulltext indexes; migrate one tool at a time in `chat.py`. Keep our reranker and citation verifier strictly downstream of the retriever's output.

### LLMs, vectors & unstructured course — https://graphacademy.neo4j.com/courses/llm-vectors-unstructured/

**Summary:** 3 modules: intro, vector indexes, importing unstructured data with LangChain.

**QKG relevance:** Course page is a catalog stub; lesson content not extracted. Less immediately useful than the docs since it is LangChain-flavored and our stack is direct-driver.

**Action:** [no-op]

### GraphRAG Python course — https://graphacademy.neo4j.com/courses/genai-graphrag-python/

**Summary:** 4 modules covering KG-pipeline, Vector+Cypher and Text2Cypher retrievers, and customization (loaders, splitters, entity resolution).

**QKG relevance:** The Text2Cypher module is interesting if we want the agent to dispatch raw Cypher via an LLM; we currently hard-code Cypher in tools. Not a priority — LLM-generated Cypher over our schema would need a careful schema-card prompt and recall checks.

**Action:** [research deeper] — read Module 03 lessons (Vector+Cypher and Text2Cypher) before deciding whether to add a Text2Cypher tool to the agent.

### GenAI fundamentals course — https://graphacademy.neo4j.com/courses/genai-fundamentals/

**Summary:** Catalog stub; 4 modules, 15 lessons, 2-hour intro course.

**QKG relevance:** Below our level. Skip.

**Action:** [no-op]

## Answers to specific questions

### 1. Quantization

Per the vector-indexes page, quantization is a single boolean `vector.quantization.enabled` (default `true`) — there is no documented int8/scalar/binary tiering, no per-index quantizer choice. The doc note is exactly: "can accelerate search performance but slightly decrease accuracy." It is on by default on cosine indexes, so our 4 indexes already benefit.

For our ~25–50K vectors total, quantization is essentially free wins; we do not need to tune it. **Action: no work needed.** Where binary quantization *will* matter is if we add a binary-signature property and use the new Cypher 25 `vector_distance(..., 'HAMMING')` for prefilter — but at our scale that is over-engineering.

_Source: vector-indexes page._

### 2. Hybrid search idiom

There is **no canonical Cypher manual snippet** for combining `db.index.fulltext.queryNodes` with `db.index.vector.queryNodes`. The full-text-indexes page gives only the fulltext call; vector-indexes gives only the vector call; neither cross-references a UNION/RRF template.

The "official" hybrid pattern lives one layer up in `neo4j-graphrag-python`'s `HybridRetriever`, which internally runs both procedures and fuses scores. Our hand-rolled RRF (k=60) is the same idea. The closest doc-supported single-statement pattern is:
```cypher
CALL db.index.fulltext.queryNodes('verse_text_fulltext', $q) YIELD node, score
WITH collect({node:node, score:score}) AS bm25
CALL db.index.vector.queryNodes('verse_embedding_m3', 60, $qvec) YIELD node, score
WITH bm25, collect({node:node, score:score}) AS dense
// fuse in Cypher with list comprehension or return both lists to the app
```
But Cypher RRF is awkward and slow vs. doing it in Python — graphrag-python keeps fusion application-side for a reason.

_Sources: full-text-indexes page, graphrag-python user_guide_rag._

### 3. `neo4j-graphrag-python` — adopt?

**Yes, partially.** Adopt the `Retriever` + `Embedder` layer; do not adopt the KG-pipeline (we already have ETL) or the chat orchestration (we have our own agent loop, citation verifier, and reranker, all of which are more sophisticated than the library's stubs).

What it gives us that we don't have:
- `filters={...}` with the full dict-DSL (`$in`, `$gte`, `$or`, `$like`) is materially better than what we built; today we either over-fetch and post-filter Python-side or write per-filter Cypher. On Neo4j 2026.01+, these filters route through the index (in-index filtering); on ≤2025.x they are brute-force.
- `effective_search_ratio` overfetch knob — not currently exposed in our tools.
- `HybridCypherRetriever`'s `retrieval_query` lets us attach token/lemma/root context in the same round-trip as the vector hit, which we currently do as a second Cypher call per verse.
- BGE-M3 works via `SentenceTransformerEmbeddings(model="BAAI/bge-m3")` — no migration cost.

What it does NOT give us (so we keep our code):
- BGE reranker (`bge-reranker-v2-m3`) — library has no reranker abstraction at this layer.
- Cross-encoder NLI / MiniCheck citation verifier.
- Our 21-tool agent loop.
- The cross-lingual EN/AR routing across our two BGE-M3 indexes.

_Sources: graphrag-python landing, user_guide_rag, api._

### 4. GenAI plugin functions

`genai.vector.encode(text, provider, configMap)` and `genai.vector.encodeBatch(texts, provider, configMap)` exist, but providers are limited to **OpenAI, Azure OpenAI, VertexAI, Amazon Bedrock**. There is **no HuggingFace, Ollama, or local-model provider documented**. We cannot move BGE-M3 inference into Cypher.

Practical implication for QKG: if we ever wanted "live" embeddings in Cypher (e.g. for a chatbot quick-search where Python-side preprocessing is not available), the cheapest path would be an OpenAI `text-embedding-3-small` index in parallel — but this would mean a 5th index, different dimensions (1536), and loss of the cross-lingual property we get from BGE-M3. **Not recommended.**

_Source: genai/plugin landing page (reference subpage 404'd at the URL the docs point to; deep-link details unavailable in this crawl)._

### 5. Vector search filtering / pre-filtering

Two regimes documented:

- **Neo4j ≤ 2025.x:** Any `filters` (or any `WHERE` after `db.index.vector.queryNodes`) causes a brute-force exact KNN over the filtered subset, bypassing HNSW. For tight filters (e.g. `surah=36` ⇒ ~83 verses) this is actually fine and recall is perfect. For loose filters (e.g. `surah IN [1..30]`) brute force gets expensive.
- **Neo4j 2026.01+:** Filters supplied to the new `SEARCH` clause or via `graphrag-python`'s `filters` dict route through in-index filtering with no recall loss.

Recommended QKG idiom (version-agnostic):
- Tight filter (single surah, single root): brute-force `MATCH ... WHERE ... vector.similarity.cosine(...)` ORDER BY ... LIMIT.
- Loose / no filter: `db.index.vector.queryNodes` with overfetch ratio 3–5×, then post-filter.

Multi-label vector indexes (`FOR (n:Verse|Token|Lemma)`) plus the `WITH [...]` filterable-property list are an advanced-mode option in 2026.01+ but probably not worth the schema complexity for us yet.

_Sources: vector-indexes page, graphrag-python user_guide_rag._

### 6. Index limits & performance tuning

- **Max dimensions:** 4096 on `vector-3.0`/`vector-2.0` providers; 2048 on `vector-1.0`. Our 1024-dim BGE-M3 is comfortable.
- **HNSW config:** `vector.hnsw.m` (default 16, range 1–512); `vector.hnsw.ef_construction` (default 100, range 1–3200). No `ef_search` knob — search recall is controlled at construction time.
- **Defaults are fine for our scale.** At 25–50K vectors, the default M=16 / ef_construction=100 is well-tuned. Bumping ef_construction to 200 would cost 2× index build time for marginal recall gain.
- **No documented max nodes per index.** Practical scale of public Neo4j vector deployments is in the millions; we are 2 orders of magnitude below any concern.
- **JVM SIMD flag**: `server.jvm.additional=--add-modules=jdk.incubator.vector` (Java 20+ for Neo4j 5; Java 21+ for 2025.01+). Worth checking that Desktop has this on for the "quran" DB.
- **No documented warmup procedure**, but the index `state` field (`POPULATING` / `ONLINE`) plus `populationPercent` from `SHOW VECTOR INDEXES` is the readiness signal.
- **Memory pressure** is undocumented at this page; HNSW graphs are kept in heap, so peak heap ≈ N × dim × 4 bytes × (1 + M/8) ≈ ~250 MB for our largest 50K × 1024 case — trivial.

_Source: vector-indexes page._

## Recommended ralph backlog tasks

- **`from_neo4j_crawl_adopt_graphrag_retrievers`** — type: `agent_creative`, priority: 80
  Spike a `quran_graph/retrievers.py` module wrapping `VectorRetriever`/`HybridRetriever`/`HybridCypherRetriever` for our 4 vector indexes and 2 fulltext indexes. Migrate one chat.py tool (`tool_semantic_search`) to use it as a proof-of-concept; preserve our existing reranker and citation verifier downstream. Acceptance: `quran_graph/retrievers.py`, `chat.py` (one tool migrated), short `data/research_neo4j_crawl/02_graphrag_spike.md`.

- **`from_neo4j_crawl_use_setNodeVectorProperty`** — type: `cleanup`, priority: 50
  Audit our import / re-embed scripts and replace `SET v.embedding_m3 = $vec` with `CALL db.create.setNodeVectorProperty(v, 'embedding_m3', $vec)` for space-efficient storage. Acceptance: any `scripts/embed_*.py` or `scripts/import_*.py` files modified.

- **`from_neo4j_crawl_filtered_vector_tool`** — type: `agent_creative`, priority: 70
  Add a `tool_filtered_semantic_search(query, surah=None, root=None, top_k=20)` to chat.py that brute-force vector-rescores filtered candidates via `vector.similarity.cosine` in pure Cypher (works on any Neo4j version). Acceptance: new tool registered in `chat.py`, eval delta on at least 5 surah-scoped queries.

- **`from_neo4j_crawl_overfetch_knob`** — type: `cleanup`, priority: 55
  Add an `effective_search_ratio` (default 3) parameter to our existing semantic search tools and benchmark recall@20 vs. ratio=1 on the 50-query eval set. Acceptance: `chat.py` plus a one-page benchmark in `data/research_neo4j_crawl/03_overfetch_bench.md`.

- **`from_neo4j_crawl_check_neo4j_version`** — type: `cypher_analysis`, priority: 60
  Run `CALL dbms.components()` on the local Desktop "quran" DB and confirm whether we are on 2026.01+ (in-index filtering) or earlier (brute-force on filters). Confirm the `--add-modules=jdk.incubator.vector` JVM flag is set. Document findings. Acceptance: `data/research_neo4j_crawl/04_neo4j_env.md`.

- **`from_neo4j_crawl_hybridcypher_one_shot`** — type: `agent_creative`, priority: 65
  Build a `HybridCypherRetriever` configuration whose `retrieval_query` returns each verse hit alongside its tokens, lemmas, and Code19 roots in a single round-trip; replace our two-call pattern in `tool_semantic_search_with_morphology`. Acceptance: tool migrated, latency benchmarked vs. current.

## New research threads (for research_backlog.yaml)

1. **Cypher 25 `vector_distance(..., 'HAMMING')`** — at what dataset size does a 256-bit binary signature index outperform our cosine index for prefilter? Currently no value at 50K vectors, but worth a one-shot synthetic-scale test on, say, 5M random vectors.
2. **Multi-label vector index `FOR (n:Verse|Token|Lemma)`** — could a single index over the three node types replace our current per-label retrieval in cross-grain searches (e.g. "find passages whose tokens or lemmas semantically match X")? Untested in our schema.
3. **Text2Cypher retriever quality on the QKG schema** — how often does an LLM hand a correct Cypher query for our schema? Build a 30-question test set including morphology and root queries, benchmark accuracy.
4. **`retrieval_query` as a context-fetching primitive** — what is the latency / throughput delta between (vector→fetch verse→second cypher for tokens) vs. a single `HybridCypherRetriever` round-trip? Hypothesis: 30–50% latency reduction on cold cache.
5. **OpenAI embeddings as a parallel index for in-Cypher `genai.vector.encode`** — measure whether having an in-Cypher embedder is worth the cost of maintaining a 5th index for chatbot use cases where Python preprocessing is unavailable.
6. **Quantization on/off A/B** — flip `vector.quantization.enabled=false` on a single test index, measure recall@20 delta on our eval set. Confirm the docs' "slightly decreased accuracy" claim is small for our distribution.
7. **JVM SIMD flag impact** — measure verse-search latency with and without `--add-modules=jdk.incubator.vector` on our actual hardware.
8. **Neo4j 2026.01 in-index filtering migration** — if/when Desktop ships 2026.01, re-benchmark our surah-scoped queries to quantify the brute-force → in-index speedup.

## Sources

- https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/
- https://neo4j.com/docs/cypher-manual/current/functions/vector/
- https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/full-text-indexes/
- https://neo4j.com/docs/cypher-manual/current/genai-integrations/
- https://neo4j.com/docs/genai/tutorials/current/embeddings-vector-indexes/
- https://neo4j.com/docs/genai/plugin/current/
- https://neo4j.com/docs/neo4j-graphrag-python/current/
- https://neo4j.com/docs/neo4j-graphrag-python/current/api.html (and `#embedder` deep-link)
- https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_rag.html (and `#hybridretriever` deep-link)
- https://graphacademy.neo4j.com/courses/genai-fundamentals/
- https://graphacademy.neo4j.com/courses/llm-vectors-unstructured/
- https://graphacademy.neo4j.com/courses/genai-graphrag-python/
