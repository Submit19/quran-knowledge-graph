# Phase 5 — Ralph Loop Reconnaissance

_Authored 2026-05-22 in worktree `intelligent-lehmann-dc26aa` on branch
`claude/phase5-ralph-design-2026-05-22`. Pure research; no runtime
changes; loop remains paused via `data/RALPH_STOP`._

This document answers, in order:

1. What IS the Ralph loop?
2. What is its relationship to `autoresearch.py` / `autoresearch_local.py`?
3. What failure mode caused the pause? (RALPH_STOP introduction context)
4. What's already been tried and rejected?
5. What does the QKG retrofit plan's Phase 5 specifically require?

Every claim below is grounded in a file or commit on `main` as of HEAD
`5b03255` (2026-05-21). Inline citations follow Phase-5-author convention:
`path/to/file.py::function` for code; `path/to/doc.md` for prose; short
SHAs for commits.

---

## 1 · What IS the Ralph loop?

A self-iterating Python orchestrator that picks the highest-priority
unblocked task from a YAML backlog, runs a typed executor against it,
verifies acceptance criteria, and writes the outcome to durable state
files. The pattern is borrowed from
[snarktank/ralph](https://github.com/snarktank/ralph) (Geoffrey Huntley
+ Ryan Carson) plus [obra/superpowers](https://github.com/obra/superpowers)
for the gate-function discipline.

### Component map

| File | LOC | Role |
|---|---:|---|
| `ralph_loop.py` | 951 | Library: state I/O, picker, executors, gate functions |
| `ralph_tick.py` | 59 | CLI: run one tick (auto-pick or `--task <id>`) |
| `ralph_run.py` | 218 | Wrapper: loop until completion or N ticks, optional auto-commit/push, daily token caps |
| `ralph_backlog.yaml` | 1,407 | Human-editable task queue (entries are tasks with id/type/priority/blockers/spec/acceptance) |
| `ralph_state.json` | 2,738 | Auto-managed: `done_task_ids`, `quarantined_task_ids`, `attempts`, `api_usage`, `history` (FIFO-capped at 500) |
| `ralph_log.md` | 108 | Append-only markdown table, one row per tick + a top "Codebase Patterns" block |
| `RALPH.md` | 284 | Operator-facing how-to + design rationale |
| `scripts/CRON_BRIEF.md` | 98 | The verbatim brief read by each cron-fired subagent |
| `data/RALPH_STOP` | 21 | Belt-and-braces halt file (checked by CRON_BRIEF step 1) |

### Task types and current executor coverage (`ralph_loop.py::EXECUTORS`)

| Type | Executor | Real or stub? | Notes |
|---|---|---|---|
| `eval` | `execute_eval` | Real | Runs an eval script, computes a metric, compares to baseline, marks REGRESSION if dropped > threshold |
| `cypher_analysis` | `execute_cypher_analysis` | Real | Three sub-modes: inline Python script, raw Cypher, or `query_kind: manual` (operator produces deliverable, executor stubs the path and lets the gate validate) |
| `cleanup` | `execute_cleanup` | **No-op DONE placeholder** | Returns DONE unconditionally. All real cleanup work happens via the operator subagent before the executor is called — the gate function is what actually verifies anything |
| `agent_creative` | `execute_agent_creative` | Real, two backends | `openrouter` (default; calls `gpt-oss-120b:free`) or `manual` (defers to operator subagent + gate) |
| `manual` / `external_run` | — | Falls through to `execute_skipped` | Returns SKIPPED |
| `prompt_variant` / `embed_op` / `cache_op` | — | **Stubs** | Listed as task types in `RALPH.md` table but no executor in `EXECUTORS` — fall through to `execute_skipped` |

### Gate functions — what the loop calls "verification"

Two layers run after the executor and can demote a `DONE` to `FAILED`:

1. **`verify_acceptance(task, result)`** (`ralph_loop.py::verify_acceptance`).
   Five check shapes: `file_exists`, `file_min_bytes`, `metric_above`,
   `metric_at_least_baseline`, raw `python` eval, and (the canonical
   one Phase 2 of the retrofit installed) `python_test_passes`.
2. **`quality_gate()`** (`ralph_loop.py::quality_gate`). A subprocess
   that smoke-imports `CORE_MODULES = [chat, app_free, reasoning_memory,
   retrieval_gate, citation_verifier, ref_resolver, ralph_loop]`. Runs
   only when `spec.commits_code: true`. Fast — < 2s when Neo4j is up.

If any check fails, the result is demoted to FAILED and the task stays
in the backlog. After `MAX_ATTEMPTS_DEFAULT = 3` failures the task is
moved to `quarantined_task_ids` and skipped by the picker.

### Tick lifecycle (single tick)

```
ralph_tick.py
  → ralph_loop.tick()
      pick_next_task()                   # priority-sorted + blockers + types filter
      attempts[task_id] += 1
      state.in_progress = task_id        # written immediately
      save_state()
      result = EXECUTOR[task.type](task) # executor runs; can mark FAILED/NEEDS_CONTEXT/BLOCKED
      verify_acceptance(task, result)    # gate 1: declared checks
      if spec.commits_code: quality_gate()  # gate 2: import smoke
      append "PATTERN: ..." lines from notes to Codebase Patterns block
      state.in_progress = None
      state.tick_count += 1
      if status in TERMINAL_OK:  done_task_ids.append(id)
      elif attempts >= max: quarantined_task_ids.append(id)
      api usage accounting (24h window) for OpenRouter spend
      save_state()
      append_log()                       # markdown row
```

### Loop wrapper (`ralph_run.py`)

Repeats `tick()` up to `--max` iterations. Three exit conditions:

- **Project complete** (`is_project_complete()` against
  `ralph_backlog.yaml::project_completion`) → exit 0.
- **Queue exhausted** (picker returns `None`) → exit 0 if project
  criteria also met, else exit 1.
- **Max iterations** reached → exit 1.

Pacing knobs: `--max-calls-per-day`, `--max-tokens-per-day`,
`--min-api-gap-sec` (default 4s → ≤15 req/min). The 24h windowed
usage is tracked in `state['api_usage']['window']`.

### Cron / subagent harness (`scripts/CRON_BRIEF.md`)

The actual orchestration is **not** `ralph_run.py` — it's a Claude Code
session fired by scheduled wake-up that reads `scripts/CRON_BRIEF.md`
verbatim and acts as the executor for `agent_creative` tasks with
`RALPH_AGENT_BACKEND=manual`. The cron pattern was:

- Wake every ~30 min.
- Sync with GitHub (`git pull --rebase && git push`).
- Decide cycle from `tick_count`:
  - `% 6 == 0` → MAINTENANCE tick (memory hygiene, ADR drift, prune)
  - `% 3 == 0` (and not MAINT) → RESEARCH tick (process 1–3 items from
    the research queue; extract findings to `proposed_tasks.yaml`)
  - else → IMPL tick (proposal review + pick top backlog task)
- Tool-call soft cap 35, hard cap 50.
- Commit + push at end.

The CRON_BRIEF orchestration is layered _on top of_ `ralph_loop.py` —
the Python library is what verifies the deliverable; the subagent is
what produces it for `agent_creative` and inline-script
`cypher_analysis` tasks.

### Status taxonomy

From `ralph_loop.py` lines 59–67 (obra/superpowers-derived):

```
DONE                — succeeded, acceptance verified
DONE_WITH_CONCERNS  — succeeded but soft-pass (no acceptance specified,
                      or agent output needing review)
NEEDS_CONTEXT       — couldn't run; missing inputs (e.g. API key, spec field)
BLOCKED             — external blocker (Neo4j down, server crashed)
REGRESSION          — ran cleanly but metric dropped past threshold
FAILED              — ran with error OR gate function rejected
QUARANTINED         — ≥ MAX_ATTEMPTS failures
SKIPPED             — task type not auto-runnable (manual / external_run)
RUNNING             — internal; transient
```

`TERMINAL_OK = {DONE, DONE_WITH_CONCERNS, SKIPPED}` is the set the loop
treats as "task complete; record it in done_task_ids". Note the
critical inclusion of **DONE_WITH_CONCERNS** in that set — the audit's
"load-bearing fiction" finding turns on this exact line.

### Empirical state at pause (from `ralph_state.json`)

- `tick_count`: 121 (across ~13 days of activity, 2026-05-07 → 2026-05-12)
- `last_tick`: 2026-05-12T17:44Z
- `done_task_ids` length 67; **unique 57** (10 duplicates — the same
  task id appears twice or more, because re-attempts that flipped to
  DONE were appended each time without dedup)
- `quarantined_task_ids`: **empty** — the 3-strikes rule never fired
  on a terminal-failed task during the recorded period (the duplicates
  in `done_task_ids` show the loop usually broke through retry)
- `attempts` (in-flight, non-zero): `{from_neo4j_crawl_enable_slow_query_log:
  2, from_neo4j_crawl_check_neo4j_version: 3, from_neo4j_yt_mcp_tool_description_audit:
  3, from_blog_stateful_ai_memory_path_convention: 1, share_minilm_across_modules:
  2}`. Five tasks were mid-retry when the loop paused; three were at
  the quarantine threshold.
- `baselines`: **empty** — no metric baselines ever captured. Every
  eval-type task ran without `metric_at_least_baseline` enforcement
  because there was no baseline to compare against. (More on this in §3.)
- `api_usage.calls_total`: 17 (only the `openrouter`-backend
  `agent_creative` ticks counted; manual-backend ticks accumulated
  zero token usage because they delegated to a Claude Code session
  running on Max-sub).
- `history` (capped at 500, currently 97): status mix below.

**Tick status mix across the 97-entry history window:**

| Status | Count | % of terminal |
|---|---:|---:|
| DONE | 22 (21 new + 1 legacy "success") | 23% |
| DONE_WITH_CONCERNS | 44 | 45% |
| FAILED | 19 (18 new + 1 legacy "failed") | 20% |
| NEEDS_CONTEXT | 12 | 12% |

**Of "successful" outcomes (DONE + DWC), DWC is 44 / 66 = 67%** — i.e.
two-thirds of the loop's "wins" were soft passes. This matches the
audit's 62% finding (audit's window was 79 ticks; mine is 97; the
ratio is stable).

