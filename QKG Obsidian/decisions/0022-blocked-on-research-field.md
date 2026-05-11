---
type: decision
adr: 0022
status: accepted
date: 2026-05-12
tags: [decision, loop, architecture]
supersedes: none
---

# ADR-0022 — blocked_on_research field for task dependencies

## Status
Accepted (2026-05-12). Active.

## Context
When switching to 4:1 IMPL:RESEARCH ratio (ADR-0021), there was a risk that implementation tasks would be picked before their required research was complete. The fix is a `blocked_on_research: [<topic_id>]` field in `data/proposed_tasks.yaml` and `data/ralph_backlog.yaml`. The IMPL picker now honors this constraint: if any listed research topic is still open in `research_backlog.yaml` or pending in `neo4j_research_queue.yaml`, the task is skipped and the next eligible task is picked. Introduced in commit `6f86187`.

## Decision
Add optional `blocked_on_research` field to task specs. When present, list the research topic IDs that must be completed before this task can proceed. The IMPL task picker checks this field and skips tasks with unmet research dependencies. Captured in `data/proposed_tasks.yaml` and `data/ralph_backlog.yaml`.

## Consequences
- **Positive:** Prevents premature implementation of tasks that depend on pending research. Allows flexible 4:1 ratio without forcing dependencies.
- **Negative:** Requires discipline in populating and maintaining the field; missing dependencies can cause tasks to block silently.
- **Neutral:** Field is optional; absence means no research dependency. Can be extended to `blocked_on_other: [task_id]` if needed for task-to-task dependencies.

## Cross-references
- Source evidence: commit `6f86187` — `git show 6f86187` for full context
- Related: [[0021-4to1-impl-research-ratio]], [[0023-synthesis-sub-step]], `repo://data/proposed_tasks.yaml`
