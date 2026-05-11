---
type: decision
adr: 0031
status: accepted
date: 2026-05-12
tags: [decision, architecture, lightrag, graph, skip]
supersedes: none
---

# ADR-0031 — Skip LightRAG Neo4j spike (QKG already exceeds LightRAG capabilities)

## Status
Accepted (2026-05-12). No further action needed.

## Context
LightRAG (EMNLP 2025, 28K GitHub stars) is a popular graph-augmented RAG library that stores extracted entities in Neo4j and uses dual-level retrieval: low-level (entity-centric) and high-level (Leiden community summaries). A spike was proposed to A/B LightRAG vs QKG on QRCD.

Task `from_ai_graph_lightrag_neo4j_spike` (commit `90aebf0`, tick 72) produced a feature comparison analysis (`data/ralph_analysis_from_ai_graph_lightrag_neo4j_spike.md`). Key finding: **QKG already exceeds LightRAG on every dimension** relevant to Quranic retrieval:

| Capability | LightRAG | QKG |
|---|---|---|
| Dense vector search | BGE-M3 (via graphrag backend) | BGE-M3 (direct) |
| BM25 full-text | Optional | verse_text_fulltext + verse_arabic_fulltext |
| Graph-augmented retrieval | Leiden community summaries | Typed edges (SUPPORTS/ELABORATES/QUALIFIES) |
| Entity resolution | LLM extraction (noisy) | Concept + ArabicRoot + Lemma (curated) |
| Arabic morphology | None | ArabicRoot + MorphPattern + Lemma hierarchy |
| Semantic domains | None | 30+ SemanticDomain nodes |
| Reasoning memory | None | (:Query)→(:ReasoningTrace)→(:ToolCall) subgraph |
| Agent tool loop | Basic retrieval | 21 tools, adaptive routing |

Additionally, the cross-research synthesis (`data/research_synthesis_2026-05-12.md`) independently reached the same SKIP conclusion before this analysis was written.

Running a QRCD A/B would cost 4–8 hours of dev time and would almost certainly produce a negative result, since LightRAG has no Arabic morphology (QRCD requires root-level matching) and its LLM-generated community summaries may distort Quranic interpretation.

## Decision
Skip the LightRAG spike entirely. Do not invest dev time in a QRCD A/B comparison. The 7-dimension feature superiority, confirmed by independent synthesis, makes the outcome highly predictable. Revisit only if LightRAG adds Arabic morphological support or releases a QRCD benchmark score that is competitive.

## Consequences
- **Positive:** Saves 4–8 hours of dev time.
- **Positive:** Avoids a "negative noise" benchmark result cluttering the eval corpus.
- **Positive:** Confirms QKG architectural direction — deep domain adaptation over general-purpose library adoption.
- **Negative:** No empirical QRCD comparison against LightRAG; future users of this codebase cannot cite a measured number.
- **Neutral:** Analogous to the HippoRAG SKIP (ADR-0010) — a pattern of skipping general-purpose graph-RAG libraries in favor of domain-specific depth.

## Cross-references
- Source evidence: commit `90aebf0`, deliverable `data/ralph_analysis_from_ai_graph_lightrag_neo4j_spike.md`
- Synthesis confirmation: `data/research_synthesis_2026-05-12.md`
- Related: [[0010-hipporag-ppr-negative]], [[0005-skip-aura-agent]]
- Proposed by: ralph IMPL tick 72
