---
type: decision
adr: 0042
status: accepted
date: 2026-05-13
tags: [decision, cypher, tool-description, few-shot, hallucination]
supersedes: none
---

# ADR-0042 — QKG-specific few-shot Cypher examples in run_cypher tool description

## Status
Accepted (2026-05-13). Shipped in commit `d31eac2`, tick 109 IMPL.

## Context
The `run_cypher` tool was being called with hallucinated property names (e.g.
wrong node labels, non-existent relationship types). The tool description was
generic, providing no schema anchors. The agentic loop had no in-context
examples of correct QKG Cypher patterns to draw from.

Benchmark and production logs showed the agent frequently queried for properties
that do not exist (`verse.id` instead of `verse.verseId`, etc.) or used wrong
relationship names.

## Decision
Add 8 QKG-specific few-shot Cypher examples directly to the `run_cypher` tool
description in `chat.py`. Examples cover:

1. Verse lookup by verseId
2. Keyword count query
3. ArabicRoot traversal via MENTIONS_ROOT
4. RELATED_TO neighbor fetch
5. SemanticDomain grouping
6. MorphPattern filtering
7. Keyword co-occurrence
8. Aggregate analytics

Each example includes the exact node labels, property names, and relationship
types used in the live QKG schema — acting as an inline schema reference.

## Consequences
- **Positive:** Eliminates the most common class of hallucinated-property errors
  in run_cypher calls.
- **Positive:** Reduces retries and NEEDS_CONTEXT failures for cypher_analysis
  tasks.
- **Positive:** Zero runtime cost — pure prompt-time fix.
- **Neutral:** Tool description grows by ~600 tokens. Accepted tradeoff given
  error-reduction benefit (ADR-0017 soft cap: 35 tool calls/tick).
- **Negative:** Examples must be kept in sync if schema evolves. Stale examples
  could re-introduce the hallucination problem.

## Cross-references
- Source: commit `d31eac2`, task `from_graphacademy_cypher_fewshots`
- Files: `chat.py` (run_cypher tool description)
- Related: ADR-0026 (tool descriptions as primary routing signal)
- Proposed by: research tick 82, graphacademy source
