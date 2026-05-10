---
date: 2026-05-07
type: session-milestone
status: archived
tags: [session, eval, system-prompt, tooling]
source: EVAL_V1_V2_REPORT.md
---

# Session/milestone: Eval v1 → v2 — System Prompt Expansion Impact

## What the session was about

An A/B evaluation of the system prompt change: v1 exposed 5 tools, v2 exposes all 10 lean-schema tools (adding `concept_search`, `hybrid_search`, `recall_similar_query`, `run_cypher`, `get_code19_features`) with precedence rules. Both runs used the same 13-question eval set, same backend (`gpt-oss-120b:free`), same env (`verse_embedding_m3` + `bge-reranker-v2-m3`). The only variable was the system prompt.

## Shipped (concrete artefacts)

- `data/eval_v1_baseline.{json,md}` — v1 results (5-tool prompt)
- `data/eval_v1_results.{json,md}` — v2 results (10-tool prompt)
- Updated `prompts/system_prompt_free.txt` — the v2 prompt now in production
- Commit: `aec0446`

## Key findings / decisions

- Citation density rose 30% (33.5 → 43.6 unique citations/question, +132 total across 13 questions) with only +0.9 additional tool calls per question (+15%). Per-call yield increased because `concept_search` fans out through the NORMALIZES_TO → Concept layer, capturing surface variants in a single call.
- `concept_search` went from 1 to 11 calls; `search_keyword` dropped from 19 to 12 — the substitution is exactly as designed (Eifrem's canonical case: "forgiveness" should match `forgive`/`forgiver`/`forgiveness` in one call).
- `hybrid_search`, `run_cypher`, `get_code19_features`, and `recall_similar_query` remained at 0 calls on this question set — which is correct. These are situational tools not triggered by the 13 thematic questions.
- Time cost: +49s/question (+23%) for the +30% citation gain is a strong trade for research-style answers.
- Citation *correctness* was not measured — 30% more citations could be 30% more noise. NLI/MiniCheck verification on a v1 vs v2 sample is the open gap.

## What was queued for next time

- Hand-grade a sample of the 26 answers (v1 + v2) to determine if the +30% citations are signal or noise.
- Add 5 targeted eval questions to exercise the unused tools: 1 Code-19 question, 1 aggregation, 1 rare-Arabic-term, 2 follow-up (session-memory) questions.
- Refresh the answer cache by re-embedding past Q&A with BGE-M3 and re-running the top 100 entries through the updated agent.
- Measure per-tool citation quality, not just call frequency.

## Cross-references

- Original report: `repo://EVAL_V1_V2_REPORT.md`
- Tools introduced in: [[session-2026-04-28-autonomous-run]]
- Current session: [[session-2026-05-10]]
