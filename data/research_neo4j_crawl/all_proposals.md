# All 25 task proposals — 2026-05-10 Neo4j ecosystem crawl

The 8 highest-priority items have been promoted to `ralph_backlog.yaml` (search
for `from_neo4j_crawl_*`). The remaining 17 are below for review — promote any
of them to the backlog by hand or wait for the loop's `discover_new_followups`
ticks to surface them again.

## Promoted to ralph_backlog.yaml (top 8)

| id | type | priority | source agent |
|----|------|---------:|--------------|
| `from_neo4j_crawl_enable_slow_query_log` | cypher_analysis | 90 | 03 |
| `from_neo4j_crawl_audit_indexes` | cypher_analysis | 88 | 03 |
| `from_neo4j_crawl_check_neo4j_version` | cypher_analysis | 85 | 01 |
| `from_neo4j_crawl_trace_vector_index` | agent_creative | 82 | 02 |
| `from_neo4j_crawl_adopt_graphrag_retrievers` | agent_creative | 80 | 01 |
| `from_neo4j_crawl_single_shot_vector_traversal` | agent_creative | 78 | 03 |
| `from_neo4j_crawl_arabic_fulltext_index` | agent_creative | 75 | 03 |
| `from_neo4j_crawl_pagination_cursors` | agent_creative | 72 | 02 |

## Held for later — agent 1 (vector + GraphRAG)

- `from_neo4j_crawl_filtered_vector_tool` (70, agent_creative) — new `tool_filtered_semantic_search(query, surah=None, root=None, top_k=20)` that brute-force vector-rescores filtered candidates via `vector.similarity.cosine` in pure Cypher (works on any Neo4j version).
- `from_neo4j_crawl_hybridcypher_one_shot` (65, agent_creative) — `HybridCypherRetriever` with `retrieval_query` returning verse + tokens + lemmas + Code19 roots in one round trip.
- `from_neo4j_crawl_overfetch_knob` (55, cleanup) — add `effective_search_ratio` (default 3) to existing semantic search tools, benchmark recall@20.
- `from_neo4j_crawl_use_setNodeVectorProperty` (50, cleanup) — replace `SET v.embedding_m3 = $vec` with `CALL db.create.setNodeVectorProperty(v, 'embedding_m3', $vec)` for space efficiency.

## Held for later — agent 2 (agentic patterns)

- `from_neo4j_crawl_reasoning_step` (high) — insert `:ReasoningStep` between `:ReasoningTrace` and `:ToolCall`. Adds `thought/action/observation` properties. Migrate 32K existing `:RETRIEVED` edges. Big schema change.
- `from_neo4j_crawl_touched_edge` (medium) — add `:TOUCHED` edges from `:ReasoningStep` to every concept/root/word the step examined (vs only what it formally retrieved). Improves wujuh/root-family audit queries.
- `from_neo4j_crawl_mcp_server` (medium) — wrap the 21 chat.py tools as a stdio MCP server so they can be used from Claude Desktop / Cursor / Codex. Reuse existing dispatcher; expose `get_qkg_schema`. Read-only by default.
- `from_neo4j_crawl_buffered_writes` (low) — replace per-tool synchronous writes in reasoning_memory.py with a buffered queue flushed at end-of-turn. Reduces 21x driver round trips per chat turn to 1-3.
- `from_neo4j_crawl_extractor_provenance` (low) — add `(:Extractor {name, version, config})` nodes for keyword extractor, Porter ER, Arabic-root extractor, embedding generator. Link via `:EXTRACTED_BY`.
- `from_neo4j_crawl_aura_text2cypher_fallback` (low) — stand up parallel Aura Agent on same DB with Text2Cypher + ~10 Cypher Templates. Wrap as 22nd tool `text2cypher_fallback`.
- `from_neo4j_crawl_neo4j_skills` (low) — install neo4j-contrib/neo4j-skills via `npx skills add` for progressive-disclosure SKILL.md docs.

## Held for later — agent 3 (Cypher + GDS + perf)

- `from_neo4j_crawl_003_profile_outlier_query` (P0) — replay slowest 5 captured `semantic_search` and `traverse_topic` queries with PROFILE; document operator tree + hot spots. (Requires slow-query log first.)
- `from_neo4j_crawl_004_parameterize_audit` (P1) — audit every Cypher in tools/* for f-string literals that should be `$`-parameters. Verify plan-cache reuse.
- `from_neo4j_crawl_006_swap_louvain_for_leiden` (P2) — Leiden is drop-in replacement for Louvain, fixes disconnected-community bug.
- `from_neo4j_crawl_007_fastrp_structural_embeddings` (P2) — 128-d FastRP on Verse-Concept-Lemma-Root projection as second vector index. A/B vs BGE-only on QRCD.
- `from_neo4j_crawl_008_hipporag_postmortem_v2` (P2) — re-run HippoRAG with narrowed projection, tf-idf-weighted edges, lower damping. Document A/B; if still negative, remove the code.
- `from_neo4j_crawl_010_node_similarity_for_related_to` (P3) — replace or augment 51K cosine-derived RELATED_TO with `gds.nodeSimilarity` (Jaccard on shared Concepts).

## How the loop should work through these

The recurring `/loop` chain ticks the highest-priority pending task in
`ralph_backlog.yaml`. As the top 8 above complete and earn `done_task_ids` entries,
the loop will start picking the next batch — at which point you (or a
`discover_new_followups` tick) can promote the held items above.

Research threads (the 22 we appended to `data/research_backlog.yaml`) are
consumed by the **research** half of the loop's alternation, not by impl ticks.

---

_See `INDEX.md` for the crawl summary, `01_*.md`/`02_*.md`/`03_*.md` for the full
agent reports with Cypher snippets, recommendations, and source URLs._
