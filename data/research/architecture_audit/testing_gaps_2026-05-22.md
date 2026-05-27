# Architecture Audit — Pass 3: Testing gaps (2026-05-22)

Branch: `claude/architecture-audit-2026-05-22`
Baseline: 210 tests collected, 209 pass + 1 skipped (run time ≈ 18.5s).
Scope per prompt: `chat.py`, `app_free.py`, `retrieval_gate.py`, `answer_cache.py`, `reasoning_memory.py`, `ref_resolver.py`, `citation_verifier.py`, plus `shared_agent.py` (added — it's the new agent-loop entry point).
Method: grep every public function symbol in `tests/`, classify as direct-tested, indirectly-touched, or zero-coverage. Cross-reference with `.github/workflows/test.yml`'s coverage step (`--cov=chat --cov=retrieval_gate`).

> **Calibration note.** A grep-by-name coverage map under-counts integration tests that exercise a function through `dispatch_tool`. Where I flag a function as "zero direct hits" I also checked the integration tests; modules listed as "no indirect coverage either" have neither a unit test nor an integration test that touches them. Worth a real `pytest --cov` run before any of these is acted on — the CI step is informational and the report is not retained.

---

## TL;DR

- **Direct coverage map for 45 public functions:** 14 directly tested (≥2 hits), 5 lightly tested (1-2 hits), **26 with zero direct test references** — most of them critical-path.
- **Four critical-path modules have ZERO test coverage** (no direct unit tests, no indirect coverage via tests/imports): `reasoning_memory.py` (452 LOC), `ref_resolver.py` (459 LOC), `citation_verifier.py` (317 LOC), `retrieval_gate.py` (213 LOC). Total: 1,441 LOC.
- **16 of 21 chat.py tool functions have no dedicated test.** Five tools are covered (`get_verse`, `find_path`, `query_typed_edges`, `run_cypher`, `recall_similar_query` via `classify_query`); the rest are exercised only when `dispatch_tool` happens to call them in an integration test. The audit's "every change is live-fire" criticism — coined when there was *one* test file — is materially better today (21 test files / 210 tests) but the dispatcher's downstream tools are still mostly live-fire.
- **app_free.py has zero handler tests.** All 10 async route handlers (`/chat`, `/api/resolve_refs`, `/api/verse/{id}`, `/stats`, `/cache-stats`, `/model-info`, `/model-status`, `/verses`, `/`, `/quran_linker.js`) are untested. The agent loop they wrap is tested at the `shared_agent.agent_stream` layer; the FastAPI surface around it is not.
- **No stale `xfail` markers.** TDD discipline is being followed correctly (Pass 1 §8a confirmed this).
- **Two root-level `test_*.py` files** (`test_va_impact.py`, `test_verse_analysis.py`) are intentional A/B harnesses, not pytest tests — collection-safe via `pyproject.toml testpaths=["tests"]` (commit `625b404`). Renaming to `harness_*.py` removes the trap and was flagged in Pass 1.
- **Highest-leverage coverage wins (low cost, high value):** `ref_resolver.py` is **pure** (regex over strings, no Neo4j, no LLM) — likely <2 hours to bring to ≥80% line coverage. `retrieval_gate.py` is mostly pure too (lost-in-middle reorder, quality assessment, rerank with injectable model) — another <2 hours.

---

## 1 · Public-function coverage map

Direct hits = number of `tests/**/*.py` files that mention the function/class by name (grep `-w`). Two or more hits ≈ has a dedicated test; one hit is usually an integration import; zero hits is the worry list.

### chat.py (26 public symbols, 21 are `tool_*`)

| Symbol | Hits | Status |
|--------|----:|--------|
| `tool_get_verse` | 13 | **Heavy** — Phase 3b whitespace-cluster regression hammers this. Healthy. |
| `tool_query_typed_edges` | 4 | OK — typed-edges concat regression covers the Cypher-injection foot-gun. |
| `tool_find_path` | 2 | OK — whitespace cluster. |
| `tool_run_cypher` | 2 | OK — denylist regression. Phase 3 plan #14 wanted this. |
| `classify_query` | 2 | Light — referenced in tests/test_shared_agent_*.py |
| `dispatch_tool` | 5 | Strong — via test_agent_loop.py + test_shared_agent_*.py |
| `run_agent_turn` | 4 | OK — same files. |
| `tool_search_keyword` | 0 | **None** |
| `tool_traverse_topic` | 0 | **None** |
| `tool_explore_surah` | 0 | **None** |
| `tool_search_arabic_root` | 0 | **None** |
| `tool_compare_arabic_usage` | 0 | **None** |
| `tool_semantic_search` | 0 | **None** — uses vector index, hard to unit-test without a fake |
| `tool_lookup_word` | 0 | **None** |
| `tool_explore_root_family` | 0 | **None** |
| `tool_get_verse_words` | 0 | **None** |
| `tool_search_semantic_field` | 0 | **None** |
| `tool_lookup_wujuh` | 0 | **None** |
| `tool_search_morphological_pattern` | 0 | **None** |
| `tool_concept_search` | 0 | **None** — Porter-stem ER, fairly testable |
| `tool_hybrid_search` | 0 | **None** — BM25+BGE-M3+RRF, complex |
| `tool_recall_similar_query` | 0 | **None** — past-trace playbook |
| `tool_get_code19_features` | 0 | **None** — pure arithmetic over graph properties, easy to fake |
| `get_tool_cache_stats` | 0 | **None** — but trivial getter |
| `clear_tool_cache` | 0 | **None** — but trivial |
| `main` | 0 | (CLI entry; out of scope) |

**Tool coverage: 5 / 21 with a dedicated test (~24%).** The other 16 ride on `dispatch_tool`; if a tool's Cypher silently returns nothing, no test will catch it.

### shared_agent.py (4 public)

| Symbol | Hits | Status |
|--------|----:|--------|
| `agent_stream` | 8 | **Heavy** — tests/test_shared_agent_*.py + regression/test_agent_mid_turn_stop_poll.py + test_sse_worker_leak.py + test_sse_keepalive.py |
| `AgentConfig` | 5 | Strong |
| `AgentCollaborators` | 5 | Strong |
| `FallbackBackend` | 2 | OK |

**Shared agent: well-covered.** This is the Phase 3a result delivering its dividend.

### app_free.py (10 async handlers + 2 request models)

| Symbol | Hits | Status |
|--------|----:|--------|
| `chat` (POST /chat) | 0 | **None** — async route; the `agent_stream` it calls *is* tested |
| `index` (GET /) | 0 | None |
| `model_status` | 0 | None |
| `model_info` | 0 | None |
| `stats_page` | 0 | None |
| `all_verses` | 0 | None |
| `get_cache_stats` | 0 | None |
| `api_resolve_refs` | 0 | **None** — wraps `ref_resolver.resolve_refs`; both untested |
| `api_get_verse` | 0 | **None** |
| `quran_linker_js` | 0 | **None** |
| `ChatRequest` (Pydantic) | 0 | None — schema validation by FastAPI |
| `ResolveRefsRequest` (Pydantic) | 0 | None |

**FastAPI surface coverage: 0 / 10 handlers.** A `TestClient(app_free.app)` smoke test (one per handler, ≈20-30 LOC each) would catch a whole category of "wired the wrong path" bugs.

### retrieval_gate.py (4 public)

| Symbol | Hits | Status |
|--------|----:|--------|
| `rerank_verses` | 0 | **None** |
| `assess_quality` | 0 | **None** — pure function, ~10 LOC |
| `lost_in_middle_reorder` | 0 | **None** — pure permutation, ~20 LOC |
| `gate_tool_result` | 0 | **None** — orchestrator; combines the other three |

**Module coverage: 0%.** The audit's "reranker drops hit@10 50%" claim depended on this module's behaviour; ironically, the module itself has no tests.

### answer_cache.py (4 public)

| Symbol | Hits | Status |
|--------|----:|--------|
| `search_cache` | 2 | OK — tests/test_answer_cache_rerank.py covers the rerank path |
| `save_answer` | 0 | **None** — the high-level entry point. `_save_cache` (private) IS covered by `test_answer_cache_io.py`, but the dedup logic, the 5,000-entry cap, the 0.98 cosine threshold are all in `save_answer` and are NOT directly tested. |
| `build_cache_context` | 0 | **None** — context-injection into system prompt |
| `cache_stats` | 0 | None — diagnostic, low risk |

### reasoning_memory.py (2 classes)

| Symbol | Hits | Status |
|--------|----:|--------|
| `ReasoningMemory` | 0 | **None** |
| `QueryRecorder` | 0 | **None** |

**Module coverage: 0%.** Writes `(:Query)-[:TRIGGERED]->(:ReasoningTrace)-[:HAS_STEP]->(:ToolCall)` + `[:RETRIEVED]` + `[:HAS_CITATION_CHECK]` on every chat. A Cypher-level fake (or a testcontainers Neo4j) could exercise these.

### ref_resolver.py (2 public)

| Symbol | Hits | Status |
|--------|----:|--------|
| `resolve_refs` | 0 | **None** |
| `link_html` | 0 | **None** |

**Module coverage: 0%.** *And* this is the most testable module in the bunch — pure regex over strings, no Neo4j, no LLM, no I/O. 8 distinct regex patterns × edge cases (range, list, Arabic digits, spelled numbers, named surah, brackets, parens, bare pair). Each has a clean fixture: `("Quran 2:255 is the Throne Verse", [Match(2, 255, "explicit", ...)])`.

### citation_verifier.py (5 public)

| Symbol | Hits | Status |
|--------|----:|--------|
| `decompose_claims` | 0 | **None** |
| `verify_citation_nli` | 0 | **None** |
| `verify_citation_minicheck` | 0 | **None** |
| `verify_citation` | 0 | **None** |
| `verify_response` | 0 | **None** |

**Module coverage: 0%.** This is the post-response NLI/MiniCheck/FActScore gate — when `ENABLE_CITATION_VERIFY=1` it produces the `verification` SSE event the UI surfaces. Untested means it can silently drift to "always supported" or "always contradicts" without anyone noticing.

---

## 2 · Aggregate

| Module | LOC | Direct-tested fns | Total public fns | Coverage % | Direct-tested LOC est. |
|--------|----:|------------------:|-----------------:|-----------:|----------------------:|
| `shared_agent.py` | 1,346 | 4 / 4 | 4 | 100% | ~1,346 |
| `chat.py` | 2,650 | 7 / 26 | 26 | 27% (by fn count) | ~700 |
| `answer_cache.py` | 261 | 1 / 4 | 4 | 25% | ~80 |
| `app_free.py` | 506 | 0 / 12 | 12 | 0% | 0 |
| `retrieval_gate.py` | 213 | 0 / 4 | 4 | 0% | 0 |
| `reasoning_memory.py` | 452 | 0 / 2 | 2 | 0% | 0 |
| `ref_resolver.py` | 459 | 0 / 2 | 2 | 0% | 0 |
| `citation_verifier.py` | 317 | 0 / 5 | 5 | 0% | 0 |
| **Totals** | **6,204** | **12 / 59** | **59** | **20% by fn count** | **~2,126 LOC** |

So **roughly 2/3 of the LOC in these modules has no direct test coverage by symbol name.** A real `pytest --cov` would refine this — `dispatch_tool` integration tests pull lines into coverage incidentally — but the symbol-level number is the right one for "if I rename or change the signature of fn X, does ANY test fail?" The answer is "no" for 47 of 59 functions.

---

## 3 · Test files in the root that aren't in `tests/`

Both are intentional A/B harnesses, not pytest tests. Both `import requests` at module load and read `.env` eagerly — they would explode under pytest collection. CLAUDE.md acknowledges this; `pyproject.toml testpaths=["tests"]` enforces it.

| File | LOC | Purpose |
|------|----:|---------|
| `test_va_impact.py` | ~240 | A/B verse-analysis enrichment impact harness |
| `test_verse_analysis.py` | ~260 | v2.0 vs v2.1 prompt A/B for verse-analysis generation |

**Risk:** filenames still match `test_*.py` glob. Any external collector (IDE auto-discovery, CI shard that doesn't honour `pyproject.toml`, `unittest discover`, `pytest tests/ test_*.py` if someone over-explicitly invokes) will trip. Two-minute rename to `harness_*.py` closes the trap permanently. *Pass-5 quick-win candidate.*

---

## 4 · Stale `xfail` audit (the prompt asked for >30-day xfails)

- **Zero `@pytest.mark.xfail` markers in `tests/`** (re-verified for this pass).
- One docstring mention in `tests/test_answer_cache_rerank.py:18` — describes the xfail-then-flip pattern but no live marker; the file was committed with the marker, the implementation landed in the same commit (`5cc0e6c` per state_2026-05-21), the marker was removed in that same commit. Discipline is being followed.
- One `@pytest.mark.skipif` on a fixture-absent guard (`tests/test_cache_coverage_shuaib_alias.py:62`) — correct, not stale.
- Heavy use of `@pytest.mark.parametrize` in the regression cluster — healthy.

**No stale TDD debt in the test suite.**

---

## 5 · Coverage instrumentation status

`.github/workflows/test.yml` runs:

```yaml
- name: Coverage report (informational, doesn't block)
  if: always()
  run: |
    python -m pytest tests/ --cov=chat --cov=retrieval_gate --cov-report=term-missing || true
```

- Only two modules are instrumented (`chat`, `retrieval_gate`). The audit's "no real correctness eval" concern parallels this — we don't even measure the test-line coverage we have.
- `--cov-report=term-missing` prints to the run log but is not uploaded as an artefact. No coverage badge, no PR comment.
- The `|| true` makes it non-blocking, which is fine for "informational", but combined with no artefact upload it means **no one ever sees the coverage number**.

**Small fix:** add `--cov-report=xml` + upload as artefact + add a PR comment via `actions/upload-artifact` + a `codecov-action` step (or self-hosted equivalent). Inexpensive, surfaces the gap above. **Even simpler:** just `tail -20 coverage` into the PR comment.

---

## 6 · Testability ranking (lowest-cost coverage wins first)

| Module | Testability | Why | Effort estimate |
|--------|:-----------:|----|----------------|
| `ref_resolver.py` | **★★★★★** | Pure regex; 8 patterns × ~5 examples each + edge cases | ~2 h, ~30 tests |
| `retrieval_gate.py` | **★★★★** | Pure permutations + injectable reranker (already monkey-patched in answer_cache test pattern) | ~2 h, ~10 tests |
| `citation_verifier.py` | **★★★** | Needs NLI/MiniCheck fakes; can monkey-patch sentence-transformer/transformers loaders | ~3-4 h, ~10 tests |
| `answer_cache.save_answer / build_cache_context / cache_stats` | **★★★** | Same in-memory cache fixture as `test_answer_cache_io.py` already uses | ~1 h, ~6 tests |
| `app_free.py` async handlers | **★★★** | FastAPI `TestClient` + monkey-patch the Neo4j driver | ~3 h, ~10 tests |
| 16 untested `chat.py` tools | **★★** | Each tool's Cypher needs a non-trivial FakeNeo4jSession extension | ~30 min/tool average → 8 h for all 16, or pick top 5 most-used per `RETRIEVED` graph data |
| `reasoning_memory.py` | **★★** | Needs Cypher write-path verification → either testcontainers Neo4j or extend FakeNeo4jSession with insert capture | ~4-6 h |

**Recommendation:** start with `ref_resolver.py` (highest-value, lowest-cost, and the module powers `/api/resolve_refs` + the JS auto-linker widget — a quiet drift here breaks the citation tooltip silently). Then `retrieval_gate.py`. These two alone close ~672 LOC of zero-coverage critical path in ≈half a day.

---

## 7 · Related: `tests/fakes/` is healthy and underused

`tests/fakes/{anthropic_client.py, llm_client.py, neo4j_session.py}` exist and are well-designed. `FakeNeo4jSession` accepts an inline graph dict and supports parametrized Cypher matching. The pattern is in `tests/conftest.py` (`empty_session`, `fatiha_session` fixtures).

**Gap:** the only Cypher patterns the fake currently handles are those exercised by `tool_get_verse` and the integration tests. Adding 16 chat-tool tests means extending the fake's Cypher coverage — non-trivial but cumulative. Alternative: spin up a `testcontainers-neo4j` for the heavier suite and keep the fake for the fast unit tests. The audit / retrofit plan (Phase 1 item #4) anticipated this trade-off.

---

## Open questions for the operator

1. **Coverage instrumentation.** Is the informational `--cov` step in `test.yml` worth promoting to "always print to PR comment", or is the team's signal-from-noise threshold already calibrated to "use grep when curious"?
2. **`ref_resolver` test sprint.** Worth a one-session focused TDD pass on this module, since it's the easiest 459 LOC to cover and powers the citation widget the UI promises? (Estimate: half-day.)
3. **`reasoning_memory` strategy.** Testing the writes-to-Neo4j layer either needs a richer Cypher fake or a testcontainers Neo4j. Which path is the operator's preference for the project going forward? (The Phase 1 retrofit guidance was "synthetic 10-verse graph OR test-scoped DB" — both are still on the table.)
