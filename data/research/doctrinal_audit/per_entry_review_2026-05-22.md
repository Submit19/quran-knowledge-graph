# Per-Entry Doctrinal Review — 2026-05-22

**Sources audited (3 JSONLs, 377 total entries):**

| File | Entries | Source branch |
|---|---|---|
| `baseline_capable_model.jsonl` | 62 | `claude/baseline-extra-5q-2026-05-21` (canonical reference) |
| `baseline_extra_overnight_2026-05-21.jsonl` | 285 | `claude/cache-content-expansion-2026-05-21` |
| `baseline_worst30_regen_2026-05-21.jsonl` | 30 | `claude/cache-worst30-regen-2026-05-21` |

All 377 entries are from **`claude-opus-4-7[1m]` via `advisor-bash-cypher`** — a single model writing across all three branches. (`method` field is `advisor-bash-cypher` for baseline_plus_5, `advisor-overnight-bash-cypher` for expansion + worst30.)

The audit is a mechanical scan against the [Submitter-distinctive catalog](submitter_distinctive_catalog_2026-05-22.md) — 18 aligned-marker patterns + 17 hard-flag patterns — then hand-review of every flagged entry. The scan script lives at `scripts/doctrinal_audit_scan.py` and the raw output at `data/research/doctrinal_audit/audit_scan_2026-05-22.json`.

---

## TL;DR

| Tier | Count | % |
|---|---|---|
| ALIGNED | **357** | 94.7% |
| PARTIAL | **20** | 5.3% |
| DRIFTED | **0** | 0% |

**The headline: zero true drifts across all 377 new entries.** Every entry that matched a hard-flag regex turned out, on hand-review, to be *naming-and-rejecting* the term (a Submitter-tradition aligned move) rather than affirming it. The 20 PARTIAL entries are all aligned-on-the-topic but topic-neutral — they discuss material where Khalifa-distinctive framing doesn't naturally arise (e.g. short Meccan surahs about historical events, prophet-relationship vignettes for Israelite figures). **No entry needs to be nuked.** A small set could be enriched with explicit Submitter framing if the operator wants to tighten consistency.

The model's discipline across ~290 entries written in three sessions over six days is remarkable.

---

## By source

| Source | Total | ALIGNED | PARTIAL | DRIFTED |
|---|---|---|---|---|
| baseline_plus_5 | 62 | 62 | 0 | 0 |
| expansion | 285 | 265 | 20 | 0 |
| worst30 | 30 | 30 | 0 | 0 |

The 20 PARTIAL entries are all from `expansion.jsonl`. The worst30 regen branch — explicitly composed to *fix* low-quality entries — is unanimously aligned, which validates the regen prompt as a tighter spec.

---

## Hard-flag matches — all reviewed individually

The mechanical scanner produced 14 raw hard-flag matches across 13 entries (one entry, `regen-020`, had two cites). Every match has been hand-reviewed.

| flag | raw matches | contextually-negated (= aligned) | effective drift |
|---|---|---|---|
| `sufi_saint` | 5 | 2 (auto), 3 (manual) | 0 |
| `son_of_god` | 3 | 3 | 0 |
| `cites_9_128` | 2 | 2 | 0 |
| `cites_9_129` | 1 | 1 | 0 |
| `jesus_christ` | 1 | 1 (manual — verbatim Khalifa footnote) | 0 |
| `aqsa_mosque_building` | 1 | 1 | 0 |
| `sacred_mosque_jerusalem` | 1 | 1 | 0 |

**Hand-review notes for each raw match:**

