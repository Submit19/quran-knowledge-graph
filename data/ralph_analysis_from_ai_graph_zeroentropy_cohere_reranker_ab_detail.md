# Reranker A/B Analysis: ZeroEntropy zerank-2 + Cohere Rerank 4 vs bge-reranker-v2-m3

_Task: `from_ai_graph_zeroentropy_cohere_reranker_ab` | Tick 32 | 2026-05-11_

## TL;DR

**Our current reranker actively hurts QRCD retrieval** — it drops hit@10 from 0.6364 (raw vector) to 0.3182 (after rerank), a 50% regression. A/B testing ZeroEntropy zerank-2 or Cohere Rerank 4 is high-priority and could recover or exceed the raw-vector baseline. Both are API-only; keys needed to run the live A/B. This doc captures the plan, baseline data, and expected outcomes.

---

## Baseline: Current Retrieval Numbers (QRCD, n=22 questions)

### Stage-by-stage ablation (`data/qrcd_ablation.json`)

| Stage | hit@10 | MRR | ms/q | Delta hit@10 |
|---|---|---|---|---|
| v0: BGE-M3-EN vector only | **0.6364** | **0.4356** | 88ms | baseline |
| v1: + bge-reranker-v2-m3 | 0.3182 | 0.1018 | 298ms | **-0.3182 (-50%)** |
| v2: + lost-in-middle reorder | 0.3182 | 0.1083 | — | -0.3182 |
| v3: full retrieval gate | 0.3182 | 0.1083 | — | -0.3182 |

**Key finding:** `bge-reranker-v2-m3` is the confirmed culprit of the ~50% hit@10 drop on QRCD Arabic queries. The reranker was described in CLAUDE.md as a multilingual improvement over the legacy English-only reranker — this ablation shows it still damages Arabic-query retrieval significantly.

### Three-way embedding comparison (`data/qrcd_retrieval_results.json`)

| Backend | hit@10 | MAP@10 | MRR |
|---|---|---|---|
| MiniLM (legacy) | 0.0909 | 0.0275 | 0.073 |
| BGE-M3-EN | **0.6364** | **0.1387** | **0.4177** |
| BGE-M3-AR | 0.5455 | 0.1077 | 0.3458 |

BGE-M3-EN is our best retriever. The reranker degrades it.

### End-to-end eval quality (eval_v1, n=13 questions)

| Cluster | avg cites | notes |
|---|---|---|
| Concrete topics (paradise, sin, hell, charity) | 38.5 | OK |
| Abstract queries (meditation, reverence) | 20.0 | **weak** |
| Short surahs (Al-Fatihah, Al-Ikhlas, Ar-Rahman) | 30.5 | weak |
| Long/rich surahs (Al-Baqarah, Yasin) | 48.0 | good |
| Global themes (common themes in Quran) | 167 | outlier-high |

Overall avg: **43.6 unique cites/question**. Target: 50.

---

## Candidates for A/B

### 1. ZeroEntropy zerank-2 (Priority: High)
- **Rank:** #1 on MTEB reranker leaderboard 2026, ELO 1680+
- **Type:** API-only (no self-hosted option)
- **API:** `https://api.zeroentropy.dev/` — requires `ZEROENTROPY_API_KEY`
- **Cost:** Unknown public pricing; likely similar to Cohere
- **Languages:** English-primary; Arabic coverage unconfirmed — this is the critical unknown

### 2. Cohere Rerank 4 Pro (Priority: High)
- **Rank:** #2 MTEB ELO 1627, RAGAS 1.0 relevance score
- **Context window:** 32K tokens
- **Languages:** 100+ languages including Arabic
- **API:** `cohere.Client.rerank(model="rerank-v3.5")` — requires `COHERE_API_KEY`
- **Cost:** ~$1/1000 documents; very affordable for our 22-question eval
- **Why preferred:** Confirmed multilingual; 32K context means it can absorb full Verse text + Arabic

