# Khalifa Corpus Discovery — Phase 1: Site Inventory

**Date:** 2026-05-27
**Branch:** `claude/khalifa-corpus-discovery-2026-05-27`
**Binding rule:** [feedback_khalifa_only_sources.md](../../../../../../.claude/projects/C--Users-alika-Agent-Teams-quran-graph-standalone/memory/feedback_khalifa_only_sources.md) — only Quran verse text + Rashad Khalifa's own primary writings; nothing else.

## Summary verdict per site

| Site | Status | Reason |
|---|---|---|
| **masjidtucson.org** | **PRIMARY canonical** | Khalifa's own mosque (ICS / Masjid Tucson); hosts his Quran translation, all 38 Appendices, 4 of his books, and the SP newsletter archive he edited 1985–1990 |
| **submission.ws** | **SECONDARY aggregator** | Khalifa-centric content but anonymous authorship + no TOS; useful as mirror / alt-PDF source but not authoritative |
| submission.org | **EXCLUDED** | Self-describes as "not owned, maintained, managed or operated by any kind of legal organizations or organized groups" — anonymous community editors; no Khalifa bylines |
| 19.org | **EXCLUDED** | Edip Yuksel platform; 162+ Yuksel articles, Khalifa is *discussed about* not *authored on* this site |
| masjidtucson.com | **EXCLUDED** | Commerce catalog only (book/DVD sales); same publisher but no primary text content |

---

## Site 1: masjidtucson.org (PRIMARY canonical)

**Operator:** International Community of Submitters (ICS) / Masjid Tucson — the mosque Dr. Rashad Khalifa founded and led until his death on 1990-01-31.

**Copyright statement:** Footer reads `© All Rights Reserved` — no dedicated Terms of Use or Reprint Permission page exists. The book PDFs (Visual Presentation, The Computer Speaks) are gated behind a per-book "I Agree to copyright terms" landing page; PDF binaries are downloadable once past the gate. *No explicit machine-readable license; treat as "all rights reserved" by default. See Open Question #1 in Phase 4.*

**Sitemap:** None advertised. Site is navigable but discovery is by following internal links.

**Top-level navigation:** `God/`, `submission/`, `submission/practices/`, `quran/`, `publications/`, `videos/`, `news/`

**Content tree (Khalifa-primary, confirmed):**

```
/quran/                                  -> Quran translation (already in graph as Verse.text + Verse.arabicPlain)
/quran/appendices/
  introduction.html                      -> ~3,500 words; signed "Rashad Khalifa / Tucson / Ramadan 26, 1409"
  proclamation.html                      -> ~650 words; org-authored (United Submitters International), NOT Khalifa-bylined → exclude
  appendix1.html ... appendix38.html     -> 38 Appendices, all attributed to Khalifa, HTML format
/publications/books/
  qhi/                                   -> "Quran, Hadith and Islam" (89 chapters as individual PDFs + consolidated qhi.html)
  vp/                                    -> "Quran: Visual Presentation of the Miracle" (1982): 52 Facts as PDFs + front matter
  computer_speaks/                       -> "The Computer Speaks" (1982): 31 Facts as PDFs + front matter
  sp/                                    -> Submitters Perspective newsletter (1985-02 → present); Khalifa edited 1985-02 → 1990-03
/videos/                                 -> Audio/Video material (Khalifa Friday sermons); links to YouTube, no text transcripts
```

**Content tree (NOT Khalifa-primary — community contributors, EXCLUDED):**

```
/publications/books/
  bp2/                                   -> Beyond Probability Series 2 (Faiz Currim & Lisa Spray)
  womensrights/                          -> Women's Rights (Lisa Spray)
  heartssurprise/                        -> Heart's Surprise (Lisa Spray)
  lifting_the_veil/                      -> Lifting the Veil (Lisa Spray)
  development_christian_doctrine/        -> (Lisa Spray)
  jesus/                                 -> Jesus: Myths & Message (Lisa Spray)
  understanding_islam/                   -> Understanding Islam (Masjid Tucson Submitters — community)
  weekly/                                -> Weekly Reminder (community-authored)
/publications/books/sp/ (post-1990-03)   -> Submitters Perspective after Khalifa's death (community-edited)
```

**Sample-verified accessibility:**
- `/quran/appendices/introduction.html` → HTML, fetch OK, Khalifa-signed
- `/publications/books/qhi/contents.html` → HTML index, fetch OK
- `/publications/books/qhi/QURAN_Hadith_Islam_pg1.pdf` → PDF binary 187 KB, fetch OK (needs pypdf extraction)
- `/publications/books/sp/1989/jan/page1.html` → HTML, fetch OK, byline "Editor: Rashad Khalifa, Ph.D."
- `/publications/books/sp/1985/` (dir listing) → **403 Forbidden** (no directory browse; must hit specific page URLs)

---

## Site 2: submission.ws (SECONDARY aggregator)

**Operator:** Unidentified. No About page, no TOS, no copyright statement on the landing or about/ pages.

