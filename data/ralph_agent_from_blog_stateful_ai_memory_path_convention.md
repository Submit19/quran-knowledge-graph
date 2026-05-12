# from_blog_stateful_ai_memory_path_convention — Implementation notes

**Task:** Add structured `memory_path` property to `ReasoningTrace` nodes.
**Status:** DONE — code change + index landed in `reasoning_memory.py`.

---

## What was changed

### `reasoning_memory.py` — two edits

**1. Schema docstring updated** — `ReasoningTrace` node doc now shows `memory_path` as a property with its format and purpose.

**2. `start_query()` updated** — `memory_path` is now computed and written at trace creation time:

```python
memory_path = f"sessions/{query_id}/traces/{trace_id}"
```

The `ReasoningTrace` CREATE includes `memory_path: $memory_path`.

**3. `ensure_schema()` updated** — new index added so path-prefix queries stay fast:

```cypher
CREATE INDEX trace_memory_path IF NOT EXISTS FOR (t:ReasoningTrace) ON (t.memory_path)
```

---

## Path format rationale

`sessions/<query_id>/traces/<trace_id>`

- **Hierarchical** — a session can contain many queries; each query triggers one trace. The path mirrors a file-system convention familiar to tooling.
- **Prefix-queryable** — given a session UUID, all its traces can be found via string prefix: `WHERE t.memory_path STARTS WITH 'sessions/<session_id>/'`.
- **Globally unique** — both IDs are UUID v4, so no collisions across sessions.
- **Forward-compatible** — if we later add a `UserSession` layer, the path can be extended to `users/<uid>/sessions/<sid>/traces/<tid>` by changing just this one line.

---

## Enabling queries

Once indexed, the following are now efficient:

```cypher
-- All traces for a given session (e.g. future UserSession grouping)
MATCH (t:ReasoningTrace)
WHERE t.memory_path STARTS WITH 'sessions/<query_id>/'
RETURN t.traceId, t.status, t.citation_count

-- Exact lookup by path (for MCP memory-tool exposure)
MATCH (t:ReasoningTrace {memory_path: $path})
RETURN t

-- Session-scoped retrieval: which verses did this session surface?
MATCH (t:ReasoningTrace)-[:RETRIEVED]->(v:Verse)
WHERE t.memory_path STARTS WITH 'sessions/<query_id>/'
RETURN v.verseId, count(*) AS n ORDER BY n DESC
```

---

## Backfill for existing traces

Existing ReasoningTrace nodes (pre-this-tick) have `memory_path = null`. A backfill script can set a `pre-memory-path` sentinel:

```cypher
MATCH (t:ReasoningTrace)
WHERE t.memory_path IS NULL
SET t.memory_path = 'sessions/unknown/traces/' + t.traceId
```

This is safe to run any time and is idempotent.

---

## Impact

- **Schema-additive** — all existing graph queries continue to work unchanged.
- **No runtime cost** — `memory_path` is a string computed in Python before the CREATE; no extra Cypher calls.
- **MCP memory tool** — when a future tool exposes `list_session_traces(session_id)`, it simply queries `STARTS WITH 'sessions/<session_id>/'`.
- **Cross-reference with `from_blog_reasoning_memory_session_layer`** (p55) — that task adds a `(:UserSession)-[:HAS_QUERY]->(:Query)` layer. The `memory_path` convention here is a prerequisite that makes the retrieval queries in that layer efficient.
