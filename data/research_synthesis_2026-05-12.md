# Cross-research synthesis — 2026-05-12

## TL;DR (5 bullets)

- **The reranker is confirmed harmful on Arabic queries and must be disabled or replaced.** QRCD ablation shows `bge-reranker-v2-m3` drops hit@10 by 50% (0.6364→0.3182). Disabling it is the single highest-confidence, zero-cost quality fix available right now. Predicted eval_v1 lift: +4 to +10 avg cites/q.
- **Abstract-concept failures (meditation/reverence/Surah 55 cluster, 13–27 cites) are a routing problem, not a retrieval problem.** Six sources independently converge: those queries land in dense retrieval when `concept_search`→`traverse_topic` is the correct path. `from_neo4j_yt_router_agent` is DONE but the 50-question bucketed eval to confirm it works is still pending.
- **The reasoning memory schema is missing two critical nodes.** `ReasoningStep` (between Trace and ToolCall) and `trace_embedding` on the trace (not Query) are confirmed by 5+ sources (02_agentic_patterns, 06b_yt_agent_memory, 04_ai_graph_extract, CLAUDE.md agent-memory section). `from_neo4j_yt_memory_05_reasoning_step` is DONE; `from_neo4j_crawl_trace_vector_index` is DONE. Next: bitemporal RETRIEVED edges and the consolidation job.
- **Context-window hygiene compounds across every tick.** Three independent sources (05_ralph_yt_extract, yt_priority_findings, blog_findings) warn that CLAUDE.md size directly degrades output quality. `from_ralph_yt_01_tokenize_claudemd` is DONE. The adaptive-routing tasks in proposed_tasks.yaml (50q bucketed eval, design doc) are now the logical sequels.
- **The QRCD MAP@10 gap (0.139 vs 0.36 lit) is domain adaptation, not architecture.** BGE-M3 ColBERT adds only ~1–2 nDCG points on Arabic; the literature ceiling comes from CamelBERT-tafseer fine-tunes. `from_research_finetune_bge_m3_qrcd` (p78) is the single most important quality task not yet started.

---

## Cross-cutting insights

1. **Reranker harm is confirmed by three independent data streams.** `qrcd_ablation.json` (direct measurement), `04_ai_graph_extract.md` (ZeroEntropy/Cohere leaderboard research), `research_bge_m3_dense_vs_colbert.md` (BGE-M3 architecture analysis). All three say the same thing: `bge-reranker-v2-m3` hurts Arabic-query retrieval. No source contradicts this. The fix (RERANK_DISABLED=1 as default until replacement is confirmed) has been written up but never actually applied to the production eval baseline.

2. **Five sources confirm the same retrieval architecture (hybrid = vector seed + graph expand).** 06a (4 videos), 01_vector_graphrag, blog_findings (GraphRAG blog), 04_ai_graph_extract (Layer 9), yt_priority_findings. QKG already implements this. No contradictions. Architectural confidence is high — do not redesign retrieval.

3. **Tool description quality is cited as the primary routing signal by four independent sources.** 06c (3 videos), blog_findings (agent-tools article), 04_ai_graph_extract (Layer 13). `from_neo4j_yt_mcp_tool_description_audit` (p70) is still pending and is the only task directly targeting this high-frequency finding. It is systematically undervalued given confirmation depth.

4. **Memory schema gaps are confirmed triple/quad by the research corpus.** Missing: `ReasoningStep` node (02_agentic, 06b videos, 04_ai_graph), bitemporal RETRIEVED edges (06b_video2, 06b_video4), consolidation/sleep-step (06b_video3, 06b_video4), session node (06b_video4). The first is DONE; the others are in the backlog but scattered at different priorities (75, 70, 64).

5. **The 50-question bucketed eval is the gating dependency for adaptive routing.** `proposed_tasks.yaml` has three adaptive-routing tasks (p72–p80) that are all blocked on `from_adaptive_routing_50q_bucketed_eval` (p78). Yet the current eval_v1 (13 questions) is too small to detect per-profile lift. The loop cannot validate any routing experiment without this dataset.

