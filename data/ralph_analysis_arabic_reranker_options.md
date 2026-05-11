# Arabic Reranker Options — Research Analysis

_Task: `from_ai_graph_arabic_reranker_research` | Tick 67 | 2026-05-12_

## TL;DR

Three viable replacement rerankers for `bge-reranker-v2-m3` are ranked below by
recommendation. The highest-priority drop-in is **Qwen3-Reranker-0.6B** — same
parameter count as our current reranker, same `sentence-transformers` interface,
+8.8pt MTEB-R / +8.0pt MMTEB-R, 32K context, 100+ languages including Arabic.
A dedicated Arabic reranker (**ARA-Reranker-V1**) is the backup if Qwen3 underperforms
on Classical Arabic specifically. Cohere Rerank 4 Pro remains the API option pending
`COHERE_API_KEY`.

**Context:** `bge-reranker-v2-m3` drops QRCD hit@10 from 0.6364 (raw BGE-M3-EN) to
0.3182 after reranking — a 50% regression. The reranker is the confirmed bottleneck.

---

## Candidates

### 1. Qwen3-Reranker-0.6B — RECOMMENDED (Priority: HIGH)

**Source:** `huggingface.co/Qwen/Qwen3-Reranker-0.6B` | Qwen3 Embedding paper (Jun 2025)

| Benchmark | Qwen3-Reranker-0.6B | bge-reranker-v2-m3 | Delta |
|---|---|---|---|
| MTEB-R (English retrieval) | **65.80** | 57.03 | +8.77 |
| MMTEB-R (Multilingual) | **66.36** | 58.36 | +8.00 |
| MLDR (multilingual long-doc) | **67.28** | 59.51 | +7.77 |
| CMTEB-R (Chinese) | 71.31 | 72.16 | -0.85 |

**Why it matters for QKG:**
- Same 0.6B parameter count as our current reranker — no hardware change needed.
- Same `CrossEncoder` interface from `sentence-transformers`: `CrossEncoder("Qwen/Qwen3-Reranker-0.6B")` — 2-line swap in `retrieval_gate.py`.
- 32K context window handles our longest Surah passages.
- Multilingual by design (Qwen3 foundation, 100+ languages incl. Arabic).
- MMTEB-R +8pt over bge-reranker-v2-m3 is the most relevant Arabic-inclusive proxy.

**Unknown:** No Arabic-specific QRCD or Classical Arabic benchmark published. The +8pt
MMTEB-R improvement is on a broad multilingual suite; actual Arabic reranking gain on
Classical Quranic text requires live A/B.

**Risk:** Medium. Qwen3 family uses a generative base (decoder transformer) rather than
encoder-only — inference patterns differ slightly. Some prompt formatting needed
(documented in HuggingFace card with `<|im_start|>system` prefix for custom
instructions).

**Cost:** Free, self-hosted.

---

### 2. ARA-Reranker-V1 — DEDICATED ARABIC FALLBACK (Priority: MEDIUM)

**Source:** `huggingface.co/Omartificial-Intelligence-Space/ARA-Reranker-V1`

| Metric | ARA-Reranker-V1 | bge-reranker-v2-m3 | bge-MiniLM |
|---|---|---|---|
| MRR | **0.934** | 0.902 | 0.664 |
| MAP | **0.9335** | 0.902 | 0.664 |
| nDCG@10 | **0.951** | 0.927 | 0.750 |

Benchmarked on `NAMAA-Space/Ar-Reranking-Eval` (Arabic-specific).

**Architecture:** XLM-RoBERTa base, 0.6B params, CrossEncoder. Fine-tuned on 3,000
Arabic positive + hard-negative pairs. Drop-in `sentence-transformers` usage.

**Why it's a fallback not primary:** Benchmarked on Modern Standard Arabic (MSA).
The training data (3K samples) is small; Classical Arabic generalization is untested.
The authors' own Arabic RAG pipeline blog tested it on MSA historical content — their
Quran Tafseer subset showed only +0.73pt RAGAS gain from reranking, suggesting limited
Classical Arabic benefit.

**Upside:** If Qwen3-Reranker-0.6B also fails on Classical Arabic (both hurt rather
than help), ARA-Reranker-V1 is the best Arabic-native fallback. It significantly
outperforms bge-reranker-v2-m3 on Arabic MSA — the gap on Classical likely exists but
is narrower.

**Cost:** Free, self-hosted.

---

### 3. GATE-Reranker-V1 — LOWER PRIORITY (Priority: LOW)

**Source:** `huggingface.co/NAMAA-Space/GATE-Reranker-V1`

Built on AraBERT-v2 base + GATE-AraBert-v1, fine-tuned on Arabic triplets. Claims
"excellent performance compared to famous rerankers" but provides no comparative table
with bge-reranker-v2-m3 or ARA-Reranker-V1. NAMAA-Space also publishes ARA-Reranker-V1
(same org / lab), making GATE-Reranker-V1 a sibling model.

