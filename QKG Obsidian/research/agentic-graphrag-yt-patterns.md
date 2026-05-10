---
type: research
status: done
priority: 78
tags: [research/retrieval, research/agentic-patterns, research/neo4j-yt]
source: data/research_neo4j_crawl/06a_yt_agentic_graphrag.md
date_added: 2026-05-10
---

# Agentic GraphRAG / Multi-Hop Reasoning (Neo4j YT — NODES AI 2026)

## TL;DR
- All four NODES AI 2026 talks independently converge on the same pattern: vector seed → graph expand. QKG's `hybrid_search → traverse_topic` chain is already on-pattern.
- A lightweight query-complexity router (abstract/structured classifier) directly addresses QKG's abstract-concept weakness (meditation/reverence/Surah 55 cluster). Route abstract queries to `concept_search` first, then traversal; not directly to dense retrieval.
- An in-loop three-way evaluator (sufficient / hop-more / replan) replaces our flat 15-turn cap and cuts wasted turns on hard queries that need replanning, not more of the same tool.
- Zero-hit fallback: if RRF top-1 score < 0.2, fire `concept_search` as a second attempt rather than returning sparse results.
- In-context scratch-pad (explicit running plan in assistant context, not just in `reasoning_memory.py`) improves multi-turn coherence.

## Key findings
- **Router agent pattern** (EventKernel video): lightweight complexity classifier routes to (a) traversal agent or (b) NL2Cypher agent. For QKG: abstract noun (no verse ref, no root) → `concept_search` first → `traverse_topic`; structured query → `run_cypher`.
- **Bridge node naming**: explicitly naming `:Verse` as the bridge between embedding space and `:ArabicRoot`/`:Concept` structured space in the system prompt helps the agent reason across the two layers.
- **NL→Cypher zero-shot**: schema + 3-5 few-shot Cypher examples in system prompt is "all we needed" (INRAE agriculture corpus, 400K nodes / 1M edges). QKG's `run_cypher` already exists; surfacing the schema card more explicitly would help.
- **Negative query failure mode**: pure agentic RAG "completely struggles with negative queries"; KG-backed agent handles them via Cypher. Documents a QKG limitation for count/rank/negation questions.
- **GraphReader three-way evaluator**: after each hop, LLM-as-judge decides: (1) sufficient → answer, (2) hop-more → expand neighbors, (3) deep-dive → replan. `deep_dive` re-triggers `initial_discovery` enabling full replanning without exceeding a turn cap.
- **LangGraph state model** (GraphReader): `{user_query, rewritten_query, current_facts, notebook, traversal_count, traversal_limit}`. Closer to a structured state machine than our implicit reasoning via tool-call cache + `reasoning_memory.py`.

## Action verdict
- ✅ Adopt — add routing heuristic: if query is abstract (no verse ref, no root), call `concept_search` FIRST, then `traverse_topic`.
  **Promoted as:** `from_neo4j_yt_router_agent` (high)
- 🔬 Research deeper — three-way in-loop evaluator (sufficient / hop-more / replan). Cost: 1 extra LLM call per hop. Target: cut 13–27 cite gap on abstract queries.
  **Promoted as:** `from_neo4j_yt_sufficiency_gate` (medium)
- 🔬 Research deeper — serial fallback cascade for zero-hit queries (if RRF top-1 < 0.2, retry with `concept_search`).
  **Promoted as:** `from_neo4j_yt_tiered_cascade` (low)

## Cross-references
- [[agentic-patterns-neo4j]] — reasoning memory schema (traces, steps, playbook recall)
- [[cypher-perf-gds]] — NL→Cypher and `run_cypher` performance
- [[eval-qrcd-report]] — QRCD gaps that the router + evaluator should address
- Source: `repo://data/research_neo4j_crawl/06a_yt_agentic_graphrag.md`
