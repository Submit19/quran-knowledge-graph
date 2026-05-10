# Neo4j Agentic / MCP / Agent-Memory Patterns — Findings for QKG

Crawl date: 2026-05-10. Scope: GraphAcademy "Context Graphs", "Building GraphRAG MCP tools", "Neo4j MCP tools", "Aura Agents", "LLM KG Construction"; Neo4j Labs `agent-memory` + `create-context-graph`; Neo4j developer/genai blog (Apr-May 2026).

## TL;DR

- **QKG's `(:Query)-[:TRIGGERED]->(:ReasoningTrace)-[:HAS_STEP]->(:ToolCall)` schema is essentially identical to the canonical Neo4j model**, but we are missing two important nodes (`ReasoningStep` between trace and tool call) and one extremely useful edge (`:TOUCHED` from steps directly to entities). Our `RETRIEVED` edge is the right idea but lives on `ToolCall` rather than on `ReasoningStep`, which breaks compatibility with `neo4j-agent-memory` audit queries.
- **A canonical, supported library exists** (`neo4j-labs/agent-memory`, async-only Python, integrates with Pydantic AI, OpenAI Agents, Claude Agent SDK, LangGraph). It already does ~80% of `reasoning_memory.py`. Migration would buy us: vector indexes on `trace_embedding`, `EXTRACTED_FROM`/`EXTRACTED_BY` provenance, `TraceOutcome` audit nodes, buffered writes, dedup pipeline, eval harness.
- **Aura Agents is no-code only** (Cypher Templates, Text2Cypher, Vector Search). Our 21-tool hand-rolled Anthropic-API loop **cannot** be deployed to it — but Aura Agents *can* be wrapped as one tool and invoked by our loop, useful for Text2Cypher fallback.
- **The official MCP server is a thin wrapper** around three tools (`get_neo4j_schema`, `read_neo4j_cypher`, `write_neo4j_cypher`). It does NOT decompose by domain. Our 21 fine-grained tools are the right shape for Anthropic's tool_use planner; we should keep them but consider exposing the same set via MCP for reuse from Claude Desktop / Cursor.
- **Tool caching is not Neo4j-native in any reference impl** — they use buffered writes + dedup, not TTL caches. Our 30s in-memory `_TOOL_CACHE` is fine; consider promoting it to a `(:ToolCallCache {key, result, expires_at})` node only if we want cross-process sharing.
- **KG construction**: Neo4j ships an LLM Graph Builder with a configurable schema, and the blog stack increasingly recommends `spaCy → GLiNER → LLM` cascade with `GLiREL` for relations. Our hand-rolled keyword/Porter-stem pipeline is fine for Arabic-specific concepts; bolt on GLiNER only if we want to extract person/place/event entities from translations.
- **Memory recall**: their canonical pattern is **vector search on `trace_embedding` + 1-hop expansion to `ToolCall` + `Entity`**. We do step 1 only (`tool_recall_similar_query`) — we are leaving the playbook on the table by not returning the `ToolCall` sequence and the resulting verses.

---

## Per-page findings

### 1. Context Graphs: Agent Memory with Neo4j (GraphAcademy)
URL: https://graphacademy.neo4j.com/courses/genai-context-graphs/

**Summary.** Intermediate course (4 modules / 19 lessons) that teaches building a Pydantic AI agent that "records its complete reasoning trace into Neo4j" and audits decisions with Cypher. Three-layer memory: short-term (messages) / long-term (POLE+O entities) / reasoning (traces, steps, tool calls). Outcome project = exactly what `reasoning_memory.py` does.

**QKG relevance.** Direct overlap with `reasoning_memory.py`. Modules 1, 4 are the highest-value lessons; modules 2, 3 are more general. Lesson titles mention an explicit "Memory API" — that's the `neo4j-agent-memory` package below.

