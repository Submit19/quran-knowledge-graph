"""
Regression: SSE worker thread leaks after consumer disconnect (Bug D).

The /chat SSE endpoint in app_free spawns a daemon thread that does LLM
calls, Neo4j queries, and pushes events into a queue. The async generator
yields those events as SSE frames. Before this fix, if the consumer
(client) disconnected, the generator stopped being driven — but the
daemon thread kept running through its remaining LLM calls and tool
dispatches. The work was wasted and, on a real server, could pin CPU/GPU
and burn API quota.

The orchestration was extracted into sse_pump.pump_worker_into_sse so it
can be tested without spinning up the whole agent loop (no Neo4j, no
LLM client, no FastAPI required in CI). A fake worker emulates the "LLM
keeps returning tool_use forever" pattern by ticking events at ~10ms
intervals until told to stop.

  - test_consumer_aclose_stops_the_worker:
      Drives the generator, pulls a few events, calls aclose(). Asserts
      the worker winds down within ~1.5s. Before the fix the worker
      kept ticking forever; the fix wraps the yield loop in try/finally,
      sets a threading.Event the worker polls, and joins with a short
      timeout.

  - test_worker_completion_terminates_normally:
      Triangulation. Same helper, worker finishes on its own. Verifies
      the normal-completion path is not broken by the fix.
"""

from __future__ import annotations

import asyncio
import threading
import time

import sse_pump


def _drive(gen, *, events_to_pull: int, then_close: bool) -> list:
    """Sync wrapper: asyncio.run an async iteration over `gen`."""
    pulled = []

    async def run():
        try:
            for _ in range(events_to_pull):
                pulled.append(await gen.__anext__())
        finally:
            if then_close:
                await gen.aclose()

    asyncio.run(run())
    return pulled


def test_consumer_aclose_stops_the_worker():
    """The headline leak: closing the SSE generator must wind down the worker."""
    finished = threading.Event()

    def never_exiting_worker(q, stop_event):
        try:
            while not stop_event.is_set():
                q.put({"t": "tick"})
                time.sleep(0.01)
            q.put(None)
        finally:
            finished.set()

    gen = sse_pump.pump_worker_into_sse(never_exiting_worker)
    pulled = _drive(gen, events_to_pull=3, then_close=True)

    assert len(pulled) == 3, f"expected to pull 3 events; got {pulled!r}"

    # After aclose, the helper should signal the worker and the worker
    # should exit within ~1s. Today's buggy code does neither.
    assert finished.wait(timeout=1.5), (
        "worker thread was not signaled to stop after consumer disconnect"
    )


def test_worker_completion_terminates_normally():
    """Triangulation: the helper must still pass through a clean worker exit."""
    finished = threading.Event()

    def short_worker(q, stop_event):
        try:
            for i in range(3):
                q.put({"t": "tick", "i": i})
            q.put(None)
        finally:
            finished.set()

    gen = sse_pump.pump_worker_into_sse(short_worker)
    pulled = _drive(gen, events_to_pull=3, then_close=False)

    # After 3 events the worker has pushed the None sentinel.
    # Drain to completion to let the generator unwind cleanly.
    async def drain():
        try:
            while True:
                await gen.__anext__()
        except StopAsyncIteration:
            pass

    asyncio.run(drain())

    assert len(pulled) == 3
    # Each pulled frame is an SSE "data: ...\n\n" line.
    for frame in pulled:
        assert frame.startswith("data: ")
        assert frame.endswith("\n\n")
    assert finished.is_set()
