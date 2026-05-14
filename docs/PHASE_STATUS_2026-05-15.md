# QKG Retrofit Status — 2026-05-15 snapshot

Auto-snapshot from `claude/overnight-research-2026-05-15` branch.
Captures where the retrofit plan (`docs/QKG_RETROFIT_PLAN.md`) actually
stands as of main HEAD `8036d2d`.

The retrofit plan is 40 numbered items in 12 phases. This doc maps
each item to its current state with concrete evidence (commit hash,
file location, test count, etc.).

---

## Phase status

| Phase | Title | Status | Evidence |
|------:|---|---|---|
| 0 | Stop the bleeding | ✅ Done | RALPH_STOP in place; CLAUDE.md retired 18,785× claim; README has neutral About |
| 1 | Build the green bar | ✅ Done | `tests/conftest.py`, `tests/fakes/*`, `tests/test_get_verse.py`, `tests/test_agent_loop.py`; 6 baseline tests + CI workflow |
| 1-fix | CI pip cache | ✅ Done | `.github/workflows/test.yml::cache-dependency-path` |
| 2 | Acceptance gate change | ✅ Done | `ralph_loop.py::python_test_passes` branch (lines ~299–346); `tests/regression/` directory; `STATE_SNAPSHOT.md` surfaces failing tests first |
| 3a-1 | Extract `shared_agent.py` from `app_free.py` | ✅ Done | `shared_agent.py` 999 LOC after 3a-2; `app_free.py` 1148 → 485 LOC |
| 3a-2 | Fix 3 blockers in `shared_agent` | ✅ Done | `AgentCollaborators` dataclass, `tool_discipline_policy` knob, `fallback_chain` config; schema standardised on `v.verseId`; FakeLLMClient e2e tests |
| 3a-3 | Port `app_lite.py` to `shared_agent` | ✅ Done | `app_lite.py` 558 → 277 LOC; `_anthropic_step` + 3 translation helpers in `shared_agent.py`; `tests/fakes/anthropic_client.py` + 3 Anthropic e2e tests |
| 3a-4 | Port `app.py` + `app_full.py` | ⬜ Pending | Awaits operator decision after Phase 4a lands |
| 3b | Fix 4 production bugs (regression-test-first) | ✅ Done | tests in `tests/regression/test_chat_207_whitespace_bug.py`, `test_typed_edges_concat.py`, `test_tool_cache_ttl_race.py`, `test_sse_worker_leak.py`; `sse_pump.py` extracted |
| 3b f-up | 4 sibling whitespace bugs | ✅ Done | `tests/regression/test_chat_whitespace_cluster.py` |
| Hotfix | `compress_tool_result` + `--openrouter` flag | ✅ Done | `tool_compressor.py::full_coverage` kwarg; `app_free.py::PREFER_OPENROUTER` |
| Housekeeping | `.gitattributes` + GH Actions version bumps | ✅ Done | `.gitattributes` at repo root; `actions/checkout@v5`, `actions/setup-python@v6` |
| 4 | Behaviour-asserted eval | 🟡 In progress | Phase 4a infrastructure prompt being executed in operator's local session (this report's overnight window) |
| 5 | Tame the Ralph loop | ⬜ Pending | Plan exists at `docs/PHASE_5_LOOP_TAMING_PLAN.md` |
| 6 | Verify recent unverified work | ⬜ Pending | Re-eval reranker, Qwen3 A/B, validate adaptive routing |
| 7 | Trim sprawl | ⬜ Pending | Drop legacy MiniLM index, consolidate 21 tools, audit `run_cypher` |
| 8 | Resolve strategic ambiguity | ⬜ Pending | Audience, translation toggle (operator paused on Khalifa positioning) |
| 9 | Honest meta-system | ⬜ Pending | Convert LLM-authored ADRs, decide reasoning-memory subgraph, measure Ralph ROI |
| 10 | Frontend cleanup | ⬜ Pending | Split `index.html`, fix `marked.parse` O(n²) |
| 11 | Restart Ralph loop on new discipline | ⬜ Pending | Gates on Phases 4 + 5 |

## Headline metrics

