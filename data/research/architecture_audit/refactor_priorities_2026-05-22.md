# Architecture Audit — Pass 5: Prioritized refactor list (2026-05-22)

Branch: `claude/architecture-audit-2026-05-22` · HEAD before this commit: `f824f11`
Synthesis of passes 1-4. Read those for the underlying evidence:

- `dead_code_2026-05-22.md` — 26 modules / ~7,950 LOC addressable
- `duplication_2026-05-22.md` — ~1,200-1,300 LOC of duplication; 44-file env scatter; chat.py 2,650 LOC
- `testing_gaps_2026-05-22.md` — 20% direct-test coverage by function count; 4 critical modules at 0%
- `docs_drift_2026-05-22.md` — README/ARCHITECTURE multi-week-stale; system-prompt tool count wrong at runtime

This pass converts findings into a sequenced backlog. Each item has the same shape so future advisor sessions can pick one without re-deriving the rationale.

---

## Backlog table (all items)

Sorted by `(severity desc, effort asc)`. Severity = blast radius if left alone. Effort = XS<30min · S<2h · M=2-6h · L=full-day · XL=multi-session.

| # | Title | Sev | Effort | LOC delta | Files | Source | Risk |
|--:|-------|:---:|:------:|----------:|------:|--------|------|
| 1 | Fix system-prompt tool count (15/10 → 21) | **HIGH** | XS | ±10 lines | 2 prompt files | docs_drift §5 | Runtime; model under-uses tools today |
| 2 | CLAUDE.md etymology bucket off-by-one (6→7) | LOW | XS | 1 char | 1 | docs_drift §6 | Cosmetic but cheap |
| 3 | Delete the 6 unambiguously dead modules | **HIGH** | S | -1,862 | 6 + README/CLAUDE.md | dead_code §1 | Code removal; needs Pass-1 list confirmed |
| 4 | Rename root `test_*.py` → `harness_*.py` | LOW | XS | 0 | 2 | testing_gaps §3 | Removes pytest-collection foot-gun |
| 5 | Consolidate `_load_env` helper into `quran_kg.env` | MED | S | -60 | 5 | duplication §1a | Pure function |
| 6 | Citation-regex consolidation → `ref_resolver` | MED | S | -30, prevents drift | 3-4 | duplication §1b | Single semantic answer |
| 7 | Unify 3 reranker entry points to `model_registry` | MED | S | -20, prevents 2nd ML load | 3 | duplication §3 | Single instance enforced |
| 8 | Centralise Neo4j driver init (`quran_kg.neo4j.get_driver`) | **HIGH** | M | -400 | 44 | duplication §2a | Massive boilerplate kill |
| 9 | README build-pipeline rewrite + dead-module purge | **HIGH** | M | n/a | 1 | docs_drift §1 | Onboarding-blocker |
| 10 | ARCHITECTURE.md rewrite (or delete + repoint) | **HIGH** | M | n/a | 1 + CLAUDE_INDEX | docs_drift §2 | Mermaid is structurally wrong |
| 11 | Khalifa UI banner (Phase 0 #3 closure) | **HIGH** | M | +UI | index.html + README | docs_drift §1c | Credibility risk per QKG_AUDIT §5 |
| 12 | `ref_resolver` test coverage (459 LOC → ≥80%) | **HIGH** | S | +~150 (tests) | 1 new test file | testing_gaps §6 | Pure regex; easiest win |
| 13 | `retrieval_gate` test coverage (213 LOC) | **HIGH** | S | +~80 (tests) | 1 new test file | testing_gaps §6 | Injectable reranker pattern exists |
| 14 | Stamp `PHASE_3A_PLAN.md` as SHIPPED | LOW | XS | 1 line | 1 | docs_drift §7 | Status clarity |
| 15 | `QKG_RETROFIT_PLAN.md` add status column | MED | S | n/a | 1 | docs_drift §7 | ~15 of 40 items now done |
| 16 | `app_free.py` + `shared_agent.py` header docstrings | LOW | S | -10 lines stale | 2 | docs_drift §11 | "ports pending" → done |
| 17 | Archive `PROJECT_SUMMARY.md` + `IMPLEMENTATION_PLAN.md` + `IMPLEMENTATION_PROMPT.md` + `TASK_PLAN.md` | LOW | XS | n/a (move) | 4 | docs_drift §3-4 | Stop maintaining dead docs |
| 18 | `STATE_SNAPSHOT.md` mark paused or delete | LOW | XS | n/a | 1 | docs_drift §9 | Avoid misleading "16 pending" |
| 19 | `SETUP_GUIDE.md` rewrite around bootstrap script | MED | M | n/a | 1 | docs_drift §8 | External-user blocker |
| 20 | `answer_cache.save_answer` + `build_cache_context` tests | MED | S | +~80 (tests) | 1 | testing_gaps §6 | Dedup/cap behaviour untested |
| 21 | `citation_verifier` test coverage (317 LOC) | MED | M | +~150 (tests) | 1 | testing_gaps §6 | Needs NLI/MiniCheck fakes |
| 22 | `app_free.py` async handlers via FastAPI `TestClient` | MED | M | +~250 (tests) | 1 | testing_gaps §6 | 10 handlers, mock Neo4j |
| 23 | `reasoning_memory` test coverage (452 LOC) | MED | M-L | +~200 (tests) | needs testcontainers or fake-Cypher | testing_gaps §6 | Largest test gap; infra question first |
| 24 | Cover 16 untested `chat.py` tool functions | MED | L | +~400 (tests) | many | testing_gaps §1 | Per-tool Cypher fakes; or testcontainers |
| 25 | Coverage report → PR comment | LOW | S | +20 (yml) | 1 | testing_gaps §5 | Visibility |
| 26 | `scripts/cache_passes/` package + unified CLI | MED | M | -150 net | 6 | duplication §2c | Pattern fix; not urgent |
| 27 | Env-var registry (`Settings` + `.env.example` validator test) | MED | M | +60 net | new files + 1 test | duplication §4 | Closes drift trap |
| 28 | App-variant FastAPI extraction → `shared_app.build_app` | **HIGH** | L | -400-500 | 4 + new module | duplication §2b | Finishes Phase 3a; needs e2e per variant |
| 29 | Split `chat.py` per QKG_AUDIT §4 | **HIGH** | L | 0 (move), ~10 files | 1 → 10 | duplication §5 | Highest cognitive value; needs trajectory baseline |
| 30 | Phase 5 Ralph loop strip (parked scaffolding decision) | MED | XL | -3,140 (if strip) | 10 | dead_code §2 | Design-first session; multi-day |
| 31 | Autoresearch fate decision + cleanup | MED | S | -1,623 (if retire) | 3 + README | dead_code §3 | Awaiting operator decision |
| 32 | Archive QRCD harnesses to `scripts/eval_archive/` | LOW | S | 0 (move) | 5 + history | dead_code §5 | Root-tree cleanup |
| 33 | Retire `embed_verses.py` + legacy MiniLM index | MED | S | -185 + Cypher | 1 + Neo4j | dead_code §4 + retrofit §26 | Coupled to graph operation |
| 34 | Move `backfill_retrieved_model_version.py` → `scripts/migrations/` | LOW | XS | 0 (move) | 1 | dead_code §4 | Convention |

34 items total. **Status counts:** 14 quick (XS/S), 12 medium (M), 5 large (L), 1 XL (Ralph strip).

---

## Top 10 quick wins (HIGH severity, ≤ M effort)

Ordered for sequencing. Each is independent unless noted; could each be one focused session.

### 1. System-prompt tool count fix (XS · runtime impact)

`prompts/system_prompt.txt:23` says "15 tools"; `prompts/system_prompt_free.txt:31` says "10 retrieval/exploration tools". `chat.py` exposes 21. The model uses what it sees. QKG_AUDIT §3 finding 4 from 2026-05-13 still unaddressed.

Two paths: (a) one-line edit per prompt file to "21" and re-enumerate; (b) generate the count line from `chat.TOOLS` at server startup so it never drifts again. (b) is better; (a) is acceptable if you want to ship in 5 minutes.

### 2. Delete the 6 unambiguously dead modules (S · -1,862 LOC)

Per dead_code §1: `graph_qa.py`, `explore.py`, `ui.py`, `consolidate_traces.py`, `run_tests_filtered.py`, `evaluate.py`. All have zero importers, zero CI/runtime hooks, all functionally superseded. Best done in one atomic commit `chore: delete 6 superseded modules` after operator green-light. Pair with README §282-285 + §368-371 removals (touched in item 9).

### 3. README build-pipeline rewrite + dead-module purge (M · onboarding-blocker)

A new user following today's README ends up with: legacy MiniLM only, no Concept layer, no Code-19 features, no mutashabihat, no BM25 fulltext index. 4+ chat tools fail silently. Add the 9 missing build scripts; remove `evaluate.py` / `autoresearch*` / `explore.py` from the doc.

While editing, take a second pass on the "Source map" + "Deployment modes" sections to align with CLAUDE.md.

### 4. ARCHITECTURE.md rewrite-or-delete (M · primary onboarding doc)

Mermaid blocks show MiniLM + ms-marco-MiniLM as the embedding/reranker stack (both legacy); "92K nodes / 403K edges / 500 entries / 15 tools" all stale; no `shared_agent` / `reasoning_memory` / `ref_resolver` / `Concept` / `Code-19` / `SIMILAR_PHRASE` mentions.

`CLAUDE_INDEX.md` explicitly points new agents here. Either rewrite to reflect 2026-05 reality (~2-3h, the Mermaid is structurally salvageable), OR delete the file and update CLAUDE_INDEX.md's pointer to CLAUDE.md.

### 5. Centralise Neo4j driver init (M · -400 LOC, 44 files)

Create `quran_kg/neo4j.py`:

```python
def get_driver(verify: bool = True) -> Driver: ...
def session(db: str = None): ...   # context manager
```

44 files currently re-implement the same 6-9-line env-read + driver-construct block. Mechanical replacement; low semantic risk. Best done as a single sweep so the defaults converge.

### 6. Khalifa UI banner + README §6 expansion (M · credibility risk)

Phase 0 #3 of the retrofit plan has shipped a one-line README paragraph but not the UI banner. QKG_AUDIT §5 ("The Religious Studies Scholar") is the only audit finding that is *credibility-risk* not *code-hygiene*. The architecture supports a banner trivially — `index.html`'s header already has a layout slot. ~30 lines of HTML + a Markdown paragraph above the "Quick Start" in README. Don't wait for Phase 8 #32 (translation toggle).

### 7. `ref_resolver` test coverage (S · 2h, 459 LOC covered)

The module is pure regex — no Neo4j, no LLM, no I/O. 8 distinct regex patterns × edge cases (range, list, Arabic digits, spelled numbers, named surah, brackets, parens, bare pair). ~30 tests in one file. This is the highest test value-per-hour in the repo. It also powers the `/api/resolve_refs` handler and the `quran_linker.js` widget — drift here breaks citation tooltips silently.

### 8. `retrieval_gate` test coverage (S · 2h, 213 LOC covered)

Mostly pure: `lost_in_middle_reorder` (pure permutation), `assess_quality` (~10-line scorer), `rerank_verses` (injectable model — the same monkey-patch pattern `tests/test_answer_cache_rerank.py` already uses). `gate_tool_result` is the orchestrator that pulls all three.

Pair with item 7 to deliver "two pure modules now at high coverage" in a single morning. Net: 672 LOC of zero-coverage critical path covered in half a day.

### 9. Citation-regex consolidation → `ref_resolver` (S · prevents drift)

3-4 modules (`shared_agent.py:203`, `evaluate.py:38`, `autoresearch_local.py:73`, `eval_qrcd.py:88`) each have their own `_BRACKET_REF` or `extract_citations`. `shared_agent.py`'s is *semantically different* — picks up unbracketed `12:1` text. Replace all with calls to `ref_resolver.resolve_refs()`. The audit's "verification eval" and "citation-density retry" both depend on consistent verse extraction; today they may disagree at the edges.

### 10. Unify 3 reranker entry points to `model_registry` (S · prevents 2nd ML load)

`model_registry.get_reranker()` exists; `retrieval_gate._get_reranker` and `answer_cache._get_reranker` should become thin aliases. `model_registry`'s own docstring documents the migration as incomplete. Two instances of `CrossEncoder(bge-reranker-v2-m3)` is ~1.2 GB; today nothing triggers it but the design intent says single-instance.

---

## Top 5 strategic recommendations (what the codebase needs going forward)

These don't fit in a single session and warrant operator commitment. Numbered by sequencing dependency.

### S1. Split `chat.py` per QKG_AUDIT §4 (L · prereq for tool consolidation)

2,650 LOC in one file. Suggested layout (from QKG_AUDIT and duplication §5):

```
chat/
  __init__.py        # re-exports the public surface (TOOLS, dispatch_tool, run_agent_turn)
  _validate.py       # input validation (lines 110-156)
  _classifier.py     # classify_query rubric (lines 1133-1774)
  _cache.py          # tool-result cache (lines 2363-2592)
  dispatch.py        # dispatch_tool + run_agent_turn
  tools/
    search.py        # 8 search/retrieval tools
    verse.py         # 3 verse-level tools
    etymology.py     # 7 etymology tools
    code19.py        # tool_get_code19_features
    escape.py        # tool_run_cypher
    schema.py        # TOOLS = [...] Anthropic schema (~590 LOC of JSON)
```

This is the largest-cognitive-impact, zero-LOC-removal refactor in the audit. It's also a prerequisite for QKG_AUDIT Phase 7 #28 (consolidate 21 → 8-10 tools, especially the etymology cluster) — easier to merge tools when they share a module.

**Approach:** Phase-3a-style trajectory baseline first (`scripts/capture_baseline_trajectory.py` is in tree and was used for the app-refactor). Then mechanical move + import-shim in `chat/__init__.py` so external imports keep working. One session; bounded risk.

### S2. Finish what Phase 3a started — app-variant FastAPI extraction (L · -400-500 LOC)

Phase 3a unified the agent **loop** into `shared_agent.py`. The FastAPI **surface** is still duplicated across `app.py` (191) / `app_full.py` (209) / `app_lite.py` (277) / `app_free.py` (506). Most routes (`/stats`, `/cache-stats`, `/model-info`, `/verses`, `/chat`, `/api/resolve_refs`, `/api/verse/{id}`, `/quran_linker.js`) are near-identical across variants.

Target: `shared_app.build_app(config) -> FastAPI`. Each `app_*.py` becomes ~30-50 LOC: "here's the config, here's whether we wire verification, here's the port".

This is also the moment to decide if all 4 variants survive (see open question 3 below). If `app_free.py` is the production app, the case for keeping the others as separate wrappers is weak.

### S3. Cache-pass CLI consolidation (M · operational surface)

6 `scripts/*cache*.py` files all follow load → process → `_save_cache` shape. Today they're chained by hand. Build `scripts/cache_passes/` with:

```python
class BasePass: name, filter_or_annotate(entry), summary(results), run()
```

Single CLI: `python -m scripts.cache_passes --pass {audit|prune|enrich|reembed|coverage}`. Net: -150 LOC after factoring + a single discoverable surface. Pairs well with item 27 (env-var registry) and unblocks Phase 5 (when the loop returns, it can dispatch a `cache_passes` op without re-grepping for which script to run).

### S4. Env-var registry + `.env.example` validator test (M · drift trap)

~44 distinct env vars read across the codebase, no central registry. Two confused pairs already in flight: `RERANK_DISABLED` vs `CACHE_RERANK_DISABLED`; `RERANKER_MODEL` default duplicated in 2 places. Build a single `quran_kg/settings.py` (plain dataclass or Pydantic) + a tiny `test_env_keys_documented.py` that asserts every `os.environ.get` key appears in `.env.example`. CLAUDE.md's freeform list becomes generated, not hand-maintained.

Estimated cost: small. Estimated value: closes the entire category of "silent typo" bugs.

### S5. Retrofit plan as an actionable scoreboard (S, ongoing)

`docs/QKG_RETROFIT_PLAN.md` is the closest thing the project has to a roadmap. **~15 of its 40 items are now done**, but the doc has no status markers — it reads identically to its 2026-05-13 form. A simple `| Status | Item |` table or `- [x]` checkboxes would make it the natural target for "what's next?" instead of "what was the plan when this was written?".

This is mostly a doc hygiene change but it converts a static plan into a living scoreboard. Pair with item 15.

---

## Three open questions for the operator

These are cross-cutting and recur across multiple passes. Answering them unlocks several backlog items at once.

### Q1. Autoresearch fate

`autoresearch.py` / `autoresearch_local.py` / `autoresearch_dashboard.py` total ~1,620 LOC, last touched 2026-04-15, labelled "older infra" in CLAUDE.md but still marketed in README. The eval/v2 framework + DSPy plans (Phase 4+) implicitly retire this workflow.

- **A. Retire** — delete + remove from README.
- **B. Revive** — pin down which scenario brings Optuna sweeps back; assign owner.
- **C. Park** — keep as-is, add "currently unmaintained" header.

My read: **A**. Confirm operator agrees and items 31 + part of 9 become a single commit.

### Q2. Phase 5 design vs strip

The Ralph loop is paused (`data/RALPH_STOP`). Roughly 10 modules / 3,140 LOC of scaffolding (`ralph_loop.py`, `ralph_run.py`, `ralph_tick.py`, `scripts/{vault_update,memory_hygiene,haiku_prep,sonnet_prep,tick_finalize,state_snapshot,capture_baseline_trajectory}.py`) sit in limbo. The retrofit plan Phase 5 (items 18-21) explicitly strips most of it.

- **A. Design first** — one focused advisor session to crystallise Phase 5 design; THEN trim.
- **B. Strip now** — invoke retrofit plan as authority; delete the parked scripts and let Phase 5 design later if/when the loop returns.
- **C. Leave alone** — accept that 3,140 LOC of parked scaffolding stays until someone needs it.

My read: **A**. The cost of the parked scaffolding is low (it's not being maintained), and a fresh strip-and-redesign benefits from being one session rather than two.

### Q3. README vs CLAUDE.md as source of truth

The same module list, build pipeline, env-var matrix, and tool count appears in both. Today CLAUDE.md is current and README is 8 weeks stale. This pattern recurs: every materially-new module needs to land in both. The drift trap is the maintenance cost, not any single doc.

- **A. README points at CLAUDE.md** — README becomes a 50-line "what this is + how to install + see CLAUDE.md for everything else". External users follow one link.
- **B. Generate README from CLAUDE.md** — script that produces README.md from CLAUDE.md sections + external-user framing.
- **C. Keep both, accept drift, periodic sync** — the current model.

My read: **A** for now (lowest cost), with a path to **B** later if the README grows again. Either kills the drift permanently.

---

## Suggested sequencing for the next 5 sessions

Each session is ~1-2 hours unless noted.

1. **Quick-wins batch A** (items 1, 2, 14, 17, 18 — all XS): system-prompt fix, CLAUDE.md off-by-one, PHASE_3A_PLAN status header, archive 4 dead plan docs, mark STATE_SNAPSHOT paused. ~45 min total. Single commit `docs: assorted hygiene fixes per architecture audit`.
2. **Dead-module purge** (items 3, 4, 16, 17 + parts of 9): delete the 6 dead modules, rename root harnesses, fix the 2 stale docstring headers, drop dead-module mentions from README. Operator green-light first.
3. **Test coverage sprint** (items 7, 12, 13, 20): `ref_resolver` + `retrieval_gate` + `answer_cache.save_answer/build_cache_context`. Half-day. Net: 1,000+ LOC of critical path freshly covered.
4. **Neo4j driver helper** (item 8): mechanical sweep across 44 files. One focused session; pair with item 5 (`_load_env`).
5. **README + ARCHITECTURE rewrite** (items 9, 10, 11): the big doc-correctness pass. Includes the Khalifa banner. Probably 2 sessions if you want to do both docs right.

After that the strategic items (S1-S5) become the next decision tree.

---

## Aggregate scorecard

| Pass | Findings | Top action surface | Quick-win count | Strategic count |
|------|---------|-------------------|----------------:|---------------:|
| 1 — Dead code | 26 modules, ~7,950 LOC addressable | Delete 6 dead, decide autoresearch + Ralph | 2 | 1 |
| 2 — Duplication | ~1,200-1,300 LOC + chat.py split | Neo4j helper, app split, chat.py split | 3 | 3 |
| 3 — Testing gaps | 1,797 LOC of zero-coverage critical modules | ref_resolver + retrieval_gate sprint | 2 | 0 |
| 4 — Docs drift | 6+ multi-week-stale docs; runtime prompt bug | README rewrite, system-prompt fix, Khalifa banner | 5 | 1 |
| **Total** | — | — | **12** | **5** |

**One-sentence headline:** the project is structurally sound — Phase 3a delivered, tests exist, BGE-M3 is in — but the surface has out-grown the documentation, the testing, and the central-helper layer it deserves; ~1,200 LOC of duplication and 4 critical untested modules are the practical debt, and the system-prompt + README staleness is the credibility debt.
