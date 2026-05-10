# 03 — Cypher Performance, Indexing, and GDS for QKG

Crawl date: 2026-05-10. Sources: Neo4j Cypher Manual (current), GDS docs (current), GraphAcademy course pages, APOC Labs docs, Neo4j Operations Manual (logging).

---

## TL;DR

- **The 647s `semantic_search` outlier is almost certainly not a vector-index issue** — vector indexes have bounded latency. It's the post-vector graph traversal (TF-IDF MENTIONS expansion, RELATED_TO walk) hitting `AllNodesScan` / `CartesianProduct` / `Eager` operators on cold cache. Wrap the slow tool call in `PROFILE` and read the plan from the bottom up; look for those three operators.
- **Turn on slow-query logging immediately**: set `db.logs.query.enabled=INFO` and `db.logs.query.threshold=500ms` in `neo4j.conf`. We are flying blind on tail-latency root-causes without `query.log` capturing every >500ms execution with its full plan, parameters, page hits, and page faults.
- **Always parameterize.** Literal-bound queries skip the plan cache. We should audit every tool's Cypher string: `name: 'foo'` → `name: $name`. Plan-build time alone can dominate a 50ms query.
- **We are likely missing a relationship-property index on `MENTIONS.from_tfidf`** (and `to_tfidf`), and a range index on `Verse.surah`/`Verse.ayah`. Vector index alone doesn't help when the next hop filters by a non-indexed edge property.
- **Vector + 1-hop expansion CAN be a single Cypher statement** via `db.index.vector.queryNodes(...) YIELD node, score MATCH (node)-[:MENTIONS]->(k) ...`. We may be doing two round trips unnecessarily — that's an easy win.
- **Replace Louvain with Leiden** for community detection. Leiden fixes Louvain's "disconnected community" bug and tends to find better-structured clusters at the same modularity. One-line change: `gds.louvain.write` → `gds.leiden.write`.
- **For retrieval beyond PPR, try FastRP node embeddings + KNN.** Embed the QKG (1223 ArabicRoot + 4762 Lemma + Concept structure) into a 128-d vector, then `gds.knn` on the embedding gives a structural-similarity edge that complements semantic vector search. Documented pattern: "Product recommendations with kNN based on FastRP embeddings."

---

## Per-Page Findings

### P1. Cypher Indexes & Constraints (GraphAcademy)

**URL:** https://graphacademy.neo4j.com/courses/cypher-indexes-constraints/

**Summary:** Course outline only — landing page lists lessons but doesn't ship the syntax. Five index categories: range, text, point, full-text, composite. Three constraint types: uniqueness, existence, node key. Course also covers "Controlling Index Usage" (hints) and query plan inspection.

**QKG relevance:** Confirms what to learn — concrete syntax fetched from the manual itself (P3, P4 below). Knowing the lesson list helps prioritize: "Creating a Composite Index on a Node Property" + "Using query hints" are the two we most need.

**Action:** Skip the course landing — go straight to the manual indexes/syntax page (P4).

---

### P2. Cypher Intermediate Queries (GraphAcademy)

**URL:** https://graphacademy.neo4j.com/courses/cypher-intermediate-queries/

**Summary:** Course covers WITH pipelining, OPTIONAL MATCH, COLLECT/UNWIND, subqueries, parameters. Confirmed snippet patterns:

```cypher
MATCH (person:Person)-[:ACTED_IN]->(movie:Movie)
WITH person, COUNT(movie) as movieCount
WHERE movieCount > 5
RETURN person.name, movieCount
```

**QKG relevance:** Our hybrid scoring queries fundamentally need this WITH-pipeline pattern. Aggregating tf-idf scores per verse before joining typed edges should be a single `WITH person, sum(...) as score WHERE score > threshold` chain.

**Action:** Refactor any Python-side score aggregation into Cypher WITH chains where possible.

---

### P3. Cypher Aggregation (GraphAcademy)

**URL:** https://graphacademy.neo4j.com/courses/cypher-aggregation/

**Summary:** Functions: `count()`, `sum()`, `avg()`, `collect()`, `min()`, `max()`, `percentileCont()`. Pattern comprehension and list functions. Course landing lists topics but no snippets here.

**QKG relevance:** `percentileCont()` is what we should be computing for our own latency metrics in-graph if we ever store query traces. `collect(DISTINCT ...)` is the right pattern for de-duping verses across multiple keyword paths.

**Action:** None directly — but knowing percentileCont exists matters for our reasoning_traces analytics.

---

### P4. Cypher Manual: Planning & Tuning (root)

**URL:** https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/

**Summary:**
- **EXPLAIN**: shows the plan, doesn't run, returns empty.
- **PROFILE**: runs the query AND tracks rows-through-each-operator + storage interactions.

> "If you want to see the execution plan but not run the query, prepend your Cypher statement with EXPLAIN."

**QKG relevance:** Workflow for diagnosing the 647s outlier — see Q1 below.

---

### P5. Cypher Manual: Query Tuning

**URL:** https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/query-tuning/

**Concrete snippets:**

Bad (literal binds skip plan cache):
```cypher
MATCH (n:Person {name: 'Alice'}) RETURN n
```

