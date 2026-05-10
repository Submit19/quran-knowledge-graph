# 06c — Neo4j YT: MCP Servers, Aura Agent & RAG Benchmarks

_Sources: sBf8TJgqdwY · sZRA4j3d0c8 · 3wwFWG03kfk · ma8KXJRLhyg_
_Extracted 2026-05-10 by ralph research subagent_

## TL;DR

- **Context window bloat is the #1 MCP deployment hazard**: each tool definition costs ~200 tokens at startup; 21 tools ≈ 4,200 tokens burned before the first user message. The graph-backed tool-registry pattern (video 3) is the strongest mitigation.
- **Lazy loading of tools is unreliable with public MCP servers**; only viable when you own the agent (which QKG's `chat.py` is). For QKG's MCP wrapper the graph-backed balanced approach (8 hot tools up front + discoverable remainder) is the recommended design.
- **Aura Agent is a managed, low-code, locked-vendor alternative** to our hand-rolled `chat.py`. It gives text-to-Cypher, similarity search, and Cypher templates out of the box, but uses Gemini 2.5 Flash and only OpenAI/Google embeddings — a poor fit for our BGE-M3 stack. Worth monitoring but not worth migrating.
- **The VectorRAG vs GraphRAG benchmark (video 4) uses RAGAS metrics, not MAP@K**. No MAP@10 numbers are stated. GraphRAG strategies consistently beat VectorRAG on multi-hop and aggregation queries; the gap is most visible with text-to-Cypher. Numbers provided are qualitative/ordinal, not numeric MAPs.
- **Tool descriptions are load-bearing**: natural-language quality of tool name + description determines whether the model calls the right tool. Our 21 tools need audited descriptions before MCP wrapping.

---

## Video 1 — sBf8TJgqdwY: Fastest Path to an Agent for Your Knowledge Graph (29 min)

**Core finding:** MCP spec guarantees `tools/list` fires at client startup — this is unavoidable. The official Neo4j MCP server (beta 3, written in Go) exposes exactly three tools: `get_schema`, `execute_read_cypher`, `execute_write_cypher`. That minimal surface is deliberate.

**[08:55–09:10]** Tool definitions + tool results both go into context; together they are the main driver of context overflow. This is called "context engineering" now.

**[19:35–19:55]** Natural-language quality of tool descriptions is critical: "the model chooses to invoke the tool based on how we've described it." Poor descriptions → wrong tool selection even with a strong model.

**[26:05–26:12]** Claude Sonnet 4.5 is the clear benchmark winner on ContextBench (multi-hop tool chaining). Consistent with QKG's choice of Sonnet as the default model.

**[28:10–28:50]** Two token-reduction strategies are named:
1. Cloudflare "code mode": converts MCP tool schemas to a TypeScript API, runs the agent as code in a sandbox. Avoids JSON tool-calling tokens.
2. Anthropic blog (cited as "a couple days ago"): same observation — direct JSON tool-calling burns tokens; code-against-tools scales better.

**[27:35–27:55]** Authorization is unsolved in MCP. Docker horror-stories blog cited. Neo4j official server is "supported"; Labs servers are "experimental." For QKG the distinction matters if we ever host publicly.

**QKG relevance:** Our 21 tools are well above the 3-tool official server. Before MCP wrapping, audit which tools are genuinely distinct vs. overlapping; consider merging `search_arabic_root` + `explore_root_family` + `compare_arabic_usage` into fewer, richer tools.

---

## Video 2 — sZRA4j3d0c8: Build Reliable AI Faster with Aura Agent & MCP Server (32 min)

**Aura Agent capabilities (EAP/preview as of video date):**

| Feature | Detail |
|---|---|
| Tool types | Similarity search (vector), text-to-Cypher (fine-tuned Gemini), Cypher templates (parameterized) |
| LLM | Gemini 2.5 Flash (hosted, no bring-your-own model yet) |
| Embeddings | OpenAI `text-embedding-ada-002` or Google Gemini only |
| Deployment | REST API with client secret/token auth via Aura API |
| MCP support | Not built-in yet; demo shows wrapping the REST endpoint manually as an MCP server `[25:40–26:05]` |

**[13:45–14:10]** Aura Agent = end-to-end low-code platform: build → test playground → deploy as endpoint, all in minutes. Infrastructure (agent loop, embedding calls, schema access) is fully managed.

**[20:20–20:55]** Cypher templates are parameterized queries stored in the agent config — equivalent to our `run_cypher` tool but declarative/pre-approved rather than free-form. Reduces hallucination risk on aggregation queries.

**[26:45–27:15]** Multi-agent demo: Aura Agent endpoint called as a tool from Claude Desktop via a custom MCP wrapper. Shows the Aura agent is itself a callable sub-agent within a larger orchestration.

**What QKG would gain from Aura Agent:** zero infrastructure for graph retrieval, built-in playground, managed auth.

**What QKG would lose:** BGE-M3 embeddings, our multilingual reranker, custom tool logic (Arabic root traversal, Code-19 features, wujuh lookup, `run_cypher` escape hatch). The entire etymology/morphology layer has no equivalent in Aura Agent. **Verdict: not a migration target.** Useful reference for Cypher-template tool design.

---

## Video 3 — 3wwFWG03kfk: Smarter MCP Servers — Using a Graph to Solve the Context Window Problem (28 min)

**This is the most directly actionable video for QKG's MCP backlog item.**

**[03:55–04:04]** Rule of thumb: **~200 tokens per tool definition** at startup. 21 QKG tools ≈ 4,200 tokens consumed before any query.

**[04:15–04:30]** Example: 60-tool MCP server (REST API surface) → ~12,000 tokens startup cost.

**[19:05–20:28]** Worked example with the 26-endpoint Aura API: full list = ~5,000 tokens; graph-backed approach (8 common + 2 discovery tools) = ~2,000 tokens → **62% reduction**.

### Three patterns (explicit trade-off table)

| Pattern | Startup tokens | Reliability | Adapts over time | Works w/ any client |
|---|---|---|---|---|
| Full list | High | ✓ (spec-guaranteed) | ✗ | ✓ |
| Lazy loading | Very low | ✗ (model must ask) | ✗ | ✗ |
| Graph-backed balanced | Medium | ✓ | ✓ | ✓ |

**[15:00–16:35]** Graph-backed approach in detail: store tools as nodes in Neo4j with category edges and a `usage_count` property. On startup, Cypher query returns top-N by usage + a `discover_tools(category)` meta-tool. Every invocation increments usage → list self-optimizes.

**[24:00–24:45]** Claude explicitly told the presenter it "cannot be compelled" — it cooperates voluntarily. Using the word "mandatory" in a tool description does not force invocation. Implication: tool description framing matters more than instruction imperatives. Naming a discovery meta-tool something like `explore_available_tools` makes it more likely to be chosen.

**[26:50–27:05]** Tool sequencing can be encoded in the graph: record which tools are called in sequence (tool A → tool B), then surface that in descriptions. Direct analogue to QKG's `RETRIEVED` edges in `reasoning_memory.py`.

**QKG MCP design recommendation:**
- Startup set (8–10 tools): `semantic_search`, `hybrid_search`, `get_verse`, `get_verse_words`, `search_arabic_root`, `lookup_word`, `explore_surah`, `search_keyword`, + `discover_qkg_tools` meta-tool.
- Discoverable by category: etymology (`lookup_wujuh`, `explore_root_family`, `compare_arabic_usage`, `search_semantic_field`, `search_morphological_pattern`), graph traversal (`traverse_topic`, `find_path`, `query_typed_edges`), advanced (`concept_search`, `recall_similar_query`, `get_code19_features`, `run_cypher`).
- Use `reasoning_memory.py` RETRIEVED edge counts as the usage signal — already collected.

---

## Video 4 — ma8KXJRLhyg: NODES 2024 — Measuring VectorRAG vs GraphRAG (23 min)

**Benchmark methodology:**

- Framework: **RAGAS** (not MAP@K). Metrics: context relevancy, context precision, context recall (retrieval); answer relevancy, faithfulness (generation).
- Datasets: Movies (~100 Q&A) and Products (~250 Q&A), custom-built with 4 complexity levels (1=property lookup, 4=multi-hop aggregation).
- Strategies tested: VectorRAG, Augmented Vector Search (vector seed + Cypher traversal), Text-to-Cypher.
- **No MAP@10 numbers are stated anywhere in this video.** Results are ordinal/relative rankings, not absolute scores.

**Key numeric finding:** No absolute scores are shown on slides visible in the transcript. Relative findings only:

- GraphRAG strategies (both) > VectorRAG on retrieval recall and most generation metrics across both datasets.
- Text-to-Cypher > Augmented Vector Search on consistency; exception: faithfulness (where AugVS wins, attributed to Cypher query noise in the context).
- VectorRAG wins context precision (returns fewer items, so precision trivially higher).
- VectorRAG competitive on the Products dataset because it is simpler (complexity ~1.6 vs Movies being higher).

**[20:45–21:15]** Explicit failure case for VectorRAG: "find genres with most movies" (aggregation over neighbor nodes) — VectorRAG returns nothing useful, AugVS partially hallucinates counts, Text-to-Cypher answers correctly.

**Applicability to QKG's QRCD gap (MAP@10 = 0.139 vs 0.36 lit):**

The RAGAS framework used here is **not** the same evaluation as QRCD MAP@10, so these numbers cannot be directly compared. However, the failure modes are consistent: our QRCD gap is largest on multi-hop Arabic questions (confirmed in `eval_ablation_retrieval.py`). The video's data suggests text-to-Cypher would help for aggregation/traversal questions. Our `run_cypher` tool is the closest equivalent but is opt-in and model-directed, not the primary retrieval path.

**[21:45–22:10]** Future work stated: use larger, well-known public benchmarks (rather than custom Q&A sets) and test more domains. QRCD is exactly the kind of established benchmark they're pointing toward — QKG is ahead of the video on this front.

---

## Cross-Cutting Patterns

1. **Tool descriptions are the interface, not the code.** Three videos independently emphasize that natural-language quality of tool descriptions determines routing. QKG's 21 tools were written for Python docstrings, not LLM consumption. A description audit pass is needed before MCP wrapping.

2. **Graph as a first-class MCP meta-layer.** Video 3 proposes storing the tool registry *in the graph itself*. QKG already stores tool usage in `reasoning_memory.py` via RETRIEVED edges — this is the exact signal needed to implement the graph-backed balanced pattern with zero new infrastructure.

3. **Text-to-Cypher bridges the GraphRAG gap.** Video 4 shows Text-to-Cypher is the most consistent retriever for complex queries. QKG's `run_cypher` provides this as an escape hatch but it is not promoted as a primary path in the system prompt.

4. **Aura Agent ≠ migration target for QKG.** Vendor lock-in on Gemini + no BGE-M3 support rules it out. Worth revisiting if they add bring-your-own embedding models.

---

## Proposed Backlog Tasks

```yaml
- id: from_neo4j_yt_mcp_tool_description_audit
  priority: 62
  title: "Audit and rewrite all 21 tool descriptions for LLM routing clarity"
  rationale: "Videos 1 & 3: natural-language quality of descriptions is the primary tool-selection signal; QKG descriptions were written as Python docstrings"
  effort: S

- id: from_neo4j_yt_mcp_graph_backed_registry
  priority: 63
  title: "Implement graph-backed tool registry using existing RETRIEVED edge counts"
  rationale: "Video 3: use usage_count from reasoning_memory.py RETRIEVED edges to rank tools in startup list; already have the data"
  effort: M

- id: from_neo4j_yt_mcp_balanced_tool_grouping
  priority: 64
  title: "Define MCP tool groups: 8-tool startup set + 3 discoverable categories"
  rationale: "Video 3: 62% token reduction with graph-backed balanced approach; startup set should be the 8 most-used tools from RETRIEVED edge analysis"
  effort: S

- id: from_neo4j_yt_mcp_text_to_cypher_promotion
  priority: 55
  title: "Promote run_cypher as a primary retrieval path for aggregation/multi-hop queries"
  rationale: "Video 4: text-to-Cypher is the most consistent retriever for complex queries; QKG's run_cypher is an escape hatch not a first-class path"
  effort: S

- id: from_neo4j_yt_mcp_wrap_aura_agent_rest
  priority: 30
  title: "Monitor Aura Agent for bring-your-own-embedding support before evaluating migration"
  rationale: "Video 2: Aura Agent currently limited to OpenAI/Google embeddings — incompatible with BGE-M3 stack"
  effort: XS
```
