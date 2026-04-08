# Implementation Plan: Hallucination Reduction

**Status:** Phase 1 ready to implement
**Baseline:** `v1.0-arabic-baseline` (tag) — Arabic integration + eval harness complete

---

## What's Already Done

| Component | Status |
|-----------|--------|
| Arabic text (Hafs ʿan ʿĀṣim, Uthmani) on all 6,234 verses | Done |
| Arabic root morphology: 1,223 roots, 36K edges | Done |
| `search_arabic_root` + `compare_arabic_usage` tools | Done |
| Bilingual frontend (Amiri font, RTL tooltips) | Done |
| Pipeline config externalization (`pipeline_config.yaml` + `config.py`) | Done |
| Evaluation harness (`evaluate.py` + 18-question `test_dataset.json`) | Done |
| Typed edge classification script (`classify_edges.py`) | Done (script exists, edges may need running) |
| `.gitignore` + secrets cleanup | Done |

---

## Architecture

```
USER QUERY
    |
[Layer 5] Semantic Entropy (5x Haiku)     <- Abstain if high entropy
    |
[Layer 1] Retrieval                        <- Current Neo4j (graph + vector + keyword)
    |                                         + rank_bm25 (in-process, no Elasticsearch)
    |                                         + cross-encoder reranking
    |                                         + FILCO sentence filtering
    |                                         + LLMLingua-2 compression
    |                                         + lost-in-middle reordering
[Layer 2] KG Grounding                     <- Typed edges (SUPPORTS, ELABORATES, etc.)
    |                                         + Arabic roots (done)
[Layer 3] Claude Agentic Loop              <- tool_choice enforcement
    |                                         + 8 tools (current) + query_typed_edges
[Layer 4] Post-Gen Verification            <- MiniCheck (always-on)
    |                                         + HHEM threshold gate
    |                                         + SelfCheckGPT (borderline only)
    |                                         + Conformal Prediction wrapper
[Layer 5] Constrained Output               <- Citation density check
    |                                         + re-generation trigger
[Eval] DeepEval + RAGChecker               <- Feeds autoresearch loop
```

---

## QIS Score (Quality-Integrity-Safety)

```python
QIS_SCORE = (
    0.30 * citation_recall          # % of expected citations found
  + 0.25 * citation_precision       # MiniCheck: % of citations that support their claim
  + 0.20 * grounding_rate           # % of paragraphs with >= 1 citation
  + 0.15 * hhem_score               # HHEM calibrated hallucination score
  + 0.10 * abstention_accuracy      # correct refusal on unanswerable questions
)
```

---

## Phase 1: Wire Typed Edges into Tools

**Impact:** High | **Effort:** Low | **Risk:** None
**Dependencies:** Run `classify_edges.py` if typed edges don't exist yet

### 1.1 Verify typed edges exist in Neo4j

```cypher
MATCH ()-[r]->() WHERE type(r) IN ['SUPPORTS','ELABORATES','QUALIFIES','CONTRASTS','REPEATS']
RETURN type(r) AS t, count(r) AS c
```

If empty, run `py classify_edges.py` first.

### 1.2 New tool: `query_typed_edges`

**File:** `chat.py`

```python
def tool_typed_edges(session, verse_id: str, edge_type: str = None) -> dict:
    """Query verses connected by a specific relationship type."""
    if edge_type:
        rows = session.run("""
            MATCH (v:Verse {verseId: $id})-[r:""" + edge_type + """]-(other:Verse)
            RETURN other.verseId AS otherId, other.surahName AS surahName,
                   other.text AS text, r.score AS score, r.confidence AS confidence
            ORDER BY r.score DESC LIMIT 12
        """, id=verse_id)
    else:
        rows = session.run("""
            MATCH (v:Verse {verseId: $id})-[r]-(other:Verse)
            WHERE type(r) IN ['SUPPORTS','ELABORATES','QUALIFIES','CONTRASTS','REPEATS']
            RETURN other.verseId AS otherId, type(r) AS relType,
                   other.text AS text, r.score AS score
            ORDER BY r.score DESC LIMIT 20
        """, id=verse_id)
```

