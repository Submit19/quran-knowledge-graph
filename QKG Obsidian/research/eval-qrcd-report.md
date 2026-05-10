---
type: research
status: done
priority: 88
tags: [research/eval, research/retrieval, research/benchmarks]
source: EVAL_QRCD_REPORT.md
date_added: 2026-05-10
---

# QRCD Benchmark Evaluation Report

## TL;DR
- BGE-M3-EN is **5–94× better than MiniLM** on every QRCD metric — confirms MiniLM was the wrong default for Arabic queries.
- BGE-M3-EN (MAP@10 = 0.139) **beats BGE-M3-AR** counter-intuitively: Khalifa's English translation includes parenthetical clarifications that bridge the lexical gap to classical Arabic questions better than bare Hafs Arabic text.
- We're at ~38% of AraBERT-base (MAP@10 = 0.36), which was fine-tuned on QRCD. Headroom is large; fine-tuning BGE-M3 on QRCD/Tafsir pairs is the primary gap-closing path.
- Full-agent loop pilot (5 items) scored 0/5 hit@10 — agent over-calls tools and re-fetches rather than synthesizing available context.

## Key findings
- **Benchmark**: QRCD v1.1 test split, 22 unique Arabic questions, 1,218 total gold verses. Pure retrieval (no agent, no reranking).

| Metric | MiniLM | BGE-M3-EN | BGE-M3-AR |
|--------|--------|-----------|-----------|
| hit@5 | 0.091 | **0.545** | 0.455 |
| hit@10 | 0.091 | **0.636** | 0.545 |
| MAP@10 | 0.028 | **0.139** | 0.108 |
| MRR | 0.073 | **0.418** | 0.346 |

- **Cross-encoder reranker** (`bge-reranker-v2-m3`) adds +0.05–0.10 MAP@10 on top (ablation in `eval_ablation_retrieval.py`). Legacy English-only reranker *actively hurt* Arabic queries (hit@10 0.32 → 0.55 after switch).
- **Domain adaptation gap**: QRCD SOTA uses CamelBERT-tydi-tafseer + AraBERTv02 ensembles reaching MAP@10 = 0.3128 (vs our 0.139). Gap is domain fine-tuning, not retrieval architecture — see [[bge-m3-dense-vs-colbert]] for decision to skip ColBERT.
- **Agent loop failure modes** (pilot): over-calls `semantic_search` when `get_verse` would suffice; doesn't recognize when context is already sufficient; no built-in "I already retrieved this" detector. Matches the sufficiency-gate gap in [[agentic-graphrag-yt-patterns]].
- **Eval framing caveat**: uses union-of-gold per question (free-form citation matching), not passage extraction spans. 22 questions is small; plan to re-run on QRCD-v3 (Quran-QA 2023) when time permits.

## Action verdict
- ✅ Adopt — BGE-M3-EN is the default index (already done). Multilingual reranker is the default (already done).
- 🔬 Research deeper — fine-tune BGE-M3 dense on synthetic QRCD-style query/verse pairs (CustomIR pattern). Expected: +5–10% Arabic-specific gain. See [[bge-m3-dense-vs-colbert]].
- 🔬 Research deeper — fix agent-loop QRCD pilot: add sufficiency gate (from [[agentic-graphrag-yt-patterns]]), reduce tool over-calling.
- 🔬 Research deeper — rerun on QRCD-v3 (larger test set) for statistical confidence.

## Cross-references
- [[bge-m3-dense-vs-colbert]] — ColBERT mode evaluation and fine-tuning path
- [[hipporag-negative-result]] — PPR retrieval that was also benchmarked against QRCD
- [[agentic-graphrag-yt-patterns]] — sufficiency gate that would fix agent pilot 0/5 result
- Source: `repo://EVAL_QRCD_REPORT.md`
