---
type: decision
adr: 0008
status: accepted
date: 2026-05-10
tags: [decision, agent-loop, architecture]
supersedes: none
---

# ADR-0008 — Do not adopt the official Anthropic Ralph plugin

## Status
Accepted (2026-05-10). Active.

## Context
The official Anthropic "Ralph Wigum" Claude Code plugin is an alternative to a hand-rolled loop: it hooks into Claude Code internally and re-injects the `prompt.md` as a new user message whenever the model has not yet emitted a "completion promise." Research tick `05_ralph_yt_extract.md` (Jeff Huntley + Dex YT, 2026-05-10) documents the plugin's failure modes in detail, with a live demonstration in the source video. Jeff Huntley explicitly warns against it for teams that want deterministic behavior.

## Decision
Do not install or use the Anthropic Ralph plugin. The existing outer-harness architecture (`ralph_run.py` + `ralph_tick.py` + cron orchestrator) is structurally superior for QKG's needs.

## Consequences
- **Positive:** No auto-compaction risk. Our "Codebase Patterns" block and status taxonomy (DONE / DONE_WITH_CONCERNS / QUARANTINED / FAILED) must survive the full tick duration — the plugin's internal compaction can silently drop these. Termination is controlled by the external acceptance gate, not by the model promising it is finished.
- **Negative:** More infrastructure to maintain (shell harness, Python acceptance gate). No built-in Claude Code UX integration.
- **Neutral:** The plugin is appropriate for casual/exploratory loops where determinism is less critical. QKG's loop writes to production graph state and commits code; the higher bar justifies the added harness complexity.

## Cross-references
- Source evidence: `repo://data/research_neo4j_crawl/05_ralph_yt_extract.md` ("The official Anthropic Ralph plugin" section)
- Related: [[0007-orchestrator-fresh-subagent]]
