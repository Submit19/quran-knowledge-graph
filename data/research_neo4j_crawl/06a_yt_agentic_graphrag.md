# 06a — Agentic GraphRAG / Multi-Hop Reasoning videos (Neo4j YT)

## TL;DR (cross-video patterns most actionable for QKG)

- **Vector-first, graph-expand wins every time.** All four videos independently arrive at the same pattern: dense/hybrid retrieval seeds an anchor entity, then graph traversal expands context. QKG already does this via `hybrid_search` → `traverse_topic`; the signal is to keep it, not replace it.
- **Router agent solves abstract-concept weakness.** A lightweight "complexity classifier" routes simple semantic queries to vector search and structured/multi-hop queries to Cypher or traversal agents. QKG's abstract-concept failures (meditation/reverence/Surah 55 cluster) look like mis-routing: they land in dense retrieval when a concept-graph hop (`NORMALIZES_TO` → `:Concept` → `RELATED_TO`) would reach them.
- **LLM-as-judge + traversal limit = reliable agentic loop.** Video 4 (GraphReader) and Video 3 (EventKernel) both gate further hops with an evaluator step checking "is context sufficient / complete / relevant?" before spending more tokens. QKG's 15-turn cap is a blunt limit; a structured sufficiency check could cut wasted turns on hard abstract queries.
- **Schema in system-prompt enables zero-shot text-to-Cypher.** Video 2 (INRAE) and Video 3 both confirm that pasting the graph schema + 3-5 few-shot Cypher examples into the LLM system prompt is all you need for reliable NL→Cypher. QKG's `run_cypher` escape hatch already exists; surfacing the schema more explicitly to the model could improve its use on complex filter queries.
- **Tiered index cascade (fact → section → fulltext) reduces cold-start misses.** Video 4 proposes: try atomic-fact embeddings first, fall back to section embeddings, then BM25 full-text. QKG currently runs BM25+BGE-M3 in parallel (RRF); a serial fallback for zero-hit queries could patch the 13-27 cite gap.

---

## Per-video findings

### Agentic GraphRAG: Autonomous Knowledge Graph Construction and Adaptive Retrieval
**URL:** https://www.youtube.com/watch?v=x9YCcVtnH1M
**Speaker / context:** Adulia (UMass Amherst grad student), 11-min NODES AI 2026 talk. Tested on 25 documents / 25 queries.

**Most relevant QKG ideas:**
- Graph-only retrieval fails when any hop entity is missing — same fragility QKG hit with HippoRAG PPR.
- Hybrid (vector seed → graph expand) hit 68% exact-match, outperforming both pure strategies. `[09:41]` "vector runs first, gets the correct entity, and the graph expands upon it."
- Orchestrator routes by rule now; future plan is to train it on accumulated query/result data `[08:04]`.

**Action verdict:** no-op (validates existing QKG hybrid design). Revisit router training once QKG has 2K+ RETRIEVED edges.

---

### Agentic RAG Meets Neo4j: Multi-Hop Reasoning Over Scientific Knowledge Graphs
**URL:** https://www.youtube.com/watch?v=fiFERKjcAXs
**Speaker / context:** Annabel Banchero & Jean-Luc Long (EchoMetrics), 30-min NODES AI 2026 talk. Domain: INRAE agriculture research corpus (~400K nodes, 1M edges).

**Most relevant QKG ideas:**
- They unified tabular + unstructured text + a **lexical concept tree** into one graph — mirrors QKG's `:Concept`/`:SemanticDomain`/`:ArabicRoot` layers bridging to `:Verse`.
- A dedicated **concept/keyword entry-point tool** finds topical anchors before graph traversal. QKG has `concept_search` but it likely under-fires on abstract queries.
- `[19:43]` Pure agentic RAG "completely struggles with negative queries"; the KG-backed agent handles them cleanly via Cypher. Documents a known QKG limitation for count/rank/negation queries.
- `[27:06]` Schema + 3-5 few-shot Cypher examples in system-prompt was "all we needed" for reliable NL→Cypher.