| Metric | Pre-retrofit | Current | Delta |
|---|---:|---:|---:|
| `app_free.py` LOC | 1,148 | 485 | −58% |
| `app_lite.py` LOC | 558 | 277 | −50% |
| `app.py` LOC | 587 | 587 | — |
| `app_full.py` LOC | 616 | 616 | — |
| `chat.py` LOC | 2,497 | ~2,510 | +0.5% (Bug B refactor) |
| `shared_agent.py` LOC | (didn't exist) | 1,327 | new |
| `sse_pump.py` LOC | (didn't exist) | 69 | new |
| Real test count | ~0 (one A/B harness) | 74 | +74 |
| `tests/regression/` count | 0 | 7 files | +7 |
| Failing tests on main | (no infra) | 0 | 0 |
| xfailed tests on main | (no infra) | 0 | 0 |
| CI workflow | none | green | live |
| Pre-commit hooks | none | live | active |
| Coverage on `shared_agent.py` | n/a | 44% | climbing |
| Bugs fixed in production code | 0 | 8 | — |
| Branches merged to main | 0 | 14 | — |
| Force-pushes to main | 0 | 0 | preserved discipline |

## Audit findings — addressed vs outstanding

Cross-references `docs/QKG_AUDIT.md` (the eight-consultant review).

### Addressed

- **#1 IR scientist — "18,785× speedup" + cache-strength framing**: retired in `CLAUDE.md` (Phase 0 commit, May 13).
- **#3 Agentic engineer — discipline policy hardcoded**: moved to config knob in Phase 3a-2.
- **#4 Senior engineer — daemon-thread leak (`app_free.py:1087`)**: fixed in Phase 3b (Bug D); `sse_pump.py` extracted.
- **#4 Senior engineer — Cypher string-concat (`chat.py::tool_query_typed_edges`)**: fixed in Phase 3b (Bug B); parameter-bound via `WHERE type(r) = $etype`.
- **#4 Senior engineer — tool-cache TTL race (`chat.py::_tool_cache_get`)**: fixed in Phase 3b (Bug C); now reads wall-clock inside the lock.
- **#4 Senior engineer — chat.py:207 whitespace bug**: fixed in Phase 3b (Bug A); 4 sibling sites swept in Phase 3b follow-up.
- **#4 Senior engineer — no real test coverage**: 74 tests now, regression directory established, CI live.
- **#4 Senior engineer — four-apps duplication**: ⚠️ partially addressed. `app_free.py` and `app_lite.py` are now thin wrappers around `shared_agent`. `app.py` and `app_full.py` still pending (Phase 3a-4).
- **Schema split (`v.reference` vs `v.verseId`)**: confirmed aliases (6,231 / 6,231 / 0 divergent); standardised `shared_agent.py` on `v.verseId` in Phase 3a-2.

### Outstanding (still flagged by the audit)

- **#1 IR scientist — eval methodology**: ⏳ Phase 4 in progress (4a infrastructure underway during this report's overnight window).
- **#2 KG architect — legacy MiniLM vector index still present**: ⬜ Phase 7.
- **#2 KG architect — reasoning-memory subgraph entangles telemetry with substrate**: ⬜ Phase 9.
- **#2 KG architect — 4 missing composite indexes**: ⬜ Phase 7 (script exists in `data/ralph_*.md` from earlier Ralph ticks).
- **#3 Agentic engineer — 21 tools, agent uses 4–6 per query**: ⬜ Phase 7.
- **#3 Agentic engineer — Query Routing Rubric is prompt-based**: ⬜ Phase 7.
- **#3 Agentic engineer — `run_cypher` is a footgun**: ⬜ Phase 7.
- **#5 Religious studies — Khalifa positioning**: ⏳ Operator-deferred (per-context decision; not blocking).
- **#6 Product strategist — no audience picked, no roadmap distinct from engineering backlog**: ⬜ Phase 8.
- **#6 Product strategist — 3D viz is demo-ware**: ⬜ Phase 8 / Phase 10.
- **#7 Engineering manager — LLM-authored ADRs**: ⬜ Phase 9.
- **#7 Engineering manager — Ralph loop ROI unmeasured**: ⬜ Phase 9 (depends on Phase 5 isolation work).
- **#8 First-principles skeptic — "does this need to be a graph at all?"**: ⬜ would require Phase 4 eval ablations.

### Honest gap analysis

The retrofit has shipped **infrastructure work** at scale, addressed **most of the senior engineer's concrete bug list**, and partially addressed the **four-apps duplication** (50% done by file count, ~60% by LOC since app_free was the biggest). 

It has shipped **zero changes** that a user landing on the deployed site would notice. The product-facing audit findings (translation positioning, audience, 3D viz, eval credibility) are all still outstanding.

This is consistent with the plan — the retrofit deliberately starts with foundation work and reaches product-facing items in Phase 8. But it's worth naming explicitly: 14 merges in, the **user-facing answer quality is provably identical to where it was on 2026-05-13** (trajectory diffs confirm this, three times).

Phase 4 is the inflection point. Once a behaviour-asserted eval exists and is calibrated, every subsequent merge gets graded against real quality. Everything done so far has been graded against "did the test we wrote pass" — which is necessary but not sufficient.

## Branches alive on origin

- `main` at `8036d2d`
- `phase-3a-port-lite` at `8036d2d` (merged; safe to delete remotely)
- `phase-4a-eval-infrastructure` — possibly live, in operator's overnight Phase 4a session
- `claude/overnight-research-2026-05-15` — this branch (research notes only)
- `claude/add-claude-documentation-ZypkY` — predates retrofit; never triaged
- `claude/evaluate-karpathy-research-TCxjg` — predates retrofit; never triaged
- `gh-pages` — Github Pages

## Suggested next actions

These are advisory; operator decides.

1. **Merge Phase 4a** (when the overnight session reports complete and CI is green). Standard FF.
2. **Triage the two stray claude/\* branches** — `git log --oneline -3 origin/claude/add-claude-documentation-ZypkY` and decide keep/delete. Has been pending for 13 days.
3. **Decide next phase after 4a:**
   - **Phase 4b** (operator-led, author 50q production set) — biggest unlock for everything downstream
   - **Phase 3a-4** (mechanical, port app.py + app_full.py) — completes the refactor narrative
   - **Phase 8** (strategic, audience + Khalifa positioning) — biggest user-facing risk
4. **Worth considering: interleave Phase 4 sooner than the plan suggests.** Five phases of code work without an eval as gate is a long time. After 4a/4b/4c land, every subsequent merge can be graded.

---

Generated by `claude/overnight-research-2026-05-15` during operator's sleep window. Read-only; no production code touched on this branch.
