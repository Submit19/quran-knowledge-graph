---
type: research
status: done
priority: 70
tags: [research/agent-memory, research/neo4j-yt, research/schema]
source: data/research_neo4j_crawl/06b_yt_agent_memory.md
date_added: 2026-05-10
---

# Neo4j Agent Memory Patterns (YT — 4 NODES AI 2026 Videos)

## TL;DR
- Three memory tiers are the 2026 consensus: short-term (session), episodic (entity KG), procedural (playbooks). QKG's `reasoning_memory.py` covers the episodic tier partially but lacks entity extraction from query text and has no procedural tier.
- Bitemporal model — `valid_from / valid_until` (world time) + `created_at / invalidated_at` (system time) as edge properties — is the consensus for temporal facts. Our `RETRIEVED` edges have no timestamps.
- Quintuple extraction (subject, predicate, object, timestamp, free-text description) replaces naive triples. Our `ToolCall` stores tool name + params but no free-text description of what was inferred.
- A consolidation "sleep step" (nightly batch) merges redundant entity nodes, clusters similar queries, and compresses descriptions. QKG has no consolidation; traces only accumulate.
- Separating raw trace logs from curated memory graph is a best practice we violate — `ReasoningTrace` serves both roles.

## Key findings
- **`RETRIEVED` needs temporal stamps**: add `valid_from` (ISO timestamp) and `model_version` string to every new RETRIEVED edge. Enables queries like "which verses were ranked highly under legacy MiniLM but not under BGE-M3?"
- **`(:Session)` node missing**: all queries in the same HTTP session (or 30-min window) should be grouped under `(:Session)-[:CONTAINS]->(:Query)`. Enables multi-turn conversation analysis and Groundhog Day detection (same question repeated across sessions).
- **Procedural memory**: high-confidence `ReasoningTrace` nodes (≥5 RETRIEVED edges, ≥3 distinct verses, no citation FAIL) should be promoted to `(:Procedure)-[:HAS_STEP]->(:Step)`. `tool_recall_similar_query` should prefer these over raw traces.
- **Reflection loop**: `tool_recall_similar_query` only retrieves past answers; there is no step where the agent evaluates if a retrieved playbook was actually useful and updates its retrieval weight.
- **Three failure modes** (Agentic Personas talk): Groundhog Day (repeated questions), Lost Escalation (yesterday's critical event missing today), Stale Assumption (old goal optimized after direction change). All three apply to QKG across sessions.
- **User-as-entity** (Temporal KG talk): linking `Query` nodes to a `(:User)` or `(:Session)` enables cross-session inference and multi-user analytics.

## Action verdict
- ✅ Adopt — add `valid_from` + `model_version` to all new RETRIEVED edges; backfill existing with sentinel values.
  **Promoted as:** `from_neo4j_yt_memory_01_bitemporal_retrieved` (high)
- ✅ Adopt — introduce `(:Session)` node grouping, linked to `(:Query)` via `[:CONTAINS]`.
  **Promoted as:** `from_neo4j_yt_memory_02_session_node` (medium)
- 🔬 Research deeper — write `consolidate_traces.py` nightly batch: cluster queries at cosine > 0.96, create `(:QueryCluster)` nodes.
  **Promoted as:** `from_neo4j_yt_memory_03_consolidation_job` (medium)
- 🔬 Research deeper — promote qualifying traces to `(:Procedure)` first-class nodes.
  **Promoted as:** `from_neo4j_yt_memory_04_procedural_nodes` (low)
- ✅ Adopt — insert `(:ReasoningStep)` between `ReasoningTrace` and `ToolCall` (also flagged in [[agentic-patterns-neo4j]]).
  **Promoted as:** `from_neo4j_yt_memory_05_reasoning_step_node` (medium)

## Cross-references
- [[agentic-patterns-neo4j]] — canonical agent-memory schema (neo4j-labs library)
- [[agentic-graphrag-yt-patterns]] — query routing and loop architecture (different video series)
- Source: `repo://data/research_neo4j_crawl/06b_yt_agent_memory.md`
