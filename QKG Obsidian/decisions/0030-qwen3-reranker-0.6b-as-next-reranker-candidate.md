---
type: decision
adr: 0030
status: proposed
date: 2026-05-12
tags: [decision, retrieval, reranker, arabic, eval]
supersedes: none
---

# ADR-0030 — Qwen3-Reranker-0.6B as next reranker candidate (A/B eval gated)

## Status
Proposed (2026-05-12). Pending A/B eval (`qwen3_reranker_ab_qrcd`, p78 in ralph_backlog).

## Context
`bge-reranker-v2-m3` is the current reranker in `retrieval_gate.py`. Benchmarking revealed a severe regression on Arabic queries: QRCD hit@10 drops from 0.6364 (raw BGE-M3-EN retrieval) to 0.3182 after reranking — a 50% regression. This makes the reranker the confirmed bottleneck for Arabic question answering.

Task `from_ai_graph_arabic_reranker_research` (commit `4ae0391`, tick 67) surveyed reranker alternatives. Key finding: **Qwen3-Reranker-0.6B** (Qwen/Qwen3-Reranker-0.6B, HuggingFace) outperforms bge-reranker-v2-m3 on every multilingual benchmark:

| Benchmark | Qwen3-Reranker-0.6B | bge-reranker-v2-m3 | Delta |
|---|---|---|---|
| MTEB-R (English) | 65.80 | 57.03 | +8.77 |
| MMTEB-R (Multilingual) | 66.36 | 58.36 | +8.00 |
| MLDR (long-doc multilingual) | 67.28 | 59.51 | +7.77 |

Same 0.6B parameter count, same `CrossEncoder` interface from `sentence-transformers`. A 2-line swap in `retrieval_gate.py`. 32K context. 100+ languages. Free, self-hosted.

Secondary fallback candidate: **ARA-Reranker-V1** (Omartificial-Intelligence-Space/ARA-Reranker-V1, MRR 0.934 vs 0.902 for bge-reranker-v2-m3 on dedicated Arabic benchmark). Use if Qwen3 underperforms on Classical Quranic Arabic specifically.

## Decision
Gate the swap on a live QRCD A/B eval (`qwen3_reranker_ab_qrcd`). If Qwen3-Reranker-0.6B matches or exceeds bge-reranker-v2-m3 on QRCD hit@10, swap it in as the default in `pipeline_config.yaml` and `retrieval_gate.py`. If Qwen3 underperforms despite MMTEB-R gains (Classical Arabic is an outlier domain), fall back to ARA-Reranker-V1 for the Arabic query path.

## Consequences
- **Positive:** Expected ~8pt MMTEB-R gain on multilingual queries; could recover the 50% Arabic regression.
- **Positive:** Drop-in swap — no schema change, no data pipeline change.
- **Positive:** 32K context handles long Surah passages that bge-reranker-v2-m3 truncates.
- **Negative:** Qwen3 uses a generative decoder base, not encoder-only. Inference latency may differ; requires prompt formatting (`<|im_start|>system` prefix as per HuggingFace card).
- **Negative:** No QRCD or Classical Arabic benchmark published for Qwen3 yet — A/B is mandatory before committing.
- **Neutral:** ARA-Reranker-V1 as fallback adds a second model to maintain if adopted.

## Cross-references
- Source evidence: commit `4ae0391`, deliverable `data/ralph_analysis_arabic_reranker_options.md`
- Eval task: `qwen3_reranker_ab_qrcd` (p78, ralph_backlog.yaml)
- Related: [[0003-multilingual-reranker]], `repo://retrieval_gate.py`
- Proposed by: ralph IMPL tick 67