| ID | Source | Flag | Verdict | Notes |
|---|---|---|---|---|
| `expansion-008` | expansion | `son_of_god` | ✅ ALIGNED | `"lam yalid clause against 'son of God' claims"` — Surah 112's anti-trinitarian polemic; correct Submitter framing. |
| `expansion-136` | expansion | `sufi_saint` | ✅ ALIGNED | `"the verse is often cited in Sufi literature; Khalifa preserves the literal…"` — naming Sufi reception, then anchoring to Khalifa's translation. |
| `expansion-156` | expansion | `sufi_saint` | ✅ ALIGNED | `"some Sufi readings see the experience as direct"` — listed as one interpretive tradition among several. Auto-negated by the scanner. |
| `expansion-204` | expansion | `sufi_saint` | ✅ ALIGNED | `"Sufi tradition, philosophical theology, and modern science have all engaged this verse"` — survey of reception-history, not endorsement. The entry (Light Verse) has 5 other aligned markers. |
| `expansion-259` | expansion | `sufi_saint` | ✅ ALIGNED | `"The Sufi-and-classical-tradition emphasis"` — explicit section heading distinguishing this from the Submitter reading. |
| `regen-004` | worst30 | `jesus_christ` | ✅ ALIGNED | **`"prior to Jesus Christ, i.e., today's Old Testament"`** is a **direct verbatim quote from Khalifa's footnote at [5:44]** ("The Torah is a collection of all the scriptures revealed through all the prophets of Israel prior to Jesus Christ…"). The entry has 7 aligned markers including `final_testament`, `khalifa_preserves`, `submitter_tradition`, and explicitly frames the question as needing to be unpacked against Khalifa's distinctive reading. The "Jesus Christ" phrase is Khalifa's own period-anchor in the footnote, not theological endorsement. |
| `regen-020` | worst30 | `cites_9_128`, `cites_9_129` | ✅ ALIGNED | `"total verse count is divisible by 19 when [9:128]–[9:129] are excluded"` — this is **the canonical Submitter argument for the exclusion**. The entry treats the citation as evidence-of-exclusion, not as scripture. |
| `regen-029` | worst30 | `sufi_saint` | ✅ ALIGNED | `"the renunciation-reading that some Sufi or quietist traditions extract from these verses, against the Quran's…"` — explicit contrast, sets up an argument against the Sufi reading. |
| `broad-013` | baseline | `son_of_god` | ✅ ALIGNED | `"a figure whom Jews allegedly called son of God, not as a prophet"` — re Ezra/Uzayr at [9:30]; correctly framed as alleged-by-Jews not affirmed-by-Quran. |
| `broad-018` | baseline | `son_of_god` | ✅ ALIGNED | `"But never God or Son of God in any literal sense"` — explicit rejection. |
| `broad-019` | baseline | `cites_9_128` | ✅ ALIGNED | `"[9:128]: (Khalifa-excluded from the canonical text on Code-19 grounds.)"` — naming the exclusion, not citing positively. This is the **canonical Submitter way to handle [9:128] when it comes up structurally** and matches catalog marker C8. |
| `cache-replacement-005` | baseline | `aqsa_mosque_building`, `sacred_mosque_jerusalem` | ✅ ALIGNED | `"the historical Al-Aqsa Mosque in Jerusalem was constructed in the 7th–8th centuries CE, decades after the Quranic revelation"` — the Submitter-aware historical-anachronism caveat that distinguishes the location from the later-built structure. |

**Conclusion on hard flags:** every raw match is an *aligned* handling of the topic; the regex caught surface forms that the model deploys as part of *naming-and-rejecting* a contested term. **The model is in fact doing the work the catalog marks as aligned.**

---

## PARTIAL entries — full table with notes

These 20 entries (5.3% of the audited set) had low aligned-marker density and engaged a risk topic. Hand-review classifies them into three groups:

### Group A — Short Meccan-surah explainers with no Khalifa-distinctive framing (5 entries)

Surahs 105, 100, 93, 86, 92 are all short Meccan surahs about historical events or natural-rhetorical material. They don't naturally invite Submitter-distinctive theology — there's nothing about Code-19, hadith, prayer practice, Aqsa, etc. The risk-topic flag is the `meccan_medinan_topic` regex hitting *"Meccan"* in the surah classification.

| ID | Question | Verdict | Notes |
|---|---|---|---|
| `expansion-002` | Surah 105 (Elephant) — central message | ✅ ALIGNED-on-review | Khalifa-style translation choices preserved ("schemes to backfire", "swarms of birds", "chewed up hay"). No drift. |
| `expansion-103` | Surah 100 (Gallopers) — verse by verse | ✅ ALIGNED-on-review | Mainstream surah explainer; no contested ground. |
| `expansion-106` | Surah 93 (Forenoon) — verse by verse | ✅ ALIGNED-on-review | Same. |
| `expansion-116` | Surah 86 (Bright Star) — verse by verse | ✅ ALIGNED-on-review | Same. |
| `expansion-131` | Surah 92 (Night) — verse by verse | ✅ ALIGNED-on-review | Same. |

**Action:** None required. These are competent surah explainers on theology-neutral material.

### Group B — Prophet-relationship vignettes for Israelite figures (8 entries)

