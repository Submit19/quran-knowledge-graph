# Khalifa Corpus Discovery — Phase 4: Operator Briefing

**Date:** 2026-05-27
**Branch:** `claude/khalifa-corpus-discovery-2026-05-27`
**Status:** Discovery complete. Awaiting operator approval before any bulk scrape.

This is a discovery-only output. No bulk download occurred. The manifest below is what an actual scrape session would consume.

---

## TL;DR

- **6 distinct Khalifa-primary material types, ~480 URLs, ~430,000 words of Khalifa text** waiting to be ingested as the corpus.
- **One canonical source (masjidtucson.org)** does all the heavy lifting. submission.ws is a useful fallback. submission.org and 19.org are EXCLUDED per the binding rule.
- **The biggest exclusion by volume:** ~430 post-Khalifa-death SP newsletter issues (April 1990 → 2026) are community-edited and excluded. The 64 issues Khalifa edited himself (Feb 1985 → March 1990) are in.
- **One open licensing question** (the per-book copyright gate on VP/CS) and **one extraction-quality concern** (Arabic-as-GIF in QHI HTML, mitigated by using PDFs). Both have pragmatic fallbacks.
- **Recommended next session:** scrape the ungated material first (~430K words from Appendices + Intro + SP-Khalifa-era + QHI), then circle back on VP/CS after operator decides on the licensing question. Estimated scrape session ~50 min ungated, +30 min for VP/CS.

---

## What's in the corpus (Khalifa-primary, ~480 URLs)

| Bucket | Source | URLs | Words | Year |
|---|---|---|---|---|
| Introduction to *The Final Testament* | masjidtucson.org/quran/appendices/introduction.html | 1 | ~3.7K | 1989 |
| 38 Appendices | masjidtucson.org/quran/appendices/appendix{1..38}.html | 38 | ~130K | 1989 |
| *Quran, Hadith and Islam* | masjidtucson.org/publications/books/qhi/ (89 PDFs + 1 HTML) | 92 | ~38K | 1982 |
| *Quran: Visual Presentation of the Miracle* | masjidtucson.org/publications/books/vp/ (52 facts + 5 front) | 57 | ~15K | 1982 |
| *The Computer Speaks* | masjidtucson.org/publications/books/computer_speaks/ (31 facts + 5 front) | 36 | ~10K | 1982 |
| Submitters Perspective (Khalifa-edited issues only) | masjidtucson.org/publications/books/sp/{1985..1990}/ | ~256 | ~230K | 1985-02 → 1990-03 |
| **Totals** | | **~480** | **~430K** | |

Full URL list + per-item attribution evidence in [`02_primary_source_manifest.json`](02_primary_source_manifest.json).

## What's NOT in the corpus (and why)

- **Post-1990 SP issues** — ~430 community-edited issues. Excluded per rule.
- **submission.org** — anonymous "Editors of Submission.org" content. Excluded.
- **19.org** — Edip Yuksel platform + articles *about* Khalifa. Excluded.
- **Lisa Spray's 5 books, Beyond Probability, Understanding Islam, Weekly Reminder** — same publisher, but community contributors. Excluded.
- **Proclamation page** — org-authored, not Khalifa-bylined.

## What's DEFERRED (needs a future session)

- **Khalifa Friday sermons / khutbas 1985–1989** — audio/video only on YouTube + submission.ws. No text transcripts on canonical sites. Needs a Whisper STT pass in a later session. Estimated ~40 hours of audio.
- **Khalifa's translation footnotes as standalone export** — may already be in `Verse.text` in Neo4j (verify before extracting; could be a 30-min spot check).

## Sites of record (priority order for the scrape session)

1. **masjidtucson.org** — primary canonical, fetches every item in the manifest
2. **submission.ws** — fallback for QHI consolidated PDF (`/downloads/qhi.pdf`); useful only if masjidtucson.org is unreachable
3. Nothing else — discovery confirmed no other site has Khalifa-primary text not also on (1)

## TOS / licensing summary

