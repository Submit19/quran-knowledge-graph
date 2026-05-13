"""Daemon-thread + queue → SSE-frame helper.

Extracted from app_free._agent_stream so the orchestration can be
tested in isolation (no Neo4j, no LLM clients, no FastAPI required).

The helper runs a worker callable in a daemon thread, drains events
from a queue, and yields each as an SSE-formatted line. When the
consumer (e.g. FastAPI's StreamingResponse) disconnects, the
finally block signals the worker via a threading.Event and joins
with a short timeout. Workers with long-running steps (LLM calls,
large Cypher) should poll the event between steps to cooperate
with the teardown.
"""

from __future__ import annotations

import asyncio
import json
import queue as tqueue
import threading
from collections.abc import AsyncIterator
from typing import Callable


async def pump_worker_into_sse(
    run_fn: Callable[[tqueue.SimpleQueue, threading.Event], None],
    *,
    join_timeout: float = 1.0,
) -> AsyncIterator[str]:
    """Run `run_fn(queue, stop_event)` in a daemon thread; yield SSE frames.

    Encapsulates the daemon-thread + queue orchestration that powers
    streaming endpoints. The worker pushes dict events into the queue
    and a final None sentinel when done; this helper drains the queue
    and yields each event as an SSE-formatted line.

    On consumer disconnect the finally block sets the stop_event and
    joins the worker thread with a short timeout. Workers with long-
    running steps MUST poll stop_event between steps for the teardown
    to take effect; the daemon flag ensures the process can still exit
    even if a step blocks past the join timeout.
    """
    q: tqueue.SimpleQueue = tqueue.SimpleQueue()
    stop_event = threading.Event()

    def target() -> None:
        try:
            run_fn(q, stop_event)
        finally:
            # Belt-and-braces sentinel — guarantees the consumer's
            # `if event is None: break` fires even if run_fn raised.
            q.put(None)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()

    try:
        while True:
            try:
                event = q.get_nowait()
            except Exception:
                await asyncio.sleep(0.05)
                continue
            if event is None:
                break
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    finally:
        stop_event.set()
        thread.join(timeout=join_timeout)
