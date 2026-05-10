# 04 — AI Knowledge Graph extract (QKG-relevant slices)

_Source: `C:\Users\alika\Agent Teams\AI tools and research knowledge graph\AI_KNOWLEDGE_GRAPH.md`
(layers 0, 4, 9, 12, 13, 20). Extracted 2026-05-10 before the folder is removed for simplicity._

The AI graph is a 270KB / 3000-line markdown reference covering the AI ecosystem in 28+ layers. Below: only the items that map to QKG's existing surface area, with a verdict on action.

## TL;DR — what we should pull into QKG

1. **ZeroEntropy zerank-2** holds #1 on the reranker leaderboard (ELO 1680+) — A/B against our `BAAI/bge-reranker-v2-m3` could be a fast win.
2. **Cohere Rerank 4 Pro** (ELO 1627, RAGAS perfect 1.0 relevance, 32K context) — second drop-in candidate; only API access though.
3. **BGE-Reranker v2.5** is out — we're on v2-m3; cheap upgrade if the multilingual story holds.
4. **LightRAG** (28K stars, EMNLP 2025, Neo4j-backed dual-level retrieval) is a *direct competitor architecture* — worth a deeper spike than what the Neo4j crawl flagged.
5. **RAG Triad metrics** (Context Relevance + Groundedness + Answer Relevance) should be added to `evaluate.py` directly — they orthogonally cover the failure modes our current 13-question eval doesn't cleanly separate.
6. **Reflexion pattern** (Shinn et al. 2023) — self-reflection step at end of each agent turn could lift answer quality on weak questions (meditation/reverence/Surah 55 cluster).
7. **Hybrid Memory Architecture (2026)** validates our `reasoning_memory.py` direction — short-term + episodic + long-term + RAG. We already have all four conceptually; comparing to **mem0 (52K stars)** and **Zep Graphiti (temporal KG)** is worthwhile.
8. **Hub-and-Spoke multi-agent topology** — 40–60% cost reduction by routing tool work through cheaper worker models. Could let us run on Sonnet/Haiku for cheap tools and only escalate to Opus for synthesis.

## Layer-by-layer findings

### Layer 0 — Foundational Research

| Paper / Concept | QKG relevance | Action |
|---|---|---|
| **Reflexion** (Shinn 2023) — self-reflection for agents | After agent turn ends, generate a one-sentence "what would I do differently?" memo and append to next turn's context. Could lift weak-question scores. | Propose ralph task. |
| **Mixture-of-Agents (MoA)** (Wang 2024) — layered agents, prior outputs as input | For high-stakes queries (low-recall on first pass), route through 2-3 parallel agents and synthesize. Expensive but high-quality. | Research thread. |
| **Agent-as-a-Judge** (2024) — full agent evaluating another agent's chain, not just final output | Direct upgrade for `eval_v1.py` — evaluate the *tool sequence* and reasoning quality, not just citation count. | Propose ralph task. |
| **Titans** (Behrouz/Google Dec 2024) — neural long-term memory at test time | Beyond our reach (architecture-level), but validates our reasoning_memory direction. | Read-only finding. |
| **Speculative sampling** (Chen DeepMind 2023) — 2-3× inference speedup | Anthropic API doesn't expose this control to us. | Read-only. |
| **Many-shot ICL** (Agarwal 2024) — 1M-context closes fine-tune gap | If we ever migrate to Claude Sonnet 1M context, we can replace fine-tuning with hundreds of in-context QRCD examples. | Future thread. |

### Layer 4 — Agent Frameworks & Orchestration

We're hand-rolled. Several patterns worth borrowing:

