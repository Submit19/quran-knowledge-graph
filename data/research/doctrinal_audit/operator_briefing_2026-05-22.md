# Operator Briefing — Doctrinal-Tone Audit (2026-05-22)

**Audit scope:** 377 cache entries added 2026-05-21 → 2026-05-26 across 3 unmerged branches (`cache-content-expansion-2026-05-21`, `cache-worst30-regen-2026-05-21`, `baseline-extra-5q-2026-05-21`). All written by `claude-opus-4-7[1m]` via `advisor-bash-cypher`.

**Audit method:** mechanical scan against a [57-item Submitter-distinctive catalog](submitter_distinctive_catalog_2026-05-22.md) + hand-review of every flagged entry. Read-only. No content changes. Pytest 208+2 throughout.

---

## Headline

| | Count | % |
|---|---|---|
| ALIGNED | 357 | **94.7%** |
| PARTIAL | 20 | 5.3% |
| DRIFTED | **0** | **0%** |

**No entry needs to be nuked. No entry contradicts a Khalifa-distinctive position. The composer was disciplined throughout.**

The 20 PARTIAL entries are all tone-neutral surah/prophet vignettes (Surah 105, Harun, Ishaq, Dawud, etc.) where the mainstream-Sunni reading IS the Khalifa reading. They are correct, just not flagged with Khalifa-distinctive markers.

**Critical safety result:** **zero citations of [9:128] or [9:129]** as scripture across all 377 entries. The 3 entries that *mention* these verses (`broad-019`, `regen-020`, plus one baseline reference) all do so to name the Khalifa-exclusion — the canonical aligned move.

---

## Top 10 entries flagged for operator review

