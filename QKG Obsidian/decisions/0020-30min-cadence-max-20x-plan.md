---
type: decision
adr: 0020
status: accepted
date: 2026-05-12
tags: [decision, loop, observability]
supersedes: none
---

# ADR-0020 — 30-min cadence (was hourly) under Max 20x plan

## Status
Accepted (2026-05-12). Active.

## Context
The user upgraded from Max 5x to Max 20x API budget (~4× headroom). Previous hourly cadence (`7 * * * *`) was conservative; 24 ticks/day × ~90K tokens/tick = ~2.16M tokens/day, hitting the Max 5x ceiling. Commit `cfe2336` shortened the cadence to every 30 minutes (`7,37 * * * *`), yielding 10 ticks/5h window = ~900K tokens/window = 45-95% of Max 20x budget. This provides meaningful throughput while leaving headroom for Sonnet prep, Haiku prep, and contingency.

## Decision
Change cron schedule from hourly (`7 * * * *`) to every 30 minutes (`7,37 * * * *`). This yields 10 ticks per 5-hour window, sustainable at ~90K tokens/tick under Max 20x plan. Update CRON_BRIEF.md with new cadence. Paired with MAINT cycle speedup (every 6 ticks instead of 12) to catch issues faster.

## Consequences
- **Positive:** 2× throughput. Issues detected and fixed 2× faster. Sweet spot between productivity and budget headroom (45-95% utilization).
- **Negative:** Faster tick rate means more operational overhead (git pushes, state syncs). Greater chance of concurrent-edit conflicts if human and cron tick simultaneously.
- **Neutral:** Still conservative vs Max 20x capacity; can be tuned to 15-minute or 20-minute cadence if needed. MAINT cycle every 6 ticks (vs. 12) to keep up with faster issue detection.

## Cross-references
- Source evidence: commit `cfe2336` — `git show cfe2336` for full context
- Related: [[0013-cron-fresh-subagent-pattern]], [[0018-haiku-end-of-tick-prep]], [[0019-sonnet-pre-warming-for-opus-tasks]], `repo://scripts/CRON_BRIEF.md`
