# 06b — Neo4j YT Agent Memory: Transcript Extracts

_Sources: F1Ihel8Dgqs · SHA-b2N9Kro · P8MIvmCTTa4 · qUF-MDnHgiw_
_Extracted 2026-05-10 by ralph research subagent_

---

## TL;DR

- The Neo4j community has converged on **three memory tiers** — short-term (session), episodic (user-specific KG), procedural (playbooks) — all backed by a shared graph layer. QKG's `reasoning_memory.py` approximates the middle tier but lacks episodic entity extraction and a procedural/playbook tier entirely.
- **Temporal invalidation** (bitemporal model: world-time + system-time as edge properties) is the consensus pattern for evolving facts. QKG has zero temporal properties on its `ReasoningTrace` or `RETRIEVED` edges — a gap.
- **Quintuple extraction** (subject, predicate, object, timestamp, free-text description) is replacing naive triple extraction. Our traces store tool call metadata but not structured quintuples queryable as knowledge facts.
- **Summary / consolidation step** ("sleep step") is universal: after accumulation, a batch job merges redundant entity nodes and compresses descriptions. QKG has no consolidation path; `Query` and `ReasoningTrace` nodes only grow.
- **Multi-agent shared memory layer** requires schema compliance testing (TCK). Not immediately relevant but sets the stage for multi-agent Quran research workflows.

---

## Video 1 — AI Agent Memory Landscape (F1Ihel8Dgqs, 29 min)

**Speaker:** Neo4j staff (NODES AI 2026 keynote follow-up)

**Schema design** `[04:55–05:15]`: Neo4j agent memory package exposes **short-term** (session messages), **long-term** (entity/relationship graph), and **reasoning memory** (decision traces). The explicit separation into three node-label namespaces contrasts with QKG, where `ReasoningTrace→ToolCall→Verse` conflates the trace and retrieval concerns into a single linear chain with no `Entity` nodes derived from the query text.

**Entity extraction pipeline** `[06:35–07:45]`: Multi-stage: statistical NER (spaCy) → GLiNER local model → LLM fallback. The base ontology is POLE+ (Person, Organisation, Location, Event, Object). QKG skips entity extraction from query text entirely; `Query.text` is embedded but never decomposed into typed entities. This means `tool_recall_similar_query` only does cosine similarity — it cannot answer "what entities appeared across past traces involving sura 2?"

**Decision-trace surfacing** `[16:57–18:13]`: The CloudCode connector extracts decision traces from JSONL session files using heuristics (user corrections, dependency changes, explicit statements like "always use X"). This is close to what QKG's `ReasoningTrace` stores, but the Neo4j approach adds an explicit `(:Decision)` node type with provenance. QKG has no equivalent — corrections and reasoning pivots are invisible.

**Multi-agent shared layer** `[20:08–24:12]`: Agents sharing a Neo4j instance need a Technology Compatibility Kit (TCK) to certify schema compliance. Not relevant yet for single-agent QKG but relevant if we ever run parallel research agents.

**Proposed QKG gap:** No entity extraction from `Query.text`; no `(:Decision)` nodes capturing reasoning pivots.

---

## Video 2 — Dynamic Memory via Temporal Knowledge Graphs (SHA-b2N9Kro, 15 min)

**Speaker:** Mik Ban, Chief AI Scientist, Perilin

**Bitemporal model** `[06:31–07:15]`: Two timestamp pairs per edge/node: `valid_from / valid_until` (world time — when the fact was true in reality) and `created_at / invalidated_at` (system time — when the graph believed it). Implemented as simple property timestamps on nodes and edges. The key pattern: **never delete; instead set `invalidated_at`**. This preserves full fact lineage.

**Compared to QKG:** Our `ReasoningTrace`, `ToolCall`, and `RETRIEVED` edges have no timestamps beyond implicit creation order. If a tool returns a verse at rank 1 in one era and rank 10 later (e.g., after adding BGE-M3 embeddings), there is no record of the change — only the latest retrieval pattern accumulates.

**Invalidation vs. deletion** `[04:55–05:20]`: Replacing deletions with temporal invalidation gives the ability to track evolution of facts. Directly applicable to QKG: when a tool's retrieval behavior changes (embedding upgrade, schema migration), we should stamp `RETRIEVED` edges with a model version rather than overwriting the signal.

**User-as-entity pattern** `[11:46–13:30]`: User sessions represented as entity nodes linked to the same KG, enabling cross-session inference. QKG equivalent would be linking `Query` nodes to a `(:User)` or `(:Session)` node for multi-session analysis — not currently modeled.

