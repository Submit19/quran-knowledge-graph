# Ralph Loop — design + how to use

A small self-iterating agent loop for the Quran Knowledge Graph project.
Wake up, pick the highest-priority unblocked task from a ranked backlog,
run it, measure impact, log what was learned, schedule next.

Two surfaces it iterates on:
1. **Answer quality** — eval-driven (`eval_v1.py` over a small held-out
   question set, citation density / time / chars per question vs baseline)
2. **Architecture** — small targeted experiments (prompt variants, config
   tweaks, cache ops, embedding refreshes, Cypher analyses)

## Files

| File | Role |
|---|---|
| `ralph_backlog.yaml` | Human-editable ranked queue. Add/edit tasks here. |
| `ralph_state.json` | Auto-managed: `in_progress`, `done_task_ids`, history. |
| `ralph_log.md` | Append-only markdown log, one row per tick. |
| `ralph_loop.py` | Core: state I/O, task picker, executors, dispatch. |
| `ralph_tick.py` | CLI entry — call this to run one tick. |

## Quick start

```bash
# See what's in the queue right now
python ralph_tick.py --status

# Preview the next pick (no changes)
python ralph_tick.py --dry

# Run one tick (auto-pick the top eligible task)
python ralph_tick.py

# Force a specific task
python ralph_tick.py --task rerun_eval_against_current

# Restrict to certain task types (e.g. only safe read-only analyses)
python ralph_tick.py --types cypher_analysis,cleanup
```

## Task types

| Type | Auto-runs? | What it does |
|---|---|---|
| `eval` | ✅ | Runs an eval script (default `eval_v1.py`), compares to baseline, marks regression if metric drops > X%. |
| `cypher_analysis` | ✅ | Runs read-only Cypher (or an inline Python snippet) and dumps output to `data/ralph_analysis_<id>.md`. |
| `cleanup` | ✅ | No-op success placeholder for hygiene tasks. Customise per-task. |
| `prompt_variant` | ⚠️ stub | Apply a prompt/code variant, eval, A/B. Stubbed — implement when needed. |
| `embed_op` | ⚠️ stub | Re-embed something (Query nodes, cache, etc.). |
| `cache_op` | ⚠️ stub | Refresh / re-key the answer cache. |
| `agent_creative` | ⚠️ stub | LLM-driven (write prompt variants, generate eval questions). Skipped in auto-mode. |
| `manual` | ❌ skip | Requires user (e.g. hand-grading answers). |
| `external_run` | ❌ skip | Needs long-running external process. |

Stub task types are skipped with a clear note. Implement their executor in
`ralph_loop.py` (`execute_<type>`) when you want them to auto-run.

## Backlog format

```yaml
- id: rerun_eval_against_current
  type: eval
  priority: 95
  description: "Run eval_v1.py vs current state, compare to baseline"
  blockers: []          # task ids that must be done first
  spec:
    script: eval_v1.py
    metric: avg_unique_cites_per_q
    compare_to: data/eval_v1_results.json
    regression_pct: 5
```

A task is **eligible** when:
- not in `done_task_ids`
- not in `skipped_task_ids`
- not the current `in_progress`
- all `blockers` are in `done_task_ids`
- `--types` filter (if any) allows its type

The picker takes the highest `priority` among eligible.

## Wake-up integration (Claude Code)

To run unattended every N hours, schedule a wake-up that runs:

```
cd C:/Users/alika/Agent\ Teams/quran-graph-standalone
python ralph_tick.py --types eval,cypher_analysis,cleanup
git add ralph_state.json ralph_log.md data/eval_*.json data/ralph_analysis_*.md
git commit -m "ralph tick" 2>/dev/null
git push 2>/dev/null
```

Restrict types to those that auto-run by default. For tasks that need
creativity (prompt variants, generating eval questions), you (Claude
in a foreground session) handle them by reading the backlog, picking
the top stubbed task, and doing the creative work then rerunning the
eval to validate.

## Adding a discovered follow-up

When a tick learns something useful (e.g. an analysis finds a gap), it
should propose a new task. Today this is manual — append to
`ralph_backlog.yaml`. Future: executors return `new_tasks: [...]` and
the loop appends them automatically.

## Status I/O contract

`ralph_state.json` shape:
```json
{
  "version": 1,
  "in_progress": null,
  "last_tick": "2026-05-07T18:00:00+00:00",
  "tick_count": 12,
  "done_task_ids": ["rerun_eval_against_current", "..."],
  "skipped_task_ids": ["hand_grade_26_answers"],
  "baselines": { "avg_unique_cites_per_q": 43.6 },
  "history": [ {TickResult}, ... ]
}
```

`ralph_log.md` is a markdown table, one row per tick: `ts, task_id,
type, status, metric Δ, notes`.

## Failure modes

- **Task fails (non-zero exit, error)**: stays in queue, loops back to
  it on the next tick. Logged with `status: failed` + error excerpt.
- **Task regresses metric**: same — stays in queue. Inspect manually,
  decide whether to remove from backlog, fix and retry, or accept.
- **No eligible task**: `tick()` returns None, exits cleanly. Edit the
  backlog or unblock something.

## Honest scope

This is intentionally a small loop — not an autonomous agent. It
runs deterministic Python tasks; creative work (prompt rewrites,
question generation) is gated behind `agent_creative` and skipped
unless wired to an LLM. Keeps the failure modes tiny.

The value is in the *backlog* and *log*: a single place to record
"things I want to try" and "things I tried + outcome." Everything
else is convenience around that.