**By task type:**

| Type | n | DONE | DONE_WITH_CONCERNS | FAILED | NEEDS_CONTEXT |
|---|---:|---:|---:|---:|---:|
| `agent_creative` | 38 | 0 | 36 (95%) | 1 | 1 |
| `cypher_analysis` | 32 | 13 | 4 | 4 | 11 |
| `cleanup` | 26 | 8 | 4 | 14 (54%) | 0 |
| `research` | 1 | 1 | — | — | — |

Three patterns jump out:

- **`agent_creative` is 95% DWC** — almost every tick of this type
  returned `DONE_WITH_CONCERNS` because the executor returns that
  status by design (lines 681–684 of `ralph_loop.py`) and the gate
  function never bumps it back to DONE. The "human review" promised
  by the status name does not happen at this throughput.
- **`cleanup` fails the quality gate >50% of the time** — driven
  entirely by Neo4j unreachability (`Address(('::1', 7687, 0, 0))
  ... WinError 10061`). The gate is correct to fail (it caught real
  import errors); the issue is that the loop ran while Neo4j was
  offline, which the operator's environment frequently was.
- **`cypher_analysis` is 34% NEEDS_CONTEXT** — driven by tasks whose
  spec was missing `query` or `script` and was never fixed before
  retry. The 3-strikes rule did fire here (`from_neo4j_crawl_check_neo4j_version`
  hit 3 NEEDS_CONTEXT in a row), but only NEEDS_CONTEXT, not FAILED;
  on the next retry an operator manually fixed the spec and the task
  recovered to DONE without going through quarantine.

