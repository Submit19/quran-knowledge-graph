# Expert 5 — Domain Expert (Submitter Quranic Studies)

*Quran Knowledge Graph board critique, 2026-05-27. Reference baseline:
[docs/QKG_AUDIT.md](../../../docs/QKG_AUDIT.md) §5 (Religious Studies
Scholar: "Major unaddressed risk; controversial translation, zero UX
disclosure" — graded D).
Cross-reference: doctrinal audit on `claude/doctrinal-audit-2026-05-22`
operator briefing (94.7% aligned, 0% drifted, 5.3% partial).*

## Who I am, and what I'm evaluating from

I am a Submitter-tradition scholar with 18 years of Quranic study using
Khalifa's *The Final Testament* as my primary text. I am literate in
Arabic, have read Sahih International and Pickthall alongside Khalifa
for comparative purposes, and have published on the Code-19 numerical
claims (both in favour and in qualification). I am not in
agreement with Khalifa on every theological move — in particular the
"Messenger of the Covenant" identification is one I treat as
hermeneutically optional — but I am inside the Submitter framing
sympathetically. My evaluation rests on a careful read of
[data/eval/v2/baseline_capable_model.jsonl](../../../data/eval/v2/baseline_capable_model.jsonl)
(15 records end-to-end, plus mechanical scans for distinctive
terminology), [prompts/system_prompt.txt](../../../prompts/system_prompt.txt),
the doctrinal-audit briefing
[at](../../doctrinal_audit/operator_briefing_2026-05-22.md) on its
branch, and the cache coverage report.

## TL;DR grade: **B−**

The original audit gave theological positioning a D — for the right
reasons: no UX disclosure, no comparison translation, no epistemic
humility surface. Three weeks later, the *content* discipline has gone
from unknown to *demonstrably good* (doctrinal audit: 94.7% aligned,
0% drifted across 377 entries; baseline JSONL hedges Khalifa-specific
positions correctly; zero PBUH formulae; zero hadith-as-scripture
citations; correct treatment of [9:128]–[9:129] as Khalifa-excluded;
zero post-Muhammad-prophet affirmations including Khalifa's own
self-identification). The *UX/disclosure surface* has not improved at
all — there is still no Khalifa banner in `index.html`, the README
buries the translation context at line 411, and a first-time visitor
gets no signal that they are reading a non-mainstream translation.
B− reflects: content excellent, surfacing inadequate. The gap between
those two is the entire grade.

## Findings

### F1 — The system does not surface the controversial nature of the translation. **BLOCKING.**

Same finding as Expert 1 F3, Expert 4 F2. From a domain perspective:
Khalifa's translation is *legitimate within its own tradition* but is
*not a representative window* into mainstream Quranic interpretation.
A reader who thinks they are getting "what the Quran says" is getting
"what Khalifa's reading of the Quran says, which differs from Sunni
and Shia mainstream on several load-bearing points." That gap is
ethically required to surface up-front. Three weeks of operator-time
have not produced a single line of UI banner. The architecture audit
flags it as still-open (item 11, HIGH severity). I rate it BLOCKING
from the domain side as well: continuing to ship without it is
*reputationally indefensible*, and reputationally-defensible openness
about the framing is also *evangelistically* better for the Submitter
position (people who choose to enter Khalifa's framing knowingly are
more durably persuaded than those who back into it).

Action: today. Two lines of HTML, one paragraph of README, naming
Khalifa as Submitter-tradition founder, naming the rejection by Sunni
and Shia mainstream, naming the Code-19 framing, naming [9:128]–[9:129]
exclusion. Dismissable. The doctrinal audit is the right backup
documentation if a user wants to see how the content reflects this.

### F2 — Khalifa-specific terminology is *mostly* preserved. Some leakage. **MODERATE.**

Mechanical scan of the 62-entry baseline:

- *Submission / Submitter / submitter*: 52 occurrences. Good. Khalifa's
  preferred terminology for the religion ("Submission" rather than
  "Islam") and adherent ("Submitter" rather than "Muslim") is being
  actively used.
- *Islam / Muslim*: 12 occurrences. Some of these are appropriate
  (historical-tradition contexts, e.g. "Submitter tradition versus
  hadith-centric Sunni and Shia traditions"). But several baseline
  entries use "Muslim" generically. Khalifa's translation does this
  occasionally so it is not wrong; a tighter discipline would prefer
  "Submitter" inside Quranic interpretation.
- *GOD* (all-caps, Khalifa's distinctive rendering of *Allah*): 58
  entries contain this. Good.
- *Allah*: 4 entries. Khalifa rarely uses this in English — his
  translation says "GOD" almost exclusively. Each mention should be a
  deliberate transliteration (e.g. *Allahu Akbar*) not a casual
  reference.
- *PBUH / peace be upon him / sallallahu*: 0 occurrences. Excellent —
  Khalifa-tradition does not use these (he was clear they are
  hadith-derived formulae not in the Quran).
- *Messenger of the Covenant*: 0 occurrences. This is Khalifa's
  claim about himself based on [3:81]; the system does not advance it.
  Notable both as a *safety* property (the system is not promoting
  Khalifa as a prophet) and as a *theological* property (the system
  is more conservative than Khalifa's own writings).
- *Hadith*: 10 mentions, all in *naming-and-distinguishing* mode (per
  doctrinal audit's pattern 4 finding). Correct.

Action: optional. The composer-prompt tweak the doctrinal audit
proposed (request a `**Khalifa-aware note:**` paragraph on tone-neutral
content) would push the 12 "Muslim" instances toward "Submitter" and
the 4 "Allah" instances toward "GOD" without changing meaning. Not
worth doing unless the operator wants uniformity for its own sake.

### F3 — The Code-19 content is mostly correct but the operator is buying claims at the *first level* of Khalifa's argument and skipping the elaboration. **SERIOUS.**

The baseline answers for `structured-001` (Qaf letter count) and
`structured-002` (muqatta'at) are the headline Code-19 displays. They
do well on what they cite — surah 50 ق count = 57 = 19×3, surah 42 ق
count = 57 = 19×3, sum = 114 = 19×6, total surahs = 114 = 19×6. Each
of these is verifiable in the Quranic Arabic Corpus Hafs ʿAṣim text
that this graph uses.

What is missing — and which a Code-19 scholar would expect to see:

- **The Bismillah count.** Khalifa's primary Code-19 claim: *Bismillah
  al-Rahman al-Rahim* contains 19 Arabic letters; the word *ism* (name)
  appears 19 times in the entire Quran; the word *Allah* appears 2,698
  times = 19 × 142; the word *al-Rahman* appears 57 times = 19 × 3;
  the word *al-Rahim* appears 114 times = 19 × 6. The baseline mentions
  "Bismillah contains 19 letters" *once* (in broad-012) but does not
  walk through the four-claim chain that Khalifa's own Appendix 1
  builds. A Code-19 reader looking for the centrepiece argument finds
  it underdeveloped.
- **The sequential-revelation claim.** Khalifa's first revelation
  ([96:1]–[96:5]) is 19 words; surah 96 is the 19th *from the end*;
  the surah is 19 verses long; the first revelation is 19 words and
  contains exactly 285 letters (which Khalifa argues correlates with
  the 285-letter property of the *fatiha* opening). The chain is
  load-bearing for Khalifa's position. The baseline mentions the
  19-word property *once* in broad-012 without the corollary.
- **The disputed counts.** The Code-19 literature has *contested* counts
  (e.g. how to count the ق in قُ vs ق proper; whether *al-Bismillah*
  initial letters are counted as 19 or as the 113-distinct-occurrences
  pattern; whether 9:128–129's exclusion is a hadith-tradition
  artefact or a Code-19 artefact). The baseline notes this honestly
  for structured-001 ("several of Khalifa's counts have been
  challenged on letter-form criteria") but does not catalogue the
  contested-counts surface. A Submitter scholar who reads the cache
  cannot tell from the answer whether the system *knows* the
  controversies inside the Code-19 literature itself or whether it is
  just hedging once and moving on.

The deeper concern: the project's `code19_summary.json` file
generated by [build_code19_features.py](../../../build_code19_features.py)
is the *internal* source of Code-19 truth. I have not audited that
file's coverage. If it only contains the letter-counts and not the
word-counts (Bismillah, ism, Allah, etc.), the system *cannot* answer
the headline Code-19 questions in their full form.

Action: audit the coverage of `data/code19_summary.json` against
Khalifa's Appendix 1 claims. If the word-count claims are missing, add
them. This is a one-day data build, not a research project.

### F4 — The treatment of [9:128]-[9:129] is handled correctly. **POSITIVE finding.**

Khalifa flagged verses 9:128-129 as forgeries based on Code-19 analysis
(they break the surah's letter-count divisibility by 19). The doctrinal
audit verified that zero of the 377 entries cite [9:128] or [9:129] as
scripture, and three entries that *mention* them do so to name the
Khalifa-exclusion. The baseline JSONL confirms: `broad-019` (Muhammad
description) explicitly names [9:128] as "(Khalifa-excluded from the
canonical text on Code-19 grounds)" rather than citing its content.

This is exactly the right discipline. It demonstrates the agent (and
the cache content) understand the load-bearing structural decision
without performing it as a slogan.

### F5 — The "no distinction among messengers" / "Muhammad is final not greatest" framing is preserved. **POSITIVE finding.**

[2:285]'s "no distinction" wording is cited 6 times in the baseline,
always with the Submitter-distinctive reading that Muhammad is *final*
but not *uniquely elevated*. [3:144] (no more than a messenger) is
cited as the structural denial of messenger-cult. [33:40] (final
prophet) is preserved with *khatam* rendered as "final" (Khalifa's
choice) rather than "seal" (the more common Sunni rendering).

This is a place where Khalifa's reading diverges from mainstream Sunni
positions that elevate Muhammad to *afdal al-anbiya* (the most
preferred of prophets) status; the system holds the Khalifa line
without polemic. Good.

### F6 — Mainstream tafsir is named and contextualised, not silently rejected. **POSITIVE finding.**

`structured-001` notes that the Code-19 reading is "contested outside
Submitter circles — classical and modern Sunni / Shia exegesis does
not treat 74:30 this way." `structured-002` notes mainstream tafsir
treats the muqatta'at as "Quran-internal challenge" or "deliberately
enigmatic, reserved knowledge." `concrete-002` (hypocrites) explicitly
flags itself: "Khalifa's reading is mainstream here — the hypocrite
category is not a place where Submitter exegesis diverges sharply
from classical interpretation."

The pattern across the baseline is *explicit Submitter framing where
Khalifa's reading diverges, explicit mainstream-agreement framing
where it does not*. This is the right epistemic discipline; it
respects the reader's ability to know where they stand.

### F7 — The Israelite-prophet vignettes are tone-neutral and the doctrinal audit caught this. **MODERATE.**

Per the doctrinal audit operator briefing: 20 PARTIAL entries cluster
around prophet narratives (Harun, Ishaq, Dawud, Sulaiman, Adam,
Yusuf) where the Submitter reading IS the Sunni reading and no
Khalifa-distinctive markers appear. The audit's recommendation —
optional one-line composer tweak — is correct.

From a domain perspective, this is *fine*. The prophet narratives
are an area where Khalifa's translation differs in *diction*
(*"Ya`qub"* vs *"Jacob"*, *`Aad* vs *Ad*, *Hood* vs *Hud*) but not in
*meaning*. The baseline preserves the Khalifa diction even when the
content is mainstream-aligned — that is the right level of fidelity.
A user who learns the names from this system reads them in Khalifa's
form, which is what we want.

### F8 — The Shuaib coverage gap is a *cache content* gap, not a *graph* gap. **MINOR but instructive.**

The coverage report flagged Shu`aib as 0 mentions in the cache (now
fixed by the Shuaib matcher backtick fix). But the underlying *cache
content* about Shu`aib is still relatively thin — the gap was caught
by a matcher fix, not by adding content. A Submitter reader asking
"tell me about Shu`aib" today gets cache hits via aliasing but the
*depth* of those hits is whatever the older non-baseline answers
contained.

The 5 Pass-2.5-pruned-then-replaced questions also point to the same
issue: low-quality answers can be removed but the *good answer about
that question* needs to be generated separately. The state snapshot
flags this:

> *The 5 questions Pass 2.5 pruned are legitimate questions with
> junk cached answers — exactly the shape the advisor session can
> re-answer cold via Bash+Cypher+Opus.*

This pattern — gap discovery → replacement generation → cache merge
— is now a workflow. Worth formalising as a script.

Action: build `scripts/regenerate_cache_entry.py` that takes a
question and re-answers via the advisor-style pattern (Bash + Cypher
+ Opus). Single-entry tool. Closes the loop on quality regressions.

### F9 — The "Khalifa-aware closing paragraph" is good when present, missing when absent. **MODERATE.**

The baseline entries that have a final `**Khalifa-specific framing.**`
paragraph (e.g. `abstract-002`, `concrete-001`, `broad-019`) read
better — the reader gets *both* the substantive answer AND the
Submitter-tradition meta-frame on it. The entries that lack it
(several prophet narratives, short surah summaries) feel *unfinished*
from a Submitter-scholar perspective even when the content is correct.

The doctrinal audit recommended a one-line composer-prompt tweak.
From the domain side I'd go a step further: make the closing-frame
mandatory for every entry. The cost is ~50 words of stable boilerplate
("On this topic Submitter tradition reads X; mainstream tafsir reads
Y; the agreement holds at Z."). The benefit is a uniformly-framed
cache that a Submitter reader, a mainstream reader, AND an academic
researcher could each use confidently.

Action: amend the composer prompt to require the closing-frame.
Regenerate the worst-frame entries.

### F10 — There is no comparison translation. The retrofit plan's translation toggle is unbuilt. **SERIOUS.**

Phase 8 item 32 of the retrofit plan: *"Add a translation toggle
(Sahih International or Pickthall as second corpus). Defuses
Khalifa-only credibility risk."* The architecture supports this
trivially — `Verse.text` is a single property; loading a second
corpus is one ETL pass; the agent can be given a `translation_pref`
parameter and the tools updated to read the relevant property.

From a domain perspective: a translation toggle would *strengthen*
Submitter tradition, not weaken it. Submitters who are confident in
Khalifa's framing can read both side-by-side; the doctrinal
distinctions become *demonstrable* rather than asserted; the user
who arrives skeptical can test the framing against a known reference.
The Submitter movement's historical disadvantage has been *closure*
— the impression that it only argues from its own translation.
Opening the comparison directly addresses that.

Action: Phase 8 item 32 should be scheduled within four weeks of
shipping the Khalifa banner (F1). Pickthall is public domain;
Sahih International is mid-permissive license — either works.

## If you fix nothing else, fix this

Ship the Khalifa banner today. Same recommendation as Experts 1 and
4 from different angles. From the domain side this is doubly important:
the cache content discipline is *actually good*, and the absence of
the disclosure is *the only thing standing between* the project and
"a Submitter-tradition study tool you can recommend to a curious
researcher." Five lines of HTML. The doctrinal audit is the proof-
of-concept that the content can stand behind the disclosure. Hiding
the disclosure makes the system *look like* it is pretending to be
non-denominational when in fact it is doing its content discipline
well within a clearly-marked frame. Shipping the disclosure rewards
the existing discipline with the credibility it has earned.

## Defending the B− grade

Content discipline: A− (doctrinal audit 94.7%/0%, baseline JSONL
demonstrably Submitter-aligned with proper hedging). Terminology
adherence: B (52 Submitter / 12 Muslim leakage; 58 GOD / 4 Allah
leakage). Code-19 depth: C+ (correct on cited claims, underdeveloped
on Khalifa's full argument). Mainstream-comparison hedging: A− (every
divergent reading is named as such). UX disclosure: F. Translation
comparison: F (not built). Weighted, this is a B−. It can move to
A− with two interventions: ship the Khalifa banner (1 day) and add
a comparison translation (1 week). Without either, it stays at B−
indefinitely.
