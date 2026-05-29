# No-surface-rule violations — 9:128 / 9:129 scan (2026-05-27)

Scan of user-facing **answer** fields against the no-surface rule (memory:
`khalifa-only-source-rule-project-foundational`): the app must never surface or
reference 9:128 / 9:129 in any form — not in brackets, not in prose, not as
"the excluded verses". The rule binds output; the source corpus may name them.

Produced by `scripts/check_no_surface_rule.py`. Only the `answer` field of each
entry is inspected — `question` / `notes_meta` / other metadata are out of scope.

## Summary

| Source | Status | Distinct entries | Surfaces |
|--------|--------|-----------------:|---------:|
| `data/eval/v2/baseline_capable_model.jsonl` (tracked) | **CLEANED in this commit** | 3 | 4 |
| `data/eval/v2/baseline_extra_overnight_2026-05-21.jsonl` (unmerged, `origin/claude/cache-content-expansion-2026-05-21`) | open — next-session cleanup | 5 | 76 |
| `data/answer_cache.json` (gitignored, ~1,612 entries) | open — next-session cleanup | 3 | 4 |

The tracked baseline is now clean and the CI guard (`tests/test_no_surface_rule.py`)
passes against it. The remaining 80 surfaces live in **unmerged / gitignored**
content and are recorded here as Path A cleanup work — they do **not** block this
commit.

## 1. `baseline_capable_model.jsonl` — CLEANED

These three entries were reworded in this commit to drop the references while
preserving meaning:

- **broad-006** (prose): "Khalifa's exclusion of 9:128–129 as forged" →
  "Khalifa's exclusion of two verses he flagged as forged additions".
- **broad-011** (prose ×2): "6,236 in the standard count with 9:128–129 included"
  and "excludes 9:128–129 on Code-19 grounds" → reworded to "the two verses
  Khalifa flagged as forged".
- **broad-019** (bracket ×1): removed the `- [9:128]: (Khalifa-excluded …)`
  bullet entirely from the list of character verses.

## 2. `baseline_extra_overnight_2026-05-21.jsonl` — UNMERGED, 76 surfaces

Lives only on `origin/claude/cache-content-expansion-2026-05-21`. Five entries —
all heavily corrupted "categorical-" overnight output — repeatedly surface the
references in both prose forms (`9:128`, `9:129`) and combined (`9:128-129`):

- **expansion-307** — ~12 surfaces ("the categorical-verses-9:128-129 controversy …")
- **expansion-308** — ~17 surfaces ("the categorical-from-[27:30]-to-9:128 count …")
- **expansion-311** — ~16 surfaces (last-revealed-verse discussion)
- **expansion-312** — ~2 surfaces ("9:128-129 forgeries")
- **expansion-313** — ~29 surfaces (an entire essay built around the two verses,
  including quoting their standard-text content)

These entries are independently low-quality (the "categorical-" prefix spam marks
them as garbage regardless of the no-surface rule) and should be dropped or
regenerated, not merged.

## 3. `data/answer_cache.json` — gitignored, 4 surfaces

Three live cache entries surface the references in prose:

- **#1514** "What does verse 2:255 say?" — "he removed two verses (9:128-129 …)"
- **#1591** "In what ways does the Quran describe itself?" — "Khalifa's exclusion
  of 9:128–129 as forged" (same prose as the now-cleaned broad-006)
- **#1596** "Explain the structure of the Quran." — "6,236 in the standard count
  with 9:128–129 included" / "excludes 9:128–129 on Code-19 grounds" (same prose
  as the now-cleaned broad-011)

Entries #1591 / #1596 are the cache copies of the baseline answers just cleaned;
re-running composition for those questions (or applying the same rewording) will
clear them.

## Disposition

- **This commit:** baseline cleaned, scanner + CI guard landed.
- **Next session (Path A):** clean / regenerate the 3 cache entries; drop the 5
  `baseline_extra_overnight` entries from the expansion branch before any merge.
- **Going forward:** wire `scripts/check_no_surface_rule.py` into a pre-commit
  hook (see `data/khalifa_corpus/COMPOSER_CONSTRAINTS.md`) so no future composer
  output can reintroduce the references silently.
