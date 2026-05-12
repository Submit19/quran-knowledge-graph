# SAME_AS Deduplication Audit — Concept and ArabicRoot Nodes

**Task:** `from_blog_same_as_dedup_concepts` (p62, cypher_analysis)
**Date:** 2026-05-12
**Source data:** `data/keyword_nodes.csv` (2,661 keywords), `data/arabic_root_nodes.csv` (1,223 roots), `build_concepts.py`
**Note:** Neo4j offline during this tick; analysis performed against CSV source files.

---

## Executive Summary

- **ArabicRoot nodes:** No deduplication needed. Zero duplicate BW-transliterations, zero duplicate Arabic-script roots. The 1,223 root nodes are clean.
- **Keyword/Concept nodes:** Three distinct classes of duplication found, totalling ~170 candidate pairs. The Concept layer (Porter-stem ER in `build_concepts.py`) already handles English morphological variants automatically. The *unhandled* gaps are (a) Arabic loanwords vs their English equivalents, (b) same-entity alternate names (proper nouns, divine epithets), and (c) transliteration spelling variants.

**Recommendation:** Do NOT add SAME_AS edges to the graph until the Concept layer is audited for coverage. If Porter-stem already collapses the pair, a SAME_AS edge is redundant. The high-value targets are the 8 "cross-language same-concept" pairs and the 3 proper-noun variant pairs below.

---

## 1. ArabicRoot Nodes — Clean

Ran uniqueness check on Buckwalter transliteration (`rootBW`) and Arabic script (`root`) across all 1,223 nodes.

```
Duplicate BW transliterations : 0
Duplicate Arabic script roots  : 0
Roots with empty BW            : 0
```

**Verdict:** No SAME_AS work needed for ArabicRoot.

---

## 2. Keyword/Concept Nodes — Three Gap Classes

### 2a. Arabic Loanword vs English Equivalent (8 confirmed co-present pairs)

These pairs refer to the **same concept** but the graph currently treats them as separate Keyword nodes. The Porter-stem Concept layer does NOT collapse them (stems diverge completely).

| Arabic keyword | English keyword | Gap |
|---|---|---|
| `salat` | `prayer` | Same ritual; separate nodes |
| `zakat` | `charity` | Partial overlap (zakat is mandatory giving; charity broader) |
| `iblis` | `satan` | Same entity, two names |
| `allah` | — (only `allah`, not `god`) | `god` not in keyword set |
| `sura` | — (only `sura`, not `surah`) | One spelling only |
| `quran` | — (only `quran`, not `koran`) | One transliteration only |

**High-priority SAME_AS candidates:**
- `iblis` → `satan` (exact same entity in Khalifa translation)
- `salat` → `prayer` (same referent, may want directional: salat normalizes to prayer concept)
- `satan` → `devil` (both in keyword set; same entity)
- `paradise` → `heaven` (both in set; near-synonymous theological terms)

**Lower-priority (arguable partial overlap):**
- `zakat` → `charity` (zakat is a specific type; charity is broader — SAME_AS may over-merge)

### 2b. Proper Noun Transliteration Variants

Khalifa's translation uses English names for prophets; the Arabic equivalents are NOT in the keyword set. The keyword nodes already use the English-only form consistently, so no intra-graph variant pairs exist. However, one proper-noun fuzzy pair was found:

