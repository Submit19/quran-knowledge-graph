# Typed Edge Schema: Replacing Generic RELATED_TO

**Date:** 2026-04-01
**Status:** Design document (read-only analysis, no modifications)

---

## 1. Problem Statement

The current graph has one thematic edge type: `RELATED_TO` (51,798 edges). Every connection between verses is scored by shared-keyword TF-IDF overlap but carries no semantic label. This means:

- "verse A supports verse B" looks identical to "verse A contradicts verse B"
- Near-verbatim refrains (426 exact-text pairs) are weighted the same as thematic elaborations
- Claude cannot filter traversals by relationship meaning (e.g., "show me only verses that qualify this ruling")
- Path-finding returns the shortest keyword-weighted path with no semantic reasoning about *how* verses connect

### Current Score Distribution

| Score Range | Count | % | Character |
|-------------|-------|---|-----------|
| 0.0 - 0.5 | 1,911 | 3.7% | Weak/tangential overlap |
| 0.5 - 1.0 | 41,221 | 79.6% | Moderate thematic overlap (bulk of graph) |
| 1.0 - 1.5 | 7,426 | 14.3% | Strong thematic connection |
| 1.5 - 2.0 | 1,046 | 2.0% | Very strong shared content |
| 2.0 - 2.5 | 165 | 0.3% | Near-parallel passages |
| 2.5+ | 29 | 0.1% | Near-verbatim or identical rulings |

---

## 2. Proposed Relationship Types

### 2.1 REPEATS

**Cypher name:** `REPEATS`
**Definition:** Near-verbatim repetition of text. Same phrase, ruling, or refrain stated in essentially the same words.

**Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `score` | float | Original RELATED_TO score (preserved) |
| `text_similarity` | float | 0.0-1.0, cosine similarity of verse embeddings or Jaccard overlap of tokens |

**Detection heuristic:** Exact text match, or embedding cosine similarity > 0.92, or token Jaccard > 0.70.

**Example pairs from the graph:**

| Pair | Score | Relationship |
|------|-------|-------------|
| 55:13 <-> 55:16 | 1.991 | Identical refrain: "(O humans and jinns,) which of your Lord's marvels can you deny?" |
| 2:136 <-> 3:84 | 3.524 | Near-identical creed statement: "Say, We believe in GOD, and in what was sent down to us..." |
| 27:10 <-> 28:31 | 3.037 | Same narrative moment (Moses and the staff) told in two surahs |
| 20:71 <-> 26:49 | 2.903 | Pharaoh's identical response to believers in two surahs |
| 2:35 <-> 7:19 | 2.834 | Same command to Adam in Paradise, told twice |

**Estimated count:** ~500-700 edges (426 exact-text matches + near-matches above embedding threshold).

---

### 2.2 ELABORATES

**Cypher name:** `ELABORATES`
**Direction:** `(detail)-[:ELABORATES]->(summary)` — the source verse expands on the target verse.
**Definition:** Verse A adds specific detail, examples, or exposition to a concept introduced in verse B. B is the concise statement; A is the expansion.

**Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `score` | float | Original RELATED_TO score |
| `confidence` | float | 0.0-1.0, classifier confidence |
| `basis` | string | What was elaborated: "ruling", "narrative", "concept", "example" |

**Detection heuristic:** High embedding similarity (> 0.75) where one verse is significantly longer than the other (length ratio > 1.5), or where verse A contains specific examples/lists expanding on verse B's general statement.

**Example pairs from the graph:**

| Pair | Score | Relationship |
|------|-------|-------------|
| 4:43 <-> 5:6 | 3.819 | 5:6 elaborates ablution procedure that 4:43 mentions briefly. 4:43 says "nor touched the women" as exception; 5:6 provides the full step-by-step washing procedure |
| 4:11 <-> 4:12 | 3.265 | 4:12 elaborates the spousal inheritance rules that 4:11 establishes for children's inheritance. Sequential verses building a complete inheritance law |
| 2:62 <-> 5:69 | 2.691 | 5:69 restates and elaborates the pluralism principle of 2:62, adding "converts" to the list |

**Estimated count:** ~3,000-5,000 edges.

---

### 2.3 SUPPORTS

**Cypher name:** `SUPPORTS`
**Direction:** `(evidence)-[:SUPPORTS]->(claim)` — the source verse provides evidence or context for the target.
**Definition:** Verse A provides independent evidence, parallel testimony, or reinforcing context for the claim or ruling in verse B. Unlike ELABORATES, the verses address the topic from different angles rather than one expanding the other.

**Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `score` | float | Original RELATED_TO score |
| `confidence` | float | 0.0-1.0, classifier confidence |

**Detection heuristic:** High thematic overlap (score > 1.0) between verses in different surahs, where neither is a verbatim repeat and neither clearly elaborates the other. Both make independent statements about the same topic.

