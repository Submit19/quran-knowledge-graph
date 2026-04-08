# Quran Knowledge Graph -- Neo4j Audit Report

**Date:** 2026-03-31
**Database:** `quran` on `bolt://localhost:7687`
**Status:** READ-ONLY analysis -- no modifications made

---

## 1. Node Inventory

### 1.1 Summary

| Metric | Value |
|---|---|
| **Total nodes** | 15,355 |
| **Unlabeled nodes** | 0 |
| **Distinct labels** | 3 |

### 1.2 Node Labels and Counts

| Label | Count |
|---|---|
| Verse | 12,580 |
| Keyword | 2,661 |
| Sura | 114 |

### 1.3 Property Keys per Label

**Verse** -- Two distinct schemas coexist (see Section 3 for analysis):

| Property | Frequency | Notes |
|---|---|---|
| `text` | 12,580 | Present on all verses |
| `number` | 6,346 | Old schema only |
| `reference` | 6,346 | Old schema only (format: `"3:19"`) |
| `sura` | 6,346 | Old schema only |
| `verseId` | 6,234 | New schema only (format: `"100:1"`) |
| `surah` | 6,234 | New schema only |
| `verseNum` | 6,234 | New schema only |
| `surahName` | 6,234 | New schema only (e.g., "The Gallopers") |
| `embedding` | 6,234 | New schema only (vector) |

**Keyword:**

| Property | Frequency |
|---|---|
| `keyword` | 2,661 |

**Sura:**

| Property | Frequency |
|---|---|
| `number` | 114 |

### 1.4 Sample Values

**Old-schema Verse:** `{reference: "3:19", sura: 3, number: 19, text: "The Quran specifies three messengers..."}`

**New-schema Verse:** `{verseId: "100:1", surah: 100, verseNum: 1, surahName: "The Gallopers", text: "By the fast gallopers.", embedding: [...]}`

**Keyword:** `{keyword: "ablution"}`, `{keyword: "righteous"}`, etc.

**Sura:** `{number: 1}` through `{number: 114}`

---

## 2. Edge Inventory

### 2.1 Summary

| Metric | Value |
|---|---|
| **Total relationships** | 109,375 |
| **Distinct relationship types** | 4 |

### 2.2 Relationship Types and Counts

| Type | Count | Source -> Target | Has Properties |
|---|---|---|---|
| `RELATED_TO` | 51,733 | Verse -> Verse | Yes (`score`) |
| `MENTIONS` | 45,064 | Verse -> Keyword | Yes (`score`) |
| `CONTAINS` | 6,346 | Sura -> Verse | No |
| `NEXT_VERSE` | 6,232 | Verse -> Verse | No |

### 2.3 Relationship Properties

**RELATED_TO** -- `score` property on all 51,733 edges:

| Stat | Value |
|---|---|
| Min | 0.2455 |
| Max | 3.8185 |
| Average | 0.8058 |

**MENTIONS** -- `score` property on all 45,064 edges:

| Stat | Value |
|---|---|
| Min | 0.0400 |
| Max | 1.0000 |
| Average | 0.3389 |

**CONTAINS** and **NEXT_VERSE** -- no properties (bare structural edges).

### 2.4 Schema Ownership of Relationships

| Relationship | Old Schema (reference) | New Schema (verseId) |
|---|---|---|
| `CONTAINS` | 6,346 | 0 |
| `NEXT_VERSE` | 6,232 | 0 |
| `RELATED_TO` | 0 | 51,733 |
| `MENTIONS` | 0 | 45,064 |

**Key finding:** The two verse populations are completely isolated from each other. Old-schema verses carry structural relationships (`CONTAINS`, `NEXT_VERSE`), while new-schema verses carry semantic relationships (`RELATED_TO`, `MENTIONS`). There are zero cross-schema relationships.

---

## 3. Data Quality Issues

### 3.1 Dual-Schema Problem (Critical)

The database contains **two completely separate populations** of Verse nodes with incompatible schemas and no shared properties (except `text`):

| Population | Count | Identifying Property | Relationships |
|---|---|---|---|
| Old schema | 6,346 | `reference` (e.g., `"3:19"`) | CONTAINS, NEXT_VERSE |
| New schema | 6,234 | `verseId` (e.g., `"100:1"`) | RELATED_TO, MENTIONS |
| **Overlap** | **0** | No node has both `reference` and `verseId` | No cross-schema edges |

The old schema includes 112 bismillah entries (verse number 0) that the new schema omits. Excluding those, both populations contain 6,234 numbered verses. Approximately 4,941 verse texts are identical across both populations, confirming these are duplicate representations of the same content.

**Impact:** Any query that traverses both structural and semantic relationships will fail silently -- it will never cross from one population to the other.

