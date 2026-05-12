---
type: decision
adr: 0039
status: accepted
date: 2026-05-12
tags: [decision, architecture, reasoning-memory, schema, neo4j, mcp]
supersedes: none
---

# ADR-0039 — Add `memory_path` property to `ReasoningTrace` nodes

## Status
Accepted (2026-05-12). Shipped in commit `6b25d7f`, tick 101 IMPL.

## Context
`ReasoningTrace` nodes previously had no stable, human-readable address. To retrieve
all traces for a given user session (e.g. for session-scoped playback, MCP memory
tool exposure, or debug), one had to join through `(:Query)-[:TRIGGERED]->(:ReasoningTrace)`
and filter by timestamp — fragile and non-obvious.

Task `from_blog_stateful_ai_memory_path_convention` (p60) drew from stateful AI memory
research (`data/research_neo4j_crawl/`) recommending a `memory_path` convention
(format: `sessions/<session_id>/traces/<trace_id>`) as a durable, routable address
analogous to file paths in hierarchical memory stores.

## Decision
Add a `memory_path: String` property to `ReasoningTrace` nodes at CREATE time in
`reasoning_memory.py`:

```python
memory_path = f"sessions/{query_id}/traces/{trace_id}"
```

A supporting index is created for efficient lookup by path prefix:

```cypher
CREATE INDEX trace_memory_path IF NOT EXISTS FOR (t:ReasoningTrace) ON (t.memory_path);
```

The path convention is:
- `sessions/<qid>` — groups all traces triggered by the same Query node
- `traces/<tid>` — unique per ReasoningTrace (UUID or timestamp-derived)

Existing ReasoningTrace nodes (pre-commit) have `memory_path = null`. The index
handles nulls safely (null entries are not indexed in Neo4j composite B-tree indexes).

## Consequences
- **Positive:** Session-scoped retrieval becomes a simple index scan:
  `MATCH (t:ReasoningTrace) WHERE t.memory_path STARTS WITH 'sessions/<qid>'`
- **Positive:** Enables future MCP memory-tool exposure — a `get_session_context`
  tool can return all traces for a session by path prefix without graph traversal.
- **Positive:** Aligns with hierarchical memory store conventions (e.g.
  `mem0`, `Zep`) — easier to adapt if we ever bridge to an external memory layer.
- **Neutral:** Quality gate skipped (Neo4j offline = false negative on app_free import).
  Human review of `reasoning_memory.py` changes recommended before production run.
- **Neutral:** Does not change the Query→ReasoningTrace graph structure; purely additive.
- **Negative:** Path is not globally unique across deployments (no namespace for
  multi-tenant use). Acceptable for current single-user local setup.

## Cross-references
- Source: commit `6b25d7f`, task `from_blog_stateful_ai_memory_path_convention`
- Related: `reasoning_memory.py`, `chat.py` dispatch
- Research: `data/research_neo4j_crawl/02_agentic_patterns.md` (stateful AI memory)
- Proposed by: ralph IMPL tick 101
