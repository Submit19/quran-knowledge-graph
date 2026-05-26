# Phase 5 — Audit Synthesis

_Companion to `phase5_ralph_reconnaissance_2026-05-22.md`. Cross-references
the eight-consultant audit (`docs/QKG_AUDIT.md`) against the actual Ralph
loop code and the 97-tick history snapshot._

For each Ralph-related audit finding: quote it verbatim, map it to specific
code or behaviour, then note whether the finding is still applicable after
the rapid evolution between the audit (`2d8de42`, 2026-05-13) and main
HEAD (`5b03255`, 2026-05-21). The audit period predates the capable-model
baseline, the answer-cache BGE-M3 reranker, and the v2 eval schema, so
some findings may have been overtaken — but the structural ones around
the loop itself are mostly untouched.

---

## §7 · The Engineering Manager (the primary Ralph audit)

This is the most-load-bearing section. It is the one Phase 5 was scoped
around.

### Finding 7.1 — "The loop demonstrably ships code"

> "79 ticks / ~13 days / ~40 code commits / 3 real features merged."

**Mapped to code:**
- `git log --grep="ralph" -i | wc -l` → 101 commits at HEAD (was 79 at
  audit time; ~22 more commits since audit, all pre-pause). 67 unique
  done_task_ids in `ralph_state.json`.
- 3 features the audit credits: `model_registry.py` (shared MiniLM
  singleton, commit `0190f19`); the 2-profile adaptive routing in
  `retrieval_gate.py` (commit `672cc68`); the `extract_eval_common.py`
  shared helpers (commit `27901f7`). All three made it into runtime
  code, not just design docs.

**Still applicable?** YES. The loop is a real shipping engine. The
"strip scope" rule in Phase 5 must NOT throw out this kernel.

**Phase 5 implication:** the surviving task types (eval, cleanup,
cypher_analysis, prompt_variant, regression, triangulation) are exactly
the ones that produced these three shipped features. Subtractive scope
change, not destructive.

---

### Finding 7.2 — "62% DONE_WITH_CONCERNS is a load-bearing fiction"

> "The 'concerns' are absorbed silently because the human-review step
> never happens at scale."

**Mapped to code:**
- `ralph_loop.py::execute_agent_creative` lines 681–684 — DEFAULT return
  status is `DONE_WITH_CONCERNS` for every `agent_creative` task that
  produces output. There is no path back to DONE in the executor.
