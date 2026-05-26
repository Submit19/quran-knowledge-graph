# Phase 5 — Phased Implementation Plan

_Operationalises `phase5_design_proposal_2026-05-22.md` as 4 atomic
sub-phases that each fit in a single advisor session. Each sub-phase
flips a specific subset of the 30 xfail tests in
`tests/test_ralph_design_*.py` to passing. Each is independently
shippable behind operator review; the loop stays paused until all
four land + the operator runs Phase 11 restart._

Effort estimates are based on "one focused advisor + fresh-local-session
cycle including code, tests-flipped-from-xfail, and an operator-review
PR". I deliberately overshoot — every sub-phase that doesn't bleed past
its estimate goes faster, never slower.

---

## Sub-phase order

```
Sub-phase 1 (S/M) — Failure-mode kernel
   →  Sub-phase 2 (M) — Observability + Stop discipline
        →  Sub-phase 3 (L) — Scope strip + Quality bar
             →  Sub-phase 4 (M) — Resumability + Integration + Pre-restart
```

Order rationale:

- **Failure-mode kernel first** because every other sub-phase assumes
  the picker handles DWC and missing acceptance correctly. Without
  sub-phase 1, sub-phases 2–4 can't be safely exercised even in dry-run.
- **Observability + Stop second** because sub-phases 3 and 4 introduce
  new tick types (regression / triangulation) whose first dry-runs
  benefit from heartbeat + auto-halt being live.
- **Scope strip + Quality bar third** is the biggest sub-phase — it's
  the one where the EXECUTORS dict actually shrinks and the v2 eval
  becomes the default metric. Heavy on test churn (5 + 4 = 9 xfail
  tests flipped).
- **Resumability + Integration last** because it depends on every
  prior change (the audit script, the on-resume self-check, and the
  v2-baseline references all reference work shipped in sub-phases
  1–3). Lands in the same commit that the operator uses to restart
  the loop (Phase 11).

---

## Sub-phase 1 — Failure-mode kernel

**Definition-of-done:**

- `ralph_loop.TERMINAL_OK = {DONE, SKIPPED}` (DWC removed)
- A `TERMINAL_NEEDS_REVIEW = {DONE_WITH_CONCERNS}` set or equivalent named constant
- `state['review_pending_task_ids']` list populated when a tick ends DWC
- `pick_next_task` filters out tasks in `review_pending_task_ids`
- `python ralph_tick.py --promote <id>` CLI flag moves a task from
  `review_pending` to `done_task_ids`
- `verify_acceptance` hard-fails when no `acceptance:` block (instead
  of soft-pass)
- `state['attempts'][task_id]` becomes a dict with `needs_context` and
  `failed_or_blocked` sub-counters
- `_migrate_state` helper handles legacy int-shape on load
- The picker reads the dict shape; `MAX_ATTEMPTS` checks the SUM
  (operator can opt to check either individual counter later — the
  default behaviour stays the same as today)
- Quarantine reason exposed via either two named constants or a
  helper that returns the reason

**xfail tests flipped to passing:**

- `tests/test_ralph_design_001_dwc_not_terminal_ok.py::test_dwc_not_in_terminal_ok`
- `tests/test_ralph_design_001_dwc_not_terminal_ok.py::test_review_pending_set_exists`
- `tests/test_ralph_design_002_acceptance_required.py::test_task_with_no_acceptance_block_fails`
- `tests/test_ralph_design_002_acceptance_required.py::test_task_with_empty_acceptance_list_fails`
- `tests/test_ralph_design_003_attempts_split.py::test_attempts_shape_is_split_dict`
- `tests/test_ralph_design_003_attempts_split.py::test_quarantine_reason_distinguishable`

Total: **6 xfail → pass** (out of 30).

**Estimated effort:** 4–6 hours. Touches `ralph_loop.py` (~80 LOC
change across the picker, tick(), verify_acceptance, status, and the
new migrator); `ralph_tick.py` (~20 LOC for `--promote`).

**Rollback plan:**

The whole sub-phase is one PR. To roll back:

1. `git revert <sub-phase-1-merge-sha>`.
2. Re-add the xfail markers to the 6 tests (single-file diff, scripted
   by `git diff` over the test changes in the same merge).
3. Existing `done_task_ids` and `attempts` are NOT migrated back to int
   shape automatically — the `_migrate_state` is one-way. If the operator
   reverts, they must hand-edit `ralph_state.json` to flatten attempt
   counts. Risk acceptable: state is gitignored cached data, not durable
   source.