**Open question raised** `[13:42–14:51]`: Should time be modeled as edge properties, or as a first-class `(:TimePoint)` entity with links from nodes/edges to it ("time tree")? The bitemporal property model breaks down for recurring or non-contiguous validity intervals.

**Proposed QKG gap:** `RETRIEVED` edges need `valid_from`, `model_version`, and optionally `invalidated_at` to make retrieval signal temporal.

---

## Video 3 — Agentic Personas with Persistent, Evolving Memory (P8MIvmCTTa4, 20 min)

**Speaker:** Fazel, AI Engineer, UNICES

**Best-practice checklist** `[17:55–19:20]`: Concrete guidelines extracted from the talk:
1. Keep raw logs **separate** from the curated memory graph (two distinct storage layers, not one).
2. Track **time, source, and confidence** on all entity/response nodes.
3. Store facts, preferences, and events as typed node categories.
4. Let the agent **reflect and update beliefs** — not just append.
5. Design for **correcting and forgetting**, not just accumulating.

**Compared to QKG:** Items 1 and 5 are unmet. We have no separation between raw trace logs and curated memory — `ReasoningTrace` serves as both. We have no forgetting or consolidation mechanism; traces only accumulate. Item 2 is partially met (embeddings have `embedding_model` and `embedded_at`) but `ToolCall` and `RETRIEVED` edges have no confidence score or source version stamp.

**Reflection loop** `[07:25–07:45]`: "Let the agent continuously learn from whatever it has produced, come up with better responses each time." This is the self-improvement loop. QKG's `tool_recall_similar_query` is a primitive version (retrieve past playbooks) but there is no step where the agent evaluates whether a retrieved playbook was actually useful and updates its weight.

