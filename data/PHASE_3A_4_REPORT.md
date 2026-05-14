# Phase 3a-4 — Final report

Port `app.py` + `app_full.py` to `shared_agent`. Closes the four-apps
duplication that was the audit's #1 tech-debt finding.

## Branch

`phase-3a-4-port-rest` at `7b87e5abba1b0db00ee745c2fe00c3da11914690`

## Commits (4 atomic, no squash)

| Hash      | Title                                                            |
|-----------|------------------------------------------------------------------|
| `7cba4b5` | phase-3a-4: baseline trajectory for app (pre-refactor)           |
| `3f64f22` | phase-3a-4: refactor app.py to thin wrapper over shared_agent    |
| `6b24220` | phase-3a-4: baseline trajectory for app_full (pre-refactor)      |
| `7b87e5a` | phase-3a-4: refactor app_full.py to thin wrapper over shared_agent |

(The `--app` arg was already wired in `scripts/capture_baseline_trajectory.py`
from Phase 3a-3, so the script-change commit listed in the operator brief was
unnecessary.)

## LOC deltas

| File              | Before | After | Delta            |
|-------------------|-------:|------:|-------------------|
| `app.py`          | 587    | 191   | **-67%** (-396) |
| `app_full.py`     | 616    | 209   | **-66%** (-407) |
| `shared_agent.py` | 1,327  | 1,327 | unchanged       |

Four-app totals (post-Phase 3a-4):

```
app.py      :  191
app_full.py :  209
app_lite.py :  277  (Phase 3a-3)
app_free.py :  508  (Phase 3a — original target)
─────────────────────────────────────
total       :  1,185 LOC across all four wrappers
shared_agent: 1,327 LOC (one place where the loop lives)
```

For reference, the pre-Phase-3a wrappers totalled `587 + 616 + 558 +
1148 = 2,909` LOC of mostly-duplicated agent-loop code.

## Test count

**113 passed, 0 xfailed** — no change. The existing
`tests/test_shared_agent_anthropic.py` (FakeAnthropicClient e2e) and
`tests/test_shared_agent_end_to_end.py` cover the code path both new
wrappers funnel through; no new tests added.

## Trajectory diffs

### `app.py`

| Field             | v0 (pre)                                                | v1 (post)                                                         | Comment                                       |
|-------------------|---------------------------------------------------------|-------------------------------------------------------------------|-----------------------------------------------|
| n_events          | 8                                                       | 9                                                                 | +1 ('Model' routing event)                    |
| event_types       | `tool, text, tool, text, tool, graph_update, text, done` | `tool, tool, text, tool, text, tool, graph_update, text, done`    | leading 'tool' (Model) added — same pattern as app_lite |
| tool_names        | Answer cache → Looking up verse → Exploring surah      | **Model** → Answer cache → Looking up verse → Exploring surah     | identical downstream sequence                 |
| has_done          | True                                                    | True                                                              | ✓                                             |
| has_error         | False                                                   | False                                                             | ✓                                             |
| verses_in_done    | `['2:254', '2:256']`                                    | `['2:254', '2:256']`                                              | ✓                                             |
| text_total_chars  | 1771                                                    | 1713                                                              | sampling variance                             |

**Verdict:** structural match. The leading 'Model' tool event is the
shared_agent routing-decision surface that already appeared in
app_lite's v1.

### `app_full.py`

| Field             | v0 (pre)                                                                                                | v1 (post)                                                          | Comment                                                                                                  |
|-------------------|---------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| n_events          | 12                                                                                                      | 9                                                                  | -3 (uncertainty + warning + retry)                                                                       |
| event_types       | `tool, uncertainty, text, tool, text, tool, graph_update, text, warning, retry, verification, done`     | `tool, tool, text, tool, text, tool, text, verification, done`     | adds 'Model'; drops 'uncertainty', 'warning', 'retry'                                                    |
| 'uncertainty'     | present                                                                                                 | **missing**                                                        | expected — `enable_uncertainty_probe=False` because shared_agent doesn't implement the probe yet (Phase 3a-5) |
| 'warning'+'retry' | present                                                                                                 | missing for this query                                             | shared_agent has `_is_simple_lookup` exemption — verse-lookup queries skip retry. Pre-existing shared behaviour (same as app_lite). Retry still fires for non-lookup queries |
| 'verification'    | present                                                                                                 | present                                                            | preserved — wrapper sets `ENABLE_CITATION_VERIFY=1` because shared_agent gates verifier on env var       |
| has_done          | True                                                                                                    | True                                                               | ✓                                                                                                        |
| has_error         | False                                                                                                   | False                                                              | ✓                                                                                                        |
| verses_in_done    | `['2:254', '2:256']`                                                                                    | `['2:254', '2:256']`                                               | ✓                                                                                                        |

