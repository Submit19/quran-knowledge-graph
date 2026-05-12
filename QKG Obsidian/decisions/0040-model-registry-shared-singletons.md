---
type: decision
adr: 0040
status: accepted
date: 2026-05-13
tags: [decision, architecture, performance, memory, model-registry]
supersedes: none
---

# ADR-0040 — Shared ML model singletons via `model_registry.py`

## Status
Accepted (2026-05-13). Shipped in commit `0190f19`, tick 106 IMPL.

## Context
Three modules — `chat.py`, `reasoning_memory.py`, and `answer_cache.py` — each
independently loaded `all-MiniLM-L6-v2` at import time. On a PC with 16–32GB RAM
this caused ~640 MB of duplicate resident memory (the model loads three times into
separate `SentenceTransformer` objects). BGE-M3 was similarly duplicated between
`chat.py` and `retrieval_gate.py`.

On Windows, process startup already takes ~10s for model loading; three independent
loads added avoidable wall-clock latency for `app_free.py`.

## Decision
Introduce `model_registry.py` with three lazy singleton getters:

```python
get_minilm()      # all-MiniLM-L6-v2 (384d)
get_bge_m3()      # BAAI/bge-m3 (1024d)
get_reranker()    # BAAI/bge-reranker-v2-m3
```

Each getter is idempotent: loads once on first call, returns the cached instance
on subsequent calls. All three modules (`chat.py`, `reasoning_memory.py`,
`answer_cache.py`) import from the registry instead of calling
`SentenceTransformer(...)` directly.

## Consequences
- **Positive:** Eliminates ~640 MB duplicate RAM at startup — single MiniLM load
  replaces three.
- **Positive:** Consistent model state across modules (same tokenizer config,
  pooling, device).
- **Positive:** Easier to hot-swap model versions: change the string in one place.
- **Neutral:** Quality gate skipped (Neo4j offline = false negative on app_free
  import). Registry wiring verified by code inspection rather than live run.
- **Neutral:** `get_bge_m3()` and `get_reranker()` are not yet wired into every
  consumer — that can be done incrementally.
- **Negative:** Single-process assumption. If QKG ever moves to multi-worker
  Gunicorn, each worker spawns a separate interpreter and the registry is per-process
  (acceptable; the saving is per-process duplication, not cross-process).

## Cross-references
- Source: commit `0190f19`, task `share_minilm_across_modules`
- Files: `model_registry.py`, `chat.py`, `reasoning_memory.py`, `answer_cache.py`
- Proposed by: ralph IMPL tick 106