**Concrete patterns.**
- POLE+O entity classification: Person / Object / Location / Event / Organization. Stored as `(:Entity:Person)`, `(:Entity:Location)` — multi-label with `Entity` as the parent.
- Three memory types share a graph: messages trigger traces, traces use tools, tools retrieve entities mentioned in messages. **Provenance is the unifying invariant.**
- The `:TOUCHED` audit edge (v0.2) goes from `ReasoningStep` directly to any `Entity` the step examined — even if the step didn't formally "retrieve" it. This is broader than our `:RETRIEVED` edge (which only fires on hits).

**Action.** Add a "Reasoning trace upgrade" backlog item — see ralph backlog below.

### 2. Neo4j Labs `agent-memory` library
URLs: https://github.com/neo4j-labs/agent-memory · https://deepwiki.com/neo4j-labs/agent-memory

**This is the canonical schema.** Quoting the deepwiki extraction:

```
Short-term:    (:Conversation {id, session_id, created_at, updated_at})
               (:Message      {id, role, content, embedding, created_at})
Long-term:     (:Entity       {id, name, type, subtype, description, embedding})
               (:Preference   {id, category, preference, importance, embedding})
               (:Fact         {id, subject, predicate, object, valid_from, valid_until})
Reasoning:     (:ReasoningTrace {id, session_id, task, success, started_at, completed_at})
               (:ReasoningStep  {id, thought, action, observation, created_at})
               (:ToolCall       {id, tool_name, arguments, result, status, duration_ms})
Provenance:    (:Extractor      {id, name, version, config, created_at})

Edges:
  (Conversation)-[:CONTAINS]->(Message)
  (ReasoningStep)-[:PART_OF]->(ReasoningTrace)
  (ReasoningTrace)-[:CALLED_TOOL]->(ToolCall)
  (Entity)-[:EXTRACTED_FROM]->(Message)
  (Entity)-[:EXTRACTED_BY]->(Extractor)
  (Step|Trace)-[:TOUCHED]->(Entity)             # v0.2
  Semantic edges: WORKS_AT, FOUNDED_BY, LIVES_IN, LOCATED_IN, MEMBER_OF, ...

Indexes (auto-created):
  vector:  message_embedding, entity_embedding, preference_embedding, trace_embedding
  spatial: entity_location  (Point property)
  unique:  entity_id, conversation_id, message_id, trace_id
  prop:    session_id, entity_name, entity_type
```

**API surface (async-only):**
```
memory.short_term.add_message(session_id, role, content)
memory.long_term.add_entity(name, entity_type)
memory.long_term.add_preference(category, preference)
context = memory.get_context(query, session_id=...)
client.buffered.submit(...) ; client.flush()         # batch writes
client.schema.adopt_existing_graph(...)              # adopt our graph
client.consolidation.dedupe_entities(...)            # entity resolution
client.eval.run(EvalSuite(...))                      # eval harness
```

**Critical comparison to `reasoning_memory.py`:**

| Aspect | QKG today | `agent-memory` |
|---|---|---|
| Trace node | `:ReasoningTrace` | `:ReasoningTrace` (match) |
| Step granularity | none — `Trace -[:HAS_STEP]-> ToolCall` | `Trace -[:CALLED_TOOL]-> ToolCall` AND `Step -[:PART_OF]-> Trace` |
| Step content | implicit (in ToolCall) | explicit `thought`, `action`, `observation` |
| Retrieval edge | `:RETRIEVED {tool, rank, turn}` from Trace to Verse | `:TOUCHED` from Step to Entity (no rank) |
| Provenance to source | none | `:EXTRACTED_FROM` + `:EXTRACTED_BY` |
| Vector index on trace | `query_embedding` on `:Query` (sibling) | `trace_embedding` on `:ReasoningTrace` itself |
| Outcome auditability | `:Answer` node | `TraceOutcome` audit nodes (v0.2) |
| Buffered writes | no — per-tool sync writes | `client.buffered.submit + flush` |
| Entity dedup | no | `consolidation.dedupe_entities` |