**What this does NOT do:**

- Does not strip scope from CRON_BRIEF.md (sub-phase 3)
- Does not add observability surface (sub-phase 2)
- Does not change the default eval metric (sub-phase 3)

**Operator-review checklist (advisor → operator handoff):**

- Diff is ≤ 150 LOC across ≤ 3 files.
- All 6 xfail removals are in the same commit as the runtime change
  (xfail discipline per CLAUDE.md).
- `python -m pytest tests/` shows 216 passed (was 210) + 2 skipped +
  24 xfailed (was 30) — the 6 flipped tests now pass.
- Loop still paused (`data/RALPH_STOP` untouched).
- One concrete demo: `python ralph_tick.py --status` shows
  `review_pending: []` and `attempts: {}` (or the migrated dict shape).

---

## Sub-phase 2 — Observability + Stop discipline

**Definition-of-done:**

- `data/.ralph_heartbeat.json` written at executor start and updated
  on phase transitions (executor_running → acceptance_check →
  quality_gate → post_tick), deleted on tick end (success or failure)
- `state['tick_durations']['window']` populated with per-tick duration records
- `ralph_loop.status()` adds `review_pending`, `spec_broken_quarantine`,
  `work_failed_quarantine`, `tick_duration_p50_sec`, `tick_duration_p95_sec`,
  `halted_via_RALPH_STOP` keys
- `ralph_tick.py --watch` exists and renders the heartbeat as a
  one-line status
- `ralph_loop.tick()` checks `data/RALPH_STOP` at the top and returns
  None when present (belt-and-braces vs CRON_BRIEF.md)
- 5-consecutive-failure auto-halt writes `data/RALPH_STOP_AUTO`
- Eval metric trend auto-halt (5%-drop-across-5-eval-ticks) also writes
  `data/RALPH_STOP_AUTO`
- `ralph_tick.py --pause "reason"`, `--resume`, `--resume-all` CLI flags
- `scripts/ralph_digest.py` exists; writes `data/ralph_digest.md`
  summarising last 24h

**xfail tests flipped to passing:**

- `tests/test_ralph_design_004_observability.py::test_tick_function_references_heartbeat`
- `tests/test_ralph_design_004_observability.py::test_state_has_tick_durations_window`
- `tests/test_ralph_design_004_observability.py::test_status_exposes_review_pending`
  (already partially covered by sub-phase 1; sub-phase 2 finalises)
- `tests/test_ralph_design_004_observability.py::test_status_exposes_duration_percentiles`
- `tests/test_ralph_design_004_observability.py::test_ralph_digest_script_exists`
- `tests/test_ralph_design_005_stop_discipline.py::test_tick_returns_none_when_ralph_stop_exists`
- `tests/test_ralph_design_005_stop_discipline.py::test_consecutive_failure_auto_halt_source_marker`
- `tests/test_ralph_design_005_stop_discipline.py::test_ralph_tick_cli_supports_pause_resume`

Total: **8 xfail → pass** (sub-phase running total: 14/30).

**Estimated effort:** 6–8 hours. Touches `ralph_loop.py` (~120 LOC for
heartbeat + duration + status fields + auto-halt logic + RALPH_STOP
check), `ralph_tick.py` (~40 LOC for `--watch` / `--pause` / `--resume`),
new file `scripts/ralph_digest.py` (~80 LOC).

**Rollback plan:**

- Heartbeat file is gitignored; nothing to clean if rolled back.
- `state['tick_durations']` is additive — old `ralph_state.json`
  without it loads cleanly.
- `data/RALPH_STOP_AUTO` is independent of `data/RALPH_STOP`; safe to
  delete manually if the trigger logic was wrong.
- Revert the merge SHA; re-add xfail markers (8 of them).

**Operator-review checklist:**

- Diff ≤ 280 LOC across ≤ 5 files (ralph_loop.py, ralph_tick.py,
  scripts/ralph_digest.py, .gitignore for the heartbeat file, a few
  small test edits).
- 14 xfail → pass cumulative. pytest tests/: 224 passed (was 216) +
  2 skipped + 16 xfailed.
