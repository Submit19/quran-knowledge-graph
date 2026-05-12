---
type: decision
adr: 0035
status: accepted
date: 2026-05-12
tags: [decision, agentic, neo4j, architecture, tool-routing]
supersedes: none
---

# ADR-0035 — Graph-backed tool registry: ToolRegistry nodes, usage_count, dynamic startup set

## Status
Accepted (2026-05-12). Spec shipped in commit `d162be7`, tick 89 IMPL.

## Context
Task `from_neo4j_yt_mcp_graph_backed_registry` (p65) designed a runtime tool registry
backed by Neo4j rather than a static in-memory list.

With 21+ tools in `chat.py`, the startup tool set (sent in every system prompt) grows
with each addition. ADR-0027 already addressed this with a static 8-tool startup set and
3 discoverable bundles. The graph-backed registry extends that pattern: tool selection
becomes data-driven (Neo4j query) rather than hard-coded, and usage signal accumulates
automatically in the graph for future re-ranking.

## Decision
Design spec (`data/ralph_agent_from_neo4j_yt_mcp_graph_backed_registry.md`) specifies:

1. **`(:ToolRegistry)` nodes** — one per tool, carrying `name`, `description_hash`,
   `category`, `startup_weight` (0/1 flag), and `usage_count` (integer).
2. **Usage seeder** — an init script populates ToolRegistry nodes from `TOOLS` list in
   `chat.py`; a post-call hook increments `usage_count` for each dispatched tool.
3. **Auto-increment hook** — after every tool dispatch in the agentic loop, a lightweight
   Cypher `MATCH (t:ToolRegistry {name:$name}) SET t.usage_count = t.usage_count + 1`
   runs asynchronously to avoid blocking latency.
4. **Dynamic startup-set query** — at agent startup, query the top-N tools by
   `startup_weight DESC, usage_count DESC` rather than reading from a static list.
5. **Drift detector** — a nightly check compares `TOOLS` in `chat.py` against
   `(:ToolRegistry)` nodes; alerts on additions/deletions not yet reflected in the graph.

The spec is marked DONE_WITH_CONCERNS — review required before implementation, because
the async increment pattern introduces a write on every tool call and may need batching
if throughput increases.

## Consequences
- **Positive:** Tool startup set becomes self-tuning — frequently-used tools rise to top,
  rarely-used ones drop out of the default prompt without manual curation.
- **Positive:** Usage signal is durable in Neo4j (survives restarts), enabling long-term
  analysis of tool utilization.
- **Positive:** Drift detector prevents silent mismatches between code and graph state.
- **Negative:** Every tool call now involves a Neo4j write (async); at scale this is
  a background write pressure source. Mitigate with batched flush or debounce.
- **Negative:** Spec-only at tick 89 — requires a follow-up IMPL tick to wire into
  `chat.py` and the agent startup sequence. Risk: operator forgets to review the
  DONE_WITH_CONCERNS flag.
- **Neutral:** Dynamic startup-set query adds ~1ms latency at agent init (negligible).

## Cross-references
- Source: commit `d162be7`, deliverable `data/ralph_agent_from_neo4j_yt_mcp_graph_backed_registry.md`
- Extends: ADR-0027 (8-tool startup set + 3 discoverable bundles)
- Proposed by: ralph IMPL tick 89
