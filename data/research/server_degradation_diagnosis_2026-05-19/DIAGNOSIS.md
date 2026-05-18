# Server-degradation diagnosis — `app_free.py` + local Ollama, 2026-05-19

Bounded read-only investigation of the failure pattern observed in the
overnight run on `claude/repetition-bug-baseline-2026-05-17`: 50
thematic questions, sequential, ~3.5h wall time, 32 OK / 11 timeout / 7
read-timeout errors; failures cluster from **Q24** onward.

## Headline finding

**Two interacting causes, one root.** The actual SSE-layer defect is that
`sse_pump.pump_worker_into_sse(dedup_text=True)` buffers every
`{"t": "text", "d": …}` event server-side and emits **no frames at all**
between the last tool event and the final `done` event. During that
window — which is precisely when the model is generating the final
several-thousand-token answer in one blocking `requests.post` to Ollama
— the client sees zero SSE bytes. As qwen3:14b's per-call latency grows
over a multi-hour run (independently observed below), the
final-answer turn crosses the client's 300s read-timeout, the runner
classifies it as `error` even though the server is still making
progress, and the disconnect leaves an in-flight worker thread because
the existing daemon-thread fix only checks `stop_event` between turns,
never inside a long blocking call. The result is the cascading-failure
pattern visible from Q24 onward.

Recommended fix scope: ~30-60 LOC in `sse_pump.py` — emit an SSE
`comment` keepalive frame (e.g. `:\n\n`) every 10-15s while the queue
is idle. Optional secondary patch in `shared_agent.agent_stream` (~10
LOC): poll `stop_event` more often than once per turn (e.g. before
`dispatch_tool` and immediately after the LLM call returns).

## What the timing data says (no server restart required)

`probe_baseline_timings.py` against the captured `run_log.jsonl`:

| phase | n  | OK | fail | OK median (s) | OK max (s) |
|-------|----|----|------|----------------|------------|
| Q1-Q23 (phase 1)  | 23 | 23 | 0  | 165 | 277 |
| Q24-Q50 (phase 2) | 27 | 9  | 18 | 224 | 296 |

- **Server doesn't fail cliff-edge.** It degrades steadily. Q11 already
  hit 277s — within 23s of the 300s budget. The rolling-window-5 median
  climbs through Q21-Q22 (189s, 212s) before Q24 finally crosses the
  line.
- **Both `error` and `timeout` verdicts have elapsed >300s on the
  client side.** Median elapsed for `error` is 334s, for `timeout` is
  330s; max elapsed for an `error` was Q40 = 451s. The runner only
  records `error` when *no SSE bytes arrive for 300s straight*
  (the `read_timeout` half of `timeout=(10, 300)`). Q40's 451s
  client-side elapsed proves the server was still trickling out
  *something*, but with long silent stretches in between.
- **Failure streaks are short.** Longest consecutive-failure run is 5
  (Q32-Q36). The system partially recovers between failures, which
  argues against a hard resource-exhaustion model (out of TCP sockets,
  Neo4j pool drained, OOM) — those would be one-way trips.

The "degradation" is therefore **latency drift**, not state corruption.
Each request gets a little slower as the run progresses, and once the
median crosses 300s some fraction of requests will be classified as
failures simply because they no longer fit in the client's budget.

## Hypothesis-by-hypothesis

### 1. Daemon-thread leak (`sse_pump.py` worker lifecycle) — **RULED IN (partial fix only)**

EVIDENCE FOR

- `sse_pump.pump_worker_into_sse` (sse_pump.py:42-136) joins the worker
  thread for **`join_timeout=1.0` second** in its `finally` block.
  Anything blocking longer than that survives the disconnect and
  keeps running.
- The worker is `daemon=True`, so it won't prevent process exit, but
  during a long run it continues to hold its Neo4j session, its
  Ollama HTTP connection, and (most importantly) Ollama's single
  serial inference slot.
- The worker only polls `stop_event.is_set()` at the **top of each
  turn** (shared_agent.py:1039-1040). Inside a turn it is blocked on:
    * `_call_backend()` — `requests.post(...)` to Ollama with
      `timeout=600` (shared_agent.py:599).
    * `dispatch_tool()` — Cypher queries, reranker, embedding lookups.
- The existing regression test
  (`tests/regression/test_sse_worker_leak.py`) only covers a worker
  that *polls stop_event in a tight ~10ms loop*. It does NOT cover a
  worker that's blocked in a synchronous I/O call that ignores
  Python-level signals.

EVIDENCE AGAINST

- All `driver.session(...)` callsites in the request path use
  `with driver.session() as s:` (context manager). When the worker
  eventually returns, the session is released cleanly. So the leak
  doesn't grow Neo4j sessions unboundedly — only as many as are
  in-flight at any given moment (typically 1-2 when this fires).
- Failures recover between bursts (longest streak = 5). A genuinely
  monotonic thread leak would not recover; this looks more like
  *transient amplification of latency drift* than runaway leakage.

