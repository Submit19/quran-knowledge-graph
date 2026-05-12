# Implementation Plan: `from_ai_graph_cohere_rerank_ab_impl`

_Tick 113 · 2026-05-13 · agent_creative IMPL_

---

## 1. Context Summary

The current `bge-reranker-v2-m3` cross-encoder **actively damages retrieval** on QRCD Arabic queries:

| Stage | hit@10 | MAP@10 | Delta |
|---|---|---|---|
| BGE-M3-EN vector only | 0.6364 | 0.1387 | baseline |
| + bge-reranker-v2-m3 | 0.3182 | 0.1018 | **-50%** |
| Full retrieval gate | 0.3182 | 0.1083 | -50% |

The reranker slot is the highest-leverage improvement target. This doc specifies:
1. `RERANKER_BACKEND=cohere` branch in `retrieval_gate.py`
2. `eval_qrcd_reranker_ab.py` eval script structure
3. Results table (placeholder — `COHERE_API_KEY` not yet set)
4. Risk register and decision gate

Source: `data/ralph_analysis_from_ai_graph_zeroentropy_cohere_reranker_ab_detail.md`

---

## 2. `retrieval_gate.py` — RERANKER_BACKEND Branch Design

### 2a. New env vars

```python
# retrieval_gate.py — top-level additions
RERANKER_BACKEND = os.environ.get("RERANKER_BACKEND", "local").strip().lower()
# Values: "local" (default, current CrossEncoder), "cohere", "zeroentropy", "disabled"
```

The existing `RERANK_DISABLED` / `RERANKER_MODEL=none` kill switches are preserved for backward compatibility; `RERANKER_BACKEND=disabled` is equivalent.

### 2b. Cohere API client (lazy-loaded)

```python
_cohere_client = None

def _get_cohere_client():
    global _cohere_client
    if _cohere_client is None:
        import cohere
        _cohere_client = cohere.ClientV2(os.environ["COHERE_API_KEY"])
    return _cohere_client
```

### 2c. Cohere rerank function

```python
def _rerank_cohere(query: str, verses: list[dict], top_k: int,
                   model: str = "rerank-multilingual-v3.0") -> list[dict]:
    """
    Rerank via Cohere Rerank API.

    Model notes:
      - "rerank-multilingual-v3.0": current multilingual GA (100+ langs, Arabic confirmed)
      - "rerank-v3.5": alias used in some SDK versions — verify against co.models.list()
      - "rerank-v4-pro": pre-release name cited in marketing; check dashboard before using

    Output shape: relevance_score in [0, 1] (already normalised — no scaling needed
    to match the downstream assess_quality() threshold of 0.3).
    """
    co = _get_cohere_client()
    texts = [v.get("text", "") for v in verses]
    response = co.rerank(
        model=model,
        query=query,
        documents=texts,
        top_n=top_k,
    )
    # Map Cohere's ranked indices back to verse dicts
    reranked = []
    for hit in response.results:
        v = dict(verses[hit.index])          # shallow copy — do not mutate original
        v["relevance_score"] = float(hit.relevance_score)
        reranked.append(v)
    return reranked
```

### 2d. Updated `rerank_verses()` dispatch

Replace the `model = _get_reranker()` block in `rerank_verses()` with:

```python
def rerank_verses(query: str, verses: list[dict], top_k: int = 20,
                   profile: str | None = None) -> list[dict]:
    if not verses or not query:
        return verses
    _RERANK_PROFILES = {"broad"}
    if profile is not None and profile not in _RERANK_PROFILES:
        return verses[:top_k]

    backend = RERANKER_BACKEND
    if backend in ("disabled",) or RERANK_DISABLED:
        return verses[:top_k]

    if backend == "cohere":
        return _rerank_cohere(query, verses, top_k)

    # backend == "local" (default): current CrossEncoder path
    model = _get_reranker()
    if model is None:
        return verses[:top_k]
    pairs = [(query, v.get("text", "")) for v in verses]
    scores = model.predict(pairs)
    for v, s in zip(verses, scores):
        v["relevance_score"] = float(s)
    verses.sort(key=lambda v: v["relevance_score"], reverse=True)
    return verses[:top_k]
```

