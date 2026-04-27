# QKG Deep-Dive Research: 6 Sources, Concrete Next Tasks

*Deep-dive follow-up to RESEARCH_2026-04-27.md after the first six tasks
landed. Compiled 2026-04-28.*

## 1. Sefaria Topic + RefTopicLink Architecture

The Sefaria stack centers on three Mongo collections that compose into a weighted, hierarchical, provenance-rich topic graph. Pulling the actual schema from `sefaria/model/topic.py`:

**`Topic`** — required `slug`, `titles`; optional `subclass` (e.g. `PersonTopic`, `AuthorTopic`), `alt_ids`, `properties`, `description` (per-language dict), `categoryDescription`, `isTopLevelDisplay`, `numSources` (count of refLinks, denormalized), `parasha`, `ref`, `isAmbiguous`, `data_source`, `image`, `portal_slug`.

**`RefTopicLink`** — required `ref`, `expandedRefs`, `is_sheet`; optional `charLevelData` (sub-verse anchoring), `unambiguousToTopic`, `descriptions` (per-language dict with `title`, `prompt`, **`primacy`** — a hand-curated promotion signal). Inherits `order`, `dataSource`, `generatedBy` from `TopicLinkHelper`.

**`IntraTopicLink`** — required `fromTopic`, `toTopic`, `linkType`, `class`, `dataSource`. Vocabulary of `linkType`: `'is-a'` (taxonomic, traversed by `get_types()` for ancestor lookup with cycle prevention), `'is-category-of'` (inverse), `'displays-under'` (display-only, decoupled from semantic isa), `'related-to'`, `'possibility-for'`. The `order` dict carries `custom_order` (manual override that "trumps" everything), `fromTfidf`, `toTfidf` — directional TF-IDF so the same link reads differently from each side.

Five patterns directly portable to QKG, distilled:

1. **Decouple `is-a` from `displays-under`.** Sefaria runs two parallel hierarchies — semantic ancestry vs UI nesting. QKG currently conflates these in its semantic-domain layer.
2. **Per-link `descriptions` with language and `primacy`.** Each (Topic, Verse) link carries its own learning-prompt text, not a generic verse blurb. QKG should store `{en, ar}` prompts on the edge, not the node.
3. **Bidirectional TF-IDF on every link.** A given verse's salience inside a topic ≠ topic's salience inside a verse — store both, query whichever side is the entry point.
4. **`expandedRefs` denormalization.** Range-refs are pre-expanded into atomic verse keys at write time so range-vs-single queries hit the same index.
5. **`charLevelData`** for sub-verse anchoring — pin a topic to a phrase, not the whole verse. Critical for Arabic where one ayah can carry 5+ themes.
6. **`numSources` denormalized counter** on Topic for cheap leaderboard sorting.
7. **`dataSource` + `generatedBy` on every edge** — Sefaria explicitly tracks whether a link came from "sefaria-project", "aspaklaria", an LLM, or human curation. QKG's HippoRAG-derived edges and human-curated edges should carry this provenance so we can A/B them.

**→ Concrete tasks:**

**S1. RefTopicLink-style edge schema with bidirectional TF-IDF + provenance** *(Effort: M, Risk: low)*

**S2. Split semantic `IS_A` from display `DISPLAYS_UNDER`** *(Effort: S, Risk: low)*

---

## 2. MiniCheck Claim Decomposition (the Gap)

MiniCheck operates at sentence granularity — `MiniCheck(document, sentence) → [0,1]`. The README is explicit: "the claim should first be broken up into sentences." The repo ships **no atomization tooling**. This means QKG's regex sentence-splitter isn't a stopgap — it's exactly what the upstream library expects, but for Arabic-rich citations it's wrong.

The right reference is **FActScore / SAFE-style atomic-fact decomposition** — break a sentence into independently-verifiable propositions, not just sentences.

**→ Concrete tasks:**

**M1. FActScore-style atomic decomposer in front of MiniCheck/NLI** *(Effort: M, Risk: medium)*

**M2. VeriScore-style verifiability gate** *(Effort: S, Risk: low)*

---

## 3. HippoRAG: Why Our PPR Failed and What to Try Next

From `src/hipporag/HippoRAG.py:graph_search_with_fact_entities()`, the personalization vector is **bimodal**: phrase nodes get weight from reranked OpenIE-fact scores normalized by entity occurrence count, passage nodes get a flat `passage_node_weight` (default **0.05**), then `node_weights = phrase_weights + passage_weights` is fed to igraph's `personalized_pagerank` as `reset_prob`.

