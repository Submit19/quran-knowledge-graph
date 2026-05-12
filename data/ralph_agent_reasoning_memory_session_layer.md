# Design: Reasoning Memory Session Layer
## Task: `from_blog_reasoning_memory_session_layer`
## Status: DELIVERABLE — design doc + diff sketch

---

## Motivation

The current reasoning memory schema records each `/chat` turn as an isolated
`(:Query)` node. There is no notion of a *conversation session* — a sequence of
related queries by the same user in one sitting. Adding this layer enables:

1. **Intra-session context injection** — surface the last N queries from the
   *current session* as context, not just the globally most-similar past queries.
   This handles follow-up questions ("what about verse 9:5?") that are
   semantically distant from their parent but logically dependent.
2. **Session-scoped playback** — `memory_path` already encodes
   `sessions/<query_id>/traces/<trace_id>`; a `UserSession` node makes this
   prefix queryable rather than implicit.
3. **Future MCP memory-tool exposure** — an MCP tool can walk
   `(:UserSession)-[:HAS_QUERY]->(:Query)` to reconstruct the session transcript.
4. **Chain-of-queries retrieval** — `(:Query)-[:NEXT_QUERY]->(:Query)` edges let
   us detect when the same concept is queried multiple times (topic persistence
   signal), which is input for `recall_similar_query` improvements.

---

## Schema additions (additive — no migrations needed)

### New node: `:UserSession`

```cypher
(:UserSession {
    sessionId,      // UUID, generated per browser page-load / API client token
    started_at,     // datetime ISO
    backend,        // e.g. "openrouter:qwen3:8b-fp8" (from first query in session)
    query_count,    // int, incremented on each HAS_QUERY edge creation
})
```

### New relationship: `(:UserSession)-[:HAS_QUERY {order}]->(:Query)`

* `order` is a 1-based counter scoped to the session, set at write time.

### New relationship: `(:Query)-[:NEXT_QUERY]->(:Query)`

* Written between consecutive queries within the same session.
* Only written when `prev_query_id` is available (i.e., second query onward).

### New BGE-M3 vector index on Query (upgrade from MiniLM-384d)

```cypher
CREATE VECTOR INDEX query_embedding_m3 IF NOT EXISTS
FOR (q:Query) ON (q.textEmbeddingM3)
OPTIONS {indexConfig: {
  `vector.dimensions`: 1024,
  `vector.similarity_function`: 'cosine'
}};
```

`textEmbeddingM3` is a new property alongside the existing `textEmbedding`
(384-dim MiniLM). Adding the M3 variant is additive; the existing
`query_embedding` index continues to work.

### New index on UserSession

```cypher
CREATE INDEX user_session_id IF NOT EXISTS FOR (s:UserSession) ON (s.sessionId);
CREATE INDEX user_session_started IF NOT EXISTS FOR (s:UserSession) ON (s.started_at);
```

---

## API surface changes (diff sketch)

### `reasoning_memory.py` — `ReasoningMemory` class

**1. `ensure_schema()` — add 3 new index/vector statements:**

```python
s.run("CREATE INDEX user_session_id IF NOT EXISTS FOR (s:UserSession) ON (s.sessionId)")
s.run("CREATE INDEX user_session_started IF NOT EXISTS FOR (s:UserSession) ON (s.started_at)")
try:
    s.run("""
        CREATE VECTOR INDEX query_embedding_m3 IF NOT EXISTS
        FOR (q:Query) ON (q.textEmbeddingM3)
        OPTIONS {indexConfig: {`vector.dimensions`: 1024, `vector.similarity_function`: 'cosine'}}
    """)
except Exception as e:
    print(f"  [reasoning_memory] m3 vector index setup: {e}")
```

**2. New method `start_session(backend: str) -> str`:**

```python
def start_session(self, backend: str) -> str:
    """Create a UserSession node. Returns session_id. Call once per browser load."""
    session_id = str(uuid.uuid4())
    ts = _now_iso()
    with self.driver.session(database=self.db) as s:
        s.run("""
            CREATE (:UserSession {
                sessionId: $sid, started_at: datetime($ts),
                backend: $backend, query_count: 0
            })
        """, sid=session_id, ts=ts, backend=backend)
    return session_id
```

**3. `start_query()` — two new keyword args: `session_id`, `prev_query_id`:**

```python
def start_query(self, text: str, backend: str, deep_dive: bool = False,
                session_id: str | None = None,
                prev_query_id: str | None = None) -> "QueryRecorder":
```

Inside the method body, after creating `(:Query)` and `(:ReasoningTrace)`, add:

```python
if session_id:
    # Atomically increment query_count and link to session
    with self.driver.session(database=self.db) as s:
        s.run("""
            MATCH (sess:UserSession {sessionId: $sid})
            MATCH (q:Query {queryId: $qid})
            CREATE (sess)-[:HAS_QUERY {order: sess.query_count + 1}]->(q)
            SET sess.query_count = sess.query_count + 1
        """, sid=session_id, qid=query_id)

if prev_query_id and session_id:
    with self.driver.session(database=self.db) as s:
        s.run("""
            MATCH (prev:Query {queryId: $prev_qid})
            MATCH (curr:Query {queryId: $curr_qid})
            MERGE (prev)-[:NEXT_QUERY]->(curr)
        """, prev_qid=prev_query_id, curr_qid=query_id)
```