### Graveyard inventory (data/ralph_*.md files)

- `data/ralph_agent_*.md`: **31 files** (4–25 KB each, total ~210 KB)
- `data/ralph_analysis_*.md`: **24 files**
- Together: 55 design / analysis artefacts produced by the loop that
  are not referenced by any other file outside `data/` and `git log`.

Spot-checks of three: all three are well-written, technically credible,
and have **never been merged or implemented as runtime changes**. They
are exactly the "62% DONE_WITH_CONCERNS design docs the operator never
reviewed" that the audit named.

---

## 2 · Relationship to `autoresearch.py` / `autoresearch_local.py`

`autoresearch.py` (367 LOC) is the **predecessor** — an Optuna-based
Bayesian TPE search over `pipeline_config.yaml` parameters that
maximises a composite "QIS" score. It runs the eval against a 15-question
core subset for ~$2–3/trial via the Anthropic API. The local variant
(`autoresearch_local.py`, 404 LOC) does the same against Ollama at zero
API cost.

Differences from Ralph:

| Dimension | autoresearch | ralph_loop |
|---|---|---|
| Optimisation target | Single composite score (QIS) over a fixed 15q subset | Per-task acceptance criteria (file exists / metric / pytest passes) |
| Search algorithm | Optuna TPE (Bayesian) | Operator-priority sort + blockers |
| Decision unit | Parameter vector (yaml config) | Task in a backlog |
| Output | `best_config.yaml` + `autoresearch_log.jsonl` | Code commits, design docs, analyses |
| Cost | ~$100–150 for 50 trials (Claude API) | Effectively zero on Max-sub (manual backend) + ~5 OpenRouter calls/day |
| Failure recovery | Trial fails → ignored; next trial proposed | 3-strikes → quarantine |
| Halt mechanism | `--budget` flag (USD cap) | `data/RALPH_STOP` file + `--max-calls-per-day` |

