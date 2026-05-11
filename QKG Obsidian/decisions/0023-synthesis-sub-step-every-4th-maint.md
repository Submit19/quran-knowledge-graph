---
type: decision
adr: 0023
status: accepted
date: 2026-05-12
tags: [decision, loop, observability]
supersedes: none
---

# ADR-0023 — SYNTHESIS sub-step every 4th MAINT tick

## Status
Accepted (2026-05-12). Active.

## Context
The backlog and research queue accumulate findings continuously. Without periodic synthesis, the project risks implementing in isolation — later learning that research contradicts earlier decisions or that patterns emerged that should reshape prioritization. Commit `6f86187` introduced a SYNTHESIS sub-step: every 4th MAINT tick (every 24th tick / ~12h at 30-min cadence), read all recent research summaries + proposed tasks + analysis reports, produce a cross-cutting insights doc at `data/research_synthesis_<date>.md`, and apply re-prioritizations back to the backlog. First synthesis ran in parallel in the commit message itself.

## Decision
Insert a SYNTHESIS sub-step into every 4th MAINT tick (every 12 hours at 30-min cadence). The step (1) reads recent research_log.md entries, proposed_tasks.yaml, and analysis markdown files; (2) spawns a one-shot subagent to produce cross-cutting insights doc; (3) applies resulting re-prioritizations to the backlog. Captured in CRON_BRIEF.md.

## Consequences
- **Positive:** Ensures "learn before doing" is not forgotten. Surfaces pattern-level insights (e.g., "reranker harm is systematic across A/B tests"). Prevents information scatter.
- **Negative:** Every 4th MAINT tick consumes extra tokens for synthesis subagent (~20-30K per synthesis). Synthesis insights must be actionable or they bloat the system.
- **Neutral:** Can tune to every 2nd MAINT (6h) or 6th MAINT (18h) if synthesis value changes. Knob: `SYNTHESIS_DISABLED=1` for offline mode.

## Cross-references
- Source evidence: commit `6f86187` — `git show 6f86187` for full context; `data/research_synthesis_2026-05-12.md` (first synthesis output)
- Related: [[0021-4to1-impl-research-ratio]], [[0022-blocked-on-research-field]], `repo://scripts/CRON_BRIEF.md`
