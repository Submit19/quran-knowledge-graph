---
task_id: from_neo4j_crawl_single_shot_vector_traversal
drafted_at: 2026-05-11T12:30:43.112646+00:00
model: claude-sonnet-4-6
purpose: Pre-warmed implementation plan; read by Opus subagent during IMPL tick.
---

# Implementation plan: `from_neo4j_crawl_single_shot_vector_traversal`

_Auto-drafted by `scripts/sonnet_prep.py` to reduce cold-discovery cost when the
IMPL tick spawns the Opus subagent. Treat as a starting point, not gospel._

---

# Implementation Plan: `from_neo4j_crawl_single_shot_vector_traversal`

## Scope Clarification

**In scope:**
- Analyze the current `tool_semantic_search` implementation in `repo://chat.py` to understand the existing two-phase pattern (vector lookup → separate 1-hop expansion query)
- Produce a research/design document at `data/ralph_agent_from_neo4j_crawl_single_shot_vector_traversal.md` describing the single-shot Cypher refactor, its rationale, and an implementation plan
- Identify the exact Cypher rewrite that merges vector index call + typed-edge expansion

**Out of scope:**
- Actually modifying `chat.py` or any production code (this is an `agent_creative` task — deliverable is a design document, not a code change)
- Running benchmarks or latency measurements
- Changing the reranker or retrieval pipeline beyond the semantic search tool

**Assumptions:**
- The current implementation makes one DB call for vector similarity, then a second call for neighbor expansion
- Neo4j supports `db.index.vector.queryNodes()` (or the `CALL` vector procedure) composable inside a full Cypher statement — this is true for Neo4j 5.x
- The typed edges being expanded are likely `NEXT`, `PREV`, `SAME_SURAH`, or similar structural relationships on `(:Verse)` nodes

---

## Files to Read

1. `repo://chat.py` — primary target; find `tool_semantic_search` function; trace every DB call inside it (look for two sequential `session.run()` / `driver.execute_query()` calls)
2. `repo://retrieval_gate.py` — check if 1-hop expansion happens here instead of (or in addition to) `chat.py`
3. `repo://pipeline_config.yaml` — identify relevant tunables (top-k, expansion depth, edge types whitelisted)
4. `repo://ARCHITECTURE.md` — confirm the retrieval flow diagram to make sure no hidden expansion step exists elsewhere
5. `repo://data/research_neo4j_crawl/INDEX.md` — the crawl finding that motivated this task; read the linked deep-crawl doc on vector+traversal patterns to ground the design

---

## Files to Modify (Deliverable Only)

| Path | Change |
|------|--------|
| `data/ralph_agent_from_neo4j_crawl_single_shot_vector_traversal.md` | **Create** — design document per acceptance criteria |

No production code changes in this tick.

---

## Sub-Step Breakdown

**Step 1 — Read and annotate the current two-phase pattern**
Open `repo://chat.py`, locate `tool_semantic_search`. Count DB round-trips. Note the Cypher for each call, the parameters passed, and where results are merged in Python. Also check `retrieval_gate.py` for any additional graph expansion calls post-rerank.

**Step 2 — Identify edge types used in expansion**
From the code inspection, extract the exact relationship types used in the 1-hop expansion (e.g., `NEXT`, `PREV`, `BELONGS_TO`, `SAME_THEME`). Check `pipeline_config.yaml` for any config-driven edge-type lists. This determines what the merged Cypher `OPTIONAL MATCH` clause must cover.

**Step 3 — Consult the crawl research artefact**
Read the relevant deep-crawl document linked from `repo://data/research_neo4j_crawl/INDEX.md` (the vector+graph single-shot source). Extract the canonical pattern — likely `CALL db.index.vector.queryNodes(...) YIELD node, score WITH node, score OPTIONAL MATCH (node)-[r:TYPE]->(neighbor) RETURN ...`. Note any Neo4j version caveats.

**Step 4 — Draft the merged Cypher**
Write the single-statement version in the design doc. Key structure:
```cypher
CALL db.index.vector.queryNodes($index, $k, $embedding)
YIELD node AS verse, score
OPTIONAL MATCH (verse)-[r:NEXT|PREV|SAME_SURAH]->(neighbor:Verse)
RETURN verse, score, collect(neighbor) AS neighbors
```
Include parameter mapping (`$index`, `$k`, `$embedding`) matching the existing call signature so the Python wrapper changes are minimal.

**Step 5 — Identify Python-side changes needed**
Document what changes in `chat.py` are required: removing the second `session.run()`, adjusting result unpacking to handle the new `neighbors` column, and verifying `top_k` semantics are preserved (vector search `$k` should probably be bumped slightly to account for dedup after expansion).

**Step 6 — Assess risks and mitigations**
Write a dedicated risks section in the document (see below for content).

**Step 7 — Write the deliverable document**
Assemble sections: motivation, current architecture, proposed Cypher, Python delta, expected latency impact, risks, and a concrete follow-up task stub for the actual code change tick. Target ≥700 bytes (easily met with a thorough document).

---

## Risks / Unknowns

- **Neo4j version compatibility**: `db.index.vector.queryNodes` composability inside `WITH` chains was stabilized in Neo4j 5.13+. Opus should check `CALL dbms.components()` output or `.env`/`docker-compose` for the installed version before claiming the pattern is drop-in safe.
- **Result cardinality explosion**: If `OPTIONAL MATCH` fanout is high (many neighbors per verse), the result set could be larger than the two-query approach. The doc should recommend `LIMIT` on neighbors or `OPTIONAL MATCH` with a `WHERE` filter.
- **Reranker contract**: `retrieval_gate.py` expects a flat list of verse objects. If the merged Cypher returns `collect(neighbor)`, the Python unpacking must flatten before passing to the reranker. Verify the interface hasn't shifted.
- **top_k semantics**: Vector search returns exactly `$k` nodes; if expansion adds neighbors those neighbors are unscored. The doc should clarify whether neighbors inherit parent score or get a discounted score, and recommend the approach.
- **The expansion may already be absent**: It's possible the current code does the expansion via a separate agentic tool call (e.g., a `tool_graph_expand` tool), not inside `tool_semantic_search`. If so, scope changes — document the correct target tool instead.

---

## Acceptance Check

After writing the document, Opus should verify:

1. `data/ralph_agent_from_neo4j_crawl_single_shot_vector_traversal.md` **exists**
2. `wc -c data/ralph_agent_from_neo4j_crawl_single_shot_vector_traversal.md` returns **≥ 700** (criterion: `file_min_bytes`)
3. The document contains: current pattern description, proposed merged Cypher, Python delta notes, risks section — substantive enough that a follow-up IMPL tick could execute the code change without re-reading `chat.py`