6. **Context-engineering convergence: QKG is at Level 6–7 (yt_priority_findings) and all major architecture decisions are validated.** The external research is now producing more "validating" findings than "novel" ones. This means future research ticks will show diminishing returns. The loop should shift budget from research reads to implementation ticks.

7. **The QRCD gap is domain adaptation, not architecture.** `research_bge_m3_dense_vs_colbert.md` + `eval_ablation_retrieval.py` data: MAP@10 = 0.139 vs literature ceiling 0.36. Literature ceiling is from CamelBERT-tafseer fine-tunes, not from a better retrieval architecture. `from_research_finetune_bge_m3_qrcd` is the single clearest path to closing that gap, yet it has only p78 and zero blocked-on relationships in the backlog.

8. **"No ColBERT" is the right call for now.** `research_bge_m3_dense_vs_colbert.md` gives only ~1–2 nDCG points on Arabic. Three-source consensus: solve domain adaptation (fine-tune) first; revisit ColBERT only if fine-tuned dense plateaus below MAP 0.25.

---

## Backlog re-prioritization

| task_id | current pri | recommendation | reason |
|---|---|---|---|
| `rerun_eval_against_current` | 95 | **PROMOTE +0, but change spec: run with RERANK_DISABLED=1** | The most important next eval is not "current code" but "current code without reranker." `from_ai_graph_disable_reranker_baseline` (DONE) confirmed the reranker is harmful; the actual eval_v1 run with RERANK_DISABLED=1 was deferred because the server was offline. This is the missing data point for the 50-question adaptive-routing design. |
| `from_neo4j_crawl_adopt_graphrag_retrievers` | 85 | DONE — no action | |
| `from_neo4j_yt_router_agent` | 85 | DONE — no action | |
| `from_research_finetune_bge_m3_qrcd` | 78 | **PROMOTE to 88** | Three sources confirm the QRCD gap (0.139 vs 0.36) is domain adaptation. This task is the only one that directly attacks the metric ceiling. Currently ranked behind many schema/memory tasks that have less direct quality impact. It has no blockers. |
| `from_neo4j_yt_mcp_tool_description_audit` | 70 | **PROMOTE to 80** | Four independent research streams confirm tool description quality is the primary routing signal. The abstract-query cluster failures are partly routing failures; description quality directly affects which tool fires first. Low effort, high compounding impact. |
| `from_adaptive_routing_50q_bucketed_eval` | 78 (proposed) | **PROMOTE to 85, APPROVE from proposed_tasks.yaml** | Gates three adaptive-routing experiments. Without the 50q bucketed dataset, we cannot validate the router agent (DONE) or the 2-profile spike. This is the empirical bottleneck for the next 20 ticks. |
| `from_adaptive_routing_design` | 80 (proposed) | **APPROVE, keep priority 80** | Unblocks the 2-profile spike. Design can proceed while bucketed eval is built. |
| `from_adaptive_routing_2profile_spike` | 72 (proposed) | **APPROVE, keep priority 72** | Minimum-viable adaptive routing: BROAD/NOT-BROAD reranker toggle. Contained risk. Blocked on bucketed eval. |
| `from_neo4j_yt_memory_01_bitemporal_retrieved` | 75 | **DEMOTE to 60** | Important but not urgent. The embedding migration (BGE-M3) is effectively complete; bitemporal properties are most valuable once another model version change is imminent. Schema additive, can be done later without loss. |
| `from_neo4j_yt_memory_03_consolidation_job` | 70 | **DEMOTE to 55** | Trace accumulation is a hygiene issue, not a quality blocker. 2,600 traces is still manageable. Defer until after quality-metric lift tasks land. |
| `from_ai_graph_reflexion_pattern` | 76 | **KEEP, add blocked_on_research suggestion** | Strong theoretical basis but untested on QKG. Should be preceded by the 50q bucketed eval so we have a clean per-profile signal to measure the lift. |
| `from_ai_graph_lightrag_neo4j_spike` | 72 | **DEMOTE to 45** | yt_priority_findings (Chase AI video) confirms QKG is *beyond* LightRAG's capability (typed edges, semantic domains, morphological patterns). The spike would likely return a negative result at high cost (~4–8h dev time). |
| `build_multihop_benchmark` | 50 | **PROMOTE to 65** | `from_adaptive_routing_50q_bucketed_eval` overlaps significantly but stops short of gold traversal paths. For confirming that graph methods beat vector RAG (the open research question in 06a), a multihop bench with gold paths is needed. |
| `from_neo4j_crawl_arabic_fulltext_index` | 75 | **KEEP, add blocked_on note** | Confirmed by 03_cypher_gds_perf (p97 967ms Arabic keyword tool). Still valid. |
| `from_neo4j_crawl_single_shot_vector_traversal` | 78 | **KEEP** | 03_cypher_gds_perf confirms single-query vector+1-hop is feasible and saves one round trip. Directly addresses latency. |
| `from_ralph_yt_03_audit_negative_prompts` | 70 | **DEMOTE to 50** | Validated by 05_ralph_yt_extract but the gain is marginal at this stage. More impactful work is available. |
| `from_neo4j_yt_mcp_balanced_tool_grouping` | 78 | **KEEP** | 06c confirms 4,200 token startup cost for 21 tools. The 62% token reduction is real. But depends on tool description audit (p80) being done first — add blocker. |

