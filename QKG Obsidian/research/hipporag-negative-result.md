---
type: research
status: done
priority: 75
tags: [research/retrieval, research/gds, research/benchmarks, research/negative-result]
source: HIPPORAG_REPORT.md
date_added: 2026-05-10
---

# HippoRAG PPR Traversal — Negative Result

## TL;DR
- HippoRAG-style Personalized PageRank underperforms vanilla BGE-M3 retrieval on QRCD by every metric except hit@20. Not a bug — the GraphRAG-Bench paper predicts this outcome for single-hop fact retrieval benchmarks.
- Root cause 1: QRCD is direct-lookup style (not multi-hop). PPR's strength is multi-hop reasoning; mixing in graph neighbors and past-query seeds dilutes strong direct-semantic signal.
- Root cause 2: past-query seeds are noise for Arabic QRCD because `reasoning_memory.py` uses MiniLM-384d (English-only) for query embeddings — Arabic QRCD questions land in random embedding space positions.
- PPR infrastructure works correctly (smoke test on "patience" produced excellent results). This is a mismatch with QRCD query style, not an implementation bug.

## Key findings
- **QRCD results**: HippoRAG hit@5 = 0.3182 vs vector-only 0.5455 (−0.23). MRR = 0.2332 vs 0.4583 (−0.23). Only hit@20 tied (0.6364 both).
- **GraphRAG-Bench prediction**: Basic RAG wins single-hop fact retrieval (83.21% Evidence Recall vs HippoRAG2 70.29%). HippoRAG wins multi-hop reasoning (87.91% ER vs RAG 64.47%). QKG's QRCD questions are short-query single-hop — the paper directly predicts our negative result.
- **Cost-quality Pareto**: HippoRAG2 ~1K tokens/query, MS-GraphRAG ~331K (global mode), LightRAG ~100K. HippoRAG2 is the Pareto winner for multi-hop use cases.
- **Re-embed fix**: re-embedding all `:Query` nodes with BGE-M3 (multilingual) and using BGE-M3 for past-query lookup would fix the multilingual embedding-space mixing bug. Then PPR's second component (past-query seeds) would have meaningful signal for Arabic queries.
- **PPR should help when**: queries are multi-hop ("Compare X and Y"), reasoning graph has many similar past queries, both past-Q and current-Q embeddings are in the same model space.
- **HippoRAG-2 tuning hints** (from deep-dive): `passage_node_weight` default 0.05 needs tuning to 0.3–0.5 for short-context retrieval. Narrower projection (Verse + Concept + Lemma only, not all 200K edges) + tf-idf-weighted edges + damping 0.5 (not 0.85) would be the clean re-run.

## Action verdict
- ❌ Skip — do not wire `tool_hipporag_traverse` into `chat.py` now. Infrastructure ready; conditions not met.
- 🔬 Research deeper — build a multi-hop Quran benchmark (compare / contrast / thematic questions) to test PPR where it should win.
  Mentioned in `RESEARCH_2026-04-28_DEEP.md` as task G1.
- 🔬 Research deeper — re-run PPR with: narrowed projection, tf-idf-weighted edges, damping 0.5, query-relevance-weighted source nodes, `passage_node_weight` = 0.3–0.5.
  **Promoted as:** `from_neo4j_crawl_008_hipporag_postmortem_v2` (P2)
- 🔬 Research deeper — re-embed `:Query` nodes with BGE-M3 so multilingual past-query seeds work for Arabic.

## Cross-references
- [[eval-qrcd-report]] — QRCD numbers; same benchmark used here
- [[cypher-perf-gds]] — GDS PageRank API details, projection tuning
- [[research-2026-04-28-deep-dive]] — deeper HippoRAG failure analysis and alternative seeds
- Source: `repo://HIPPORAG_REPORT.md`
