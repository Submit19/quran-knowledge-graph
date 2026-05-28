# Khalifa Corpus Discovery — Phase 3: Sample Verification

**Date:** 2026-05-27
**Goal:** Fully fetch 3 representative items from the Phase 2 manifest and verify content / quality / extraction concerns.

## Sample 1 — Appendix 24, "Two False Verses Removed from the Quran"

**URL:** https://www.masjidtucson.org/quran/appendices/appendix24.html
**Format:** HTML
**Author byline (verbatim):** "Rashad Khalifa, PhD" — opening header reads "(from: Quran The Final Testament, by Rashad Khalifa, PhD.)"
**Word count:** ~12,000–13,000 (extensive — 70+ numbered sections)
**Khalifa-primary verdict:** ✅ **confirmed primary**

### Verbatim opening (first ~120 words)

> Appendix 24
> (from: Quran The Final Testament, by Rashad Khalifa, PhD.)
> Tampering with the Word of God
> A superhuman mathematical system pervades the Quran and serves to guard and authenticate every element in it. Nineteen years after the Prophet's death, some scribes injected two false verses at the end of Sura 9, the last sura revealed in Medina. The evidence presented in this Appendix incontrovertibly removes these human injections, restores the Quran to its pristine purity, and illustrates a major function of the Quran's mathematical code, namely, to protect the Quran from the slightest tampering. Thus, the code rejects ONLY the false injections 9:128-129.

### 9:128 / 9:129 references in the essay

**Yes — referenced extensively** (by number) throughout the essay. This is *the source document* for the project's rule that 9:128 and 9:129 are forged injections.

**Tension to surface to operator:**
- The binding hard rule (operator-set 2026-05-27) says the **runtime app must NEVER surface or reference 9:128 or 9:129 in any form** — not in brackets, not in prose, not as "the two excluded verses".
- Appendix 24 *itself* is Khalifa-primary and inarguably belongs in the corpus.
- The Appendix mentions these verse numbers ~dozens of times by design — it's the essay that makes the case for excluding them.

**Recommendation:** Ingest Appendix 24 as a corpus document with full text preserved. Apply the no-surface rule at the COMPOSER step (system prompt + post-generation regex scrub on output text). Do not pre-redact the source — the composer needs to know the essay exists to handle "why do Submitters exclude these verses?" queries without surfacing them.

### Extraction-quality notes

- Clean HTML, no Arabic-as-image issues.
- Contains internal cross-references to other appendices (e.g., "Appendix 1," "Appendix 23") — preserve as anchors for graph linking.
- Contains external citations to **non-Khalifa** scholarly works: "AL ITQAAN FEE 'ULUM AL QURAN by Jalaluddin Al-Suyuty" and "'ULUM AL-QURAN, by Ahmad von Denffer, Islamic Foundation, Leicester." These are *Khalifa's citations of others* — preserve verbatim as part of his text; the rule excludes those works as primary sources but Khalifa quoting them is still Khalifa-primary writing.

---

## Sample 2 — *Quran, Hadith and Islam* (consolidated HTML)

**URL:** https://www.masjidtucson.org/publications/books/qhi/qhi.html
**Format:** HTML consolidated (alternative to 89 per-chapter PDFs)
**Author byline (verbatim):** "by Rashad Khalifa, Ph.D. / Imam, Mosque of Tucson, Arizona, U.S.A." with personal signature "Rashad Khalifa / August 19, 1982"
**Word count:** ~18,000–20,000
**Khalifa-primary verdict:** ✅ **confirmed primary** (the book Khalifa wrote setting out his hadith-rejection thesis)

### Verbatim opening (Preface)

> After more than 12 years of computerized research of Quran, PHYSICAL EVIDENCE was discovered proving that Quran is indeed the infallible word of God.

(Preface continues that Hadith & Sunna "have nothing to do with Prophet Muhammad" and represent "flagrant disobedience of God and His final prophet.")

### Extraction-quality concerns

**Arabic text is inline GIF images, NOT Unicode** — file references like `hadith1.gif`, `hadith2.gif` appear throughout where Arabic phrases would naturally sit. The book itself even acknowledges: "the Arabic images would increase the size...Unfortunately, inclusion of the Arabic images would be...time to load."

**Implications for the scrape session:**
1. **HTML text extraction will silently drop the Arabic content.** No Unicode characters to grab.
2. **Two options for the scraper:**
   - (a) Skip Arabic; ingest English-only text. Acceptable if QHI's argument is structurally complete in English (it appears to be — the Arabic is mostly illustrative quotation).
   - (b) Fetch the GIFs alongside the HTML and OCR them in a later pass. Higher fidelity but adds a non-trivial OCR step.
3. **The per-chapter PDFs (`QURAN_Hadith_Islam_pg{1..89}.pdf`) probably have Arabic as embedded text** — worth sampling one PDF in the actual scrape session to confirm before deciding HTML-vs-PDF as the canonical extraction path.

**Recommendation for the scrape session:** Use the per-chapter PDFs as the canonical source (Arabic preserved as text), fall back to consolidated `qhi.html` if a PDF fetch fails. Skip GIFs; rely on PDF for Arabic.

