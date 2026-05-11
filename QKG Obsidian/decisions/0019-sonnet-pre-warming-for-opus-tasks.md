---
type: decision
adr: 0019
status: accepted
date: 2026-05-12
tags: [decision, agentic, loop]
supersedes: none
---

# ADR-0019 — Sonnet pre-warming for [opus] tasks

## Status
Accepted (2026-05-12). Active.

## Context
Tasks tagged `[opus]` (high-complexity reasoning) were entering the backlog without any draft or scaffolding. When the IMPL tick selected one, the nested Opus subagent had to discover and plan from scratch, consuming ~$0.50 worth of Opus tokens. Commit `cfe2336` introduced `scripts/sonnet_prep.py`: at tick_finalize end, if the next pending `[opus]` task has no existing draft, call Sonnet to produce an implementation-plan markdown. The IMPL subagent then reads this draft as context, skipping cold discovery and saving ~$0.40 per task ($0.10 Sonnet cost saves $0.50 Opus cost).

## Decision
Add `scripts/sonnet_prep.py` to `tick_finalize.py`. At end-of-tick, if the next pending task is tagged `[opus]` and has no draft file, call Claude Sonnet to produce a detailed implementation plan and save to `data/sonnet_drafts/<task_id>.md`. Update CRON_BRIEF.md to tell IMPL ticks to check for and include the draft in nested Opus prompts.

## Consequences
- **Positive:** Opus subagent starts with a ready-made plan instead of cold-starting. Net cost savings ~$0.40/task. Reduces variance in Opus output quality.
- **Negative:** Adds Sonnet call per tick when `[opus]` task is pending (~$0.10 cost). Sonnet draft must be accurate or it misdirects Opus.
- **Neutral:** Knobs: `SONNET_PREP_DISABLED=1` (skip), `SONNET_PREP_MODEL=<id>` (default `claude-sonnet-4-6`).

## Cross-references
- Source evidence: commit `cfe2336` — `git show cfe2336` for full context
- Related: [[0013-cron-fresh-subagent-pattern]], [[0020-30min-cadence]], `repo://scripts/sonnet_prep.py`