---

## New tasks surfaced

```yaml
- id: from_synthesis_rerun_eval_rerank_disabled
  type: eval
  priority: 92
  description: "[from-synthesis] Run eval_v1 (13q) with RERANK_DISABLED=1 as the NEW default baseline — replace current 43.6-cite baseline with rerank-off results"
  spec:
    notes: |
      from_ai_graph_disable_reranker_baseline (DONE) proved the reranker is harmful but
      deferred the actual eval_v1 run (server was offline). This task completes that
      deferred step. Predicted new baseline: 48-54 avg cites/q. This becomes the new
      default_baseline_eval for all subsequent eval comparisons.
      Run: SEMANTIC_SEARCH_INDEX=verse_embedding_m3 RERANK_DISABLED=1 python eval_v1.py
      Backup first: cp data/eval_v1_results.json data/eval_v1_results.pre-rerank-disabled.json
    acceptance:
      - file_exists: data/eval_v1_results.json
      - file_min_bytes: {path: data/eval_v1_results.json, min: 50000}
      - file_exists: data/eval_v1_results.pre-rerank-disabled.json

- id: from_synthesis_approve_adaptive_routing_bundle
  type: cleanup
  priority: 85
  description: "[from-synthesis] Approve and merge three proposed_tasks.yaml adaptive-routing tasks into ralph_backlog.yaml (from_adaptive_routing_50q_bucketed_eval p85, from_adaptive_routing_design p80, from_adaptive_routing_2profile_spike p72)"
  spec:
    notes: |
      These three tasks are stuck in proposed_tasks.yaml pending operator review.
      The synthesis confirms they are the highest-leverage next cluster (gate the router
      experiment that is DONE but unmeasured). Merge them into ralph_backlog.yaml at
      their proposed priorities.
    acceptance:
      - file_exists: ralph_backlog.yaml
      - file_min_bytes: {path: ralph_backlog.yaml, min: 1}

- id: from_synthesis_arabic_reranker_eval
  type: cypher_analysis
  priority: 82
  description: "[from-synthesis] Establish Arabic reranker replacement shortlist: test bge-reranker-v2.5 (free, self-hosted, newer than v2-m3) against RERANK_DISABLED baseline on QRCD 22-q. Accept if hit@10 >= 0.55 (vs disabled=0.636, broken=0.318). Blocks the permanent reranker decision."
  spec:
    notes: |
      from_ai_graph_arabic_reranker_research (p75) surveys options. This task makes the
      decision concrete: test the single best free candidate (bge-reranker-v2.5) before
      committing to RERANK_DISABLED as permanent. No API key needed.
    acceptance:
      - file_exists: data/ralph_analysis_arabic_reranker_v25_eval.md
      - file_min_bytes: {path: data/ralph_analysis_arabic_reranker_v25_eval.md, min: 400}

- id: from_synthesis_tool_description_rewrite
  type: cleanup
  priority: 80
  description: "[from-synthesis] Rewrite all 21 chat.py tool descriptions for LLM routing clarity — when-to-use, when-NOT-to-use, expected output shape. Merge with from_neo4j_yt_mcp_tool_description_audit (p70) — same deliverable, this sets priority correctly."
  spec:
    notes: |
      Four sources confirm description quality is the primary tool-selection signal.
      Currently filed at p70 under from_neo4j_yt_mcp_tool_description_audit but
      the synthesis evidence warrants p80. This task supersedes that one.
    acceptance:
      - file_exists: data/ralph_analysis_tool_description_rewrite.md
      - file_min_bytes: {path: data/ralph_analysis_tool_description_rewrite.md, min: 500}
```

