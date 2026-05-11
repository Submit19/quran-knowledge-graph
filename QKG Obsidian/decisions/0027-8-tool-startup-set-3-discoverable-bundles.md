---
type: decision
adr: 0027
status: accepted
date: 2026-05-12
tags: [decision, tooling, agentic, context]
supersedes: none
---

# ADR-0027 — 8-tool startup set with 3 discoverable category bundles

## Status
Accepted (2026-05-12). Active.

## Context
The agentic loop currently declares all 21 chat.py tools upfront to the LLM in every turn. With the new verbose tool descriptions (ADR-0026), this costs ~2,400 additional context tokens per turn. As tick count grows and the tool count rises (new tools planned for adaptive routing, HyDE spike, betweenness rerank), this overhead compounds.

Task `from_neo4j_yt_mcp_balanced_tool_grouping` (commit `df62790`) produced a design doc (`data/ralph_agent_from_neo4j_yt_mcp_balanced_tool_grouping.md`) specifying:
- **Startup set (8 tools):** the tools used in ≥80% of turns — `search_keyword`, `semantic_search`, `hybrid_search`, `get_verse`, `explore_surah`, `search_arabic_root`, `run_cypher`, `recall_similar_query`.
- **3 discoverable bundles:** Etymology (6 tools), Deep Analysis (3 tools), Code-19 (2 tools). Each bundle is surfaced as a single meta-tool that expands on first use.
- **Decision gate before implementation:** measure actual per-tool usage distribution across eval_v1 (18 questions) before hardcoding the split.

The design includes a risk register: if the LLM fails to invoke a bundle expansion for niche queries, coverage drops. Mitigation: system prompt explicitly tells the model about bundles and when to expand them.

## Decision
Adopt the 8+3-bundle architecture. The startup set and bundle membership should be validated against actual eval_v1 tool-call data before shipping to production. Implementation is gated on `rerun_eval_against_current` (p95) completing so we have real per-tool frequency data.

## Consequences
- **Positive:** ~2,400 tokens/turn savings once implemented. Enables verbose descriptions (ADR-0026) without net context growth.
- **Positive:** Scales gracefully as new tools are added — add to an existing bundle rather than inflating the startup set.
- **Negative:** Adds complexity to the tool dispatch layer (bundle expansion logic). One extra round-trip per bundle first-use.
- **Negative:** Risk of the LLM not expanding a bundle when needed (e.g. Arabic morphology query never triggering Etymology bundle). Needs A/B eval before full rollout.
- **Neutral:** Blocked on eval data; implementation deferred until `rerun_eval_against_current` completes.

## Cross-references
- Source evidence: commit `df62790`, deliverable `data/ralph_agent_from_neo4j_yt_mcp_balanced_tool_grouping.md`
- Related: [[0026-tool-descriptions-as-primary-routing-signal]], `repo://chat.py`, `repo://app_free.py`
- Blocked by: `rerun_eval_against_current` (p95 in ralph_backlog.yaml)