### 3.2 NULL Property Analysis

| Property | NULL Count | Total Verses | Notes |
|---|---|---|---|
| `text` | 0 | 12,580 | All verses have text |
| `number` | 6,234 | 12,580 | Missing on new-schema verses |
| `reference` | 6,234 | 12,580 | Missing on new-schema verses |
| `sura` | 6,234 | 12,580 | Missing on new-schema verses |
| `verseId` | 6,346 | 12,580 | Missing on old-schema verses |
| `surah` | 6,346 | 12,580 | Missing on old-schema verses |
| `verseNum` | 6,346 | 12,580 | Missing on old-schema verses |
| `surahName` | 6,346 | 12,580 | Missing on old-schema verses |
| `embedding` | 6,346 | 12,580 | Missing on old-schema verses |

All NULLs are explained by the dual-schema split -- within each population, all expected properties are fully populated.

### 3.3 Empty Strings

| Check | Count |
|---|---|
| Verse `text = ""` | 0 |
| Verse `reference = ""` | 0 |
| Verse `surahName = ""` | 0 |
| Keyword `keyword = ""` | 0 |

No empty string issues found.

### 3.4 Duplicate Verses

- No duplicate `reference` values found in old-schema verses.
- No duplicate `verseId` values found in new-schema verses.
- Uniqueness constraints enforce this at the database level.

However, **4,065 text values are shared** across the 12,580 total verses. This is primarily because approximately 4,941 old-schema and new-schema verses represent the same content with identical text. There are also a small number of legitimately repeated short phrases in the Quran itself.

### 3.5 Inconsistent Keywords

No case-insensitive duplicates found among the 2,661 keywords. All keywords appear to be consistently lowercased.

### 3.6 Orphan Nodes