Good (parameterized — plan reuse):
```cypher
MATCH (n:Person {name: $name}) RETURN n
```

> "Try to use parameters instead of literals when possible. This allows Cypher to re-use queries instead of having to parse and build new execution plans."
>
> "Queries should aim to filter data as early as possible in order to reduce the amount of work that has to be done in the later stages of query execution."

**QKG relevance:** **Audit every f-string Cypher in our toolset.** If we have any `f"MATCH (v:Verse {{surah:{surah}}})"` we are losing the plan cache and paying parse cost on every call.

---

### P6. Cypher Manual: Execution Plans & Operators

**URLs:**
- https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/execution-plans/
- https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/operators/

**Summary:**

**Read execution plans bottom-up.** Each operator has Id, Details, Estimated Rows.

**Operator hierarchy (best → worst):**
1. **Best:** `NodeIndexSeek`, `NodeUniqueIndexSeek`, `DirectedRelationshipIndexSeek`
2. **Acceptable:** `NodeIndexScan`, `NodeByLabelScan`, `DirectedRelationshipTypeScan`
3. **Bad:** `AllNodesScan`, `DirectedAllRelationshipsScan`

**Eager (blocking) operators** — accumulate ALL rows before passing on:
- `EagerAggregation`, `Sort`, `Top`, `Distinct`
- `NodeHashJoin`, `ValueHashJoin`
- `Eager` (used for write-isolation)

**Cartesian-product operator:** `CartesianProduct` — multiplies row counts. Always investigate.

**Expansion:**
- `Expand(All)` — traverses all matching rels (default, ok)
- `Expand(Into)` — specific node-pair, more efficient
- `VarLengthExpand(Pruning)` — preferred over `VarLengthExpand(All)` on large graphs

**QKG red flags:** Combinations of `AllNodesScan` + `CartesianProduct`, or `VarLengthExpand(All)` without pruning, or back-to-back `Eager` operators.

---

### P7. Cypher Manual: Index Syntax (verbatim)

**URL:** https://neo4j.com/docs/cypher-manual/current/indexes/syntax/

```cypher
-- RANGE (the workhorse — equality, range, prefix)
CREATE RANGE INDEX verse_surah_ayah IF NOT EXISTS
FOR (v:Verse) ON (v.surah, v.ayah);

-- TEXT (CONTAINS, STARTS WITH, ENDS WITH)
CREATE TEXT INDEX verse_text_en IF NOT EXISTS
FOR (v:Verse) ON (v.text_en);

-- RELATIONSHIP-PROPERTY (huge for our MENTIONS edges)
CREATE RANGE INDEX mentions_from_tfidf IF NOT EXISTS
FOR ()-[r:MENTIONS]-() ON (r.from_tfidf);

-- LOOKUP (Neo4j ships these by default — confirm)
CREATE LOOKUP INDEX node_label_lookup IF NOT EXISTS
FOR (n) ON EACH labels(n);

-- FULL-TEXT (Lucene-backed, fuzzy, boosts)
CREATE FULLTEXT INDEX verse_fulltext IF NOT EXISTS
FOR (v:Verse) ON EACH [v.text_en, v.text_ar];

-- VECTOR (we already have these for embeddings)
CREATE VECTOR INDEX verse_embedding_bge_en IF NOT EXISTS
FOR (v:Verse) ON v.embedding_bge_en
OPTIONS { indexConfig: {
  `vector.dimensions`: 1024,
  `vector.similarity_function`: 'cosine'
}};

-- INSPECT
SHOW INDEXES;
SHOW VECTOR INDEXES YIELD name, state, populationPercent;

-- DROP
DROP INDEX verse_text_en IF EXISTS;
```

**QKG relevance:** This is the inventory we need to audit our DB against. See Q2.

---

### P8. Cypher Manual: Vector Indexes (deep dive)

**URL:** https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/

**Critical snippet — vector + 1-hop traversal in a single query:**

```cypher
MATCH (m:Movie {title: 'Godfather, The'})
CALL db.index.vector.queryNodes('moviePlots', 5, m.embedding)
YIELD node AS movie, score
MATCH (movie)<-[:ACTED_IN]-(actor:Actor)
RETURN movie.title, actor.name, score
ORDER BY score DESC
```

**Modern (Neo4j 2026.01+) SEARCH clause:**
```cypher
MATCH (movie:Movie)
  SEARCH movie IN (
    VECTOR INDEX moviePlots
    FOR m.embedding
    LIMIT 5
  ) SCORE AS score
MATCH (movie)<-[:ACTED_IN]-(actor:Actor)
RETURN movie.title, actor.name, score
```

> Note: `db.index.vector.queryNodes` is **deprecated as of 2026.04** — migrate to `SEARCH ... IN ( VECTOR INDEX ...)`.

**QKG relevance:** **Direct answer to Q6.** Our `tool_semantic_search` likely does (a) vector query in Python, (b) round-trip back with verse IDs to expand. Single-shot Cypher version below in Q6.

---

### P9. Cypher Manual: Index Hints

**URL:** https://neo4j.com/docs/cypher-manual/current/indexes/search-performance-indexes/index-hints/

