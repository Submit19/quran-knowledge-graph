# QKG Retrofit Plan

Authored 2026-05-13 after a deep multi-consultant audit + a read of Kent Beck's *Test-Driven Development: By Example*. Companion doc: `docs/QKG_AUDIT.md`.

This is the **sequenced operation list** for retrofitting TDD discipline and trimming sprawl. Items are ordered by dependency — earlier items unblock later ones. Items 1–10 must precede resuming the Ralph loop or it will encode existing problems deeper.

---

## Headline guidance

- **Don't restart from scratch.** The Neo4j graph is the irreplaceable asset. Retrofit the discipline, not the code.
- **Stop the Ralph loop before changing the gates.** The loop will fight the discipline change if left running. Pause it for ~1 week of human attention (Phases 0–5), then unleash it on the new acceptance criteria.
- **Single most important item: change the acceptance gate from `file_min_bytes` → `python_test_passes`** (item #8 below). Without it, everything else regresses on the next 50 ticks.

---

## Phase 0 — Stop the bleeding (1–2 hours)

1. **Pause the Ralph loop** — write `data/RALPH_STOP` and disable the cron / close the session that hosts it.
2. **Retire misleading marketing claims from `CLAUDE.md`** — delete "18,785× speedup"; reframe "5× MAP@10" with sample size (n=22) and absence of CIs.
3. **Add a Khalifa disclosure** to README and (eventually) a UI banner. One paragraph; surfaced before any answer is read.

## Phase 1 — Build the green bar (Day 1–2)

4. **Install pytest + mockable Neo4j fixture** (synthetic ~10-verse graph or test-scoped DB). *(Beck: Isolated Test.)*
5. **Write the first failing test for `tool_get_verse`** — red then green. First green bar. Commit.
6. **Build a mockable LLM client** (Self Shunt) — returns canned `tool_use` payloads so the agent loop is testable without API calls.
7. **Wire pre-commit / CI to run tests** — failing tests block commits.

## Phase 2 — Change the acceptance gates (Day 2)

8. **Replace `file_min_bytes` / `file_exists` in `ralph_backlog.yaml` with `python_test_passes`.** *(Beck: Red→Green is the only completion signal.)*
9. **Rewrite `STATE_SNAPSHOT.md`** so the top line is the current failing test, not the top backlog item. *(Beck: Broken Test.)*
10. **Create `regression_tests/`** — every bug from the audit gets a failing test added *before* the fix.

## Phase 3 — Eliminate the worst duplication (Day 3–4)

11. **Refactor `app.py` / `app_full.py` / `app_lite.py` / `app_free.py`** into `shared_agent.py` + four thin config wrappers. *(Beck: eliminate duplication. ~600 LOC of copy-paste eliminated.)*
12. **Fix daemon-thread leak on client disconnect** (`app_free.py:1087`) — regression test first.
13. **Fix Cypher string-concat in `tool_query_typed_edges`** (`chat.py:520`) — regression test first.
14. **Fix tool-cache TTL race** (`chat.py:2263`) — regression test first.

## Phase 4 — New behaviour-asserted eval (Day 4–5)

15. **Build a 30–50 question Test List eval.** Each is a falsifiable behaviour assertion (tool path, citation set, structural properties) — not a citation count. *(Beck: Test List.)*
16. **Retire `avg_unique_cites_per_q` as headline metric.** Keep as secondary diagnostic only.
17. **Run the new eval, publish baseline with CIs.** This is the *real* attractor the loop converges toward.

## Phase 5 — Tame the Ralph loop (Day 5–7)

18. **Strip loop scope to code/eval/refactor only** — remove research-summarisation, ADR backfill, vault hygiene from the loop's diet.
19. **Isolate each tick** — worktree-per-tick or container-per-tick; no state pollution between iterations.
20. **Do-Over MAINT subtask** — every 6th MAINT, prune `data/ralph_agent_*.md` + `data/ralph_analysis_*.md` for done-shipped tasks older than 14 days.
21. **Forbid speculative abstraction** — no new classifiers / profiles / routing tables without two failing tests that triangulate them. *(Beck: Triangulate.)*

## Phase 6 — Verify recent unverified work (Week 2)

22. **Re-eval `bge-reranker-v2-m3` on QRCD** — the "reranker drops hit@10 50%" claim was on the *old* English-only model; never re-measured after the swap.
23. **Run the queued Qwen3-Reranker A/B** (p78 in backlog) against the new bucketed eval.
24. **Validate the adaptive-routing prediction** — +50% hit@10 on non-BROAD was a prediction, not a measurement.
25. **Blind-regrade `data/eval_v1_results.json`** with a second model to separate citation-volume from correctness.

## Phase 7 — Trim sprawl (Week 2–3; can run parallel to Phase 6)

26. **Drop the legacy `verse_embedding` MiniLM vector index** — no production callers, measured harmful.
27. **Add the 4 missing composite indexes** from `fc700f2`'s audit.
28. **Consolidate 21 tools toward 8–10.** Start with the 6-tool etymology cluster → 1–2 tools with mode args.
29. **Promote `classify_query()` from prompt to code.** Demote prompt rubric to fallback.
30. **Audit + log every `run_cypher` invocation.** Regression-test the denylist.

## Phase 8 — Resolve strategic ambiguity (Week 3)

31. **Pick an audience** — Submitters / academic researchers / agent-tooling developers / all-three-with-modes.
32. **Add a translation toggle** (Sahih International or Pickthall as second corpus). Defuses Khalifa-only credibility risk.
33. **Demote the 3D viz from primary UX** to optional toggle / demo.
34. **Write a one-page product brief** — who, what, why, success metric — next to `CLAUDE_INDEX.md`.

## Phase 9 — Honest meta-system (Week 3–4)

35. **Stop generating ADRs by LLM from commit messages.** Convert ADRs 0013–0032 to "Decision Logs"; reserve ADR format for human-authored future decisions.
36. **Decide on the reasoning-memory subgraph** — separate Neo4j DB or `:Telemetry` label-guard. Stop entangling telemetry with substrate.
37. **Measure the Ralph loop's ROI** — token cost per tick × ticks per day vs. equivalent direct human work.

## Phase 10 — Frontend cleanup (Month 2; lower priority)

38. **Split `index.html`** into shell + `chat.js` + `graph.js` + `citation.js`.
39. **Fix `marked.parse(currentText)` O(n²) on streaming.**

## Phase 11 — Resume the loop on new discipline (end of Week 1)

40. **Restart Ralph loop** with new acceptance criteria (`python_test_passes` only), narrower scope (code/eval/refactor), Broken-Test handoff. *(Beck: dynamic attractor.)*

---

## Augmenting / supporting tools (install in phase noted)

### Foundation (Phase 0–1)
- **`uv`** (Astral) — replace pip/venv. 10–100× faster cold-start; deterministic lockfile.
- **`pre-commit` + `ruff` + `mypy`** — lint, format, type-check on every commit.
- **`devcontainer.json` or nix flake** — reproducible env; matters once ticks run in worktrees.
- **`Pydantic` for tool schemas** — replace dict-shaped returns with typed models. Closes the audit's "inconsistent return shapes" finding as a type error.

### Build (Phase 1–4)
- **Langfuse (self-hosted) or LangSmith (managed)** — LLM observability. Traces every prompt, tool call, token cost. Drop-in with a decorator.
- **`promptfoo` or Inspect AI** — prompt regression as CI gate. Wire to Phase 4's eval set.
- **GitHub Actions CI that runs the eval on every PR** — every change accountable to the eval.
- **`Pydantic` models for tool schemas** (continues from foundation).

### Once eval works (Phase 4+)
- **DSPy** — compile prompts against the eval set. Replaces hand-tuned prompts with optimized ones.
- **Expose QKG as an MCP server** — biggest strategic add. Reusable, embeddable, opens new audiences. Pairs cleanly with Phase 3's shared-agent refactor.
- **`camel-tools`** — academic-grade Arabic NLP; expands user-input coverage.
- **Inspect AI** — adversarial / safety eval for Phase 6.

### Supporting stack (when needed)
- **`neo4j-migrations`** — versioned schema migrations.
- **`DVC`** — data version control for `data/answer_cache.json`, eval results, embeddings.
- **Conventional Commits + `git-cliff`** — auto-generated CHANGELOG.md.
- **`Playwright`** — E2E browser tests when the frontend splits.
- **`pytest-watch`, `pytest-xdist`, `pytest-cov`** — fast dev loop, parallel runs, coverage.

### Process plugins (meta)
- **ADR-tools CLI** — replaces Haiku-generated ADRs with disciplined human-authored ones.
- **Weekly external shadow review** — quarterly outside-eyes audit prevents drift.
- **`mkdocs-material` or `pdoc`** — living docs generated from code.
- **Operator weekly notebook** — Monday review of last-week metrics from Langfuse + Ralph ticks.

---

## Seven evaluation/test additions that compound with TDD+Ralph

1. **Property-based testing (Hypothesis)** — generative; multiplies coverage. Add in Phase 1.
2. **LLM-as-judge with calibrated rubric** — continuous quality signal instead of binary. Phase 4.
3. **Differential / shadow testing** — diff old-vs-new on real queries. Critical for Phase 3 refactor.
4. **Adversarial eval** — hostile prompts, missing-verse queries, theological traps. Phase 6.
5. **Cost + latency observability** — per-request + per-tick token usage and latency. Phase 5.
6. **User feedback signal** — thumbs up/down on answers → `:UserRating` node. Phase 8.
7. **Snapshot regression** — store every eval answer; diff on every change. Phase 1.

---

## Critical path

```
Phase 0 (stop loop)
  → Phase 1 (pytest + first green bar)
    → Phase 2 (change gates)
      → Phase 3 (refactor 4 apps + bug fixes)
        → Phase 4 (new eval)
          → Phase 5 (tame loop)
            → Phase 11 (restart loop on new discipline)

After loop restarts, parallel:
  Phase 6 (re-eval)
  Phase 7 (trim sprawl)
  Phase 8 (strategy)
  Phase 9 (meta-system)
  Phase 10 (frontend, lower priority)
```

**Total human attention before loop restart: ~1 week (Phases 0–5).** After that the loop carries Phases 6–10 on the new gates.

---

## Acceptance criteria for "Phase 0 complete"

- `data/RALPH_STOP` exists and cron is paused (or session terminated).
- `CLAUDE.md` no longer contains "18,785×" or any speedup framed as cache-hit-vs-cold-call.
- `CLAUDE.md`'s QRCD claim is reframed with n=22 + caveat.
- `README.md` has a Khalifa disclosure paragraph in the first screen of content.
- A commit lands on a new branch (not main) with these changes, clearly labelled `phase-0: stop the bleeding`.
- **No code beyond docs/config has been changed.** Phase 1 happens in a separate session.

---

## Don't do (anti-patterns)

- ❌ Don't start over / rewrite from scratch — see "Headline guidance".
- ❌ Don't restart the Ralph loop until Phase 5 lands.
- ❌ Don't merge Phase 0 to `main` until Phase 1 tests exist — leave it on a branch so the loop, when restarted, can't run against partial state.
- ❌ Don't auto-progress to Phase 1 in the same session — Phase 0 is doc + config only, fast to review.
- ❌ Don't add new features during the retrofit. Resist the urge to "while I'm in there".

---

## Source

Built from:
- A multi-consultant audit (IR scientist, KG architect, agentic-systems engineer, senior engineer, religious-studies scholar, product strategist, engineering manager, first-principles skeptic).
- A read of Kent Beck, *Test-Driven Development: By Example* (2002 draft, 132 pages).
- Direct exploration of the QKG codebase, eval results, ADRs, and Ralph loop infrastructure.

Full audit: `docs/QKG_AUDIT.md`.