**Failures of stateless agents** `[14:00–15:15]`: Three failure modes named — Groundhog Day (repeating questions), Lost Escalation (yesterday's critical event missing today), Stale Assumption (old goal optimised after direction change). All three apply to QKG: if a user asks the same question twice months apart, the agent does not know whether the prior answer was accepted, corrected, or wrong.

---

## Video 4 — Agentic Memory (qUF-MDnHgiw, 28 min)

**Speaker:** Tomas, Generative AI Researcher, Neo4j

**Quintuple extraction** `[12:42–14:15]`: The evolution from triples (subject, predicate, object) to **quintuples** (subject, predicate, object, **timestamp**, **free-text description**) is the key schema shift of the last year. The description field captures nuanced information that cannot be expressed as a single predicate. QKG's `ToolCall` node has `tool_name` and parameters but no free-text description of what was inferred, and no temporal component.

**Consolidation / "sleep step"** `[15:21–16:58]`: After accumulation, a batch process merges entity mentions across sessions into a single canonical node. Example: John Davis appears in 20 conversations → a single `(:Person {name: "John Davis"})` node with a consolidated description. Claude's own memory (mentioned as a real production system) runs this once every 24 hours. QKG analog would be: merge `Query` nodes with cosine similarity > 0.98 into a canonical cluster node, then summarise their shared retrieval patterns.

**Procedural memory** `[21:35–25:13]`: Stores recurring task templates, prompt patterns, and metric definitions so the agent responds consistently to repeated request types. The Neo4j data model: `(:Procedure)-[:HAS_STEP]->(:Step)` with hierarchical categorisation. This is directly analogous to QKG's `tool_recall_similar_query` playbook system — but the playbooks are currently just raw `ReasoningTrace` nodes, not first-class `(:Procedure)` nodes with structured steps.

**Frameworks comparison** `[25:39–26:25]`: mem0 and Zep focus on **episodic memory** (graphs built from conversations). Cognee is in the middle. All three support Neo4j as backend. This confirms the earlier research noting mem0 (52K stars) and Zep/Graphiti as candidates — both are building exactly the episodic tier that QKG is missing.

**Short-term schema** `[06:07–07:14]`: Graph model: `(:User)-[:HAS_SESSION]->(:Session)-[:HAS_MESSAGE {order}]->(:Message)`. Retrieval is just session ID → ordered message sequence. QKG currently has `(:Query)-[:TRIGGERED]->(:ReasoningTrace)` with no `(:Session)` grouping — multi-turn conversations within one session are invisible.

---

## Cross-Cutting Patterns

| Pattern | Videos | QKG Status |
|---|---|---|
| Three-tier memory (short/episodic/procedural) | 1, 3, 4 | Partial — only reasoning tier exists |
| Bitemporal edge properties | 2, 4 | Missing — no timestamps on RETRIEVED or ToolCall |
| Quintuple extraction (triple + time + description) | 2, 4 | Missing — ToolCall has no free-text or temporal field |
| Consolidation / sleep step | 3, 4 | Missing — traces accumulate unbounded |
| Separate raw log vs. curated graph | 3 | Missing — ReasoningTrace serves both roles |
| Reflection / belief update loop | 3, 4 | Primitive — recall only, no weight update |
| Session grouping node | 4 | Missing — no (:Session) between User and Query |
| Entity extraction from query text | 1 | Missing — Query.text embedded but not decomposed |

---

## Proposed ralph_backlog Tasks

```yaml
- id: from_neo4j_yt_memory_01_bitemporal_retrieved
  type: schema
  priority: high
  description: >
    Add `valid_from` (ISO timestamp) and `model_version` string properties to all
    new RETRIEVED edges written by reasoning_memory.py. Backfill existing edges
    with created_at=null, model_version="pre-bge-m3" sentinel. This enables
    temporal queries: which verses were ranked highly under legacy MiniLM but not
    under BGE-M3?
  acceptance: |
    - reasoning_memory.py writes valid_from and model_version on every RETRIEVED edge
    - Backfill script runs without error; existing edges have sentinel values
    - One Cypher query in CLAUDE.md demonstrating temporal retrieval filter

- id: from_neo4j_yt_memory_02_session_node
  type: schema
  priority: medium
  description: >
    Introduce (:Session {session_id, started_at}) node between User (or app instance)
    and Query. Link: (:Session)-[:CONTAINS]->(:Query). Group all queries arriving
    within the same HTTP session or within a 30-minute idle window into one Session.
    Enables multi-turn conversation analysis and Groundhog Day detection.
  acceptance: |
    - reasoning_memory.py creates or reuses (:Session) node keyed on session_id header
    - CONTAINS edges written for every Query in that session
    - Cypher query counting queries per session works correctly

- id: from_neo4j_yt_memory_03_consolidation_job
  type: infra
  priority: medium
  description: >
    Write consolidate_traces.py: batch job that (a) finds Query node clusters with
    cosine similarity > 0.96 on query_embedding, (b) creates a (:QueryCluster) node
    with merged retrieval statistics, (c) links members via [:MEMBER_OF]. Schedule
    as a nightly cron task. This is the "sleep step" pattern from Video 4.
  acceptance: |
    - consolidate_traces.py runs without modifying or deleting existing nodes
    - QueryCluster nodes created for clusters of ≥ 3 similar queries
    - Cluster size distribution logged to ralph_log.md

- id: from_neo4j_yt_memory_04_procedural_nodes
  type: schema
  priority: low
  description: >
    Promote high-confidence ReasoningTraces to (:Procedure) nodes. A trace qualifies
    if it has ≥ 5 RETRIEVED edges to ≥ 3 distinct verses and its Answer node has
    no CitationCheck with verdict=FAIL. Procedure node stores canonical tool sequence
    as ordered steps. tool_recall_similar_query should prefer Procedure nodes over
    raw traces in its cosine search.
  acceptance: |
    - Promotion script identifies qualifying traces; Procedure nodes created
    - tool_recall_similar_query returns Procedure hits before raw trace hits
    - At least 10 Procedure nodes created from existing trace corpus

- id: from_neo4j_yt_memory_05_reasoning_step_node
  type: schema
  priority: medium
  description: >
    Insert the missing (:ReasoningStep) node between ReasoningTrace and ToolCall
    (previously flagged in prior research). A ReasoningStep groups ToolCalls by
    reasoning turn, carries a free-text `rationale` field (the quintuple description),
    and holds `turn_number`. This closes the gap identified in Videos 2 and 4.
  acceptance: |
    - reasoning_memory.py writes (:ReasoningStep) nodes with turn_number and rationale
    - HAS_STEP edge from ReasoningTrace now points to ReasoningStep, not ToolCall
    - ToolCall linked via (:ReasoningStep)-[:EXECUTED]->(:ToolCall)
    - Existing traces unaffected (schema additive)
```

---

## Sources

- `data/research_neo4j_crawl/yt_F1Ihel8Dgqs.md` — NODES AI 2026: Agent Memory Landscape
- `data/research_neo4j_crawl/yt_SHA-b2N9Kro.md` — Temporal KG / Perilin (Mik Ban)
- `data/research_neo4j_crawl/yt_P8MIvmCTTa4.md` — Agentic Personas / UNICES (Fazel)
- `data/research_neo4j_crawl/yt_qUF-MDnHgiw.md` — Agentic Memory / Neo4j (Tomas)
