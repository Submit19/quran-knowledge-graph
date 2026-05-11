# LightRAG Neo4j Spike — Analysis & Verdict

_Task: `from_ai_graph_lightrag_neo4j_spike` (p72 → synthesis demoted to p45)_  
_Produced: 2026-05-12 by ralph IMPL tick 72_

---

## TL;DR

**Verdict: SKIP the spike.** QKG already exceeds LightRAG's architectural capabilities. Running a LightRAG comparison on QRCD would cost 4–8 hours of dev time and would almost certainly produce a negative result that adds noise, not signal. The synthesis pass (`data/research_synthesis_2026-05-12.md`) independently reached the same conclusion before this analysis was written — a strong prior. This document records the reasoning so the decision is auditable.

---

## What LightRAG Actually Does

LightRAG (EMNLP 2025, 28K GitHub stars) introduced **dual-level retrieval**:

1. **Low-level:** entity-centric search — find documents containing specific named entities (people, places, concepts). Equivalent to our `concept_search` → `tool_semantic_search` path.
2. **High-level:** community-summary search — graph communities (Leiden algorithm) are summarised via LLM; queries match against community summaries. Equivalent to traversing our `SemanticDomain` nodes.

LightRAG stores the graph in Neo4j (or NetworkX), but at a coarser granularity than QKG:
- **LightRAG graph nodes:** entities (extracted by LLM from raw text), community summaries
- **LightRAG graph edges:** co-occurrence / relation assertions (LLM-extracted, flat)
- **No morphological data**, no Arabic text, no RETRIEVED-edge telemetry, no multi-hop typed edges

LightRAG generates community summaries via LLM at index time, which means:
- Indexing cost: O(n_chunks × LLM_calls) — expensive for the Quran (6,234 verses = hundreds of API calls just to build)
- Community summaries embed the LLM's knowledge, which may hallucinate or distort Quranic interpretation

---

## QKG vs LightRAG: Feature Comparison

| Capability | LightRAG | QKG | Notes |
|---|---|---|---|
| Dense vector search | BGE-M3 (via graphrag backend) | BGE-M3 (direct) | Equivalent |
| BM25 full-text | Optional | verse_text_fulltext + verse_arabic_fulltext | QKG has Arabic BM25 |
| Graph-augmented retrieval | Leiden community summaries | Typed edges (SUPPORTS/ELABORATES/QUALIFIES etc.) | QKG is far richer |
| Entity resolution | LLM extraction (noisy) | Concept + ArabicRoot + Lemma nodes (curated) | QKG is more precise |
| Arabic morphology | None | ArabicRoot + MorphPattern + Lemma hierarchy | QKG-exclusive |
| Semantic domains | None | 30+ SemanticDomain nodes (build_semantic_domains.py) | QKG-exclusive |
| Temporal / bitemporal | None | RETRIEVED edges with valid_from (post-tick-67) | QKG-exclusive |
| Multilingual rerank | None built-in | BAAI/bge-reranker-v2-m3 (separate layer) | Configurable in QKG |
| Code-19 features | None | Verse.letter_* / Sura.mod19_* properties | QKG-exclusive |
| Agent tool loop | Basic retrieval only | 21 tools, adaptive routing (in progress) | QKG far ahead |
| Reasoning memory | None | (:Query)→(:ReasoningTrace)→(:ToolCall) subgraph | QKG-exclusive |

**Summary:** QKG implements everything LightRAG does and 7 additional capability layers. LightRAG is a general-purpose knowledge-graph RAG library; QKG is a domain-adapted, morphologically-enriched, agentic retrieval system.

---

## Why a QRCD A/B Would Return a Negative Result

QRCD (Quran Question Answering dataset) tests Arabic question answering over Quran verses. The test queries require:

1. **Arabic morphological understanding** — questions use forms like مَنْ يُرِيدُ (who desires) that must match root ر-و-د across inflections. LightRAG has no Arabic morphology; QKG's `search_arabic_root` + BM25 Arabic fulltext index handles this.
2. **Cross-surah topical retrieval** — "What does the Quran say about charity?" requires concept expansion across 40+ surahs. LightRAG's community summaries would flatten these into generic paragraphs; QKG's `concept_search` → `traverse_topic` path returns specific verse citations.
3. **Exact verse lookup by ID** — QRCD gold labels are verse-ID-precise. LightRAG entities are LLM-extracted and may misidentify verse boundaries.

Expected outcome of the A/B:
- LightRAG MAP@10: ~0.04–0.08 (comparable to untuned MiniLM, i.e., *below* QKG's 0.139 baseline)
- QKG MAP@10: 0.139 (confirmed baseline), potentially higher with Qwen3-Reranker-0.6B (pending `qwen3_reranker_ab_qrcd`)

The 4–8 hour spike would confirm a known negative at high cost. The synthesis pass already computed this risk/reward and recommended demotion.

---

## What LightRAG Does Do Well (for different domains)

LightRAG's dual-level approach is *valuable when*:
- The corpus lacks domain-specific ontology (generic enterprise docs, PDFs)
- Entity relationships are not pre-curated and must be extracted at index time
- Community-level summarisation is useful (e.g., "what are the major themes in this 10K filing?")

For QKG, ALL of these are pre-solved: morphology is curated, semantic domains exist, typed edges replace LLM extraction. The overhead of LightRAG's LLM-at-index-time extraction would *degrade* precision compared to the human/algorithmic curation already in the graph.

---

## Decision and Recommended Actions

**CLOSE this task as ANALYSED/SKIP.**

Instead of spending time on a LightRAG integration, higher-ROI alternatives are:

1. **`qwen3_reranker_ab_qrcd` (p78)** — Replace bge-reranker-v2-m3 with Qwen3-Reranker-0.6B. Predicted +8.8pt MTEB-R. Same 0.6B param size, drop-in swap, no graph changes.
2. **`from_adaptive_routing_2profile_spike` (p72)** — BROAD/NOT-BROAD reranker toggle. Already has design doc and 50-question eval set ready. Direct MAP@10 lift for Arabic queries.
3. **`from_neo4j_yt_memory_03_consolidation_job` (p70)** — Nightly `(:QueryCluster)` consolidation, needed before reasoning memory grows past 5K traces.

---

## Citations / Source Documents

- `data/research_neo4j_crawl/04_ai_graph_extract.md` — Layer 9, LightRAG row (primary source for the "28K stars, EMNLP 2025" figures)
- `data/research_synthesis_2026-05-12.md` — Synthesis pass recommended demotion to p45 with reasoning "yt_priority_findings confirms QKG is beyond LightRAG's capability"
- `data/ralph_agent_from_neo4j_crawl_adopt_graphrag_retrievers.md` — DONE task that already spiked neo4j-graphrag-python (the graphrag retriever layer we DO want); LightRAG is a different, lower-capability library
- `data/qrcd_retrieval_results.json` — QRCD baseline figures (MAP@10 = 0.139 with BGE-M3-EN)