- Loop still paused.
- Concrete demos:
  - `touch data/RALPH_STOP_TEST; mv data/RALPH_STOP_TEST data/RALPH_STOP;
     python ralph_tick.py --dry`
    shows `HALTED by data/RALPH_STOP`. Cleanup: `rm data/RALPH_STOP`.
    (Operator MUST NOT actually run this against the real RALPH_STOP — use a
    temp throwaway. The advisor session demonstrates the path; the operator
    confirms by reading the source.)
  - `python ralph_tick.py --watch &; python ralph_tick.py --dry; kill %1`
    shows the heartbeat lifecycle.
  - `python scripts/ralph_digest.py` writes a digest from the 97-tick
    history.

---

## Sub-phase 3 — Scope strip + Quality bar

**Definition-of-done:**

- `EXECUTORS` dict shrunk: remove `agent_creative` from cron dispatch;
  add `regression`, `triangulation`, `cache_op`, `embed_op` (the
  latter two as real executors, not stubs)
- `agent_creative` stays as a function in `ralph_loop.py` (operator
  can still invoke via `RALPH_AGENT_BACKEND=manual python ralph_tick.py
  --task <id>`); the function does NOT appear in `EXECUTORS`
- `CRON_BRIEF.md` rewritten to strip:
  - MAINT memory-hygiene block (lines 71–75)
  - MAINT ADR-drift detection block (lines 76–77)
  - MAINT every-24th synthesis sub-step
  - The entire RESEARCH cycle (step 5)
  - `scripts/tick_finalize.py` reduced to call only `state_snapshot.py`
- Scaffolding-edit lockdown helper (`detect_scaffolding_edit` or
  similar) implemented; tick() invokes it post-commit; rejects diffs
  touching `ralph_loop.py`, `ralph_run.py`, `ralph_tick.py`,
  `CRON_BRIEF.md`, `data/RALPH_STOP*`, `tests/test_ralph_*.py`
- Triangulation gate (Phase 5 plan item 21): detects classifier /
  routing-table additions; refuses to pass without ≥2 new tests in
  the same commit; bypass via `# triangulation-exempt: <reason>`
- `execute_regression` exists; handles xfail-removal workflow:
  reads target file, confirms `xfail(strict=True)` present, runs
  pytest, removes marker via in-place edit, re-runs pytest, runs
  full-suite gate
- `execute_eval` default: `metric = "hard_pass_rate"`, `script =
  "scripts/run_v2_eval.py"`, `compare_to = "data/eval/v2/baseline_capable_model.jsonl"`
- `scripts/run_v2_eval.py` exists; reads the v2 baseline + asserts;
  tallies hard_pass_rate as a single number
- `verify_acceptance::python_test_passes` ALSO runs full-suite pytest
  with `--maxfail=1`

**xfail tests flipped to passing:**

- `tests/test_ralph_design_006_scope_discipline.py::test_regression_executor_registered`
- `tests/test_ralph_design_006_scope_discipline.py::test_triangulation_executor_registered`
- `tests/test_ralph_design_006_scope_discipline.py::test_agent_creative_not_in_executors`
- `tests/test_ralph_design_006_scope_discipline.py::test_cron_brief_strips_maintenance_research`
- `tests/test_ralph_design_006_scope_discipline.py::test_scaffolding_edit_lockdown_helper_exists`
- `tests/test_ralph_design_008_quality_bar.py::test_execute_eval_default_metric_is_hard_pass`
- `tests/test_ralph_design_008_quality_bar.py::test_python_test_passes_includes_full_suite_check`
- `tests/test_ralph_design_008_quality_bar.py::test_execute_regression_exists`
- `tests/test_ralph_design_008_quality_bar.py::test_triangulation_gate_helper_exists`

Total: **9 xfail → pass** (sub-phase running total: 23/30).

**Estimated effort:** 10–14 hours (the biggest sub-phase). Touches
`ralph_loop.py` (~250 LOC of new executors + gates + scaffolding-lockdown);
`CRON_BRIEF.md` rewrite (~30 lines deleted, ~10 reshaped);
`scripts/run_v2_eval.py` new (~120 LOC); `scripts/tick_finalize.py`
trim. **Highest-risk sub-phase** because it changes the most
behavioural surface.

**Rollback plan:**

- `CRON_BRIEF.md` revert is a single-file rewrite — `git checkout
  <prev-sha> -- scripts/CRON_BRIEF.md` restores immediately.
- Removed-from-cron-dispatch `agent_creative` is a one-line change in
  EXECUTORS dict; trivial revert.
