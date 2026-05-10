---
type: decision
adr: 0011
status: accepted
date: 2026-04-27
tags: [decision, citation-verification, quality]
supersedes: none
---

# ADR-0011 — MiniCheck-FT5 + NLI for citation verification

## Status
Accepted (2026-04-27). Active (env-gated).

## Context
The system produces answers grounded in verse citations, but the LLM can hallucinate or over-claim: citing a verse that does not actually support the stated claim. A post-response verification step was needed. Options evaluated: (1) pure NLI cross-encoder (`cross-encoder/nli-deberta-v3-xsmall`) scoring premise=verse, hypothesis=claim; (2) MiniCheck-FT5 (`flan-t5-large` fine-tuned for claim grounding, from Liyan06/MiniCheck); (3) FActScore-style atomic claim decomposition (claim split via LLM → per-atom NLI). All three are implemented in `citation_verifier.py` (commit `9cf268f`, 2026-04-27).

## Decision
Implement all three modes in `citation_verifier.py` and gate the feature behind `ENABLE_CITATION_VERIFY=1`. Default backend is NLI; MiniCheck selectable via `CITATION_VERIFIER_MODEL=minicheck`; FActScore-style decomposition via `CITATION_DECOMPOSE=atomic`. Verification runs post-response and results are streamed as `verification` SSE events — they do not block the answer.

## Consequences
- **Positive:** Provides a grounded signal for when the model's citations are unsupported. MiniCheck-FT5 is purpose-built for this task. Atomic decomposition catches partial support (claim contains a supported sub-claim and an unsupported sub-claim).
- **Negative:** All three backends add latency post-response. FActScore-style decomposition requires an OpenRouter LLM call (additional cost). The feature is compute-heavy for a solo-dev setup; keeping it opt-in is the right default.
- **Neutral:** Verification results are written to `(:CitationCheck)` nodes in the reasoning graph, accumulating a long-term signal of which tool/verse combinations produce weak citations.

## Cross-references
- Source evidence: `repo://CLAUDE.md` (`citation_verifier.py` subsystem note, env vars section)
- Related: [[0002-bge-m3-over-minilm]], [[0012-5-tier-memory-stack]]
