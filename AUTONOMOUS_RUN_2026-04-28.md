# Autonomous Run — 2026-04-27 / 2026-04-28

User asked: "plan out these and implement them all while I sleep ... start and
finish each task before moving on to the next. Once you finish, explore more
of the sources you found ... then begin on those tasks after planning those
out too."

This is the result.

---

## Overview

**11 substantive tasks landed across 3 phases. All committed and pushed to `origin/main`.**

| Phase | What | Outcome |
|-------|------|---------|
| 1 | Six implementations from RESEARCH_2026-04-27.md | 6/6 completed |
| 2 | Deeper exploration of sources cited | RESEARCH_2026-04-28_DEEP.md written |
| 3 | Implement four follow-up tasks from deep-dive | 4/5 completed (T3 blocked) |

**Bottom-line numbers**:
- QRCD MAP@10: **0.028 → 0.139** (5× lift) just from BGE-M3 retrieval
- 41,138 edges enriched with bidirectional TF-IDF + provenance
- 3,270 new SIMILAR_PHRASE edges (mutashabihat) ingested with CC0 license
- Citation verifier now has both NLI and MiniCheck-FT5 backends + atomic claim decomposition
- Sefaria-style auto-linker (resolver + API + JS widget) shipped
- HippoRAG ruled out for QRCD across 36 hyperparameter configurations — saves future tuning effort

---

## Phase 1 — Original 6 tasks

### Task 1: Code-19 arithmetic features ✅
Commit `9cf268f`. Stamped 6,234 verses + 114 surahs with letter-frequency counts (13 mysterious letters), per-sura mysterious-letter divisibility-by-19 indicators, position_in_sura, char/word counts.

Verified:
- Khalifa total = **6,346 = 19 × 334** ✓
- Qaf in Surah 50 = **57 = 19 × 3** ✓
- Qaf in Surah 42 = **57 = 19 × 3** ✓

New tool `get_code19_features(scope, target)` available to the agent. Pure arithmetic — cannot be hallucinated.

### Task 2: MiniCheck-FT5 citation verifier ✅
Commit `2040742`. Added MiniCheck-Flan-T5-Large as alternative to NLI-DeBERTa for citation verification.

Smoke test on 3 plausible Quran-style citations:
- NLI: 0/3 supported, precision **0.0** (too strict)
- MiniCheck: 2/3 supported, precision **0.67** (caught one borderline)

Switch via `CITATION_VERIFIER_MODEL=minicheck` env var.

### Task 3: BGE-M3 multilingual embeddings ✅
Commit `2754e34`. Re-embedded all 6,234 verses with BAAI/bge-m3 (1024-dim, multilingual). Both English (`embedding_m3`) and Arabic (`embedding_m3_ar`). Additive — old MiniLM `embedding` untouched.

Switch via `SEMANTIC_SEARCH_INDEX=verse_embedding_m3`.

### Task 4: QRCD benchmark eval ✅
Commit `1b32a4e`. Two evaluators (retrieval-only and full agent loop). On 22 unique QRCD questions:

| metric    | MiniLM | **BGE-M3-EN** | BGE-M3-AR | AraBERT (lit) |
|-----------|--------|---------------|-----------|----|
| hit@10    | 0.091  | **0.636**     | 0.545     | — |
| recall@10 | 0.001  | **0.132**     | 0.085     | — |
| map@10    | 0.028  | **0.139**     | 0.108     | 0.36 (fine-tuned) |
| mrr       | 0.073  | **0.418**     | 0.346     | — |

Off-the-shelf BGE-M3 hits ~38% of fine-tuned AraBERT MAP@10 with no training. Plenty of headroom for future reranking and fine-tuning.

### Task 5: Sefaria-inspired ref-resolver ✅
Commit `fde671e`. Three pieces, all working end-to-end:

1. **`ref_resolver.py`**: `resolve_refs(text)` finds Quranic citations in English/Arabic. Patterns: `[2:255]`, `(2:255)`, `Q. 24:35`, `Surah Al-Baqarah verse 286`, `Ayat al-Kursi`, Arabic `سورة البقرة آية 255`, ranges like `[2:255-258]`.
2. **API endpoints** in app_free.py: `POST /api/resolve_refs`, `GET /api/verse/<id>`, `GET /quran_linker.js`.
3. **JS widget** `static/quran_linker.js`: drop-in `<script>` tag that auto-links any web page; tooltips show Khalifa English + Hafs Arabic.

Demo: `static/linker_demo.html`.

### Task 6: HippoRAG-style PPR ✅ (negative result)
Commit `b0e725d`. Implemented `hipporag_traverse.py` combining BGE-M3 vector seeds + past-Query seeds + graph structure into Personalized PageRank.