**Snippets:**

```cypher
-- Force planner to use a specific index
MATCH (v:Verse {surah: $surah})
USING RANGE INDEX v:Verse(surah)
RETURN v;

-- Force a label scan instead of an index (for low-selectivity queries)
MATCH (v:Verse)
USING SCAN v:Verse
WHERE v.surah > 100
RETURN v;

-- Force a join at a specific node (for OPTIONAL MATCH patterns)
MATCH (k:Keyword)-[:MENTIONS]->(v:Verse)<-[:RELATED_TO]-(v2:Verse)
USING JOIN ON v
RETURN k, v, v2;
```

**Warning from docs:** "Join hints are advanced and risky—they may force a very bad starting point if misused."

**QKG relevance:** Last-resort tool when we have a known-good plan but the planner picks something different. Use only after confirming with PROFILE that the planner is choosing wrong.

---

### P10. Cypher Manual: Full-Text Indexes

**URL:** https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/full-text-indexes/

**Lucene-powered patterns we should use:**

```cypher
-- Fuzzy match (~ tolerance) for typos
CALL db.index.fulltext.queryNodes("verse_fulltext", 'mercy~0.7') YIELD node, score
RETURN node.surah, node.ayah, score LIMIT 20;

-- Boolean
CALL db.index.fulltext.queryNodes("verse_fulltext", 'mercy AND forgive') YIELD node, score;

-- Field-targeted (per-property)
CALL db.index.fulltext.queryNodes("verse_fulltext", 'text_ar:"الرحمن"') YIELD node, score;
```

Configuration for Arabic content:
```cypher
CREATE FULLTEXT INDEX verse_arabic_fulltext FOR (v:Verse) ON EACH [v.text_ar]
OPTIONS { indexConfig: { `fulltext.analyzer`: 'arabic' }};
```

**QKG relevance:** `tool_search_keyword` p95 967ms could improve if backed by a full-text index with the Arabic analyzer (we may be doing CONTAINS scans now). Lucene fuzzy matching also gives us free typo-tolerance.

---

### P11. Cypher Manual: Subqueries

**URL:** https://neo4j.com/docs/cypher-manual/current/subqueries/call-subquery/

**Pattern — per-row aggregation without loading everything:**

```cypher
MATCH (t:Topic)
CALL (t) {
  MATCH (t)<-[m:MENTIONS]-(v:Verse)
  RETURN sum(m.from_tfidf) AS topicScore, count(v) AS verseCount
}
RETURN t.name, topicScore, verseCount
ORDER BY topicScore DESC LIMIT 10;
```

`OPTIONAL CALL` returns null instead of dropping rows. `CALL { ... } IN TRANSACTIONS` for batched writes.

**QKG relevance:** Per-verse score isolation in hybrid retrieval — see Q3.

---

### P12. Operations Manual: Slow Query Logging

**URL:** https://neo4j.com/docs/operations-manual/current/monitoring/logging/

**Config snippet for `neo4j.conf`:**
```
db.logs.query.enabled=INFO
db.logs.query.threshold=500ms
db.logs.query.parameter_logging_enabled=true
```

Log location: `<NEO4J_HOME>/logs/query.log`

Each entry includes execution time, planning/CPU/wait time, memory, page hits, page faults, session, user, query text, and parameters.

**QKG relevance:** **Single most important config change to make right now.** With `INFO` + 500ms threshold, every slow `semantic_search` will land in `query.log` with its full plan stats.

---

### P13. GDS Algorithms: Community Detection (catalog)

**URL:** https://neo4j.com/docs/graph-data-science/current/algorithms/community/

**Available algorithms:**
- Louvain (current)
- Leiden (recommended replacement)
- Label Propagation
- Modularity Optimization
- Strongly Connected Components, Weakly Connected Components
- K-Core, Triangle Count, Local Clustering Coefficient
- K-Means, HDBSCAN, Clique Counting, Approximate Maximum k-cut
- Speaker-Listener Label Propagation (SLLPA — overlapping communities)

**QKG relevance:** SLLPA is interesting because Quranic concepts cross verse boundaries — overlapping community detection might surface multi-theme verses better than hard partitioning.

---

### P14. GDS: Leiden

**URL:** https://neo4j.com/docs/graph-data-science/current/algorithms/leiden/

**Snippet:**
```cypher
CALL gds.leiden.stream('qkg_concepts', {
  randomSeed: 42,
  gamma: 1.0,
  maxLevels: 10
})
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId) AS node, communityId
ORDER BY communityId;
```

Key params: `gamma` (resolution; higher → more communities), `theta` (randomness in decomposition, 0.01 default), `maxLevels` (10 default).

> "Some of the communities found by Louvain are not well-connected. [Leiden] periodically randomly breaks down communities into smaller well-connected ones."

**QKG action:** Re-run our community pass with Leiden, same projection, compare modularity and community count to our current 16-cluster Louvain output (mod 0.5324).

---

### P15. GDS: PageRank (incl. Personalized)

**URL:** https://neo4j.com/docs/graph-data-science/current/algorithms/page-rank/

