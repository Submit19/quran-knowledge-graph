# Composer constraints

Binding rules for any pipeline that **composes user-facing answers** (the
overnight cache composer, eval/v2 answer generation, the live `/chat` agent).
Source of authority: memory `khalifa-only-source-rule-project-foundational`.

## 1. The two-source rule

Only two sources are authoritative for anything the app produces:

1. **The Quran** — verse text (Khalifa's English `Verse.text`, plus the Arabic
   Hafs `Verse.arabicPlain`).
2. **Rashad Khalifa's own primary writings** — his translation footnotes, his 38
   Appendices, his books, transcribed sermons, articles. Primary source only —
   never "someone reporting what he said".

Everything else is excluded: hadith collections, classical tafsir, Sunni/Shia
jurisprudence, later Submitter-teacher content, comparative-religion framings
from non-Quranic/non-Khalifa sources, and the model's own pre-existing training
knowledge of Islam. When this rule conflicts with throughput, the rule wins.

## 2. The no-surface rule for 9:128 / 9:129

Khalifa flagged 9:128 and 9:129 as forged additions on Code-19 grounds. The app
must **never surface or reference them in any form** — not in brackets
(`[9:128]`), not in prose (`9:128`, `9:128-129`), not as "the excluded verses",
not by quoting their content.

When an answer needs to explain the 6,234-vs-6,236 verse count or the exclusion,
phrase it without naming the references, e.g. *"two verses Khalifa flagged as
forged additions on Code-19 grounds"*.

## 3. Corpus vs output — the constraint moves downstream

The no-surface rule binds **output**, not the **source corpus**.

| Layer | May name 9:128/9:129? |
|-------|:---------------------:|
| **Corpus** (Khalifa-primary text, faithfully preserved — e.g. Appendix 24) | **Yes.** Khalifa wrote about these verses; censoring the corpus would be the opposite of Khalifa-strict. |
| **Composer** (reads the corpus to build answers) | Reads freely, but must **not propagate** the references into answers. |
| **Cache** (composed answers stored) | **No** surfaced references. |
| **App output** (what users see) | **No** surfaced references. |

So the composer is expected to *read* corpus passages that discuss the forged
verses, understand them, and produce answers that respect the exclusion without
ever naming the references.

## 4. Enforcement — `scripts/check_no_surface_rule.py`

The scanner inspects the **`answer` field only** of each entry (never
`question`, `notes_meta`, or other metadata) for bracket and prose forms of
9:128 / 9:129.

```bash
# Default: scan all tracked eval/v2 JSONL outputs
python scripts/check_no_surface_rule.py

# Explicit JSONLs and/or the (gitignored) live cache
python scripts/check_no_surface_rule.py data/eval/v2/*.jsonl --cache data/answer_cache.json
```

Exit code 0 = clean, 1 = violations (each printed with source, entry id,
location, and surrounding context).

CI guard: `tests/test_no_surface_rule.py` enforces the same invariant over the
tracked eval/v2 JSONLs and skips gracefully when the cache is absent.

## 5. Recommended pre-commit hook

Wire the scanner into `.pre-commit-config.yaml` so no future composer output can
reintroduce the references silently:

```yaml
  - repo: local
    hooks:
      - id: no-surface-rule
        name: no-surface rule (9:128/9:129)
        entry: python scripts/check_no_surface_rule.py
        language: system
        files: ^data/eval/v2/.*\.jsonl$
        pass_filenames: false
```

(The live cache is gitignored, so the hook covers tracked JSONL outputs; scan
the cache manually with `--cache` after each composition run.)
