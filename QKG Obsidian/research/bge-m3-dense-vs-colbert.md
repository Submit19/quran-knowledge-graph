---
type: research
status: done
priority: 68
tags: [research/retrieval, research/embeddings, research/benchmarks]
source: data/research_bge_m3_dense_vs_colbert.md
date_added: 2026-05-10
---

# BGE-M3 Dense vs ColBERT Mode for QKG

## TL;DR
- On MIRACL Arabic, BGE-M3 multi-vector (ColBERT mode) beats dense by only +1.2 nDCG@10 (79.6 vs 78.4). The all-modes hybrid adds +1.8. Small lift, not the 5–15 points hoped for.
- No public benchmark tests BGE-M3 ColBERT mode on Quranic / classical Arabic. QRCD SOTA uses fine-tuned AraBERT/CamelBERT ensembles (best MAP@10 ~0.3128) — gap is domain adaptation, not retrieval architecture.
- **Decision: skip ColBERT POC. Fine-tune BGE-M3 dense on QRCD/Tafsir pairs first.** Fine-tuning closes more of the 0.139 → 0.36 gap with less infra disruption.
- Neo4j 2026.01 has no native multi-vector / late-interaction index. ColBERT must live outside Neo4j as Python-side rerank over Neo4j HNSW top-100 candidates.

## Key findings
- **Published numbers** (BGE-M3 paper, MIRACL Arabic): dense 78.4 / multi-vec 79.6 / all-modes 80.2. On Arabic RAG study, BGE-M3 dense scored 82.72 on Quran Tafseer subset — beating Arabic-specific models.
- **Storage cost**: ColBERT vecs shape `(n_tokens, 1024)` in bf16. For 6,234 verses at ~80 tokens avg: ~160 KB/verse → ~1 GB total vs ~25 MB dense-only. Trivial at our scale.
- **Latency**: top-100 ColBERT MaxSim rerank costs ~25 ms CPU (maxsim-cpu / mixedbread). Negligible vs current cross-encoder rerank pass. Adding ColBERT on top of the existing cross-encoder would be redundant.
- **Cross-encoder already covers it**: `bge-reranker-v2-m3` already provides late-interaction-like fine-grained scoring on top-K candidates. An additional ColBERT layer is redundant at our scale.
- **Fine-tuning path** (CustomIR pattern, arxiv 2510.21729): unsupervised fine-tune BGE-M3 dense on synthetic QRCD-style query/verse pairs. Arabic-specific tuning shows 5–10% gains. This is the correct next step.
- **Revisit ColBERT if**: fine-tuned dense plateaus below MAP@10 = 0.25, or cross-encoder rerank is removed for cost reasons.

## Action verdict
- ❌ Skip — ColBERT POC for now. Expected lift (~1–2 nDCG) doesn't justify infra overhead when cross-encoder is already in place.
- 🔬 Research deeper — fine-tune BGE-M3 dense on QRCD train set / synthetic Tafsir query pairs. Expected +5–10% Arabic gain.
- 🔬 Research deeper — quantization on/off A/B on our actual vector index to confirm "slightly decreased accuracy" is negligible.

## Cross-references
- [[eval-qrcd-report]] — QRCD baseline numbers (MAP@10 = 0.139) that fine-tuning should improve
- [[vector-graphrag-neo4j-docs]] — Neo4j vector index constraints (one vector per node, no native multi-vector)
- [[research-2026-04-27-stack-alternatives]] — original proposal to evaluate BGE-M3 mode tradeoffs
- Source: `repo://data/research_bge_m3_dense_vs_colbert.md`
