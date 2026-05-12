---
type: decision
adr: 0032
status: accepted
date: 2026-05-12
tags: [decision, retrieval, reranker, adaptive-routing, architecture]
supersedes: none
---

# ADR-0032 — 2-profile adaptive reranker gate: BROAD query profile only

## Status
Accepted (2026-05-12). Shipped in commit `672cc68`, tick 73 IMPL.

## Context
ADR-0024 established the principle: keep reranker on but route per query type. Task
`from_adaptive_routing_2profile_spike` (p72) was the implementation spike. The QRCD
ablation data showed a clear split:

- **BROAD queries** (open-ended, multi-concept): reranker helps — precision uplift
- **All other profiles** (STRUCTURED, ABSTRACT, CONCRETE, ARABIC): reranker hurts —
  hit@10 drops ~50% on Arabic; similar regressions on abstract/concept queries

The 2-profile gate is the minimal viable configuration: one condition, one branch.

## Decision
In `retrieval_gate.py`, gate reranking on `classify_query()` output:
- `BROAD` → reranker ON (bge-reranker-v2-m3)
- All other profiles → skip reranker (return candidates as-is from retrieval stage)

`classify_query()` was extended with `arabic` and `broad` bucket detection. The
implementation is a single if/else branch at the top of the rerank path — zero extra
latency on non-BROAD queries (reranker model not loaded for those calls).

QRCD ablation evidence: -50% hit@10 on non-BROAD queries with reranker on. That
regression is now eliminated for the majority of query traffic.

## Consequences
- **Positive:** Eliminates -50% Arabic hit@10 regression without losing BROAD uplift.
- **Positive:** Zero latency cost on non-BROAD queries (model not invoked).
- **Positive:** The `classify_query()` extension is reusable for future routing decisions.
- **Negative:** BROAD boundary is heuristic — complex queries that are partially BROAD
  may be miscategorised. Calibration against 50q_bucketed_eval data is pending.
- **Negative:** Qwen3-Reranker A/B (`qwen3_reranker_ab_qrcd`, ADR-0030) still needed;
  2-profile gate is a harm-reduction measure, not a quality improvement.
- **Neutral:** When Qwen3 A/B lands, the BROAD-only gate remains the correct scope —
  profile scope and reranker model are orthogonal decisions.

## Cross-references
- Source evidence: commit `672cc68`, deliverable `data/ralph_agent_from_adaptive_routing_2profile_spike.md`
- QRCD ablation: `data/qrcd_ablation.json`
- Related: [[0024-keep-reranker-adaptive-routing-not-global-disable]], [[0030-qwen3-reranker-0.6b-as-next-reranker-candidate]]
- Proposed by: ralph IMPL tick 73
