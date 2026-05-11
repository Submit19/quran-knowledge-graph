---
type: decision
adr: 0021
status: accepted
date: 2026-05-12
tags: [decision, loop, observability]
supersedes: none
---

# ADR-0021 — 4:1 IMPL:RESEARCH ratio (was 1:1 alternation)

## Status
Accepted (2026-05-12). Active.

## Context
Early phase (ticks 1-35) executed research-then-implement cycles: 1:1 RESEARCH:IMPL alternation. Phase 1 deep-crawl research was foundational and necessary (Neo4j docs, GraphAcademy, YouTube channels). By tick 36+, the 21 remaining research queue items were incremental (blog posts validating existing knowledge, subsection deep-dives, GraphAcademy tutorials). Signal-to-noise dropped. Meanwhile the backlog grew to 42 evidence-rooted, ready-to-ship tasks. Commit `6f86187` changed the cycle from alternation to 4:1 IMPL:RESEARCH ratio. Across 12 ticks: 2 MAINT + 2 RESEARCH + 8 IMPL. Can re-tune via `blocked_on_research` field if research queue grows >40.

## Decision
Switch from % 2 (RESEARCH/IMPL alternation) to % 3 cycle decision. Across 12 ticks: [MAINT, RESEARCH, IMPL, IMPL, MAINT, RESEARCH, IMPL, IMPL, IMPL, IMPL, RESEARCH, IMPL]. Ratio 4:1 IMPL:RESEARCH. Implement `blocked_on_research` field to skip implementation tasks dependent on pending research. Re-tune knob back to % 2 if research backlog grows >40; raise to % 4 if it empties below 5.

## Consequences
- **Positive:** 4× faster throughput on implementation. Backlog clears 4× faster. Research is batched (every 3 ticks), reducing context-switching.
- **Negative:** Risk of implementing tasks that should wait for deeper research. Requires `blocked_on_research` discipline to prevent this.
- **Neutral:** Tunable; can revert to 1:1 alternation if research signal improves. Phase 2 (May onwards) is implementation-heavy by design.

## Cross-references
- Source evidence: commit `6f86187` — `git show 6f86187` for full context
- Related: [[0022-blocked-on-research-field]], [[0023-synthesis-sub-step]], `repo://scripts/CRON_BRIEF.md`
