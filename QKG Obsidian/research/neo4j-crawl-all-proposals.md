---
type: research
status: done
priority: 55
tags: [research/backlog, research/neo4j]
source: data/research_neo4j_crawl/all_proposals.md
date_added: 2026-05-10
---

# All 25 Neo4j Crawl Proposals — Backlog Index

## TL;DR
- 8 highest-priority tasks promoted to `ralph_backlog.yaml` on 2026-05-10.
- 17 additional tasks held for later — promoted when the top 8 complete.
- This note is an index/triage document, not a research finding. Use it to understand backlog structure and find which crawl agent produced each task.

## Promoted to `ralph_backlog.yaml` (top 8)

| ID | Priority | Agent source |
|----|----------|-------------|
| `from_neo4j_crawl_enable_slow_query_log` | 90 | [[cypher-perf-gds]] |
| `from_neo4j_crawl_audit_indexes` | 88 | [[cypher-perf-gds]] |
| `from_neo4j_crawl_check_neo4j_version` | 85 | [[vector-graphrag-neo4j-docs]] |
| `from_neo4j_crawl_trace_vector_index` | 82 | [[agentic-patterns-neo4j]] |
| `from_neo4j_crawl_adopt_graphrag_retrievers` | 80 | [[vector-graphrag-neo4j-docs]] |
| `from_neo4j_crawl_single_shot_vector_traversal` | 78 | [[cypher-perf-gds]] |
| `from_neo4j_crawl_arabic_fulltext_index` | 75 | [[cypher-perf-gds]] |
| `from_neo4j_crawl_pagination_cursors` | 72 | [[agentic-patterns-neo4j]] |

## Held for later (agent 1 — vector + GraphRAG)
- `from_neo4j_crawl_filtered_vector_tool` (70)
- `from_neo4j_crawl_hybridcypher_one_shot` (65)
- `from_neo4j_crawl_overfetch_knob` (55)
- `from_neo4j_crawl_use_setNodeVectorProperty` (50)

## Held for later (agent 2 — agentic patterns)
- `from_neo4j_crawl_reasoning_step` (high)
- `from_neo4j_crawl_touched_edge` (medium)
- `from_neo4j_crawl_mcp_server` (medium)
- `from_neo4j_crawl_buffered_writes` (low)
- `from_neo4j_crawl_extractor_provenance` (low)
- `from_neo4j_crawl_aura_text2cypher_fallback` (low)
- `from_neo4j_crawl_neo4j_skills` (low)

## Held for later (agent 3 — Cypher + GDS + perf)
- `from_neo4j_crawl_003_profile_outlier_query` (P0)
- `from_neo4j_crawl_004_parameterize_audit` (P1)
- `from_neo4j_crawl_006_swap_louvain_for_leiden` (P2)
- `from_neo4j_crawl_007_fastrp_structural_embeddings` (P2)
- `from_neo4j_crawl_008_hipporag_postmortem_v2` (P2)
- `from_neo4j_crawl_010_node_similarity_for_related_to` (P3)

## Action verdict
- ✅ Adopt — this note exists as a lookup reference; no action needed here.
- Source index: `repo://data/research_neo4j_crawl/INDEX.md`

## Cross-references
- [[vector-graphrag-neo4j-docs]] · [[agentic-patterns-neo4j]] · [[cypher-perf-gds]] · [[ai-graph-ecosystem-extracts]]
- Source: `repo://data/research_neo4j_crawl/all_proposals.md`
