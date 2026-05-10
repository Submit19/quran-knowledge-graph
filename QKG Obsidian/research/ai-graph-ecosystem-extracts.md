---
type: research
status: done
priority: 72
tags: [research/retrieval, research/reranker, research/agent-memory, research/observability, research/mcp]
source: data/research_neo4j_crawl/04_ai_graph_extract.md
date_added: 2026-05-10
---

# AI Ecosystem Graph — QKG-Relevant Extracts

## TL;DR
- ZeroEntropy zerank-2 (ELO 1680+, #1 reranker leaderboard 2026) and Cohere Rerank 4 Pro (ELO 1627, RAGAS 1.0 relevance, 32K context) are the top upgrade candidates over our `BAAI/bge-reranker-v2-m3`.
- LightRAG (28K stars, EMNLP 2025, Neo4j-backed dual-level retrieval) is a direct competitor architecture worth a deeper spike.
- Reflexion pattern (Shinn 2023) — self-reflection memo appended at end of each agent turn — could lift weak-question scores (meditation/reverence/Surah 55 cluster).
- Hub-and-Spoke multi-agent topology: 40–60% cost reduction by routing cheap tools (keyword search, verse lookup) to Haiku, reserving Opus for synthesis.
- 3-tier eval strategy: dev (Braintrust/Langfuse experiments) → staging (100–500 golden set) → production (async LLM-as-judge on live traffic). We're Tier 2 only.

## Key findings
- **BGE-Reranker v2.5** is out — we're on v2-m3; free upgrade candidate if multilingual story holds.
- **ColBERT/RAGatouille** (late interaction, self-hosted) is faster than cross-encoders on large candidate sets — see [[bge-m3-dense-vs-colbert]] for our decision to skip for now.
- **RAG Triad metrics** (Context Relevance, Groundedness, Answer Relevance) should be added to `evaluate.py` to orthogonally cover failure modes the current 13-question eval misses.
- **Hybrid Memory Architecture** (short-term + episodic + long-term + RAG) is the 2026 dominant pattern. We have all four conceptually; `reasoning_memory.py` is the episodic tier. MemPalace (96.6% LongMemEval), Zep/Graphiti (63.8%), mem0 (49.0%) are benchmark comparators.
- **MCP scale**: 21,845+ MCP servers in Glama Registry; 97M monthly SDK downloads. Our MCP server task priority should be elevated above "medium." FastMCP wraps our 21 tools in ~50 lines.
- **MCP Apps** (Jan 2026): tools can return rich HTML in sandboxed iframes. Our 3D verse graph could be served as an MCP App from Claude Desktop.
- **Critical MCP rule**: STDIO servers must never use `print()` / `console.log()` — corrupts JSON-RPC. Use `stderr` or file logging.
- **Tool failure pattern**: several QKG tools return `{}` or `[]` on miss rather than `{"error": "...", "hint": "..."}`. Structured errors allow the planner to re-plan; silent empty returns cause hallucination-by-silence.

## Action verdict
- 🔬 Research deeper — ZeroEntropy zerank-2 + Cohere Rerank 4 Pro A/B against `bge-reranker-v2-m3` on QRCD. Single-day spike, potentially large lift.
- 🔬 Research deeper — LightRAG dual-level retrieval spike against QKG's concept_search + traverse_topic chain.
- 🔬 Research deeper — Reflexion pattern feasibility on `chat.py` (one sentence "what would I do differently?" memo appended to next turn).
- 🔬 Research deeper — Hub-and-Spoke routing: model cheap vs synthesis tool calls for cost estimate.
- ✅ Adopt — add RAG Triad metrics to `evaluate.py`.
- ✅ Adopt — audit 21 tools for silent empty-return failure modes; switch to structured error dicts.

## Cross-references
- [[bge-m3-dense-vs-colbert]] — ColBERT / reranker comparison details
- [[agentic-patterns-neo4j]] — MCP server design (21-tool wrapping)
- [[mcp-tool-registry-patterns]] — token-budget design for MCP wrapping
- [[agent-memory-yt-extracts]] — memory architecture benchmark comparators (MemPalace, Zep, mem0)
- Source: `repo://data/research_neo4j_crawl/04_ai_graph_extract.md`
