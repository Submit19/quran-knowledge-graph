---
type: decision
adr: 0001
status: accepted
date: 2026-04-08
tags: [decision, data, translation]
supersedes: none
---

# ADR-0001 — Use Rashad Khalifa's translation exclusively

## Status
Accepted (2026-04-08). Active.

## Context
The project needed a single English Quran translation to serve as the primary corpus for vector embeddings, keyword extraction, and LLM grounding. The standard Quran contains 6,236 verses. Multiple translations exist (Yusuf Ali, Pickthall, Sahih International, Khalifa). The project's scope includes Khalifa's "mathematical miracle of 19" features (Code-19 arithmetic properties on Verse nodes), which require alignment with his specific verse numbering and textual notes. Khalifa's translation controversially excludes verses 9:128–129, which he argued were later additions detectable via the mathematical code, leaving 6,234 verses.

## Decision
Use Rashad Khalifa's *The Final Testament* as the sole English translation. Arabic text uses the standard Hafs ʿan ʿĀṣim (Uthmani script) reading from the Quranic Arabic Corpus, independent of translation theology.

## Consequences
- **Positive:** Consistent verse numbering across all graph features; enables Code-19 arithmetic properties; translation's parenthetical clarifications improve BGE-M3 cross-lingual retrieval quality (English text is richer than bare Arabic).
- **Negative:** 9:128–129 are absent; the system cannot answer questions about those two verses. Khalifa-specific theological framing (Messenger of the Covenant, rejection of hadith) is baked into the corpus and will surface in model answers.
- **Neutral:** System prompt explicitly acknowledges Khalifa interpretations so users understand the framing.

## Cross-references
- Source evidence: `repo://CLAUDE.md` ("Translation Context" section)
- Related: [[0002-bge-m3-over-minilm]]
