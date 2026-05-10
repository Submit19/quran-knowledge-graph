# Research: BGE-M3 dense vs ColBERT mode for QKG

_2026-05-10 · spawned by ralph research tick · QKG retrieval question_

## TL;DR
- On MIRACL **Arabic**, BGE-M3 multi-vector beats dense by **+1.2 nDCG@10** (79.6 vs 78.4); the all-modes hybrid adds **+1.8** (80.2). Small lift, not the 5–15 point gap published benchmarks suggest elsewhere.
- No public benchmark directly tests BGE-M3 ColBERT mode on Quranic / classical Arabic. QRCD literature still uses fine-tuned AraBERT/CamelBERT ensembles (best MAP@10 ~0.31) — none use multi-vector.
- ColBERT MaxSim rerank over top-100 is cheap: **5–25 ms** with optimized libraries (maxsim-cpu, PLAID), **50–100 ms** with naive PyTorch CPU.
- **Neo4j 2026.01 has no native multi-vector / late-interaction index.** One vector per node, max 4096d. ColBERT must live outside Neo4j (Python-side rerank).
- **Recommendation: skip ColBERT POC for now. Fine-tune BGE-M3 dense on QRCD/Tafsir pairs first** — that path closes more of the 0.139 → 0.36 gap with less infra disruption.

## Findings

### 1. Published benchmarks
**BGE-M3 paper (arxiv 2402.03216v3) — MIRACL nDCG@10:**
- Arabic: dense 78.4 / sparse 67.1 / **multi-vec 79.6** / dense+sparse 79.6 / all 80.2
- 18-lang avg: dense 67.8 / sparse 53.9 / **multi-vec 69.0** / all 70.0
- MLDR long-doc avg: dense 52.5 / sparse 62.2 / multi-vec 57.6 / all 65.0 (sparse wins on long docs)

**Arabic RAG study (arxiv 2506.06339):** BGE-M3 dense scored 70.99 avg / **82.72 on Quran Tafseer**, beating Arabic-specific models (Arabic-Triplet-Matryoshka 66.46). ColBERT mode not tested.

**QRCD / Quran QA 2023 SOTA (arxiv 2508.06971):** ensemble of CamelBERT-tydi-tafseer + AraBERTv02 reached MAP@10=0.3128. No BGE-M3, no ColBERT. Our 0.139 baseline is below this — gap is domain adaptation, not retrieval architecture.

### 2. Implementation cost
```python
from FlagEmbedding import BGEM3FlagModel
m = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
out = m.encode(texts, return_dense=True, return_colbert_vecs=True)
score = m.colbert_score(out['colbert_vecs'][q], out['colbert_vecs'][d])
```
**Storage:** per-doc shape `(n_tokens, 1024)` in bf16. For 6,234 verses ~80 tokens avg → ~80×1024×2 B = ~160 KB/verse → **~1 GB total** (vs ~25 MB dense-only). Trivial at our scale.

### 3. Latency
For 6K-doc corpus with dense-prefilter→top-100→ColBERT-rerank pattern:
- maxsim-cpu (mixedbread): **~5 ms** for ~1K docs CPU
- PLAID/ColBERTv2 GPU: **tens of ms** even at 140M passages
- Naive PyTorch CPU: 50–100 ms for 1K docs
- p95 add-on for top-100 rerank: **~25 ms** (Medium benchmarks)

Practical budget on our scale: **<30 ms added query latency**. Negligible vs current cross-encoder rerank pass.

### 4. Neo4j compatibility
Neo4j 2026.01 vector indexes: **one vector per node, max 4096d**, no multi-vector / late-interaction primitive. The 2026.01 update added multi-label/relationship indexes with filter properties, not multi-vector storage. **Pattern (b) full ColBERT index in Neo4j is not viable.** Only workable pattern: **(a) Neo4j HNSW dense top-100 → Python-side MaxSim rerank**, with ColBERT vecs stored either as a serialized BLOB property on Verse nodes or in a sidecar parquet/numpy file keyed by verse_id.

### 5. Recommendation for QKG
**Skip ColBERT for now.** Reasons:
1. Expected lift on Arabic is only ~1–2 nDCG points (per BGE-M3's own paper) — not the 5–15 we hoped for.
2. Our 0.139 → 0.36 gap is *domain adaptation* (literature uses CamelBERT-tafseer fine-tunes), not late interaction.
3. Cross-encoder bge-reranker-v2-m3 already provides late-interaction-like fine-grained scoring on top-K. Adding ColBERT layer is redundant.
4. Better next experiment: **fine-tune BGE-M3 dense** on synthetic QRCD-style query/verse pairs (CustomIR pattern, arxiv 2510.21729) — small-model fine-tunes show +2.3 Recall@10 and Arabic-specific tuning shows 5–10% gains.

Revisit ColBERT only if (a) fine-tuned dense plateaus below 0.25 MAP, or (b) cross-encoder rerank is removed for cost reasons.

## Integration sketch (if "try")
```python
# 1. Index build (one-time, ~30 min on 6K verses)
for v in verses:
    cb = model.encode(v.text_en, return_colbert_vecs=True)['colbert_vecs'][0]
    np.save(f"colbert/{v.id}.npy", cb.astype(np.float16))  # ~160KB each

# 2. Query path
candidates = neo4j.dense_topk(query_emb, k=100)            # existing path
q_cb = model.encode(query, return_colbert_vecs=True)['colbert_vecs'][0]
scored = [(c, maxsim(q_cb, np.load(f"colbert/{c.id}.npy"))) for c in candidates]
top = sorted(scored, key=lambda x: -x[1])[:20]
# 3. existing cross-encoder rerank on top
```
Use `maxsim-cpu` (mixedbread) for the maxsim call. Eval against current MAP@10=0.139 on QRCD before keeping.

## Bibliography
- BGE-M3 paper: https://arxiv.org/html/2402.03216v3
- Optimizing RAG Pipelines for Arabic: https://arxiv.org/html/2506.06339
- Two-Stage Quranic QA (QRCD SOTA): https://arxiv.org/html/2508.06971
- maxsim-cpu / mixedbread: https://www.mixedbread.com/blog/maxsim-cpu
- BGE-M3 HF discussion on ColBERT vec usage: https://huggingface.co/BAAI/bge-m3/discussions/16
- Neo4j vector indexes (Cypher manual): https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/
- CustomIR (unsupervised dense fine-tune): https://arxiv.org/abs/2510.21729
- bge-m3-onnx (storage format reference): https://github.com/yuniko-software/bge-m3-onnx