**Verdict:** acceptable behaviour-preserving differences. The
uncertainty omission is documented in the commit + module docstring;
the warning/retry omission is shared behaviour for verse-lookup
queries.

## PHASE B gate state

**State (ii)** — `enable_uncertainty_probe` exists in `AgentConfig`
(`shared_agent.py:94`) but NO code branch consumes it. The flag is
decorative. Took the FALLBACK PATH at PHASE D: shipped `app_full.py`
with `enable_uncertainty_probe=False`, documented in the commit message
and the module docstring, recommended Phase 3a-5 follow-up to
implement the probe end-to-end in `shared_agent.agent_stream` and
re-enable the flag.

## Smoke tests

Both apps booted cleanly and `GET /model-info` returned the expected
JSON.

```
$ curl http://localhost:8081/model-info
{"model":"claude-sonnet-4-5","backend":"anthropic","cost":"paid"}

$ curl http://localhost:8083/model-info
{"model":"claude-sonnet-4-5","backend":"anthropic","cost":"paid"}
```

`/model-info` is a new endpoint added by both wrappers (mirrors
app_lite's, which already had it).

## CI status

**Green.** Run IDs `25860589782` (tests) and `25860589780` (eval-v2),
both completed successfully. 113 tests passed; eval-v2 informational
workflow passed in 15s.

## Asks for operator

1. **Variant table mismatch on `app.py`.** The table in
   `docs/PHASE_3A_PLAN.md` marks `citation-density retry`,
   `uncertainty probe`, and `verification` as "yes" for `app.py`. The
   actual pre-refactor code had all three commented out. The port
   preserved the observable behaviour (all three `False`). If the
   intent of the table was "this is the *target* behaviour, fix the
   regression now," tell me and I'll flip the flags in a follow-up.

2. **Variant table mismatch on `app_full.py`.** The table marks
   `reasoning-memory playbook` and `classify_query → rerank knob` as
   "yes" for app_full. The pre-refactor code never wired them up
   (only `app_free.py` did). The port preserved observed behaviour
   (both `False`). Same question — flip in a follow-up if desired.

3. **Citation verifier env coupling.** `shared_agent.agent_stream`
   gates the verifier on both `enable_citation_verifier=True` AND
   `os.getenv("ENABLE_CITATION_VERIFY") == "1"`. The original
   `app_full.py` ran verification unconditionally. The wrapper now
   sets `os.environ.setdefault("ENABLE_CITATION_VERIFY", "1")` at
   import time so app_full's unconditional-verify behaviour is
   preserved without forcing the env flag on for other apps. If
   you'd prefer the verifier be a pure config-flag question (no env
   var), the gating can be relaxed in shared_agent.

4. **Phase 3a-5 scheduling.** Recommended: a separate phase to
   implement `enable_uncertainty_probe` in
   `shared_agent.agent_stream`. The probe needs to fire BEFORE the
   agent loop (it inspects the question with 5-Haiku probes to
   estimate semantic entropy, then conditionally augments the system
   prompt). Should be ~40 LOC in `agent_stream`, plus an
   `uncertainty` event surfaced through the queue. No urgency — it's
   one observable Phase 5 behaviour out of three (verification +
   density retry already work).

## Anything unexpected

- `_is_simple_lookup` exemption (inherited from `app_free.py` →
  `shared_agent`) now applies to `app_full.py` queries too. Pre-
  refactor app_full ran the density-retry unconditionally for *any*
  response with < 30% citation density. Post-refactor, simple
  verse-lookup questions skip the retry. This is arguably more
  sensible — a "What does 2:255 say?" question really only needs one
  citation — but it's a behaviour change worth flagging.
- `app.py` and `app_full.py` both had a hand-rolled `_fetch_verses`
  that used `v.reference` (legacy property). `shared_agent`'s
  version uses `v.verseId` (post-Phase-3a-2 standardisation). Both
  properties exist on Verse nodes in production, so the port is
  drop-in compatible — but verses are now fetched by `verseId`
  instead of `reference`.

## Soft cap status

~2.5 hours elapsed (Part A orient, Part C app.py port, Part D
app_full.py port, Part E push/CI/report). Well under the 6-hour soft
cap — partial 3a-4 contingency unused.

## Where this leaves the plan

After this branch lands, the audit's #1 tech-debt finding (four-apps
duplication) is **mostly closed**:

```
✅ Phase 3a-1    shared_agent.py extracted
✅ Phase 3a-2    3 blockers fixed
✅ Phase 3a-3    app_lite.py ported
🟡 Phase 3a-4    app.py + app_full.py ported  (THIS BRANCH)
⬜ Phase 3a-5    (new) implement uncertainty_probe in shared_agent
```

The only remaining piece is the uncertainty probe (Phase 3a-5).
`app_free.py` (the original target of Phase 3a) is already in
shared_agent.