**33 new-schema Verse nodes have zero relationships.** These are mostly short verses (Muqatta'at / disconnected letters and brief phrases) that apparently failed to generate meaningful keyword or similarity connections:

| verseId | Text (sample) |
|---|---|
| 2:1 | A.L.M. |
| 3:1 | A.L.M. |
| 20:1 | T. H. |
| 28:1 | T. S. M. |
| 29:1, 30:1, 31:1, 32:1 | A. L. M. |
| 40:1 through 46:1 | H. M. |
| 42:2 | `A. S. Q. |
| 73:1 | O you cloaked one. |
| 74:3 | Extol your Lord. |
| 74:27 | What retribution! |
| 86:16 | But so do I. |
| 89:3 | By the even and the odd. |
| 114:3 | "The god of the people. |

All old-schema verses have at least one relationship (via `CONTAINS` from their Sura).

---

## 4. Coverage Check

### 4.1 Totals

| Metric | Value |
|---|---|
| Total Verse nodes | 12,580 |
| Old-schema verses (with bismillah) | 6,346 |
| New-schema verses (no bismillah) | 6,234 |
| Expected unique numbered verses (standard Quran) | 6,236 |
| Surahs represented | 114 (all present in both schemas) |
| Sura nodes | 114 |

### 4.2 New-Schema Verses vs. Expected (Standard Quran)

The new-schema population matches expected verse counts exactly for 113 of 114 surahs. The one exception:

| Surah | Expected | Actual | Difference |
|---|---|---|---|
| 9 (At-Tawbah) | 129 | 127 | -2 |

**Verses 128 and 129 of Surah 9 are missing** from both the old and new schema. This is a known theological position in certain Quran translations (the Rashad Khalifa / "Authorized Version" translation considers these two verses to be later additions). The translation used appears to be this version.

### 4.3 Old-Schema Verses vs. Expected

The old schema has expected count + 1 for 112 surahs (the +1 being bismillah as verse 0). The exceptions:

- **Surah 1 (Al-Fatiha):** Matches expected (7) with no verse 0 -- the bismillah is integrated as verse 1.
- **Surah 9 (At-Tawbah):** Has 127 verses (no verse 0, and missing 128-129) -- Surah 9 traditionally has no bismillah, and the two disputed verses are absent.

### 4.4 Verse Counts by Surah (New Schema)

| Surah | Actual | Expected | | Surah | Actual | Expected | | Surah | Actual | Expected |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 7 | 7 | | 39 | 75 | 75 | | 77 | 50 | 50 |
| 2 | 286 | 286 | | 40 | 85 | 85 | | 78 | 40 | 40 |
| 3 | 200 | 200 | | 41 | 54 | 54 | | 79 | 46 | 46 |
| 4 | 176 | 176 | | 42 | 53 | 53 | | 80 | 42 | 42 |
| 5 | 120 | 120 | | 43 | 89 | 89 | | 81 | 29 | 29 |
| 6 | 165 | 165 | | 44 | 59 | 59 | | 82 | 19 | 19 |
| 7 | 206 | 206 | | 45 | 37 | 37 | | 83 | 36 | 36 |
| 8 | 75 | 75 | | 46 | 35 | 35 | | 84 | 25 | 25 |
| 9 | **127** | **129** | | 47 | 38 | 38 | | 85 | 22 | 22 |
| 10 | 109 | 109 | | 48 | 29 | 29 | | 86 | 17 | 17 |
| 11 | 123 | 123 | | 49 | 18 | 18 | | 87 | 19 | 19 |
| 12 | 111 | 111 | | 50 | 45 | 45 | | 88 | 26 | 26 |
| 13 | 43 | 43 | | 51 | 60 | 60 | | 89 | 30 | 30 |
| 14 | 52 | 52 | | 52 | 49 | 49 | | 90 | 20 | 20 |
| 15 | 99 | 99 | | 53 | 62 | 62 | | 91 | 15 | 15 |
| 16 | 128 | 128 | | 54 | 55 | 55 | | 92 | 21 | 21 |
| 17 | 111 | 111 | | 55 | 78 | 78 | | 93 | 11 | 11 |
| 18 | 110 | 110 | | 56 | 96 | 96 | | 94 | 8 | 8 |
| 19 | 98 | 98 | | 57 | 29 | 29 | | 95 | 8 | 8 |
| 20 | 135 | 135 | | 58 | 22 | 22 | | 96 | 19 | 19 |
| 21 | 112 | 112 | | 59 | 24 | 24 | | 97 | 5 | 5 |
| 22 | 78 | 78 | | 60 | 13 | 13 | | 98 | 8 | 8 |
| 23 | 118 | 118 | | 61 | 14 | 14 | | 99 | 8 | 8 |
| 24 | 64 | 64 | | 62 | 11 | 11 | | 100 | 11 | 11 |
| 25 | 77 | 77 | | 63 | 11 | 11 | | 101 | 11 | 11 |
| 26 | 227 | 227 | | 64 | 18 | 18 | | 102 | 8 | 8 |
| 27 | 93 | 93 | | 65 | 12 | 12 | | 103 | 3 | 3 |
| 28 | 88 | 88 | | 66 | 12 | 12 | | 104 | 9 | 9 |
| 29 | 69 | 69 | | 67 | 30 | 30 | | 105 | 5 | 5 |
| 30 | 60 | 60 | | 68 | 52 | 52 | | 106 | 4 | 4 |
| 31 | 34 | 34 | | 69 | 52 | 52 | | 107 | 7 | 7 |
| 32 | 30 | 30 | | 70 | 44 | 44 | | 108 | 3 | 3 |
| 33 | 73 | 73 | | 71 | 28 | 28 | | 109 | 6 | 6 |
| 34 | 54 | 54 | | 72 | 28 | 28 | | 110 | 3 | 3 |
| 35 | 45 | 45 | | 73 | 20 | 20 | | 111 | 5 | 5 |
| 36 | 83 | 83 | | 74 | 56 | 56 | | 112 | 4 | 4 |
| 37 | 182 | 182 | | 75 | 40 | 40 | | 113 | 5 | 5 |
| 38 | 88 | 88 | | 76 | 31 | 31 | | 114 | 6 | 6 |

No missing surahs. No surahs with 0 verses. Only Surah 9 deviates from the standard count.

---

## 5. Edge Quality

### 5.1 Classification

| Type | Category | Count | Has Score/Weight | Purpose |
|---|---|---|---|---|
| `RELATED_TO` | Semantic (meaningful) | 51,733 | Yes (similarity score) | Verse-to-verse semantic similarity |
| `MENTIONS` | Semantic (meaningful) | 45,064 | Yes (relevance score) | Verse-to-keyword association |
| `CONTAINS` | Structural (generic) | 6,346 | No | Surah contains verse |
| `NEXT_VERSE` | Structural (specific) | 6,232 | No | Sequential ordering |

### 5.2 Quality Metrics

| Metric | Value |
|---|---|
| **Total edges** | 109,375 |
| **Edges with properties (scored)** | 96,797 (88.5%) |
| **Edges without properties** | 12,578 (11.5%) |
| **Semantically meaningful edges** | 96,797 (88.5%) |
| **Structural/generic edges** | 12,578 (11.5%) |

The graph is heavily weighted toward semantic relationships. The `RELATED_TO` and `MENTIONS` edges both carry numeric scores, enabling weighted traversals and ranked results.

### 5.3 Observations

- `NEXT_VERSE` count (6,232) is 2 fewer than expected (6,234 - 114 = 6,120 within-surah links + 113 cross-surah links = 6,233). The count is close but may have minor chain breaks.
- `CONTAINS` count (6,346) matches old-schema verse count exactly, confirming every old-schema verse belongs to a surah.
- The new-schema verses have **no structural relationships** (no CONTAINS, no NEXT_VERSE), only semantic ones.

---

## 6. Top 20 Most Connected Nodes

| Rank | Type | Identifier | Degree |
|---|---|---|---|
| 1 | Keyword | disbelieve | 298 |
| 2 | Keyword | know | 296 |
| 3 | Sura | Sura 2 (Al-Baqarah) | 287 |
| 4 | Keyword | send | 279 |
| 5 | Keyword | among | 275 |
| 6 | Keyword | righteous | 274 |
| 7 | Keyword | may | 258 |
| 8 | Keyword | life | 252 |
| 9 | Keyword | everything | 243 |
| 10 | Sura | Sura 26 (Ash-Shu'ara) | 228 |
| 11 | Keyword | would | 225 |
| 12 | Keyword | make | 225 |
| 13 | Keyword | heaven | 220 |
| 14 | Keyword | revelation | 209 |
| 15 | Sura | Sura 7 (Al-A'raf) | 207 |
| 16 | Keyword | good | 204 |
| 17 | Keyword | see | 202 |
| 18 | Sura | Sura 3 (Al-Imran) | 201 |
| 19 | Keyword | believer | 198 |
| 20 | Keyword | guide | 198 |

**Observations:**
- Keywords dominate the top-connected list (16 of 20), which is expected since each keyword connects to many verses via `MENTIONS`.
- The 4 Sura nodes that appear are the longest surahs (2, 26, 7, 3), with degree driven by `CONTAINS` relationships.
- Some top keywords are generic/functional words ("may", "would", "make", "among") rather than theologically significant terms, suggesting keyword extraction could benefit from better stopword filtering.
- Theologically meaningful keywords like "disbelieve", "righteous", "heaven", "revelation", "believer", and "guide" appropriately rank high.

---

## 7. Database Indexes and Constraints

### 7.1 Constraints (Uniqueness)

| Name | Label | Property |
|---|---|---|
| `verse_ref` | Verse | `reference` |
| `verse_id` | Verse | `verseId` |
| `sura_num` | Sura | `number` |
| `kw_id` | Keyword | `keyword` |

### 7.2 Indexes

| Name | Type | Label | Property |
|---|---|---|---|
| `verse_ref` | RANGE | Verse | `reference` |
| `verse_id` | RANGE | Verse | `verseId` |
| `verse_surah` | RANGE | Verse | `surah` |
| `verse_embedding` | VECTOR | Verse | `embedding` |
| `sura_num` | RANGE | Sura | `number` |
| `kw_id` | RANGE | Keyword | `keyword` |

The vector index on `embedding` enables similarity search on the new-schema verses.

---

## 8. Summary of Findings

### Critical Issues

1. **Dual-schema fragmentation:** The database contains two isolated populations of Verse nodes (6,346 old-schema + 6,234 new-schema) with zero cross-population relationships. This means structural traversals (surah containment, sequential reading order) and semantic traversals (similarity, keyword mentions) operate on entirely separate node sets. Any application querying across both relationship types will get incomplete or empty results.

2. **Missing verses 9:128-129:** Both populations are missing the last two verses of Surah At-Tawbah. This is consistent with the Rashad Khalifa translation but deviates from the standard 6,236-verse Quran.

### Moderate Issues

3. **33 orphan verses** in the new schema have no relationships at all. Most are Muqatta'at (disconnected letters) or very short phrases that likely produced no meaningful keyword matches or similarity scores above threshold.

4. **No embeddings on old-schema verses:** The 6,346 old-schema verses lack the `embedding` property, so they cannot participate in vector similarity search.

5. **Generic keywords in top connections:** Words like "may", "would", "make", "among" appear as highly connected keywords, suggesting the keyword extraction did not adequately filter common English function words.

### Positive Findings

- All 114 surahs are represented with correct verse counts (except the intentional 9:128-129 omission).
- No empty strings, no duplicate identifiers, no unlabeled nodes, no case-inconsistent keywords.
- Uniqueness constraints properly enforce data integrity.
- 88.5% of all edges carry a numeric score, enabling weighted/ranked graph queries.
- Vector index is in place for embedding-based similarity search.

### Recommended Actions

1. **Merge the two verse populations** into a single unified schema, consolidating properties and relationships onto one set of Verse nodes.
2. **Generate embeddings** for any verses currently lacking them.
3. **Connect the 33 orphan verses** to at least their parent Sura and adjacent verses.
4. **Review keyword extraction** to filter out generic function words, or at minimum add a `stopword` flag to distinguish them from theologically meaningful terms.
5. **Decide on 9:128-129** -- either add them if completeness is desired, or document the translation choice explicitly in the graph metadata.