VERDICT — **RULED IN as a real defect but as an AMPLIFIER, not the
root cause.** The "Bug D" daemon-thread fix from Phase 3b was a
half-fix: it works for `stop_event`-polling workers, fails for workers
blocked inside the 600s Ollama POST. After a client read-timeout, the
worker keeps running, completes (or aborts) its Ollama call somewhere
in the next 30-300s, and during that window subsequent requests can
queue behind it on Ollama's serial inference path. The fact that the
runner pauses 5s between requests, combined with most Ollama calls
completing in <60s, keeps this from cascading into total failure.

### 2. Ollama / qwen3:14b state accumulation — **RULED IN (likely primary)**

EVIDENCE FOR

- The rolling-median elapsed climbs steadily across phase 1
  (~150s → ~190s → ~210s by Q22) **without any code-side state
  changing**. The simplest explanation is that the inference process
  itself is getting slower.
- qwen3:14b is a 14B-parameter MoE-style model running with
  `num_ctx=24576` per call (shared_agent.py:961). Over hours of
  continuous inference, common Ollama-side degradations are: KV-cache
  fragmentation, GPU VRAM fragmentation forcing larger allocator
  passes, model state staleness in the runtime.
- Ollama's HTTP API is documented to **serialize** requests against a
  single loaded model (one in-flight at a time). When a leaked worker
  (hypothesis 1) is still chewing on its previous POST, the next
  POST blocks waiting for the slot — adding the previous call's
  remaining latency to the next call's wall time.

EVIDENCE AGAINST

- Cannot verify directly from inside this read-only diagnosis session.
  No nvidia-smi captures from the original run; no Ollama-server
  logs included in the baseline artifact set. Need a fresh
  reproduction (see "Reproduction recipe" below) with nvidia-smi
  sampling once per question to nail it down quantitatively.

VERDICT — **RULED IN, with the caveat that direct telemetry was not
captured.** The latency-drift pattern in phase 1 is consistent with
Ollama-side slowdown rather than anything controllable from
`app_free.py`. The fix at this layer is operational, not code:
restart Ollama between long sequential runs, or send
`POST /api/generate {keep_alive: 0}` between batches.

### 3. Neo4j session / connection-pool exhaustion — **RULED OUT**

EVIDENCE FOR / AGAINST

- Grep over the request-path files (`app_free.py`, `shared_agent.py`,
  `chat.py`, `reasoning_memory.py`) shows every `driver.session(...)`
  call uses the `with` context manager. Sessions auto-close on
  scope exit, including on exceptions. No raw `session = driver.session()`
  patterns anywhere in the request path.
- The Neo4j Python driver's default `max_connection_pool_size` is 100.
  Even with hypothesis-1 in-flight leaks, peak concurrency is 2-3
  worker threads, well within budget.
- A genuine pool-exhaustion symptom would be a sharp cliff
  (everything fails simultaneously once the 100th connection is
  drawn), not the gradual drift actually observed.

VERDICT — **RULED OUT.** Code inspection is sufficient evidence; no
probe needed.

### 4. Reasoning-memory write pile-up — **RULED OUT**

EVIDENCE FOR / AGAINST

- Each query writes a small constant number of nodes:
  1 `Query` + 1 `ReasoningTrace` + N `ToolCall` (typically 7-8) +
  some `RETRIEVED` edges. Neo4j with the documented indexes handles
  this in <10ms per write — even 50 queries × 8 calls = ~400 ToolCall
  writes, total ~4s budget across the whole run.
- No accumulating in-memory state on the Python side
  (`QueryRecorder` holds counters, frees on `finish()`).
- A real reasoning-memory bottleneck would show up as proportional
  per-tool-call slowdown across the whole run, not the latency drift
  + abrupt failure pattern observed.

VERDICT — **RULED OUT** based on code inspection. (A live probe would
just confirm: write throughput stays flat across a re-run.)

### 5. TCP keepalive / socket exhaustion — **RULED OUT**

EVIDENCE FOR / AGAINST

- 50 sequential requests over 3.5h ≈ one connection every 4 minutes.
  TIME_WAIT exhaustion needs *hundreds per second*, not one per
  240 seconds.
- The runner uses `requests.post(..., stream=True)`; each connection
  closes when the body is consumed or the iterator is closed. No
  pool exhaustion on the client side either.
- Windows ephemeral-port range is 49152-65535 (~16k ports); the run
  never used more than ~50.

VERDICT — **RULED OUT.** Order-of-magnitude estimate is sufficient.

## Bonus finding — answer-cache I/O tax (real, but not the cause)

`probe_cache_io_cost.py` against the live `data/answer_cache.json`
(47 MB, 1,561 entries):

- `_load_cache()`: median **450 ms** per call
- `_save_cache()`: median **970 ms** per call
- Every `/chat` does load (build_cache_context) + load (save_answer) +
  save (save_answer) ≈ **1.9s of pure JSON I/O per request**
- Across 50 requests: ~95s of cache-I/O overhead — non-trivial but
  not the cause of 300s+ timeouts