**Concrete patterns / code:**
- `[11:50]` Dense + sparse → rerank → top-k IDs → LLM writes Cypher on same IDs. Validates QKG's `hybrid_search` → `run_cypher` chain.
- `[13:26]` Hardcoded expert-finder tool: concept lookup → traversal → aggregation → score. QKG analogy: composite `find_concept_cluster` tool hopping Concept→Verse→ArabicRoot.

**Action verdict:** adopt — make `concept_search` the default first call for abstract queries via system-prompt tool-order adjustment.

---

### NODES AI 2026 - EventKernel: Multi-Hop Reasoning and GraphRAG for AI-Powered Event Intelligence
**URL:** https://www.youtube.com/watch?v=sUysPxT9YCk
**Speaker / context:** Unnamed presenter, 26-min NODES AI 2026 demo. Domain: event management system (conferences, sessions, CFPs, users, venues).

**Most relevant QKG ideas:**
- **Bridge node pattern** `[08:37]`: one shared node type (`:User`) connects lexical graph to domain graph. QKG equivalent: `:Verse` bridges embedding space to `:ArabicRoot`/`:Concept` structured space. Naming this bridge explicitly in the system prompt helps the agent reason across layers.
- **Router agent + two sub-agents** `[23:41]`: complexity classifier routes to (a) traversal agent (DFS/BFS, open-ended) or (b) retriever agent (NL→Cypher + task decomposition). Directly fixes QKG's abstract vs. structured routing gap.
- `[24:28]` Task decomposition for multi-part queries: break into sub-questions, run NL2Cypher for each, consolidate. Useful for "how often does root X appear in surahs that also mention concept Y?"
- `[24:47]` In-loop evaluator checks for hallucination before returning; QKG's citation verifier is post-response — moving it pre-response would cut bad citations.

**Action verdict:** adopt — the router + two sub-agents is the clearest architectural fix for QKG's abstract-concept weakness. Propose as ralph task.

---

### GraphReader Agentic RAG: Rethinking Long-Context Retrieval Systems
**URL:** https://www.youtube.com/watch?v=SYU5Bn7B98A
**Speaker / context:** Jayata Batara & Somia Ranjandas (Deoid), 27-min NODES AI 2026 demo. Implementation of Alibaba GraphReader paper (Nov 2024) using open-source models (Llama 3.3 70B via Groq, sentence-transformers, Neo4j + LangGraph).

**Most relevant QKG ideas:**
- **Tiered retrieval fallback** `[16:20]`: fact-embedding → section-embedding → BM25 full-text (serial, each fires on zero-hit). QKG runs all three in parallel (RRF) which is better generally, but a zero-hit detector fallback to `concept_search` could patch cold abstract queries.
- **Scratch-pad / notebook pattern** `[16:46]`: agent maintains an explicit in-context running plan. QKG's `reasoning_memory.py` writes to Neo4j post-hoc; an in-context scratch-pad (passed as assistant context) could improve multi-turn coherence for hard abstract queries.
- **Three-way evaluator** `[18:45]`: after each hop LLM-as-judge decides (1) sufficient → answer, (2) hop-more → expand neighbors, (3) deep-dive → replan. QKG's flat 15-turn cap wastes turns when replanning is needed.
- `[16:28]` LangGraph agent state: `{user_query, rewritten_query, current_facts, notebook, traversal_count, traversal_limit}` — clean model; QKG approximates with tool-call cache + reasoning_memory but less structured.

**Concrete patterns / code:**
- `[20:49]` LangGraph flow: `initial_discovery → hop_analyzer → context_manager → evaluate_answer → [sufficient|hop_more|deep_dive]`. The `deep_dive` branch re-triggers `initial_discovery`, enabling full replanning without exceeding a turn cap.

**Action verdict:** research deeper — three-way evaluator + scratch-pad is the most novel pattern; directly targets the 13-27 cite gap. Cost: 1 extra LLM call per hop decision.

---

## Cross-cutting patterns (where multiple videos converge)