**Gaps in QKG:** missing `ReasoningStep`, missing `:TOUCHED`, missing `trace_embedding` (we put it on `:Query`), missing buffered writes.
**Strengths in QKG worth keeping:** `:RETRIEVED {tool, rank, turn}` is *more* specific than `:TOUCHED` for citation use cases — keep it as an edge type, ideally promote to `(:Step)-[:RETRIEVED]->(:Verse)`.

### 3. Building GraphRAG Python MCP tools (GraphAcademy)
URL: https://graphacademy.neo4j.com/courses/genai-mcp-build-custom-tools-python/

**Summary.** 2 modules. Module 02 lessons of interest: "Connecting to Neo4j", "Build a GraphRAG Tool", "Handling Large Datasets with Pagination". Landing page is thin; lesson bodies are gated.

**QKG relevance.** Pagination lesson is directly relevant — our `search_keyword`, `semantic_search`, and `concept_search` all hard-cap at 10–25 results with no cursor.

**Concrete patterns (from MCP docs + the contrib repo).** MCP tools should:
- declare `inputSchema` JSON-Schema with `query` + `params`;
- return JSON-serialized arrays;
- enforce a response-size limit (`NEO4J_RESPONSE_TOKEN_LIMIT`) to avoid blowing the model context.

**Action.** Add pagination cursors to the 8 search tools; expose response-token cap.

### 4. Using the Neo4j MCP Tools (GraphAcademy)
URL: https://graphacademy.neo4j.com/courses/genai-mcp-neo4j-tools/

**Summary.** The official `mcp-neo4j-cypher` server exposes only **3 tools**: `get_neo4j_schema`, `read_neo4j_cypher`, `write_neo4j_cypher`. There is also `mcp-neo4j-memory` (a separate server) with 9 memory tools: `read_graph`, `search_nodes`, `find_nodes`, `create_entities`, `delete_entities`, `create_relations`, `delete_relations`, `add_observations`, `delete_observations`. And `mcp-neo4j-aura-manager`, `mcp-neo4j-data-modeling`, `mcp-neo4j-gds`.

**Read-only enforcement.** `--read-only` CLI flag or `NEO4J_READ_ONLY=true` env var disables `write_neo4j_cypher` entirely. **No allowlist/denylist of Cypher fragments** — they trust the read/write split. Our `run_cypher` denylist (DELETE/MERGE/etc.) is *stricter* than theirs and worth keeping.

**QKG relevance.** Two architectural choices to make:
1. **Build our own MCP server** wrapping our 21 tools — this lets Claude Desktop, Cursor, etc. use QKG's domain-specific retrieval directly. Recommended.
2. **Adopt `mcp-neo4j-cypher` for the `run_cypher` tool**, keep our own dispatcher for the other 20.

### 5. Aura Agents (GraphAcademy + docs)
URLs: https://graphacademy.neo4j.com/courses/aura-agents/ · https://neo4j.com/docs/aura/aura-agent/ · https://neo4j.com/blog/genai/build-context-aware-graphrag-agent/

**Summary.** Hosted no-code/low-code agent platform on AuraDB. Three tool types only: **Cypher Template** (parameterised query), **Similarity Search** (vector index), **Text2Cypher** (NL→Cypher via fine-tuned model). Read-only. Agents publish as REST endpoints + MCP servers. Region-locked to GCP `europe-west1`. First-500 users get $100 Aura credit.

**Verdict on QKG migration:** **NO.** Aura Agents cannot run our Anthropic tool-use loop with custom Python. Our citation-validation step, our wujuh / morphological-pattern / code19 tools, and our `recall_similar_query` cannot be expressed as Cypher Templates without losing logic.

**However — it can be a sub-tool.** Wrap an Aura Agent as one of our 21 tools (or as the 22nd "text2cypher_fallback" tool) and call it when our planner's confidence is low.

**Pricing.** Internal agents free; external (deployed) charged per call. Region constraint matters for latency.

### 6. LLM Knowledge Graph Construction (GraphAcademy)
URL: https://graphacademy.neo4j.com/courses/llm-knowledge-graph-construction/

