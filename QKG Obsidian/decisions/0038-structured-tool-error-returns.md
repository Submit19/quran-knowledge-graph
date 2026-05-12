---
type: decision
adr: 0038
status: accepted
date: 2026-05-12
tags: [decision, architecture, agentic, tools, error-handling]
supersedes: none
---

# ADR-0038 — Structured `{error: ...}` returns for all 21 chat.py tools

## Status
Accepted (2026-05-12). Shipped in commit `c57f455`, tick 99 IMPL.

## Context
An audit of all 21 agentic tools in `chat.py` (`from_ai_graph_tool_error_audit`, p80)
revealed that 7 tools were returning `None`, empty strings, or bare exception strings
on failure. The AI Graph research source documented this as the "tool failures ignored"
anti-pattern: the agent model sees an empty result and may silently skip the tool or
hallucinate a follow-up, with no structured signal to retry or re-route.

The audit identified two failure modes:
1. **`found: False` paths** — tools that reached a "not found" branch returned `None`
   or an empty dict instead of `{"error": "not found", "detail": ...}`.
2. **Missing try/except** — tools that queried Neo4j with no exception guard; any
   driver error (e.g. offline) propagated as an unhandled Python exception, crashing
   the tool call entirely.

## Decision
All 21 tools in `chat.py` must return a dict or JSON-serialisable object. On failure,
the return value must include at minimum `{"error": "<short reason>"}`. Seven tools
were updated in this commit:

- `lookup_word` — `found: False` path now returns `{"error": "word not found", "form": form}`
- `explore_root_family` — `found: False` path now returns `{"error": "root not found", "root": root}`
- `get_verse_words` — `found: False` path now returns `{"error": "verse not found", "verseId": vid}`
- `search_semantic_field` — `found: False` path now returns `{"error": "domain not found", "domain": domain}`
- `semantic_search` — wrapped in try/except, returns `{"error": str(e)}` on Neo4j failure
- `hybrid_search` — wrapped in try/except, returns `{"error": str(e)}` on Neo4j failure
- `lookup_wujuh` — wrapped in try/except, returns `{"error": str(e)}` on Neo4j failure

The remaining 14 tools were already returning structured dicts or raising in a
way the dispatch layer handled.

## Consequences
- **Positive:** The model receives a structured error object it can parse and act on
  (e.g. fallback to `search_keyword` when `lookup_word` returns `{error: word not found}`).
- **Positive:** Monitoring — `ToolCall.ok = false` nodes in reasoning memory can now
  always be correlated with a `summary` field that contains the error type.
- **Positive:** Quality gate can check for `"error"` keys in tool outputs and flag
  high-error ticks for inspection.
- **Neutral:** Quality gate skipped (Neo4j offline at time of commit = false negative
  on app_free import). Human review of the 7 patched functions is recommended before
  a production run.
- **Negative:** None identified. Change is additive and backward-compatible.

## Cross-references
- Source: commit `c57f455`, task `from_ai_graph_tool_error_audit`
- Related: `chat.py` (all 21 tools), `reasoning_memory.py` (ToolCall.ok field)
- Research: `data/research_neo4j_crawl/04_ai_graph.md` (tool failures ignored pattern)
- Proposed by: ralph IMPL tick 99
