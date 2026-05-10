---
type: architecture
subsystem: ralph-loop
status: current
date_added: 2026-05-10
---

# Ralph Loop — Self-Improvement Cron

## What it does

An overnight autonomous improvement loop: a cron fires every hour, spawns one fresh LLM subagent that picks the highest-priority unblocked task from `ralph_backlog.yaml`, does the work, validates impact, commits, and returns a 4-line summary. No persistent context accumulates — the fresh-subagent pattern avoids auto-compaction degradation.

## Where it lives

- `ralph_loop.py` — library: task picker, executor dispatch, status taxonomy, gate function, `TickResult` dataclass
- `ralph_tick.py` — CLI entry point (`python ralph_tick.py [--task <id>] [--dry] [--status]`)
- `ralph_run.py` — loop wrapper; `--max`, `--types`, `--git-commit`, pacing (`--max-calls-per-day`, `--min-api-gap-sec`)
- `ralph_backlog.yaml` — human-editable task queue with `priority`, `type`, `acceptance_criteria`
- `ralph_state.json` — auto-managed: `in_progress`, `done_task_ids`, `tick_count`, `history`, `api_usage`
- `ralph_log.md` — append-only tick log with a **Codebase Patterns** block for durable learnings

## Status taxonomy

| Status | Meaning |
|--------|---------|
| `DONE` | Succeeded; acceptance criteria verified |
| `DONE_WITH_CONCERNS` | Succeeded but a sub-check warned |
| `NEEDS_CONTEXT` | Missing inputs/dependencies |
| `BLOCKED` | External blocker (Neo4j down, model unreachable) |
| `REGRESSION` | Metric dropped below threshold — do not commit |
| `FAILED` | Ran with error |
| `QUARANTINED` | ≥ 3 failures — removed from auto-pick |
| `SKIPPED` | Task type not auto-runnable (manual / external_run) |

`MAX_ATTEMPTS_DEFAULT = 3` — three failures → `QUARANTINED`. Pattern from the "superpowers" implementer principle: "3 failed attempts → architectural problem."

## Tick alternation

`state.tick_count % 2`: even ticks run `IMPL` tasks (code changes), odd ticks run `RESEARCH` tasks (crawl + summarize). Research ticks pop from `data/research_neo4j_crawl/neo4j_research_queue.yaml` (~111 items across 5 sources).

## Gate function

After an executor completes, `ralph_loop` runs the quality gate: re-runs the eval harness (`eval_v1.py`) and compares metric before/after. A regression (metric drop) forces `REGRESSION` status and skips the commit.

## Manual mode

`RALPH_AGENT_BACKEND=manual` — the Opus operator does the work out-of-band; `ralph_tick.py` validates the result against acceptance criteria and updates state. Useful when the task requires multi-file refactors too large for a single subagent context.

## Codebase Patterns block

`ralph_log.md` contains a `<!-- PATTERNS:START --> ... <!-- PATTERNS:END -->` section. Executors append durable learnings here when they discover something general. Future ticks read this block as system context before starting work.

## Cross-references
- [[memory-stack]] — Ralph loop is Tier 2 operational state
- [[agent-loop]] — Ralph subagents use the same agentic pattern internally
- [[overview]] — Ralph sits outside the request path; it improves the system offline
- Source: `repo://ralph_loop.py`, `repo://ralph_run.py`, `repo://ralph_tick.py`, `repo://RALPH.md`, `repo://CLAUDE_INDEX.md` (Loop architecture section)
