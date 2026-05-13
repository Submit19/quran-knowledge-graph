# Phase 3a — Shared agent-loop refactor

Plan for the next step of `docs/QKG_RETROFIT_PLAN.md`. Phase 3b shipped four
production bug fixes and the `sse_pump.py` extraction; Phase 3a is the larger
refactor that collapses `app.py`, `app_full.py`, `app_lite.py`, and
`app_free.py` onto a single shared agent module.

This document only **plans** the refactor. No code changes here.

---

## Goal

Reduce each of the four `app*.py` files to a ~100-line config wrapper that
imports a shared agent module and bolts on app-specific knobs.

| App           | LOC today | Backend                            | Notable variant                                 |
| ------------- | --------- | ---------------------------------- | ----------------------------------------------- |
| `app.py`      | 587       | Anthropic (paid)                   | citation-density retry, uncertainty hook (commented), full TOOLS schema |
| `app_full.py` | 616       | Anthropic                          | "everything on" — paid variant with verification + cache + memory |
| `app_lite.py` | 558       | Anthropic / lean                   | Minimal-tool subset                             |
| `app_free.py` | 1,148     | Ollama / OpenRouter (local + free) | Lean schemas, deep-dive routing, OpenAI-style `tool_calls`, BUG D fix lives here |

Today every app re-implements:

- The streaming `/chat` endpoint and `_agent_stream` async generator.
- The daemon thread + `queue.SimpleQueue` + SSE-yield pattern (Phase 3b
  already extracted this into `sse_pump.py`).
- The agent loop body: build messages → call LLM → dispatch tools → repeat.
- Answer-cache lookup and write-back.
- Reasoning-memory recording.
- Citation-density retry (in `app.py`, `app_full.py`).
- Uncertainty probing (commented out in `app.py`).
- Tool-result compression.
- Citation verification (env-gated).
- `/stats`, `/verses`, `/` endpoints.

Most of that body is identical across files — drift between them is the
single largest source of "fix it once, leave it broken three times" bugs in
this codebase.

---

## What "behaviour preservation" means concretely

| Axis                          | `app.py` | `app_full.py` | `app_lite.py` | `app_free.py`         |
| ----------------------------- | -------- | ------------- | ------------- | --------------------- |
| Backend                       | Anthropic| Anthropic     | Anthropic     | Ollama + OpenRouter   |
| Tool schema                   | full     | full          | lean subset   | OLLAMA_TOOLS (OpenAI) |
| Citation-density retry        | yes      | yes           | no            | no                    |
| Uncertainty probe (env-gated) | yes      | yes           | no            | no                    |
| Verification (env-gated)      | yes      | yes           | no            | yes                   |
| Priming graph update          | no       | no            | no            | **yes**               |
| Reasoning-memory playbook     | no       | yes           | no            | **yes**               |
| classify_query → rerank knob  | no       | yes           | no            | **yes**               |
| Tool-result compression       | no       | yes           | no            | **yes**               |
| Daemon-thread leak fix        | (n/a)    | (n/a)         | (n/a)         | **Phase 3b, locked**  |
| Default port                  | 8081     | 8082          | 8083          | 8085                  |

The `app_free.py` column has the most "yes" entries and the only locked
constraint — that is why it is the highest-risk port and the one we
sequence last.

---

## Module layout

### `shared_agent.py` (new — the destination)

Public surface (the only names callers should depend on):