**Content character:** Khalifa-centric. Hosts:
- An index of 50 Khalifa Quranic study sessions at `/listen-to-quranic-study-sessions-with-dr-rashad-khalifa/` — **detailed text summaries**, not full transcripts; actual audio lives elsewhere on the site
- Khalifa YouTube videos curated at `/videos-aboutquran-and-submission-by-dr-rashad-khalifa-sp-258822432/`
- Alt-PDF mirror of QHI: `https://submission.ws/downloads/qhi.pdf` (single file vs. masjidtucson.org's per-chapter PDFs)
- An "Audios" → "Submission Radio" section

**Verdict:** **secondary**. Useful as fallback PDF mirror or for the study-session index (when those are eventually STT'd). Anything sourced *from here only* (not also on masjidtucson.org) should be treated as needing Khalifa-primary verification before inclusion. Per the rule, no Khalifa-primary corpus item should depend solely on submission.ws.

---

## Site 3: submission.org (EXCLUDED)

**Operator:** "Editors of Submission.org" — explicitly self-described as "not owned, maintained, managed or operated by any kind of legal organizations or organized groups… a group of like-minded, monotheistic individuals all over the world." Anonymous community.

**Content character:** Topical articles on Submission theology with no individual author bylines. Page footer attributes to collective Editors.

**Khalifa-primary content:** None bylined. The Quran section on this site uses Khalifa's translation but the surrounding commentary is community-authored.

**Verdict:** **EXCLUDED.** No Khalifa-primary content present that isn't already on masjidtucson.org. Per the binding rule, "subsequent Submitter teachers' content (community newsletters, modern teachers, 'Khalifa's followers said')" is excluded.

---

## Site 4: 19.org (EXCLUDED)

**Operator:** Reformist platform; dominated by Edip Yuksel (162+ articles in his category).

**Content character:** Articles *about* Khalifa ("Year 1974: the Historic Discovery and Announcement by Rashad Khalifa", "In Defense of Rashad Khalifa against Slanderers", "Is Rashad's Translation of the Quran Error-free?") — all secondary attribution.

**Verdict:** **EXCLUDED.** Edip Yuksel post-Khalifa work is explicitly excluded by the rule. Articles *about* Khalifa = secondary attribution, not primary corpus material.

---

## Site 5: masjidtucson.com (EXCLUDED)

Commerce catalog (`/catalog/`) selling printed books, CDs, DVDs. Same publisher as masjidtucson.org but no full-text content. Useful as a cross-reference for "which titles does the publisher recognize as Khalifa-authored" (Quran: Final Testament; The Computer Speaks; Quran: Visual Presentation; Quran, Hadith and Islam — 4 of his books, all already inventoried above).

---

## TOS / copyright concerns to surface to operator

1. **No explicit license.** None of the canonical sites publish a Creative Commons license, reprint permission, or "may be reproduced for…" clause. Default is "All Rights Reserved."
2. **Per-book copyright gate.** `/publications/books/vp/` and `/publications/books/computer_speaks/` require users to "I Agree" before downloading PDFs. This is a click-through agreement whose text I should pull before bulk-fetching past the gate. *Phase 3 sample verification will quote the gate text verbatim so operator can decide.*
3. **No `robots.txt` checked yet.** Should pull robots.txt before any scrape session to honor crawl directives.
4. **No machine-readable contact for permission request.** `info@masjidtucson.org` exists; if the operator wants to be conservative, the ethical path is to email and request permission to mirror for research use, framing the project as Submitter-aligned (not adversarial).

---

## What's NOT available anywhere on the canonical sites

- **Full-text sermon transcripts.** Sermons exist only as YouTube videos (1987–1990) and audio files. submission.ws has chapter-level summaries of 50 study sessions but not full STT transcripts. **Implication:** if the corpus needs sermon text, it requires a separate STT pass (Whisper or similar) in a later session.
- **A consolidated Khalifa-only PDF library.** Each book is per-chapter or per-fact PDFs; no single-file "Collected Works" download exists.
- **Khalifa's translation footnotes as a standalone export.** The footnotes appear inline in `/quran/noframes/` and `/quran/frames/` but aren't extracted separately. Worth checking whether they're already captured in `Verse.text` in the Neo4j graph (vs. needing a separate extraction pass).

---

## Counts for Phase 2 manifest

Provisional Khalifa-primary item count from this Phase 1 inventory:

- 38 Appendices (HTML)
- 1 Introduction to The Final Testament (HTML)
- 1 book: Quran, Hadith and Islam (89 chapter PDFs + 1 consolidated HTML)
- 1 book: Quran: Visual Presentation of the Miracle (52 Facts + ~5 front-matter PDFs = ~57 PDFs)
- 1 book: The Computer Speaks (31 Facts + ~4 front-matter PDFs = ~35 PDFs)
- ~62 Submitters Perspective issues 1985-02 → 1990-03 (each issue ~4 pages, so ~248 page-HTMLs)

**Conservative total: ~480 source items**. Phase 2 will enumerate exact URLs.