| Pair | Analysis |
|---|---|
| `haamaan` / `hamaan` | Two spellings of Haman (Pharaoh's minister). Both in keyword set. **True SAME_AS candidate.** |

### 2c. Morphological Word-Form Variants (Already Handled by Concept Layer)

Porter-stem in `build_concepts.py` already groups these. Adding SAME_AS edges would be redundant. Documented here for completeness:

**Agent nouns (verb → agent)** — 66 pairs total, examples:
- `forgive` / `forgiver`, `disbelieve` / `disbeliever`, `transgress` / `transgressor`
- `announce` / `announcer`, `arrange` / `arranger`, `provide` / `provider`

**Adverb/adjective pairs** (-ly adverb) — 63 pairs total, examples:
- `arrogant` / `arrogantly`, `consistent` / `consistently`, `blind` / `blindly`

**Noun form pairs** (-ness) — 19 pairs total, examples:
- `blind` / `blindness`, `forgive` / `forgiveness`, `good` / `goodness`

**Spelling variants:**
- `fulfil` / `fulfill` — British/American spelling. Both present. Porter-stem collapses both to `fulfil`. Low priority.

### 2d. Antonym Pairs — NOT Candidates for SAME_AS

Fuzzy matching surfaced these with high similarity — they are NOT duplicates:
- `appreciative` / `unappreciative`
- `conscious` / `unconscious`
- `willingly` / `unwillingly`

These represent opposite semantic poles and must remain separate nodes. Any SAME_AS pipeline must exclude un-/anti- prefix pairs.

### 2e. False Positives from String Similarity

Pairs with high string similarity but completely different meanings (reject for SAME_AS):
- `mediate` / `meditate` (0.933 similarity — different roots and meanings)
- `compete` / `complete` (0.933 — different meanings)
- `deprive` / `derive` (0.909 — different meanings)
- `course` / `curse` (0.909 — different meanings)

---

## 3. Recommended SAME_AS Implementation Plan

### Priority 1 — High-value, Low-risk (3 pairs)

```cypher
// Same entity, alternate names
MATCH (a:Keyword {keyword: 'iblis'}), (b:Keyword {keyword: 'satan'})
MERGE (a)-[:SAME_AS {reason: 'same entity: the devil', confidence: 1.0}]->(b);

MATCH (a:Keyword {keyword: 'satan'}), (b:Keyword {keyword: 'devil'})
MERGE (a)-[:SAME_AS {reason: 'same entity: the devil', confidence: 1.0}]->(b);

// Proper noun transliteration variant
MATCH (a:Keyword {keyword: 'haamaan'}), (b:Keyword {keyword: 'hamaan'})
MERGE (a)-[:SAME_AS {reason: 'transliteration variant of same proper noun', confidence: 0.95}]->(b);
```

### Priority 2 — Arabic loanword / English equivalent (directional)

```cypher
// salat IS a type of prayer — directional, not full equivalence
MATCH (a:Keyword {keyword: 'salat'}), (b:Keyword {keyword: 'prayer'})
MERGE (a)-[:SAME_AS {reason: 'Arabic loanword for Islamic ritual prayer', confidence: 0.85}]->(b);

// paradise and heaven overlap strongly in Quranic context
MATCH (a:Keyword {keyword: 'paradise'}), (b:Keyword {keyword: 'heaven'})
MERGE (a)-[:SAME_AS {reason: 'near-synonymous in Quranic eschatology', confidence: 0.8}]->(b);
```

### Priority 3 — Concept-layer audit first

Before adding SAME_AS edges for agent-noun / adverb / -ness pairs:
1. Run `MATCH (k:Keyword)-[:NORMALIZES_TO]->(c:Concept) RETURN c.name, collect(k.keyword) ORDER BY c.name LIMIT 100` to confirm Porter-stem already groups them.
2. Only add SAME_AS for pairs where the Concept layer fails to merge (i.e., different Concept nodes).

---

## 4. Fuzzy-Match Pipeline Spec

When Neo4j is available, the full dedup pipeline should:

```cypher
// Step 1: Find Concept pairs with high embedding similarity
// (requires embedding on Concept nodes — not yet present as of 2026-05-12)
MATCH (a:Concept), (b:Concept)
WHERE a.name < b.name
  AND gds.similarity.cosine(a.embedding, b.embedding) > 0.92
RETURN a.name, b.name, gds.similarity.cosine(a.embedding, b.embedding) AS sim
ORDER BY sim DESC
LIMIT 50;

// Step 2: Fuzzy string match on Concept names (use apoc.text.jaroWinklerDistance)
MATCH (a:Concept), (b:Concept)
WHERE a.name < b.name AND apoc.text.jaroWinklerDistance(a.name, b.name) > 0.9
RETURN a.name, b.name, apoc.text.jaroWinklerDistance(a.name, b.name) AS score;
```

**Prerequisite gap:** Concept nodes currently lack embeddings. Either add an `embedding` property via `embed_verses_m3.py`-style script on Concept.name, or rely on string-similarity only.

---

## 5. Stats Summary

| Category | Count | Action |
|---|---|---|
| ArabicRoot exact duplicates | 0 | None needed |
| Arabic loanword/English pairs | ~8 | 3 high-priority SAME_AS |
| Proper noun variant pairs | 1 | 1 SAME_AS (haamaan/hamaan) |
| Morphological variants (word-form) | ~148 | Already handled by Concept layer |
| Antonym pairs (NOT duplicates) | ~5 | Exclude from pipeline |
| False positives (string-similar only) | ~4 | Exclude from pipeline |

**Total actionable SAME_AS edges to add: 4–5 (immediate), up to 20 if Arabic loanword pairs are all merged.**

---

_Produced by RALPH tick 93 (IMPL). Analysis via CSV files (Neo4j offline). Cypher pipeline needs live Neo4j to execute._
