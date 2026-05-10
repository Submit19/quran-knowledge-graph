---
type: architecture
subsystem: graph-schema
status: current
date_added: 2026-05-10
---

# Neo4j Graph Schema

## What it does

Stores 6,234 Quranic verses (Khalifa English + Hafs Arabic) plus etymology, morphology, semantic structure, and per-session reasoning traces. All queries are hand-rolled Cypher against the `quran` database — no neo4j-graphrag-python wrapper.

## Where it lives

Neo4j Desktop, `bolt://localhost:7687`, database name `quran` (env `NEO4J_DATABASE`). Schema defined across `build_graph.py`, `embed_verses_m3.py`, `build_arabic_roots.py`, `import_etymology.py`, `reasoning_memory.py`.

## Node labels — Core

| Label | Count | Key properties |
|-------|-------|----------------|
| `Verse` | 6,234 | `verseId` (S:V), `text`, `arabicText`, `arabicPlain`, `surah`, `verseNum`, `surahName`, `embedding` (MiniLM 384d), `embedding_m3` (BGE-M3 EN 1024d), `embedding_m3_ar` (BGE-M3 AR 1024d), `embedding_model`, `is_initial_verse`, `letter_*` (Code-19 features) |
| `Keyword` | 2,636 | `keyword` (Porter-stemmed English lemma) |
| `Concept` | 2,388 | Porter-stem entity-resolved Keyword canonical form |
| `Sura` | 114 | `number`, `verses_count`, `mysterious_letters`, `ml_letter_counts_json`, `mod19_verse_count` |

## Node labels — Etymology

| Label | Count | Key properties |
|-------|-------|----------------|
| `ArabicRoot` | 1,223 | `root` (tri-literal), `rootBW` (Buckwalter), `gloss`, `verseCount` |
| `Lemma` | 4,762+ | `lemma`, `glossEn`, `pos`, `verseCount` |
| `MorphPattern` | 100+ | `pattern` (wazn), `label`, `meaningTendency` |
| `SemanticDomain` | 30+ | `domainId`, `nameEn`, `nameAr`, `description` |
| `WordToken` | (per verse) | `tokenId`, `verseId`, `wordPos`, `arabicText`, `pos`, `morphFeatures`, `wazn`, `translitBW` |

## Node labels — Reasoning Memory

| Label | Key properties |
|-------|----------------|
| `Query` | `queryId`, `text`, `textEmbedding` (384d MiniLM), `timestamp`, `backend`, `deep_dive` |
| `ReasoningTrace` | `traceId`, `total_duration_ms`, `turn_count`, `tool_call_count`, `citation_count`, `status` |
| `ToolCall` | `callId`, `turn`, `order_in_turn`, `tool_name`, `args_json`, `summary`, `ok`, `duration_ms`, `result_citation_count` |
| `Answer` | `answerId`, `text`, `text_hash`, `cited_verses`, `char_count` |
| `CitationCheck` | `checkId`, `ref`, `nli_label`, `score` |

## Relationships

| Type | Count | Direction | Key properties |
|------|-------|-----------|----------------|
| `MENTIONS` | 41K | Verse → Keyword | `score`, `from_tfidf`, `to_tfidf`, `data_source`, `generated_by` |
| `NORMALIZES_TO` | 2,636 | Keyword → Concept | — |
| `RELATED_TO` | 51K | Verse ↔ Verse | `score` (shared rare keywords), capped 12/verse, 93.7% cross-surah |
| `MENTIONS_ROOT` | ~100K | Verse → ArabicRoot | `forms`, `count` |
| `SIMILAR_PHRASE` | 3,270 | Verse ↔ Verse | `dataSource: 'waqar144-mutashabiha'` |
| `SUPPORTS` / `ELABORATES` / `QUALIFIES` / `CONTRASTS` / `REPEATS` | 7K total | Verse ↔ Verse | `score`, `confidence` |
| `CONTAINS` | 6,234 | Sura → Verse | — |
| `NEXT_VERSE` | ~6,120 | Verse → Verse | sequential |
| `TRIGGERED` | — | Query → ReasoningTrace | — |
| `HAS_STEP` | — | ReasoningTrace → ToolCall | `order` |
| `RETRIEVED` | ~32K | ReasoningTrace → Verse | `tool`, `rank`, `turn`, `call_id` |
| `PRODUCED` | — | Query → Answer | — |
| `HAS_CITATION_CHECK` | — | ReasoningTrace → CitationCheck | — |

## Vector indexes

| Name | Dimensions | Model | Node.property |
|------|-----------|-------|---------------|
| `verse_embedding` | 384 | all-MiniLM-L6-v2 (legacy) | Verse.embedding |
| `verse_embedding_m3` | 1024 | BAAI/bge-m3 EN | Verse.embedding_m3 |
| `verse_embedding_m3_ar` | 1024 | BAAI/bge-m3 AR | Verse.embedding_m3_ar |
| `query_embedding` | 384 | all-MiniLM-L6-v2 | Query.textEmbedding |

## Full-text indexes

| Name | Analyzer | Covers |
|------|----------|--------|
| `verse_text_fulltext` | English | Verse.text |
| `verse_arabic_fulltext` | Arabic | Verse.arabicPlain |

## Cross-references
- [[overview]]
- [[retrieval-pipeline]] — which indexes each retrieval stage queries
- [[reasoning-memory]] — the Query/Trace/ToolCall subgraph detail
- ADRs: [[../decisions/0002-bge-m3-over-minilm]]
- Source: `repo://CLAUDE.md` (Neo4j Graph Schema section), `repo://edge_schema.md`