**Example pairs from the graph:**

| Pair | Score | Relationship |
|------|-------|-------------|
| 27:3 <-> 31:4 | 3.151 | Independent descriptions of righteous believers: both list Salat, Zakat, and certainty in the Hereafter, in different surahs with different framing |
| 2:62 <-> 46:13 | 1.604 | Both independently state that believers who lead righteous lives need not fear — from different contexts (pluralism vs. general principle) |
| 2:62 <-> 41:8 | 1.495 | Independent affirmation of recompense for righteous believers |

**Estimated count:** ~5,000-8,000 edges.

---

### 2.4 QUALIFIES

**Cypher name:** `QUALIFIES`
**Direction:** `(qualifier)-[:QUALIFIES]->(rule)` — the source verse adds a condition or exception to the target.
**Definition:** Verse A introduces a condition, exception, caveat, or contextual limitation to the statement in verse B. "X is forbidden... except when Y."

**Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `score` | float | Original RELATED_TO score |
| `confidence` | float | 0.0-1.0, classifier confidence |
| `qualification_type` | string | "exception", "condition", "scope_limitation", "temporal" |

**Detection heuristic:** One verse contains conditional language ("except", "unless", "if", "but", "provided that", "when") and the pair shares a common subject (via keywords). LLM classification is likely needed for accuracy.

**Example pairs from the graph:**

| Pair | Score | Relationship |
|------|-------|-------------|
| 16:115 <-> 2:173 | 3.282 | Both state food prohibitions, but 16:115 adds the explicit exception: "If one is forced (to eat these), without being deliberate or malicious, then GOD is Forgiver, Most Merciful" — qualifying the prohibition in 2:173 |
| 16:115 <-> 6:145 | 3.256 | 6:145 lists prohibited foods; 16:115 qualifies with the duress exception |
| 2:173 <-> 6:145 | 2.975 | 6:145 frames it as "I do not find... any food that is prohibited... except:" — qualifying/specifying 2:173's general prohibition |

**Estimated count:** ~1,000-2,000 edges.

---

### 2.5 CONTRASTS

**Cypher name:** `CONTRASTS`
**Direction:** Undirected (both verses contrast each other).
**Definition:** Verses present apparently opposing perspectives, complementary opposites, or theological tension that invites reconciliation. Not contradiction — the Quran is self-consistent — but verses that address the same topic from different angles that a reader might initially perceive as tension.

**Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `score` | float | Original RELATED_TO score |
| `confidence` | float | 0.0-1.0, classifier confidence |
| `contrast_type` | string | "complementary_opposites", "different_audience", "progressive_revelation", "general_vs_specific" |

**Detection heuristic:** Verses share topic keywords but contain opposing sentiment markers or complementary pairs (mercy/punishment, reward/consequence, believer/disbeliever). LLM classification strongly recommended.

**Example pairs (conceptual — need LLM verification):**

| Pair | Potential Contrast |
|------|-------------------|
| 2:256 ("no compulsion in religion") <-> verses on consequences of disbelief | Complementary: free choice exists, but choice has consequences |
| Verses on God's mercy <-> verses on God's punishment | Complementary opposites: both attributes of God, different audiences |
| General forgiveness verses <-> specific prohibition verses | General vs. specific scope |

**Estimated count:** ~500-1,500 edges. This is the rarest and most nuanced type — expect high false-positive rate without LLM classification.

---

### 2.6 SHARES_THEME

**Cypher name:** `SHARES_THEME`
**Definition:** Pure thematic overlap that doesn't fit a more specific category. The generic fallback — verses share keywords/concepts but the relationship is associative, not structural.

**Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `score` | float | Original RELATED_TO score (preserved exactly) |

**Detection heuristic:** Any existing RELATED_TO edge that is not classified into one of the five specific types above.

**Estimated count:** ~35,000-42,000 edges (the majority — most connections are loose thematic association).

---

## 3. Migration Strategy

### Recommendation: Option (b) — Additive (new typed edges alongside RELATED_TO)

**Chosen approach:** Add new typed edges alongside the existing `RELATED_TO` edges. Do NOT delete or modify `RELATED_TO`.

**Justification:**