### 1.3 Enrich `get_verse` with typed edge info

After existing RELATED_TO query, add typed edge summary.

### 1.4 Update system prompt with typed edge descriptions

### 1.5 Frontend: color-coded link types in 3D graph

---

## Phase 2: Retrieval Quality Gating

**Impact:** High | **Effort:** Medium | **Risk:** Low
**Dependencies:** None

### 2.1 Cross-encoder reranking (`retrieval_gate.py`)

Model: `cross-encoder/ms-marco-MiniLM-L-6-v2` (~80MB, fast CPU)

```python
def rerank_verses(query, verses, top_k=20) -> list[dict]
def assess_retrieval_quality(verses, threshold=0.3) -> str  # "good"|"marginal"|"poor"
```

### 2.2 FILCO sentence filtering

CPU-only, inline. For each retrieved verse, score individual sentences against the query. Drop sentences below threshold before stuffing context.

### 2.3 Lost-in-middle reordering

Reorder retrieved verses: most relevant at start AND end (U-shape). Middle positions get lower-relevance items. Trivial — just sort order change.

### 2.4 Corrective RAG fallback

If keyword search quality is "poor", auto-trigger semantic search as fallback. Pass `user_query` through the pipeline.

### 2.5 LLMLingua-2 compression (defer if latency too high)

Compress retrieved context before Claude calls. Runs a small model (~300MB). May add 1-2s latency. Implement last in this phase and A/B test.

### 2.6 rank_bm25 in-process

Add BM25 as a third retrieval path alongside keyword and semantic. Pure Python, no Elasticsearch. `pip install rank-bm25`.

---

## Phase 3: Post-Generation Verification

**Impact:** Very High | **Effort:** High | **Risk:** Medium (latency + cost)
**Dependencies:** Benefits from Phase 2

### 3.1 MiniCheck (primary, always-on)

Verify every claim against cited verse text. Options:
- **Local:** Download model, run on CPU/GPU (~2GB)
- **Modal.com:** Serverless endpoint, pay-per-call

Returns `{claim, cited_verse, entailment_score}` for each citation.

### 3.2 HHEM v2.1 (threshold gate)

Vectara API — single HTTP call per response. Returns calibrated hallucination probability [0,1]. If > 0.5, flag response for review. Near-zero integration effort.

### 3.3 SelfCheckGPT (borderline fallback)

Only triggered when HHEM score is in the "uncertain" range (0.3-0.7). Generates 3-5 variant responses via Haiku, checks consistency. High divergence = likely hallucination.

### 3.4 Conformal Prediction wrapper

Pure Python. Calibrate on eval set to get statistical guarantees: "with 95% confidence, this citation is correct." Wraps MiniCheck scores.

### 3.5 Frontend: verification badge

SSE event `{t: "verification", d: {precision, recall, flagged}}`. Display green/amber badge on each response.

---

## Phase 4: Constrained Output

**Impact:** Medium | **Effort:** Low | **Risk:** Low
**Dependencies:** Phase 3 claim extraction logic

### 4.1 Citation density check

Count paragraphs without `[sura:verse]` citations. If > 30% uncited, trigger one retry.

### 4.2 Re-generation trigger

Append instruction: "Add citations to every claim, or remove unsupported claims." Cap at 1 retry.

### 4.3 Warning SSE event

If still uncited after retry, emit `{t: "warning", d: "N paragraph(s) lack citations"}`.

---

## Phase 5: Uncertainty Quantification

**Impact:** Medium | **Effort:** Low | **Risk:** Low (cost: ~5 Haiku calls per uncertain query)
**Dependencies:** None

### 5.1 Semantic Entropy

For each query, generate 5 responses with Haiku (temperature 0.7). Cluster by semantic similarity. High entropy (many distinct clusters) = model is uncertain = abstain or flag.

### 5.2 Wire into Layer 5 gate

Run BEFORE retrieval. If entropy is very high, respond with "I'm not confident I can answer this accurately from the Quran" instead of generating a potentially hallucinated response.

---

## Phase 6: System Prompt Refinement

**Impact:** Medium | **Effort:** Low | **Risk:** None
**Dependencies:** After all other phases

