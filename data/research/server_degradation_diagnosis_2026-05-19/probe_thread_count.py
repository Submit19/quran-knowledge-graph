"""Probe: does the app_free.py worker thread leak after client disconnect?

Operator-runnable probe. Requires a running app_free.py + Neo4j + Ollama with
qwen3:14b loaded. Fires N short /chat requests; each request the client
ABORTS mid-stream by closing the connection after T seconds (simulating the
runner's 300s read-timeout, but compressed to 5-10s for fast feedback).

Server-side, we cannot directly read `threading.active_count()` of a remote
process, so the operator should watch the server's stdout (it prints
`[turn N] backend=... model=...` per turn) AND `tasklist /fi "pid eq <pid>" /v`
or Resource Monitor for thread count growth on the python.exe PID.

Alternative: this probe asks /model-status — if degradation is happening,
status responses themselves should start lagging.

Usage:
    python probe_thread_count.py --n 20 --abort-after 8

Reads the /chat response stream and forcibly closes the connection after
``--abort-after`` seconds, regardless of completion state. Reports per-call
client-side timing.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from threading import Thread

import requests

BASE = os.getenv("BASE", "http://localhost:8085")


def _abort_after_one(idx: int, question: str, abort_after: float) -> dict:
    payload = {"message": question, "history": [], "local_only": True}
    t0 = time.time()
    sse_frames = 0
    aborted = False
    err = None
    try:
        r = requests.post(f"{BASE}/chat", json=payload, stream=True,
                          timeout=(5, abort_after + 60))
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                sse_frames += 1
            if time.time() - t0 > abort_after:
                aborted = True
                r.close()  # mimic the runner's behaviour on read-timeout break
                break
    except Exception as e:
        err = f"{e.__class__.__name__}: {str(e)[:120]}"
    elapsed = round(time.time() - t0, 2)

    # Probe the server for liveness right after the abort.
    health_t0 = time.time()
    try:
        h = requests.get(f"{BASE}/model-status", timeout=5)
        health_ms = int((time.time() - health_t0) * 1000)
        health_state = h.json().get("state")
    except Exception as he:
        health_ms = int((time.time() - health_t0) * 1000)
        health_state = f"err:{he.__class__.__name__}"

    return {
        "idx": idx,
        "elapsed": elapsed,
        "sse_frames": sse_frames,
        "aborted": aborted,
        "error": err,
        "post_abort_health_ms": health_ms,
        "post_abort_health": health_state,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=20, help="number of abort cycles")
    p.add_argument("--abort-after", type=float, default=8.0,
                   help="seconds before client closes the SSE connection")
    p.add_argument("--question", default="What does the Quran say about charity?")
    p.add_argument("--inter-pause", type=float, default=2.0)
    args = p.parse_args()

    print(f"  base={BASE}  n={args.n}  abort_after={args.abort_after}s")
    print(f"  question={args.question!r}")
    print()
    print(f"  {'#':>3}  {'elapsed':>7}  {'frames':>6}  {'health_ms':>9}  "
          f"{'health':>15}  notes")
    for i in range(1, args.n + 1):
        row = _abort_after_one(i, args.question, args.abort_after)
        print(f"  {i:3d}  {row['elapsed']:>7.2f}s  {row['sse_frames']:>6d}  "
              f"{row['post_abort_health_ms']:>9d}  "
              f"{row['post_abort_health']!s:>15}  "
              f"{'aborted' if row['aborted'] else ''} "
              f"{row['error'] or ''}")
        sys.stdout.flush()
        time.sleep(args.inter_pause)

    print()
    print("  Interpretation:")
    print("  * If post_abort_health_ms grows over the run, the server's")
    print("    event loop is being starved by leaked worker threads.")
    print("  * If a fresh /chat (started after an abort) takes far longer")
    print("    than its first turn would naturally need, Ollama is queued")
    print("    behind the leaked worker's in-flight call.")
    print("  * Watch the server's stdout for `[turn N]` lines — if turns from")
    print("    aborted requests keep printing AFTER you've moved to the next")
    print("    request, the worker thread is in fact leaking (Bug D is")
    print("    not actually fixed for mid-Ollama-call disconnects).")


if __name__ == "__main__":
    main()
