---
type: decision
adr: 0013
status: accepted
date: 2026-05-12
tags: [decision, loop, architecture]
supersedes: none
---

# ADR-0013 — Cron orchestrator spawns fresh subagent per tick

## Status
Accepted (2026-05-12). Active. Foundation for all 0014-0023.

## Context
The fresh-subagent pattern (ADR-0007) runs each cron-fired tick in its own context window to avoid accumulation and drift. Prior iterations executed all ticks in the same orchestrator session, causing context inflation and reasoning leakage. Commit `c638985` formalized the spawn-and-commit flow: cron fires, creates a fresh general-purpose subagent, that subagent picks a task, does work, runs the acceptance gate, and commits. The orchestrator script (outside agent context) manages the cron schedule and state persistence.

## Decision
Every 30-minute cron fire spawns a completely fresh Claude Code subagent process. The orchestrator passes no prior session context — only the prompt `CRON_BRIEF.md` file (see ADR-0016) and a state directory. Each subagent is independent; multi-step work is persisted to disk (YAML, markdown, JSON) and picked up by the next tick. No carry-over of reasoning or reasoning_memory within the agent.

## Consequences
- **Positive:** Eliminates context bloat and prior-tick bias. Acceptance gate runs deterministically outside the model, not at the model's discretion. Git operations (commit/push) are guaranteed by the harness wrapper.
- **Negative:** Startup cost per tick (fresh context load, state disk read). Cannot execute cross-tick stateful work without explicit disk hand-off.
- **Neutral:** Cron schedule is `7,37 * * * *` (every 30 min, see ADR-0020); tick type alternates IMPL/RESEARCH/MAINT per CRON_BRIEF.md; halt flag is `data/RALPH_STOP`.

## Cross-references
- Source evidence: commit `c638985` — `git show c638985` for full context; `repo://scripts/CRON_BRIEF.md`
- Related: [[0007-orchestrator-fresh-subagent]], [[0016-cron-prompt-file-based]], [[0020-30min-cadence]]
