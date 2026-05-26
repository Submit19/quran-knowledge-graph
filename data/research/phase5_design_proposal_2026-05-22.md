# Phase 5 — Design Proposal: Taming the Ralph Loop

_Builds on `phase5_ralph_reconnaissance_2026-05-22.md` and
`phase5_audit_synthesis_2026-05-22.md`. Extends the existing
`docs/PHASE_5_LOOP_TAMING_PLAN.md` (items 18–21 in
`docs/QKG_RETROFIT_PLAN.md`)._

This document proposes the specific changes needed to "tame" the Ralph
loop before Phase 11 restart. Each section follows the operator's
required structure:

- **Problem** — what specifically is being solved (with evidence)
- **Proposed solution** — the concrete change
- **Alternatives considered** — what was rejected and why
- **Risks** — what could go wrong with the proposed solution
- **Test scenario** — one concrete scenario the design must handle

The seven sections map 1-to-1 to the operator's seven Phase 5 design
dimensions: failure-mode prevention, observability, stop discipline,
scope discipline, resumability, quality bar, system integration.

**Hard guarantee:** every proposal below is implementable WITHOUT
runtime code changes in this session. Phase 4 (the xfail test
scaffolding) and Phase 5 (the phased implementation plan) wire each
proposal to executable tests and atomic merge-able sub-phases for a
later session.

**Hard non-goal:** none of this design removes `data/RALPH_STOP` or
restarts the loop. Phase 11 (operator-approved restart) is a separate
operator action whose preconditions this design enumerates.

---

## §A · Failure-mode prevention

### Problem

The audit (`docs/QKG_AUDIT.md` §7) named five failure modes that
caused the pause; the synthesis confirmed three are still active in
code at HEAD `5b03255`. In priority order:

1. **`agent_creative` → DONE_WITH_CONCERNS → TERMINAL_OK** is a
   straight-through pipe. 95% of agent_creative ticks (36/38) become
   DWC; the picker treats DWC as "done"; the graveyard accumulates.
   This is the load-bearing fiction.
2. **`verify_acceptance` returns DWC when no acceptance block exists**
   (`ralph_loop.py` lines 296–300). Any task without `acceptance:` in
   its spec gets a free soft pass. Currently affects ~10–15 of the
   80+ backlog tasks.
3. **Tasks with broken specs hit `NEEDS_CONTEXT` repeatedly without
   conversion to FAILED**. The 3-strikes rule fires on FAILED but
   `NEEDS_CONTEXT` is also in `TERMINAL_FAIL` — and `attempts` shows
   3 tasks at the quarantine threshold from `NEEDS_CONTEXT` retries,
   but the picker did pick them again on next tick (because the spec
   got hand-fixed). The mechanism works, but the discipline is
   "operator fixes spec mid-stream", not "loop quarantines and
   surfaces".

### Proposed solution

Three independent changes, layered:

**A.1 — Remove `DONE_WITH_CONCERNS` from `TERMINAL_OK`.**

```python
# Before (current ralph_loop.py line 69):
TERMINAL_OK = {DONE, DONE_WITH_CONCERNS, SKIPPED}

# After:
TERMINAL_OK = {DONE, SKIPPED}
TERMINAL_NEEDS_REVIEW = {DONE_WITH_CONCERNS}
```

Effect: DWC tasks stay in `pending` (not appended to `done_task_ids`)
until the operator manually promotes them by:

- adding a `# review-promote: <task_id> reason=<...>` line to
  `ralph_log.md` Codebase Patterns block, OR
- moving the task id into a new `state['reviewed_task_ids']` list
  via `python ralph_tick.py --promote <task_id>`.

A new task picker rule: if a task has reached DONE_WITH_CONCERNS, the
picker skips it (`in_review`) until the operator promotes or
quarantines. This converts DWC from "silent pass" to "explicit
operator gate".

**A.2 — Require `acceptance:` for all task types `tick()` executes.**

```python
# In ralph_loop.py::verify_acceptance, lines 296-300:
if not checks:
    # Hard fail (was: soft pass).
    return False, [{"check": "no acceptance specified",
                    "passed": False,
                    "detail": "Phase 5: every executable task must declare acceptance"}]
```

