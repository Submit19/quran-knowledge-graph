# Tool Description Audit — `from_neo4j_yt_mcp_tool_description_audit`

**Date:** 2026-05-12  
**Task:** Audit and rewrite all 21 chat.py tool descriptions for LLM routing clarity.  
**Sources:** 3 NODES videos + 1 blog post (synthesis-promoted, priority 70→80).

---

## Audit Summary

All 21 tool descriptions were reviewed against the criteria: clear when-to-use, when-NOT-to-use, and expected output shape. The descriptions were already partially routing-optimized from prior work, but several had ambiguous priority ordering and missing primary-use guidance.

## Tools reviewed — no changes needed (14/21)

These already met all three criteria with clear decision boundaries and output shapes:

- `get_verse` — clear ID-known use case, explicit "explore first" redirect
- `traverse_topic` — multi-keyword use case clearly stated
- `find_path` — explicit "have both IDs first" gate
- `explore_surah` — surah-summary use case clear, includes dense-surah tip
- `query_typed_edges` — use-after-get_verse pattern explicit
- `search_arabic_root` — root vs form distinction clear
- `compare_arabic_usage` — form-comparison distinction clear
- `lookup_word` — word vs root distinction clear
- `explore_root_family` — derivative tree use case explicit
- `get_verse_words` — verse-grammar use case clear
- `search_semantic_field` — domain overview vs root drill-down clear
- `lookup_wujuh` — wujuh/polysemy use case and fallback explicit
- `search_morphological_pattern` — morphology query routing clear
- `get_code19_features` — math miracle / Code-19 routing clear

## Tools rewritten (6/21)

### `search_keyword`
**Issue:** No explicit guidance to prefer concept_search for English concepts.  
**Fix:** Added "PREFER concept_search over this tool for any common English concept" as leading guidance.

### `semantic_search`
**Issue:** Fallback role not prominent enough — "USE WHEN" was before the fallback context.  
**Fix:** Added "USE AS FALLBACK when concept_search returns no results" as a distinct labeled line.

### `concept_search`
**Issue:** Didn't explicitly state it supersedes search_keyword.  
**Fix:** Added "This supersedes search_keyword for English concepts — always prefer concept_search."

### `hybrid_search`
**Issue:** Arabic-script routing not labeled as PRIMARY use case.  
**Fix:** Added "USE AS PRIMARY TOOL when the query is in Arabic script — always set lang='ar'" as the first USE clause.

### `recall_similar_query`
**Issue:** "USE AT THE START" was buried after other USE WHEN clauses.  
**Fix:** Moved playbook-first guidance to the top: "CALL THIS FIRST at the start of any turn before using other retrieval tools."

### `run_cypher`
**Issue:** "Last resort" message was weak — description started with capabilities, not restriction.  
**Fix:** Added "LAST RESORT — only use when no specialised tool covers the use case" as the opening phrase.

---

## Routing decision tree (for reference)

```
Question received
├─ recall_similar_query (always first — shortcut if past answer exists)
│
├─ Query in Arabic script?
│   └─ YES → hybrid_search(lang='ar')
│
├─ Single canonical English concept (faith, mercy, prayer...)?
│   └─ YES → concept_search → [no results] → semantic_search
│
├─ Specific proper name / rare phrase / transliteration?
│   └─ YES → hybrid_search(lang='en')
│
├─ Abstract multi-word phrase?
│   └─ YES → semantic_search
│
├─ Known verse IDs?
│   ├─ One ID → get_verse → query_typed_edges
│   └─ Two IDs → find_path
│
├─ Arabic root / morphology query?
│   ├─ root occurrences → search_arabic_root
│   ├─ form comparison → compare_arabic_usage
│   ├─ derivative tree → explore_root_family
│   ├─ specific word → lookup_word
│   ├─ wujuh/polysemy → lookup_wujuh
│   └─ morphological pattern → search_morphological_pattern
│
├─ Whole surah?
│   └─ explore_surah
│
├─ Multi-keyword thematic sweep?
│   └─ traverse_topic
│
├─ Code-19 / letter counts?
│   └─ get_code19_features
│
└─ Aggregation / custom count / no tool covers it?
    └─ run_cypher (last resort)
```

---

## Files modified

- `chat.py` — 6 tool descriptions updated (lines ~1651–2210)
