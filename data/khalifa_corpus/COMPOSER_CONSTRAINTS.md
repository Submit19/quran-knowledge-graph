# Composer Constraints — Corpus vs Output

This corpus is **source material**, not user-facing output. The Khalifa-only
source rule (`memory/feedback_khalifa_only_sources.md`) draws a sharp line
between what the corpus *contains* and what the composer is allowed to *surface*.
Anyone wiring this corpus into the composition pipeline must hold both halves.

## The two-source rule (what the composer may draw on)

The composer may ground answers in exactly two sources, and nothing else:

1. **The Quran** — verse text (Khalifa's English translation + Arabic Hafs),
   from the Neo4j graph.
2. **Rashad Khalifa's own primary writings** — this corpus: his Introduction,
   38 Appendices, *Quran, Hadith and Islam*, and the Khalifa-era *Submitters
   Perspective* issues.

No hadith, no classical tafsir, no jurisprudence, no later Submitter teachers,
no model training-knowledge fill. The composer should be able to cite
"Khalifa, *The Final Testament*, Appendix 24" the same way it cites `[9:40]`.

## The 9:128 / 9:129 no-surface rule (where the constraint binds)

Khalifa flagged 9:128–129 as forged injections. The rule:

> The runtime app must NEVER surface or reference 9:128 or 9:129 in any form —
> not in brackets, not in prose, not even as "the two excluded verses".

**This binds the composer's *output*, not the corpus.** The constraint moves
*down* the pipeline; censoring the source would be the opposite of
Khalifa-strict, because Appendix 24 *is* Khalifa's own essay making the case
for excluding those verses.

| Layer | 9:128/9:129 references? |
|---|---|
| **Corpus** (this directory — Khalifa-primary, faithfully preserved) | **Allowed.** Appendix 24, several SP issues, etc. discuss them by number. Flagged via `flagged_9_128_129: true` in frontmatter (18 files), never stripped. |
| **Composer prompt** (corpus chunks fed to the model) | Allowed — the composer needs to *understand* Khalifa's argument to answer "why do Submitters reject these verses?" |
| **Composer output** (what the model writes) | **Forbidden.** System-prompt instruction + a post-generation scrub on output text. |
| **Cache** (composed answers stored) | **Forbidden.** Zero surfaced references. |
| **App output** (what users see) | **Forbidden.** Zero surfaced references. |

### Practical implications for the wiring session

- **Do not pre-redact this corpus.** The `flagged_9_128_129` frontmatter field
  is a *signal*, not a delete instruction. Use it to route flagged chunks
  through extra output-scrubbing, not to exclude them from retrieval.
- **Enforce no-surface at the composer's output**, via (a) an explicit
  system-prompt instruction, and (b) a post-generation regex scrub
  (the scraper uses `9\s*[:.]\s*12[89]` to detect; the composer's scrub should
  be at least as broad and also catch prose forms like "verse 128 of sura 9").
- **Attribution caveat for SP issues.** Khalifa edited every Khalifa-era SP
  issue, but shorter items within an issue may be other contributors. Each SP
  file's frontmatter carries a `byline_note`; the corpus is Khalifa-primary at
  the *issue* level, not guaranteed at the *paragraph* level. If the composer
  ever attributes a specific SP sentence to Khalifa verbatim, prefer lead
  articles over short notices.
