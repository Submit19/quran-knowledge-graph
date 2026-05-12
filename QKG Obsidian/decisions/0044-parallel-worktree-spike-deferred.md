---
type: decision
adr: 0044
status: proposed
date: 2026-05-13
tags: [decision, loop-architecture, worktree, parallelism, ralph]
supersedes: none
---

# ADR-0044 — Parallel worktree spike for ralph loop (deferred)

## Status
Proposed / Design-only (2026-05-13). Spike design doc shipped in commit `259b966`,
tick 113 IMPL. No implementation committed yet.

## Context
The ralph loop currently executes one task per tick serially. As the IMPL backlog
grows (17 pending as of tick 114), throughput is limited to ~1 task per 30 min
fire. The Jeff Huntley parallel-worktree pattern (YT video 04) suggests running
N subagents in parallel git worktrees, each owning a shard of the state, merging
back on completion.

## Decision
Spike design (`data/ralph_agent_from_ralph_yt_04_parallel_worktree_spike.md`)
documents the pattern but **defers implementation** pending resolution of:

1. **Neo4j singleton:** local Neo4j is single-writer; parallel subagents can read
   concurrently but write conflicts (ReasoningTrace, RETRIEVED edges) require
   either serialized writes or subagent write isolation.
2. **ralph_state.json shard/merge:** each worktree needs a state shard; merge
   must handle `done_task_ids`, `attempts`, and `tick_count` without losing
   increments. Design proposes `.gitattributes` union merge driver.
3. **[opus] task restriction:** Opus tasks must not run in parallel (cost + API
   limits); shard logic must filter them to a single lane.

The proof-of-concept `ralph_parallel.py` is sketched in the design doc. The
current decision is: **do not implement until Neo4j write-conflict strategy is
resolved**.

## Consequences
- **Positive:** If implemented, 2–4× throughput increase on the IMPL backlog.
- **Positive:** Design doc captures all gotchas (conflict surface, .gitattributes
  union driver, Opus restriction) for when implementation resumes.
- **Neutral:** Implementation risk is moderate: worktree + merge is well-tested
  git infrastructure; the main risk is ralph_state.json consistency.
- **Negative:** Adds operational complexity (N worktrees to clean up on crash).
- **Negative:** Deferred — no throughput benefit until operator approves and
  implements the Neo4j write isolation strategy.

## Cross-references
- Source: commit `259b966`, task `from_ralph_yt_04_parallel_worktree_spike`
- Files: `data/ralph_agent_from_ralph_yt_04_parallel_worktree_spike.md`
- Related: ADR-0007 (orchestrator + fresh-subagent), ADR-0013 (cron pattern)
- Proposed by: ralph IMPL tick 113, YT source ralph:P7jboLT0w2w
