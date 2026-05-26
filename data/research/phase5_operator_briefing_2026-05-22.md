# Phase 5 Operator Briefing — Ralph loop taming

_For the operator. 10-minute read. Authored 2026-05-22 on branch
`claude/phase5-ralph-design-2026-05-22`. No runtime code touched;
loop remains paused via `data/RALPH_STOP`._

---

## What Ralph is + what was wrong

Ralph is a self-iterating Python loop (`ralph_loop.py` + `ralph_tick.py`
+ `ralph_run.py` + `scripts/CRON_BRIEF.md`) that picks the highest-priority
unblocked task from `ralph_backlog.yaml`, runs a typed executor, verifies
acceptance criteria, and writes outcomes to `ralph_state.json` +
`ralph_log.md` + `data/ralph_*.md`. It produced 121 ticks across 13 days
before being paused 2026-05-13 with `data/RALPH_STOP`.

The audit (`docs/QKG_AUDIT.md` §7 + the Beck TDD lens) named five
structural defects, replicated on the live 97-tick history snapshot:

1. **The load-bearing fiction.** 67% of the loop's "successful"
   outcomes (44 of 66 DONE+DWC) are DONE_WITH_CONCERNS — soft passes
   the operator never reviews. Concentrated in `agent_creative`
   (36/38 = 95% DWC). Design docs accumulate in `data/ralph_*.md`
   (55 files today) unread.
2. **Meta-system mass.** The loop spends real cycles writing ADRs from
   commit messages (a category error), maintaining a vault, doing
   memory hygiene — none of which ships code.
3. **No Red.** Beck's gap: decisions ship at tick N, feedback scheduled
   for tick ≥ N+15. The loop has no failing-test attractor.
4. **State pollution.** Every tick runs in the operator's main checkout;
   no worktree isolation; ticks inherit prior ticks' state.
5. **Bus factor.** The loop produces ~7 ticks/day; the operator can
   realistically review ~3/week. Backlog grows monotonically.

`RALPH_STOP` was the explicit operator pause to address the structural
problems before they compound. Phase 5 is the design session for the
fix — Phase 11 (a separate operator-only commit) is the restart.

---

## The taming approach

Eight specific changes across seven design dimensions
(`data/research/phase5_design_proposal_2026-05-22.md`):

| § | Change | Why |
|---|---|---|
| A.1 | Drop `DONE_WITH_CONCERNS` from `TERMINAL_OK` | DWC must require explicit operator promote, not silent inclusion in `done_task_ids` |
| A.2 | `verify_acceptance` hard-fails on missing `acceptance:` block | Removes the second leg of the load-bearing fiction |
| A.3 | Split `attempts` counter (`needs_context` vs `failed_or_blocked`) | Quarantine reason becomes legible — operator knows whether to fix YAML or fix code |
| B | Heartbeat + duration telemetry + `--watch` + digest | Live observability beyond "in_progress field in JSON" |
| C | Loop-level RALPH_STOP check + auto-halt on 5 consecutive fails + metric trend halt + `--pause` / `--resume` CLI | Stop discipline beyond the cron-only check |
| D | `EXECUTORS` shrinks + CRON_BRIEF strip + scaffolding-edit lockdown | Adopts existing PHASE_5_LOOP_TAMING_PLAN item 18; explicitly removes meta-system work |
| E | Pre-restart audit script + SHA-pinned restart gate + on-resume self-check | Phase 11 becomes mechanical, not vibes |
| F | `regression` + `triangulation` task types + full-suite pytest gate + v2-eval as default metric + triangulation gate (PHASE_5 item 21) | Beck's Red bar; the v2 eval becomes the attractor |
| G | Default to v2 baseline + real `execute_cache_op` + `reads_graph` spec field | Loop integrates with recently-shipped systems instead of being oblivious |

All eight are designed to be **subtractive of behaviour but additive
of structure** — Ralph still ships code, just under tighter discipline.

