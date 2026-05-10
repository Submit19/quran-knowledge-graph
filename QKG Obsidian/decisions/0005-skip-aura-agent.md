---
type: decision
adr: 0005
status: accepted
date: 2026-05-10
tags: [decision, infrastructure, hosting]
supersedes: none
---

# ADR-0005 — Skip Aura Agent migration

## Status
Accepted (2026-05-10). Active.

## Context
Neo4j Aura Agent (EAP/preview as of May 2026) is a managed low-code platform that provides text-to-Cypher, similarity search, and Cypher templates as a REST endpoint — no infrastructure to manage. Research tick `06c_yt_mcp_aura_benchmarks.md` (commit `cf51eae`, 2026-05-10) evaluated Aura Agent capabilities from a Neo4j video (`sZRA4j3d0c8`). Key constraint: Aura Agent is locked to Gemini 2.5 Flash as the LLM, and only supports OpenAI `text-embedding-ada-002` or Google Gemini embeddings — there is no bring-your-own-model path for embeddings or LLMs.

## Decision
Do not migrate to Aura Agent. Continue with the hand-rolled `chat.py` + local Neo4j stack. Monitor Aura Agent's roadmap for bring-your-own-embedding support before re-evaluating.

## Consequences
- **Positive:** Retains BGE-M3 multilingual embeddings, multilingual reranker, and all custom tool logic (Arabic root traversal, Code-19 features, wujuh lookup, `run_cypher` escape hatch, morphology layer). None of these have equivalents in Aura Agent.
- **Negative:** Must maintain all retrieval infrastructure ourselves. Aura's managed playground and auth plumbing are attractive for future productization.
- **Neutral:** Aura's Cypher-template tool design is a useful reference pattern for improving `run_cypher` safety/predictability (declarative pre-approved queries).

## Cross-references
- Source evidence: `repo://data/research_neo4j_crawl/06c_yt_mcp_aura_benchmarks.md` (Video 2 section)
- Related: [[0006-local-neo4j]]