They share the same goal — "improve the pipeline overnight without
operator attention" — but **operate at different abstraction levels**.
`autoresearch` tunes existing knobs; `ralph_loop` proposes and verifies
new code / design. The two are not coupled — Ralph never invokes
autoresearch and vice versa. Autoresearch is effectively dormant
(`CLAUDE.md` calls it "older infra"; no commits to it since 2026-04).

The retrofit plan does not mention autoresearch directly — it's not
in scope for Phase 5. The implicit understanding: autoresearch is a
narrower, more disciplined tool (clear input/output, real metric, real
budget) that the operator could revive if Phase 4's behaviour-asserted
eval becomes the optimisation target. Phase 5 work does NOT replace
or block autoresearch.

---

## 3 · What failure mode caused the pause?

`data/RALPH_STOP` was introduced in commit `05c81e3` (2026-05-13)
titled "phase-0: stop the bleeding — retire misleading claims". The
commit message + the body of `data/RALPH_STOP` make the framing
explicit: the pause is **not** because the loop crashed or produced
broken code. It is because the loop was **growing faster than the
product and the audit declared its acceptance gates inadequate**.

Quoting `data/RALPH_STOP`:

> Do not resume until Phase 5 lands (see plan). The cron / session that
> hosts the loop has been stopped separately; this file is a belt-and-braces
> signal read by:
>   - scripts/CRON_BRIEF.md (step 1: halt check)
>   - scripts/state_snapshot.py (marks status as HALTED)
>   - CLAUDE_INDEX.md (stop-condition reference)

The audit (`docs/QKG_AUDIT.md` §7, the Engineering Manager perspective)
named four failure modes:

1. **62% `DONE_WITH_CONCERNS` is a load-bearing fiction.** The "concerns"
   are absorbed silently because the human-review step never happens
   at scale. (Confirmed: 67% of successful outcomes in my snapshot.)
2. **The loop is rewriting its own scaffolding.** "Max 20x, 30-min cadence,
   end-of-tick prep, Sonnet pre-warming, ADR backfill. *Meta-system
   gaining mass faster than the product.*"
