---
type: architecture
subsystem: reasoning-memory
status: current
date_added: 2026-05-10
---

# Reasoning Memory

## What it does

Persists every `/chat` request as a subgraph in Neo4j so the agent can learn from past reasoning patterns. Each query writes a `Query → ReasoningTrace → ToolCall` chain and accumulates `RETRIEVED` edges linking traces to the verses each tool returned. Similar past queries are surfaced as a "playbook" via `tool_recall_similar_query`.

## Where it lives

- `reasoning_memory.py` — `ReasoningMemory` class + `QueryRecorder` class
- Called from `app_free.py` and `app.py` at query start/end and per tool call

## Graph schema

```mermaid
graph LR
    Q["(:Query)\nqueryId, text, textEmbedding\ntimestamp, backend"] -->|TRIGGERED| T
    T["(:ReasoningTrace)\ntraceId, turn_count\ntool_call_count, citation_count\nstatus"] -->|HAS_STEP {order}| TC
    TC["(:ToolCall)\ncallId, turn, tool_name\nargs_json, summary\nok, duration_ms"] -->|RETRIEVED {tool,rank,turn}| V
    V["(:Verse)\nverseId"]
    Q -->|PRODUCED| A["(:Answer)\nanswerText, cited_verses"]
    T -->|HAS_CITATION_CHECK| CC["(:CitationCheck)"]
```

## Key API

```python
rm = ReasoningMemory(driver)
rm.ensure_schema()          # idempotent — CREATE INDEX IF NOT EXISTS

recorder = rm.start_query(text, backend="ollama:qwen3:8b")
recorder.log_tool_call(turn=1, order=0, tool_name="search_keyword",
                       args={...}, summary="...", ok=True,
                       duration_ms=1200, result_payload=tool_result)
recorder.finish(answer_text="...", citation_count=12, status="completed")

rm.find_similar_queries("How should I endure hardship?", top_k=3, min_sim=0.7)
```

`log_tool_call` with `result_payload` automatically extracts verse references from the JSON payload via regex, then writes `(ReasoningTrace)-[:RETRIEVED {tool, rank, turn}]->(Verse)` edges in a single batch.

## Vector index for recall

`query_embedding` — cosine, 384d, all-MiniLM-L6-v2 over `Query.textEmbedding`. Used by `find_similar_queries()` which backs `tool_recall_similar_query`. Returns past query text + tool step sequence + final answer.

## Accumulated scale (~2026-05-10)

- ~2,662 `ReasoningTrace` nodes
- ~32K `RETRIEVED` edges
- These are the raw signal for future fine-tuning or RL on which retrieval tools work best per query type

## Known gaps

- **Missing `:ReasoningStep`** — the schema uses `ToolCall` directly; a separate Step node for intermediate reasoning text was proposed but not implemented.
- **No bitemporal properties** — `ReasoningTrace` has no `valid_from / valid_to`; temporal queries rely on `Query.timestamp` alone.
- **No `:Session` grouping** — individual queries are not grouped by user session. Multi-turn conversations look like independent Query nodes.
- **Embedding model mismatch** — `Query.textEmbedding` uses legacy MiniLM-384d (not BGE-M3-1024d); similarity recall is weaker than verse retrieval. Tracked in backlog.

## Cross-references
- [[graph-schema]] — full node/relationship property list
- [[agent-loop]] — recorder called around each `dispatch_tool()` call
- [[citation-verification]] — `HAS_CITATION_CHECK` edges written by verifier
- Source: `repo://reasoning_memory.py`, `repo://CLAUDE.md` (Key Subsystems section)
