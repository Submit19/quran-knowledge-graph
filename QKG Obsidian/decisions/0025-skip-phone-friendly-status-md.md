---
type: decision
adr: 0025
status: accepted
date: 2026-05-12
tags: [decision, observability]
supersedes: none
---

# ADR-0025 — Skip phone-friendly STATUS.md (operator uses Claude app on phone)

## Status
Accepted (2026-05-12). Active. Superseded 861403d (keep safety net only).

## Context
An earlier commit (`861403d`) added a phone-optimized STATUS.md summary and modified `state_snapshot.py` to generate mobile-friendly views. The rationale was to let the operator check state on GitHub mobile browser. However, the operator clarified that they interact via the Claude app on their phone, not via GitHub mobile browser. The phone-friendly STATUS.md became redundant — Claude (running in-session on the phone app) can read `STATE_SNAPSHOT.md` and underlying state files (YAML, markdown) directly. Commit `38594e7` reverted STATUS.md and the corresponding state_snapshot.py mobile-view code while keeping the push-flush safety net (`git pull --rebase && git push` at tick start).

## Decision
Remove the phone-friendly STATUS.md view. Rely on `STATE_SNAPSHOT.md` (machine-generated, dense, version-controlled) and in-session Claude reading state files directly. Keep the push-flush safety net (tick-start `git pull --rebase && git push`) since that is useful for GitHub-as-backup regardless of mobile use.

## Consequences
- **Positive:** Reduces state_snapshot.py complexity (removed ~150 lines of mobile-view generation). One fewer file to version-control. Operator gets fresher context via direct in-session state reading instead of stale GitHub renders.
- **Negative:** No standalone mobile-friendly view on GitHub. Operator must use Claude app to check state (which they were already doing).
- **Neutral:** STATE_SNAPSHOT.md remains; it is dense and sufficient for in-session reading. Push-flush safety net still runs to keep GitHub in sync.

## Cross-references
- Source evidence: commit `38594e7` — `git show 38594e7` for full context
- Related: [[0007-orchestrator-fresh-subagent]], [[0012-5-tier-memory-stack]], `repo://scripts/state_snapshot.py`