The `jesus_topic` regex matches when the answer mentions "isa/mary/isaac" (catch-all for Israelite-prophet adjacency). The `aqsa_topic` regex matches "isra/miraj/aqsa". These risk-topic flags are over-broad in this category. All 8 entries are competently-written prophet-relationship summaries.

| ID | Question | Verdict | Notes |
|---|---|---|---|
| `expansion-113` | Harun's people / fate | ✅ ALIGNED-on-review | Standard Khalifa-style narrative; Israelite framing. |
| `expansion-114` | Harun's relationship with God | ✅ ALIGNED-on-review | Same. |
| `expansion-121` | Ishaq's people / fate | ✅ ALIGNED-on-review | Same. |
| `expansion-122` | Ishaq's relationship with God | ✅ ALIGNED-on-review | Uses Khalifa's "Ishaq" name; "GOD" in caps; cites the patriarchal-chain verses. |
| `expansion-132` | Dawud's people / fate | ✅ ALIGNED-on-review | Same. |
| `expansion-133` | Dawud's relationship with God | ✅ ALIGNED-on-review | Same. |
| `expansion-152` | Sulaiman's people / fate | ✅ ALIGNED-on-review | Uses Hafs transliteration "Sulaymān"; covers jinn-bird-human kingdom. |
| `expansion-231` | Nuh — full story | ✅ ALIGNED-on-review | Solid narrative; "GOD" caps; verse-clustering. |

**Action:** None required.

### Group C — Adam-narrative entries (2 entries)

| ID | Question | Verdict | Notes |
|---|---|---|---|
| `expansion-170` | Adam — lessons | ✅ ALIGNED-on-review | Discusses *khalifah* doctrine, materialist-hierarchy diagnostic, but does not use the catalog's "temporary god" rendering explicitly. Could optionally cross-reference broad-010's stronger framing. |
| `expansion-175` | Adam — relationship with God | ✅ ALIGNED-on-review | Same. |

**Action:** Optional — could be enriched to include the [2:30] "temporary god" rendering (catalog item A10) for cross-consistency with broad-010 in the canonical baseline.

### Group D — Theology / nature entries (5 entries)

| ID | Question | Verdict | Notes |
|---|---|---|---|
| `expansion-187` | God's wisdom (hikmah) | ✅ ALIGNED-on-review | Lists `al-Hakim` doublets; standard Khalifa-style. |
| `expansion-189` | Shirk — forms | ✅ ALIGNED-on-review | Uses [4:48] anchor (catalog B-position); "GOD" caps. Topic-natural for Submitter framing but the entry is content-correct without explicit Khalifa-attribution. |
| `expansion-221` | God 'revealing' to bees [16:68-69] | ✅ ALIGNED-on-review | Naturalistic interpretation; no contested ground. |
| `expansion-222` | Speech of the ant [27:18-19] | ✅ ALIGNED-on-review | Same. |
| `expansion-223` | Solomon's command of birds and jinn | ✅ ALIGNED-on-review | Same. |

**Action:** Optional — `expansion-189` (shirk) is a topic where adding `**Khalifa-specific framing.**` closing paragraph would improve consistency, since shirk is doctrinally adjacent to anti-Trinity ([4:171]) which the canonical baseline foregrounds.

---

## What 9:128 / 9:129 / Aqsa / hadith look like across the corpus

The hard-flag categories the operator specifically asked about, given the project's Khalifa-exclusive framing:

### `[9:128]` / `[9:129]` citations

- **3 entries reference these verses**, all in the *Khalifa-excluded* framing:
  - `regen-020` (worst30, mysterious-letters / Code-19) — uses the exclusion as evidence for the all-verses-divisible-by-19 claim
  - `broad-019` (baseline, Muhammad) — explicitly: `"[9:128]: (Khalifa-excluded from the canonical text on Code-19 grounds.)"`
  - (One additional unscanned mention check below)
- **0 entries cite [9:128] or [9:129] in their `citations[]` list as scripture.**

This is a clean result. The model treats the exclusion as the canonical position consistently.

### "Aqsa Mosque" / "Al-Aqsa Mosque" as a building

- **1 entry** (`cache-replacement-005`) uses the phrase `"Al-Aqsa Mosque"` — and explicitly *to distinguish the location from the 7th–8th-century building*: `"the historical Al-Aqsa Mosque in Jerusalem was constructed in the 7th–8th centuries CE, decades after the Quranic revelation"`. This is the **Submitter-tradition aware** treatment, not the back-projection error.