- `ralph_loop.py::verify_acceptance` returns `DONE_WITH_CONCERNS` for
  ANY task with no `acceptance` block specified (lines 296–300:
  "No acceptance specified — superpowers would call this a soft pass.
  We accept it but flag as DONE_WITH_CONCERNS later.").
- `ralph_loop.py::TERMINAL_OK = {DONE, DONE_WITH_CONCERNS, SKIPPED}` —
  the picker treats DWC as "task complete, move to done_task_ids".
  This is the **single line that converts the soft pass into a
  hard "done"** in the state machine.

**Empirically:**
- Audit window (79 ticks): 62% DWC of all terminal outcomes.
- My fresh window (97 ticks): 67% DWC of DONE+DWC, 45% DWC overall.
- agent_creative-only: 36/38 = 95% DWC. The fiction is concentrated
  in this one executor.

**Still applicable?** YES, fully unchanged. No code touching this
executor has merged since the audit.

**Phase 5 implication (existing plan + my extensions):**
- Phase 5 plan item 18 already removes `agent_creative` from cron dispatch.
- Design proposal must also fix `TERMINAL_OK` to either (a) drop
  `DONE_WITH_CONCERNS` from the success-set so DWC tasks stay pickable
  and require an explicit operator promotion to DONE, or (b) tie DWC
  to a hard expiry (auto-quarantine if not reviewed within N days).
  Without one of these, even after agent_creative is removed, any
  task type that omits acceptance criteria still gets a silent soft-pass.

---

### Finding 7.3 — "The loop is rewriting its own scaffolding"

> "Max 20x, 30-min cadence, end-of-tick prep, Sonnet pre-warming, ADR
> backfill. *Meta-system gaining mass faster than the product.*"

**Mapped to code:**
- `scripts/CRON_BRIEF.md` step 6 (every MAINT tick): "Memory hygiene
  (every MAINT tick). Run `python scripts/memory_hygiene.py`" + ADR-drift
  detection + every-4th-MAINT synthesis sub-step. This IS the
  meta-system the audit names.
- `scripts/haiku_prep.py`, `scripts/sonnet_prep.py`, `scripts/tick_finalize.py`,
  `scripts/state_snapshot.py`, `scripts/memory_hygiene.py` — every one
  of these scripts exists to keep the loop's surrounding meta-system
  consistent. They're not bugs; they're the load.
- Ralph commits like `b8f7b72` (tick 114 "memory hygiene, ADR-drift
  (0042+0043+0044)") and `3b7b0e0` (tick 108 "memory hygiene, ADR-drift
  (0040+0041)") are exactly the audit's pattern.
- `QKG Obsidian/decisions/` — 44 ADR files, of which 0013–0044 are
  visibly machine-authored. The audit's category-error claim is
  evident from the prose: ADR 0013–0044 describe what changed in a
  commit, not why a human chose between alternatives.

**Still applicable?** YES, unchanged. The Obsidian vault, the ADR
backfill, the synthesis docs — all still in place.

**Phase 5 implication:**
- Phase 5 plan item 18 (scope strip) removes "research summarisation,
  ADR backfill, vault hygiene" from the loop's diet.
- Design proposal must also concretely list which scripts get
  unwired from CRON_BRIEF.md. Candidates: `haiku_prep.py`,
  `sonnet_prep.py` (operator-only), `memory_hygiene.py` (operator-only
  or moved to a separate cron that is NOT the Ralph loop).
- The Obsidian vault stays (it's a useful operator artefact), but
  Ralph stops writing to it. ADR-by-LLM is retired (retrofit plan
  Phase 9 item 35 does this separately).

---

### Finding 7.4 — "LLM-authored ADRs are a category error"

> "ADRs encode human judgement; Haiku reading commit messages produces
> confabulations of decisions."

**Mapped to code:**
- `scripts/CRON_BRIEF.md` step 6, ADR-drift detection block:
  "For each such commit, check whether a corresponding ADR exists in
  `QKG Obsidian/decisions/`. If not, spawn a Haiku subagent to write
  one using the existing 0001-0025 Nygard template."
- The ADRs themselves: 0013 (after 0012) onward read as machine
  authored. Sample (ADR 0044, "parallel worktree spike deferred"):
  the body restates what the corresponding `ralph_agent_*.md` says,
  not what the operator considered and discarded.

**Still applicable?** YES, unchanged.

**Phase 5 implication:**
- This is technically retrofit plan Phase 9 item 35 ("convert ADRs
  0013–0032 to Decision Logs"), NOT Phase 5. But Phase 5 must
  remove ADR-writing from the loop's diet (item 18), otherwise the
  category error continues even after item 35 is done.

---

### Finding 7.5 — "Bus factor terrible"

> "Loop keeps ticking out work no one reviews; queues choke within a week."

**Mapped to code:**
- 31 `ralph_agent_*.md` files; 24 `ralph_analysis_*.md` files; total 55.
- `ralph_backlog.yaml` is 1,407 lines — about 80 tasks at audit time;
  current state shows 67 done, 5 in-flight, no quarantined, plus the
  remaining ~10–15 pending (operator's manual count from a 2026-05-21
  snapshot, since `ralph_state.json::pending` is computed from
  `len(backlog) - done - skipped - quarantined`, not stored).
- Operator review throughput: ~3 commits/week reviewing/merging Ralph
  work, based on `git log --grep="merge.*ralph"` — far below the
  ~7 ticks/day production rate the loop sustained.

**Still applicable?** YES. The queue length didn't grow much during
the pause (no new tasks added), but the review backlog accumulated.
The capable-model baseline + cache-merge work over 2026-05-20→05-21
was the operator clearing the highest-value queue (Phase 4); Phase 5's
graveyard remains untouched.

**Phase 5 implication:**
- Phase 5 plan item 20 (prune graveyard) addresses the artefact backlog
  directly.
- Design proposal must add a creation-rate cap: limit the loop to N
  ticks/day OR N agent_creative-equivalent design docs/week. Pruning
  is a release valve; rate-limiting is the regulator.
- Resumability design must require operator explicit unhalt with a
  fresh backlog review (no auto-restart on the existing queue).

---

### Finding 7.6 — "Strip the loop to code/eval/refactor"

> "Not research summarisation, not ADR backfill, not memory hygiene."

This is the prescriptive finding that the existing PHASE_5_LOOP_TAMING_PLAN
turned into items 18–21. Already covered above. Phase 5 design proposal
implements this without modification.

---

## §1 · The Information Retrieval Scientist — touches Ralph indirectly

### Finding 1.1 — "n=13 is not an evaluation"

> "eval_v1.py is an existence test masquerading as a quality metric.
> avg_unique_cites_per_q=43.6 is a count, not correctness."

**Mapped to code:**
- `ralph_loop.py::execute_eval` lines 392–450 — defaults `metric =
  "avg_unique_cites_per_q"`, defaults `compare_to = "data/eval_v1_results.json"`,
  defaults `script = "eval_v1.py"`. The audit's primary critique target
  is the loop's PRIMARY METRIC.
- `_read_eval_metrics` (lines 373–389) supports four metrics:
  `avg_unique_cites_per_q`, `avg_chars_per_q`, `avg_time_sec_per_q`,
  `avg_tools_per_q` — none of which measure correctness.

**Still applicable?** PARTIALLY. The v2 eval (`data/eval/v2/SCHEMA.md`)
introduced behaviour-asserted scoring (hard-pass via citation +
substring + tool checks; not a citation count). Capable-model baseline
(2026-05-21) scored 42/57 = 74% hard-pass under the agent-equivalent
reading. This is real progress that the audit's "0 real numbers"
critique didn't anticipate.

The remaining gap: the Ralph loop's `execute_eval` still defaults to
`eval_v1.py + avg_unique_cites_per_q`. It has NO codepath that runs
the v2 eval and tallies hard-pass against the v2 baseline.

**Phase 5 implication:**
- Quality-bar binding (one of the gaps from reconnaissance §5): the
  default metric in `execute_eval` should be the v2 hard-pass rate,
  not `avg_unique_cites_per_q`.
- Phase 5 design proposal must specify the v2-eval-binding executor
  shape, even if implementation slips to a later sub-phase.

---

### Finding 1.2 — "'Reranker drops hit@10 50%' was never re-measured on multilingual"

> "The adaptive routing design rests on inference, not measurement."

**Mapped to code:**
- `retrieval_gate.py` — 2-profile gate added in commit `672cc68`
  (Ralph tick 73). The 50% number was from QRCD on the OLD English-only
  reranker (`ms-marco-MiniLM-L-6-v2`); the gate now defaults to
  `bge-reranker-v2-m3` (multilingual). The premise of the gate is
  unverified on the current model.

**Still applicable?** YES, unchanged. Retrofit plan Phase 6 item 22
("Re-eval bge-reranker-v2-m3 on QRCD") and item 24 ("validate
adaptive-routing prediction") are the remediation; they are Phase 6,
not Phase 5.

**Phase 5 implication:**
- This is a triangulation-rule case study. The 2-profile gate in
  `retrieval_gate.py` is exactly the kind of single-example abstraction
  Phase 5 item 21 forbids: a classifier with three buckets, no tests,
  shipped on a prediction. The triangulation gate must trigger
  retroactively on `git log -p retrieval_gate.py` for commit `672cc68`
  in any pre-restart dry-run test.

---

## §3 · The Agentic Systems Engineer — touches Ralph through tool surface

### Finding 3.1 — "21 tools, agent uses 4–6 per query"

Not a Ralph finding per se. Mentioned here because Phase 5 item 28
(consolidate 21 tools to 8–10) is Phase 7 work, not Phase 5. Phase 5
design proposal must NOT pre-consolidate tools.

### Finding 3.2 — "`run_cypher` is a footgun"

Phase 7 item 30, not Phase 5. Not in scope.

---

## §4 · The Senior Software Engineer

### Finding 4.7 — "38 data/ralph_*.md artefacts the loop never deletes"

**Mapped to code:**
- 55 files at HEAD vs 38 at audit (17 new across the audit→pause window).
- `ralph_loop.py` writes new files; nothing in the codebase deletes them.
- `scripts/memory_hygiene.py` does not touch this pattern (it manages
  PATTERNS block, SESSION_LOG, vault MOC — none of which are the
  artefact graveyard).

**Still applicable?** YES, slightly worse (17 more files).

**Phase 5 implication:** Phase 5 plan item 20 (prune_graveyard) is
exactly the remediation. Design proposal must specify the function
location, the trigger schedule (every 6th MAINT tick), and the
commit-message pattern so the operator can `git revert` if anything
important was lost.

---

## §8 · The First-Principles Skeptic

### Finding 8.3 — "Does the Ralph loop need to exist for this product?"

> "Pattern-research disguised as feature work."

This is the existential question Phase 5 cannot answer alone — Phase 11
(restart) is where the operator commits or doesn't commit to the loop.

**Phase 5 implication:** the Phase 5 design must produce a tamed loop
that is CHEAP enough to keep around even if the operator decides post-restart
that it isn't worth running daily. The design must support "run it
weekly" or "run it manually only" as first-class modes — not just
"run it nightly at 30-min cadence" as today's CRON_BRIEF assumes.

---

## TDD lens (Kent Beck) — the canonical synthesis

### Finding TDD-1 — "The Ralph loop has no Red"

> "Red → Green → Refactor; QKG's loop is brief → design doc → commit.
> No failing test defines done. That's why 62% of ticks are DWC — no
> green bar to converge to."

**Mapped to code:**
- `verify_acceptance` supports `python_test_passes` (lines 347–363),
  but only ~5 of the 80+ tasks in `ralph_backlog.yaml` use it. The
  rest use `file_min_bytes` or `file_exists` (the audit's anti-pattern).
- Retrofit plan Phase 2 item 8 ("Replace `file_min_bytes` /
  `file_exists` with `python_test_passes`") has not been retroactively
  applied to the backlog. Most existing tasks still use the old gates.

**Still applicable?** YES. The mechanism is in place; the discipline
isn't.

**Phase 5 implication:**
- Design proposal must require: every NEW task in the post-Phase-5
  backlog MUST use `python_test_passes` (or `metric_at_least_baseline`
  against the v2 eval). Backfilling old tasks is operator-optional.
- The xfail-first pattern (operator preference from CLAUDE.md) maps
  cleanly: a `regression` task (new in Phase 5 plan item 18) is
  "remove `@pytest.mark.xfail(strict=True)` from `tests/test_X.py`
  after the underlying fix lands"; the acceptance gate is the
  pytest run with that test removed-from-xfail and passing.

---

### Finding TDD-2 — "Loop violates Isolated Test at meta-level"

> "Ticks inherit full state; not order-independent."

**Mapped to code:**
- Every tick runs in the operator's main checkout (`scripts/CRON_BRIEF.md`
  step 0: "Working directory: `C:\Users\alika\Agent Teams\quran-graph-standalone`").
- `ralph_state.json` is mutated in place by each tick.
- `ralph_log.md` is appended to.
- Any file the task touches (chat.py, retrieval_gate.py, etc.) is
  modified directly in main.

**Still applicable?** YES, unchanged. The retrofit plan Phase 5 item 19
(worktree isolation) is exactly the remediation.

**Phase 5 implication:** worktree-per-tick is non-negotiable in the
design proposal. The challenge is **state reconciliation** — Ralph
state lives in main, ticks write in worktrees — and that's the open
question Phase 5 plan flags (open question 5 in PHASE_5_LOOP_TAMING_PLAN.md
section "Open questions for the operator"). Design proposal must
specify the lock + merge pattern.

---

### Finding TDD-3 — "Most ticks are Obvious Implementation without Fake It or Triangulate"

> "Adaptive routing shipped on a prediction; the eval to triangulate it
> is task #95."

**Mapped to code:**
- `retrieval_gate.py::classify_query` (commit `672cc68`) — three-bucket
  classifier (ARABIC / BROAD / other), no tests in same commit.
- Same shape across reflexion memo schema (`ralph_agent_from_ai_graph_reflexion_pattern.md`),
  sufficiency gate (`ralph_agent_from_neo4j_yt_sufficiency_gate.md`),
  graph-backed tool registry (`ralph_agent_from_neo4j_yt_mcp_graph_backed_registry.md`).

**Still applicable?** YES, unchanged.

**Phase 5 implication:** Phase 5 plan item 21 (triangulation gate)
is exactly the remediation. Design proposal must include the
`# triangulation-exempt: <reason>` bypass with a budget — e.g.
"max 2 exempt commits/week, logged in `ralph_log.md` Codebase Patterns".

---

### Finding TDD-4 — "data/ralph_*.md graveyard is absence of Do Over"

> "Beck: throwing away work is a tool, not a failure."

Already covered in §4.7 above. Phase 5 plan item 20 (prune every 6th
MAINT) is the remediation.

---

## Findings still applicable but OUT OF SCOPE for Phase 5

For completeness — these are valid Ralph-adjacent findings the Phase
5 design proposal should NOT try to fix:

| Audit § | Finding | Where it lives |
|---|---|---|
| §2 KG Architect | Kill legacy MiniLM vector index | Phase 7 item 26 |
| §2 KG Architect | Add 4 missing composite indexes | Phase 7 item 27 |
| §3 Agentic | Consolidate 21 tools to 8–10 | Phase 7 item 28 |
| §3 Agentic | Promote `classify_query` from prompt to code | Phase 7 item 29 |
| §3 Agentic | Log every `run_cypher` invocation | Phase 7 item 30 |
| §4 Senior Eng | 4-app duplication | Phase 3 item 11 |
| §4 Senior Eng | chat.py 2,497 LOC split | Not yet phased |
| §5 Religious Studies | Khalifa disclosure UI | Phase 8 item 32 |
| §6 Product | Audience definition | Phase 8 item 31 |
| §9 (implicit) | ADR-by-LLM retirement | Phase 9 item 35 |

These will be **referenced** in Phase 5 design where the loop interacts
with them (e.g. Phase 5 should NOT add new ADR-writing executors), but
the fixes themselves are someone else's session.

---

## Cross-cutting synthesis: what Phase 5 must do

Distilling the audit and TDD findings against the actual loop code,
the Phase 5 design must:

1. **Sever the `agent_creative` → DONE_WITH_CONCERNS → TERMINAL_OK
   path.** Either remove `agent_creative` from cron dispatch (retrofit
   plan item 18, in plan) AND/OR remove `DONE_WITH_CONCERNS` from
   `TERMINAL_OK`. Both are independently sufficient; together they're
   belt-and-braces.
2. **Bind quality to a real metric.** Default `execute_eval` to the v2
   eval and `hard_pass_rate`, not `eval_v1.py + avg_unique_cites_per_q`.
   Old metrics stay as secondary diagnostics.
3. **Isolate ticks.** Worktree-per-tick (retrofit plan item 19, in plan).
   Resolve the state-reconciliation open question via file-lock.
4. **Prune the graveyard.** Every 6th MAINT tick (retrofit plan item
   20, in plan).
5. **Forbid speculative abstraction.** Triangulation gate (retrofit
   plan item 21, in plan) + log-budget for `triangulation-exempt`
   bypasses.
6. **Cap loop throughput.** Rate-limit creation, not just delete
   artefacts after the fact. Specifically: max N agent_creative-style
   design docs per week (zero if `agent_creative` is fully removed
   from cron; otherwise small).
7. **Surface live state.** A current-tick observability surface
   beyond `ralph_state.json::in_progress` (operator dashboard or
   simple JSON the operator can `cat` mid-tick).
8. **Make resumability explicit.** Operator-only restart, requires
   fresh backlog review, requires v2-eval-as-default-metric verified
   in same commit that removes `RALPH_STOP`.

Items 1–5 are inside the existing PHASE_5_LOOP_TAMING_PLAN. Items 6–8
are the Phase 5 design proposal's contribution.
