---
type: decision
adr: 0016
status: accepted
date: 2026-05-12
tags: [decision, loop, observability]
supersedes: none
---

# ADR-0016 — Cron prompt moved to scripts/CRON_BRIEF.md (file-based brief)

## Status
Accepted (2026-05-12). Active.

## Context
The cron orchestrator was embedding the full subagent prompt (~6KB) inline in the Python scheduler. This inflated the orchestrator-session context by ~1.5K tokens per fire, and edits to the brief required deleting and recreating the cron job. Commit `a6bdcf6` externalized the brief to `scripts/CRON_BRIEF.md`. The cron prompt became a 5-line stub that reads and injects the file content. This reduces per-tick overhead and makes brief updates editable without scheduler restarts.

## Decision
Move the subagent brief from the orchestrator code to `scripts/CRON_BRIEF.md`. The cron scheduler reads this file at each fire and passes its content as the main task prompt. The brief contains the full task decomposition (cycle decision, task picker logic, tool caps, acceptance gates, etc.). The scheduler wrapper stays in Python; the brief stays in markdown.

## Consequences
- **Positive:** ~1.5K token saving per fire (5h × 10 fires = ~15K/day saved). Brief edits no longer require CronDelete+CronCreate. Brief is human-readable and version-controlled.
- **Negative:** Brief must be kept in sync manually; an outdated file is silent (no error, just stale behavior).
- **Neutral:** File is read at cron-fire time, not cached. Brief must be valid markdown and well-structured for subagents to parse.

## Cross-references
- Source evidence: commit `a6bdcf6` — `git show a6bdcf6` for full context
- Related: [[0013-cron-fresh-subagent-pattern]], `repo://scripts/CRON_BRIEF.md`, `repo://scripts/README.md`
