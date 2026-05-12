---
type: decision
adr: 0041
status: accepted
date: 2026-05-13
tags: [decision, eval, benchmark, multihop, graph-retrieval]
supersedes: none
---

# ADR-0041 — Multi-hop benchmark dataset for graph-vs-vector evaluation gate

## Status
Accepted (2026-05-13). Shipped in commit `c8047ca`, tick 107 IMPL.

## Context
QKG's QRCD eval (MAP@10) measures single-hop retrieval quality. There was no
systematic benchmark for **multi-hop reasoning** — queries requiring 2–3 graph
traversal steps (e.g. root → verse → typed-edge → related verse) that are the
primary differentiator of graph-backed retrieval over pure vector RAG.

Without such a benchmark the claim "graph methods outperform vector RAG" was
architectural intuition, not measured evidence. Adaptive-routing decisions and
future retrieval improvements lacked a concrete gate metric.

## Decision
Create `data/multihop_bench.jsonl` — 30 multi-hop benchmark questions, 10 per
difficulty tier (2-hop, 3-hop, complex), covering:

- ArabicRoot → Verse → RELATED_TO traversal
- SemanticDomain → Verse → typed edge (SUPPORTS/QUALIFIES/CONTRASTS)
- SIMILAR_PHRASE (mutashabihat) path-finding
- Wujuh polysemy → morphological pattern → Verse
- ReasoningTrace mining (recall_similar_query playback)
- Code-19 arithmetic traversal

Each question carries: `question`, `expected_verse_ids`, `hop_count`, `tool_path`,
`notes`. The file gates future retrieval improvements: a tool sequence that
recovers `expected_verse_ids` within `hop_count` calls passes.

## Consequences
- **Positive:** Provides a concrete go/no-go gate for graph-first retrieval
  improvements (e.g. `from_neo4j_crawl_single_shot_vector_traversal`,
  `rerun_hipporag_after_query_reembed`).
- **Positive:** Exposes which hop types QKG handles well vs. poorly — directs
  future research priorities.
- **Positive:** 30-question scale is runnable in ~5 min; small enough for CI-style
  gating.
- **Neutral:** Produced with DONE_WITH_CONCERNS — questions need human review
  before being used as a hard gate (see `data/ralph_agent_build_multihop_benchmark.md`).
- **Neutral:** `expected_verse_ids` are best-effort from graph inspection, not
  human-verified ground truth. Treat as soft reference until audited.
- **Negative:** No automated runner yet. Running the bench requires wiring
  `multihop_bench.jsonl` into an eval harness (a follow-on task).

## Cross-references
- Source: commit `c8047ca`, task `build_multihop_benchmark`
- Files: `data/multihop_bench.jsonl`, `data/ralph_agent_build_multihop_benchmark.md`
- Related eval: `eval_v1.py`, `eval_ablation_retrieval.py`
- Proposed by: ralph IMPL tick 107