The failure mode the team saw on QRCD likely traces to one of three things: (a) Arabic OpenIE is sparse, so fact edges are too few — almost all PPR mass lives on the synonym-edge backbone, which collapses to dense retrieval; (b) `passage_node_weight=0.05` is the HippoRAG-1 default; HippoRAG-2 ablations (arxiv 2502.14802) show this needs to be tuned per dataset, often 0.3–0.5 for short-context retrieval; (c) on QRCD the queries are short and single-hop, which the GraphRAG-Bench paper (next section) confirms is exactly where graph methods underperform.

**→ Concrete tasks:**

**H1. Re-run PPR with HippoRAG-2 dual-node + tuned passage_node_weight grid** *(Effort: S, Risk: medium)*

**H2. Replace OpenIE with Quranic Arabic Corpus syntactic edges** *(Effort: M, Risk: medium)*

**H3. "Simpler personalization" baseline: lemma-walk** *(Effort: S, Risk: low)*

---

## 4. GraphRAG-Bench Decision Tree (predicts our negative result)

| Task type | Winner | Numbers |
|---|---|---|
| **Single-hop fact retrieval** | **Basic RAG** | 83.21% Evidence Recall vs HippoRAG2 70.29% |
| **Multi-hop reasoning** | **HippoRAG** | 87.91% ER vs RAG 64.47% |
| **Summarization / contextual synthesis** | **HippoRAG / HippoRAG2** | 90.95% / 87.82% vs RAG 73.38% |

Cost-per-query, normalized: MS-GraphRAG ~331K tokens (global mode), LightRAG ~100K, LazyGraphRAG ~7K, **HippoRAG2 ~1K**. HippoRAG2 is the cost-quality Pareto winner on multi-hop; Basic RAG on single-hop.

**This paper directly predicts QKG's QRCD result.** QRCD is a short-query, single-hop verse-retrieval benchmark — exactly the regime where the paper says basic RAG dominates. The negative result isn't a bug; it's the paper's headline finding.

**→ Concrete tasks:**

**G1. Build a multi-hop Quran benchmark** *(Effort: L, Risk: low)*

**G2. Add task router that picks RAG vs GraphRAG per query** *(Effort: M, Risk: medium)*

---

## 5. Tarteel QUL — Ingestion Targets

QUL exposes via `qul.tarteel.ai/resources` (sqlite + SQL dumps, MIT-licensed):

- **Ayah Topics**: 2,512 topics with semantic relations between them
- **Mutashabihat**: 5,277 similar-phrase pairs; **Similar ayahs**: 4,001 entries
- **Mukhtasar tafsir** (32) + **Detailed tafsir** (82) = 114 tafsir works
- **Audio** with word-level timestamps

**→ Concrete tasks:**

**T1. Ingest Mutashabihat + Similar-Ayahs as `:SIMILAR_PHRASE` and `:SIMILAR_AYAH` edges** *(Effort: S, Risk: low)*

**T2. Ingest QUL ayah-topics as a parallel topic ontology** *(Effort: M, Risk: medium)*

**T3. Ingest word-level recitation timestamps** *(Effort: S, Risk: low)*

---

## 6. Doha Historical Dictionary RAG

DHDA: **~300,000 lexical entries**, **~1B-word dated text corpus**, sources spanning **400 AD inscriptions → pre-Islamic poetry → early Islamic → classical → modern**. This is a strict superset of QAC on the diachronic axis.

**→ Concrete tasks:**

**D1. Add diachronic attestations to existing `Lemma` nodes** *(Effort: L, Risk: medium)*

**D2. Mirror Doha's intent router for our citation-verifier API** *(Effort: M, Risk: low)*

---

## Prioritized Next Tasks (ROI ÷ effort)

| Rank | Task | Effort | Why now |
|---|---|---|---|
| **1** | **T1**: Ingest QUL Mutashabihat + Similar-Ayahs (9,278 edges) | S | Free, scholarly-vetted, immediately enriches the graph |
| **2** | **H1**: PPR hyperparameter sweep + edge-sign sanity check | S | The "negative result" might be a 4-line fix |
| **3** | **S1**: RefTopicLink edge schema with bidirectional TF-IDF + provenance | M | Foundation for every future tagger (blocks T2) |
| **4** | **M1**: FActScore atomic-claim decomposer in front of MiniCheck/NLI | M | Direct lift on the already-shipped citation verifier |
| **5** | **G1**: Multi-hop Quran benchmark | L | Strategic — gates the whole graph-retrieval roadmap |