On QRCD (22 questions): **HippoRAG underperforms vanilla retrieval** (hit@10: 0.64 → 0.50, mrr: 0.46 → 0.23). Two diagnosed causes:
1. QRCD is single-hop direct-lookup — wrong regime for PPR (predicted by GraphRAG-Bench arXiv:2506.05690)
2. Embedding-space mismatch: reasoning_memory's Query embeddings are MiniLM-English, but QRCD queries are Arabic

Documented in HIPPORAG_REPORT.md. Not wired into chat.py — premature.

---

## Phase 2 — Deeper exploration

Spawned a research agent to dig into 6 specific sources. Report at
**`RESEARCH_2026-04-28_DEEP.md`**. Identified 5 follow-up tasks ranked by ROI/effort:

1. T1 — Ingest QUL Mutashabihat (free 9k+ scholarly-vetted similarity edges)
2. H1 — PPR hyperparameter sweep + edge-sign sanity check
3. S1 — Sefaria-pattern bidirectional TF-IDF + provenance schema
4. M1 — FActScore atomic-claim decomposer in front of MiniCheck/NLI
5. G1 — Multi-hop Quran benchmark (deferred — large effort)

Most importantly: the deep-dive **predicted Task 6's negative result** by citing GraphRAG-Bench. The negative result wasn't a bug — it was the literature's headline finding for our regime.

---

## Phase 3 — Follow-up tasks

### T1: Mutashabihat edges ✅
Commit `0f600c7`. QUL website is JS-gated, but found `Waqar144/Quran_Mutashabihat_Data` (CC0) on GitHub instead.

- 1,344 raw entries → 2,712 unique src→dst pairs → 3,270 directional `:SIMILAR_PHRASE` edges (bidirectional MERGE)
- Provenance: `dataSource='waqar144-mutashabiha'`
- Spot-check: `[107:3]` "And does not advocate the feeding of the poor" → `[69:34]` "Nor did he advocate the feeding of the poor" ✓

### H1: PPR hyperparameter sweep ✅ (definitive negative)
Commit `6d1d782`. 36-config sweep over `(pagerank_alpha, alpha_vector, beta_past, include_similar_phrase)`.

**Best PPR**: hit@10 = 0.5455 (Δ=−0.09 vs vanilla 0.6364).
**No configuration beats vanilla.** Even with the new SIMILAR_PHRASE edges added to the subgraph.

This rules out tuning as the cause. PPR is wrong-tool for QRCD. Reserve for a future multi-hop benchmark.

### M1: FActScore atomic decomposer ✅
Commit `c7a21b4`. Added `_decompose_sentence_atomic()` to citation_verifier.py. Each multi-clause sentence → atomic propositions via OpenRouter `gpt-oss-120b:free`.

Smoke test:
```
in:  "The Quran teaches that God is the Light of the heavens and
      the earth and that His light is exemplified by a niche
      containing a lamp [24:35]."
out: [{claim: "God is the Light of the heavens and the earth.",
       citations: ["24:35"]},
      {claim: "God's light is exemplified by a niche containing a lamp.",
       citations: ["24:35"]}]
```

Switch via `CITATION_DECOMPOSE=atomic`. Composes with M's MiniCheck integration: `CITATION_DECOMPOSE=atomic + CITATION_VERIFIER_MODEL=minicheck` gives the FActScore-pipeline equivalent for verse grounding.

