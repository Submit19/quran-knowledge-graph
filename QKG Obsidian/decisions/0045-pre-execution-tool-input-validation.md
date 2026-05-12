---
type: decision
adr: 0045
status: accepted
date: 2026-05-13
tags: [decision, agentic, tool-schema, input-validation, robustness]
supersedes: none
---

# ADR-0045 — Pre-execution input validation in chat.py tool handlers

## Status
Accepted (2026-05-13). Implemented in commit `0b2a823`, tick 119 IMPL.

## Context
Chat.py tools were silently failing or producing misleading Neo4j errors when
the agent passed out-of-range values (e.g. surah 0, verse 999, invalid language
string). The Neo4j driver would either return empty results or raise a raw
driver exception that the agent loop misinterpreted. This caused retry spirals
where the model would call the same broken tool 3+ times.

The `from_blog_tool_input_validation` task (sourced from research:blog_neo4j:agent-tools)
proposed adding guards before any Cypher fires, returning a structured
`{error, reason}` response so the agent can self-correct in a single turn.

## Decision
Add lightweight `_validate_*` helpers in `chat.py` that are called at the top
of each affected tool handler — before any Neo4j query — and return a structured
`{error: True, reason: "..."}` dict on invalid input:

- `_validate_surah_number(n)` — rejects values outside 1–114
- `_validate_verse_id(vid)` — rejects malformed `"surah:verse"` strings
- `_validate_language(lang)` — rejects values outside `{"en", "ar"}`

Tools guarded: `get_verse`, `find_path`, `explore_surah`, `query_typed_edges`,
`get_verse_words` (5 of 21 tools — those most prone to LLM hallucinated values).

## Consequences
- **Positive:** Agent receives a clear error message and can self-correct without
  a Cypher round-trip; eliminates the silent-empty-result failure mode.
- **Positive:** Structured `{error, reason}` is consistent with the earlier
  `from_ai_graph_tool_error_audit` pattern (ADR-0038), completing the defence-in-
  depth: pre-execution validation + post-execution structured error returns.
- **Neutral:** Adds ~30 LOC of guard helpers; negligible overhead.
- **Negative:** Quality gate flagged DONE_WITH_CONCERNS because Neo4j was offline
  during the tick (false negative on acceptance check). Validation logic is
  correct but untested against live DB in this tick.

## Cross-references
- Source: commit `0b2a823`, task `from_blog_tool_input_validation`
- Related: ADR-0038 (structured tool error returns, post-execution)
- Proposed by: research tick, blog_neo4j:agent-tools