### 3. Cohere Rerank 4 Fast (Priority: Medium)
- **Rank:** ELO 1506 (#7)
- **Cost:** ~$0.10/1000 documents — 10x cheaper than Pro
- **Use case:** If Pro wins, benchmark Fast to see if budget version is adequate

### 4. BGE-Reranker v2.5 (Priority: Low, fallback)
- Newer than our v2-m3 but same family
- Self-hosted (free), drop-in replacement
- Likely marginal improvement given v2-m3 already hurts us — same architecture

---

## A/B Execution Plan

### Step 1: Cohere Rerank 4 A/B (easiest to run)

```python
# eval_qrcd_reranker_ab.py
import cohere
co = cohere.Client(os.getenv("COHERE_API_KEY"))

def rerank_cohere(query, docs, model="rerank-v3.5", top_n=10):
    results = co.rerank(
        query=query,
        documents=[d["text"] for d in docs],
        model=model,
        top_n=top_n
    )
    return [docs[r.index] for r in results.results]
```

Run on:
1. QRCD 22-question set (data available in `eval_qrcd_retrieval.py`)
2. eval_v1 13-question set via `/chat` endpoint with `RERANKER=cohere`

Compare: hit@10, MAP@10, MRR, avg cites/question.

### Step 2: ZeroEntropy zerank-2 A/B

```python
# ZeroEntropy uses OpenAI-compatible API format
from openai import OpenAI
zeroentropy = OpenAI(
    base_url="https://api.zeroentropy.dev/v1",
    api_key=os.getenv("ZEROENTROPY_API_KEY")
)
# Call their rerank endpoint (exact API shape to verify on signup)
```

### Step 3: retrieval_gate.py abstraction

Add `RERANKER_BACKEND=local|cohere|zeroentropy` env var to `retrieval_gate.py`. The current `_rerank_cross_encoder` becomes one branch; new API branches call out.

---

## Expected Outcomes

### Conservative estimate (Cohere 4 Pro)
- Cohere is confirmed multilingual + 32K context
- If it can correctly score Arabic verse text against Arabic questions, we expect hit@10 to **recover to 0.45-0.55** (vs 0.3182 current, 0.6364 raw floor)
- MRR likely recovers to 0.25-0.35
- Abstract eval_v1 cluster (meditation/reverence) expected to improve 5-15 cites

### Optimistic estimate (zerank-2)
- If Arabic coverage is adequate: could match or beat raw BGE-M3 vector (hit@10 ~0.65)
- At ELO 1680+, zerank-2 should correctly rank Quranic passages for semantically abstract queries better than a cross-encoder trained primarily on English passages

### If both fail on Arabic
- Fall back to: **disable reranker entirely** (`RERANK_DISABLED=1`) which already beats the reranked result by 2x on hit@10
- Then research Arabic-specific rerankers (CAMeL-BERT or AraBART fine-tuned for reranking)

---

## Prerequisites / Blockers

| Requirement | Status |
|---|---|
| `COHERE_API_KEY` in `.env` | Missing — user needs to add |
| `ZEROENTROPY_API_KEY` in `.env` | Missing — user needs to signup at zeroentropy.dev |
| QRCD eval harness (`eval_qrcd_retrieval.py`) | Exists |
| retrieval_gate.py abstraction | Not yet — needs new env-switch branch |
| `eval_qrcd_reranker_ab.py` script | Needs to be written (30 min) |

---

## Proposed Follow-Up Tasks

1. **`from_ai_graph_cohere_rerank_ab_impl`** (priority 82): Write `eval_qrcd_reranker_ab.py`, add `RERANKER_BACKEND=cohere` branch to `retrieval_gate.py`, run on QRCD 22-q + eval_v1, compare. Blocker: `COHERE_API_KEY` set.

2. **`from_ai_graph_disable_reranker_baseline`** (priority 75): Verify the `RERANK_DISABLED=1` path end-to-end by running eval_v1 with reranker off and confirming avg cites improves vs current (hypothesis: 43.6 -> ~48+). No external keys needed — run today.

3. **`from_ai_graph_arabic_reranker_research`** (priority 55): Research Arabic-specific reranking options (CAMeL-BERT, AraBART, JAIS-based reranker). QRCD Arabic queries are the core weakness.

---

## Summary

The reranker slot is currently costing us 50% of our hit@10. Replacing it with Cohere Rerank 4 Pro (confirmed Arabic multilingual) is the highest-expected-value next step. ZeroEntropy zerank-2 is the stretch target if Cohere is insufficient. Both require API keys — the implementation plan above is ready to execute the moment keys are available. Until then: **run `RERANK_DISABLED=1` as an interim improvement** (recovers to raw BGE-M3 baseline of 0.6364 hit@10 vs 0.3182 current).
