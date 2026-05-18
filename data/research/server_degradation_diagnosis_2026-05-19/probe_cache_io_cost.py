"""Measure the per-request cost of answer_cache.json load/save.

`shared_agent.agent_stream` calls `build_cache_context` at the start of every
chat (which `_load_cache`s the full JSON) AND `save_answer` at the end (which
`_load_cache`s + `_save_cache`s). With a 49MB cache, this adds non-trivial
overhead to every request.

This probe times each operation against the live cache file. Pure I/O — no
Neo4j, no Ollama, no model load.
"""
from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

# Find the real repo root (run from a worktree).
HERE = Path(__file__).resolve()
for p in HERE.parents:
    cand = p / "data" / "answer_cache.json"
    if cand.exists():
        CACHE = cand
        break
else:
    raise SystemExit("answer_cache.json not found in any parent's data/ dir")

print(f"  cache: {CACHE}")
print(f"  size:  {CACHE.stat().st_size / 1024 / 1024:.1f} MB")

# Warm OS file cache.
_ = CACHE.read_bytes()

# Time _load_cache equivalent.
load_times = []
N = 5
for _ in range(N):
    t0 = time.perf_counter()
    with open(CACHE, "r", encoding="utf-8") as f:
        entries = json.load(f)
    load_times.append((time.perf_counter() - t0) * 1000)

print()
print(f"  entries:        {len(entries):,}")
print(f"  load times (ms): "
      f"min={min(load_times):.0f}  "
      f"median={statistics.median(load_times):.0f}  "
      f"max={max(load_times):.0f}  "
      f"(N={N})")

# Time _save_cache equivalent (write to /tmp to avoid clobbering live cache).
import tempfile
save_times = []
with tempfile.TemporaryDirectory() as td:
    out = Path(td) / "scratch.json"
    for _ in range(N):
        t0 = time.perf_counter()
        with open(out, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=1)
        save_times.append((time.perf_counter() - t0) * 1000)
print(f"  save times (ms): "
      f"min={min(save_times):.0f}  "
      f"median={statistics.median(save_times):.0f}  "
      f"max={max(save_times):.0f}  "
      f"(N={N})")

# A typical /chat does both: 1 load (cache lookup) + 1 load + 1 save (save).
per_req_load_load_save_ms = (
    statistics.median(load_times)
    + statistics.median(load_times)
    + statistics.median(save_times)
)
print()
print(f"  est. cache I/O per /chat (1 load + 1 load + 1 save) = "
      f"{per_req_load_load_save_ms:.0f} ms")
print(f"  over 50 sequential requests: {50 * per_req_load_load_save_ms / 1000:.1f} s "
      "of pure cache I/O (no LLM, no Neo4j)")

# Per-entry dedup scan cost (numpy dot products inside save_answer).
import numpy as np
embs = np.array([e["embedding"] for e in entries], dtype=np.float32)
print()
print(f"  embeddings matrix: shape={embs.shape}  "
      f"nbytes={embs.nbytes / 1024 / 1024:.1f} MB")
fake_q = np.random.randn(embs.shape[1]).astype(np.float32)
fake_q /= np.linalg.norm(fake_q)
dot_times = []
for _ in range(20):
    t0 = time.perf_counter()
    # mimic save_answer dedup loop: pure Python scan (line 75 in answer_cache.py).
    for entry in entries:
        sim = float(np.dot(fake_q, entry["embedding"]))
        if sim > 0.98:
            break
    dot_times.append((time.perf_counter() - t0) * 1000)
print(f"  save_answer dedup scan (pure-Python loop): "
      f"median={statistics.median(dot_times):.0f} ms  "
      f"max={max(dot_times):.0f} ms  (N=20)")
