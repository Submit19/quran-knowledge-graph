# Phase 5 — Ralph Loop Taming Plan

Companion to `docs/QKG_RETROFIT_PLAN.md` items 18–21. Cross-reference: `docs/QKG_AUDIT.md` §7 (the engineering-manager critique of meta-system growth).

---

## Goal

The Ralph loop, as it stood at audit time, was eating the product:

- 79 ticks in ~13 days, of which 62% were `DONE_WITH_CONCERNS` design docs the operator never reviewed.
- Loop scope expanded to research summarisation, ADR backfill, memory hygiene, vault drift detection — none of which ship code.
- No isolation between ticks; later ticks inherited prior ticks' state pollution.
- Speculative abstractions (adaptive routing classifier, sufficiency gate, reflexion memo schema) shipped on prediction without failing tests to triangulate.

Phase 5 strips the loop back to **code, eval, refactor**. Everything else is operator work or doesn't happen.

The Phase 11 restart only proceeds after Phase 5 lands. Restarting on the old gates would re-encode the existing problems.

## Scope changes (item 18)

`ralph_loop.py` task types in scope post-Phase 5:

| Type | Allowed? | Rationale |
|---|---|---|
| `eval` | ✅ | Beck's attractor needs feedback. Required. |
| `cleanup` | ✅ | Bug fixes, regression test additions, dead-code removal. |
| `cypher_analysis` | ✅ | Cypher migrations, index audits, schema fixes. Touches code or schema. |
| `cache_op` | ✅ | Refresh / invalidate cache; touches code paths. |
| `embed_op` | ✅ | Re-embed verses; ships measurable change. |
| `prompt_variant` | ⚠️ Restricted | Requires `python_test_passes` against the v2 eval (Phase 4). No prompt edit lands without measured impact. |
| `agent_creative` | ❌ | This is the design-doc ticket type that produced 62% `DONE_WITH_CONCERNS`. Operator-only going forward. |
| `manual` | ❌ | Tasks marked manual were always operator work; remove from loop dispatch. |
| `external_run` | ❌ | Ditto. |
| (new) `regression` | ✅ | Adds a regression test pulled out of `xfail` once a fix lands; canonical Phase 3b shape. |
| (new) `triangulation` | ✅ | Adds a second test for an existing single-example abstraction. Forces compliance with item 21. |

The loop's `EXECUTORS` dict in `ralph_loop.py` shrinks accordingly. `agent_creative` execution path stays in code (operator may still invoke manually) but is removed from cron dispatch.

## Tick isolation (item 19)

Current state: each tick runs in the operator's main checkout, mutating `ralph_state.json`, `ralph_log.md`, `STATE_SNAPSHOT.md`, plus any code files the task touches. Later ticks see whatever the previous tick left behind.

Phase 5 isolates ticks via git worktree:

```bash
# At tick start:
TICK_ID="tick-$(date -u +%Y%m%d-%H%M%S)-$(uuidgen | head -c 8)"
WORKTREE=".ralph-worktrees/$TICK_ID"
git worktree add -b "ralph/$TICK_ID" "$WORKTREE" main

# Run the tick inside the worktree (subprocess.run cwd=WORKTREE).
# The tick reads state from main checkout (read-only), writes results
# to the worktree, commits + pushes its branch.

# At tick end (success):
git worktree remove "$WORKTREE"
git push origin "ralph/$TICK_ID"
# Operator (or a separate gate process) merges acceptable branches.

# At tick end (failure):
# Worktree preserved for forensics. Branch left local.
```

State files (`ralph_state.json`, `ralph_log.md`) are written in the **main checkout** by a small post-tick reconciliation step, after the tick branch is committed. This keeps state authoritative in main while iterations run in worktrees.

Disk cost: ~50–200 MB per active worktree (plus QKG's data files which are shared via git's worktree mechanism). Cleanup is automatic on success.

Threading concern: only one tick runs at a time today. Worktree isolation makes parallel ticks possible later (separate experiment; not Phase 5). Phase 5 keeps tick concurrency at 1 to avoid Neo4j contention.

## Do-Over MAINT subtask (item 20)

Every 6th MAINT tick runs an additional pruning pass:

```python
def prune_graveyard(repo_root: Path, age_threshold_days: int = 14) -> list[Path]:
    """
    Remove data/ralph_agent_*.md and data/ralph_analysis_*.md files
    whose corresponding task is DONE-and-shipped AND last-modified
    > age_threshold_days ago.
    """
    pruned = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=age_threshold_days)
    state = load_ralph_state(repo_root)
    done_ids = {t["id"] for t in state["task_history"] if t["status"] == "DONE"}

    for pattern in ("data/ralph_agent_*.md", "data/ralph_analysis_*.md"):
        for path in (repo_root).glob(pattern):
            task_id = extract_task_id_from_filename(path)
            if task_id not in done_ids:
                continue  # task not done yet, keep
            if datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) > cutoff:
                continue  # too recent, keep
            path.unlink()
            pruned.append(path)
    return pruned
```

Pruned files are listed in the MAINT tick's commit message ("pruned 14 stale ralph_*.md files older than 14 days"). Operator can `git revert` the commit if anything important was lost.

