---
type: decision
adr: 0026
status: accepted
date: 2026-05-12
tags: [decision, retrieval, tooling, agentic]
supersedes: none
---

# ADR-0026 — Tool descriptions are the primary routing signal; rewrite for LLM clarity

## Status
Accepted (2026-05-12). Active.

## Context
Cross-research synthesis (`data/research_synthesis_2026-05-12.md`, insight #4) identified that 4 independent sources (Neo4j MCP YT series, AI graph patterns, blog posts, eval results) all converge on the same finding: the quality of tool descriptions is the dominant factor in whether an LLM routes to the right tool. The original chat.py tool descriptions were short and described what each tool *does* without explaining *when* to use it versus not, or what output shape to expect. This caused observable routing failures in eval (wrong tool selected, redundant tool calls, semantic_search chosen over hybrid_search for mixed queries).

Commit `24b7784` rewrote all 20 tool descriptions in chat.py to include three structured sections: when-to-use, when-NOT-to-use, and output-shape. The synthesis result elevated this task from p70 to p80.

## Decision
Each tool description in chat.py must include:
1. **When to use:** the query patterns or intent signals that should trigger this tool.
2. **When NOT to use:** explicitly name the alternative tool and why it wins instead.
3. **Output shape:** what the caller receives (list of `{verseId, text, score, ...}` objects, a string, etc.).

This is a standing convention: any new tool added to chat.py must follow this format. Reviews of tool additions should check for all three sections.

## Consequences
- **Positive:** Reduces LLM routing errors. Gives the agentic loop a richer signal to distinguish overlapping tools (e.g. `search_keyword` vs `concept_search` vs `hybrid_search`). Reduces wasted tool calls within a single turn.
- **Positive:** Enables Haiku-level models to route correctly without Opus-level reasoning about what each tool does.
- **Negative:** Longer descriptions consume more context tokens per tool declaration (~200 tokens overhead per turn). Mitigated by the tool grouping decision (ADR-0027) which hides infrequently-used tools until needed.
- **Neutral:** Does not change any runtime behavior; purely a description-layer concern.

## Cross-references
- Source evidence: commit `24b7784` — `git show 24b7784`
- Related: [[0027-8-tool-startup-set-3-discoverable-bundles]], `repo://chat.py`, `data/research_synthesis_2026-05-12.md`
- Synthesis insight: from_neo4j_yt_mcp_tool_description_audit priority 70→80