**Personalized PageRank (single source):**
```cypher
MATCH (q:Verse {surah: 1, ayah: 1})
CALL gds.pageRank.stream('qkg_full', {
  sourceNodes: [q],
  dampingFactor: 0.85,
  maxIterations: 20,
  tolerance: 1e-7
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId), score ORDER BY score DESC LIMIT 20;
```

**Weighted multi-source PPR (HippoRAG-style):**
```cypher
MATCH (q1:Verse {surah:1,ayah:1}), (q2:Verse {surah:2,ayah:255})
CALL gds.pageRank.stream('qkg_full', {
  sourceNodes: [[q1, 1.0], [q2, 2.0]]
})
YIELD nodeId, score ...
```

**QKG relevance:** Our HippoRAG negative result on QRCD might trace to (a) wrong projection — including too many low-signal MENTIONS edges, (b) damping factor too high (0.85 default biases away from sources), (c) not weighting source nodes by query relevance. New thread below.

---

### P16. GDS: Node Embeddings (FastRP, Node2Vec, GraphSAGE, HashGNN)

**URL:** https://neo4j.com/docs/graph-data-science/current/machine-learning/node-embeddings/

**FastRP — production-ready, fast:**
```cypher
CALL gds.fastRP.stream('qkg_concepts', {
    embeddingDimension: 128,
    iterationWeights: [0.0, 1.0, 1.0],
    propertyRatio: 0.0,
    randomSeed: 42
})
YIELD nodeId, embedding
RETURN nodeId, embedding;
```

For inductive embedding (works on new nodes without retraining), use FastRP with `propertyRatio: 1.0` + `featureProperties: ['some_node_prop']`, or GraphSAGE.

**QKG relevance:** This is our missing retrieval signal. Embed the QKG structure (Verse-Concept-Lemma-Root tree + RELATED_TO edges), then vector-search the embeddings → structural-similarity verses. Combined with the BGE semantic vector search, we get a 2-vector hybrid (semantic + structural).

---

### P17. GDS: Similarity / KNN

**URL:** https://neo4j.com/docs/graph-data-science/current/algorithms/knn/

**KNN over a node property (e.g. FastRP embedding):**
```cypher
CALL gds.knn.stream('qkg_with_embeddings', {
    topK: 10,
    nodeProperties: {embedding: 'COSINE'},
    sampleRate: 1.0,
    deltaThreshold: 0.0,
    randomSeed: 42
})
YIELD node1, node2, similarity
RETURN gds.util.asNode(node1).id, gds.util.asNode(node2).id, similarity
ORDER BY similarity DESC LIMIT 100;
```

For graph-structure similarity (Jaccard-style on shared neighbors):
```cypher
CALL gds.nodeSimilarity.stream('qkg_concepts', {
    similarityCutoff: 0.5,
    topK: 10
})
YIELD node1, node2, similarity ...
```

**QKG relevance:** `gds.nodeSimilarity` could replace or complement our 51K cosine-derived `RELATED_TO` edges — it's mathematically grounded (Jaccard on shared concepts) and cheaper to maintain.

---

### P18. GDS: Graph Projection (Cypher style)

**URL:** https://neo4j.com/docs/graph-data-science/current/management-ops/graph-creation/graph-project-cypher-projection/

**Selective projection — only Verse + Concept + MENTIONS, with tf-idf as weight:**
```cypher
MATCH (source)
WHERE source:Verse OR source:Concept
OPTIONAL MATCH (source)-[r:MENTIONS]->(target)
WHERE target:Verse OR target:Concept
WITH gds.graph.project(
  'qkg_verse_concept',
  source,
  target,
  {
    sourceNodeLabels: labels(source),
    targetNodeLabels: labels(target),
    relationshipType: type(r),
    relationshipProperties: r { .from_tfidf }
  }
) AS g
RETURN g.graphName, g.nodeCount, g.relationshipCount;
```

**QKG action:** Project a *narrow* subgraph for each algorithm rather than the whole 200K-edge graph. This is likely why our HippoRAG was slow and noisy — too many irrelevant edges in the projection.

---

### P19. APOC Procedures (selected)

**URL:** https://neo4j.com/labs/apoc/4.4/overview/