| Site | License status |
|---|---|
| masjidtucson.org | "© All Rights Reserved" footer + per-book click-through gate on VP/CS only. No explicit reprint policy. No `robots.txt` checked yet (do this before scraping). |
| submission.ws | No TOS, no copyright statement visible. Don't scrape unless masjidtucson.org fails. |

The VP/CS gate text (verbatim, from sample verification):

> Except as permitted under the Copyright Act of 1976, this book may not be reproduced in whole or in part in any manner without written permission from the copyright owner.

Standard "all rights reserved" — does not preclude fair use (research / transformation / non-public-republication). Operator decides whether to email `info@masjidtucson.org` for explicit permission or to rely on fair use for a research-internal corpus.

## Sample verification (Phase 3) headline findings

| Sample | Verdict | Key insight |
|---|---|---|
| Appendix 24 ("Two False Verses") | ✅ Khalifa-primary, 12-13K words | This is the source essay for the 9:128/129 rule — references those verses ~dozens of times by number. **Corpus must preserve full text; runtime composer must scrub references in output.** |
| QHI consolidated HTML | ✅ Khalifa-primary, 18-20K words, dated Aug 19 1982 | **Arabic appears as inline GIF images, not Unicode** — extraction will silently drop Arabic. Use per-chapter PDFs instead (Arabic likely embedded as text). |
| SP Feb 1985 issue #1 | ✅ Khalifa-edited; lead piece "WHO ARE WE?" | Inaugural issue masthead was "Muslim Perspective" / "Monthly Bulletin of United Submitters International" — renamed later. Preserve actual masthead per-issue. No explicit per-article bylines on inaugural issue; treat issue-as-unit. |

## Recommended scrape session plan

### Format & storage

- **Output format: Markdown** (`.md`), one file per source URL or per book chapter. Why Markdown:
  - Unified format across HTML and PDF inputs
  - Preserves heading structure (important for Appendix structure, book chapters)
  - Easy to embed (chunk into 1024-token windows for BGE-M3)
  - Human-readable for spot-checking
- **Per-file frontmatter** (YAML) with: source URL, fetch date, source format, byline / attribution evidence, year, category (`appendix` | `book_chapter` | `newsletter_issue` | `intro`)
- **Storage location: `data/khalifa_corpus/`** as a tracked directory. **Rationale:** the corpus is small (~4 MB extracted Markdown), worth tracking in git so the cache + composer pipeline have deterministic content to retrieve from. Unlike `data/answer_cache.json` (90 MB, gitignored), this is bounded and stable.
- **Directory structure:**
  ```
  data/khalifa_corpus/
    introduction.md
    appendices/
      appendix01.md ... appendix38.md
    books/
      quran_hadith_islam/
        ch01.md ... ch89.md
      visual_presentation/
        fact01.md ... fact52.md
        intro.md, summary.md
      computer_speaks/
        fact01.md ... fact31.md
    newsletters/
      1985/
        02_who_are_we.md
        ...
      1990/
        03_final_issue.md
    MANIFEST.json     # ingestion-time manifest with hashes, URLs, byline metadata
    LICENSE_NOTE.md   # quote the copyright gate verbatim + operator's licensing decision
  ```

### Sources in priority order

1. **First**: Appendices + Introduction (~39 HTML pages, ~5 min) — no gate, clean text
2. **Second**: SP newsletter Khalifa-era (~256 HTML pages, ~10 min) — no gate, clean text
3. **Third**: QHI book — try per-chapter PDFs first, fall back to consolidated HTML — ~10 min
4. **Fourth**: VP + CS books (~93 PDFs, ~15 min) — **gated; only after operator clears Open Question #1**

### Verification pass within scrape session