The existing `docs/PHASE_5_LOOP_TAMING_PLAN.md` (items 18–21 of the
retrofit plan) covered 4 of these (D, F.4 partly, plus the worktree
+ pruning items I've explicitly deferred). The design proposal adds
the other 4 (A.1, A.2, A.3, B, C, E, F.1-F.3, G).

**Worktree-per-tick (existing plan item 19) and graveyard pruning
(item 20) are deferred.** Item 19 has a real prerequisite — the
4-app duplication (audit §4) means model loads aren't shareable
across worktrees yet; refactor first, parallel later. Item 20 is
fine to slot into sub-phase 3 as a small addition, but the failure
mode it solves (creation rate, not cleanup) is better addressed by
removing `agent_creative` from cron dispatch (sub-phase 3) than by
deleting files after the fact.

---

## What lands when (phased plan)

`data/research/phase5_implementation_plan_2026-05-22.md` breaks the
8 changes into 4 atomic sub-phases:

| Sub-phase | Concerns | LOC | Effort | xfail tests flipped |
|---|---|---:|---:|---:|
| **1 — Failure-mode kernel** | §A.1, §A.2, §A.3 | ~100 | 4–6h | 6 |
| **2 — Observability + Stop** | §B, §C | ~280 | 6–8h | 8 (cum. 14) |
| **3 — Scope + Quality bar** | §D, §F, partial §G | ~400 | 10–14h | 9 (cum. 23) |
| **4 — Resumability + Integration** | §E, rest of §G | ~270 | 6–8h | 7 (cum. 30) |
| **Total** | | **~1,050** | **26–36h** | **30** |
| **Phase 11 (operator-only)** | Delete `data/RALPH_STOP`; restart cron | ~5 | <30 min | — |

Order is topologically forced — sub-phase 2 needs the review_pending
plumbing from sub-phase 1; sub-phase 4's audit needs the v2 metric
default from sub-phase 3; etc. The four sub-phases each fit in one
advisor + fresh-local-session cycle and are independently reviewable.

The 30 xfail tests in `tests/test_ralph_design_*.py` are the
executable spec. Each sub-phase flips its subset of xfail markers in
the same commit as the runtime change (per CLAUDE.md xfail discipline).

---

## What the operator needs to decide before any of it happens

Three orthogonal decisions. None block the design; each affects how
sub-phase 3 (the big one) ships:

**D1 — Sub-phase ordering: as proposed, or interleaved with worktree
isolation?**

As proposed: failure-mode → obs+stop → scope+quality → resume+integ.
The PHASE_5_LOOP_TAMING_PLAN worktree-isolation item is deferred.

Alternative: insert worktree-per-tick between sub-phases 2 and 3,
under the assumption that the 4-app duplication can be tolerated for
a single shared model load if the worktrees are sequential (which
sub-phase 3 keeps them).

Recommendation: as proposed. The 4-app refactor unblocks much more
than worktree-per-tick; do it under its own phase.

**D2 — `agent_creative` removal completeness.**

Sub-phase 3 removes `agent_creative` from the `EXECUTORS` dict (cron
dispatch), but **keeps the function in `ralph_loop.py` so the operator
can still invoke it manually** via `RALPH_AGENT_BACKEND=manual
python ralph_tick.py --task <id>`.

Alternative: full deletion (delete the function too; remove the
spec.backend=manual code path).

Recommendation: keep it. Operator's working pattern has been the
manual invocation; deleting forces operator workflow change. Cost
of keeping: ~150 LOC of dead-from-cron-perspective code. Acceptable.

**D3 — Phase 11 restart trigger.**

Two paths after sub-phase 4 merges:

- **(a) Operator pauses 1 week, observes the suite holds at 240+2,
  reviews the four sub-phase commits, then runs Phase 11.**
- **(b) Operator runs Phase 11 immediately after sub-phase 4 merges,
  relying on the pre-restart audit + on-resume self-check to catch
  problems.**

Recommendation: (a). The audit + self-check are belt-and-braces;
human-eyes-on-the-diff is the third belt. The whole point of Phase
5 is to slow the loop down on purpose.

---

## Three open questions the design couldn't answer

1. **Is `agent_creative` even worth keeping, given Phase 5 strips it
   from cron?**
   The operator's workflow currently uses the `RALPH_AGENT_BACKEND=manual`
   path for ~all design-doc work (the cron subagent runs against an
   Opus model, not OpenRouter). If that's the de facto operating mode,
   the `execute_agent_creative` function — including the OpenRouter
   call to `gpt-oss-120b:free` — is dead code. **Cleaner to delete it
   entirely in a small follow-up after sub-phase 3** (D2 alternative).
   Reconnaissance didn't have evidence to decide.

2. **What does the v2 eval look like as a Ralph metric?**
   Sub-phase 3 changes `execute_eval`'s default to `hard_pass_rate`
   against `data/eval/v2/baseline_capable_model.jsonl`. The plan
   creates a `scripts/run_v2_eval.py` to produce that number. But
   **the v2 eval framework hasn't been hardened for repeated runs**
   — every existing run was the one-shot baseline. Will running the
   v2 eval on every loop tick (or every N) hit `/chat` 57 times,
   exercising cache hits, and produce a stable hard_pass_rate? Or
   does the v2 eval need its own batched runner with caching disabled
   first? **This is the most likely thing to surface during sub-phase
   3 implementation** and may force the v2-runner work into its own
   sub-phase between 3 and 4.

3. **Do we want the loop to ever restart at the current cadence
   (~7 ticks/day), or is a tamed cadence the design target?**
   The design proposal doesn't impose a tick rate. CRON_BRIEF's
   30-min cadence is unchanged in the plan. But the audit's
   bus-factor finding (review throughput ~3/week vs production rate
   ~7/day) is partly a rate problem, not just a discipline problem.
   **If post-restart the operator finds even the tamed loop produces
   more than they can review weekly, the right answer is to slow
   the cron** (e.g. 4h cadence → 6 ticks/day max). Phase 5 design
   doesn't pre-decide; operator decides post-restart based on
   observation.

---

## What the next session is good for

After this design lands on `main` (operator-merged), the next advisor
+ fresh-session cycle is **sub-phase 1 — Failure-mode kernel**. That's
the smallest sub-phase (4–6h), the one whose tests are most isolated
from other systems, and the prerequisite for everything else. It's
also the highest-value: removing DWC from TERMINAL_OK alone fixes the
load-bearing fiction.

The prompt skeleton for that session, ready to paste:

```
Phase: Phase 5 sub-phase 1 — Failure-mode kernel
Read first:
- data/research/phase5_design_proposal_2026-05-22.md §A
- data/research/phase5_implementation_plan_2026-05-22.md sub-phase 1
- tests/test_ralph_design_001_dwc_not_terminal_ok.py
- tests/test_ralph_design_002_acceptance_required.py
- tests/test_ralph_design_003_attempts_split.py

Task: implement §A.1, §A.2, §A.3 of the design proposal.

Hard constraints:
- TDD: remove xfail markers in the SAME commit as the runtime change
- data/RALPH_STOP stays in place
- Atomic commits per concern (§A.1, §A.2, §A.3 may each be one commit)
- pytest tests/ must show 216 passed + 2 skipped + 24 xfailed

Branch: claude/phase5-subphase1-failure-mode-2026-XX-XX
Operator merges separately.
```

The same shape repeats for sub-phases 2, 3, 4 against the matching
xfail test files.

---

## Files this session produced

- `data/research/phase5_ralph_reconnaissance_2026-05-22.md` — 522 lines, the
  reconnaissance: what Ralph is, what failed, what's been tried, what
  Phase 5 requires.
- `data/research/phase5_audit_synthesis_2026-05-22.md` — 444 lines, audit
  findings mapped to code/behaviour with applicability notes.
- `data/research/phase5_design_proposal_2026-05-22.md` — 1,136 lines, the
  8-change design across 7 dimensions with alternatives + risks + test
  scenarios.
- `tests/test_ralph_design_001..009.py` — 9 files, 800 lines, 30 xfail tests
  + 2 guardrails.
- `data/research/phase5_implementation_plan_2026-05-22.md` — 434 lines, the
  4-sub-phase breakdown with effort + LOC + rollback per sub-phase.
- `data/research/phase5_operator_briefing_2026-05-22.md` — this file.

All on branch `claude/phase5-ralph-design-2026-05-22`. Loop remains
paused; no runtime code touched; pytest tests/ shows 210 passed +
2 skipped + 30 xfailed.
