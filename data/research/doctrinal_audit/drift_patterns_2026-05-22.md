# Drift Patterns Analysis — 2026-05-22

Systematic patterns from the per-entry audit ([detail](per_entry_review_2026-05-22.md)). 377 entries, 20 PARTIAL, 0 DRIFTED.

The headline result (zero true drift) leaves the *patterns* discussion narrow: there are no drift clusters because there is no drift. The interesting analysis lies in **where the PARTIAL flags concentrated** — categorically, temporally, and topically. Those concentrations point at where the composer prompt could be tightened if the operator wants tighter consistency without sacrificing the model's tone-neutrality on neutral material.

---

## 1. Drift by category (where do PARTIALs concentrate?)

| Category | Total | ALIGNED | PARTIAL | PARTIAL % |
|---|---|---|---|---|
| `prophets` | 73 | 63 | 10 | **13.7%** |
| `theological` | 48 | 43 | 5 | 10.4% |
| `surah_themes` | 110 | 105 | 5 | 4.5% |
| `ethical` | 48 | 48 | 0 | **0%** |
| `legal_ritual` | 6 | 6 | 0 | **0%** |

**The `prophets` category drifts the most by a wide margin.** Of the 10 prophet-category PARTIALs, 8 are *prophet-relationship vignettes* for Israelite figures (Harun, Ishaq, Dawud, Sulaiman). For these figures the *mainstream-Sunni reading IS the Khalifa reading* — the Quran's portrait of Aaron / Isaac / David / Solomon doesn't naturally invite Khalifa-distinctive caveats. The model defaults to tone-neutral content, which the scanner reads as "low marker density".

The remaining 2 prophet-category PARTIALs are the Adam-narrative entries (`expansion-170`, `-175`) which discuss the *khalifah* doctrine in mainstream-Islamic terms without invoking Khalifa's "temporary god" rendering ([2:30], catalog A10). This is the one place in the prophet-category PARTIALs where a Khalifa-distinctive cross-reference is plausibly missing.

**The `ethical` and `legal_ritual` categories are perfectly aligned.** These are topics where Submitter tradition diverges most sharply (Salat from Quran-only, Zakat as obligatory, etc.) and the composer instinctively reaches for the catalog markers.

---

## 2. Drift by time window (was there a "bad session"?)

| Hour bucket | Total | ALIGNED | PARTIAL | PARTIAL % |
|---|---|---|---|---|
| 2026-05-21T12 | 75 | 74 | 1 | 1.3% |
| 2026-05-21T13 | 35 | 33 | 2 | 5.7% |
| 2026-05-22T00 | 30 | 30 | 0 | 0% |
| **2026-05-24T12** | **25** | **17** | **8** | **32.0%** |
| 2026-05-24T13 | 70 | 65 | 5 | 7.1% |
| 2026-05-24T14 | 5 | 5 | 0 | 0% |
| 2026-05-26T11 | 45 | 41 | 4 | 8.9% |
| 2026-05-26T12 | 30 | 30 | 0 | 0% |

**The 2026-05-24T12 window has 32% PARTIAL rate** — 8 of 25 entries flagged. This is by far the highest drift-rate window. All 8 are the prophet-relationship vignettes (Harun, Ishaq, Dawud) and short surah explainers (Surah 86, 92). Looking at the entry IDs (113, 114, 116, 121, 122, 131, 132, 133), this is a **batch session focused on prophets-of-Israel and short Meccan surahs** that the composer powered through with a tone-neutral approach.

