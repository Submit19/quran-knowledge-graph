---
type: decision
adr: 0010
status: accepted
date: 2026-04-28
tags: [decision, retrieval, graph-traversal]
supersedes: none
---

# ADR-0010 — HippoRAG PPR — definitive negative result, not wired into chat

## Status
Accepted (2026-04-28). Active.

## Context
HippoRAG-style retrieval uses Personalized PageRank (PPR) over a verse subgraph, seeding it with vector hits, past-query citations, and typed graph edges (SUPPORTS, ELABORATES, etc.). The hypothesis was that graph diffusion would surface multi-hop connections missed by pure vector retrieval. `eval_qrcd_hipporag_sweep.py` tested 36 PPR configurations (alpha/beta/gamma weight combinations) against the QRCD 22-question benchmark (commit `d3f5e10`, 2026-04-28). Results are in `HIPPORAG_REPORT.md`.

## Decision
Do not wire `tool_hipporag_traverse` into `chat.py`. Keep `hipporag_traverse.py` as a helper module. The PPR-as-post-reranker variant (`ppr_rerank()`) remains available as a helper but is also not wired by default.

## Consequences
- **Positive:** Avoids routing queries through a retriever that demonstrably hurts QRCD metrics. The code is preserved and can be activated if conditions improve.
- **Negative:** Potential multi-hop retrieval gains are unrealized. The known partial cause — Query nodes embedded in MiniLM space while QRCD queries are Arabic — is a fixable bug (re-embed with BGE-M3), but re-testing has not been prioritized.
- **Neutral:** The PPR infrastructure is reusable with different seed types (Arabic-root-matched seeds, SemanticDomain seeds). Future multi-hop benchmarks may vindicate the approach. The negative result itself is valuable: it confirms QRCD is direct-lookup style, not multi-hop, and that graph diffusion dilutes strong vector signals on this benchmark.

## Cross-references
- Source evidence: `repo://HIPPORAG_REPORT.md`; `repo://CLAUDE.md` (`hipporag_traverse.py` subsystem note)
- Related: [[0002-bge-m3-over-minilm]]