3. **LLM-authored ADRs are a category error.** ADRs encode human
   judgement; Haiku reading commit messages produces confabulations
   of decisions. (Confirmed: `QKG Obsidian/decisions/0013–0044` are
   visibly machine-authored; their text describes _what happened in a
   commit_, not _why a human chose between alternatives_.)
4. **Bus factor terrible.** "Loop keeps ticking out work no one reviews;
   queues choke within a week."

Beck's TDD lens (`docs/QKG_AUDIT.md`, TDD section) added a fifth:

5. **The loop has no Red.** Red → Green → Refactor; QKG's loop is
   brief → design doc → commit. No failing test defines done. That's
   why 62% of ticks are DWC — no green bar to converge to.

These five failure modes are the canonical "why we paused" list. They
are NOT bugs in `ralph_loop.py` — they're structural defects in the
loop's _attractor_: what work the loop optimises for, and what
acceptance criteria call that work "done".

### Side bug, post-pause: app_free.py degradation

Separately, commit `bb45311` (2026-05-19) diagnosed a degradation in
`app_free.py` over a long sequential workload — `sse_pump.pump_worker_into_sse(dedup_text=True)`
emits no SSE frames during final-answer generation; the daemon-thread
fix only polls stop_event between agent turns, not inside the 600s
Ollama POST. This is a real bug but it is **not the reason the loop
paused** — the loop had already been paused for 6 days when this was
diagnosed. The audit references this only obliquely (Phase 3 item 12
in the retrofit plan).

---

## 4 · Already tried and rejected (the "rejected experiments" memory)

The Ralph loop's own output is its own rejected-experiments archive.
Every design doc in `data/ralph_agent_*.md` is, by status, a
DONE_WITH_CONCERNS deliverable that **was not promoted** to code. They
are not all bad — some are excellent design — but as a class they
represent ideas the operator paused on review and never circled back to.

Spot-check sample (read in full during reconnaissance):

| File | Type | Verdict at pause |
|---|---|---|
| `ralph_agent_from_adaptive_routing_2profile_spike.md` | agent_creative | 2-profile reranker gate. **Shipped** in code (commit `672cc68`) but the QRCD evidence the design rested on was never re-measured on the new multilingual reranker → audit §1 |
| `ralph_agent_from_neo4j_yt_sufficiency_gate.md` | agent_creative | 3-way sufficiency gate (sufficient/hop_more/replan). Never shipped. Operator pre-Phase-5 view: probably won't ship before Phase 4 eval is real. |
| `ralph_agent_from_ai_graph_reflexion_pattern.md` | agent_creative | Reflexion memo schema. Speculative abstraction — exactly the shape Phase 5 item 21 forbids. |
| `ralph_agent_from_ralph_yt_04_parallel_worktree_spike.md` | agent_creative | Parallel worktree spike for the loop itself. ADR 0044 marks it "deferred." Foundation for Phase 5 item 19. |
| `ralph_agent_propose_streaming_progress_indicator.md` | agent_creative | UX idea. Untouched. |
| `ralph_agent_propose_search_bar_autocomplete.md` | agent_creative | UX idea. Untouched. |
| `ralph_agent_build_multihop_benchmark.md` | agent_creative | 30-question multi-hop benchmark dataset spec. **Shipped** as `data/multihop_bench.jsonl` (commit `c8047ca`); not yet wired to eval. |
| `ralph_agent_propose_session_memory_ux.md` | agent_creative | UX idea. Untouched. |

**Pattern in this graveyard**: the design docs are usually decent; the
problem is the ratio of design-doc throughput to operator-review
throughput. The loop produces these at ~1/day; the operator can
realistically review and decide on ~1/week. The queue grows
monotonically.

Beyond design docs, three specific patterns were tried and rejected:

a. **HippoRAG / PPR retrieval.** Implemented (`hipporag_traverse.py`),
   measured on QRCD across 36 configurations
   (`data/qrcd_hipporag_sweep.json`), definitively underperforms
   vanilla. Documented in `HIPPORAG_REPORT.md`. NOT in the Ralph
   graveyard because it was a deliberate full-implementation experiment,
   not a loop-spawned design doc. Mentioned here only because Phase 5
   should NOT re-propose it.

