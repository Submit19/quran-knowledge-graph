---
type: architecture
subsystem: agent-loop
status: current
date_added: 2026-05-10
---

# Agent Loop

## What it does

An LLM drives graph exploration via 21 named tools over up to 15 turns. The model decides which tools to call based on the question, accumulates context across turns, and produces a grounded answer with Quranic verse citations.

## Where it lives

- `chat.py` — all 21 tool function bodies (Cypher queries) + `dispatch_tool()` + tool-call cache + `TOOLS` schema list
- `app_free.py` — loop orchestrator; bridges sync tool execution to async SSE via `queue.SimpleQueue` + daemon thread
- `prompts/system_prompt_free.txt` — lean system prompt for local models

## Tool taxonomy (21 tools)

**Search / retrieval (8)**

| Tool | What it does |
|------|-------------|
| `search_keyword` | All verses mentioning a keyword, grouped by surah; Porter-stem normalized |
| `semantic_search` | Vector search via active index (`verse_embedding_m3` by default) |
| `traverse_topic` | Multi-keyword search + 1-2 hop RELATED_TO graph walk |
| `hybrid_search` | BM25 (fulltext) + BGE-M3 dense → RRF k=60 fusion |
| `concept_search` | Expands query through NORMALIZES_TO canonical form before searching |
| `find_path` | Shortest thematic path between two verse IDs |
| `explore_surah` | All verses in a surah + cross-surah connections |
| `recall_similar_query` | Vector lookup over `query_embedding` index — returns past tool steps as a playbook |

**Verse-level (3)**

| Tool | What it does |
|------|-------------|
| `get_verse` | Full verse + keywords + RELATED_TO neighbors + Arabic roots + typed edges |
| `get_verse_words` | Word-by-word breakdown (WordToken → Lemma → ArabicRoot → MorphPattern) |
| `query_typed_edges` | SUPPORTS / ELABORATES / QUALIFIES / CONTRASTS / REPEATS edges for a verse |

**Etymology / morphology (7)**

| Tool | What it does |
|------|-------------|
| `search_arabic_root` | All verses mentioning a tri-literal root via MENTIONS_ROOT |
| `compare_arabic_usage` | Compare two roots across shared verses |
| `lookup_word` | Arabic word → root, lemma, pattern, occurrences |
| `explore_root_family` | Full derivative tree of a root (lemmas grouped by wazn) |
| `search_semantic_field` | All roots/lemmas in a SemanticDomain |
| `lookup_wujuh` | Polysemy data — all senses of a root/lemma |
| `search_morphological_pattern` | Find all words following a wazn pattern |

**Code-19 + escape hatch (2)**

| Tool | What it does |
|------|-------------|
| `get_code19_features` | Verse/Sura arithmetic Code-19 properties |
| `run_cypher` | Read-only raw Cypher (denylist-guarded against write operations) |

## Anthropic SDK tool-use protocol

Tools are defined as JSON schemas in `chat.py`'s `TOOLS` list. The agent loop sends `messages + tools` to the Anthropic API; tool calls come back as `tool_use` content blocks. `dispatch_tool()` maps `tool_name → function`, executes against a live Neo4j session, optionally passes the result through `retrieval_gate.gate_tool_result()`, then appends a `tool_result` message and continues.

## Tool-call cache

`TOOL_CACHE_TTL_SEC=30` (default). A dict keyed by `(tool_name, json(args))` with TTL eviction. Cold semantic_search is 18.8s; a cache hit is 0ms — 18,785× speedup on repeated calls within the same session. Max 256 entries (FIFO). Override with `TOOL_CACHE_MAX` / `TOOL_CACHE_TTL_SEC=0` to disable.

## Turn cap

`MAX_TOOL_TURNS=15` (default in `chat.py`; `app_free.py` uses 8 for local models). If the model hasn't stopped calling tools at the cap, the loop forces final-answer generation.

## Cross-references
- [[overview]] — request flow context
- [[retrieval-pipeline]] — gate applied inside `dispatch_tool()`
- [[reasoning-memory]] — each tool call is logged post-execution
- [[graph-schema]] — node/index definitions the tools query
- Source: `repo://chat.py`, `repo://app_free.py`, `repo://CLAUDE.md` (Key Subsystems section)