`agent_creative` tasks already require deliverable-file acceptance via
`file_min_bytes`; the same pattern extends to every type. Backlog tasks
without `acceptance:` are not eligible for the picker (skipped with a
clear console line: "task X has no acceptance — operator must update
backlog").

**A.3 — Distinguish "broken spec" from "broken work" in the
3-strikes rule.**

A task that fails 3× with `NEEDS_CONTEXT` (missing spec field) is a
DIFFERENT failure mode from one that fails 3× with `FAILED` (work
genuinely couldn't be done). Split the counter:

```python
# State shape change:
state["attempts"][task_id] = {
    "needs_context": 0,
    "failed_or_blocked": 0,
}
# Quarantine if EITHER counter hits max_attempts:
if attempts[task_id]["needs_context"] >= max_a:
    # ALSO: emit a clear "spec broken — operator must fix backlog YAML" line
    print(f"[ralph] SPEC-BROKEN-QUARANTINE {task['id']}")
elif attempts[task_id]["failed_or_blocked"] >= max_a:
    print(f"[ralph] WORK-FAILED-QUARANTINE {task['id']}")
```

Effect: when the loop quarantines, the operator knows whether to
fix the YAML or fix the underlying code/system.

### Alternatives considered

- **"Just remove `agent_creative` from `EXECUTORS`."** Equivalent to
  Phase 5 plan item 18, which keeps it for operator manual use but
  removes it from cron dispatch. We adopt this in §D below. It is
  necessary but not sufficient — even without `agent_creative`, the
  DWC → TERMINAL_OK pipe still leaks (any task without `acceptance:`
  hits it). **Rejected as sole fix.**
- **Auto-quarantine all DWC after N hours of no operator action.**
  Considered. Problem: the operator's natural review cadence is days,
  not hours, and the loop should be runnable in offline batches.
  **Rejected** in favour of the explicit-promote rule (A.1).
- **Add a new `REVIEW_PENDING` status outside `TERMINAL_OK` and
  `TERMINAL_FAIL`.** Cleaner conceptually but bigger code surface;
  the picker would need a new branch. **Rejected** for the simpler
  in_review-via-DWC approach. (Equivalent outcome; fewer lines.)

### Risks

- **R-A.1 (high):** old backlog tasks without `acceptance:` blocks
  will suddenly stop being eligible. ~10–15 tasks; operator must fix
  YAML or move them to a `paused_task_ids` list. Mitigation: Phase 5
  sub-phase 1 includes a one-time backlog audit script that lists
  every offending task; operator decides per-task. The loop's startup
  emits "WARNING: N backlog tasks have no acceptance — skipping".
- **R-A.2 (medium):** the `# review-promote:` parser is a new surface
  area; could be exploited by a careless commit. Mitigation: the
  promote-via-CLI flag (`--promote <id>`) is the canonical path;
  the log-comment parser is a convenience and can be disabled.
- **R-A.3 (low):** splitting the attempts counter means existing
  state files need migration. Mitigation: a `_migrate_state(state)`
  shim runs once on load if `attempts[task_id]` is an int (old shape).

### Test scenario

> The loop picks an `agent_creative` task that produces a deliverable.
> Before Phase 5: the executor returns DONE_WITH_CONCERNS; the picker
> appends to `done_task_ids`; the next tick picks something else. The
> deliverable sits in `data/ralph_agent_*.md` un-reviewed forever.
>
> After Phase 5: the executor returns DONE_WITH_CONCERNS; the picker
> sees DWC and routes to `state['review_pending_task_ids']`; the task
> is NOT appended to `done_task_ids`. The next tick still avoids it
> (the picker filters by "not in review_pending"). The operator runs
> `python ralph_tick.py --promote <id>` after reading the deliverable;
> the task moves to `done_task_ids` and is logged in `ralph_log.md`
> as "PROMOTED 2026-05-25T... by operator".

This is the canonical test the xfail scaffold (Phase 4) will encode.

---

## §B · Observability

### Problem

The operator cannot see what the loop is doing while it runs. Today:

- `ralph_state.json::in_progress` shows the current task id, written
  at tick start.
- `ralph_log.md` gets appended to at tick end (markdown table row).
- `data/ralph_*.md` artefacts appear when written.

There is no live progress signal, no token-rate metric, no per-tick
duration histogram, no "the loop is hung on Neo4j connect" surface.
The operator finds out the loop is unhealthy by noticing the commit
cadence has stopped — usually minutes-to-hours later.

The audit didn't explicitly cite this, but the audit's "62% DWC absorbed
silently" failure mode is partly an observability problem: the operator
can't tell DWC apart from DONE in `ralph_state.json` without parsing
the history list.

### Proposed solution

**B.1 — Heartbeat file written by `tick()` while executor runs.**

```python
# ralph_loop.py::tick() — early in the function, before executor runs:
heartbeat = ROOT / "data" / ".ralph_heartbeat.json"
heartbeat.write_text(json.dumps({
    "tick_id": tick_id,                  # NEW: stable id for this tick
    "task_id": task["id"],
    "type": task["type"],
    "started_at": result.started_at,
    "executor": task["type"],
    "phase": "executor_running",         # one of: picking, executor_running,
                                          # acceptance_check, quality_gate,
                                          # post_tick
    "pid": os.getpid(),
    "host": socket.gethostname(),
}, indent=2))
# update `"phase"` field at each transition; delete at tick end.
```

A small CLI: `python ralph_tick.py --watch` reads this file every 2s
and prints a one-line status. Operator (or a separate notebook/page)
can poll it remotely.

**B.2 — Per-tick duration + token telemetry in `ralph_state.json`.**

The existing `api_usage.window` (24h-rolling) is fine for cost; add a
parallel `tick_durations.window` (24h-rolling) for latency:

```python
state["tick_durations"]["window"].append({
    "ts": result.finished_at,
    "task_id": task["id"],
    "type": task["type"],
    "executor_sec": executor_dur,
    "acceptance_sec": acceptance_dur,
    "quality_gate_sec": qgate_dur,
    "total_sec": total_dur,
    "status": result.status,
})
```

Useful for spotting degradation (the `app_free.py` slowdown that took
2 days to diagnose would have surfaced immediately if per-tick total
duration was visible).

**B.3 — A `python ralph_tick.py --status` enhancement.**

Today's `--status` prints:

```json
{
  "tick_count": 121,
  "last_tick": "2026-05-12T17:44:25.800667+00:00",
  "in_progress": null,
  ...
}
```

Add to the status output:

```json
{
  ...,
  "review_pending": ["task_a", "task_b"],          # NEW
  "spec_broken_quarantine": ["task_c"],            # NEW (split from quarantine)
  "work_failed_quarantine": [],                     # NEW
  "tick_duration_p50_sec": 14.2,                    # NEW (from window)
  "tick_duration_p95_sec": 71.5,                    # NEW
  "daily_api_calls": 17,                            # NEW (existing api_usage)
  "halted_via_RALPH_STOP": true                     # NEW
}
```

**B.4 — A markdown digest file the operator can `cat` to see the
last 24h.**

`python scripts/ralph_digest.py` writes `data/ralph_digest.md`:

```markdown
# Ralph digest — 2026-05-25 to 2026-05-26 (24h)

- ticks: 19 (8 DONE, 6 DONE_WITH_CONCERNS → review_pending, 5 FAILED)
- avg tick: 14.2s · p95: 71.5s · longest: 312s (from_X)
- 6 tasks awaiting review:
  - from_X: design doc 4.1KB
  - from_Y: design doc 6.7KB
  - ...
- 0 new quarantined
- 24h API calls: 17 (cap 50)
```

Generated by a separate script; the loop does NOT run it (to keep the
loop's scope as code/eval/refactor only).

### Alternatives considered

- **Stand up Langfuse / LangSmith.** Retrofit plan Phase 1 lists this
  for LLM observability. Out of scope for Phase 5 — the loop is not
  the LLM agent, and most ticks make zero LLM calls. **Deferred.**
- **Write to a SQLite database instead of JSON.** Considered. The
  current shape is one file + one log. A SQLite addition would force
  every reader (`status`, `--watch`, `--digest`, `tick_finalize.py`)
  through a schema migration. **Rejected** for the simpler JSON +
  heartbeat approach.
- **Stream to a websocket the operator's terminal subscribes to.**
  Overkill for the operator's actual cadence (poll every few minutes,
  not every second). **Rejected.**

### Risks

- **R-B.1 (low):** the heartbeat file is gitignored but lives in `data/`.
  A future cleanup pass might delete it. Mitigation: explicit `.gitignore`
  entry; documentation in RALPH.md.
- **R-B.2 (medium):** the duration telemetry adds ~50 bytes per tick
  to `ralph_state.json`. Capped at 24h window (~40 ticks at current
  cadence), so ~2 KB; negligible. The full `history` list is already
  capped at 500.
- **R-B.3 (low):** if `tick()` crashes mid-executor, the heartbeat
  file becomes stale (phase="executor_running" forever). Mitigation:
  `--watch` flags a heartbeat older than 2× max executor timeout as
  STALE; operator can `rm data/.ralph_heartbeat.json` manually.

### Test scenario

> The operator starts a tick at T=0 that runs for 300s. At T=10s,
> they want to know if it's still alive or wedged on Neo4j.
>
> Before Phase 5: they parse `ralph_state.json::in_progress` to see
> the task id and infer from the absence of a new commit that it's
> running. No signal on health.
>
> After Phase 5: they run `python ralph_tick.py --watch` and see:
> `tick-20260525-180000-a3b8c1d2 · from_X · phase=executor_running ·
> running for 12.3s (median 14.2s, p95 71.5s)`. They know it's
> healthy. At T=200s, the same output reads:
> `... · phase=executor_running · running for 200.0s (>> p95 71.5s) · STALL?`.

---

## §C · Stop discipline

### Problem

`data/RALPH_STOP` is the only halt mechanism that's tested in practice
(it's checked at `scripts/CRON_BRIEF.md` step 1). `ralph_run.py` has
`--max-calls-per-day` and `--max-tokens-per-day` daily caps but no
loop-level "rate degradation" pause or metric-regression auto-halt.

Three failure modes the existing stop discipline doesn't cover:

1. **Quality regression cascade.** A bad commit causes 5 consecutive
   ticks to fail their `python_test_passes` gate. Today: the loop
   keeps ticking, accumulating retries and 3-strikes quarantines.
   Post-Phase-5: should auto-halt and write a clear marker.
2. **Metric regression slow burn.** If `execute_eval` shows a
   monotonic drop in the v2 hard_pass_rate over the last 5 ticks
   (each tick within the 5% regression_pct gate, so no individual
   tick is REGRESSION, but the trend is bad), the loop today doesn't
   notice.
3. **`RALPH_STOP` check is only in CRON_BRIEF.md, not in
   `ralph_loop.py::tick()`.** If the loop is invoked directly (e.g.
   `python ralph_run.py` instead of via the cron subagent), it does
   NOT check `RALPH_STOP`. Belt-and-braces fail.

### Proposed solution

**C.1 — Loop-level `RALPH_STOP` check in `ralph_loop.py::tick()`.**

```python
# At the very top of tick():
if (ROOT / "data" / "RALPH_STOP").exists():
    print("[ralph] HALTED by data/RALPH_STOP. Tick exits.")
    return None
```

Two-layer check (CRON_BRIEF step 1 + this) makes the halt belt-and-braces.

**C.2 — Quality regression cascade auto-halt.**

```python
# After each tick, in ralph_loop.py::tick() post-save:
recent = state["history"][-5:]
fails = [h for h in recent if h.get("status") in {"FAILED", "REGRESSION"}]
if len(fails) >= 5:
    halt_path = ROOT / "data" / "RALPH_STOP_AUTO"
    halt_path.write_text(
        f"Auto-halt at {result.finished_at} — 5 consecutive failures.\n"
        f"Last 5 task ids:\n" +
        "\n".join(f"- {h['task_id']}: {h['status']}" for h in recent) +
        "\n\nManual remediation required. Delete this file AND data/RALPH_STOP\n"
        "if you want to resume.\n"
    )
    print(f"[ralph] AUTO-HALT — 5 consecutive failures. Wrote {halt_path}.")
```

The `RALPH_STOP_AUTO` file is separate from `RALPH_STOP` so the
operator can tell apart "operator paused for design work" from "loop
self-paused because something is broken". Both halt the loop.

**C.3 — Metric regression trend auto-halt.**

Only applies to `eval`-type ticks. After each eval, check the last 5
eval ticks' `metric_after`:

```python
# Only after an eval tick:
eval_window = [h for h in state["history"] if h["type"] == "eval"][-5:]
metrics = [h.get("metric_after") for h in eval_window]
metrics = [m for m in metrics if m is not None]
if len(metrics) >= 5 and metrics[0] - metrics[-1] >= 0.05 * metrics[0]:
    # 5% cumulative drop across 5 eval ticks — slow burn.
    # Auto-halt with same mechanism as C.2.
    ...
```

**C.4 — Operator-friendly halt CLI.**

```bash
python ralph_tick.py --pause "reason: design work"   # writes RALPH_STOP
python ralph_tick.py --resume                          # removes RALPH_STOP_AUTO only
python ralph_tick.py --resume-all                      # removes both
```

The `--pause` writes a freshly-dated `RALPH_STOP` with the operator's
reason; `--resume-all` requires confirmation (an explicit flag, not
just a y/N prompt — the loop's restart is a real decision).

### Alternatives considered

- **Add a per-tick `--max-failures-in-window N` flag.** Equivalent to
  C.2 but pushes the responsibility to the operator who launches the
  cron. **Rejected** for the always-on default.
- **Run the quality regression check on EVERY tick, not just eval.**
  Considered. The 5-consecutive-failure rule already covers code
  regressions (cleanup tasks failing the quality gate); a separate
  per-eval trend signal is cheap. **Adopted both.**
- **Use signal handlers (`SIGINT`/`SIGTERM`) for clean shutdown.**
  Different mechanism — handles "operator hit Ctrl-C" but not "loop
  detects unhealthy state and wants to stop itself". **Adopted in
  addition** (graceful shutdown in §G integration).

### Risks

- **R-C.1 (medium):** the 5-consecutive-fail threshold is arbitrary;
  a single bad commit could trigger it. Mitigation: clear console
  message, the operator can `rm data/RALPH_STOP_AUTO` and inspect.
  Tunable via env var `RALPH_AUTO_HALT_FAILURES` (default 5, set to
  999 to disable).
- **R-C.2 (low):** the trend check (C.3) could false-positive on
  normal eval noise. Mitigation: requires monotonic 5% drop across
  the FULL window, not just 5% drop start-to-end. Conservative
  enough that operator's existing eval cadence wouldn't trigger
  spurious halts.

### Test scenario

> A bad commit lands on main that breaks the answer cache. The next
> eval tick scores 0.65 (was 0.74 baseline). Each subsequent eval
> tick stays around 0.65–0.67. None individually trip the 5%
> regression_pct (which is per-tick relative). After 5 eval ticks,
> the metric_after sequence is [0.74, 0.71, 0.68, 0.66, 0.65] — a
> 12% cumulative drop.
>
> Before Phase 5: loop keeps ticking; operator notices the eval
> dashboard drifted at the next morning review.
>
> After Phase 5: at tick 5 of the cascade, `tick()` detects the
> trend, writes `data/RALPH_STOP_AUTO`, the next tick sees it and
> exits. Operator's `python ralph_tick.py --status` shows
> `halted_via_RALPH_STOP_AUTO: true` and the reason file.

---

## §D · Scope discipline

### Problem

This is the section most-completely covered by the existing
`docs/PHASE_5_LOOP_TAMING_PLAN.md` (item 18). The audit's "rewriting
its own scaffolding" + "research summarisation" + "ADR backfill" findings
all map to scope creep that the existing plan strips.

The gap: the plan describes **what stays/goes** in `EXECUTORS` dict
but does NOT describe **what stays/goes in `CRON_BRIEF.md`**. The
cron brief is what actually orchestrates the surrounding meta-system
(MAINT every 6th tick, research every 3rd, synthesis every 24th). Today
the brief delegates to `scripts/memory_hygiene.py`, `scripts/haiku_prep.py`,
`scripts/sonnet_prep.py`, `scripts/tick_finalize.py`, `scripts/state_snapshot.py`.

If `agent_creative` is removed from `EXECUTORS` but `CRON_BRIEF.md`'s
RESEARCH step (processing items from `data/research_neo4j_crawl/`)
still fires, then the loop still produces research-summarisation
work — just by a different path.

### Proposed solution

**D.1 — Adopt the existing Phase 5 plan item 18 verbatim.**

```python
# ralph_loop.py::EXECUTORS post-Phase-5:
EXECUTORS = {
    "eval":            execute_eval,
    "cleanup":         execute_cleanup,
    "cypher_analysis": execute_cypher_analysis,
    "cache_op":        execute_cache_op,         # NEW (stub today)
    "embed_op":        execute_embed_op,         # NEW (stub today)
    "regression":      execute_regression,       # NEW (Phase 5)
    "triangulation":   execute_triangulation,    # NEW (Phase 5)
    # AGENT_CREATIVE explicitly REMOVED from cron-dispatch.
    # It stays in code for `RALPH_AGENT_BACKEND=manual` operator use.
}
```

`prompt_variant` remains a stub; can only be invoked manually until a
real executor exists (Phase 5 plan item 18: "Restricted; requires
`python_test_passes` against v2 eval").

**D.2 — Strip `CRON_BRIEF.md` to code/eval/refactor.**

Rewrite `scripts/CRON_BRIEF.md` to remove:

- The MAINT every-6th memory-hygiene block (lines 71–75 of CRON_BRIEF.md
  call `scripts/memory_hygiene.py`).
- The MAINT every-6th ADR-drift detection block (lines 76–77).
- The MAINT every-24th synthesis sub-step (lines 77–78).
- The entire RESEARCH cycle (step 5, lines 58–69) — research summarisation
  is the audit's "ADR backfill"-adjacent failure mode.

What stays:

- Halt check (step 1).
- Sync (step 2).
- IMPL tick procedure (step 4) — but with `agent_creative` removed.
- End-of-tick housekeeping reduced to: `python scripts/state_snapshot.py`
  ONLY (no `tick_finalize.py` with its 12-tick MORNING_REPORT auto-gen).
- Commit + push (step 8).

The MAINT cycle becomes "every Nth tick, run `prune_graveyard()`" — the
Phase 5 plan item 20. Nothing else.

**D.3 — Remove auxiliary scripts from the loop's dependencies.**

The Ralph loop should NOT depend on:

- `scripts/haiku_prep.py` (Haiku classification of `data/proposed_tasks.yaml`
  entries — this is the proposal-staging system the loop should stop
  exercising).
- `scripts/sonnet_prep.py` (Sonnet pre-warming of agent_creative tasks
  — agent_creative is gone from cron).
- `scripts/memory_hygiene.py` (PATTERN promotion, SESSION_LOG drift,
  vault MOC refresh, ADR audit — all meta-system maintenance).
- `scripts/state_snapshot.py` STAYS (cheap, useful, idempotent).
- `scripts/tick_finalize.py` is rewritten to ONLY call
  `state_snapshot.py` — no MORNING_REPORT.md, no vault_update.py.

These scripts remain in the repo for OPERATOR use; they just don't
fire from the cron path.

**D.4 — Lock-down: the loop cannot edit its own scaffolding.**

A new `triangulation`-class gate (Phase 5 plan item 21 already covers
the classifier case): refuse any commit from a Ralph tick that
modifies any of:

- `ralph_loop.py`
- `ralph_tick.py`
- `ralph_run.py`
- `ralph_backlog.yaml` (except via the manual proposal-review CLI flow)
- `scripts/CRON_BRIEF.md`
- `data/RALPH_STOP*`
- `tests/test_ralph_*.py` (regression tests get added by `regression`
  task type, which has its own narrow gate — see §F)

Detection: `git diff --name-only HEAD~1 HEAD` from inside the
post-tick gate; reject if any of the forbidden paths appear.

Bypass: `# scaffolding-exempt: <operator-reason>` in the commit body,
counts against a weekly budget (1/week, logged).

### Alternatives considered

- **Allow `agent_creative` in cron but force every output to require
  manual promote (§A.1).** This is equivalent in effect — the
  designed-doc throughput would drop to whatever the operator can
  review. Slightly riskier (the executor still runs, still costs
  OpenRouter quota). **Adopted as backup** (the OpenRouter knob),
  but **removing from EXECUTORS is the primary fix.**
- **Move CRON_BRIEF.md research/MAINT logic to a separate cron, not
  the Ralph loop.** Considered. Risk: operator runs both crons by
  accident; the loop's "scope is code/eval/refactor" promise weakens.
  **Rejected** in favour of "delete the scope from CRON_BRIEF.md
  entirely; if the operator wants research summarisation, they invoke
  it manually."
- **Keep `agent_creative` in EXECUTORS but require `acceptance:
  python_test_passes` on every task.** Wouldn't work: most
  `agent_creative` tasks produce a design doc (an .md file), not test
  code, so `python_test_passes` is the wrong gate. **Rejected.**

### Risks

- **R-D.1 (high):** the operator depends on `scripts/memory_hygiene.py`
  and `scripts/tick_finalize.py` for several non-Ralph workflows (state
  snapshot, session log, vault). Mitigation: scripts stay in repo,
  callable manually. The CRON_BRIEF change is what removes them from
  the loop's hot path.
- **R-D.2 (medium):** ADRs 0013–0044 are machine-authored and the
  retrofit plan Phase 9 item 35 demotes them to Decision Logs. Phase
  5 stripping ADR-write from the loop's diet pre-emptively, before
  the demotion is done, means ADRs 0045+ won't get auto-created. This
  is FINE — the audit's category-error finding makes the auto-creation
  itself the bug.
- **R-D.3 (low):** the scaffolding-edit lockdown could false-positive
  on legitimate operator-driven Ralph commits (e.g. the operator does
  a small `ralph_loop.py` cleanup via a Ralph `cleanup` task). Bypass
  tag handles this.

### Test scenario

> A Ralph `cleanup` task tries to edit `ralph_loop.py::HISTORY_CAP`
> from 500 to 200. The executor runs, the smoke import passes, the
> pre-commit hook fires.
>
> Before Phase 5: commit lands. Loop self-modified.
>
> After Phase 5: the scaffolding-edit lockdown gate detects
> `ralph_loop.py` in the diff, refuses the commit. Console:
> `[ralph] SCAFFOLDING-EDIT-REJECT: ralph_loop.py in diff. Add
> "# scaffolding-exempt: <reason>" to the commit body or revert.`
> Operator either bypasses with reason or reverts. The loop does NOT
> rewrite its own scaffolding.

---

## §E · Resumability

### Problem

The retrofit plan Phase 11 says "delete `RALPH_STOP` in the same
commit that re-enables cron." That's clear on the file mechanic but
silent on:

- Which backlog tasks are eligible to be picked first on restart?
- How does the loop verify the v2 eval is now the gating metric?
- Does the operator get a "fresh start" or "resume from last state"?

A naïve restart picks the highest-priority pending task in
`ralph_backlog.yaml` — which might be a stale `agent_creative` task,
or a task whose `acceptance:` block uses `file_min_bytes` (the
audit's anti-pattern), or a task whose `metric: avg_unique_cites_per_q`
references the retired metric.

### Proposed solution

**E.1 — A pre-restart audit script.**

`python scripts/ralph_restart_audit.py` (new) walks
`ralph_backlog.yaml` and emits a report:

```
=== Ralph restart audit — 2026-05-26 ===

Tasks NOT in done_task_ids: 18
  ✅ Acceptable for restart: 4
    - regression_test_for_X (regression, python_test_passes)
    - cleanup_dead_code_Y (cleanup, python_test_passes)
    - ...
  ❌ Blocked by Phase 5 rules: 14
    - propose_X_redesign (agent_creative — type removed from cron)
    - audit_indexes (cleanup, no acceptance:)
    - re-eval_baseline (eval, metric=avg_unique_cites_per_q — retired)
    - ...

⚠ Tasks awaiting review_pending (DWC from pre-pause): 6
  Operator: review + promote or delete before restart.

Open questions for operator:
  - 14 backlog tasks blocked. Edit or remove from backlog before restart.
  - 6 review_pending. Review or move to skipped.
  - data/RALPH_STOP present (operator-paused).
  - data/RALPH_STOP_AUTO present? No.
```

**E.2 — Restart requires explicit gate.**

`python ralph_tick.py --resume-all` (from §C) requires that
`ralph_restart_audit.py` was run and emitted "READY" since the last
commit touching `ralph_backlog.yaml`. Implementation: the audit
writes `data/.ralph_restart_audit_OK` with the backlog file's SHA;
`--resume-all` reads it and rejects if the SHA doesn't match.

This is the Phase 5 plan's "operator approves the restart explicitly
(one commit, one human review)" requirement, made mechanical.

**E.3 — Loop state preservation across pauses.**

Today, `ralph_state.json` is preserved across pauses; the loop resumes
on the same `done_task_ids`, `attempts`, etc. This is correct.

Phase 5 design EXPLICITLY confirms:

- `done_task_ids` is preserved.
- `attempts` is **reset to {}** on resume (a paused task gets a fresh
  3-strikes window — fair on a tamed loop).
- `history` is preserved (FIFO-capped at 500).
- `api_usage.window` 24h-rolling is preserved (covers the case where
  pause was < 24h).
- `review_pending_task_ids` (new from §A) is preserved; operator
  reviews them as part of E.1's audit.

**E.4 — Loop on-resume self-check.**

When `tick()` runs after `RALPH_STOP` (and `RALPH_STOP_AUTO` if
applicable) has been removed, the FIRST thing it does is:

1. Re-run `quality_gate()` — confirm core modules import.
2. Run `python -m pytest tests/ -q --maxfail=1` — confirm a clean
   green bar (post-Phase 1 of retrofit).
3. Check that `data/eval/v2/SCHEMA.md` exists and that the default
   `execute_eval` metric is `hard_pass_rate`, not
   `avg_unique_cites_per_q`. If not, abort with clear message.

Any failure → write `data/RALPH_STOP_AUTO` with reason; do not pick a task.

### Alternatives considered

- **Force a backlog rewrite on every restart.** Considered. Operator
  cost too high; the existing backlog has lots of usable signal.
  **Rejected.**
- **Hash-pin the backlog file as a restart precondition.** That's E.2.
  **Adopted.**
- **Bare-bones restart: delete RALPH_STOP, next tick runs.** Simplest.
  Rejected because the audit's failure-mode-not-fixed risk is too
  high — restart without explicit gate would re-encode the old
  problems on whatever tasks the picker grabs first.

### Risks

- **R-E.1 (medium):** the pre-restart audit script could be brittle
  if `ralph_backlog.yaml` evolves. Mitigation: small, deterministic,
  pinned to current backlog schema; doesn't need to be perfect — just
  enumerate flagged tasks for the operator.
- **R-E.2 (low):** `data/.ralph_restart_audit_OK` could be stale if
  the operator edits `ralph_backlog.yaml` in two commits and runs the
  audit between. Mitigation: SHA-pin to the YAML file specifically;
  audit auto-invalidates on any backlog edit.

### Test scenario

> Operator decides to restart after Phase 5 lands. They run
> `python scripts/ralph_restart_audit.py`. Output:
> "14 blocked, 6 review_pending — fix before --resume-all."
>
> They edit `ralph_backlog.yaml`: delete the 6 agent_creative tasks
> from the queue (or recategorise as `manual`), add `acceptance:
> python_test_passes` to the 5 cleanup tasks, change the eval task's
> metric to `hard_pass_rate`.
>
> They re-run audit. Output: "READY (8 tasks eligible for first
> tick; backlog SHA matched)."
>
> They delete `data/RALPH_STOP`, run `python ralph_tick.py --resume-all`.
> The first tick runs `quality_gate()` + `pytest --maxfail=1` + v2-eval-default
> check. All pass. The picker selects the highest-priority eligible
> task. Loop is alive again under new discipline.

---

## §F · Quality bar

### Problem

The audit's TDD-1 finding: "QKG's loop is brief → design doc → commit.
No failing test defines done." The retrofit plan's solution is
`python_test_passes` (Phase 2 item 8) — already implemented in
`verify_acceptance` but used by only ~5 of the 80+ backlog tasks.

Three specific quality-bar gaps remain:

1. **The default eval metric is the retired one.** `execute_eval`
   defaults to `avg_unique_cites_per_q`; the v2 hard-pass rate is
   not wired.
2. **`python_test_passes` runs `pytest <path>` but doesn't enforce
   a CLEAN suite.** A task can specify `python_test_passes:
   tests/test_my_fix.py` and ignore the rest of the suite. A
   bad commit that fixes the targeted test but breaks an unrelated
   one would still pass the gate.
3. **The xfail discipline is operator preference but not encoded in
   the loop.** Operator's CLAUDE.md: "TDD with the xfail pattern for
   bug fixes". The Phase 5 plan introduces a `regression` task type
   for "removes an xfail marker once a fix lands"; the design
   proposal must specify the gate.

### Proposed solution

**F.1 — Default `execute_eval` to v2 hard-pass rate.**

```python
# ralph_loop.py::execute_eval — change defaults:
script = spec.get("script", "scripts/run_v2_eval.py")  # NEW
metric = spec.get("metric", "hard_pass_rate")           # WAS avg_unique_cites_per_q
compare_to = spec.get("compare_to", "data/eval/v2/baseline_capable_model.jsonl")
```

`_read_eval_metrics` gains:

```python
if metric == "hard_pass_rate":
    # Read v2 JSONL, count hard-pass per the asserts.
    ...
```

The legacy metrics remain supported (so old `eval` tasks still work
when re-run for diagnostic), but the default changes. Operator can
opt back to v1 explicitly per-task via `spec.metric:
avg_unique_cites_per_q`.

**F.2 — `python_test_passes` enforces full-suite green.**

```python
# In verify_acceptance, when "python_test_passes" check runs:
# Run the targeted path AND a fast full-suite check.
for p in paths:
    proc = subprocess.run([sys.executable, "-m", "pytest", p, "-q", "--tb=short"], ...)
    if proc.returncode != 0:
        all_ok = False
        # ... detail ...
# THEN also run the full suite with --maxfail=1 (fast termination):
proc_full = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-q", "--maxfail=1", "--tb=short"],
    capture_output=True, text=True, timeout=600,
    cwd=str(ROOT),
)
if proc_full.returncode != 0:
    all_ok = False
    out.append({"check": "python_test_passes tests/ (full-suite check)",
                "passed": False, "detail": ...})
```

Overhead: ~15s per gate run today (208 tests, 17.58s clean). The
`--maxfail=1` ensures we don't pay the full cost if there's a
regression.

**F.3 — `execute_regression` task executor.**

A new task type for the xfail-pattern operator workflow:

```yaml
- id: fix_shuaib_curly_apostrophe
  type: regression
  priority: 80
  description: "Flip tests/regression/test_shuaib_apostrophe.py from xfail to pass after matcher fix"
  spec:
    test_path: tests/regression/test_shuaib_apostrophe.py
    acceptance:
      python_test_passes: tests/regression/test_shuaib_apostrophe.py
    commits_code: true
```

`execute_regression` (`ralph_loop.py::execute_regression`):

1. Read the target test file.
2. Confirm it contains `@pytest.mark.xfail(strict=True)` somewhere.
3. Run pytest at that path — expect it to PASS (the fix has already
   landed in an earlier commit; this tick just removes the marker).
4. If it passes, remove the `xfail(strict=True)` line from the test
   file via a deterministic in-place edit.
5. Run pytest again at that path — must still PASS.
6. Run the full suite via the F.2 gate.
7. Commit with message `regression: remove xfail from <test_path> after fix landed in <prior_sha>`.

This is the canonical "Beck Red → Green → Refactor" loop, fitted to
the operator's xfail discipline.

**F.4 — Triangulation gate from Phase 5 plan item 21.**

Adopt verbatim from `docs/PHASE_5_LOOP_TAMING_PLAN.md`:

```python
def acceptance_classifier_or_routing_change(task, diff):
    classifier_signals = detect_classifier_additions(diff)
    if not classifier_signals:
        return AcceptanceSuccess()
    new_test_count = count_new_tests_in_diff(diff)
    if new_test_count < 2:
        return AcceptanceFailure(...)
    return AcceptanceSuccess()
```

Detection heuristics from the plan. Bypass tag: `# triangulation-exempt:
<reason>` with a weekly budget (3/week, logged to Codebase Patterns block).

### Alternatives considered

- **Don't add full-suite check; trust the targeted test.** The
  audit's reason for the gate (`bs7n`) is exactly this: "broken
  Python in any of the core modules and the live agent loop breaks".
  Trust-the-targeted-test would re-encode the audit's gap. **Rejected.**
- **Use property-based testing (Hypothesis) in the regression
  executor.** Retrofit plan additions list Hypothesis as a Phase 1
  add. **Deferred** — Phase 5 design specifies the regression
  executor shape; Hypothesis integration is a later sub-phase.
- **Default eval to BOTH v1 and v2 metrics (run both).** Considered.
  Doubles tick duration; the v1 metric is the retired one per the
  retrofit plan. **Rejected** in favour of clean cut.

### Risks

- **R-F.1 (medium):** the full-suite gate adds ~15–20s per gated tick.
  At current cadence (5–10 ticks/day), ~2–3 min/day total. Negligible.
  At a possible-future cadence of 50 ticks/day, ~15 min/day. Still
  fine.
- **R-F.2 (medium):** `execute_regression`'s "remove xfail line"
  mechanic is fragile (regex on `@pytest.mark.xfail(strict=True)`).
  Mitigation: refuse to run if the line shape doesn't match exactly;
  fall back to operator manual edit.
- **R-F.3 (low):** the v2 eval doesn't yet have a script that produces
  `hard_pass_rate` as a single number. Mitigation: `scripts/run_v2_eval.py`
  is created as part of Phase 5 sub-phase 4 (the regression executor)
  with a simple "count hard_pass=true / total" tally.

### Test scenario

> A bug fix for the Shuaib-apostrophe matcher landed in commit
> `5b03255` (already on main). The corresponding xfail test at
> `tests/regression/test_shuaib_apostrophe.py` still has the xfail
> marker. The operator creates a `regression` task in `ralph_backlog.yaml`.
>
> Before Phase 5: no `regression` task type exists; operator does
> the work manually.
>
> After Phase 5: the loop picks the task. `execute_regression`
> confirms the xfail marker is present, runs pytest at the path
> (currently xpass — the test passes despite xfail), removes the
> xfail line via in-place edit, re-runs pytest (still passes), runs
> the full-suite gate (208 → 209 tests, 0 fails), and commits with
> the canonical message. The Codebase Patterns block in `ralph_log.md`
> gets a "PATTERN: xfail removal for X after fix landed in Y" line.

---

## §G · Integration with rest of system

### Problem

The Ralph loop interacts with several recently shipped systems that
post-date the audit. The Phase 5 plan doesn't address how the tamed
loop fits with:

1. **The answer cache + its new BGE-M3 reranker.** Cache is now 1,607
   entries with `embedding_m3` per entry; `answer_cache.search_cache`
   does BGE-reranker-v2-m3 on top of cosine retrieval (commit
   `5cc0e6c`).
2. **The reasoning-memory subgraph.** 32K+ `:RETRIEVED` edges,
   per-trace `memory_path` props (commit `6b25d7f`'s spec; partially
   shipped).
3. **The v2 eval framework.** 57 questions + 15 held-out; capable-model
   baseline merged 2026-05-21; schema at `data/eval/v2/SCHEMA.md`.
4. **The cache schema enrichment fields** (commit `5cc0e6c`):
   `quality_score`, `cite_count`, `has_arabic`, `model_estimated`,
   `model_confidence`.

The loop today is oblivious to all of these. A `cache_op` task (stub)
would need to know about the cache's new shape; a `cypher_analysis`
task surfacing "underperforming questions" should know about
`tools_used_agent_equivalent` from the capable-model baseline.

### Proposed solution

**G.1 — Loop tasks reference v2 eval as canonical truth.**

Anywhere a Ralph task previously read `data/eval_v1_results.json` or
`data/answer_cache.json`, the post-Phase-5 default is:

- `data/eval/v2/baseline_capable_model.jsonl` (the 57 answers)
- `data/eval/v2/SCHEMA.md` (the assertion shape)
- `data/answer_cache.json` is still the operational cache, but the
  loop reads it through `answer_cache.search_cache` (with reranker)
  rather than direct JSON parse — so cache improvements automatically
  propagate.

**G.2 — `cache_op` executor scope.**

The stub `cache_op` task type becomes real:

```python
def execute_cache_op(task, state, result):
    """
    Tasks: cache cleanup, re-rerank, recompute fields, prune.
    spec.operation: 'recompute_embeddings' | 'prune_by' | 'rerank_window' | ...
    Always read-only-then-write; never destructive without backup.
    """
    ...
```

Allowed operations:

- `recompute_embeddings` — re-embed N entries with a new model
- `prune_by` — apply a Cypher-like filter (e.g. `score<X AND validity<Y`)
  and write a paper trail in `data/research/cache_pruned_<date>.jsonl`
- `rerank_window` — re-rerank top-K with current reranker

The executor refuses to run if `data/answer_cache.json` doesn't have
a backup younger than 48h (`data/answer_cache.json.bak`). The Phase
3 retrofit work (commit `5cc0e6c`) established the backup pattern;
the executor enforces it.

**G.3 — Reasoning-memory subgraph integration.**

A new spec field: `reads_graph: true` declares the task touches the
reasoning-memory subgraph (RETRIEVED edges, ReasoningTrace nodes,
Query nodes). The executor:

- Refuses to run if `NEO4J_URI` is unreachable (avoids the cleanup-FAILED
  cascade from §3's empirical data).
- Logs the Cypher executed to `data/ralph_cypher_log.md` (audit's
  Phase 7 item 30 hint, applied to the loop's own footprint).
- Adds the result row count to `result.notes`.

**G.4 — The loop's own reasoning-memory writes.**

Today, the loop does NOT write to the reasoning-memory subgraph
(reasoning_memory.py is for app_free.py's live queries). Phase 5
keeps it that way — the loop's outputs go to files (`ralph_log.md`,
`ralph_state.json`, `data/ralph_*.md`), not the graph. The graph is
for the live agent; the loop is for the build system. Crossing the
streams was an early temptation that the audit reinforced; Phase 5
formalises the split.

**G.5 — Bootstrap fixture awareness.**

The reconnaissance noted ([[state_2026-05-21]] open chip 1) the
fresh-worktree friction: `.env`, `data/answer_cache.json`, prompt
files. The Phase 5 loop should NOT depend on `data/answer_cache.json`
existing — `execute_eval` against the v2 baseline reads the JSONL
file directly, which IS tracked in git. This makes the loop runnable
on a fresh CI checkout (e.g. GitHub Actions, which the retrofit plan's
"GitHub Actions CI" line mentions but doesn't implement).

### Alternatives considered

- **Have the loop write its own RETRIEVED-style edges for tick
  outcomes.** Considered. Crosses the loop/runtime stream the audit
  explicitly flagged. **Rejected.**
- **Cache invalidation: have the loop wipe answer_cache.json on
  schema migration.** Destructive; rejects the retrofit plan's
  "don't restart from scratch" guidance. **Rejected.**
- **Skip v2-eval integration; let the operator wire it manually
  later.** Would leave §F.1 (default eval metric) un-fixed. **Rejected.**

### Risks

- **R-G.1 (medium):** `data/eval/v2/baseline_capable_model.jsonl` is
  a single file; the v2 eval framework hasn't been hardened. If the
  schema changes, every Ralph eval task breaks. Mitigation:
  Phase 5 sub-phase 4 includes a tiny `data/eval/v2/SCHEMA.md` pin
  + checksum.
- **R-G.2 (low):** the `reads_graph: true` enforcement could false-
  positive on tasks that incidentally import `reasoning_memory.py`
  but don't actually query Neo4j. Mitigation: declarative spec
  field, not auto-detected.

### Test scenario

> An `eval` task is picked. `execute_eval` reads `data/eval/v2/baseline_capable_model.jsonl`
> (which IS in git). For each of the 57 questions, the task hits
> `/chat` against the live `app_free.py` server, scores against the
> assert sheet, and produces a single `hard_pass_rate` number.
>
> Before Phase 5: `execute_eval` reads `eval_v1.py` results, reports
> `avg_unique_cites_per_q`. The metric the audit retired is the
> loop's primary signal.
>
> After Phase 5: `execute_eval` reads the v2 baseline, reports
> `hard_pass_rate` (e.g. 0.74). Operator's eval ticks now anchor
> against the same metric the retrofit plan made canonical.

---

## Bringing it together

The seven sections above propose **eight concrete changes**:

1. (§A.1) Drop `DONE_WITH_CONCERNS` from `TERMINAL_OK`.
2. (§A.2) Require `acceptance:` on every executable task.
3. (§A.3) Split the attempts counter (`needs_context` vs `failed_or_blocked`).
4. (§B) Heartbeat file + duration telemetry + `--watch` CLI + digest.
5. (§C) Loop-level `RALPH_STOP` check + auto-halt on 5 consecutive
   failures + metric trend halt.
6. (§D) `EXECUTORS` dict shrinks (retrofit plan item 18) + CRON_BRIEF.md
   strips MAINT/RESEARCH cycles + scaffolding-edit lockdown.
7. (§E) Pre-restart audit script + restart gate via backlog SHA-pin +
   on-resume self-check.
8. (§F) `regression` + `triangulation` task types + full-suite check +
   v2-eval default + triangulation gate.

Plus the system-integration adjustments in §G (mostly defaults and
spec-field discipline, not new code paths).

Atomicity: each of (1)–(8) is independently shippable. The phased
implementation plan (Phase 5 sub-phase doc, next document) splits
them across 4 sub-phases for review.

---

## Open design questions for the operator

Three questions whose answers don't change the proposal but do affect
sub-phase ordering:

**Q1. Should the scaffolding-edit lockdown apply to operator commits
too, or Ralph-only?** The retrofit plan's analogous question (open
question 3 in `PHASE_5_LOOP_TAMING_PLAN.md`) recommends Ralph-only
initially. This proposal adopts Ralph-only; the operator can edit
scaffolding freely. If post-restart the operator finds themselves
accidentally tripping the gate, promote to a pre-commit hook later.

**Q2. The pre-restart audit script (§E.1) — does it BLOCK restart
on warnings (`review_pending`, blocked tasks) or just emit them?**
Proposal default: warnings are surfaced; only ERRORS (no acceptance,
retired metric, agent_creative in queue) block. The SHA-pin gate
catches "operator hasn't reviewed since editing the backlog"; the
audit itself is read-only.

**Q3. Should the loop's first post-restart tick be DRY-RUN by
default?** Proposal default: no — once `RALPH_STOP` is removed, the
loop is live. But add a CLI knob `python ralph_run.py --max 1 --dry`
for a sanity check; the operator can run it manually before the cron
re-fires. The cron itself does not dry-run; that would defeat the
purpose.

The design proposal does not depend on the answers to these
questions. The implementation plan (next doc) is structured so any
of the three defaults can flip without re-ordering the sub-phases.
