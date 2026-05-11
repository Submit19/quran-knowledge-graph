---
type: decision
adr: 0029
status: proposed
date: 2026-05-12
tags: [decision, agentic, reflexion, self-improvement, memory]
supersedes: none
---

# ADR-0029 — Reflexion pattern for weak-query cluster improvement

## Status
Proposed (2026-05-12). Pending implementation review.

## Context
The eval harness surfaces a "weak-question cluster" (e.g., repeated meditation/reverence queries about Surah 55) where the agent repeatedly chooses sub-optimal tool sequences, producing low cite counts (~13 vs target >27). The Reflexion pattern (Shinn et al. 2023) addresses this by having the agent generate a one-sentence post-turn self-critique memo, store it persistently, and inject relevant past memos into the planner context at the start of future similar queries.

Task `from_ai_graph_reflexion_pattern` (commit `2cf2398`) produced a design doc (`data/ralph_agent_from_ai_graph_reflexion_pattern.md`) specifying:
- End-of-turn hook: `_run_reflexion(turn_dict)` calls the LLM with a one-sentence critique prompt.
- Persistence: `data/reflexion_memos.jsonl` (JSONL, one entry per turn, with query embedding, memo, and timestamp).
- Recall: cosine similarity search at planner context build time, top-3 memos injected.
- New Neo4j nodes proposed: `(:ReflexionMemo)` with `HAS_MEMO` edge from `ReasoningTrace` for graph-level persistence (alternative to JSONL).

## Decision
Adopt the Reflexion pattern for the weak-query cluster, starting with JSONL persistence (simpler, no schema change). Evaluate whether the Neo4j `(:ReflexionMemo)` graph node adds value after the JSONL baseline is measured. Gate full rollout on eval showing ≥2× cite improvement on the weak-question cluster.

## Consequences
- **Positive:** Self-improving agent loop — each answered question makes similar future queries better.
- **Positive:** Recall is zero-cost at query time (local cosine search on JSONL); no extra Neo4j call.
- **Positive:** Memos are interpretable and auditable (plain text in JSONL).
- **Negative:** End-of-turn LLM call adds latency (~500ms) to every response. Can be made async/background.
- **Negative:** Memo quality depends on LLM self-critique capability; may need prompt tuning.
- **Negative:** JSONL grows unbounded; needs periodic pruning or similarity-based deduplication.
- **Neutral:** Neo4j graph persistence (`(:ReflexionMemo)`) deferred to follow-up — JSONL baseline first.

## Cross-references
- Source evidence: commit `2cf2398`, deliverable `data/ralph_agent_from_ai_graph_reflexion_pattern.md`
- Related: [[0012-5-tier-memory-stack]], `repo://chat.py`, `repo://reasoning_memory.py`
- Research basis: Shinn et al. 2023 "Reflexion: Language Agents with Verbal Reinforcement Learning"