- `execute_regression`, `execute_triangulation`, `execute_cache_op`,
  `execute_embed_op` are all new functions; reverting drops them
  cleanly (no callers outside EXECUTORS).
- Triangulation + scaffolding-edit gates are post-commit checks; if
  they false-positive in production, env-var kill switch
  `RALPH_GATES_DISABLED=1` short-circuits both.
- 9 xfail markers go back if rolled back.

**Operator-review checklist:**

- This is the largest PR. Operator should expect ~400 LOC across
  ≤ 8 files. Worth doing in 2 reading passes.
- 23 xfail → pass cumulative. pytest tests/: 233 passed + 2 skipped +
  7 xfailed.
- Loop STILL paused — do not delete `data/RALPH_STOP` here.
- Concrete demos:
  - `python ralph_tick.py --task <regression_test_task_id> --dry`
    shows the regression executor's planned action.
  - `python scripts/run_v2_eval.py --dry` reads the v2 baseline,
    tallies hard_pass_rate, prints to stdout (no Neo4j needed for the
    file read; live `/chat` calls are gated by `--live` flag).
  - Triangulation gate true-positive: a synthetic commit with a new
    3-bucket dict and no tests fails the gate.
  - Triangulation gate true-negative: the same commit with `#
    triangulation-exempt: testing` succeeds.

**Risk note for operator:** This sub-phase is where the loop's
behaviour visibly changes the most. Recommend a 1-week pause between
sub-phase 3 merge and sub-phase 4 to absorb any rough edges before
the restart-precondition work.

---

## Sub-phase 4 — Resumability + Integration + Pre-restart

**Definition-of-done:**

- `scripts/ralph_restart_audit.py` exists; walks `ralph_backlog.yaml`
  and reports per-task fitness for restart (categorises as eligible /
  blocked / review_pending; reports the v2-metric default check;
  enumerates `RALPH_STOP*` files)
- The audit writes `data/.ralph_restart_audit_OK` with the backlog SHA
  on clean run (E.2)
- `ralph_tick.py --resume-all` reads the OK file and rejects unless
  the SHA matches the current `ralph_backlog.yaml`
- `post_resume_self_check` helper in `ralph_loop.py` (or equivalent
  name); called at top of `tick()` immediately after the RALPH_STOP
  check (or just before the picker); runs `quality_gate()`,
  `pytest tests/ -q --maxfail=1`, and confirms `execute_eval` default
  metric is `hard_pass_rate`; aborts via `RALPH_STOP_AUTO` if any check
  fails
- `execute_eval` references `data/eval/v2/` paths
- `execute_cache_op` is implemented (read-only-then-write; refuses
  destructive ops without backup)
- `spec.reads_graph: true` honoured in tick(): Neo4j-reachability check
  before executor runs; BLOCKED status if unreachable

**xfail tests flipped to passing:**

- `tests/test_ralph_design_007_resumability.py::test_restart_audit_script_exists`
- `tests/test_ralph_design_007_resumability.py::test_restart_audit_runs_clean`
- `tests/test_ralph_design_007_resumability.py::test_on_resume_self_check_helper_exists`
- `tests/test_ralph_design_009_integration.py::test_execute_eval_default_compare_to_is_v2_baseline`
- `tests/test_ralph_design_009_integration.py::test_execute_cache_op_exists`
- `tests/test_ralph_design_009_integration.py::test_cache_op_registered`
- `tests/test_ralph_design_009_integration.py::test_reads_graph_spec_field_is_recognised`

Total: **7 xfail → pass** (sub-phase running total: 30/30).

**Estimated effort:** 6–8 hours. Touches `ralph_loop.py` (~80 LOC for
self-check + cache_op + reads_graph); `ralph_tick.py` (~40 LOC for
`--resume-all` SHA gate); `scripts/ralph_restart_audit.py` new (~150 LOC).

**Rollback plan:**

- Each new file (`ralph_restart_audit.py`) and helper deletes cleanly.
- The `--resume-all` flag change is a single CLI surface; revert
  via single-line edit.
- 7 xfail markers go back if rolled back.

**Operator-review checklist:**

- Diff ≤ 280 LOC across ≤ 5 files.
- 30 xfail → pass cumulative. pytest tests/: 240 passed + 2 skipped +
  0 xfailed. (Two original guardrails + 30 design tests + the 208
  pre-existing tests.)
