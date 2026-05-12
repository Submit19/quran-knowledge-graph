---
type: decision
adr: 0043
status: proposed
date: 2026-05-13
tags: [decision, reranker, eval, cohere, retrieval]
supersedes: none
---

# ADR-0043 — Cohere reranker A/B evaluation plan (COHERE_API_KEY required)

## Status
Proposed (2026-05-13). Design doc shipped in commit `ea6053a`, tick 113 IMPL.
Decision pending actual QRCD eval results.

## Context
QKG uses `BAAI/bge-reranker-v2-m3` as the default cross-encoder reranker. The
prior ablation showed the reranker helps BROAD queries but hurts CONCRETE ones
(ADR-0024). The 2-profile adaptive gate (ADR-0032) partially addresses this.

Research (task `from_ai_graph_arabic_reranker_research`) identified Qwen3-Reranker
as a strong local alternative (ADR-0030). An additional candidate is Cohere
Rerank v3 (API-based), which has strong multilingual benchmarks and avoids
local GPU overhead.

## Decision
Defer the final reranker choice until a controlled A/B is run. Design doc
(`data/ralph_agent_from_ai_graph_cohere_rerank_ab_impl.md`) specifies:

- `RERANKER_BACKEND=cohere` env flag in `retrieval_gate.py`
- `eval_qrcd_reranker_ab.py` script structure for A/B comparison
- Decision gate: **promote Cohere only if hit@10 > bge-reranker-v2-m3 baseline
  (0.6364) on the QRCD benchmark**
- Risk register: API latency (+50–150ms/query), cost ($1/1K queries), key mgmt

The plan is intentionally staged: the design doc + eval script are the
deliverable; the actual run requires `COHERE_API_KEY` to be set.

## Consequences
- **Positive:** Avoids premature optimization — only switches if measured lift.
- **Positive:** Reduces local GPU pressure if Cohere wins (cloud inference).
- **Neutral:** Results table in design doc has placeholders; no measurement yet.
- **Negative:** Requires operator to supply COHERE_API_KEY and run eval manually.
- **Negative:** API dependency adds latency and ongoing cost if adopted.

## Cross-references
- Source: commit `ea6053a`, task `from_ai_graph_cohere_rerank_ab_impl`
- Files: `data/ralph_agent_from_ai_graph_cohere_rerank_ab_impl.md`
- Related: ADR-0024 (adaptive routing over global reranker disable),
  ADR-0030 (Qwen3-Reranker candidate), ADR-0032 (2-profile gate)
- Proposed by: ralph IMPL tick 113
