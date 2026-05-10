---
date: 2026-04-27
type: session-milestone
status: archived
tags: [session, research, retrieval, architecture]
source: RESEARCH_2026-04-27.md
---

# Session/milestone: Research — Skeptical Stack Audit and Extension Roadmap

## What the session was about

A deep research pass commissioned in "challenge the stack, don't affirm it" mode. A research agent surveyed the 2024–2026 literature on multilingual embeddings, Quran-RAG benchmarks, citation verification, graph retrieval, and adjacent open-source projects (Sefaria, Cognee), then produced a ranked list of 13 high-impact additions and 7 specific critiques of the current QKG stack.

## Shipped (concrete artefacts)

- `RESEARCH_2026-04-27.md` — full 13-item addition table with effort/risk ratings, 7 critical stack challenges, adjacent-project analysis (Sefaria, Cognee, Logos), 10 recent papers to read, and a people-to-follow list
- Identified Code-19 as defensible differentiated territory (arithmetic features that cannot be hallucinated)

## Key findings / decisions

- `all-MiniLM-L6-v2` is the single biggest performance bottleneck — English-only, 384-dim, 256-token context; Arabic sits unembedded. BGE-M3 or Arctic Embed L v2.0 is the drop-in replacement.
- The QRCD benchmark (AraBERT-base fine-tuned MAP@10 = 0.36) was identified as the external bar QKG retrieval should be measured against — internal 218-question QIS is insufficient.
- MiniCheck-FT5 (Tang et al., EMNLP 2024) was called out as GPT-4-class faithfulness checking at 400× lower cost, purpose-built for verse-citation grounding.
- Sefaria is the closest analog project; its Linker, ref-resolver, bidirectional-TF-IDF edge schema, and `dataSource`/`generatedBy` provenance patterns are directly portable to QKG.
- The HippoRAG / PPR angle was flagged as high-ROI but needing evaluation — the reasoning-trace graph already has the topology, PPR is "mostly a Cypher query."
- Typed-edge taxonomy (SUPPORTS/ELABORATES/QUALIFIES/CONTRASTS/REPEATS) was criticized as hand-authored when tafsir sources provide a scholarly-grounded alternative.

## What was queued for next time

- Implement BGE-M3 embeddings (additive, switchable via env var).
- Run QRCD benchmark evaluation to get an honest MAP@10 number vs literature baseline.
- Prototype HippoRAG PPR on top of the existing reasoning-trace graph.
- Investigate Sefaria's bidirectional TF-IDF + provenance schema for adoption.
- Add MiniCheck-FT5 as a citation verifier backend alongside NLI-DeBERTa.

## Cross-references

- Original report: `repo://RESEARCH_2026-04-27.md`
- Deep-dive follow-up: [[session-2026-04-28-research-deep-dive]]
- Implementation that executed on these findings: [[session-2026-04-28-autonomous-run]]
