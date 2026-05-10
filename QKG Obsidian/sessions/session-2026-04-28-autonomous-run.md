---
date: 2026-04-28
type: session-milestone
status: archived
tags: [session, autonomous-run, retrieval, graph-enrichment, milestone]
source: AUTONOMOUS_RUN_2026-04-28.md
---

# Session/milestone: Overnight Autonomous Build — 11 Tasks, 3 Phases

## What the session was about

The largest single build session on the project. The user asked for "plan out these and implement them all while I sleep." Across three phases — six planned tasks, a deep research expansion, and four follow-up tasks from that research — 11 substantive features landed and were committed to `origin/main`. The session also produced a clean negative result on HippoRAG that saved future tuning effort.

## Shipped (concrete artefacts)

- **BGE-M3 multilingual embeddings** (`embed_verses_m3.py`): 6,234 verses re-embedded in 1024-dim EN + AR; switchable via `SEMANTIC_SEARCH_INDEX` env var; old MiniLM untouched
- **QRCD benchmark eval** (`eval_qrcd.py`, `eval_qrcd_retrieval.py`): MAP@10 lifted 5× (MiniLM 0.028 → BGE-M3-EN 0.139); off-the-shelf hits ~38% of fine-tuned AraBERT
- **Code-19 arithmetic features** (`build_code19_features.py`): 6,234 verses + 114 surahs stamped with letter counts, mod-19 indicators; new `get_code19_features` tool; verified Khalifa totals (6,346 = 19×334)
- **MiniCheck-FT5 citation verifier** + **FActScore atomic decomposer**: env-gated backends; composable via `CITATION_DECOMPOSE=atomic + CITATION_VERIFIER_MODEL=minicheck`
- **Sefaria-style ref-resolver + JS linker widget** (`ref_resolver.py`, `static/quran_linker.js`): auto-links Quranic citations on any page; API endpoints `/api/resolve_refs`, `/api/verse/<id>`
- **Bidirectional TF-IDF on 41,138 MENTIONS edges** (`backfill_bidirectional_tfidf.py`): `from_tfidf` + `to_tfidf` + provenance on every Verse→Keyword edge
- **3,270 SIMILAR_PHRASE edges** from CC0 mutashabihat dataset (`import_mutashabihat.py`)
- **HippoRAG PPR** (`hipporag_traverse.py`): implemented but not wired to chat — honest negative result on QRCD documented in `HIPPORAG_REPORT.md`; 36-config grid sweep confirmed no PPR configuration beats vanilla retrieval on QRCD

## Key findings / decisions

- BGE-M3 delivers a 5× MAP@10 lift over MiniLM with no training — the single highest-ROI implementation of the entire project to date.
- HippoRAG underperforms vanilla (hit@10: 0.64 → 0.50, MRR: 0.46 → 0.23) across all 36 hyperparameter configurations. QRCD is single-hop direct-lookup — exactly the regime where GraphRAG-Bench predicts basic RAG wins. Not wired into production.
- The research phase predicted this negative result before it was run — validating the research-before-implement workflow.
- T3 (QUL audio timestamps) was blocked by 403 auth-gating on `static-cdn.tarteel.ai`; needs a contributor account or browser automation.

## What was queued for next time

- Try BGE-M3 path live: restart `app_free.py` with `SEMANTIC_SEARCH_INDEX=verse_embedding_m3` and evaluate answer quality.
- Re-embed `reasoning_memory`'s `:Query` nodes with BGE-M3 so HippoRAG past-query seeds aren't garbage on Arabic queries; then re-run H1 sweep.
- Build G1 multi-hop Quran benchmark (~200 hand-curated questions) — the strategic unblocker for graph retrieval methods.
- Test `CITATION_DECOMPOSE=atomic + CITATION_VERIFIER_MODEL=minicheck` on a real `/chat` response.

## Cross-references

- Original report: `repo://AUTONOMOUS_RUN_2026-04-28.md`
- Research that drove Phase 1: [[session-2026-04-27-research-stack-alternatives]]
- Research that drove Phase 3: [[session-2026-04-28-research-deep-dive]]
- Eval follow-up: [[session-2026-05-07-eval-v1-v2]]