**Output shape compatibility:** Cohere returns `relevance_score` in [0, 1]; the local CrossEncoder returns raw logits (unbounded). `assess_quality()` uses a 0.3 threshold — this threshold was calibrated for the local model. After switching to Cohere, re-calibrate: a score of 0.3 in Cohere's space maps to roughly 30% confidence (already semantically meaningful). If `assess_quality()` fires `"poor"` too often on Cohere output, lower threshold to 0.15 for the first eval run.

---

## 3. `eval_qrcd_reranker_ab.py` — Script Structure

Mirror pattern from `eval_qrcd_retrieval.py` and `eval_ablation_retrieval.py`.

```python
"""
eval_qrcd_reranker_ab.py — Reranker A/B: BGE-M3 local vs Cohere vs disabled.

Runs 22 QRCD questions through the BGE-M3-EN vector retrieval path, then
applies three reranking conditions:
  A. RERANKER_BACKEND=local (bge-reranker-v2-m3, current default)
  B. RERANKER_BACKEND=cohere (Cohere Rerank Multilingual v3.0)
  C. RERANKER_BACKEND=disabled (vector-only, raw BGE-M3 order)

Metrics per condition: hit@10, MAP@10, MRR, avg latency (ms/q).
Outputs: data/qrcd_reranker_ab_results.json + console table.

Usage:
  COHERE_API_KEY=<key> python eval_qrcd_reranker_ab.py
  # Without key: only runs conditions A and C (local + disabled).
"""

import json, os, time
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import retrieval_gate  # import after setting RERANKER_BACKEND

load_dotenv()

QRCD_PATH  = Path("data/qrcd_test.jsonl")
OUTPUT     = Path("data/qrcd_reranker_ab_results.json")
TOP_K      = 10
EMBED_MODEL = "BAAI/bge-m3"   # same as SEMANTIC_SEARCH_INDEX=verse_embedding_m3

def load_qrcd():
    """Return list of {question, gold_verses: set[str]}."""
    ...  # same as eval_qrcd_retrieval.py expand_verse_range logic

def retrieve_raw(driver, model, question, top_k=30):
    """BGE-M3-EN vector search — returns list[dict] with 'text', 'verse_id' keys."""
    ...  # copy vector search block from eval_qrcd_retrieval.py, top_k=30 pre-rerank

def compute_metrics(ranked_ids, gold_set, k=10):
    """Return dict: hit@k, map@k, mrr."""
    ...  # standard IR metrics, same as other eval scripts

def run_condition(driver, model, questions, backend_name, cohere_model=None):
    os.environ["RERANKER_BACKEND"] = backend_name
    # Force module re-read of env var (module-level var is already set; patch inline)
    retrieval_gate.RERANKER_BACKEND = backend_name
    results = []
    for q in questions:
        raw = retrieve_raw(driver, model, q["question"])
        if backend_name == "cohere":
            reranked = retrieval_gate._rerank_cohere(q["question"], raw, TOP_K,
                                                      model=cohere_model or "rerank-multilingual-v3.0")
        elif backend_name == "disabled":
            reranked = raw[:TOP_K]
        else:  # local
            reranked = retrieval_gate.rerank_verses(q["question"], raw, TOP_K, profile="broad")
        ids = [v["verse_id"] for v in reranked]
        results.append(compute_metrics(ids, q["gold_verses"]))
    return results

def main():
    driver = GraphDatabase.driver(os.getenv("NEO4J_URI", "bolt://localhost:7687"), ...)
    model  = SentenceTransformer(EMBED_MODEL)
    questions = load_qrcd()

    conditions = ["disabled", "local"]
    if os.getenv("COHERE_API_KEY"):
        conditions.append("cohere")

    all_results = {}
    for cond in conditions:
        t0 = time.time()
        res = run_condition(driver, model, questions, cond)
        elapsed = time.time() - t0
        hit10  = sum(r["hit@10"] for r in res) / len(res)
        map10  = sum(r["map@10"] for r in res) / len(res)
        mrr    = sum(r["mrr"]    for r in res) / len(res)
        all_results[cond] = {"hit@10": hit10, "map@10": map10, "mrr": mrr,
                              "ms_per_q": elapsed * 1000 / len(res)}
        print(f"{cond:12s}  hit@10={hit10:.4f}  MAP@10={map10:.4f}  MRR={mrr:.4f}  {elapsed*1000/len(res):.0f}ms/q")

    with open(OUTPUT, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved: {OUTPUT}")

if __name__ == "__main__":
    main()
```

