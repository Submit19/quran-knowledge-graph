---
type: decision
adr: 0024
status: accepted
date: 2026-05-12
tags: [decision, eval, retrieval]
supersedes: none
---

# ADR-0024 — Keep reranker on, fix per-bucket via adaptive routing (NOT global disable)

## Status
Accepted (2026-05-12). Active.

## Context
A/B testing and ablation studies (commits `fb3b19a`, `d69a513`, `1c0c2d2`) revealed that `bge-reranker-v2-m3` drops hit@10 by ~50% on Arabic queries (0.6364→0.3182) and by similar margins on abstract-concept queries in English. The synthesis document `research_synthesis_2026-05-12.md` (derived from 6+ independent research sources) confirmed the reranker is systematically harmful. An initial impulse was to globally disable reranking (`RERANK_DISABLED=1`). However, closer analysis shows the harm is not uniform: reranking helps on some query types (concrete-noun retrieval) and hurts on others (abstract concepts, non-English). Rather than disable globally, the decision is to keep the reranker on and route query types to use it adaptively — per-bucket decision. This requires the pending 50-question bucketed eval to confirm lift per profile.

## Decision
Do NOT globally disable reranking. Instead, build an adaptive routing layer (proposed `from_adaptive_routing_design` p80, `from_adaptive_routing_2profile_spike` p72) that routes queries by type: BROAD (use reranker) vs NOT-BROAD (skip reranker). The 50-question bucketed eval (`from_adaptive_routing_50q_bucketed_eval` p85) will validate per-profile lift. Keep `bge-reranker-v2-m3` in the stack; tune its usage per query profile.

## Consequences
- **Positive:** Preserves reranker benefit on query types where it helps. Avoids losing 5-10 points on concrete-noun queries. Maintains architectural coherence (reranker is a valid tool, just needs smart gating).
- **Negative:** Requires building and validating the adaptive router first (50q eval + design + 2-profile spike = ~40-60 hours). More complex than global disable. If adaptive routing fails, the reranker problem remains.
- **Neutral:** Immediate workaround for production is `RERANK_DISABLED=1` if needed; toggle via env var while bucketed eval is running.

## Cross-references
- Source evidence: commits `fb3b19a` (disable baseline), `d69a513` (A/B analysis), `1c0c2d2` (ablation), `6f86187` (synthesis) — `data/research_synthesis_2026-05-12.md` lines 5, 13, 35–43
- Related: [[0021-4to1-impl-research-ratio]], [[0022-blocked-on-research-field]], `repo://data/proposed_tasks.yaml` (adaptive_routing tasks)