---

## Sample 3 — Submitters Perspective issue #1, February 1985

**URL:** https://www.masjidtucson.org/publications/books/sp/1985/feb/page1.html
**Format:** HTML
**Editor:** "Rashad Khalifa, Ph.D." (per masthead)
**Khalifa-primary verdict:** ✅ **confirmed primary** (Khalifa-edited issue; lead piece is editorial)

### Lead article

**Title:** "WHO ARE WE?"
**Sub-section title also present:** "To Save The Muslim Ummah"

### Opening framing (paraphrased from fetch)

> Islam Today Is Like A Precious Jewel That Is Buried Under Piles Upon Piles Of man-made innovations.

The piece sets out the publication's mission: remove fourteen centuries of innovations, restore Islam's authentic Quran-only core.

### Findings worth flagging

1. **Publication originally called "Muslim Perspective"**, not "Submitters Perspective" — renamed at some point (likely as the movement transitioned terminology from "Muslim" to "Submitter"). The URL path `/sp/` is the *current* naming; some pre-1990 issues may have the masthead "Muslim Perspective" or "Monthly Bulletin of United Submitters International." Preserve the actual masthead title per-issue, not the URL slug.
2. **No explicit per-article bylines** on the inaugural issue. Khalifa-as-editor is the only attribution. **Implication:** the scrape session should treat all Khalifa-era SP article text as "Khalifa-edited, attribution unclear" unless a specific byline appears in-page. Article-level Khalifa-vs-contributor filtering is unreliable here; treat the corpus item as the issue, not the article.
3. The text is clean HTML, English-only (no Arabic-as-image issue in the sample).

### Generalization

A spot-check of the **January 1989** issue (Phase 1 sample) showed an explicit "Editor: Rashad Khalifa, Ph.D." byline on a substantive lead piece. So bylines exist in some issues. The scrape session should:
- Preserve any explicit byline metadata it finds in each page's HTML
- Default to attribution `"Editor: Rashad Khalifa, Ph.D. (issue editor)"` for un-bylined pieces in 1985-02 → 1990-03 issues
- Tag issues by mast-head title so renames are preserved

---

## Sample 4 (bonus) — Copyright gate text on `/publications/books/computer_speaks/`

I fetched the copyright-agreement page that gates *Visual Presentation* and *The Computer Speaks* book downloads.

### Verbatim gate text

> Except as permitted under the Copyright Act of 1976, this book may not be reproduced in whole or in part in any manner without written permission from the copyright owner.

That's the complete restriction text (per WebFetch summary). No additional "personal use only" or "non-commercial only" clauses.

### Implications

- **It's standard "all rights reserved" language**, not an explicit no-scraping clause and not an explicit reproduction permission. The 1976 Act explicitly carves out fair use (§107) — research, scholarship, non-commercial transformation.
- **A research-internal corpus** (used by the project's composer, not republished as text) plausibly falls under fair use given:
  - Educational / research purpose
  - Transformative use (composer generates new answers, doesn't reproduce the book)
  - The audience is Submitters who would buy the book if charged (no market harm)
  - Even if outputs *cite* the book, citation ≠ reproduction
- **The conservative path** is to email `info@masjidtucson.org`, identify the project as Submitter-aligned (the binding rule positions Khalifa as the Messenger of the Covenant — explicit alignment with the publisher's worldview), and request explicit permission to mirror for non-public research use. This costs ~1 email and provides clean cover.
- **The corpus-pragmatic path** is to start the scrape with the *un-gated* sources (38 Appendices + Introduction + SP issues + QHI HTML, which has no gate) and defer VP/CS until permission is obtained.

This is Open Question #1 for the operator.

---

## Summary verdict on extraction quality

| Source | Format | Encoding | Extraction reliability |
|---|---|---|---|
| Appendices | HTML | Clean Unicode | High |
| Introduction | HTML | Clean Unicode | High |
| SP issues (Khalifa era) | HTML | Clean Unicode | High |
| QHI (consolidated HTML) | HTML | Arabic as GIF images | Medium (English only) |
| QHI (per-chapter PDFs) | PDF | Likely embedded text | Medium-High (sample one in scrape session) |
| VP & CS books | PDF | Likely embedded text + heavy diagrams | Medium (text fine; diagrams lost) |

## Estimated effort for the actual scrape session

| Step | Effort |
|---|---|
| Fetch 38 Appendices + Introduction (39 HTML pages) | ~5 min |
| Fetch 64 SP issues × ~4 pages = 256 HTML pages | ~10 min |
| Fetch QHI: 92 PDFs + 1 consolidated HTML | ~10 min (PDF download faster than HTML rendering) |
| Fetch VP: 57 PDFs (if operator clears copyright gate) | ~10 min |
| Fetch CS: 36 PDFs (if operator clears copyright gate) | ~5 min |
| PDF text extraction (pypdf / pdfminer) | ~15 min |
| HTML → Markdown conversion | ~10 min |
| Verification pass + emit unified manifest with per-item provenance | ~15 min |
| **Total scrape-session estimate** | **~80 min** if all gates cleared; ~50 min if VP+CS deferred |
