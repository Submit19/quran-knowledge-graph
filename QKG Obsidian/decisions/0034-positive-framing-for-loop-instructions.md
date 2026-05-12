---
type: decision
adr: 0034
status: accepted
date: 2026-05-12
tags: [decision, loop, agentic, prompt-engineering]
supersedes: none
---

# ADR-0034 — Positive framing for loop instructions (no negative imperatives)

## Status
Accepted (2026-05-12). Shipped in commit `45e4a63`, tick 82 IMPL.

## Context
Task `from_ralph_yt_03_audit_negative_prompts` (p72) audited system prompts and loop
infrastructure for negative-form instructions ("don't X", "never Y", "avoid Z").

Research backing (Jeff Huntley YT extract `05_ralph_yt_extract.md`): LLMs trained with
RLHF are more reliably steered by positive action statements than by negations. Negative
imperatives require the model to suppress a behavior; positive imperatives activate a
specific alternative. Under context pressure (long conversations, compaction), negations
are the first instructions to erode.

9 instances were identified across `ralph_loop.py`, `CRON_BRIEF.md`, and `ralph_backlog.yaml`.

## Decision
Rewrite all negative-form loop instructions as positive action statements:

- "don't retry an unchanged broken spec" → "fix the spec once, then re-run"
- "never commit partial work" → "commit only when the deliverable is complete"
- "avoid spiraling on fix-retry loops" → "after two failures, fix the spec and move on"
- (and 6 others in the same spirit)

The rule is: every behavioral constraint in loop infrastructure must be expressed as
"do X" rather than "don't X". The equivalent positive action must be explicit, not
left to inference.

## Consequences
- **Positive:** More reliable instruction-following under context pressure.
- **Positive:** Positive frames are easier to audit — you can verify compliance by
  observing the specified action, rather than detecting the absence of a forbidden one.
- **Negative:** Some instructions are naturally expressed as negations (e.g., safety
  guards). These were left as-is where no clean positive equivalent existed.
- **Neutral:** Ongoing hygiene: new loop instructions added to CRON_BRIEF.md or
  ralph_loop.py should follow the positive-framing convention from the start.

## Cross-references
- Source: commit `45e4a63`, files `ralph_loop.py`, `scripts/CRON_BRIEF.md`, `ralph_backlog.yaml`
- Evidence: `data/research_neo4j_crawl/05_ralph_yt_extract.md` (Jeff Huntley on Ralph loop design)
- Proposed by: ralph IMPL tick 82