This is a separate file to flag for a follow-up: the cache should be
either (a) backed by Neo4j, (b) loaded once at process start and held
in-memory with append-only writes, or (c) incrementally written.
**Out of scope for the degradation fix.**

## Recommended fix scope

**Primary fix — keep the SSE stream alive.** In `sse_pump.py`, when
the queue has been empty for ~10s, yield an SSE comment frame:

```python
yield ": keepalive\n\n"
```

This is a no-op on the JS client (comment frames start with `:` per the
SSE spec) and re-arms the client's read-timeout. Replaces the current
busy-wait sleep loop with a wait-with-deadline. **~30 LOC in
`sse_pump.py:106`**; one new regression test covering "consumer's
read-timeout doesn't fire while worker is blocked".

**Secondary fix — make Ollama-call interruption real.** In
`shared_agent.run`, after `_call_backend` returns AND between
`dispatch_tool` calls, check `stop_event.is_set()` and bail. **~10
LOC**. Doesn't help when the worker is *currently* inside `requests.post`
(Python signals can't interrupt a blocking syscall from another thread
on Windows), but tightens the post-call window. A more thorough fix
would use `requests.Session` + a Future-style pattern, but that's a
larger refactor.

**Optional operational fix — Ollama refresh between bursts.**
Send `POST /api/generate {model, keep_alive: 0}` to force-unload then
reload before a long eval. Not a code change; a runner-level concern.

## Open questions

- **Direct GPU/VRAM evidence missing.** Without nvidia-smi or
  `ollama ps` captures from the original run, the "Ollama is genuinely
  slowing down" claim is inferred from latency drift, not measured.
  A controlled re-run with `nvidia-smi --query-gpu=memory.used,utilization.gpu
  --format=csv -l 5 > captures/gpu.csv` would settle it.
- **Does the worker-thread leak actually fire in normal client
  behaviour?** The runner's 300s read-timeout closes the connection;
  FastAPI/Starlette `StreamingResponse` should propagate that to a
  cancellation of the async generator, hitting `pump_worker_into_sse`'s
  `finally`. `probe_thread_count.py` is staged for the operator to run
  against a live server to confirm thread accumulation.
- **Was Q24 the first failure because of cache size?** The cache grew
  from ~1500 to ~1561 entries during this run. Per-request cache I/O
  is ~2s — across 23 successful questions that's ~46s of accumulated
  tax. Plausible contributor but not enough to explain a 300s budget
  blow-up by itself.

## Reproduction recipe (for verifying any subsequent fix)

Compressed version of the overnight run — should hit at least one
"error" verdict in 30-45 min if the bug is still present.

```bash
# 1. Restart everything fresh.
#    - stop the Neo4j 'quran' DB, restart it
#    - kill any running ollama serve, restart it
#    - launch app_free.py with qwen3:14b
SEMANTIC_SEARCH_INDEX=verse_embedding_m3 \
RERANKER_MODEL=BAAI/bge-reranker-v2-m3 \
python app_free.py --model qwen3:14b

# 2. Run the first 15 thematic questions back-to-back, no inter-pause.
#    This is enough sequential pressure to reproduce phase-2 behaviour
#    in ~30 min instead of ~2h.
python -c "
import requests, time
qs = [
    'What does the Quran say about charity?',
    'What does the Quran teach about forgiveness?',
    'What does the Quran say about gratitude?',
    'What does the Quran say about sin?',
    'What does the Quran say about patience?',
    'What does the Quran teach about humility?',
    'What does the Quran say about repentance?',
    'How does the Quran describe true belief?',
    'What does the Quran say about hypocrisy?',
    'What does the Quran teach about justice?',
    'What does the Quran say about wealth and worldly attachment?',
    'What does the Quran teach about death and the soul?',
    'How does the Quran describe the mercy of God?',
    'What does the Quran say about prayer?',
    'What does the Quran teach about honoring parents?',
]
for i, q in enumerate(qs, 1):
    t0 = time.time()
    r = requests.post('http://localhost:8085/chat',
                      json={'message': q, 'history': [], 'local_only': True},
                      stream=True, timeout=(10, 300))
    frames = 0
    last_frame = time.time()
    max_gap = 0
    for line in r.iter_lines(decode_unicode=True):
        if line and line.startswith('data: '):
            frames += 1
            gap = time.time() - last_frame
            max_gap = max(max_gap, gap)
            last_frame = time.time()
    print(f'Q{i:2d}: {time.time()-t0:.1f}s, frames={frames}, '
          f'max_inter_frame_gap={max_gap:.1f}s')
    time.sleep(1)
"

# 3. Verify the fix.
#    A fixed server should show max_inter_frame_gap <= 15s on every
#    question (the keepalive cadence). The current code shows gaps
#    that grow with answer-generation latency; once one crosses 300s
#    you've reproduced the bug.
```

## Total wall time + cost

- Wall time: ~70 min (within the 3h budget)
- Token cost: $0 (no Anthropic / OpenRouter calls; all work was local
  reads + probes)
