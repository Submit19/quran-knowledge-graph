---
date: 2026-04-28
type: session-milestone
status: archived
tags: [session, research, architecture, retrieval]
source: RESEARCH_2026-04-28_DEEP.md
---

# Session/milestone: Research Deep Dive — 6 Sources, Concrete Next Tasks

## What the session was about

A targeted deep-dive into six specific sources identified in the previous day's research: the Sefaria codebase (actual schema from `model/topic.py`), MiniCheck's decomposition gap, HippoRAG's internal personalization vector, the GraphRAG-Bench paper, Tarteel QUL ingestion targets, and the Doha Historical Dictionary RAG paper. The output was a prioritized task list (T1/H1/S1/M1/G1) that became the Phase 3 agenda for the subsequent autonomous run.

## Shipped (concrete artefacts)

- `RESEARCH_2026-04-28_DEEP.md` — 6-section analysis with per-source concrete tasks (T1–T3, H1–H3, S1–S2, M1–M2, G1–G2, D1–D2)
- Prioritized 5-item task queue: T1 (mutashabihat ingest) > H1 (PPR sweep) > S1 (TF-IDF + provenance) > M1 (FActScore decomposer) > G1 (multi-hop benchmark)

## Key findings / decisions

- Sefaria's `IntraTopicLink` carries bidirectional `fromTfidf`/`toTfidf` on every edge — same link reads differently depending on which side is the entry point; QKG adopted this pattern for MENTIONS edges.
- MiniCheck has no built-in atomization; FActScore-style atomic decomposition must be added upstream — making QKG's regex sentence-splitter a deliberate architectural choice, not an oversight.
- HippoRAG's failure on QRCD was traced to three causes: sparse Arabic OpenIE facts, wrong default `passage_node_weight` (0.05 vs recommended 0.3–0.5 for short-context), and most fundamentally the GraphRAG-Bench finding that basic RAG dominates on single-hop retrieval (QKG's QRCD regime).
- The GraphRAG-Bench paper directly predicts the HippoRAG negative result before it was run — the research phase actually served as a hypothesis validator for the implementation phase.
- Tarteel QUL exposes MIT-licensed SQLite dumps including 5,277 mutashabihat pairs and 4,001 similar-ayah entries — but the JS-gated CDN blocked direct script access; a CC0 GitHub alternative (`Waqar144/Quran_Mutashabihat_Data`) was identified as the practical ingestion path.
- Doha Historical Dictionary (300K entries, 1B-word diachronic corpus) was rated L-effort but strategically important for the etymology sub-project.

## What was queued for next time

- Execute T1–M1 in sequence during the autonomous run (Phase 3 of `AUTONOMOUS_RUN_2026-04-28`).
- Defer G1 (multi-hop benchmark, ~200 hand-curated questions) as a strategic but large effort.
- Revisit H2 (replace OpenIE with Quranic Arabic Corpus syntactic edges) once multi-hop benchmark exists.

## Cross-references

- Original report: `repo://RESEARCH_2026-04-28_DEEP.md`
- Prior research: [[session-2026-04-27-research-stack-alternatives]]
- Implementation of findings: [[session-2026-04-28-autonomous-run]]