**Summary.** 3 modules / 10 lessons. Centred on the **Neo4j LLM Graph Builder** (web tool + Python lib). Schema is configurable: pass an allowlist of node labels and relationship types; the LLM is constrained to that schema.

**QKG relevance.** Low-medium. Our extraction is rule-based (Porter stems, Arabic roots, Quran-specific concepts). Hybrid path: keep deterministic Quran-specific extraction; layer LLM Graph Builder for English translation entities (people, places, events) where rule-based is weaker — POLE+O fits naturally.

### 7. Recent Neo4j developer blog posts (Apr 2026)

| Post | Date | Relevance to QKG |
|---|---|---|
| [Introducing Create Context Graph](https://neo4j.com/blog/genai/introducing-create-context-graph/) | recent | Scaffolding tool that generates the agent-memory schema + 8 framework integrations. Worth running once to compare scaffold to ours. |
| [Introducing Neo4j Agent Skills](https://neo4j.com/blog/developer/introducing-neo4j-agent-skills/) | Apr 2026 | "Skills" are progressive-disclosure SKILL.md docs (à la Anthropic skills). Install via `npx skills add neo4j-contrib/neo4j-skills`. Worth installing in our claude-code session. |
| [Building Stateful AI: Aura Agent + MCP + Persistent Memory](https://neo4j.com/blog/genai/building-stateful-ai-integrating-aura-agent-lifecycle-with-mcp-and-persistent-memory/) | Apr 2026 | **Most relevant.** Memory exposed as a markdown-filesystem (`Page` nodes + `LINKS_TO`). 8 MCP tools: `write/read/append/rename/delete/list/search/find_backlinks_memory`. Suggests `databases/<dbid>.md`, `agents/<id>.md`, `learnings/<topic>.md` page taxonomy. Useful as a *learnings* layer above our trace store. |
| [Multi-Agent Memory with Neo4j](https://medium.com/neo4j/when-your-agents-share-a-brain-...) | Apr 2026 | All agents share one graph via `context_graph_tools()`. 4 shared tools: `search_context, get_entity_graph, add_memory, get_user_preferences`. Provenance via `(decision)-[:MENTIONS]->(entity)<-[:MENTIONS]-(earlier_finding)`. Confirms `:MENTIONS` is the canonical "this message touched this entity" edge. |
| [Microsoft Agent Framework + Neo4j](https://medium.com/neo4j/building-an-ai-agent-with-memory-microsoft-agent-framework-neo4j-...) | Apr 2026 | Reference impl using Microsoft AF + agent-memory. Shows the same Conversation/Message/Trace schema applied. |

---

## Answers to specific questions

**1. Reasoning trace schema (Context Graphs course / agent-memory).**
Canonical: `(:Conversation)-[:CONTAINS]->(:Message)`, `(:Message)-[:TRIGGERED]->(:ReasoningTrace)`, `(:ReasoningTrace)<-[:PART_OF]-(:ReasoningStep)`, `(:ReasoningTrace)-[:CALLED_TOOL]->(:ToolCall)`, `(:ReasoningStep)-[:TOUCHED]->(:Entity)`, `(:Entity)-[:EXTRACTED_FROM]->(:Message)`, `(:Entity)-[:EXTRACTED_BY]->(:Extractor)`. Vector indexes on `message_embedding`, `entity_embedding`, `trace_embedding`. **QKG drift from canonical:** we collapse `ReasoningStep` into `ToolCall`, we put the embedding on `Query` not `ReasoningTrace`, we have no `Extractor` provenance. **Drop nothing — we're a strict subset.**

**2. MCP tool design (mcp-neo4j-cypher).** The official server is intentionally tiny (3 tools). It does *not* validate the answer is a strict subset; it recommends domain-specific tools "where they exist" and the Cypher tool as fallback. Our 21-tool decomposition is *exactly* the recommended pattern; we should expose them via MCP so Claude Desktop / Cursor can use them too. Return shape recommendation: JSON-serialized list of records, with `NEO4J_RESPONSE_TOKEN_LIMIT` enforced. Error handling: raise structured errors so the LLM can re-plan; don't silently return `[]`. We currently return `[]` on miss in several tools — should switch to `{status: "no_results", hint: "..."}`.

**3. Cross-tool memory recall.** The canonical recipe (multi-agent post) is: vector search on `trace_embedding` for similar past task, then 1-hop expansion to `(:ToolCall)` and 2-hop to `(:Entity)` to recover the *playbook* (which tools fired, in what order, and what they returned). We do step 1 only (`tool_recall_similar_query` returns past `Query` text + answer). **Better pattern:** when we hit a recall, also return the full `[(ToolCall.tool_name, ToolCall.arguments)]` sequence so the planner can replay/skip.

**4. Aura Agents.** No, we cannot deploy `chat.py` to Aura. The platform offers only Cypher Template + Similarity Search + Text2Cypher tools, read-only, no custom Python. We *can* deploy a parallel Aura Agent fed by Cypher Templates over the same DB and call it as a sub-tool from our planner.

**5. Tool-call cache.** No reference impl uses a graph-native TTL cache. They use buffered writes + entity dedup instead. Our 30s `_TOOL_CACHE` is the right pattern for in-process. **Only promote to a `(:ToolCallCache)` node if** we move to multi-process (gunicorn workers, Lambda, etc.). At that point: `MERGE (c:ToolCallCache {key: $key}) ON CREATE SET c.result = $result, c.expires_at = datetime() + duration({seconds:30})`.

**6. KG construction.** Pipeline `agent-memory` advertises: `spaCy → GLiNER → LLM → GLiREL`. Use spaCy/GLiNER for cheap extraction, fall back to an LLM only on novel entities, then run GLiREL for relationship typing. Hybrid recommendation for QKG: keep our deterministic root/concept/keyword pipeline as the primary; layer GLiNER on top of English translations for POLE+O entities (extracts "Mecca", "Pharaoh", "Battle of Badr" etc.); store under `(:Entity:Location)`, `(:Entity:Person)`, etc., aliased to existing nodes via `(:Entity)-[:ALIAS_OF]->(:Concept)`.

---

## Recommended `ralph_backlog` tasks

```yaml
- id: from_neo4j_crawl_reasoning_step
  type: schema-migration
  priority: high
  description: |
    Insert `:ReasoningStep` between `:ReasoningTrace` and `:ToolCall`.
    Migrate existing 32K `:RETRIEVED` edges so they originate from
    `:ReasoningStep` instead of `:ReasoningTrace`. Add `thought`,
    `action`, `observation` properties. Schema becomes:
      (:ReasoningTrace)<-[:PART_OF]-(:ReasoningStep)
      (:ReasoningStep)-[:CALLED_TOOL]->(:ToolCall)
      (:ReasoningStep)-[:RETRIEVED {rank, turn}]->(:Verse)
  acceptance:
    - 100% of past traces backfilled with synthetic ReasoningStep nodes
    - new reasoning_memory.write_step() API used by chat.py loop
    - audit query `MATCH (t:ReasoningTrace)<-[:PART_OF]-(s:ReasoningStep)-[:CALLED_TOOL]->(tc) RETURN ...` returns >=1 row per past trace

- id: from_neo4j_crawl_trace_vector_index
  type: schema-migration
  priority: high
  description: |
    Move trace embedding from `(:Query.query_embedding)` to
    `(:ReasoningTrace.trace_embedding)`. Build vector index
    `trace_embedding` (cosine). Update `tool_recall_similar_query` to
    query the new index AND return the full ToolCall sequence
    (playbook), not just the past answer text.
  acceptance:
    - vector index exists and is online
    - tool_recall_similar_query returns {past_query, past_answer, tool_sequence: [{tool_name, arguments}, ...]}
    - chat.py planner receives playbook and can skip already-explored tools

- id: from_neo4j_crawl_touched_edge
  type: schema-extension
  priority: medium
  description: |
    Add `:TOUCHED` edges from `:ReasoningStep` to every concept/root/word
    the step examined, even if the step did not formally retrieve them.
    Distinguishes "I looked at this" from "I cited this" (the latter
    stays on :RETRIEVED). Improves wujuh / root-family audit queries.
  acceptance:
    - new edge type populated for at least search_keyword, concept_search, search_arabic_root tools
    - audit query returns broader entity graph than RETRIEVED-only

- id: from_neo4j_crawl_pagination_cursors
  type: tool-extension
  priority: medium
  description: |
    Add cursor-based pagination to the 8 search/retrieval tools
    (search_keyword, semantic_search, traverse_topic, hybrid_search,
    concept_search, find_path, explore_surah, lookup_wujuh).
    Tool input gets optional `cursor: str`, response includes
    `next_cursor` when more results exist. Cap response token size
    via env var QKG_RESPONSE_TOKEN_LIMIT (default 8000).
  acceptance:
    - chat.py planner can request page 2 of any search tool
    - long-tail surahs (Baqarah, Tawbah) no longer truncate at 25 hits

- id: from_neo4j_crawl_mcp_server
  type: feature
  priority: medium
  description: |
    Wrap the 21 chat.py tools as a stdio MCP server so they can be
    used from Claude Desktop, Cursor, Codex, etc. Reuse the existing
    tool dispatcher; expose `get_qkg_schema` that summarises the
    Verse/Word/Root/Concept node taxonomy. Read-only by default.
  acceptance:
    - `mcp-qkg` package installable
    - `claude_desktop_config.json` recipe in README
    - all 21 tools callable via MCP with same JSON schemas as Anthropic tool_use

- id: from_neo4j_crawl_buffered_writes
  type: performance
  priority: low
  description: |
    Replace per-tool synchronous writes in reasoning_memory.py with
    a buffered queue flushed at end of turn (or every N writes).
    Reduces 21x driver round-trips per chat turn to 1-3.
  acceptance:
    - measured p95 chat-turn latency drops by >=200ms
    - no traces lost on process kill (graceful flush hook)

- id: from_neo4j_crawl_extractor_provenance
  type: schema-extension
  priority: low
  description: |
    Add `(:Extractor {name, version, config})` nodes for our keyword
    extractor, Porter-stem ER, Arabic-root extractor, and the LLM
    embedding generator. Link via `:EXTRACTED_BY` from concepts/roots.
    Enables "which extractor produced this concept?" audit queries.
  acceptance:
    - 4 :Extractor nodes seeded
    - concepts created after migration carry :EXTRACTED_BY edges

- id: from_neo4j_crawl_aura_text2cypher_fallback
  type: feature
  priority: low
  description: |
    Stand up a parallel Aura Agent on the same QKG database with
    Text2Cypher enabled (+ ~10 Cypher Templates for our most-common
    queries). Wrap as a 22nd tool `text2cypher_fallback` invoked when
    the planner's confidence on existing tools is low.
  acceptance:
    - Aura Agent deployed in europe-west1
    - tool callable from chat.py loop via REST
    - logged as :ToolCall like any other tool

- id: from_neo4j_crawl_neo4j_skills
  type: tooling
  priority: low
  description: |
    Install neo4j-contrib/neo4j-skills via `npx skills add ...` so
    that this Claude Code workspace gets progressive-disclosure
    SKILL.md docs for Cypher patterns, Python driver, and AI/search.
  acceptance:
    - skill files present under .claude/skills/
    - test prompt "write a Cypher query that returns the longest verse" triggers the cypher skill
```

---

## New research threads

1. **Test-drive `neo4j-labs/agent-memory` against our 2,662 existing traces.** Run `client.schema.adopt_existing_graph(...)` and see how much migration it does for free vs. how much we'd need to write. If adoption is clean, consider swapping `reasoning_memory.py` wholesale.
2. **`Page`-as-memory pattern** from the Stateful AI blog. Should QKG store *learned* knowledge (e.g., "Surah 9 has unusual basmala absence") as `(:Page {path: 'learnings/surah-9-basmala.md', content: ...})`? Could become the agent's growing playbook.
3. **GLiNER + GLiREL feasibility on Quran translations.** Run a 50-surah pilot to estimate POLE+O entity coverage and dedup quality before any schema change.
4. **MCP server for QKG: stdio vs HTTP transport.** stdio is simpler for Claude Desktop; HTTP enables remote access. Decide based on whether we want public read-only access.
5. **Aura Agent cost model under our query mix.** External agent call price × ~3 calls/chat × expected QPS — does Text2Cypher fallback pay for itself?
6. **Neo4j Agent Skills install + behavior in Claude Code.** Does installing `neo4j-skills` overlap or conflict with our existing `claude-api` skill? Worth a 30-min spike.
7. **`TraceOutcome` pattern** — agent-memory v0.2 introduces it for "indexable audit queries" but the docs are thin. Find a worked example (probably in the Context Graphs course module 4 lessons we couldn't fetch).
8. **Multi-agent shared graph** — if we ever add a separate "verse explainer" agent or "etymology agent" alongside chat.py, the canonical pattern is `context_graph_tools()` returning the same 4-tool set. Worth a design note now.

---

## Sources

- [Context Graphs: Agent Memory with Neo4j (course)](https://graphacademy.neo4j.com/courses/genai-context-graphs/)
- [Building GraphRAG Python MCP tools (course)](https://graphacademy.neo4j.com/courses/genai-mcp-build-custom-tools-python/)
- [Using the Neo4j MCP Tools (course)](https://graphacademy.neo4j.com/courses/genai-mcp-neo4j-tools/)
- [Building Agents in Neo4j Aura (course)](https://graphacademy.neo4j.com/courses/aura-agents/)
- [LLM Knowledge Graph Construction (course)](https://graphacademy.neo4j.com/courses/llm-knowledge-graph-construction/)
- [neo4j-labs/agent-memory (GitHub)](https://github.com/neo4j-labs/agent-memory)
- [neo4j-labs/agent-memory (DeepWiki)](https://deepwiki.com/neo4j-labs/agent-memory)
- [neo4j-labs/create-context-graph (GitHub)](https://github.com/neo4j-labs/create-context-graph)
- [neo4j-contrib/mcp-neo4j-cypher (GitHub)](https://github.com/neo4j-contrib/mcp-neo4j/tree/main/servers/mcp-neo4j-cypher)
- [Aura Agent docs](https://neo4j.com/docs/aura/aura-agent/)
- [Neo4j MCP integrations guide](https://neo4j.com/developer/genai-ecosystem/model-context-protocol-mcp/)
- [From recall to reasoning: how context graphs upgrade an agent's brain (blog)](https://neo4j.com/blog/genai/from-recall-to-reasoning-how-context-graphs-upgrade-an-agents-brain/)
- [Meet Lenny's Memory: Building Context Graphs (blog)](https://neo4j.com/blog/developer/meet-lennys-memory-building-context-graphs-for-ai-agents/)
- [Building Stateful AI: Aura Agent + MCP + Persistent Memory (blog)](https://neo4j.com/blog/genai/building-stateful-ai-integrating-aura-agent-lifecycle-with-mcp-and-persistent-memory/)
- [Introducing Neo4j Agent Skills (blog)](https://neo4j.com/blog/developer/introducing-neo4j-agent-skills/)
- [When Your Agents Share a Brain: Multi-Agent Memory with Neo4j (Medium)](https://medium.com/neo4j/when-your-agents-share-a-brain-building-multi-agent-memory-with-neo4j-bac609f17b23)
- [Building an AI Agent with Memory: MS Agent Framework + Neo4j (Medium)](https://medium.com/neo4j/building-an-ai-agent-with-memory-microsoft-agent-framework-neo4j-e3eab8f09694)
- [Aura Agent: Create your own GraphRAG agent in minutes (blog)](https://neo4j.com/blog/genai/build-context-aware-graphrag-agent/)
