---
type: decision
adr: 0033
status: accepted
date: 2026-05-12
tags: [decision, reasoning-memory, neo4j, architecture, agentic]
supersedes: none
---

# ADR-0033 — QueryCluster batch consolidation: greedy cosine>0.96, MEMBER_OF edges

## Status
Accepted (2026-05-12). Shipped in commit `00b4ac1`, tick 83 IMPL.

## Context
The `(:Query)` nodes in reasoning memory accumulate over time. Semantically near-duplicate
queries (e.g., "what does the Quran say about prayer?" in ten phrasings) fragment the
`RETRIEVED` edge signal — instead of a strong cluster pointing at a set of verses, you
get thin individual edges. This degrades the `recall_similar_query` playbook's ability
to find relevant precedents.

Task `from_neo4j_yt_memory_03_consolidation_job` (p72) implemented the remedy.

## Decision
`consolidate_traces.py` runs as a nightly batch:

1. Load all `(:Query)` embeddings (BGE-M3 EN 1024-dim) into memory.
2. Single-pass greedy clustering: for each query, assign to the first existing cluster
   whose centroid cosine-similarity ≥ 0.96; else start a new cluster.
3. For each cluster with ≥ 2 members, create/update a `(:QueryCluster)` node (idempotent
   MERGE) and write `(:Query)-[:MEMBER_OF]->(:QueryCluster)` edges.
4. The cluster node carries a `representative_text` (first member) and `member_count`.

Threshold 0.96 was chosen to avoid over-merging; semantically distinct questions with
shared surface tokens (e.g., "prayer in Surah 2" vs. "prayer in Surah 3") remain separate.

## Consequences
- **Positive:** `recall_similar_query` can now aggregate RETRIEVED edges across
  cluster members, giving a stronger prior on high-value verses for common query themes.
- **Positive:** Idempotent MERGE means re-runs are safe; no duplicates.
- **Positive:** Nightly batch keeps Neo4j write pressure low (vs. online clustering per query).
- **Negative:** 0.96 threshold is heuristic; may need tuning if over/under-merge is observed.
- **Negative:** QueryCluster nodes are not yet wired into the agent's tool calls —
  `recall_similar_query` still queries individual Query nodes. A follow-up task is needed
  to leverage clusters in retrieval.
- **Neutral:** Greedy single-pass is O(n*k) where k = cluster count; acceptable for
  current scale (~1,500 queries), revisit if query count exceeds 50K.

## Cross-references
- Source: commit `00b4ac1`, deliverable `consolidate_traces.py`
- Related: `reasoning_memory.py`, `recall_similar_query` tool in `chat.py`
- Proposed by: ralph IMPL tick 83
