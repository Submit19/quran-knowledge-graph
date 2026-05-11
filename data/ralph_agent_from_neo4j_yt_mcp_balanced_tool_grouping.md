# Balanced MCP Tool Grouping — Implementation Spec

**Task:** from_neo4j_yt_mcp_balanced_tool_grouping  
**Source:** NODES 2026 "Smarter MCP Servers" video + RETRIEVED edge analysis  
**Date:** 2026-05-12

---

## Problem

QKG currently exposes all 21 tools to the LLM in every chat turn. At ~200 tokens per tool description, this costs approximately **4,200 tokens** before the first message. The NODES 2026 video demonstrated a **62% reduction** in tool-related overhead by sending only 8 high-frequency tools at startup and making 3 discoverable category bundles available on demand.

Our reasoning_memory RETRIEVED edge data (from `data/ralph_analysis_analyze_retrieved_edges_top_per_tool.md` and `data/ralph_analysis_measure_per_tool_latency.md`) provides the empirical basis for ranking.

---

## Tool Usage Signal (from reasoning_memory.py)

Based on RETRIEVED edge counts and ToolCall frequency from Neo4j:

| Tool | n_calls | RETRIEVED hits | Notes |
|------|---------|----------------|-------|
| search_keyword | 2,332 | moderate | highest call frequency |
| semantic_search | 1,355 | high (2:177 × 9) | p95 latency 949ms — cold-start |
| get_verse | 613 | n/a | fast (p50 6ms) |
| traverse_topic | 673 | moderate | p95 1,998ms |
| explore_surah | 66 | low | fast (p50 5ms) |
| concept_search | 12 | low | underused but high-value |
| hybrid_search | ~unknown | n/a | newer, not in ToolCall yet |
| recall_similar_query | ~unknown | n/a | newer |
| run_cypher | ~unknown | n/a | escape hatch |

---

## Proposed Tool Groups

### Group A: Startup Set (8 tools — always sent)

Ranked by call frequency + answer-quality criticality:

1. `search_keyword` — highest call frequency (2,332 calls), BM25-style
2. `semantic_search` — second highest (1,355 calls), vector retrieval
3. `get_verse` — third highest (613 calls), fast lookup
4. `traverse_topic` — fourth (673 calls), graph hop, strong multi-hop
5. `hybrid_search` — strategic inclusion: BM25+BGE-M3+RRF, replaces the above two for most queries
6. `concept_search` — underused but synthesis + routing upgrade makes it critical for ABSTRACT queries
7. `recall_similar_query` — past-playbook injection; high ROI on repeated query themes
8. `run_cypher` — escape hatch; agents fall back here when other tools fail

**Token cost: ~1,600 tokens** (8 × 200t). Down from 4,200t.  
**Savings: ~2,600 tokens/turn.**

### Group B: Etymology & Morphology Bundle (6 tools — discoverable)

Trigger phrase for the LLM: "Use `request_tool_group('etymology')` to access Arabic root, morphology, and semantic domain tools."

Tools included:
- `search_arabic_root`
- `compare_arabic_usage`
- `lookup_word`
- `explore_root_family`
- `search_semantic_field`
- `lookup_wujuh`

### Group C: Surah-Level Bundle (3 tools — discoverable)

Trigger phrase: "Use `request_tool_group('surah')` to access surah-level and morphological pattern tools."

Tools included:
- `explore_surah`
- `search_morphological_pattern`
- `get_verse_words`

### Group D: Analysis Bundle (4 tools — discoverable)

Trigger phrase: "Use `request_tool_group('analysis')` to access typed-edge queries, Code-19, and extended verse tools."

Tools included:
- `query_typed_edges`
- `get_code19_features`
- `find_path`
- `get_verse_words` (shared with Group C — duplicate intentional)

---

## Implementation Plan

### Phase 1: Implement tool grouping in `chat.py` (1–2 hours)

**Step 1.1 — Define group constants near top of `chat.py`:**
```python
STARTUP_TOOLS = [
    "search_keyword", "semantic_search", "get_verse",
    "traverse_topic", "hybrid_search", "concept_search",
    "recall_similar_query", "run_cypher"
]

TOOL_GROUPS = {
    "etymology": ["search_arabic_root", "compare_arabic_usage", "lookup_word",
                  "explore_root_family", "search_semantic_field", "lookup_wujuh"],
    "surah":     ["explore_surah", "search_morphological_pattern", "get_verse_words"],
    "analysis":  ["query_typed_edges", "get_code19_features", "find_path", "get_verse_words"],
}
```

**Step 1.2 — Add `get_tools_for_request(requested_groups=None)` helper:**
```python
def get_tools_for_request(requested_groups: list[str] | None = None) -> list[dict]:
    """Return Anthropic tool-schema list for the startup set + any requested groups."""
    all_tools = build_all_tool_schemas()  # existing logic
    tool_map = {t["name"]: t for t in all_tools}
    
    active_names = list(STARTUP_TOOLS)
    for group in (requested_groups or []):
        active_names.extend(TOOL_GROUPS.get(group, []))
    
    return [tool_map[n] for n in dict.fromkeys(active_names) if n in tool_map]
```

