---
type: decision
adr: 0018
status: accepted
date: 2026-05-12
tags: [decision, agentic, loop]
supersedes: none
---

# ADR-0018 — Haiku end-of-tick prep (validate_specs + precache_research + preclassify_proposals)

## Status
Accepted (2026-05-12). Active.

## Context
At the end of each tick, before the orchestrator commits, there are three failure-safe jobs that improve the next tick's efficiency. Commit `53cd6fd` introduced `scripts/haiku_prep.py`, run by `tick_finalize.py` after main work but before commit. Three sub-steps: (1) validate_specs fixes malformed YAML and warns about tasks missing required fields; (2) precache_research pre-fetches the next 2 WebFetch-handler URLs to local cache (24h TTL, 200KB cap); (3) preclassify_proposals uses Haiku to annotate pending tasks with classification, duplicate_of, and relates_to links.

## Decision
Run three Haiku-driven prep jobs at tick_finalize time:
1. **validate_specs** (pure Python) — auto-fix file_min_bytes, warn about missing query/script/query_kind in cypher_analysis tasks.
2. **precache_research** (pure Python + requests) — pre-fetch next 2 research URLs to `data/research_cache/` (gitignored, per-machine).
3. **preclassify_proposals** (Haiku API calls) — for each pending proposal lacking haiku_notes, call Claude Haiku to annotate classification, duplicates, and cross-references.

## Consequences
- **Positive:** IMPL ticks see pre-classified tasks (faster picker); RESEARCH ticks can read cached content; spec validation surfaces issues early (see `data/spec_warnings.md`). Cost is ~$0.005/call × 24 ticks/day = ~$0.12/day.
- **Negative:** Adds ~12s per tick (three sub-jobs). Cache is per-machine (gitignored); offline mode requires `HAIKU_PREP_DISABLED=1`.
- **Neutral:** Haiku model is tunable via `HAIKU_PREP_MODEL` env var (default `claude-haiku-4-5`). Precache count tunable via `HAIKU_PREP_PRECACHE_N`.

## Cross-references
- Source evidence: commit `53cd6fd` — `git show 53cd6fd` for full context
- Related: [[0015-manual-cypher-analysis-task-mode]], [[0016-cron-prompt-file-based-brief]], `repo://scripts/haiku_prep.py`