- **LangGraph v1.1.8 (Apr 2026):** *Node Caching* (skip recomputation on retries), *Pre/Post Model Hooks* (inject guardrails before/after model calls), *UntrackedValue* (transient state not checkpointed). Our chat.py already does roughly the first two informally — formalizing them could clean up code.
- **Production gotchas table** (Layer 4): "Tool failures ignored — LLM calls tool with wrong params, function returns null, agent continues with bad data → validate tool inputs before execution; return structured errors LLM can reason about." Audit our 21 tools for this; some return `{}` on failure rather than `{"error": ...}`.
- **Multi-agent topology — Hub-and-Spoke**: orchestrator on Opus delegates to cheap workers (Haiku) for tool calls. **40-60% cost reduction documented in production**. We could route etymology / search_keyword / get_verse to Haiku and reserve Opus for synthesis.

### Layer 9 — RAG, Vector DBs & Knowledge

**Reranker upgrade candidates** (we currently use `BAAI/bge-reranker-v2-m3`):

| Reranker | Numbers | Notes |
|---|---|---|
| **ZeroEntropy zerank-2** | ELO 1680+ — **#1 on the reranker leaderboard** in 2026 | API only |
| **Cohere Rerank 4 Pro** | ELO 1627 (#2), 32K context, RAGAS 1.0 relevance, 100+ languages | API only |
| **Cohere Rerank 4 Fast** | ELO 1506 (#7) | Cheaper than Pro |
| **BGE-Reranker v2.5** | Newer than our v2-m3 | Self-hosted, free |
| **ColBERT/RAGatouille** | Late interaction; faster than cross-encoders | Self-hosted, free |

**Validation of our architecture:** the "standard hybrid RAG pipeline" Layer 9 describes (Vector + BM25 → RRF → cross-encoder rerank → LLM) is *exactly* what `chat.py` + `retrieval_gate.py` already do. We're on-pattern.

**Direct competitors / inspirations:**

| Tool | Stars | Why it matters |
|---|---|---|
| **LightRAG** | 28K | EMNLP 2025; **dual-level retrieval** (low-level entity + high-level concept); **Neo4j storage backend supported**; LLM cache management; Langfuse + RAGAS integration. Our concept_search is similar but coarser. |
| **Cognee** | 14.2K | ECL (Extract, Cognify, Load) pipeline; **92.5% accuracy vs 60% for traditional RAG** in their benchmarks; agent memory in 6 lines; Apache 2.0. |
| **GraphRAG (Microsoft)** | — | "10-100× more expensive to index — not a default; use when relationships between entities matter." We do already. |

**RAG Triad eval metrics** (we should add to `evaluate.py`):
- **Context Relevance:** is the retrieved context relevant to the query? (Low → fix retrieval)
- **Groundedness:** is the answer supported by the retrieved context? (Low → tighten system prompt)
- **Answer Relevance:** does the answer address what was asked? (Low → instruction-following issue)

### Layer 12 — Observability & Evaluation

| Tool | Pricing | Why it might matter for QKG |
|---|---|---|
| **Langfuse** | Free 50K units/mo, $29/mo Core, **MIT self-host** | OpenTelemetry-based; framework-agnostic; **acquired by ClickHouse Jan 2026 for $400M Series D**. Our `reasoning_memory.py` does ~30% of what Langfuse does. Could replace or complement. |
| **Braintrust** | Free 1M spans (most generous tier), $249/mo Pro | "Eval-driven development" — CI/CD deployment blocking on regression. We could wire eval_v1.py through this. |
| **AgentOps** | Free tier | **Agent-specific** — execution graphs, time-travel debugging, multi-agent workflow visualization, integrates with Anthropic SDK. Direct fit for QKG agentic loop. |
| **Phoenix (Arize)** | Free OSS, paid AX | Behavioral drift detection, bias detection, LLM-as-judge scoring. |

**3-tier eval strategy (2026 best practice):**
1. **Tier 1 — Dev experiments**: pre-merge eval on prompt/model/RAG changes (Braintrust/Langfuse experiments)
2. **Tier 2 — Staging**: regression on 100-500 example golden set (DeepEval/RAGAS/custom)
3. **Tier 3 — Production**: sample X% of live traffic, async LLM-as-judge scoring (Langfuse traces)

We're at Tier 2 only. Adding Tier 3 would let us catch real-world drift.

**LLM-as-Judge calibration tip:** use **reasoning models** (o3-mini, Claude Sonnet/Opus) as judges. They produce significantly better logical-consistency scores than non-reasoning models. Calibrate against 100 human-labeled samples; target ≥80% agreement.

### Layer 13 — MCP

The Neo4j crawl already surfaced "wrap our 21 tools as an MCP server." Layer 13 confirms scale: **21,845+ MCP servers in Glama Registry alone, 75+ built into Claude, 97M monthly SDK downloads.** This is mainstream now. Our MCP server task should be **higher priority** than the medium I gave it earlier.

**FastMCP** for Python is minimal boilerplate — `@mcp.tool()` decorator on each function. Our 21 tools could be wrapped in ~50 lines.

**Critical rules:**
1. STDIO MCP servers: **never use print/console.log** — corrupts JSON-RPC. Use stderr or file logging. (Affects how we'd port `chat.py` tools.)
2. Treat all tool inputs as untrusted — they come from an LLM, not a user. Already enforced via `run_cypher` denylist; need to audit other tools.
3. Test with **MCP Inspector** at `http://localhost:<port>/mcp` before deployment.

**MCP Apps (Jan 2026):** tools can return rich HTML interfaces rendered in sandboxed iframes within the chat. Our 3D verse graph + bilingual tooltips could be served as MCP Apps from the QKG MCP server — usable from Claude Desktop, not just our `app_free.py` web UI.

### Layer 20 — Agent Memory Systems (added to graph in Apr 2026)

**Big news: we should benchmark our `reasoning_memory.py` against these.**

| System | LongMemEval | Key feature |
|---|---|---|
| **MemPalace** | **96.6%** | MIT, launched Apr 5 2026; contextual associations |
| **Zep (Graphiti)** | 63.8% | Temporal KG; <200ms retrieval; 18.5% accuracy improvement; SOC2/HIPAA |
| **Mem0** | 49.0% | 52K+ stars; broadest integrations; async mode default; 26% accuracy gain vs plain vector |
| **Letta (MemGPT)** | N/A | LLM-as-Operating-System: Core (context window), Recall (searchable history), Archival (long-term) |

**Hybrid Memory Architecture (the 2026 dominant pattern):**
```
SHORT-TERM (session)  → In-context window
EPISODIC BUFFER       → Recent turns compressed (Mem0 ~50ms)
LONG-TERM MEMORY      → Persistent key-facts store (Mem0 graph, Zep)
KNOWLEDGE BASE        → Org docs / domain knowledge via RAG
```

We have versions of all four (chat.py context window, answer_cache.py, reasoning_memory.py, the Quran graph itself). Validating against benchmarks like LongMemEval would tell us where we sit.

## Promoted to ralph_backlog (5 new tasks)

See `ralph_backlog.yaml` for `from_ai_graph_*` entries. Top of list: ZeroEntropy + Cohere Rerank A/B (single-day spike, large potential lift).

## Promoted to research_backlog (6 new threads)

See `data/research_backlog.yaml`. Top: Reflexion pattern feasibility on chat.py.

## Pages NOT extracted (skipped intentionally)

- Layers 1, 2, 3 (foundation/open-source models, model serving) — model choice is downstream of our agentic stack
- Layer 5 (coding agents) — not relevant to QKG; relevant to *how I work on QKG*
- Layers 6, 7, 8 (browser/no-code/workflow) — out of scope
- Layer 10 (fine-tuning) — already addressed by `from_research_finetune_bge_m3_qrcd`
- Layer 11 (creative AI), 14 (trending OSS), 15-19 (voice/hardware/edge/verticals/labeling), 21-28 — not relevant
- Production AI Stack, NZ-specific content, vertical AI — not relevant to QKG specifically

If anything in those skipped sections becomes relevant, the AI graph (now at sibling location `..\AI tools and research knowledge graph\`) can be re-read.