For each extracted file:
- Re-detect byline / attribution in the extracted text; compare against manifest expectation; flag any mismatch
- Token-count + Arabic-presence check
- Run a regex scrub to detect `9:128` or `9:129` strings — flag (don't remove) so operator can verify the binding rule's scope
- Emit per-file `*.provenance.json` sidecars

### Estimated scrape session time

| Scope | Time | Output |
|---|---|---|
| Ungated only (Appendices + Intro + SP + QHI) | ~50 min | ~387 source files → ~405K words ingested |
| Full (+VP +CS, after operator approval) | ~80 min | ~480 source files → ~430K words ingested |

---

## Three open questions for the operator before scraping begins

### Q1 — Licensing on VP and CS books

Both *Visual Presentation* and *The Computer Speaks* sit behind a per-book copyright agreement gate stating:

> Except as permitted under the Copyright Act of 1976, this book may not be reproduced in whole or in part in any manner without written permission from the copyright owner.

This doesn't preclude fair use for research, but it's a click-through assertion of the publisher's position. Options:

- **(A) Email `info@masjidtucson.org`** identifying the project as Submitter-aligned research using Khalifa's writings to ground a Quran exploration agent. Request written permission. ETA: 1 email + ~1 week wait.
- **(B) Rely on fair use** — corpus is research-internal, transformative (composer generates new text), non-republished. Proceed. *Faster but exposes the project if the publisher later objects.*
- **(C) Skip VP and CS for now** — start the corpus with the ungated material (387 files / ~405K words is already very substantial). Revisit VP+CS after a decision on (A) vs (B).

Recommendation: **(C) then (A) in background**. The 25K-word VP+CS slice is only ~6% of the corpus; missing it for the first scrape doesn't materially degrade the pipeline, and the gated-then-approved path is cleanest.

### Q2 — How to handle 9:128 / 9:129 in Appendix 24 (and likely other Khalifa writings)

The binding hard rule: **the runtime app must NEVER surface or reference 9:128 or 9:129 in any form.**

Appendix 24 is the essay that *originates* the project's exclusion of these verses — it cites them ~dozens of times by number. The same likely applies to other Appendices, the introduction, and possibly SP issues from Khalifa's later years.

Options for where the rule applies in the pipeline:

- **(A) Pre-redact at ingestion** — strip `9:128` / `9:129` strings from the corpus before storage. *Risk:* breaks the composer's ability to handle "why do Submitters reject these verses?" questions.
- **(B) Preserve in corpus, scrub at composer-output** — corpus has full text; composer's system prompt + a post-generation regex enforce no-surface in user-visible output. *Lets the composer "know" the essay exists without leaking the verse numbers.*
- **(C) Preserve in corpus, scrub at composer-prompt** — same as (B) but also redact verse numbers from any corpus chunks injected into the composer's prompt. *Safest, but the composer can't actually answer "why are these excluded?" because the substantive answer requires the numbers.*

Recommendation: **(B)**. Aligns with the rule (no surfacing in output) without breaking the composer's intelligence about Khalifa's own argument.

### Q3 — Sermon transcripts: scope this session or defer?

Khalifa's Friday sermons 1987-1989 exist as YouTube videos and audio files on submission.ws. No text transcripts on canonical sites. Estimated ~40 hours of audio.

Options:

- **(A) In scope for this session** — fire a Whisper STT step (using openai-whisper or similar) inside the scrape session. *Significantly extends session time — STT on 40 hours = many hours of compute.*
- **(B) Out of scope; defer to a dedicated session** — initial corpus ships with 6 buckets / 480 URLs / 430K words. Sermons are a Phase-N addition.
- **(C) Skip permanently** — rely only on Khalifa's written material. Sermons may be transcribed for community use but the project commits to text-only primary sources.

Recommendation: **(B)**. Initial corpus is already substantial. Sermons earn their own session with its own time/compute budget once the rest of the pipeline (corpus → retriever → composer rewire) is proven.

---

## What's already committed on this branch

Four commits in chronological order:

1. `48ebffa` — research: corpus discovery phase 1 — Submitter-canonical site inventory
2. `e160ed6` — research: corpus discovery phase 2 — Khalifa primary-source manifest
3. `af5d135` — research: corpus discovery phase 3 — sample verification
4. *(this commit)* — docs: corpus discovery briefing + recommended scrape plan

All deliverables sit under [`data/research/khalifa_corpus_discovery/`](.).

Tests passing: 208 passed + 2 skipped (matches working-tree baseline; no code changes in this discovery branch).