### S1: Sefaria-pattern bidirectional TF-IDF ✅
Commit `8a6e474`. Enriched all **41,138** `:MENTIONS` edges with:
- `from_tfidf` — verse-side salience (how central is keyword K to verse V?)
- `to_tfidf` — keyword-side salience (how much of K's total weight comes from V?)
- `data_source` + `generated_by` (provenance for future writers)

Sample on Ayat al-Kursi by from_tfidf:
- "unawareness" → to_tfidf = 1.0 (verse owns 100% of keyword's mention weight)
- "moment" → to_tfidf = 1.0 (same)
- "slumber" → to_tfidf = 0.34
- "heaven" → to_tfidf = 0.004 (common keyword)

Different rankings depending on which side you query from. Provenance fields prepare for future ingestion paths (QUL topics, LLM-generated edges, manual curation).

### T3: QUL audio timestamps ❌ (deferred)
Same auth-gating issue as the QUL Mutashabihat dataset. The `static-cdn.tarteel.ai/qul/` paths return 403 without browser auth. Tracked as future work — needs either (a) a contributor account on QUL or (b) Chrome MCP automation through their admin UI.

---

## What's now in your environment

### New env vars

```bash
# Citation verification (post-response NLI/MiniCheck check). Off by default.
ENABLE_CITATION_VERIFY=1
CITATION_VERIFIER_MODEL=nli|minicheck       # default: nli
MINICHECK_MODEL=flan-t5-large               # roberta-large | deberta-v3-large | flan-t5-large
MINICHECK_THRESHOLD=0.5                     # support probability cutoff

# Claim decomposition (FActScore-style atomization before verification)
CITATION_DECOMPOSE=regex|atomic             # default: regex
DECOMPOSE_MODEL=openai/gpt-oss-120b:free    # via OpenRouter

# Switch which Neo4j vector index tool_semantic_search uses
SEMANTIC_SEARCH_INDEX=verse_embedding|verse_embedding_m3|verse_embedding_m3_ar
```

### New chat tools

- `get_code19_features(scope, target)` — Khalifa-style arithmetic over Arabic text

### New scripts (run-once)

- `build_code19_features.py` — stamp Code-19 features
- `analyze_graph_structure.py` — degree/betweenness/modularity report
- `embed_verses_m3.py` — re-embed with BGE-M3 (idempotent via source_hash)
- `backfill_embedding_provenance.py` — stamp legacy embeddings with provenance
- `backfill_bidirectional_tfidf.py` — Sefaria-style TF-IDF on MENTIONS edges
- `import_mutashabihat.py` — ingest CC0 mutashabihat as :SIMILAR_PHRASE edges

### New evaluators

- `eval_qrcd_retrieval.py` — pure-retrieval A/B (MiniLM vs BGE-M3-EN vs BGE-M3-AR)
- `eval_qrcd.py` — full /chat agent loop (heavier)
- `eval_qrcd_hipporag.py` — vanilla vs HippoRAG A/B
- `eval_qrcd_hipporag_sweep.py` — 36-config PPR grid

### New API endpoints

- `POST /api/resolve_refs` — find Quranic citations in any text
- `GET /api/verse/<verse_id>` — return one verse with English + Arabic
- `GET /quran_linker.js` — drop-in JS widget for third-party sites

### New static files

- `static/quran_linker.js` — Sefaria-style citation linker
- `static/linker_demo.html` — manual test page

### New report files

- `RESEARCH_2026-04-27.md` — initial research on stack alternatives
- `RESEARCH_2026-04-28_DEEP.md` — deeper dive on 6 sources
- `EVAL_QRCD_REPORT.md` — QRCD benchmark write-up
- `HIPPORAG_REPORT.md` — HippoRAG implementation + negative result
- `AUTONOMOUS_RUN_2026-04-28.md` (this file)

---

## What I'd suggest next (when you're back)

In rough order of value-per-effort:

1. **Try the BGE-M3 path live**: restart `app_free.py` with
   `SEMANTIC_SEARCH_INDEX=verse_embedding_m3`, ask a few questions, see if
   the retrieval quality lift transfers to the agent's answers.

2. **Wire `get_code19_features` into a sample answer**: ask "Why does
   Surah 50 begin with Qaf?" and see if the agent uses the new tool to
   cite the 57=19×3 figure.

3. **Try the JS linker on a real page**: open
   `static/linker_demo.html` in a browser with `app_free.py` running.
   Hover citations to see tooltips.

4. **Re-embed reasoning_memory's :Query nodes with BGE-M3** so the
   HippoRAG past-query seeds aren't garbage on Arabic queries. Then re-run
   the H1 sweep — maybe PPR works on multi-hop queries that QRCD can't
   measure.

5. **Try `CITATION_DECOMPOSE=atomic + CITATION_VERIFIER_MODEL=minicheck`
   on a real /chat response** to see how much of the answer survives the
   strict atomic+MiniCheck pipeline. Will probably surface specific
   over-claims the system has been making.

6. **Build G1 (multi-hop Quran benchmark)** — strategic but L effort.
   Until this exists we can't tell whether *any* graph method (PPR,
   GraphRAG, LightRAG) is justified for QKG. ~200 hand-curated multi-hop
   questions. This is the unblocker for resurrecting Task 6.

---

## Commits this run

```
9cf268f  task 1: code-19 arithmetic features as Neo4j properties + tool
2040742  task 2: MiniCheck-FT5 as alternative citation verifier backend
2754e34  task 3: BGE-M3 multilingual embeddings (additive, env-flag switchable)
1b32a4e  task 4: QRCD benchmark eval — BGE-M3 = 5-94x lift over MiniLM
fde671e  task 5: Sefaria-inspired Quranic citation linker (resolver + API + JS widget)
b0e725d  task 6: HippoRAG-style PPR — implementation + honest negative result
0f600c7  phase 3 T1: ingest mutashabihat similarity edges
6d1d782  phase 3 H1: PPR sweep — definitive negative on QRCD
c7a21b4  phase 3 M1: FActScore-style atomic claim decomposer
8a6e474  phase 3 S1: bidirectional TF-IDF + provenance on MENTIONS edges
(this)   wrap-up report
```

All on `origin/main`. Sleep well.
