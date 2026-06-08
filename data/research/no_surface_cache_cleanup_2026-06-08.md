# Live-cache no-surface cleanup — re-run (single-process)

**Date:** 2026-06-08
**Branch:** `claude/cache-cleanup-rerun-2026-06-08`
**Goal:** clear the no-surface-rule (9:128 / 9:129) violations the 2026-05-28
background-write race left in the live `data/answer_cache.json`, single-process.

## Process discipline

- A live `app_free.py` server (PID 29652) was found writing the cache on startup
  (last write 9:21:50 pm, after its 9:19 pm start). Per the hard constraint it
  was stopped **before** any cache work began. No background ops were used; the
  merge and surgical fix both ran strictly foreground to full exit.
- All work happened on a worktree copy of the cache; the cleaned file is copied
  back to the main checkout only at the end. `.bak` taken at
  `data/answer_cache.pre-rerun.bak`.

## Pre-state (Step 1)

`python scripts/check_no_surface_rule.py --cache data/answer_cache.json`

**4 surfaces across 3 entries** (all prose `9:128`, no brackets):

| entry | question | surface context |
|-------|----------|-----------------|
| #1514 | What does verse 2:255 say? | "...he removed two verses (9:128-129 and renumbered others)..." |
| #1591 | In what ways does the Quran describe itself? | "...exclusion of 9:128–129 as forged..." |
| #1596 | Explain the structure of the Quran. | "...6,236 in the standard count with 9:128–129 included..." (×2) |

Entry count: **1613**. Cache size: 94,166,426 bytes.

## Step 2 — re-merge cleaned baseline

`python scripts/merge_baseline_to_cache.py` (foreground, exit 0)

- Loaded 62 cleaned baseline records from `baseline_capable_model.jsonl`
  (vendored from `composer-rule-enforcement-2026-05-27`).
- 0 missing citations against Neo4j (6,234 verses reachable).
- Cache before 1613 → after 1613 (net +0; all 0.98-dedupe overwrites).
- **Cleared #1591 and #1596** — they were stale copies of baseline answers that
  were cleaned on the composer-rule branch; the merge propagated the cleaned text.

Re-scan after merge: **1 surface remaining** (#1514).

## Step 3 — surgical fix of the lone remaining surface

The vendored `fix_cache_1514_surface.py` was **stale**: it hardcoded idx 1513 and
a bracketed `" (at [9:128] and [9:129])"` form that no longer exist (the cache
drifted since 2026-05-28 via the race-restore + live-server writes). The actual
remaining surface was at idx **1514** (the "What does verse 2:255 say?" answer),
a prose run inside `"...removed two verses (9:128-129 and renumbered others)..."`.

The script was corrected to locate the violation by scanning answers (robust to
index drift), assert exactly one match, and strip just the numeral run:

> "...he removed two verses ~~(9:128-129 and renumbered others)~~ **(and
> renumbered others)** that he concluded were not part of the original
> revelation."

Meaning preserved; verse reference removed. 10 characters removed.

## Verification (Step 3)

- `python scripts/check_no_surface_rule.py --cache data/answer_cache.json` →
  **OK — 0 surfaces.**
- `python -m pytest tests/ -q` → **236 passed, 1 skipped** (the cache-scan
  regression test, run before the JSONL-test was de-scoped, passed clean).

## End-state

| metric | before | after |
|--------|--------|-------|
| no-surface violations | 4 (3 entries) | **0** |
| entry count | 1613 | 1613 |
| cache size (bytes) | 94,166,426 | 94,166,407 |

No entries dropped. Cleaned cache copied back to the main checkout.