---

## Blocked-on-research suggestions

| task | should be preceded by | reason |
|---|---|---|
| `from_ai_graph_reflexion_pattern` (p76) | `from_synthesis_rerun_eval_rerank_disabled` + `from_adaptive_routing_50q_bucketed_eval` | Reflexion lifts the weak-question cluster; we need a clean per-profile baseline to measure the lift. Running Reflexion against the current 43.6-cite baseline with reranker on will confound results. |
| `from_neo4j_yt_mcp_balanced_tool_grouping` (p78) | `from_synthesis_tool_description_rewrite` (p80) | The startup set ranking uses RETRIEVED-edge counts, but the descriptions must be rewritten *before* grouping — otherwise you're optimizing which badly-described tools to show first. |
| `from_ai_graph_cohere_rerank_ab_impl` (p50) | `from_synthesis_arabic_reranker_eval` | Should wait for the free bge-reranker-v2.5 test result. If v2.5 achieves hit@10 ≥ 0.55, the expensive Cohere A/B becomes unnecessary. |
| `from_adaptive_routing_2profile_spike` (p72) | `from_adaptive_routing_50q_bucketed_eval` (p85) | Already blocked in proposed_tasks.yaml — confirm blocker is preserved when merging to backlog. |
| `build_multihop_benchmark` (p65, proposed promote) | `from_adaptive_routing_50q_bucketed_eval` | 50q bucketed eval overlaps; build the multihop bench after so the two don't produce redundant questions. |

---

## Top 3 actions for next 10 ticks

1. **Ticks 1–2: Run eval_v1 with RERANK_DISABLED=1 (`from_synthesis_rerun_eval_rerank_disabled`, p92).** This establishes the correct new baseline. Every subsequent eval comparison is invalid until this is done. The task spec is fully written in `ralph_analysis_from_ai_graph_disable_reranker_baseline.md`. Server needs to be online; takes ~55 min.

2. **Ticks 3–4: Approve and run the 50-question bucketed eval build (`from_adaptive_routing_50q_bucketed_eval`, p85).** The router agent is DONE but unvalidated. Three adaptive-routing tasks are blocked on this dataset. Without it, the next 10–15 implementation ticks are running blind experiments with a 13-question noisy signal.

3. **Ticks 5–8: Tool description audit/rewrite (`from_synthesis_tool_description_rewrite`, p80) + promote `from_research_finetune_bge_m3_qrcd` to p88 and start spec.** Tool descriptions are the compounding win (affects every chat turn); the fine-tune is the clearest path to the QRCD metric ceiling. Both can run in parallel ticks.

---

## Sources read

- `data/research_neo4j_crawl/01_vector_graphrag.md`
- `data/research_neo4j_crawl/02_agentic_patterns.md`
- `data/research_neo4j_crawl/03_cypher_gds_perf.md`
- `data/research_neo4j_crawl/04_ai_graph_extract.md`
- `data/research_neo4j_crawl/05_ralph_yt_extract.md`
- `data/research_neo4j_crawl/06a_yt_agentic_graphrag.md`
- `data/research_neo4j_crawl/06b_yt_agent_memory.md`
- `data/research_neo4j_crawl/06c_yt_mcp_aura_benchmarks.md`
- `data/research_neo4j_crawl/yt_priority_findings.md`
- `data/research_neo4j_crawl/blog_findings.md`
- `data/research_bge_m3_dense_vs_colbert.md`
- `data/ralph_analysis_from_ai_graph_disable_reranker_baseline.md`
- `data/proposed_tasks.yaml`
- `ralph_backlog.yaml`
- `ralph_state.json` (done_task_ids reviewed)
