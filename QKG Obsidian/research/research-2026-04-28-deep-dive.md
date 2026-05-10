---
type: research
status: done
priority: 75
tags: [research/retrieval, research/schema, research/citation-verify, research/data-sources]
source: RESEARCH_2026-04-28_DEEP.md
date_added: 2026-05-10
---

# Deep-Dive Research: Sefaria, MiniCheck, HippoRAG, GraphRAG-Bench, Tarteel QUL, Doha Dictionary (2026-04-28)

> The full 6-section analysis is at `repo://RESEARCH_2026-04-28_DEEP.md`. This note distills the key decisions and outstanding tasks.

## TL;DR
- Sefaria's `RefTopicLink` schema (bidirectional TF-IDF, per-link `descriptions`, `primacy`, `charLevelData`, `dataSource + generatedBy` provenance) is the most directly actionable architectural blueprint. Five patterns are portable to QKG's typed-edge layer.
- MiniCheck operates at sentence granularity; the repo ships no atomization tooling. FActScore-style atomic-fact decomposition (independently-verifiable propositions, not just sentences) is the correct front-end for QKG's Arabic-rich citations.
- HippoRAG PPR failure traces to: Arabic OpenIE sparsity + `passage_node_weight=0.05` (too low for short-context retrieval) + noisy 200K-edge projection. HippoRAG-2 hyperparameters (0.3–0.5 passage weight, lower damping) may recover it.
- GraphRAG-Bench predicts our QRCD negative result: Basic RAG wins single-hop fact retrieval; HippoRAG wins multi-hop. Build a multi-hop Quran benchmark to test where PPR should win.
- Tarteel QUL provides 9,278 scholarly-vetted similar-phrase / similar-ayah pairs (MIT), 114 tafsir works, word-level audio timestamps — free enrichment for the graph.

## Key findings

**Sefaria schema (5 portable patterns):**
1. Decouple `IS_A` (semantic ancestry) from `DISPLAYS_UNDER` (UI nesting) — currently conflated in QKG's semantic-domain layer.
2. Per-link `descriptions {en, ar}` with `primacy` — each (Topic, Verse) edge carries its own learning-prompt text, not a generic verse blurb.
3. Bidirectional TF-IDF: `fromTfidf` ≠ `toTfidf` — already backfilled in QKG (2026-04).
4. `expandedRefs` denormalization: range-refs pre-expanded to atomic verse keys at write time.
5. `dataSource + generatedBy` on every edge — needed to A/B HippoRAG-derived vs human-curated edges.

**MiniCheck gap**: regex sentence-splitter is what the upstream library expects, but Arabic-rich citations need FActScore-style decomposition (claim → independently-verifiable atomic propositions). `CITATION_DECOMPOSE=atomic` env var already exists; the quality of the decomposer LLM matters.

**GraphRAG-Bench cost comparison**: HippoRAG2 ~1K tokens/query vs MS-GraphRAG ~331K (global). For multi-hop Quran queries, PPR is the correct choice on cost-quality Pareto; wrong to use for single-hop QRCD-style retrieval.

**Tarteel QUL ingestion targets**: Mutashabihat (5,277) + Similar-Ayahs (4,001) = ~9,278 edges — partially ingested as `:SIMILAR_PHRASE` edges (data_source: 'waqar144-mutashabiha'). Full QUL dump adds 2,512 ayah-topics + 114 tafsir works.

## Action verdict
- ✅ Adopt — RefTopicLink-style edge schema with `dataSource + generatedBy` provenance on every edge.
- ✅ Adopt — decouple `IS_A` from `DISPLAYS_UNDER` in semantic-domain layer.
- 🔬 Research deeper — FActScore-style atomic decomposer quality: benchmark different decomposer LLMs on citation accuracy.
- 🔬 Research deeper — HippoRAG-2 parameter sweep: `passage_node_weight` 0.3–0.5, damping 0.5, narrow projection.
- 🔬 Research deeper — multi-hop Quran benchmark (compare/contrast/thematic queries) to validate PPR.
- 🔬 Research deeper — Tarteel QUL full ingest: ayah-topics ontology + remaining tafsir works.
- 🔬 Research deeper — Doha Historical Dictionary diachronic attestations for `Lemma` nodes (high effort, high linguistics value).

## Cross-references
- [[hipporag-negative-result]] — PPR results and re-run recommendations
- [[eval-qrcd-report]] — QRCD baseline that multi-hop benchmark should complement
- [[research-2026-04-27-stack-alternatives]] — parent research that spawned this deep-dive
- Source: `repo://RESEARCH_2026-04-28_DEEP.md`
