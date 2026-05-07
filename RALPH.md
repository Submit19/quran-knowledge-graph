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

## Patterns borrowed from snarktank/ralph (Geoffrey Huntley pattern)

The "ralph wiggum" loop pattern, as implemented by Ryan Carson at
[snarktank/ralph](https://github.com/snarktank/ralph). Key insight:
**run a fresh agent in a loop, with persistent state in files (not
context). Agent reads files, picks the next thing, does it, updates
the files, exits. Wrapper detects "complete" signal and stops.**

### 1. Codebase Patterns block in `ralph_log.md`
> "If you discover a reusable pattern that future iterations should know, add it to the `## Codebase Patterns` section."

`ralph_log.md` now has a fenced `<!-- PATTERNS:START -->...END -->`
block at the top. Append durable, project-wide learnings here (separate
from per-tick rows). API: `ralph_loop.add_codebase_pattern("...")`.

Tasks can also set their `notes` to start with `PATTERN: ...` and the
loop will auto-promote it to the patterns block on success.

### 2. Repo-wide quality gate before commit
> "ALL commits must pass your project's quality checks (typecheck, lint, test). Broken code compounds across iterations."

Tasks that mutate code declare `commits_code: true` in their spec.
After the executor declares DONE, the loop runs `quality_gate()` —
a fast (~2s) smoke import of all core modules. Failure demotes
the task to FAILED and keeps it in the queue for retry.

### 3. Project-wide completion signal
> Snarktank ralph emits `<promise>COMPLETE</promise>` when all stories pass.

Our equivalent: `project_completion:` block at the top of
`ralph_backlog.yaml`. Supports:
```yaml
project_completion:
  all_tasks_done: true              # all non-skipped, non-quarantined done
  ignore_quarantined: true
  min_metric:
    name: avg_unique_cites_per_q
    eval: data/eval_v1_results.json
    value: 50.0
  require_files: [data/multihop_bench.jsonl]
```

`ralph_run.py` checks this before each tick and exits 0 when met.

### 4. Loop wrapper (`ralph_run.py`)
> The snarktank `ralph.sh` runs N iterations, exits on completion signal.

Cross-platform Python equivalent. Calls `tick()` repeatedly until:
- project completion criteria met (exit 0), or
- queue exhausted (exit 0 if criteria still met, 1 otherwise), or
- max iterations reached (exit 1).

```bash
python ralph_run.py                          # 10 iterations
python ralph_run.py --max 20 --sleep 30
python ralph_run.py --types eval,cypher_analysis,cleanup --git-commit
python ralph_run.py --dry                    # preview each iteration
```

`--git-commit` adds + commits + pushes after every tick (snarktank
style). Without it, you commit by hand or via your wake-up.

### Why the snarktank shape works for us

The original ralph loop is "feed the same prompt to a fresh Claude
in a bash loop." We're not doing that — our executors are Python,
not LLM calls. But the **persistence-via-files** discipline transfers
directly:
- `ralph_backlog.yaml` is our `prd.json`
- `ralph_state.json + ralph_log.md` is our `progress.txt`
- `data/ralph_*.md` artefacts are our `archive/`
- `ralph_run.py` is our `ralph.sh`

A future tick that's *re-entered from cold* (e.g. a wake-up that didn't
inherit context) reads the backlog, the state, and the patterns block,
then picks the right thing. That's the whole point.

## Patterns borrowed from obra/superpowers

The loop integrates several patterns from
[obra/superpowers](https://github.com/obra/superpowers):

### 1. Gate function (verification before completion)
> "NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE."

Every task can declare `acceptance` checks in its spec. After the
executor runs, `verify_acceptance()` runs them. If any fail, the
task is marked `FAILED` even if the executor said `DONE`.

Supported acceptance check shapes:
```yaml
acceptance:
  - file_exists: data/eval_v1_results.json
  - file_min_bytes: {path: data/eval_v1_results.json, min: 50000}
  - metric_above: {name: avg_unique_cites_per_q, value: 30}
  - metric_at_least_baseline: avg_unique_cites_per_q   # within 5%
  - python: "result.metric_after is not None and result.metric_after > 25"
```

### 2. Three-strikes rule (quarantine after N failed attempts)
> "After three failed attempts, suggest an architectural problem rather than a simple bug."

Each task tracks `attempts` per id. Default `MAX_ATTEMPTS = 3`
(override in `spec.max_attempts`). Once exceeded, the task is moved
to `quarantined_task_ids` and skipped by the picker until manually
unblocked. Successful completion resets the counter.

### 3. Implementer status taxonomy (richer than success/fail)
> Four statuses: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED.

The loop uses:
- `DONE` — succeeded, acceptance criteria verified
- `DONE_WITH_CONCERNS` — succeeded but soft-pass (no acceptance specified, or agent output that needs human review)
- `NEEDS_CONTEXT` — couldn't run; missing inputs (e.g., API key)
- `BLOCKED` — external blocker (Neo4j down, server crashed)
- `REGRESSION` — ran cleanly but metric dropped below threshold
- `FAILED` — ran with error
- `QUARANTINED` — hit `MAX_ATTEMPTS`
- `SKIPPED` — task type not auto-runnable

### 4. Subagent-driven with constructed context
> "By precisely crafting their instructions and context, you ensure they stay focused. They should never inherit your session's context or history."

The `agent_creative` executor calls OpenRouter (`gpt-oss-120b:free` by
default) with a fresh, narrow context: only the task's `description` +
`spec`. The orchestrator's session history is NEVER passed. Output is
written to `data/ralph_agent_<id>.md` and marked `DONE_WITH_CONCERNS`
so a human reviews before downstream tasks consume it.

### 5. Acceptance criteria explicit in plan (TDD shape)
> "Run the command. Read the output. THEN claim the result."

`acceptance` is the test you'd write before the implementation. For
prompt-variant work this means: define the metric+threshold the
variant must clear in the spec, then apply the variant, then run the
eval. The gate function is the "test pass."

## Honest scope

This is intentionally a small loop — not an autonomous agent. It
runs deterministic Python tasks; creative work calls a fresh OpenRouter
subagent with constructed context (no session history); creative output
defaults to `DONE_WITH_CONCERNS` so a human reviews before
downstream use. Keeps the failure modes tiny.

The value is in the *backlog* and *log*: a single place to record
"things I want to try" and "things I tried + outcome." Everything
else is convenience around that.