---

## 4. Results Table (COHERE_API_KEY not yet set)

| Condition | hit@10 | MAP@10 | MRR | ms/q | Notes |
|---|---|---|---|---|---|
| disabled (vector only) | 0.6364 | 0.1387 | 0.4177 | 88ms | from `data/qrcd_ablation.json` |
| local (bge-reranker-v2-m3) | 0.3182 | 0.1018 | 0.1018 | 298ms | from `data/qrcd_ablation.json` — confirmed regression |
| cohere (rerank-multilingual-v3.0) | **[TBD — needs COHERE_API_KEY]** | [TBD] | [TBD] | ~500ms est. | 100+ langs, Arabic confirmed |
| cohere-fast (rerank-english-light-v3.0) | [TBD] | [TBD] | [TBD] | ~200ms est. | 10x cheaper — run after Pro |

**Conservative estimate for Cohere Pro:** hit@10 ~0.45–0.55 (midpoint between reranked and raw; confirmed multilingual). If Cohere matches or exceeds `disabled` (0.6364), it becomes the new default. If it falls below `disabled`, the interim recommendation `RERANK_DISABLED=1` stands.

---

## 5. Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| `COHERE_API_KEY` absent | **Current blocker** | User adds key to `.env` before running eval |
| Cohere model name mismatch | Medium | Verify with `co.models.list()` or Cohere dashboard — `rerank-multilingual-v3.0` is the stable GA name as of 2026-05 |
| Cohere `relevance_score` scale vs `assess_quality()` threshold | Low | Re-calibrate `assess_quality()` threshold from 0.3 → 0.15 for first run; re-raise if `"poor"` fires on clearly relevant verses |
| API rate limits on 22-q run | Very low | Cohere trial: 1K API calls/month free; 22 questions × 30 docs = 660 rerank calls — within free tier |
| Output shape mismatch | Low | `_rerank_cohere()` already normalises to `{verse_id, text, relevance_score}` — same as local path |
| `profile` gate skips Cohere on CONCRETE queries | Medium | For A/B, force `profile="broad"` in eval script to get consistent comparison across all 22 questions |
| Arabic text truncation at 32K limit | Very low | Longest Quran verse is ~80 tokens; 30 verses × 80 tokens = 2400 tokens — well within 32K |

---

## 6. Decision Gate

After running `eval_qrcd_reranker_ab.py` with `COHERE_API_KEY` set:

| Result | Action |
|---|---|
| Cohere hit@10 > disabled (0.6364) by ≥ 2 pts | **Set `RERANKER_BACKEND=cohere` as new default in `.env`; update CLAUDE.md** |
| Cohere hit@10 ≥ disabled (within 2 pts) | Keep Cohere as option; run `qwen3_reranker_ab_qrcd` first to compare free alternatives |
| Cohere hit@10 < disabled | Set `RERANK_DISABLED=1` as default (recovers 2× hit@10 vs current); explore ZeroEntropy zerank-2 |
| Cohere + Fast differ by < 5 pts | Use Fast (10× cheaper) for production |

---

## 7. Follow-Up Tasks Generated

1. **`qwen3_reranker_ab_qrcd`** (p78, already in backlog) — Qwen3-Reranker-0.6B is free (HuggingFace), may match Cohere multilingual quality. Run after Cohere A/B for cost comparison.
2. **If Cohere wins:** Add `RERANKER_BACKEND` env to `CLAUDE.md` optional env vars section and `.env.example`.
3. **If all API rerankers fail on Arabic:** Promote `from_research_finetune_bge_m3_qrcd` — domain-adaptive fine-tune is the QRCD gap per synthesis insight.

---

## 8. Acceptance Checklist

- [x] `data/ralph_agent_from_ai_graph_cohere_rerank_ab_impl.md` exists
- [x] File size >= 600 bytes
- [x] Contains `retrieval_gate.py` branch design (pseudocode for `_rerank_cohere` + dispatch)
- [x] Contains `eval_qrcd_reranker_ab.py` structure description
- [x] Contains results table (placeholder cells for COHERE_API_KEY-blocked run)
- [x] Contains risk register with COHERE_API_KEY blocker callout
- [x] Contains decision gate criteria