1. **Hybrid = vector seed + graph expand** (all 4 videos). QKG already does this. Validated.
2. **Concept/keyword nodes as entry-point layer** (V2 + V3 + V1). A dedicated "find concept anchors first" step before traversal repeatedly outperforms going straight to dense retrieval for abstract queries. QKG's `concept_search` tool exists but is probably under-called.
3. **NL→Cypher with schema in system-prompt** (V2 + V3). Zero-shot works well if schema + 3-5 examples are present. QKG's `run_cypher` is gated but could be more proactively used.
4. **In-loop evaluator / sufficiency gate** (V3 + V4). Explicit stop/continue/replan decision before consuming another turn. QKG lacks this — it relies on the model's implicit judgment.
5. **Router agent for query complexity** (V1 + V3). Rule-based now, trainable later. Directly maps to QKG's abstract vs. structured split.

---

## Proposed ralph_backlog tasks

```yaml
- id: from_neo4j_yt_router_agent
  title: "Add complexity-router to dispatch abstract vs structured queries"
  priority: high
  rationale: >
    V3 (EventKernel) and V1 (Agentic GraphRAG) both show that a lightweight
    router agent (classify query complexity → route to traversal agent or
    NL2Cypher agent) closes the abstract-concept gap. QKG's abstract-concept
    weakness (meditation/reverence/Surah 55 cluster, 13-27 cites) matches
    exactly the failure mode pure agentic-RAG exhibits in V2 (INRAE).
  implementation_sketch: >
    In chat.py system prompt, add routing heuristic: if query contains abstract
    noun (no verse ref, no root), call concept_search FIRST then traverse_topic.
    Longer term: add a classify_query_complexity() pre-step that routes to
    (a) semantic path or (b) structured Cypher path.
  files: [chat.py, app_free.py]

- id: from_neo4j_yt_sufficiency_gate
  title: "Add three-way in-loop evaluator (sufficient / hop-more / replan)"
  priority: medium
  rationale: >
    V4 (GraphReader) and V3 (EventKernel) both use an LLM-as-judge after each
    hop to decide continue/stop/replan, rather than a flat turn cap. QKG's
    15-turn limit wastes turns on hard abstract queries that need replanning,
    not more of the same tool. A structured sufficiency check could cut the
    13-27 cite gap and reduce hallucination on low-evidence abstract queries.
  implementation_sketch: >
    After each tool-call batch in the agentic loop, inject a short evaluator
    prompt: "Based on retrieved context so far, can you answer <query>?
    Reply: sufficient / hop_more / replan". Replan path triggers concept_search
    restart. Cap replan retries at 2.
  files: [chat.py]

- id: from_neo4j_yt_tiered_cascade
  title: "Add serial fallback cascade for zero-hit queries"
  priority: low
  rationale: >
    V4 proposes fact-embedding → section-embedding → BM25 as serial fallback
    (each fires only if previous returns zero hits). QKG runs all three in
    parallel via RRF which is better for normal queries, but for queries that
    score near-zero everywhere (cold abstract concepts), a dedicated zero-hit
    detector that retries with BM25-only or concept_search could recover lost
    recalls.
  implementation_sketch: >
    In hybrid_search(), if RRF top-1 score < threshold (e.g. 0.2), fall through
    to concept_search() on the query terms as a second attempt. Log these
    fallback events to reasoning_memory for analysis.
  files: [chat.py]
```

---

### Agentic GraphRAG: Multi-Agent Knowledge Graph Construction
**URL:** https://www.youtube.com/watch?v=bxXb8oT5E-k
**Speaker / context:** Internal research team (unnamed), ~27-min NODES community talk. Use-case: multi-researcher team building a shared KG from uploaded PDFs / Excel / JSON, queried via Neo4j MCP server + OpenAI ChatKit.

**TL;DR:** 4-agent KG *construction* pipeline (Analyze → Extract → Merge → QC). Not a retrieval improvement, but validates QKG's existing Concept ER layer and highlights two patterns worth reviewing.

**Most relevant QKG ideas:**