- Loop STILL paused. Phase 11 (restart) is a SEPARATE commit, not
  part of this sub-phase.
- Concrete demos:
  - `python scripts/ralph_restart_audit.py` runs cleanly on the live
    backlog; emits READY or per-task blockers.
  - Edit `ralph_backlog.yaml` (e.g. add a comment); re-run audit;
    OK file SHA invalidated; `python ralph_tick.py --resume-all` (still
    paused, dry-run) rejects with "audit must be re-run against the
    current backlog".

---

## Phase 11 — Operator-only restart commit (NOT a sub-phase)

After all four sub-phases are merged + the operator has reviewed
`scripts/ralph_restart_audit.py`'s output + decided to restart:

**Single commit on a `phase-11-loop-restart-2026-XX-XX` branch:**

1. Delete `data/RALPH_STOP`.
2. Restart whatever cron / wake-up was hosting the loop (`scripts/CRON_BRIEF.md`
   is now slim enough to be safe).
3. Optional: a one-tick dry run via `python ralph_run.py --max 1 --dry`
   in the same session to confirm the picker works as expected.

The Phase 5 advisor work does NOT do this commit. The operator-merge
gate from CLAUDE.md (`Operator-merge gate`) explicitly requires the
operator to do this.

---

## Cumulative summary

| Sub-phase | Effort | LOC | xfail flipped | xfailed left | Reverts cleanly? |
|---|---:|---:|---:|---:|---|
| 1 — Failure-mode kernel | 4–6h | ~100 | 6 | 24 | Yes (state migrator is one-way; doc warns) |
| 2 — Obs + Stop | 6–8h | ~280 | 8 | 16 | Yes (all additive) |
| 3 — Scope + Quality | 10–14h | ~400 | 9 | 7 | Yes (env-var kill switch for gates) |
| 4 — Resume + Integ | 6–8h | ~270 | 7 | 0 | Yes (new files; clean delete) |
| **Total** | **26–36h** | **~1,050** | **30** | **0** | |

Plus Phase 11 (operator restart): a single 5-line commit.

---

## Dependencies between sub-phases

```
Sub-phase 1
  ├─ blocks ─→ Sub-phase 2's review_pending status field
  ├─ blocks ─→ Sub-phase 3's regression task type (it appends to
  │            done_task_ids via the new picker flow)
  └─ blocks ─→ Sub-phase 4's restart audit (it reports on review_pending)

Sub-phase 2
  └─ blocks ─→ Sub-phase 4's post-resume self-check (it writes
                RALPH_STOP_AUTO if checks fail)

Sub-phase 3
  └─ blocks ─→ Sub-phase 4's audit (it checks for v2 metric default)

Sub-phase 4
  └─ blocks ─→ Phase 11 (operator restart)
```

No cycles; clean topological order.

---

## What this plan deliberately does NOT do

- **Does not enable parallel ticks.** Worktree isolation (PHASE_5_LOOP_TAMING_PLAN
  item 19) is a separate experiment. The 4-app refactor (retrofit
  plan Phase 3 item 11) is a prerequisite for worktree-per-tick because
  of shared model loads; Phase 5 ships the discipline first, the
  parallel-ticks experiment can run after.
- **Does not refactor `chat.py`** (still 2,497 LOC). Retrofit plan
  Phase 7 work.
- **Does not consolidate the 21 tools.** Retrofit plan Phase 7 item 28.
- **Does not convert ADRs 0013–0044 to Decision Logs.** Retrofit plan
  Phase 9 item 35.
- **Does not remove `agent_creative` from the codebase entirely.** It
  remains callable via operator's manual path (`RALPH_AGENT_BACKEND=manual
  python ralph_tick.py --task <id>`); only the cron-dispatch entry
  is removed.
- **Does not pre-restart the loop.** Phase 11 is operator-only.

---

## A note on the operator's xfail-pattern discipline

CLAUDE.md (user globals, "Engineering discipline"):

> TDD with the xfail pattern for bug fixes:
>   1. Write the failing regression test with `@pytest.mark.xfail(strict=True)`. Commit.
>   2. Fix the code; remove the xfail marker in the SAME commit.
>   The test stays as a regression guard forever.

This plan honours that pattern exactly: each sub-phase's runtime change
removes the corresponding xfail markers in the same commit. The 30
xfail tests authored in Phase 4 of this design session ARE the
executable spec the implementer reads.
