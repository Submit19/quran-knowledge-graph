---
type: decision
adr: 0015
status: accepted
date: 2026-05-12
tags: [decision, agentic, loop]
supersedes: none
---

# ADR-0015 — Manual mode for cypher_analysis tasks (query_kind: manual)

## Status
Accepted (2026-05-12). Active.

## Context
Several pending tasks in `data/proposed_tasks.yaml` have acceptance criteria (what the deliverable should contain) but no `query` or `script` field. These were entering NEEDS_CONTEXT → FAILED → manual-recovery loops, costing 10-15K tokens per retry. The `cypher_analysis` executor was rejecting them as ill-formed. Commit `a6bdcf6` added support for `query_kind: manual` (or absence of both `query` and `script`). When set, the executor skips Cypher execution and returns `DONE_WITH_CONCERNS`, allowing the operator to write the deliverable file and the gate to validate it.

## Decision
Extend `execute_cypher_analysis` in `ralph_loop.py` to accept `query_kind: manual`. When set, skip query execution and defer to the acceptance gate to validate a pre-produced deliverable file (e.g., `data/analyses/<task_id>.md`).

## Consequences
- **Positive:** Fixes 4 pending cypher_analysis tasks that had only acceptance criteria. Avoids retry spirals. Operator has full control over analysis quality and scope.
- **Negative:** Manual mode requires out-of-band human intervention for those specific tasks.
- **Neutral:** Paired with ADR-0014 (manual agent_creative mode). Default is normal Cypher execution when `query` or `script` is present. Applies alongside ADR-0018 (Haiku prep validation) which warns about these tasks in `data/spec_warnings.md`.

## Cross-references
- Source evidence: commit `a6bdcf6` — `git show a6bdcf6` for full context
- Related: [[0014-ralph-agent-backend-manual-mode]], [[0018-haiku-end-of-tick-prep]], `repo://ralph_loop.py` (execute_cypher_analysis fn)
