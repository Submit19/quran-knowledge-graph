---
type: decision
adr: 0007
status: accepted
date: 2026-05-10
tags: [decision, agent-loop, architecture]
supersedes: none
---

# ADR-0007 — Adopt orchestrator-with-fresh-subagent pattern over plain cron-into-session

## Status
Accepted (2026-05-10). Active.

## Context
The self-improvement loop needs to run on a cron schedule and execute tasks autonomously. The simplest approach is a cron job that calls `claude --session <existing-session>` and appends a task prompt — but this accumulates context across ticks, eventually causing context drift and degraded behavior. An alternative was the official Anthropic Ralph plugin (rejected — see ADR-0008). Research tick `05_ralph_yt_extract.md` (Jeff Huntley + Dex YT conversation, commit `30a0aa0`) documented the "one context window, one goal" principle: each task should execute in a fresh context so the model has full headroom and no stale prior-tick debris.

## Decision
Each cron fire spawns a fresh general-purpose subagent (via Claude Code harness subprocess) that does exactly ONE tick — reads state from disk, picks the top-priority task, does the work, runs `ralph_tick.py` acceptance gate, commits, and pushes. The orchestrator script lives outside the agent context. This is the closest match to Jeff's "Ralph fresh-context principle" within Claude Code's harness architecture.

## Consequences
- **Positive:** Each tick starts with a clean context window; no risk of prior-tick reasoning leaking. Acceptance gate runs deterministically in the orchestrator layer, not at the model's discretion. Git commit/push is guaranteed by the harness.
- **Negative:** Startup cost per tick (fresh context load, state read from disk). Cannot carry in-flight multi-step work across ticks without persisting intermediate state to disk.
- **Neutral:** Cron schedule is `7 * * * *` (hourly at :07). Tick alternates IMPL/RESEARCH by `tick_count % 2`. Halt flag: `data/RALPH_STOP`.

## Cross-references
- Source evidence: `repo://data/research_neo4j_crawl/05_ralph_yt_extract.md` (Jeff Huntley + Dex YT)
- Related: [[0008-no-ralph-plugin]], `repo://CLAUDE_INDEX.md` (Loop architecture section)
