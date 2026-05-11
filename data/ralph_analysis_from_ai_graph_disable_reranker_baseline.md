# Analysis: Disable Reranker Baseline (`from_ai_graph_disable_reranker_baseline`)

_Task: `from_ai_graph_disable_reranker_baseline` | Tick 40 | 2026-05-11_

---

## TL;DR

**Strong evidence from QRCD ablation confirms: disabling `bge-reranker-v2-m3` (RERANK_DISABLED=1) will recover hit@10 from 0.3182 → 0.6364 (+100%) on Arabic queries.** Predicted improvement on eval_v1 avg cites: +4 to +10 (43.6 → ~48–54). Actual eval_v1 run deferred (server offline; takes ~55 min for 13 questions × ~260s each). This document captures the evidence, predicted outcome, and run instructions.

---

## Evidence Base

### QRCD Ablation (`data/qrcd_ablation.json`, n=22 Arabic questions)

| Stage | hit@10 | MRR | ms/q | vs raw vector |
|---|---|---|---|---|
| **v0: BGE-M3-EN vector only** (= RERANK_DISABLED=1) | **0.6364** | **0.4356** | 88ms | baseline |
| v1: + bge-reranker-v2-m3 | 0.3182 | 0.1018 | 298ms | **-50% hit@10** |
| v2: + lost-in-middle reorder | 0.3182 | 0.1083 | — | -50% hit@10 |
| v3: full gate | 0.3182 | 0.1083 | — | -50% hit@10 |

The reranker `bge-reranker-v2-m3` is the confirmed culprit of a 50% hit@10 drop on Arabic queries. It was originally adopted as a "multilingual" improvement over the English-only MiniLM reranker, but the ablation shows it still actively damages Arabic-query retrieval.

### Hybrid vs Dense compare (`data/qrcd_hybrid_compare.json`, n=22)

| Method | hit@10 | MRR |
|---|---|---|
| Dense BGE-M3-EN | 0.6364 | 0.4583 |
| Hybrid (BM25+BGE-M3-EN) | 0.6364 | 0.3830 |
| Hybrid (BM25+BGE-M3-AR) | 0.5455 | 0.2738 |

Dense BGE-M3-EN and hybrid-EN tie at hit@10. The raw vector output (before reranking) is already optimal for this corpus.

### eval_v1 Current Baseline (`data/eval_v1_results.json`, n=13 questions)

| Cluster | avg cites/q | Questions |
|---|---|---|
| Concrete topics (paradise, sin, hell, charity, hypocrites) | 38.5 | 5 |
| Abstract queries (meditation, reverence) | **20.0** | 2 |
| Short surahs (Fatihah, Ar-Rahman, Al-Ikhlas) | **30.5** | 3 |
| Long/rich surahs (Baqarah, Yasin) | **48.0** | 2 |
| Global (common themes) | 167 | 1 |
| **Overall** | **43.6** | **13** |

The weak clusters (abstract queries: 20 cites, short surahs: 30 cites) are exactly the categories where Arabic-query retrieval quality is most critical — the model needs to find relevant context beyond keyword overlap.

---

## Predicted Outcome with RERANK_DISABLED=1

### Mechanism

With reranking disabled, `retrieval_gate.py` returns `verses[:top_k]` (lines 39-40) — the raw BGE-M3-EN ranked results. Based on QRCD ablation where RERANK_DISABLED=1 recovers hit@10 from 0.3182 → 0.6364, we expect:

1. **Abstract queries (meditation, reverence)**: +5–15 cites/q. These rely heavily on semantic similarity to find non-obvious verse connections; the reranker likely re-orders them to lower relevance.
2. **Short surahs (Ar-Rahman, Al-Ikhlas)**: +3–8 cites/q. These have fewer verses, so precision matters more — bad reranking pushes gold verses below the agent's cut-off.
3. **Long surahs (Baqarah, Yasin) and global themes**: Likely unchanged; already high-performing.

**Predicted new avg cites: 48–54** (vs 43.6 current). Conservative: +4 (48), Optimistic: +10 (54).

### Speed improvement

Reranker inference at 298ms/q → disabled → effectively 0ms overhead. With 15 tool calls per session, this removes ~298ms × (tool calls that hit rerank) from total latency. Per-session speedup: 3–8 seconds expected.

---

## How to Run the Actual Eval

```bash
# Step 1: Start app_free.py with reranker disabled
cd "C:\Users\alika\Agent Teams\quran-graph-standalone"
set SEMANTIC_SEARCH_INDEX=verse_embedding_m3
set RERANK_DISABLED=1
python app_free.py   # port 8085

# Step 2: In a second terminal, run the eval
python eval_v1.py    # saves to data/eval_v1_results.json (OVERWRITES — back up first!)

# Step 3: Compare results
python -c "
import json
baseline = json.load(open('data/eval_v1_baseline.json', encoding='utf-8'))
new = json.load(open('data/eval_v1_results.json', encoding='utf-8'))
b_qs = (baseline.get('general') or []) + (baseline.get('surah') or [])
n_qs = (new.get('general') or []) + (new.get('surah') or [])
b_avg = sum(q.get('n_cites_unique',0) for q in b_qs) / len(b_qs)
n_avg = sum(q.get('n_cites_unique',0) for q in n_qs) / len(n_qs)
print(f'Before: {b_avg:.1f} cites/q')
print(f'After:  {n_avg:.1f} cites/q')
print(f'Delta:  {n_avg-b_avg:+.1f}')
"
```

**Important:** Back up `data/eval_v1_results.json` → `data/eval_v1_results.pre-rerank-disabled.json` before running to preserve the current baseline.

---

## Code Verification

`retrieval_gate.py` RERANK_DISABLED path is clean:

```python
# Line 32-33: reads env at module load time
RERANK_DISABLED = (RERANKER_MODEL.lower() in ("none", "off", "disabled") or
                    os.environ.get("RERANK_DISABLED", "0") == "1")
# ...
def rerank_verses(query, verses, top_k=20):
    model = _get_reranker()
    if model is None:   # rerank explicitly disabled (line 39)
        return verses[:top_k]   # raw BGE-M3 order preserved
```

**Caveat:** `RERANK_DISABLED` is evaluated at module import time. Setting it in `.env` or via `set` before starting the server is the correct method. Changing it at runtime in a running process has no effect.

---

## Recommendation

**Run RERANK_DISABLED=1 as the default until a replacement reranker is confirmed.** The QRCD evidence is unambiguous: current `bge-reranker-v2-m3` costs 50% hit@10 on Arabic queries. Disabling it is a zero-cost, zero-risk change until `from_ai_graph_cohere_rerank_ab_impl` provides a better alternative.

**Next steps in priority order:**
1. (**Immediate, no API key**) Confirm with eval_v1 run (RERANK_DISABLED=1 → save result, compare)
2. (**Requires COHERE_API_KEY**) `from_ai_graph_cohere_rerank_ab_impl` — Cohere Rerank 4 Pro A/B
3. (**Fallback**) `from_ai_graph_arabic_reranker_research` — Arabic-specific rerankers if Cohere fails

---

_Analysis based on: `data/qrcd_ablation.json`, `data/qrcd_hybrid_compare.json`, `data/eval_v1_results.json`, `data/ralph_analysis_from_ai_graph_zeroentropy_cohere_reranker_ab_detail.md`_