| Factor | Option (a) Replace | Option (b) Additive | Option (c) Property |
|--------|-------------------|---------------------|---------------------|
| **Safety** | Destructive — if classifier is wrong, data is lost | No data loss — RELATED_TO remains as ground truth | No data loss |
| **Query compatibility** | All existing queries break (`-[:RELATED_TO]-` returns nothing) | All existing queries work unchanged | All existing queries work unchanged |
| **Query power** | Must enumerate types: `-[:SUPPORTS\|ELABORATES\|...]-` | Can query specific types OR fall back to RELATED_TO | Must filter: `WHERE r.type = 'SUPPORTS'` |
| **Performance** | Same edge count | ~2x edges (typed + original) | Same edge count |
| **Cypher ergonomics** | Clean relationship types | Clean relationship types + fallback | Property filtering is slower than type filtering in Neo4j |
| **Incremental rollout** | All-or-nothing | Can classify in batches, partial coverage is fine | Can classify in batches |
| **Visualization** | Must update frontend link colors | Can add new link colors, existing "related" still works | Must update frontend to read property |

**Why not (c):** Neo4j indexes relationship types natively but does NOT index relationship properties efficiently. Querying `WHERE r.type = 'SUPPORTS'` requires scanning all RELATED_TO edges. Separate relationship types enable `MATCH ()-[:SUPPORTS]->()` which uses the relationship type index directly. At 51,798 edges this matters for interactive response times.

**Why not (a):** The classification will be imperfect (LLM-based, ~80-90% accuracy expected). Keeping RELATED_TO as the ground-truth scored layer means we can always fall back, re-classify, or correct without data loss.

### Migration Order

1. **Phase 1 (algorithmic):** Classify REPEATS using text similarity — high precision, no LLM needed
2. **Phase 2 (algorithmic):** Classify ELABORATES using length ratio + embedding similarity heuristics
3. **Phase 3 (LLM-assisted):** Classify SUPPORTS, QUALIFIES, CONTRASTS using Claude batch classification
4. **Phase 4 (fallback):** Any unclassified RELATED_TO edge implicitly remains SHARES_THEME (no explicit edge needed — absence of a typed edge = generic theme)

SHARES_THEME edges are NOT explicitly created. Instead, the query pattern is:
- Want specific types? → `MATCH ()-[:SUPPORTS]-()`
- Want all thematic connections? → `MATCH ()-[:RELATED_TO]-()`
- Want unclassified only? → `MATCH (a)-[:RELATED_TO]-(b) WHERE NOT (a)-[:SUPPORTS|ELABORATES|QUALIFIES|REPEATS|CONTRASTS]-(b)`

This avoids duplicating 35,000+ generic edges.

---

## 4. Neo4j Schema Changes

### 4.1 New Relationship Types

```cypher
// No explicit creation needed — relationships are created implicitly in Neo4j.
// But document the expected types:
// :REPEATS, :ELABORATES, :SUPPORTS, :QUALIFIES, :CONTRASTS
```

### 4.2 New Indexes

```cypher
// Relationship property indexes (Neo4j 5.x+)
// These speed up filtering by score/confidence within a relationship type

CREATE INDEX rel_repeats_score IF NOT EXISTS
FOR ()-[r:REPEATS]-() ON (r.score);

CREATE INDEX rel_elaborates_score IF NOT EXISTS
FOR ()-[r:ELABORATES]-() ON (r.score);

CREATE INDEX rel_supports_score IF NOT EXISTS
FOR ()-[r:SUPPORTS]-() ON (r.score);

CREATE INDEX rel_qualifies_score IF NOT EXISTS
FOR ()-[r:QUALIFIES]-() ON (r.score);

CREATE INDEX rel_contrasts_score IF NOT EXISTS
FOR ()-[r:CONTRASTS]-() ON (r.score);
```

### 4.3 Updated GraphMeta

```cypher
MERGE (m:GraphMeta {key: 'edge_schema'})
SET m.version = '2.0',
    m.typed_edges = ['REPEATS', 'ELABORATES', 'SUPPORTS', 'QUALIFIES', 'CONTRASTS'],
    m.generic_edge = 'RELATED_TO',
    m.note = 'Typed edges are additive overlays on RELATED_TO. A verse pair can have both RELATED_TO (scored) and one or more typed edges (classified). Absence of a typed edge means SHARES_THEME (generic).',
    m.classification_date = datetime()
```

---

## 5. Impact on Existing Code

### chat.py — Tool Queries

**Current:** All tools query `RELATED_TO` only.
**After:** Tools can optionally filter by type for more precise results.

```cypher
-- Current (still works, returns all thematic connections):
MATCH (v:Verse {verseId: $id})-[r:RELATED_TO]-(other:Verse)
ORDER BY r.score DESC LIMIT 12

-- New option (filter to specific relationship):
MATCH (v:Verse {verseId: $id})-[r:SUPPORTS]-(other:Verse)
ORDER BY r.score DESC LIMIT 12

-- New option (multiple types):
MATCH (v:Verse {verseId: $id})-[r:ELABORATES|QUALIFIES]-(other:Verse)
ORDER BY r.score DESC LIMIT 12
```

**No breaking changes.** Existing queries continue to work. New typed queries are optional enhancements.

### app.py — Graph Visualization