The next-highest is 2026-05-26T11 at 8.9% — the second prophets-vignette session (Sulaiman, Nuh, plus theological topics on bees/ants/Solomon's birds). Same pattern.

**The first session (05-21T12, 75 entries) had only 1.3% PARTIAL** — strong evidence that the composer was setting expectations at the higher Submitter-distinctive density there and naturally relaxed for later batches that happened to be on tone-neutral topics.

This is **not concerning drift** but rather *attention-budget allocation*: the composer spent the explicit-framing energy where it mattered (Code-19, Aqsa, Jesus, Muhammad, Salat, shirk-as-doctrine) and ran in tone-neutral mode for prophet-vignettes and short surahs.

**Insight for the composer prompt:** the model is implicitly choosing when to deploy explicit Submitter framing. If the operator wants more uniform marker density, the composer prompt could require an explicit `**Khalifa-specific framing**` closing paragraph for every entry. The trade-off: it may force performative-Submitter framing onto topics that don't need it (e.g. Surah 105 The Elephant).

---

## 3. Citation patterns (where do verses concentrate?)

**Total citations across 377 entries: 5,400 occurrences of 2,737 distinct verses.** That's ~14.3 citations per entry — comfortably above the baseline asserts' minimum-citations threshold and consistent with the operator's "evidence over volume" preference.

**Top 15 most-cited verses:**

| Rank | Verse | n | Significance |
|---|---|---|---|
| 1 | **[74:30]** | 14 | *"Over it is nineteen"* — Code-19 anchor |
| 2 | **[39:53]** | 12 | *"never despair of GOD's mercy"* — universal-mercy verse |
| 3 | [21:85] | 11 | Job's patience (the *Ayyub* citation cluster) |
| 4 | [2:177] | 11 | Righteousness-definition verse |
| 5 | [4:163] | 11 | Patriarchal-chain inspiration |
| 6 | [1:1] | 10 | Al-Fatihah opening |
| 7 | [2:125] | 10 | Abraham at the shrine |
| 8 | [38:48] | 10 | Prophets-as-righteous |
| 9 | [27:15] | 10 | David-Solomon endowment |
| 10 | [34:13] | 10 | Solomon's craft-workers |
| 11 | [2:1] | 10 | Alif-Lam-Mim — muqatta'at |
| 12 | [112:1] | 9 | *"Say: He is the One and Only God"* |
| 13 | [96:1] | 9 | Iqra' — first revelation |
| 14 | [2:127] | 9 | Abraham raises the foundations |
| 15 | [2:30] | 9 | *"placing a representative … on Earth"* |

The distribution is dominated by **structurally-canonical Quranic anchors** — Code-19 [74:30], universal-mercy [39:53], anti-Trinity [112:1], muqatta'at [2:1], khalifah [2:30]. These are the verses an aligned Submitter-tradition reading would naturally reach for. **The citation profile alone confirms the corpus is doctrinally on-topic.**

**Critical safety check — [9:128] and [9:129]:**

| Verse | Citations across 377 entries |
|---|---|
| [9:128] | **0** |
| [9:129] | **0** |

**Zero citations across the entire 377-entry new content.** This is the cleanest possible result on the Khalifa-exclusion constraint. The 3 entries that *mention* these verses (`broad-019`, `regen-020`, plus citations sample from baseline) all reference the *exclusion* — naming it, not citing positively.

---

## 4. Risk-topic engagement frequency

How often does the corpus engage doctrinally-loaded topics?

| Topic | Entries engaging |
|---|---|
| `meccan_medinan_topic` | 149 |
| `jesus_topic` (Jesus / Mary / Isa / Maryam adjacency) | 83 |
| `salat_topic` (Salat / Contact Prayer / five-times) | 70 |
| `hadith_topic` (mentions hadith / sunnah / sira) | 57 |
| `aqsa_topic` (Aqsa / night journey / isra / miraj) | 52 |
| `code19_topic` (Code-19 / nineteen / 74:30) | 43 |
| `trinity_topic` | small |

The corpus engages all the high-doctrinal-load topics extensively. **57 entries mention "hadith"** — every one of them in *naming-and-distinguishing* mode (per Pass 2). The corpus does not duck the contested ground; it engages it consistently.

---

## 5. Marker density distribution

| Aligned markers | Entries | Visual |
|---|---|---|
| 0 | 7 | ▆ |
| 1 | 40 | ████████████████████ |
| 2 | 63 | ███████████████████████████████ |
| 3 | **95** | ███████████████████████████████████████████████ |
| 4 | 62 | ███████████████████████████████ |
| 5 | 47 | ███████████████████████ |
| 6 | 24 | ████████████ |
| 7 | 22 | ███████████ |
| 8 | 6 | ███ |
| 9 | 9 | ████ |
| 10+ | 2 | █ |

Mode: 3 markers. Median: 3 markers. The distribution is roughly normal around 3, with a fat right tail. **The heavy-marker entries (7+) are clustered on the topics catalog Section E predicts** — Code-19, Jesus, Muhammad, prayer, Aqsa, anti-Trinity.

---

## 6. Most-used aligned markers (top 15 across 377 entries)

| Marker | Hits | What it indicates |
|---|---|---|
| `god_caps_in_quote` | 280 | Khalifa's typographic convention preserved in quoted verses |
| `submitter_word` | 245 | "Submitter" / "submitters" — the core community-noun |
| `khalifa_preserves` | 172 | The verb-phrase for translation choices |
| `translation_word` | 155 | "Khalifa's translation" |
| `khalifa_framework` | 129 | Naming Khalifa's exegetical framework |
| `hedging_classical` | 79 | "classical tafsir / mainstream Sunni / contested outside" caveats |
| `contact_prayer` | 62 | "Contact Prayer (Salat)" |
| `code_19` | 43 | Code-19 / nineteen / mathematical miracle references |
| `submitter_tradition` | 42 | "Submitter tradition / Khalifa-specific" tagging |
| `most_gracious` | 37 | The *Ar-Rahman* rendering |
| `obligatory_charity` | 35 | "obligatory charity (Zakat)" |
| `hadith_caveat` | 29 | "hadith-derived / anti-Hadith" caveats |
| `graph_count` | 20 | Project-distinctive verse-count anchoring |
| `quran_alone` | 14 | Submitter-tradition Quran-alone source claim |
| `egyptian_standard` | 7 | Meccan/Medinan classification provenance |

**Insight:** the lower-frequency markers (`temporary_god` at 4, `messenger_of_covenant` at 5, `kun_fa_yakun` at 4, `messenger_no_distinction` at 4) are the *highest-distinctive* Submitter moves. They concentrate in the canonical baseline (broad-018, broad-010, etc.) and are sparsely deployed in the expansion set. This is fine — they should be sparse, used where they actually apply.

---

## 7. The three patterns to summarize for the operator

1. **The "tone-neutral surah/prophet vignette" pattern.** When the composer batched short Meccan surahs (105, 100, 93, 86, 92) and Israelite-prophet vignettes (Harun, Ishaq, Dawud, Sulaiman), it ran in low-marker mode. Defensible because the mainstream IS the Khalifa reading on this material, but the operator may want every entry to carry at least one Khalifa-distinctive translation flourish for uniform tone.

2. **The "2026-05-24T12 batch" effect.** A single session-hour produced 8/20 of the PARTIAL entries — all prophets-of-Israel or short Meccan surahs. This is a *batching* artifact, not a *quality* artifact: the composer's attention-budget naturally went broader-than-deep when running through a long backlog of structurally-similar entries. Pre-batching by topic-density could mitigate this if it matters to the operator.

3. **The "shirk and hikmah" pattern.** Two theological entries — `expansion-189` (shirk) and `expansion-187` (hikmah) — sit in a category where Khalifa-distinctive framing is highly natural (anti-Trinity, anti-shirk universalism) but the entry doesn't reach for it. These two are the most-improvable entries: they're correct but not as deep-Khalifa as the canonical-baseline `abstract-002` (forgiveness) which they structurally parallel.

---

## 8. What would tighten consistency further (composer-prompt suggestions for Pass 4)

The Pass 4 briefing will distill these into actionable recommendations. The candidate moves:

- **Require closing `**Khalifa-specific framing**` paragraph** on every entry. Risk: forces performative-Submitter framing onto topic-neutral material.
- **Bias toward the catalog's heavy markers** (`temporary_god`, `kun_fa_yakun`, `messenger_of_covenant`) where they apply. Light-touch suggestion in the prompt.
- **Pre-batch by topic-density** so the composer's attention is reset between high-Khalifa-divergence and low-divergence topics. Probably overkill for the volume.
- **No change.** The corpus is fine as-is; the PARTIAL entries are correctly tone-neutral on neutral topics.

The Pass 4 briefing recommends **the no-change option** with optional enrichment of `expansion-189` (shirk) and a small composer-prompt tweak — see operator_briefing_2026-05-22.md.