- **LLM semantic deduplication (Agent 3)** `[16:01–17:20]`: after parallel chunk extraction produces 84 raw entities, Agent 3 groups by type and does LLM-based semantic reasoning ("are these two entities the same real-world thing?") to produce 32 canonical entities. Outputs include a canonical name + merge rationale. This is exactly what QKG's `NORMALIZES_TO` edges do (Porter-stem ER over Keywords). Their finding: string matching alone fails for multi-word / paraphrased entities; semantic dedup is required. **QKG already does this** via `build_concepts.py`. Validating.

- **Graph QC agent (Agent 4)** `[19:00–21:00]`: semantic auditor samples parts of the final graph, asks the LLM to flag vague/inconsistent/reversed relationships against the original schema, and removes only low-confidence ones. Removed 3 relationships in the demo run. QKG has typed edges (SUPPORTS, ELABORATES, QUALIFIES, CONTRASTS, REPEATS) with `classify_edges.py`, but no post-hoc QC pass. A periodic graph quality audit (`cypher_analysis` task) could surface poorly-typed or reversed edges. Low priority for now — QKG's typed edge count is small (7K).

- **Batch UNWIND+MERGE write pattern** `[22:50–23:30]`: group all nodes and relationships by type, write each type in its own Cypher query. ~10× faster than row-by-row inserts; 57 nodes + 179 relationships in 2s. QKG's `build_graph.py` and `import_neo4j.py` already use UNWIND. Confirmed best practice.

- **LangSmith / eval-first culture** `[10:35–18:30]`: every agent step is wrapped with a traceable function; full LLM input/output + reasoning captured for prompt iteration. Mirrors QKG's `reasoning_memory.py` approach. They found eval was the "bedrock" before trusting the pipeline at scale.

**Action verdict:** no new tasks. Validates QKG's existing Concept ER (NORMALIZES_TO), UNWIND+MERGE writes, and reasoning_memory tracing. Periodic graph QC edge audit noted as future low-priority `cleanup` task if typed edge count grows significantly.

---

### Agentic GraphRAG: Multi-Agent Knowledge Graph Construction for Research Teams
**URL:** https://www.youtube.com/watch?v=KJSHagHkX8I
**Speaker / context:** Akil Ham, ~28-min NODES AI 2026 talk. Use-case: internal research team with fragmented cloud/personal-folder storage; goal is a shared KG ingestion tool queried via Neo4j MCP + OpenAI ChatKit (GPT-5, Next.js frontend, LangSmith tracing).

**TL;DR:** Highly similar architecture to `bxXb8oT5E-k` (4-agent Analyze→Extract→Merge→QC pipeline). Independently arrives at the same patterns. Mainly validating for QKG; one new detail on GDS future roadmap.

**Most relevant QKG ideas:**

- **LLM semantic dedup again** `[16:00–17:15]`: extracted 84 entities across 5 chunks → merged to 32 via LLM reasoning on descriptions (not string matching). Confirms QKG's `build_concepts.py` / `NORMALIZES_TO` approach is on-track.

- **Graph QC auditor (Agent 4)** `[19:00–21:40]`: removes only low-confidence/reversed relationships — in the demo, 3 out of 179 relationships flagged as semantically mismatched or reversed. Confirms the value of QKG's typed edge classification (`classify_edges.py`), but also signals that a post-hoc audit scan is worth adding eventually.

- **Batch UNWIND+MERGE** `[22:50–23:50]`: speaker independently reports ~10× write speedup and 2-second insert for 57 nodes + 179 relationships. Matches QKG's existing pattern.

- **GDS future roadmap** `[26:43–27:03]`: speaker explicitly lists PageRank, community detection, link prediction, and similarity as next steps for graph analytics. Aligns with the existing `graphrag_state_of_art` and `from_blog_betweenness_centrality_rerank` tasks already in the backlog.

- **Multimodal extraction** `[27:06–27:19]`: images + video ingestion planned. Not relevant to QKG's fixed Quran corpus.

- **LangSmith / eval-first** `[10:35–18:30]`: same pattern as `bxXb8oT5E-k`. Validating.

**Action verdict:** no new tasks. All actionable signals (semantic dedup, typed edge QC, UNWIND+MERGE, GDS analytics) are already represented in the backlog. Validating tick.
