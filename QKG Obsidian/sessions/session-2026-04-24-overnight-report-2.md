---
date: 2026-04-24
type: session-milestone
status: archived
tags: [session, cache-seeding, bug-fix, infrastructure]
source: OVERNIGHT_REPORT_2.md
---

# Session/milestone: Second Overnight Cache Seeding — The Cache Bug Fix (500 → 845)

## What the session was about

A 12-hour seeding window (2026-04-23 19:42 → 2026-04-24 07:56) that ran phases 6–8, growing the cache from 500 to 845 entries. Critically, this session identified and fixed two bugs in `answer_cache.py` that had silently prevented any growth beyond 500 — the most important engineering event of the entire seeding arc.

## Shipped (concrete artefacts)

- `answer_cache.py` fix: dedupe threshold raised `0.95 → 0.98`; entry cap raised `500 → 5000`
- `chat.py tool_semantic_search` enhanced with VectorCypherRetriever pattern — single Cypher query returns verse + 5 related + 5 Arabic roots + typed edges (SUPPORTS / ELABORATES / QUALIFIES / CONTRASTS / REPEATS)
- `reasoning_memory.py` — new module implementing Neo4j Labs Agent Memory pattern; wired into `app_free.py`; past similar queries injected as system-prompt playbooks
- Phase question banks for phases 6, 7, and 8
- Commits: `a65cb74`, `4174c74`

## Key findings / decisions

- The 0.95 dedupe threshold was overwriting semantic siblings (e.g., "fasting" clobbering "fasting during Ramadan and exceptions"). Raising to 0.98 was the unlock for all future cache growth.
- The 500-entry hard cap with eviction-of-oldest meant every new entry after 500 silently displaced an old one. Combined, both bugs made the cache appear stuck.
- Specific-verse questions yield 85–92% cache-growth rate vs 78% for broad thematic questions — targeted phase design matters.
- Final hour of phase 8 showed severe slowdown (500s+ per question) — diagnosed as provider-side OpenRouter pressure, not account-level throttling.
- Phase 8 ended at 138/180 questions (42 remaining) due to the 7-hour deadline cap.

## What was queued for next time

- Run the 42 unfinished Phase 8 questions.
- Wire VerseAnalysis into a proper tool rather than pre-injecting to avoid citation-format drift.
- Continue seeding toward 1000+ entries now that the cap bug is resolved.

## Cross-references

- Original report: `repo://OVERNIGHT_REPORT_2.md`
- Preceded by: [[session-2026-04-22-overnight-report]]
- Continued in: [[session-2026-04-26-weekend-report]]
