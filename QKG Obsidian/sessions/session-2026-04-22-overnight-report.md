---
date: 2026-04-22
type: session-milestone
status: archived
tags: [session, cache-seeding, infrastructure]
source: OVERNIGHT_REPORT.md
---

# Session/milestone: First Overnight Cache Seeding (0 → 500)

## What the session was about

The first unattended seeding run built the answer cache from scratch, processing ~595 questions across 5 phases over roughly 20 hours. It established the core seeding infrastructure (per-phase question banks, OpenRouter primary + local Ollama fallback, citation-normalization pass) and validated the pipeline end-to-end before handing off to the second overnight.

## Shipped (concrete artefacts)

- `data/answer_cache.json` — 500 entries (453 unique post-dedupe at the time), 4.15 MB
- `overnight_seed.py` + `overnight_seed_phase2/3/4.py` — per-phase question banks and seeder engine
- `normalize_citations.py` — rewrote bold-markdown citations to `[X:Y]` format; recovered 1,889 hidden citations
- Phase-state archives: `.phase1.json`, `.phase2.json`, `.phase3-final.json`
- `LOCAL_ONLY_MODE` auto-switch in seeder (triggers after 3 consecutive 429s from OpenRouter)

## Key findings / decisions

- 74% of the 500 cache entries have 16+ unique citations; average is 30 citations per answer — quality bar set high from the start.
- Unicode stdout crash (`→` → `'charmap' codec`): fixed by adding UTF-8 reconfigure at top of `app_free.py`.
- OpenRouter daily quota (2000 requests) was hit mid-run; the auto-fallback to local Qwen3 bridged the gap until UTC midnight reset.
- Citation format inconsistency from `gpt-oss-120b:free` (bold markdown instead of `[X:Y]`) was a silent quality killer caught only by post-hoc inspection.
- Coverage after 500 entries: all 114 surahs touched, 20+ Arabic roots, all major prophets + 15 lesser figures, core theology and eschatology categories.

## What was queued for next time

- Continue seeding to grow cache beyond 500 (dedupe cap of 500 was not yet known to be a bug at this point).
- Wire VerseAnalysis JSONs as a proper `tool_get_verse_analysis` tool rather than pre-injecting them.
- Investigate why ~10–15% of single-Arabic-word questions produce 0-char answers despite tool calls completing.

## Cross-references

- Original report: `repo://OVERNIGHT_REPORT.md`
- Continued in: [[session-2026-04-24-overnight-report-2]]
- Related: [[session-2026-04-26-weekend-report]]