- `AgentConfig` dataclass — captures every per-app axis. Frozen after
  construction.
  - `backend: Literal["anthropic", "ollama", "openrouter"]`
  - `model: str` (or callable for the free app's routing)
  - `tools: list` (Anthropic blocks or OpenAI `function` dicts)
  - `system_prompt: str`
  - `max_tool_turns: int`
  - `enable_citation_density_retry: bool`
  - `enable_uncertainty_probe: bool`
  - `enable_verification: bool`
  - `enable_priming_graph_update: bool`
  - `enable_reasoning_memory_playbook: bool`
  - `enable_tool_result_compression: bool`
  - `enable_model_routing_event: bool`
  - `min_citations: int` (for citation-density retry)
- `agent_stream(message, history, config, **per_request_overrides)` — the
  async generator that all `@app.post("/chat")` handlers call. Wraps the
  worker in `sse_pump.pump_worker_into_sse`. Handles backend dispatch,
  cache lookup, reasoning memory, agent loop, verification, sentinel.
- `build_app(config) -> FastAPI` — optional convenience that wires the
  standard endpoints (`/`, `/stats`, `/verses`, `/chat`, `/cache-stats`,
  `/model-status`, `/model-info`). Apps with extra endpoints
  (`app_free`'s `/api/resolve_refs`, `/quran_linker.js`) call this and
  then add their own.

Private helpers (implementation detail — tested but not stable API):

- `_anthropic_step(client, msgs, tools, ...)` — one round of the agent
  loop against the Anthropic SDK.
- `_ollama_step(...)` and `_openrouter_step(...)` — same shape, different
  backend.
- `_dispatch_tool_calls(session, blocks, user_query)` — pulls tool_use
  blocks out of a response, fans them out to `chat.dispatch_tool`,
  returns `tool_result` blocks.
- `_run_agent_loop(q, stop_event, config, msgs, session)` — the body
  that goes inside the worker.
- `_apply_cache_context(message, system_prompt)` → optionally augmented
  system prompt.
- `_record_reasoning_memory_start(...)` / `_record_reasoning_memory_finish(...)`.

### Where `chat.py` is imported

- `shared_agent` imports `chat.TOOLS`, `chat.dispatch_tool`, and
  `chat.classify_query` (free app only).
- Each `app*.py` wrapper imports nothing from `chat` directly — it goes
  through `shared_agent`. This is what kills the "fix it once, leave it
  broken in three apps" failure mode.

### Threading / SSE contract

- The shared agent loop runs in a daemon thread, started by
  `sse_pump.pump_worker_into_sse`. The Phase 3b stop_event contract is
  preserved: the loop body polls `stop_event.is_set()` at the top of
  each turn and returns early on disconnect.
- Backend step functions (`_anthropic_step`, `_ollama_step`,
  `_openrouter_step`) MUST NOT swallow `stop_event` — they only do one
  LLM call and return.

### Error-recovery contract

- `requests.ConnectionError` and `requests.Timeout` → push a `{"t":
  "error", ...}` event, mark the reasoning-memory trace failed.
- Generic `Exception` → push a sanitized error event with str(e)[:300].
- The finally block in the worker target ALWAYS pushes the None sentinel
  (this is already in `sse_pump.pump_worker_into_sse`).

---

## Migration plan

**Refactor app_free.py first.** It has the most LOC (1,148), the most
variant axes (routing, priming, playbook, classify_query, compression),
AND the Phase 3b daemon-thread fix. If the shared module can cover
app_free without losing any of those, the other three apps will be
strictly easier.

Order:

1. Extract `shared_agent.py` with the public surface and an Anthropic-
   only implementation. No app changes yet — module compiles, tests
   added.
2. Port `app.py` onto `shared_agent`. Run differential tests (see below)
   on a corpus of cached queries; diff each SSE frame.
3. Port `app_full.py`. The shared module gains a `full_coverage` knob.
4. Port `app_lite.py`. The shared module gains a `lite_tools` knob (or
   the wrapper just passes a different `config.tools`).
5. Extend `shared_agent` with Ollama + OpenRouter steps.
6. Port `app_free.py` last. Verify the Phase 3b stop_event check is
   wired through the shared loop body.

After each port: keep the OLD app file in git history until the next
port lands; if a regression surfaces, revert the single migration.

---

## Test strategy

### New tests covering `shared_agent`

- `tests/test_shared_agent.py`
  - `test_agent_stream_yields_text_then_done_for_zero_tool_calls` —
    FakeLLMClient returns immediate `end_turn`. Generator yields one
    `text` frame + `done` + None.
  - `test_agent_stream_dispatches_tool_then_yields_text` — FakeLLMClient
    returns `tool_use` then `end_turn`. Verify `tool` event +
    tool_result + `text` + `done`.
  - `test_agent_stream_respects_max_tool_turns` — Fake returns `tool_use`
    forever. Loop terminates at `config.max_tool_turns`.
  - `test_agent_stream_signals_worker_on_aclose` — duplicate of the
    `sse_pump` test but driven through `agent_stream`, using fakes for
    LLM + session.
  - `test_citation_density_retry_fires_when_under_min` — verify the
    retry message is sent on the second LLM call when `len(refs) <
    MIN_CITATIONS`.
  - `test_citation_density_retry_disabled_when_flag_off` — same setup,
    `config.enable_citation_density_retry=False`, verify no retry.

### Tests covering each wrapper

- `tests/test_apps.py`
  - `test_app_py_uses_anthropic_full_tools` — import `app`; assert
    `app.agent_config.backend == "anthropic"`, `app.agent_config.tools
    == chat.TOOLS`.
  - `test_app_lite_py_uses_anthropic_lite_tools` — same idea, smaller
    tool subset.
  - `test_app_free_py_uses_ollama_lean_tools_and_routing` — assert
    Ollama path + classify_query knob + priming knob.

These wrapper tests are intentionally small — the heavy logic lives in
`shared_agent` and is tested there.

### Differential testing

Per `docs/QKG_RETROFIT_PLAN.md` augmenting-tools item #3 (shadow
testing on cached queries):

1. Pick 20 representative queries from `answer_cache` (mix of CONCRETE,
   BROAD, ARABIC profiles).
2. Snapshot each app's pre-refactor SSE output for those queries
   (capture into `tests/golden/<app>/<query_hash>.sse`).
3. After each app's port, replay the same queries against the refactored
   app and diff the SSE frame sequences. Tolerate ordering differences
   inside a single tool's `args` dict; reject any new or missing
   `text`/`tool`/`done` events.
4. Track diffs in `data/phase_3a_diff.json`. If diff_count > 0 on the
   golden corpus, port is not done.

This is the "behaviour preservation" gate — the refactor isn't
complete until every wrapper round-trips the goldens.

---

## Risk register

| Risk                                                                                                | Catch                                                                                                                            |
| --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `app_free.py`'s tool-call format (OpenAI-style `tool_calls`) differs from Anthropic blocks          | Step functions return a normalised internal representation; `_dispatch_tool_calls` operates on that, not on raw blocks.          |
| Loss of the Phase 3b daemon-thread leak fix during refactor                                         | Reuse `sse_pump.pump_worker_into_sse` verbatim; the agent loop body retains the `stop_event.is_set()` check at top of each turn. |
| Citation-density retry semantics drift                                                              | Dedicated regression test BEFORE porting `app.py`. Same for uncertainty probe (re-enable just to test, then re-disable).         |
| Reasoning-memory schema growth during the refactor (new fields)                                     | Schema migrations land separately, not as part of this refactor.                                                                 |
| Free app's classify_query → reranker routing                                                        | Carry the existing `_query_profile` knob through as `config.classify_query`. Cover with one wrapper test.                        |
| Per-app port-number defaults (`:8081`, `:8082`, `:8083`, `:8085`)                                   | Each wrapper sets `port` in its `if __name__ == "__main__"` block; not part of the shared module.                                |
| 0% baseline coverage on app files makes the differential gate the only safety net                  | New tests bring coverage up before the port. Don't merge a port until coverage on the wrapper is ≥ 50%.                         |

---

## Out of scope

- **The Phase 3b daemon-thread leak fix in `app_free.py` is locked.** Any
  refactor that loses it is rejected. The regression test
  (`tests/regression/test_sse_worker_leak.py`) guards the shared helper;
  the agent-loop stop_event check is the corresponding wrapper-side
  guard.
- Tool schema redesign. The shared agent accepts whatever tool list each
  app passes; harmonising the two schemas (Anthropic blocks vs OpenAI
  `function` dicts) is its own piece of work.
- Endpoint consolidation for `/api/resolve_refs`, `/quran_linker.js` —
  those stay app-specific.
- Switching from `queue.SimpleQueue` to `asyncio.Queue`. The current
  thread-and-poll bridge works; rewriting it as fully-async is a bigger
  re-architecture that doesn't belong here.

---

## Acceptance criteria for Phase 3a

- `shared_agent.py` exists and is the only place the agent loop body
  lives.
- Each of `app.py`, `app_full.py`, `app_lite.py`, `app_free.py` is
  ≤ ~150 LOC and contains no agent-loop logic.
- The differential test corpus (20 queries × 4 apps) is zero-diff
  against pre-refactor goldens.
- The Phase 3b stop_event semantics are preserved in `app_free.py`
  (`tests/regression/test_sse_worker_leak.py` still passes;
  additionally a new `agent_stream`-level test exercises the same
  contract via the shared module).
- Coverage on `shared_agent.py` ≥ 60%; coverage on each `app*.py`
  wrapper ≥ 50%.