**4. New method `find_session_context(session_id, current_query_id, top_n=3) -> list[dict]`:**

Returns the most recent N queries in the session (excluding the current one),
for injection as system context.

```python
def find_session_context(self, session_id: str, current_query_id: str,
                          top_n: int = 3) -> list[dict]:
    """Return last N queries in session as context rows."""
    with self.driver.session(database=self.db) as s:
        rows = s.run("""
            MATCH (sess:UserSession {sessionId: $sid})-[hq:HAS_QUERY]->(q:Query)
            WHERE q.queryId <> $cur_qid
            OPTIONAL MATCH (q)-[:PRODUCED]->(a:Answer)
            RETURN q.queryId AS queryId, q.text AS text, hq.order AS order,
                   a.text AS answer
            ORDER BY hq.order DESC
            LIMIT $n
        """, sid=session_id, cur_qid=current_query_id, n=top_n).data()
    return rows
```

**5. Async wrapper (optional, for app_free.py daemon thread):**

`start_session` and the session-linking inside `start_query` are cheap (single
MERGE/CREATE). No async wrapping needed — they run synchronously in the daemon
thread before the first token is emitted.

---

## `app_free.py` — integration diff sketch

### Session lifecycle

The frontend (index.html) generates a `session_id` UUID on page load and sends
it in each `/chat` request body. The server:

1. On *first* request with a new `session_id`: calls `reasoning_memory.start_session()`.
2. On *subsequent* requests in the same session: passes `session_id` + `prev_query_id`
   to `start_query()`.

**Request model change (Pydantic):**

```python
class ChatRequest(BaseModel):
    message: str
    history: list = []
    deep_dive: bool = False
    session_id: str | None = None      # NEW
    prev_query_id: str | None = None   # NEW — returned by prior /chat response
```

**Response model change:**

```python
# In the SSE `done` event, add:
"query_id": rec.query_id if rec else None
```

(Frontend stores `query_id` from the last response and sends it as
`prev_query_id` on the next request — zero server-side session state needed.)

**Session context injection (in `run()`, after answer-cache lookup):**

```python
if rec and session_id:
    try:
        sess_ctx = reasoning_memory.find_session_context(
            session_id, rec.query_id, top_n=3
        )
        if sess_ctx:
            ctx_lines = ["## Recent queries in this session:"]
            for r in sess_ctx:
                ctx_lines.append(f"- Q: {r['text']}")
                if r.get('answer'):
                    ctx_lines.append(f"  A: {r['answer'][:200]}...")
            system_content = system_content + "\n\n" + "\n".join(ctx_lines)
            msgs[0] = {"role": "system", "content": system_content}
    except Exception as se:
        print(f"  [session_ctx] lookup failed: {se}")
```

---

## Implementation notes

### Why BGE-M3 on Query nodes?

The existing `query_embedding` index uses all-MiniLM-L6-v2 (384-dim, English
only). Arabic follow-up questions ("ما هو الصبر؟") won't match their English
predecessors under MiniLM. Upgrading `find_similar_queries()` to use
`query_embedding_m3` (BGE-M3, 1024-dim, multilingual) gives cross-lingual
session continuity — the same motivation as the verse embedding upgrade.

Migration path: `find_similar_queries()` gains a `use_m3: bool = True`
parameter that selects between `query_embedding` and `query_embedding_m3`
indexes, defaulting True when the m3 index exists.

### Performance

- `find_session_context()` is O(query_count) per session but bounded by `top_n=3` LIMIT.
- `start_session()` is a single CREATE (negligible).
- Session-linking inside `start_query()` adds one MATCH+CREATE+SET per query —
  adds <5ms per request (Neo4j local, same pattern as existing RETRIEVED edges).

### Backward compatibility

All changes are additive:
- Existing `start_query()` callers without `session_id` are unaffected (both new
  kwargs default to `None`; the session-linking block is skipped entirely).
- Existing `(:Query)` nodes gain no new required properties.
- The `query_embedding` index is kept; `query_embedding_m3` is a second index.

### Rollout order

1. `reasoning_memory.py` — add `ensure_schema()` stmts, `start_session()`,
   `find_session_context()`, modify `start_query()` signature. ~60 LOC.
2. `app_free.py` — add `session_id` / `prev_query_id` to `ChatRequest`, call
   `start_session()` on first request, inject session context. ~30 LOC.
3. `index.html` — generate UUID on page load, attach to each `/chat` POST,
   store returned `query_id`. ~10 LOC in the existing `fetch('/chat')` call.

Total: ~100 LOC across 3 files. No schema migrations. No new dependencies.

---

## Acceptance criteria

- `data/ralph_agent_reasoning_memory_session_layer.md` exists (this file).
- File >= 600 bytes.

_Generated by ralph loop tick 103 IMPL, 2026-05-12_