b. **Auto-merging from Ralph branches to main.** Never enabled; the
   CRON_BRIEF only pushes to feature branches and the operator merges
   via UI / fresh session ([[feedback_merge_via_session]]). Phase 5
   must not enable auto-merge.

c. **Letting the loop edit its own scaffolding.** Several ticks in the
   history table touched `ralph_loop.py`, `CRON_BRIEF.md`, or
   `ralph_backlog.yaml` itself (e.g. `from_ralph_yt_03_audit_negative_prompts`
   rewrote 10 negative-form instructions in CRON_BRIEF.md). Audit §7
   flagged this as "loop rewriting its own scaffolding". Phase 5 plan
   item 18 (scope strip) implicitly forbids this; Phase 5 design
   should make it explicit.

---

## 5 · What does the QKG retrofit plan's Phase 5 specifically require?

From `docs/QKG_RETROFIT_PLAN.md` and the companion `docs/PHASE_5_LOOP_TAMING_PLAN.md`:

### Mandate (retrofit plan, items 18–21)

- **Item 18** — Strip loop scope to code/eval/refactor only. Remove
  research-summarisation, ADR backfill, vault hygiene from the loop's
  diet.
- **Item 19** — Isolate each tick. Worktree-per-tick or container-per-tick;
  no state pollution between iterations.
- **Item 20** — Do-Over MAINT subtask. Every 6th MAINT tick, prune
  `data/ralph_agent_*.md` + `data/ralph_analysis_*.md` for done-shipped
  tasks older than 14 days.
- **Item 21** — Forbid speculative abstraction. No new classifiers /
  profiles / routing tables without two failing tests that triangulate
  them (Beck: Triangulate).

### Concrete design from `docs/PHASE_5_LOOP_TAMING_PLAN.md`

**Scope (item 18) — `EXECUTORS` dict shrinks to:**

```
✅ eval, cleanup, cypher_analysis, cache_op, embed_op
⚠️ prompt_variant (only with python_test_passes gate)
❌ agent_creative (operator-only; remove from cron dispatch)
❌ manual, external_run (already SKIPPED today)
+  regression (new: adds a regression test pulled from xfail once a fix lands)
+  triangulation (new: adds a second test for an existing single-example abstraction)
```

**Tick isolation (item 19) — worktree-per-tick:**

```bash
TICK_ID="tick-$(date -u +%Y%m%d-%H%M%S)-$(uuidgen | head -c 8)"
WORKTREE=".ralph-worktrees/$TICK_ID"
git worktree add -b "ralph/$TICK_ID" "$WORKTREE" main
# Run tick inside the worktree.
# On success: git worktree remove $WORKTREE; git push origin ralph/$TICK_ID
# On failure: preserve worktree for forensics; branch left local
```

State files (`ralph_state.json`, `ralph_log.md`) are written in the
main checkout by a small post-tick reconciliation step, after the tick
branch is committed. Disk cost: ~50–200 MB per active worktree;
cleanup automatic on success.

**Pruning (item 20) — every 6th MAINT tick:**

```python
def prune_graveyard(repo_root, age_threshold_days=14):
    # Remove data/ralph_agent_*.md + ralph_analysis_*.md whose task is
    # DONE-and-shipped AND last-modified > 14 days ago.
    ...
```

**Triangulation gate (item 21) — reject commits that add classifiers / routing tables without ≥2 tests:**

Detection heuristics:
- New function whose name matches `^classify_|^route_|^select_profile|^pick_(tool|model|backend)`
- New dict literal with ≥3 string keys mapping to function/string values, named `*_PROFILES`, `*_BUCKETS`, `*_ROUTES`, `*_DISPATCH`
- New `if/elif` chain with ≥3 branches over a string variable that didn't exist on the previous commit