- Document all new tools (typed edges)
- Strengthen citation mandate with verification awareness
- Add typed-edge language guidance
- Add note about retrieval confidence levels
- Add abstention instruction for uncertain topics

---

## Phase 7: Evaluation Expansion

**Impact:** High | **Effort:** Medium | **Risk:** None
**Dependencies:** None — can run in parallel

### 7.1 Expand test dataset to ~200 questions

- **100 standard** — clear Quranic topics with well-known verses
- **50 edge cases** — ambiguous topics, commonly misattributed verses
- **50 unanswerable** — questions the Quran doesn't address (tests abstention)

### 7.2 Add HHEM + abstention metrics to evaluate.py

Update `pipeline_config.yaml` composite weights to match QIS_SCORE formula.

### 7.3 Integrate DeepEval + RAGChecker

Automated evaluation infrastructure that feeds the autoresearch loop.

---

## Implementation Order

```
Step 0:  Run baseline eval (py evaluate.py --ids q01,q02,q03)
Step 1:  Phase 1 — typed edges in tools (low effort, high value)
Step 2:  Phase 2.1-2.4 — retrieval gating (cross-encoder + CRAG + FILCO + reorder)
Step 3:  Phase 3.1-3.2 — MiniCheck + HHEM (core verification)
Step 4:  Phase 4 — constrained output (citation density)
Step 5:  Phase 7.1 — expand eval set to 200 questions
Step 6:  Run autoresearch loop to optimize pipeline_config.yaml
Step 7:  Phase 3.3-3.4 — SelfCheckGPT + Conformal (borderline cases)
Step 8:  Phase 5 — Semantic Entropy (uncertainty gate)
Step 9:  Phase 2.5-2.6 — LLMLingua-2 + BM25 (optimization)
Step 10: Phase 6 — system prompt refinement
```

Re-evaluate after each step. Let the ARL tell you which methods actually move the QIS score.

---

## What We're NOT Doing (and Why)

| Method | Reason to skip |
|--------|---------------|
| CAD, DoLa, ITI, RepE, SEPs, NeuroLogic, SynCheck/FOD | Require open-weight model logit access. Claude API doesn't expose logits. |
| FLARE, RankRAG, R-Tuning, FactTune/DPO | Require model fine-tuning or training. |
| Pinecone + Elasticsearch | 3 data stores for 6,234 verses is overengineering. Neo4j vector index + in-process BM25 covers it. |
| 6 verification methods simultaneously | Redundant. MiniCheck + HHEM covers 90% of cases. Add SelfCheckGPT for borderline only. |
| Multi-agent debate | $0.008/query for marginal gain at this scale. |
| LINC formal verification | Translating Quranic verse semantics into FOL is a research project, not engineering. |

---

## New Dependencies (cumulative)

| Package | Phase | Size | Purpose |
|---------|-------|------|---------|
| `rank-bm25` | 2 | ~50KB | In-process BM25 ranking |
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | 2 | ~80MB | Retrieval reranking |
| `cross-encoder/nli-deberta-v3-xsmall` | 3 | ~180MB | Citation entailment (MiniCheck) |
| `vectara-hhem` or API call | 3 | API | Hallucination scoring |
| `deepeval` | 7 | ~20MB | Eval framework |

## New Files

| File | Phase | Purpose |
|------|-------|---------|
| `retrieval_gate.py` | 2 | Cross-encoder reranking + FILCO + CRAG |
| `citation_verifier.py` | 3 | MiniCheck + HHEM + SelfCheckGPT |
| `uncertainty.py` | 5 | Semantic Entropy |

## Modified Files

| File | Phases | Changes |
|------|--------|---------|
| `chat.py` | 1,2,6 | New tool, reranker integration, prompt |
| `app.py` | 1,3,4 | Typed edges in graph, verification SSE, citation check |
| `index.html` | 1,3,4 | Link colors, verification badge, warning |
| `evaluate.py` | 7 | HHEM metric, abstention metric |
| `pipeline_config.yaml` | All | New config knobs per phase |
| `test_dataset.json` | 7 | Expand to ~200 questions |
