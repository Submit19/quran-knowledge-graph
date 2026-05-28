# Khalifa Corpus Discovery — Phase 2: Primary-Source Manifest

**Date:** 2026-05-27
**Binding rule:** [feedback_khalifa_only_sources.md](../../../../../../.claude/projects/C--Users-alika-Agent-Teams-quran-graph-standalone/memory/feedback_khalifa_only_sources.md)
**Machine-readable companion:** [`02_primary_source_manifest.json`](02_primary_source_manifest.json)

Per the rule: only Quran verse text + Khalifa's own primary writings. The Quran translation itself is already in the graph as `Verse.text`. This manifest covers everything ELSE that is Khalifa-primary and not yet in the graph.

## Khalifa-PRIMARY items (6 buckets, ~480 source URLs)

| # | Item | Year | Format | URLs | Est. words | Khalifa-primary? |
|---|---|---|---|---|---|---|
| 1 | Introduction to The Final Testament | 1989 | HTML × 1 | 1 | ~3,700 | ✅ Signed "Rashad Khalifa / Tucson / Ramadan 26, 1409" |
| 2 | 38 Appendices to The Final Testament | 1989 | HTML × 38 | 38 | ~130,000 | ✅ Attributed throughout to Khalifa |
| 3 | *Quran, Hadith and Islam* | 1982 | PDF × 89 chapters + HTML consolidated | 92 | ~38,000 | ✅ Title page byline "By: Rashad Khalifa, Ph.D." |
| 4 | *Quran: Visual Presentation of the Miracle* | 1982 | PDF × 57 | 57 | ~15,000 | ✅ Title page byline; Islamic Productions, Tucson |
| 5 | *The Computer Speaks: God's Message to the World* | 1982 | PDF × 36 | 36 | ~10,000 | ✅ Title page byline; Islamic Productions, Tucson |
| 6 | Submitters Perspective newsletter, 1985-02 → 1990-03 | 1985–1990 | HTML × ~256 pages | ~256 | ~230,000 | ✅ "Editor: Rashad Khalifa, Ph.D." — 64 issues during his editorship |
| **Total** | | | | **~480 URLs** | **~430,000 words** | |

Estimated extracted corpus: **≈ 4 MB of Markdown text** after PDF / HTML extraction (PDF binaries themselves sum to ≈ 80 MB).

### Per-item URLs

All exact URLs are in the JSON manifest. Patterns (for the scraper):

- **Appendices:** `https://www.masjidtucson.org/quran/appendices/appendix{1..38}.html` + `introduction.html`
- **QHI book:** `https://www.masjidtucson.org/publications/books/qhi/QURAN_Hadith_Islam_pg{1..89}.pdf` + 3 front-matter PDFs + `qhi.html` (consolidated HTML alternative). Alt mirror: `https://submission.ws/downloads/qhi.pdf` (single-file).
- **Visual Presentation:** `https://www.masjidtucson.org/publications/books/vp/fact{01..52}.pdf` + 5 front-matter PDFs
- **Computer Speaks:** `https://www.masjidtucson.org/publications/books/computer_speaks/fact{01..31}.pdf` + ~5 front-matter PDFs
- **SP newsletter:** `https://www.masjidtucson.org/publications/books/sp/{YYYY}/{mmm}/page{1..4}.html` for the 64 Khalifa-edited issues (year/month list in JSON)

## EXPLICITLY EXCLUDED (and why)

Per the binding rule, the following are NOT Khalifa-primary and must NOT enter the corpus:

| Excluded | Why |
|---|---|
| Proclamation page (`/quran/appendices/proclamation.html`) | Authored by ICS / United Submitters International as an org, not Khalifa-bylined |
| Lisa Spray's 5 books (Jesus, Women's Rights, Heart's Surprise, Lifting the Veil, Christian Doctrine) | Community contributor; not Khalifa |
| Beyond Probability Series 1 & 2 (Abdullah Arik / Faiz Currim / Lisa Spray) | Community contributors |
| Understanding Islam (Masjid Tucson Submitters) | Collective community byline |
| Weekly Reminder | Modern community-authored, post-Khalifa |
| **Submitters Perspective April 1990 onwards (through 2026)** | Post-Khalifa community editorship — **this is the biggest exclusion by volume**; ~430 community-edited issues |
| **submission.org entire site** | Anonymous community editors; self-described as "not owned, maintained, managed or operated by any kind of legal organizations" |
| **19.org entire site** | Edip Yuksel platform; articles ABOUT Khalifa are secondary attribution |
| masjidtucson.com | Commerce catalog only; no full-text content |

## Khalifa-primary vs Khalifa-as-referenced: the rule applied

The brief calls out this distinction: a page that says "Khalifa wrote X" with his actual text verbatim is primary IF the quoted text is verifiably his. A page that says "Khalifa believed Y" without verbatim quotation is secondary — exclude.

Examples from this discovery:

- ✅ **Appendix 24, "Two False Verses Removed from the Quran"** — Khalifa's own essay arguing 9:128-9:129 are forged. PRIMARY (and is the source of the project's exclusion rule for those two verses; surface the *essay* in the corpus, but per the binding hard rule the *runtime app* must still never surface the two verses themselves).
- ✅ **SP 1989-Jan-page1 "God Exposes Their Disbelief: I.S.N.A. (Mohamedan Society of North America) Cancels the First Pillar of Islam"** — bylined "Editor: Rashad Khalifa, Ph.D." — PRIMARY.
- ❌ **19.org "In Defense of Rashad Khalifa against Slanderers"** — article *about* Khalifa by community author; SECONDARY → exclude.
- ❌ **submission.org topical articles** — anonymous "Editors of Submission.org" byline; SECONDARY → exclude.
- ❌ **Proclamation** — org-authored, not personally bylined to Khalifa → exclude.

## Items deferred to future corpus-expansion sessions

| Item | Reason deferred |
|---|---|
| Khalifa Friday sermons / khutbas (1985–1989) | No text transcripts exist on canonical sites. YouTube videos + submission.ws session summaries available. Needs Whisper STT in a later session. |
| Khalifa's translation footnotes (standalone export) | Need to verify whether `Verse.text` in Neo4j already includes footnote text. If yes, skip; if no, extract. |

## Key counts for operator

- **6 distinct material types** (1 intro + 38 appendices + 4 books + 1 newsletter series)
- **~480 URLs** to fetch
- **~430K words** of estimated Khalifa-primary text
- **~80 MB PDF + HTML on disk** before extraction; **~4 MB Markdown** after
- **64 Khalifa-edited SP issues** vs **~430 post-Khalifa SP issues excluded** — the exclusion rule is doing real work here
- **5 community-authored books on the same publisher's site EXCLUDED** — the rule is doing real work here
- **0 dependencies on submission.org or 19.org** — both excluded entirely