All 20 PARTIAL entries are correct content; none need *rewriting* in the strict sense. If the operator wants the most-improvable handful (rank-ordered by how much they'd benefit from explicit Submitter framing), this is the list:

| # | ID | Category | Why review | Recommended action |
|---|---|---|---|---|
| 1 | `expansion-189` | theological | Shirk is doctrinally adjacent to anti-Trinity ([4:171]); could match canonical `abstract-002` depth | Enrich with `**Khalifa-specific framing**` closing paragraph that ties shirk to universalism via [2:62] |
| 2 | `expansion-170` | prophets (Adam) | Discusses *khalifah* doctrine without invoking the "temporary god" rendering | Optional: cross-reference broad-010's stronger framing |
| 3 | `expansion-187` | theological (hikmah) | Topic-natural for Submitter framing but no explicit closing paragraph | Optional: add the *hikmah-and-kitab* pairing distinctively |
| 4 | `expansion-175` | prophets (Adam) | Same as #2 — Adam relationship with God | Optional cross-reference to broad-010 |
| 5 | `expansion-122` | prophets (Ishaq) | Correct content; no Khalifa-specific marker | Leave as-is unless uniformity is wanted |
| 6 | `expansion-114` | prophets (Harun) | Same | Leave as-is |
| 7 | `expansion-133` | prophets (Dawud) | Same | Leave as-is |
| 8 | `expansion-231` | prophets (Nuh) | Correct narrative; no closing Khalifa-framing paragraph | Optional |
| 9 | `expansion-002` | surah_themes (105) | Short Meccan surah, tone-neutral | Leave as-is |
| 10 | `expansion-152` | prophets (Sulaiman) | Correct content; no specific marker | Leave as-is |

**Net recommendation:** rewrite only #1 (`expansion-189` shirk). Everything else is either acceptable as-is or marginal-improvement territory.

---

## Top 5 drift patterns the operator should know about

1. **Tone-neutral material clusters in two categories.** `prophets` (13.7% PARTIAL) and `theological` (10.4% PARTIAL) carry the PARTIAL load. Within `prophets`, the Israelite-figure vignettes (Harun, Ishaq, Dawud, Sulaiman) and the Adam-narrative are the source. These are topics where mainstream Sunni reading and Khalifa reading converge.

2. **The 2026-05-24T12 hour is the highest-PARTIAL window** (32% — 8/25 entries). This was a batched session on prophets-of-Israel and short Meccan surahs. The composer ran broader-than-deep — defensible attention-budget allocation, not quality drift. Pre-batching by topic-density could mitigate this.

3. **Citation profile is doctrinally on-point.** Most-cited verse: [74:30] (Code-19 anchor, 14 hits). Top-10 includes [39:53] universal-mercy, [112:1] anti-Trinity opening, [2:30] khalifah, [2:127] Abraham at the shrine, [21:85] Job. **The composer is reaching for the right verses without prompting.**

4. **Hadith handling is consistent.** 56 entries mention "hadith" — all in *naming-and-distinguishing* mode (e.g. `expansion-130` Surah 77 develops [77:50] as the *anti-Hadith proof-text*). Zero entries cite Sahih Bukhari / Muslim / Tirmidhi / Abu Dawud / Nasa'i / Ibn Majah as Submitter-binding. Zero PBUH formulae. Zero "Holy Prophet". Zero Caliph-positive references.

5. **The "name-and-reject" pattern is the model's default for contested terms.** Every raw hard-flag regex hit (Son-of-God, Aqsa-Mosque, Jesus Christ, 9:128) turned out, on review, to be the model *naming the term to reject or contextualize it*. This is exactly the catalog-aligned C8 / D-section move. The model has internalized the discipline.

---

## Recommended composer-prompt tweak (one line)

The composer prompt currently produces high-quality output 94.7% of the time. The only systematic gap is on tone-neutral surah/prophet vignettes. **One light-touch addition** would close most of it:

> *"Even when the topic is tone-neutral (e.g. short Meccan surah, Israelite-prophet vignette), include at least one Khalifa-distinctive translation choice with explicit `Khalifa preserves` / `Khalifa renders` tagging. If no Khalifa-distinctive reading exists for the verses cited, conclude with a one-sentence `**Khalifa-aware note:**` paragraph stating that the Submitter reading on this material is mainstream."*

This is **optional** — the corpus is fine without it. But it would push the 20 PARTIALs into clean ALIGNED territory and eliminate the "marker density falls off on tone-neutral batches" pattern.

**Anti-recommendation:** do NOT mandate `**Khalifa-specific framing**` closing paragraphs on every entry. That would force performative Submitter-flag content onto topics that don't need it (the Elephant, the She-Camel, etc.) and degrade the model's tonal judgment.

---

## Three open questions for the operator

1. **Should `expansion-189` (shirk) be regenerated?** It's the single most-improvable entry — content is correct but framing depth doesn't match the canonical baseline's `abstract-002` (forgiveness). Cost: a few minutes of advisor-bash-cypher. Benefit: tighter cache-consistency on a doctrinally-central topic.

2. **Should the composer prompt get the one-line tweak above?** Trade-off: tighter uniformity vs. risk of performative-Submitter creep. The current 94.7% alignment may be the sweet spot.

3. **Is the audit method itself worth reproducing?** The 57-item catalog + regex scanner is mechanical and fast (sub-minute on 377 entries). It could become a pre-merge gate for future cache-content branches — every new cache-content branch runs through `scripts/doctrinal_audit_scan.py` and surfaces any DRIFTED entries before merge. The hand-review step is necessary (regex catches false-positives), but the mechanical pass dramatically narrows the human-review surface from "read every entry" to "review N hard-flag matches".

---

## Files produced this session

| File | Lines | Purpose |
|---|---|---|
| `data/research/doctrinal_audit/submitter_distinctive_catalog_2026-05-22.md` | 126 | The 57-item catalog (Pass 1) |
| `data/research/doctrinal_audit/per_entry_review_2026-05-22.md` | ~280 | Per-entry table + group-by-group hand review (Pass 2) |
| `data/research/doctrinal_audit/audit_scan_2026-05-22.json` | (raw data) | Machine-readable scoring for every entry |
| `data/research/doctrinal_audit/drift_patterns_2026-05-22.md` | ~190 | Patterns by category, time, topic, marker density (Pass 3) |
| `data/research/doctrinal_audit/operator_briefing_2026-05-22.md` | (this file) | One-page summary (Pass 4) |
| `scripts/doctrinal_audit_scan.py` | ~230 | The mechanical scanner |
| `scripts/check_drift_extras.py` | ~50 | Sanity check for PBUH / Sahaba / Bukhari etc. |
| `scripts/export_audit_table.py` | ~90 | Markdown table generator |
| `scripts/drift_patterns_analysis.py` | ~120 | Pattern analysis driver |

All committed on `claude/doctrinal-audit-2026-05-22`. No content branches touched. No cache files modified.

---

## TL;DR — the one paragraph

Audited 377 new cache entries across three unmerged branches. 357/20/0 = 94.7% aligned, 5.3% partial-on-tone-neutral-material, **0% drifted**. The model (Opus 4.7 advisor-bash-cypher) was disciplined: zero [9:128]/[9:129] citations, zero hadith-as-scripture citations, zero PBUH formulae, zero crucifixion-as-fact, zero post-Muhammad-prophet affirmations. Every flagged term (Son-of-God, Aqsa-Mosque, Jesus-Christ) turned out on review to be the model naming-and-rejecting. The 20 PARTIAL entries are all tone-neutral surah/prophet vignettes; one (`expansion-189` shirk) is worth regenerating, the rest are leave-as-is. Recommend a one-line composer-prompt tweak if you want even tighter uniformity, but the corpus is mergeable as-is.