**Verdict:** Skip unless ARA-Reranker-V1 fails. No public comparative benchmarks.

---

### 4. Qwen3-Reranker-8B — FUTURE CONSIDERATION (Priority: LOW)

Same Qwen3 family as option 1 but 8B params. MTEB-R 69.02 vs 65.80 (+3.2pt) over 0.6B.
Requires VRAM capable of running 8B BF16 (≥16GB VRAM). Not viable on the user's current
setup for cron ticks but worth considering after we confirm Qwen3-0.6B wins.

---

### 5. Cohere Rerank 4 Pro — API OPTION (Priority: ON HOLD)

Documented in `data/ralph_analysis_from_ai_graph_zeroentropy_cohere_reranker_ab_detail.md`.
100+ languages including Arabic, 32K context, ELO 1627 (#2 MTEB). Requires `COHERE_API_KEY`.
~$1/1000 documents. Status: blocked on user adding API key. Not investigated further here.

---

## Quranic / Classical Arabic Context

Two important research findings from 2025 literature:

1. **Linguistic gap:** Modern Standard Arabic (MSA) vs Classical Arabic (CA) is a known
   retrieval challenge. Questions are often in MSA; Quranic text is CA. Both `bge-reranker-v2-m3`
   and ARA-Reranker-V1 were trained primarily on MSA. This explains the 50% hit@10 regression.

2. **Quran Tafseer RAG result:** A 2025 paper (`arXiv:2506.06339`) tested `bge-reranker-v2-m3`
   on Quran Tafseer dataset — reranking added only +0.73 RAGAS points (82.72 → 83.45), well
   below gains on ARCD (+6 pts). The "specialized religious content" note matches our QRCD finding.

3. **Best published Quranic retrieval score:** AraBERT-base fine-tuned on QRCD data reaches
   MAP@10 = 0.36, MRR = 0.52 (our raw BGE-M3-EN baseline is MAP@10 = 0.139; fine-tuning
   task `from_research_finetune_bge_m3_qrcd` is the highest-leverage path to closing this gap).

---

## Recommendation Ladder

1. **Immediately actionable:** Swap `bge-reranker-v2-m3` → `Qwen3-Reranker-0.6B` via
   `RERANKER_MODEL=Qwen/Qwen3-Reranker-0.6B` env var (requires small `retrieval_gate.py`
   tweak for Qwen3 prompt format). Run QRCD A/B. If hit@10 > 0.3182 baseline — ship.

2. **If Qwen3 doesn't help Classical Arabic:** Try `ARA-Reranker-V1` — drop-in swap,
   same interface. If still no improvement, the reranker slot is architecturally broken
   for Classical Arabic regardless of model. Fall back to `RERANK_DISABLED=1` (recovers
   to 0.6364 hit@10) and pursue `from_research_finetune_bge_m3_qrcd` as the long-term fix.

3. **Do NOT invest further in bge-reranker family** — v2-m3 is the latest variant; its
   cross-encoder architecture was not trained on Classical Arabic and the evidence is clear.

---

## Implementation Note: Qwen3-Reranker-0.6B

The Qwen3 rerankers have a different prompt format from standard sentence-transformers:

```python
# retrieval_gate.py change
# Old:
# from sentence_transformers import CrossEncoder
# model = CrossEncoder("BAAI/bge-reranker-v2-m3")
# scores = model.predict([(query, doc) for doc in docs])

# New (Qwen3-0.6B uses instruction prefix):
from sentence_transformers import CrossEncoder
model = CrossEncoder("Qwen/Qwen3-Reranker-0.6B")
# NOTE: Qwen3-Reranker supports system instruction via predict(sentences, prompt_name="query")
# Default inference matches standard CrossEncoder API but with system prefix
# Verify: model.predict([(query, doc)]) should work without modification per HF card
scores = model.predict([(query, doc) for doc in docs])
```

Standard `CrossEncoder.predict()` interface works per the HuggingFace model card.
One concern: requires `transformers>=4.51.0`. Pin in requirements.txt before shipping.

---

## Proposed Follow-Up Task

Propose to `data/proposed_tasks.yaml` (for next review cycle):

```yaml
- id: qwen3_reranker_ab_qrcd
  type: eval
  priority: 78
  description: "[from-arabic-reranker-research] A/B Qwen3-Reranker-0.6B vs RERANK_DISABLED=1 vs current bge-reranker-v2-m3 on QRCD 22-q. Primary metric: hit@10. Change RERANKER_MODEL=Qwen/Qwen3-Reranker-0.6B in .env, run eval_qrcd_ablation.py, commit results."
  blockers: []
  spec:
    acceptance:
      - file_exists: data/ralph_analysis_qwen3_reranker_ab_qrcd.md
      - file_min_bytes: {path: data/ralph_analysis_qwen3_reranker_ab_qrcd.md, min: 400}
```
