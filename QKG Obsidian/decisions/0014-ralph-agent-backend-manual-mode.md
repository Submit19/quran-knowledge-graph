---
type: decision
adr: 0014
status: accepted
date: 2026-05-12
tags: [decision, agentic, loop]
supersedes: none
---

# ADR-0014 — RALPH_AGENT_BACKEND=manual mode for execute_agent_creative

## Status
Accepted (2026-05-12). Active.

## Context
Tasks tagged `[opus]` or requiring extended multi-step reasoning were being routed to OpenRouter free-tier models, which produced shallow or vague deliverables. An alternative was to run these tasks in-session with Opus, but the cron-based orchestrator spawns fresh subagents that cannot interact with a persistent session. Commit `c638985` introduced a manual-mode escape hatch: when `RALPH_AGENT_BACKEND=manual` is set, `execute_agent_creative` skips the OpenRouter call, returns `DONE_WITH_CONCERNS`, and defers to the gate function. The operator (running Opus in a separate context) then produces the deliverable out-of-band and persists it to disk.

## Decision
Add `RALPH_AGENT_BACKEND=manual` mode to `ralph_loop.py`. When set, task executors (especially `execute_agent_creative`) skip remote model calls and return a sentinel status that tells the gate to validate a pre-produced deliverable file instead of auto-executing.

## Consequences
- **Positive:** Enables Opus-grade work on high-value tasks without coupling the orchestrator to a single session. Operator has full control over task execution quality.
- **Negative:** Manual mode requires out-of-band human intervention; cannot be fully automated.
- **Neutral:** Used alongside ADR-0015 (manual cypher_analysis) to handle tasks whose specs specify acceptance criteria but no query. Default is `RALPH_AGENT_BACKEND=openrouter` for unsupervised ticks.

## Cross-references
- Source evidence: commit `c638985` — `git show c638985` for full context
- Related: [[0013-cron-fresh-subagent-pattern]], [[0015-manual-cypher-analysis]], `repo://ralph_loop.py` (execute_agent_creative fn)