**Step 1.3 — Add a meta-tool `request_tool_group` to the startup set:**
```python
{
    "name": "request_tool_group",
    "description": (
        "Request additional tool groups. Call this BEFORE using any tool in that group. "
        "Available groups: 'etymology' (Arabic root/morphology/semantic-domain tools), "
        "'surah' (surah-level + morphological pattern tools), "
        "'analysis' (typed-edge queries, Code-19, path-finding). "
        "When to use: when you need Arabic linguistic analysis, full surah inspection, "
        "or Code-19 arithmetic. "
        "When NOT to use: for ordinary verse lookup or keyword search — those are in the "
        "startup set. "
        "Output: confirmation string listing newly available tool names."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "groups": {
                "type": "array",
                "items": {"type": "string", "enum": ["etymology", "surah", "analysis"]},
                "description": "One or more group names to unlock."
            }
        },
        "required": ["groups"]
    }
}
```

**Step 1.4 — Handle `request_tool_group` in the dispatch loop (`app_free.py`):**

The agentic loop currently runs a fixed tool list per session. Change it to track a `session_active_groups` set and re-call `get_tools_for_request(session_active_groups)` after each `request_tool_group` tool call, then continue the loop with the expanded schema.

```python
# In the agentic loop (app_free.py, inside handle_chat_stream):
active_groups: set[str] = set()
tools = get_tools_for_request()

# Inside tool dispatch:
if tool_name == "request_tool_group":
    new_groups = tool_args.get("groups", [])
    active_groups.update(new_groups)
    tools = get_tools_for_request(list(active_groups))
    # Return confirmation to model:
    yield tool_result(tool_use_id, f"Unlocked groups: {new_groups}. New tools available: {[t['name'] for g in new_groups for t in TOOL_GROUPS.get(g, [])]}")
    continue  # re-enter loop with updated tools
```

### Phase 2: System prompt update (30 min)

Add a paragraph to the system prompt in `app_free.py`:

```
You have access to 8 core tools. For Arabic etymology, morphology, or semantic domains,
call request_tool_group(groups=["etymology"]) first. For full surah exploration or
morphological patterns, call request_tool_group(groups=["surah"]).
For typed-edge queries, Code-19 features, or path-finding, call
request_tool_group(groups=["analysis"]).
```

### Phase 3: RETRIEVED-edge-based startup set refresh (ongoing — cron task)

Add to `scripts/tick_finalize.py`:
```python
# Every 24 ticks: re-query Neo4j for top-8 tools by RETRIEVED edge count.
# If the ranking has shifted (any tool not in current STARTUP_TOOLS appears in top 8),
# log to data/tool_ranking_drift.md for operator review.
```

---

## Token Savings Estimate

| Scenario | Tools sent | ~Tokens |
|---|---|---|
| Current (all 21) | 21 | 4,200 |
| Startup only (no groups requested) | 9 (8 + meta-tool) | 1,800 |
| Startup + etymology | 15 | 3,000 |
| Startup + all groups | 22 | 4,400 |

**Typical chat (no etymology):** 4,200 → 1,800 = **−2,400 tokens/turn**.  
At 1,500 chat queries in answer_cache, compounded savings over seeding runs: ~3.6M tokens.

---

## Risk Register

| Risk | Severity | Mitigation |
|------|----------|------------|
| Model forgets to call request_tool_group before using an unavailable tool | Medium | Return structured error: `{error: "tool_not_loaded", available_groups: [...]}` from dispatch |
| RETRIEVED-edge data is sparse for newer tools (hybrid_search, recall_similar_query) | Low | Startup set hard-codes strategic picks; data-driven re-ranking is Phase 3 |
| System prompt instruction adds ~50 tokens (partially offsets savings) | Low | Net still −2,350 tokens |
| `request_tool_group` adds one round-trip per group needed | Low | Typography/thematic queries rarely need etymology; most queries resolve in startup set |

---

## Decision Gate

Before merging to `app_free.py`:
1. Run `eval_v1.py` baseline — confirm avg_unique_cites_per_q does not regress >2%.
2. Spot-check 3 Arabic-root queries manually (those are the most likely to be mis-routed).
3. Confirm the meta-tool shows up correctly in the SSE `tool` event stream.

---

## Files Changed

- `chat.py` — add `STARTUP_TOOLS`, `TOOL_GROUPS`, `get_tools_for_request()`, `request_tool_group` schema
- `app_free.py` — track `active_groups` per session, dispatch `request_tool_group` in tool loop
- `app_free.py` system prompt — add group-unlock instructions

**Estimated effort:** 2–3 hours for Phase 1 + 2. Phase 3 is a cron hook (30 min).
