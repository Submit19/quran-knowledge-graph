---
type: research
status: done
priority: 82
tags: [research/agent-memory, research/mcp, research/agentic-patterns]
source: data/research_neo4j_crawl/02_agentic_patterns.md
date_added: 2026-05-10
---

# Neo4j Agentic + MCP + Agent Memory Patterns

## TL;DR
- QKG's reasoning memory schema is a strict subset of the canonical `neo4j-labs/agent-memory` schema — we're missing `ReasoningStep` (between Trace and ToolCall), the `:TOUCHED` edge, and `trace_embedding` on `:ReasoningTrace` (ours is on `:Query`).
- `neo4j-labs/agent-memory` (Python, async) covers ~80% of `reasoning_memory.py` and adds buffered writes, entity dedup, and an eval harness.
- Aura Agents cannot host our 21-tool Anthropic loop — no custom Python, Gemini-only LLM, OpenAI/Google embeddings only. Not a migration target.
- The official `mcp-neo4j-cypher` server exposes only 3 tools by design; our 21-tool decomposition is the recommended domain-specific pattern — we should wrap them as an MCP server.
- Canonical memory recall recipe: vector search on `trace_embedding` → 1-hop expand to `ToolCall` → return playbook (tool sequence). We currently return only the past answer text.

## Key findings
- **Schema gap**: `(:ReasoningTrace)<-[:PART_OF]-(:ReasoningStep)-[:CALLED_TOOL]->(:ToolCall)` — we collapse step into tool call. Fixes audit queries and matches `agent-memory` API.
- **Embedding placement**: `trace_embedding` should be on `:ReasoningTrace`, not on sibling `:Query`. After migration, `tool_recall_similar_query` should return the full tool sequence (playbook replay).
- **`:TOUCHED` edge**: broader than `:RETRIEVED` — fires when a step *examines* an entity, not only when it cites. Our `:RETRIEVED {tool, rank, turn}` is still valuable for citation use; keep both.
- **Buffered writes**: replace 21× synchronous driver round-trips per chat turn with a flush at end-of-turn — expected p95 drop ≥200ms.
- **MCP exposure**: `FastMCP` Python library; `@mcp.tool()` decorator. 21 tools ≈ 4,200 token startup cost in MCP clients — use graph-backed balanced loading (see [[mcp-tool-registry-patterns]]).
- **GLiNER + GLiREL cascade** for entity extraction from query text (POLE+O): worth piloting on English translations to build `:Entity:Person` / `:Entity:Location` nodes aliased to existing `:Concept` nodes.

## Action verdict
- ✅ Adopt — insert `:ReasoningStep` between Trace and ToolCall; migrate existing traces.
  **Promoted as:** `from_neo4j_crawl_reasoning_step` (high)
- ✅ Adopt — move `trace_embedding` to `:ReasoningTrace`; update `tool_recall_similar_query` to return playbook.
  **Promoted as:** `from_neo4j_crawl_trace_vector_index` (priority 82)
- ✅ Adopt — add cursor pagination to 8 search tools + `QKG_RESPONSE_TOKEN_LIMIT` env cap.
  **Promoted as:** `from_neo4j_crawl_pagination_cursors` (priority 72)
- ✅ Adopt — wrap 21 tools as stdio MCP server (`mcp-qkg`).
  **Promoted as:** `from_neo4j_crawl_mcp_server` (medium)
- ❌ Skip — Aura Agents migration. No BGE-M3, no custom Python, Gemini-locked.
- 🔬 Research deeper — Test-drive `neo4j-labs/agent-memory` `adopt_existing_graph()` against our 2,662 existing traces.

## Cross-references
- [[vector-graphrag-neo4j-docs]] — retriever layer feeds the memory graph
- [[mcp-tool-registry-patterns]] — MCP token-budget design for our 21 tools
- [[agent-memory-yt-extracts]] — YouTube series on memory patterns supplements this
- Source: `repo://data/research_neo4j_crawl/02_agentic_patterns.md`