Bypass: `# triangulation-exempt: <reason>` tag in the commit body.

**Acceptance criteria for Phase 5 complete:**

1. `EXECUTORS` shrunk; `agent_creative` no longer in cron dispatch.
2. Worktree isolation in use; every tick branch named `ralph/<tick_id>`.
3. `prune_graveyard()` in MAINT every 6th tick.
4. Triangulation gate active; tested against 3+ true positives and
   3+ false positives from git history.
5. Pre-restart dry run produces 5+ clean ticks with no operator intervention.
6. `data/RALPH_STOP` STILL in place at end of Phase 5; restart is its
   own operator-approved commit (Phase 11).

### What the Phase 5 plan does NOT cover (gaps for Phase 5 design to fill)

The existing plan covers four of the operator's seven Phase 5 design
dimensions (failure-mode prevention, scope discipline, partial
observability, and quality-bar through pytest gates). It does **not**
cover, or covers thinly:

1. **Observability** — How does the operator see what the loop is
   doing while it runs? `ralph_log.md` is a markdown table read after
   the fact, not a live signal. No dashboard, no current-tick
   status outside `ralph_state.json::in_progress`.
2. **Stop discipline** — Beyond `RALPH_STOP`, what conditions
   auto-pause the loop? Currently: 3-strikes quarantine on per-task
   basis, daily token caps in `ralph_run.py`. No loop-level rate
   degradation pause, no metric-regression auto-halt, no integration
   with operator messaging.
3. **Resumability** — How does the operator restart after a pause?
   Retrofit plan Phase 11 says "delete `RALPH_STOP` in same commit
   that re-enables cron" — but the cron mechanism itself (CRON_BRIEF
   subagent) is not described as restartable. State preservation
   across pauses is implicit, not designed.
4. **Quality bar** — How does the loop know its outputs are good?
   `python_test_passes` is one signal; the new Phase 4 v2 eval is
   another. The plan mentions both but doesn't say how the loop binds
   the v2 eval into per-task acceptance criteria.
5. **Integration with rest of system** — Cache, reasoning-memory,
   eval framework. The retrofit plan strips scope (good); it does NOT
   say how the loop's surviving task types interact with the recently
   shipped systems (BGE-M3 reranking in cache, capable-model baseline
   in `data/eval/v2/`, the 32K `:RETRIEVED` edges in the graph).

The Phase 5 design proposal (next document) addresses these five gaps
while staying inside the four-item retrofit plan envelope.

---

## Headline reconnaissance findings

1. **Ralph is structurally intact and pause-safe.** No code rot; no
   broken paths; `RALPH_STOP` is checked at exactly one entry point
   (CRON_BRIEF step 1) and the cron itself is stopped. Restart is a
   trivial operator action.
2. **The audit's `DONE_WITH_CONCERNS` finding is replicated** on the
   97-tick history window: 67% of "successful" terminal outcomes are
   soft passes, driven entirely by the `agent_creative` executor's
   default-to-DWC return.
3. **The graveyard is real**: 55 `data/ralph_*.md` files, almost none
   merged. Phase 5 item 20 (prune) is necessary but secondary — the
   issue is creation, not deletion.
4. **The 3-strikes rule fires but rarely converts to QUARANTINE.**
   Tasks usually break through via operator-fixed spec on retry. The
   `quarantined_task_ids` list is empty; the `attempts` map shows 5
   tasks in mid-retry at pause. Phase 5 needs to distinguish "retry
   because spec was broken" from "retry because the work is genuinely
   not done".
5. **`autoresearch.py` is unrelated to the Phase 5 work** — it's a
   sibling tool with a tighter loop and a real budget. Out of scope.
6. **The retrofit plan covers 4 of 7 operator design dimensions** —
   gaps are observability, stop discipline beyond RALPH_STOP,
   resumability, full quality-bar binding, and integration with the
   recently shipped systems (BGE-M3, capable-model baseline,
   reasoning-memory).

Phase 2 (audit synthesis) and Phase 3 (design proposal) build on
exactly these findings.
