---
type: decision
adr: 0003
status: accepted
date: 2026-04-28
tags: [decision, retrieval, reranking]
supersedes: none
---

# ADR-0003 — Use multilingual reranker (BAAI/bge-reranker-v2-m3) over English-only

## Status
Accepted (2026-04-28). Active.

## Context
`retrieval_gate.py` applies a cross-encoder reranker on top of the initial vector retrieval pass. The legacy reranker was `cross-encoder/ms-marco-MiniLM-L-6-v2`, trained exclusively on English MS MARCO passages. Ablation analysis in `eval_ablation_retrieval.py` (commit `Nixon: argue-each-component-out`, 2026-04-28) revealed this model was actively harming retrieval quality on Arabic queries: it scored Arabic verse text vs. an Arabic question without any Arabic training signal, producing near-random reranking. The ablation quantified the damage as a 32-point drop in hit@10 on Arabic QRCD items compared to running with no reranker at all.

## Decision
Replace `cross-encoder/ms-marco-MiniLM-L-6-v2` with `BAAI/bge-reranker-v2-m3` as the default reranker. The switch is env-gated (`RERANKER_MODEL`) so the legacy model can still be selected for English-only workloads if needed.

## Consequences
- **Positive:** hit@10 on Arabic queries rises from 0.32 (with English-only reranker) to 0.55. Multilingual model handles both English and Arabic verse text vs. Arabic/English query pairs correctly.
- **Negative:** Slightly heavier model than MiniLM reranker; cold-start adds latency. Still self-hosted, no API dependency.
- **Neutral:** The ablation finding (English-only reranker as a net negative on Arabic) should be documented prominently as a warning against reverting this decision.

## Cross-references
- Source evidence: `repo://CLAUDE.md` (`retrieval_gate.py` subsystem note); `eval_ablation_retrieval.py` results
- Related: [[0002-bge-m3-over-minilm]], [[0004-skip-colbert]]
