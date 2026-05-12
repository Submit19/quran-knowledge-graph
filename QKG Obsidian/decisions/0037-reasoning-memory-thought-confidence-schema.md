---
type: decision
adr: 0037
status: accepted
date: 2026-05-12
tags: [decision, architecture, reasoning-memory, schema, neo4j]
supersedes: none
---

# ADR-0037 — Extend reasoning memory with `thought` + `confidence` on ToolCall / ReasoningStep nodes

## Status
Accepted (2026-05-12). Spec shipped in commit `ae4659c`, tick 91 IMPL.

## Context
`ToolCall` nodes in the reasoning memory subgraph captured *what* the agent did
(`tool_name`, `args_json`, `summary`, `ok`, `duration_ms`) but not *why it chose
this tool* or *how confident the reasoning was*. The Neo4j Context Graph
decision-trace pattern (source: `data/research_neo4j_crawl/02_agentic_patterns.md`)
recommends storing a `thought` rationale and a `confidence` scalar alongside each
tool call to enable auditability, self-improvement loops, and pattern mining.

Task `from_blog_extend_reasoning_memory_confidence` (p78) produced spec
`data/ralph_agent_from_blog_extend_reasoning_memory_confidence.md`.

## Decision
Add two optional properties to both `ToolCall` and `ReasoningStep` nodes:

- `thought: String` — agent's pre-call rationale (<=500 chars). NULL if not supplied.
- `confidence: Float` — 0.0..1.0. NULL if not supplied.

Changes are additive (no migration needed — `SET` on a non-existent property is a
no-op in Neo4j; existing 32K+ ToolCall nodes simply have `null` values).

A supporting index is created:

```cypher
CREATE INDEX toolcall_confidence IF NOT EXISTS FOR (tc:ToolCall) ON (tc.confidence);
```

Callers that consume these fields must use `coalesce(tc.confidence, 1.0)` or
`WHERE tc.thought IS NOT NULL` to be safe against pre-existing null nodes.

## Consequences
- **Positive:** Full auditability — replay exactly what the model was "thinking" when
  it chose `hybrid_search` over `semantic_search`.
- **Positive:** Self-improvement signal — find ToolCall nodes where `confidence < 0.4`
  and citation yield was zero; these are prime prompt-tuning targets.
- **Positive:** Pattern mining — cluster by `thought` embedding to discover recurring
  reasoning strategies across queries.
- **Negative:** Requires `reasoning_memory.py` changes to accept and store `thought` +
  `confidence` kwargs in every call site. DONE_WITH_CONCERNS flag — human review
  before wiring is required.
- **Neutral:** Schema is additive; zero downtime, no reindex required.

## Cross-references
- Source: commit `ae4659c`, deliverable `data/ralph_agent_from_blog_extend_reasoning_memory_confidence.md`
- Related: `reasoning_memory.py`, `chat.py` dispatch, `data/research_neo4j_crawl/02_agentic_patterns.md`
- Proposed by: ralph IMPL tick 91
