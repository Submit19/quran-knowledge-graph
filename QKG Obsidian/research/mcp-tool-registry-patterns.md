---
type: research
status: done
priority: 63
tags: [research/mcp, research/neo4j-yt, research/context-management]
source: data/research_neo4j_crawl/06c_yt_mcp_aura_benchmarks.md
date_added: 2026-05-10
---

# MCP Tool Registry, Aura Agent, and RAG Benchmarks (Neo4j YT)

## TL;DR
- Context window bloat is the #1 MCP deployment hazard: ~200 tokens per tool definition at startup. Our 21 tools = ~4,200 tokens consumed before the first user message.
- Graph-backed balanced loading (8 hot tools upfront + discoverable categories) cuts startup cost 62% (Video 3 measured: 5K tokens → 2K tokens).
- Tool descriptions are the primary routing signal — natural language quality determines whether the model calls the right tool. Our 21 docstrings were written for Python, not LLM consumption. Audit before MCP wrapping.
- Aura Agent is locked to Gemini + OpenAI/Google embeddings — not a migration target for QKG's BGE-M3 stack.
- GraphRAG strategies consistently beat VectorRAG on multi-hop and aggregation queries (RAGAS measured); Text-to-Cypher is the most consistent retriever for complex queries.

## Key findings
- **Graph-backed tool registry**: store tools as nodes in Neo4j with a `usage_count` property; on startup, Cypher returns top-N by usage + a `discover_tools(category)` meta-tool. Self-optimizes as usage accumulates. QKG already has the usage signal in `reasoning_memory.py` RETRIEVED edge counts — zero new infrastructure needed.
- **Recommended startup set** (8–10 tools): `semantic_search`, `hybrid_search`, `get_verse`, `get_verse_words`, `search_arabic_root`, `lookup_word`, `explore_surah`, `search_keyword` + `discover_qkg_tools` meta-tool.
- **Discoverable categories**: etymology (`lookup_wujuh`, `explore_root_family`, `compare_arabic_usage`, `search_semantic_field`, `search_morphological_pattern`), traversal (`traverse_topic`, `find_path`, `query_typed_edges`), advanced (`concept_search`, `recall_similar_query`, `get_code19_features`, `run_cypher`).
- **"Mandatory" doesn't force invocation**: Claude "cannot be compelled" — uses tool descriptions voluntarily. Naming matters more than instruction imperatives. Name the discovery tool `explore_available_qkg_tools`.
- **Tool sequencing in graph**: record which tools fire sequentially (A → B patterns) in the graph; surface in descriptions. QKG's RETRIEVED edge sequence in `reasoning_memory.py` already captures this.
- **Text-to-Cypher gap**: VectorRAG fails on aggregation queries ("find genres with most movies"). QKG's `run_cypher` is the closest equivalent but is opt-in; promoting it as primary for aggregation/count queries would close this gap.
- **Authorization in MCP**: unsolved in the spec. Neo4j's official server is "supported"; Labs servers are "experimental." Matters if QKG is ever hosted publicly.

## Action verdict
- ✅ Adopt — audit and rewrite all 21 tool descriptions for LLM routing clarity before MCP wrapping.
  **Promoted as:** `from_neo4j_yt_mcp_tool_description_audit` (priority 62)
- ✅ Adopt — implement graph-backed tool registry using RETRIEVED edge counts from `reasoning_memory.py`.
  **Promoted as:** `from_neo4j_yt_mcp_graph_backed_registry` (priority 63)
- ✅ Adopt — define MCP startup set (8 tools) + 3 discoverable categories.
  **Promoted as:** `from_neo4j_yt_mcp_balanced_tool_grouping` (priority 64)
- 🔬 Research deeper — promote `run_cypher` as a primary retrieval path for aggregation/multi-hop queries.
  **Promoted as:** `from_neo4j_yt_mcp_text_to_cypher_promotion` (priority 55)
- ❌ Skip — Aura Agent migration. No BGE-M3, no custom Python, Gemini-locked.

## Cross-references
- [[agentic-patterns-neo4j]] — MCP server design and the 21-tool decomposition rationale
- [[ai-graph-ecosystem-extracts]] — MCP scale context (21K+ servers, FastMCP library)
- [[agentic-graphrag-yt-patterns]] — router patterns that depend on well-described tools
- Source: `repo://data/research_neo4j_crawl/06c_yt_mcp_aura_benchmarks.md`