**Current:** All thematic links rendered as `"type": "related"` in the frontend.
**After:** Can pass the typed edge label through:

```python
# In _graph_for_tool, when creating links from tool results:
link(v1, v2, "supports")    # instead of "related"
link(v1, v2, "elaborates")
link(v1, v2, "repeats")
```

**Frontend (index.html):** Add link colors per type:

```javascript
const LINK_COLORS = {
  related:    '#334155',   // existing grey
  supports:   '#10b981',   // green
  elaborates: '#6366f1',   // indigo
  qualifies:  '#f59e0b',   // amber
  repeats:    '#64748b',   // slate (dim, these are redundant)
  contrasts:  '#ef4444',   // red
};
```

### System Prompt

Add typed-edge awareness to the system prompt:

```
The graph now has typed relationships between verses:
- SUPPORTS: verse A provides evidence for verse B
- ELABORATES: verse A expands on verse B with more detail
- QUALIFIES: verse A adds a condition or exception to verse B
- CONTRASTS: verses present complementary perspectives on the same topic
- REPEATS: near-verbatim repetition across surahs

When answering, note the relationship type. For example:
"[5:6] elaborates the ablution rules mentioned in [4:43]"
"[16:115] qualifies the food prohibition in [2:173] with a duress exception"
```

---

## 6. Classification Pipeline Design

### Phase 1: REPEATS (Algorithmic)

```python
# For each RELATED_TO edge:
# 1. Compute token Jaccard similarity
# 2. Compute embedding cosine similarity (already stored)
# 3. If Jaccard > 0.70 OR embedding_cosine > 0.92: classify as REPEATS

tokens_a = set(text_a.lower().split())
tokens_b = set(text_b.lower().split())
jaccard = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
```

### Phase 2: ELABORATES (Algorithmic)

```python
# For each RELATED_TO edge NOT already REPEATS:
# 1. Compute length ratio
# 2. If ratio > 1.5 AND embedding_cosine > 0.75:
#    The longer verse ELABORATES the shorter

ratio = max(len(text_a), len(text_b)) / min(len(text_a), len(text_b))
```

### Phase 3: SUPPORTS, QUALIFIES, CONTRASTS (LLM-Assisted)

For remaining high-score edges (score > 1.0, ~8,666 edges), batch-classify with Claude:

```
Given these two Quran verses, classify their relationship as one of:
- SUPPORTS: A provides independent evidence for B's claim
- QUALIFIES: A adds a condition/exception to B
- CONTRASTS: A and B present complementary perspectives
- THEME_ONLY: Just topical overlap, no structural relationship

Verse A: [4:43] "O you who believe, do not observe the Contact Prayers..."
Verse B: [5:6] "O you who believe, when you observe the Contact Prayers..."

Classification:
```

**Batch size:** 50 pairs per API call, ~174 calls for 8,666 edges.
**Cost estimate:** ~$2-5 in API costs at Haiku pricing.
**Low-score edges (< 1.0):** Default to SHARES_THEME (no typed edge created). These 43,132 edges are mostly loose thematic association not worth classifying.

---

## 7. Estimated Final Edge Counts

| Type | Estimated Count | Source |
|------|-----------------|--------|
| `RELATED_TO` (preserved) | 51,798 | Existing, unchanged |
| `REPEATS` | 500-700 | Algorithmic (Jaccard + embedding) |
| `ELABORATES` | 3,000-5,000 | Algorithmic (length ratio + embedding) |
| `SUPPORTS` | 2,000-4,000 | LLM classification |
| `QUALIFIES` | 500-1,500 | LLM classification |
| `CONTRASTS` | 200-800 | LLM classification |
| SHARES_THEME (implicit) | ~35,000-42,000 | Unclassified RELATED_TO edges |

**Total new edges:** ~6,200-12,000 typed edges overlaying the existing 51,798 RELATED_TO edges.

---

## 8. Open Questions

1. **Should typed edges be directional?** SUPPORTS, ELABORATES, and QUALIFIES have natural direction (evidence->claim, detail->summary, qualifier->rule). REPEATS and CONTRASTS are symmetric. The schema above specifies direction where appropriate.

2. **Should we classify edges with score < 1.0?** The current design skips them (79.6% of edges). If we want full coverage, LLM cost increases ~5x. Recommendation: start with score > 1.0, evaluate quality, then decide.

3. **Multi-label edges?** Can a pair be both ELABORATES and QUALIFIES? (e.g., a verse that expands on a ruling while adding an exception). Recommendation: yes, allow multiple typed edges per pair. The additive approach naturally supports this.

4. **Confidence threshold?** Should we only create typed edges above a certain classifier confidence? Recommendation: 0.7 confidence minimum. Below that, leave as unclassified SHARES_THEME.
