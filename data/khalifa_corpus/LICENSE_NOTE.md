# Khalifa Corpus — Copyright & Provenance

**Scraped:** 2026-05-29 · **Source of record:** masjidtucson.org · **Branch:** `claude/khalifa-corpus-scrape-2026-05-27`

This directory holds Rashad Khalifa's own primary writings, scraped from
masjidtucson.org for a non-commercial, research-internal Submitter study tool.
It is the second retrieval layer (alongside the Neo4j verse graph) that grounds
the composer in Khalifa-primary text — see `memory/feedback_khalifa_only_sources.md`
(the binding rule) and `COMPOSER_CONSTRAINTS.md` (how the rule applies downstream).

## What's here (ungated sources only)

| Bucket | Source | Files | Words | Year |
|---|---|---|---|---|
| Introduction to *The Final Testament* | /quran/appendices/introduction.html | 1 | ~3.8K | 1989 |
| 38 Appendices | /quran/appendices/appendix{1..38}.html | 38 | ~49K | 1989 |
| *Quran, Hadith and Islam* | /publications/books/qhi/ (per-page PDFs) | 80 | ~15K | 1982 |
| Submitters Perspective (Khalifa-era) | /publications/books/sp/{1985..1990}/ | 64 | ~130K | 1985-02 → 1990-03 |
| **Total** | | **183** | **~198K** | |

Exact per-file provenance (title, author, source URL, masthead, sha256,
word/char counts, 9:128/9:129 flag) is in `MANIFEST.json`.

### Extraction notes
- **QHI** word count is lower than the source's printed length: Arabic
  quotations in these typeset PDFs render as embedded glyphs, not Unicode, so
  the Arabic is not preserved (English commentary extracts cleanly). The
  per-page PDFs were used precisely because the consolidated `qhi.html` renders
  Arabic as inline GIFs — even worse for extraction.
- **SP** masthead varies by issue (early issues are "Muslim Perspective" /
  "Monthly Bulletin of United Submitters International"); the original masthead
  is preserved per-issue in frontmatter.

## Copyright posture

masjidtucson.org carries an "© All Rights Reserved" footer. The Appendices,
Introduction, QHI book, and SP newsletters scraped here are **not** behind any
click-through gate. They were fetched politely: a single identifying
User-Agent, ≥1 second between requests, and on-disk caching to avoid re-fetch.

The corpus is used **research-internally and transformatively** — the composer
generates new answers grounded in this text; it does not republish the books.
This is consistent with fair use (educational/research purpose, transformative
use, no market substitution for the original publications).

## Gated sources — DEFERRED (not in this scrape)

Two books sit behind a per-book copyright-agreement gate on masjidtucson.org:

- *Quran: Visual Presentation of the Miracle* (1982) — 57 files, ~15K words
- *The Computer Speaks: God's Message to the World* (1982) — 36 files, ~10K words

The gate text reads, verbatim:

> Except as permitted under the Copyright Act of 1976, this book may not be
> reproduced in whole or in part in any manner without written permission from
> the copyright owner.

This is standard "all rights reserved" language and does not preclude fair use,
but it is an explicit publisher assertion. Per the discovery briefing's
recommendation (option C-then-A), these are deferred to a future session once
permission is settled.

### ⚠ Operator action item

> **Email `info@masjidtucson.org`** requesting explicit permission to include
> *Visual Presentation of the Miracle* + *The Computer Speaks* in this
> Khalifa-source corpus, for a non-commercial, Submitter-audience study tool.
> Permission would unblock ~25K additional words across 93 files.

## Excluded by the binding rule (never in this corpus)

- Post-1990-03 Submitters Perspective issues (community-edited)
- submission.org, 19.org (anonymous / post-Khalifa community)
- Lisa Spray's books, *Beyond Probability*, *Understanding Islam*, *Weekly
  Reminder*, the *Proclamation* page (community contributors / org-bylined)
- Hadith collections, classical tafsir, jurisprudence (non-Khalifa sources)

## Deferred (future sessions)

- Khalifa Friday sermons 1985–1989 (audio/video only; needs a Whisper STT pass)
- Khalifa's translation footnotes as a standalone export (verify first whether
  already captured in Neo4j `Verse.text`)
