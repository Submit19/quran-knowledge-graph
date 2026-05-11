---
type: decision
adr: 0028
status: proposed
date: 2026-05-12
tags: [decision, arabic, retrieval, fulltext, routing]
supersedes: none
---

# ADR-0028 — Arabic fulltext routing: BM25 path via `_is_arabic_query()` in `tool_search_keyword`

## Status
Proposed (2026-05-12). Pending implementation review.

## Context
`tool_search_keyword` has historically used CONTAINS/regex matching on `Verse.arabicPlain`, which is slow (full scan) and provides no relevance ranking or diacritic-normalization. The `verse_arabic_fulltext` BM25 index (Lucene Arabic analyzer) was added by `build_fulltext_index.py` and is used by `hybrid_search`, but `tool_search_keyword` does not use it.

Task `from_neo4j_crawl_arabic_fulltext_index` (commit `a5e250e`) produced a design doc (`data/ralph_agent_from_neo4j_crawl_arabic_fulltext_index.md`) specifying:
- A helper `_is_arabic_query(text)` that detects whether the user query contains Arabic script.
- A BM25 branch in `tool_search_keyword` that calls `db.index.fulltext.queryNodes("verse_arabic_fulltext", kw)` with optional `~1` fuzzy suffix.
- The English/English-transliteration branch remains unchanged (CONTAINS or keyword MENTIONS lookup).
- Expected p95 latency for Arabic keyword searches: ≤200 ms (vs current full-scan which can hit seconds on 6,234 nodes).

## Decision
Add `_is_arabic_query()` routing to `tool_search_keyword` so that Arabic-script queries automatically use the `verse_arabic_fulltext` BM25 index. Default fuzzy distance: 0 (exact), with `~1` available via an optional `fuzzy: bool` parameter to the tool.

## Consequences
- **Positive:** Faster Arabic keyword search (BM25 vs full-scan CONTAINS); relevance-ranked results.
- **Positive:** Diacritic normalization handled by Lucene Arabic analyzer — users without full tashkeel get correct results.
- **Positive:** Zero schema changes — `verse_arabic_fulltext` index already exists.
- **Negative:** Fuzzy matching on Arabic may produce false positives at edit-distance > 1; cap at `~1`.
- **Negative:** Adds a code branch to `tool_search_keyword`; needs integration test with Arabic queries.
- **Neutral:** This is a design doc only — `chat.py` edit and eval validation still pending.

## Cross-references
- Source evidence: commit `a5e250e`, deliverable `data/ralph_agent_from_neo4j_crawl_arabic_fulltext_index.md`
- Related: [[0026-tool-descriptions-as-primary-routing-signal]], `repo://chat.py`, `repo://build_fulltext_index.py`
- See also: `verse_arabic_fulltext` index (Arabic analyzer, Lucene, Verse.arabicPlain)