**For QKG specifically:**
- `apoc.text.levenshteinSimilarity(s1, s2)` — keyword fuzzy match (Latin-script)
- `apoc.text.sorensenDiceSimilarity` — n-gram similarity (better for Arabic transliteration variants)
- `apoc.text.jaroWinklerDistance` — short-string fuzzy match
- `apoc.periodic.iterate("MATCH ...", "SET ...", {batchSize:1000, parallel:true})` — schema migrations (we'll need this when re-embedding)
- `apoc.coll.frequencies(list)` — quick keyword histogram
- `apoc.map.merge` — merge tool-result maps in Cypher
- `apoc.convert.toJson` — return structured JSON from Cypher (avoids client-side parsing)

---

## Answers to the 7 Specific Questions

### Q1. EXPLAIN vs PROFILE — diagnosing the 647s outlier

**Workflow:**
1. **First, capture the failing query** by enabling slow-query logging:
   ```
   db.logs.query.enabled=INFO
   db.logs.query.threshold=500ms
   db.logs.query.parameter_logging_enabled=true
   ```
   Restart Neo4j. Reproduce the slow `semantic_search` call. Grep `query.log` for entries >10000ms. The log entry contains the full Cypher and bound parameters.

2. **Run `EXPLAIN` first** on the captured query — costs nothing, returns the planner's intended plan. Look for: `AllNodesScan`, `CartesianProduct`, `VarLengthExpand(All)`, sequences of `Eager` operators.

3. **Run `PROFILE`** with the same parameters. PROFILE actually executes the query and reports rows-through-each-operator and db-hits. Read **bottom-up**.

4. **Specific things to look at on the 647s outlier:** plan vs estimated rows divergence (>10x means stale stats — run `CALL db.stats.retrieve("GRAPH COUNTS")` and consider `CALL db.indexes()` to verify indexes are ONLINE). Also check page-cache hits in the log entry — if page-faults dominate, the working set doesn't fit in the page cache and we need to bump `server.memory.pagecache.size`.

5. **Server-side monitoring beyond query.log:**
   - `dbms.listQueries()` — currently-running queries with elapsed times
   - `dbms.killQuery(id)` — kill a runaway
   - For continuous: enable `metrics.csv.enabled=true` and ship to Prometheus.

### Q2. Indexes we are likely missing

Audit: `SHOW INDEXES YIELD name, type, labelsOrTypes, properties, state`.

**High-confidence wins:**
```cypher
-- For traverse_topic: surah/ayah lookups
CREATE RANGE INDEX verse_surah_ayah IF NOT EXISTS
FOR (v:Verse) ON (v.surah, v.ayah);

-- For score-aware MENTIONS expansion
CREATE RANGE INDEX mentions_from_tfidf IF NOT EXISTS
FOR ()-[r:MENTIONS]-() ON (r.from_tfidf);
CREATE RANGE INDEX mentions_to_tfidf IF NOT EXISTS
FOR ()-[r:MENTIONS]-() ON (r.to_tfidf);

-- For typed-edge filtering (SUPPORTS, ELABORATES, etc.)
-- type filter is fast (token index), but if we filter by edge confidence:
CREATE RANGE INDEX typed_edge_confidence IF NOT EXISTS
FOR ()-[r:SUPPORTS|ELABORATES|QUALIFIES|CONTRASTS|REPEATS]-() ON (r.confidence);

-- For keyword/concept exact lookup
CREATE RANGE INDEX keyword_text IF NOT EXISTS FOR (k:Keyword) ON (k.text);
CREATE RANGE INDEX concept_stem IF NOT EXISTS FOR (c:Concept) ON (c.stem);
CREATE RANGE INDEX root_arabic IF NOT EXISTS FOR (r:ArabicRoot) ON (r.root);
CREATE RANGE INDEX lemma_form IF NOT EXISTS FOR (l:Lemma) ON (l.form);

-- Full-text on Arabic + English (replaces CONTAINS for tool_search_keyword)
CREATE FULLTEXT INDEX verse_fulltext_en IF NOT EXISTS
FOR (v:Verse) ON EACH [v.text_en]
OPTIONS { indexConfig: { `fulltext.analyzer`: 'english' }};
CREATE FULLTEXT INDEX verse_fulltext_ar IF NOT EXISTS
FOR (v:Verse) ON EACH [v.text_ar]
OPTIONAL { indexConfig: { `fulltext.analyzer`: 'arabic' }};
```

**Composite vs single-property:** Composite `(surah, ayah)` is a range index spanning two properties — used when the query filters on both, or just on `surah` (prefix). Cannot serve a query that filters only `ayah`.

### Q3. Single-query hybrid scoring

```cypher
// Hybrid: semantic + keyword tf-idf + typed-edge boost in ONE statement
WITH $query_embedding AS qe, $keywords AS kws
CALL db.index.vector.queryNodes('verse_embedding_bge_en', 50, qe)
YIELD node AS v, score AS semScore

// Aggregate keyword tf-idf for this verse
OPTIONAL MATCH (v)<-[m:MENTIONS]-(k:Keyword) WHERE k.text IN kws
WITH v, semScore, sum(coalesce(m.to_tfidf, 0.0)) AS kwScore

// Aggregate typed-edge inbound support
OPTIONAL MATCH (v)<-[s:SUPPORTS|ELABORATES]-(other:Verse)
WITH v, semScore, kwScore, count(s) AS supportCount

// Final scoring expression (tunable weights)
WITH v,
     semScore,
     kwScore,
     supportCount,
     (0.6 * semScore + 0.3 * (kwScore / (1.0 + kwScore)) + 0.1 * log(1 + supportCount)) AS hybrid
ORDER BY hybrid DESC
LIMIT 10
RETURN v.surah, v.ayah, v.text_en, semScore, kwScore, supportCount, hybrid;
```

This is a single round trip. The `WITH` chain filters early (LIMIT 50 from vector index), aggregates, scores, sorts. `OPTIONAL MATCH` ensures verses without keyword/typed-edge matches aren't dropped.

### Q4. Community detection alternatives to Louvain

| Algorithm | When to use | One-liner |
|---|---|---|
| **Leiden** | Drop-in Louvain replacement; fixes disconnected communities | `gds.leiden.write('g', {writeProperty:'leidenCom'})` |
| **Label Propagation** | Faster than Louvain, lower modularity | `gds.labelPropagation.write` |
| **Modularity Optimization** | Direct mod max, no hierarchy | `gds.modularityOptimization.write` |
| **SLLPA** | Overlapping communities (verses ∈ multiple themes) | `gds.alpha.sllpa.write` |
| **Strongly Connected Components** | Directed cycles only — likely irrelevant for QKG | `gds.scc.write` |
| **K-Means** on FastRP | Fixed K, distance-based on embeddings | `gds.kmeans.write` after `gds.fastRP` |

**Recommended pipeline for QKG:**
```cypher
// 1. Project narrow concept-subgraph
MATCH (a)-[r:MENTIONS|RELATED_TO]-(b)
WHERE (a:Verse OR a:Concept) AND (b:Verse OR b:Concept)
WITH gds.graph.project('qkg_concept', a, b,
  {sourceNodeLabels: labels(a), targetNodeLabels: labels(b),
   relationshipType: type(r), relationshipProperties: r { .from_tfidf }}
) AS g RETURN g.graphName;

// 2. Run Leiden weighted by tf-idf
CALL gds.leiden.write('qkg_concept', {
  writeProperty: 'leidenCom',
  relationshipWeightProperty: 'from_tfidf',
  randomSeed: 42, gamma: 1.0
}) YIELD communityCount, modularity;

// 3. Compare with current Louvain output side by side
MATCH (v:Verse)
RETURN v.louvainCom AS louvain, v.leidenCom AS leiden, count(*) AS n
ORDER BY n DESC LIMIT 30;
```

### Q5. GDS for retrieval beyond PPR

**The HippoRAG negative result on QRCD likely stems from one of:**
- All 200K edges in the projection — too noisy
- Damping factor 0.85 — too much random-jump weight
- Source nodes equally weighted — no query-side signal
- Edge weights uniform — tf-idf signal lost

**Alternative GDS retrieval signals:**

1. **FastRP embeddings + KNN** (most promising):
   ```cypher
   CALL gds.fastRP.write('qkg_concept', {
     embeddingDimension: 128, randomSeed: 42,
     writeProperty: 'structEmb',
     relationshipWeightProperty: 'from_tfidf'
   });
   // Then create vector index on structEmb and use as second retrieval channel
   CREATE VECTOR INDEX verse_struct_emb FOR (v:Verse) ON v.structEmb
   OPTIONS { indexConfig: { `vector.dimensions`: 128, `vector.similarity_function`: 'cosine' }};
   ```
   At query time, score each candidate verse with both BGE-semantic and FastRP-structural cosine; combine with learned weights.

2. **Node Similarity** as a graph-derived RELATED_TO replacement:
   ```cypher
   CALL gds.nodeSimilarity.write('qkg_concept', {
     similarityCutoff: 0.3, topK: 12,
     writeRelationshipType: 'JACCARD_SIM', writeProperty: 'score'
   });
   ```

3. **Betweenness centrality** to identify "bridge" verses (cross-surah connectors). Use to up-weight in retrieval.

4. **Eigenvector centrality** as a global-importance prior on Verses, multiplied into final score.

**Documented pattern (cited):** "Product recommendations with kNN based on FastRP embeddings" — exact analogue for Quran retrieval.

### Q6. Vector index + 1-hop traversal in one query

We're answering Q6 directly:

```cypher
// Single-query: KNN verses + expand 1 hop along typed support edges
CALL db.index.vector.queryNodes('verse_embedding_bge_en', 20, $qVec)
YIELD node AS v, score AS semScore
OPTIONAL MATCH (v)-[r:SUPPORTS|ELABORATES|QUALIFIES]-(neighbor:Verse)
WITH v, semScore, collect(DISTINCT {
  surah: neighbor.surah, ayah: neighbor.ayah,
  text: neighbor.text_en, edge: type(r)
})[..5] AS neighbors
RETURN v.surah, v.ayah, v.text_en, semScore, neighbors
ORDER BY semScore DESC;
```

If we want to **rank by semantic + neighbor support count** (graph-aware reranking):

```cypher
CALL db.index.vector.queryNodes('verse_embedding_bge_en', 50, $qVec)
YIELD node AS v, score AS semScore
OPTIONAL MATCH (v)-[r:SUPPORTS|ELABORATES]-(:Verse)
WITH v, semScore, count(r) AS supportDeg
WITH v, semScore, supportDeg, semScore * (1 + 0.05 * supportDeg) AS rerank
ORDER BY rerank DESC LIMIT 10
RETURN v.surah, v.ayah, semScore, supportDeg, rerank;
```

(Migrate to `SEARCH ... IN ( VECTOR INDEX ... )` syntax once we're on Neo4j 2026.04+.)

### Q7. APOC functions worth knowing for QKG

| APOC | QKG use case |
|---|---|
| `apoc.text.levenshteinSimilarity(a,b)` | Fuzzy keyword match for Latin transliterations of Arabic |
| `apoc.text.sorensenDiceSimilarity(a,b)` | Better for variant Arabic forms via n-gram |
| `apoc.text.jaroWinklerDistance(a,b)` | Short-string match (proper nouns) |
| `apoc.periodic.iterate("MATCH ...", "SET ...", {batchSize:500, parallel:false})` | Schema migrations (re-embedding 6234 verses safely) |
| `apoc.coll.frequencies(list)` | Quick keyword distribution per surah |
| `apoc.map.merge(m1, m2)` | Combining tool results into single record |
| `apoc.convert.toJson(map)` | Returning structured nested JSON for tool boundaries |
| `apoc.coll.intersection(a, b)` | Overlap of keyword sets between verses |

For our 100K MENTIONS_ROOT migration when changing schema:
```cypher
CALL apoc.periodic.iterate(
  "MATCH (v:Verse) RETURN v",
  "MATCH (v)-[old:MENTIONS_ROOT]->(r:ArabicRoot)
   MERGE (v)-[new:HAS_ROOT {tfidf: old.tfidf}]->(r)
   DELETE old",
  {batchSize: 1000, parallel: false, retries: 3}
);
```

---

## Recommended `ralph_backlog` Tasks

```yaml
- id: from_neo4j_crawl_001_enable_slow_query_log
  type: ops
  priority: P0
  description: >
    Add db.logs.query.enabled=INFO and db.logs.query.threshold=500ms
    (and parameter_logging_enabled=true) to neo4j.conf. Restart. Verify
    query.log is populating.
  acceptance: >
    A reproduction of the 647s semantic_search outlier appears in
    <NEO4J_HOME>/logs/query.log with full Cypher, bound params, page
    hits, page faults, and elapsed time.

- id: from_neo4j_crawl_002_audit_indexes
  type: investigation
  priority: P0
  description: >
    Run SHOW INDEXES and compare against the recommended set in Q2.
    Specifically verify presence of: verse_surah_ayah composite range,
    mentions_from_tfidf/to_tfidf relationship-property indexes, and
    verse_fulltext_en/ar full-text indexes.
  acceptance: >
    Markdown table in research/ inventorying what we have vs. the Q2
    recommendation, with a concrete CREATE INDEX migration script for
    any missing index.

- id: from_neo4j_crawl_003_profile_outlier_query
  type: investigation
  priority: P0
  description: >
    Replay the slowest 5 captured semantic_search and traverse_topic
    queries with PROFILE. Document the operator tree and any
    AllNodesScan/CartesianProduct/Eager hot spots.
  acceptance: >
    PROFILE output saved as text, annotated with the bad operators and
    the proposed fix for each.

- id: from_neo4j_crawl_004_parameterize_audit
  type: refactor
  priority: P1
  description: >
    Audit every Cypher query string in tools/* for f-string literals
    that should be $-parameters. Convert. Verify with EXPLAIN that
    the plan is now reused (via SHOW TRANSACTIONS or query.log
    "planning" time approaching 0 on repeat runs).
  acceptance: >
    All Cypher in tools/ uses $-parameters; planning time on repeated
    same-shape queries drops below 5ms.

- id: from_neo4j_crawl_005_single_shot_vector_traversal
  type: refactor
  priority: P1
  description: >
    Refactor tool_semantic_search to do vector query + 1-hop typed-edge
    expansion in a single Cypher statement (Q6 pattern). Eliminate the
    second round trip for "expand neighbors of top-K".
  acceptance: >
    p50 latency for tool_semantic_search drops by at least 30%; query
    count per tool call halves.

- id: from_neo4j_crawl_006_swap_louvain_for_leiden
  type: experiment
  priority: P2
  description: >
    Run Leiden on the same projection used for current Louvain. Compare
    modularity, community count, and qualitative coherence against
    current 16-cluster, 0.5324-modularity Louvain output.
  acceptance: >
    Side-by-side report showing both algorithms' outputs on the same
    100 sample verses, with a recommendation on which to ship.

- id: from_neo4j_crawl_007_fastrp_structural_embeddings
  type: experiment
  priority: P2
  description: >
    Compute 128-d FastRP embeddings on a Verse-Concept-Lemma-Root
    projection. Add as second vector index. A/B test hybrid retrieval
    (BGE + FastRP) vs. BGE-only on QRCD.
  acceptance: >
    QRCD benchmark numbers for: (a) BGE only, (b) BGE + FastRP linear
    combo with grid-searched weight. Decision recorded.

- id: from_neo4j_crawl_008_hipporag_postmortem_v2
  type: investigation
  priority: P2
  description: >
    Re-run HippoRAG PPR but with: narrowed projection (Verse + Concept
    + Lemma only), tf-idf weighted edges, lower damping (0.5), and
    query-relevance-weighted source nodes via [[node, weight]] form.
  acceptance: >
    Documented A/B vs. vanilla retrieval on QRCD. If still negative,
    publish a definitive negative-result note and remove the code.

- id: from_neo4j_crawl_009_arabic_fulltext_index
  type: feature
  priority: P2
  description: >
    Create FULLTEXT INDEX with the Arabic analyzer over Verse.text_ar.
    Switch tool_search_keyword Arabic path to use db.index.fulltext.queryNodes
    instead of CONTAINS / regex.
  acceptance: >
    p95 of Arabic-keyword tool_search_keyword drops below 200ms; supports
    Lucene fuzzy (~0.7) syntax for typo tolerance.

- id: from_neo4j_crawl_010_node_similarity_for_related_to
  type: experiment
  priority: P3
  description: >
    Replace or augment the current 51K cosine-derived RELATED_TO edges
    with gds.nodeSimilarity (Jaccard on shared Concepts). Measure
    cross-surah ratio and qualitative relevance vs. current.
  acceptance: >
    Comparison report; decision to keep cosine, swap to Jaccard, or
    union both.
```

---

## New Research Threads

1. **Page-cache sizing.** The 647s outlier strongly suggests cold-cache disk reads dominate. Profile `server.memory.pagecache.size` against actual store size on disk; rule of thumb is page cache ≥ store + indexes. Compute actual numbers for the QKG instance.
2. **Query plan stability over schema changes.** When we add the recommended indexes, do existing tool plans regress (planner picks new index suboptimally)? Need a regression harness that captures EXPLAIN output for each tool's canonical query and diffs across deploys.
3. **Vector index recall vs. K.** We `LIMIT 5/10/20` from `db.index.vector.queryNodes`. Vector index uses HNSW — recall isn't 100%. Measure recall@K vs. brute-force cosine on a sample of 200 queries.
4. **GDS in-memory graph lifecycle.** `gds.graph.project` graphs live in JVM heap. We need a policy for when to keep, refresh, drop. Recommend nightly `gds.graph.project` materialization + `gds.fastRP.write` to persistent properties; algorithms run against the materialized embeddings, not the live projection.
5. **Migrate to Neo4j 2026.04+ SEARCH syntax.** `db.index.vector.queryNodes` is deprecated in favor of `MATCH ... SEARCH ... IN ( VECTOR INDEX ... )`. Plan version upgrade and Cypher migration.
6. **Query plan cache hit rate as a metric.** Neo4j exposes plan-cache metrics (`neo4j.cypher.planning.misses`, `.hits`). Tracking them post-parameterization audit gives us a hard signal of whether Q4 above worked.
7. **Composite index on relationship properties.** Our MENTIONS edges have both `from_tfidf` and `to_tfidf` — a composite relationship-property index would help queries that filter on both. Check if Neo4j supports composite REL indexes (manual implies yes for range type).
8. **APOC vs native: text similarity in vector vs Cypher.** For fuzzy keyword match, is `apoc.text.levenshteinSimilarity` faster than a full-text index Lucene fuzzy query, or is it the other way? Benchmark on our actual 2,636 keyword set.

---

## Sources

- Neo4j Cypher Manual — Planning & Tuning: https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/
- Neo4j Cypher Manual — Query Tuning: https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/query-tuning/
- Neo4j Cypher Manual — Execution Plans: https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/execution-plans/
- Neo4j Cypher Manual — Operators: https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/operators/
- Neo4j Cypher Manual — Indexes (root): https://neo4j.com/docs/cypher-manual/current/indexes/
- Neo4j Cypher Manual — Index Syntax: https://neo4j.com/docs/cypher-manual/current/indexes/syntax/
- Neo4j Cypher Manual — Vector Indexes: https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/
- Neo4j Cypher Manual — Full-Text Indexes: https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/full-text-indexes/
- Neo4j Cypher Manual — Index Hints: https://neo4j.com/docs/cypher-manual/current/indexes/search-performance-indexes/index-hints/
- Neo4j Cypher Manual — Subqueries: https://neo4j.com/docs/cypher-manual/current/subqueries/call-subquery/
- Neo4j Operations Manual — Logging: https://neo4j.com/docs/operations-manual/current/monitoring/logging/
- GDS — Community Detection: https://neo4j.com/docs/graph-data-science/current/algorithms/community/
- GDS — Leiden: https://neo4j.com/docs/graph-data-science/current/algorithms/leiden/
- GDS — PageRank: https://neo4j.com/docs/graph-data-science/current/algorithms/page-rank/
- GDS — Node Embeddings: https://neo4j.com/docs/graph-data-science/current/machine-learning/node-embeddings/
- GDS — FastRP: https://neo4j.com/docs/graph-data-science/current/algorithms/fastrp/
- GDS — Similarity (catalog): https://neo4j.com/docs/graph-data-science/current/algorithms/similarity/
- GDS — KNN: https://neo4j.com/docs/graph-data-science/current/algorithms/knn/
- GDS — Cypher Projection: https://neo4j.com/docs/graph-data-science/current/management-ops/graph-creation/graph-project-cypher-projection/
- APOC — Overview: https://neo4j.com/labs/apoc/4.4/overview/
- GraphAcademy — Cypher Indexes & Constraints: https://graphacademy.neo4j.com/courses/cypher-indexes-constraints/
- GraphAcademy — Cypher Intermediate: https://graphacademy.neo4j.com/courses/cypher-intermediate-queries/
- GraphAcademy — Cypher Aggregation: https://graphacademy.neo4j.com/courses/cypher-aggregation/
- GraphAcademy — GDS Fundamentals: https://graphacademy.neo4j.com/courses/gds-fundamentals/
