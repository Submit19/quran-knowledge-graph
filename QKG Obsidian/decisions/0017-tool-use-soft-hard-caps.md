---
type: decision
adr: 0017
status: accepted
date: 2026-05-12
tags: [decision, loop, observability]
supersedes: none
---

# ADR-0017 — Tool-use soft/hard caps (35/50)

## Status
Accepted (2026-05-12). Active.

## Context
Early ticks exhibited failure-retry loops: a subagent would call a tool 50+ times in a single attempt, hitting the hard limit and then failing. Analysis showed these were not productive exploration but NEEDS_CONTEXT spirals — the tool-use loop was retrying the same search with minor variations. A soft cap (35 calls, nudges the model to break out) and hard cap (50 calls, abort) were introduced in commit `a6bdcf6`. This prevents looping while leaving headroom for legitimately complex tasks like `router_agent` (took 31 calls) and some `agent_creative` tasks (up to 35+).

## Decision
Implement dual tool-use limits: soft cap at 35 calls (subagent should wrap up), hard cap at 50 calls (executor aborts). Soft cap is a heuristic hint; hard cap is a fence. Initial values set per `a6bdcf6`; tuned to 35/50 in `cfe2336`.

## Consequences
- **Positive:** Prevents spiral failures from being silent cost drains. Subagent receives a clear signal to change strategy rather than retrying the same tool. Hard cap prevents runaway sessions.
- **Negative:** Legitimately deep tasks might need >35 calls; the soft cap is just a nudge (not a fatal limit).
- **Neutral:** Caps are applied per task executor, not globally. Can be tuned per environment variable (e.g., `TOOL_USE_SOFT_CAP=40`).

## Cross-references
- Source evidence: commit `a6bdcf6` (initial 30/40); commit `cfe2336` (tuned to 35/50) — `git show a6bdcf6` and `git show cfe2336` for context
- Related: [[0013-cron-fresh-subagent-pattern]], `repo://ralph_loop.py` (tool-use limit enforcement)