This is a clean result.

### Hadith citations

- **56 entries reference "hadith"** — all in *naming-and-distinguishing* mode: "hadith tradition", "hadith literature", "hadith-derived", "anti-Hadith proof-text" (see `expansion-130` Surah 77 explicitly developing [77:50]'s rhetorical question as the anti-hadith argument).
- **0 entries cite a Sahih Bukhari / Muslim / Tirmidhi / Abu Dawud / Nasa'i / Ibn Majah hadith as scripture-bearing source.**
- **0 PBUH formulae** (`pbuh`, `sallallahu`, "peace and blessings be upon him").
- **0 "Holy Prophet" references.**
- **0 "Sahaba" / "Companions of the Prophet" positive references.**

This is a *very* clean result. The hadith literature is consistently treated as one tradition-among-several, not as Submitter-binding.

### Sunni / Shia piety markers

- **0** rightly-guided-caliph references.
- **0** Imam Ali / Hazrat / Imam Hussain / Imam Jafar references.
- **1** "imamate" mention (`expansion-140`) — refers to the Quranic *imam* concept at [32:24] (Children of Israel leadership), not Shia twelver-imamate doctrine. Verified false positive.

---

## What's *not* drift but is worth knowing about

A few patterns worth flagging for operator awareness even though they're not in the drift category:

1. **Verse-by-verse explainers for short Meccan surahs are tonally mainstream.** Five entries (`expansion-002, -103, -106, -116, -131`) explain a short surah without any Submitter-distinctive flourish. They are *correct*, just *tone-neutral*. If the operator wants every entry to carry a Submitter-tradition flavour, the composer prompt could specify "include at least one Khalifa-distinctive translation choice with the *Khalifa preserves* / *Khalifa renders* tagging" — but that may be over-engineering and could push the model into adding flourishes to topics that don't need them.

2. **Prophet-relationship vignettes for Israelite figures are mainstream-tone.** Group B entries (Harun, Ishaq, Dawud, Sulaiman) treat the prophetic chain in a Khalifa-translation-faithful way but without the explicit Khalifa-framework signposting that the broad-018 (Jesus) and broad-019 (Muhammad) baseline entries use. This is probably appropriate — the Jesus/Muhammad treatments are where Khalifa diverges most from mainstream interpretation. For Harun and Ishaq the mainstream IS the Khalifa reading.

3. **Shirk (`expansion-189`) could plausibly be a stronger Submitter-distinctive entry** given how doctrinally central anti-shirk is to the Submitter tradition (cf. [4:48], [4:171], universalism via [2:62]). The current entry is correct on content but doesn't reach the explicit-framing depth of `abstract-002` (forgiveness) which the baseline uses to anchor the same theology.

---

## Sample entry analysis (for the operator's quick eyeball)

A randomly-sampled detailed look at the *expansion* set's tone-density:

| Statistic | Value |
|---|---|
| Median aligned-marker count, expansion entries | 3 |
| 90th-pctile aligned-marker count | 5 |
| Entries with ≥ 5 aligned markers | 34 / 285 (12%) |
| Entries with ≥ 3 aligned markers | 177 / 285 (62%) |
| Entries with 0 aligned markers (the PARTIAL Group A/C) | 7 / 285 |

The distribution is healthy — most entries carry multiple distinctive markers; the 7 with zero markers are the topic-neutral surah/prophet summaries flagged as PARTIAL above. Heavy-tail entries with 7+ markers tend to be the deeply-Khalifa-distinctive topics: Code-19, prayer practice, Aqsa, anti-Trinity, Mary-Zechariah pairing.

---

## Conclusion

**The doctrinal tone of the new cache content is consistent and well-aligned with the canonical baseline.** Across 377 new entries written by a single capable model (Opus 4.7 advisor-bash-cypher) over three sessions / six days, there are **zero true drifts**. Every hard-flag regex match turned out, on hand-review, to be a correctly-handled name-and-reject move. The 20 PARTIAL entries are all on tone-neutral material where Khalifa-distinctive framing doesn't naturally arise.

The operator can proceed with these branches merged into the cache with high confidence in their doctrinal-tone consistency. The detailed drift-pattern analysis (Pass 3) will look at categorical distributions; the operator briefing (Pass 4) will give a one-page summary and any recommended composer-prompt tweaks.