Conservative thresholds:
- 14 days = roughly 3 sprints of loop activity
- DONE-and-shipped only (never prunes incomplete or in-flight artefacts)
- Only `ralph_agent_*.md` and `ralph_analysis_*.md` patterns (the loop's own output graveyard, not arbitrary `.md` files)

The 5 long-standing untracked files in the repo (audit's Phase 7 work) are NOT in scope here — those are pre-loop cruft. Phase 5's prune is for ongoing loop hygiene only.

## Triangulation gate (item 21)

Forbid speculative abstraction. New rule in the gate function:

```python
def acceptance_classifier_or_routing_change(task: Task, diff: GitDiff) -> AcceptanceResult:
    """
    Reject any commit that adds a new classify_* function, profile bucket,
    routing table, or rule-based dispatcher unless the same commit also
    adds at least 2 tests in tests/ exercising the new branches.
    """
    classifier_signals = detect_classifier_additions(diff)
    if not classifier_signals:
        return AcceptanceSuccess()

    new_test_count = count_new_tests_in_diff(diff)
    if new_test_count < 2:
        return AcceptanceFailure(
            reason=(
                f"Speculative abstraction detected ({classifier_signals}). "
                f"Beck's Triangulate rule (Phase 5 item 21): new classifiers, "
                f"profiles, or routing tables require ≥2 tests in the same commit. "
                f"This commit adds {new_test_count}."
            )
        )
    return AcceptanceSuccess()
```

Detection heuristics for `detect_classifier_additions`:
- New function whose name matches `^classify_|^route_|^select_profile|^pick_(tool|model|backend)`
- New dict literal with ≥3 string keys mapping to function/string values, named `*_PROFILES`, `*_BUCKETS`, `*_ROUTES`, `*_DISPATCH`
- New `if/elif` chain with ≥3 branches over a string variable that didn't exist on the previous commit

False-positive rate matters. Document the gate's signature so operator can tag a commit `# triangulation-exempt: <reason>` to bypass when the classifier is actually a renaming or re-organising rather than new logic.

## Restart conditions for Phase 11

The loop only restarts when ALL of:

1. Phase 5 items 18–21 are merged to main.
2. Phase 4 v2 eval is the gating metric (`ralph_backlog.yaml::default_baseline_metric` updated).
3. Phase 1 CI is green on main (already true post-Phase 1 fix).
4. `data/RALPH_STOP` is removed in the same commit that re-enables cron.
5. Operator approves the restart explicitly (one commit, one human review).

The restart is a deliberate operator action, not a delegated tick. The loop never restarts itself.

## Migration

| Day | Work |
|---|---|
| 1 | Item 18: scope changes in `ralph_loop.py::EXECUTORS`. Add `regression` + `triangulation` task types. Tests for the new dispatch. |
| 2 | Item 19: worktree isolation. New helper `scripts/ralph_tick_worktree.py`. Cron brief updated. Test with a synthetic fast tick on a fixture branch. |
| 3 | Item 20: `prune_graveyard()` in `scripts/memory_hygiene.py` (or a new file). Wired into MAINT every 6th tick. Unit tests against a temp dir. |
| 4 | Item 21: triangulation gate. Detection heuristics + bypass tag + tests for both true positives and false positives. |
| 5 | End-to-end dry run on a short branch with `data/RALPH_STOP` still in place. Operator reviews. If clean, Phase 11 restart prompt. |

## Acceptance criteria for Phase 5 complete

- `ralph_loop.py::EXECUTORS` shrunk to allowed task types only; `agent_creative` no longer in cron dispatch.
- Worktree isolation in use; every tick branch named `ralph/<tick_id>`; main checkout state files updated post-tick only.
- `prune_graveyard()` in MAINT every 6th tick; first run lists what it pruned in commit message.
- Triangulation gate active; tested against 3+ true-positive commits and 3+ false-positive commits from git history.
- Pre-restart dry run produces 5+ clean ticks with no operator intervention required.
- `data/RALPH_STOP` still in place at end of Phase 5 — restart is its own operator-approved commit (Phase 11).

## Open questions for the operator

1. **Worktree storage location.** `.ralph-worktrees/` in the repo root (gitignored) keeps things local; `~/.ralph-worktrees/<repo>` keeps the repo clean but loses portability. Recommend `.ralph-worktrees/` + gitignore entry.
2. **Pruning aggressiveness.** 14 days conservative; 7 days more aggressive. Calibrate after 1 month of post-Phase-5 operation based on how often the operator references old artefacts.
3. **Triangulation gate scope.** Apply to all Ralph commits, or also to operator commits via pre-commit hook? Recommend Ralph-only initially; promote to pre-commit once the gate's false-positive rate is known to be low.
4. **`agent_creative` removal completeness.** Some operator workflows might rely on `RALPH_AGENT_BACKEND=manual python ralph_tick.py --task <id>` for design docs. Keep that manual path; only remove from cron dispatch. Acceptable?
5. **State reconciliation race.** When two ticks try to update `ralph_state.json` from different worktrees back to main, how is the merge handled? Recommend: post-tick reconciliation runs serial via a `flock` on `data/.ralph-state.lock`; if locked, second tick waits with timeout.

## What this plan deliberately does not do

- **Doesn't replace cron.** The cron mechanism is fine; only the tick contents change. (Cron stays session-hosted; no OS-level cron.)
- **Doesn't add new memory infrastructure.** The Obsidian vault, `STATE_SNAPSHOT.md`, `SESSION_LOG.md`, ADRs all stay. Phase 9 reviews ADR-by-LLM separately.
- **Doesn't enable parallel ticks.** Worktree isolation is a prerequisite; actually running parallel ticks is a separate experiment for after the loop has been stable on the new gates for a while.
- **Doesn't change the orchestrator-with-subagent pattern.** That pattern (ADR-0007) was sound; what changed is what the subagent is allowed to do.
- **Doesn't restart the loop.** Phase 11 is a separate operator-approved commit.
