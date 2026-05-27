"""Doctrinal-tone consistency audit — mechanical scanner.

Read-only scan of three JSONL files. Scores every entry against the
Submitter-distinctive catalog and emits a per-entry table + flagged-entry
summary. No content changes; no Anthropic API calls.

Usage:
    python scripts/doctrinal_audit_scan.py /tmp/expansion.jsonl /tmp/worst30.jsonl /tmp/baseline_plus_5.jsonl
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Marker patterns. Lowercased regexes scanned against the answer text.
# ---------------------------------------------------------------------------

ALIGNED_MARKERS = [
    ("contact_prayer", re.compile(r"contact prayer\s*\(salat\)|\bsalat\b", re.I)),
    (
        "obligatory_charity",
        re.compile(r"obligatory charity\s*\(zakat\)|\bzakat\b", re.I),
    ),
    ("most_gracious", re.compile(r"most gracious", re.I)),
    ("submitter_word", re.compile(r"\bsubmitter(s)?\b", re.I)),
    ("god_caps_in_quote", re.compile(r"\bGOD\b")),  # case-sensitive
    ("final_testament", re.compile(r"final testament", re.I)),
    (
        "khalifa_preserves",
        re.compile(r"khalifa preserves|khalifa renders|khalifa's translation", re.I),
    ),
    (
        "submitter_tradition",
        re.compile(r"submitter tradition|khalifa-specific|khalifa specific", re.I),
    ),
    (
        "code_19",
        re.compile(
            r"code[\s\-]?19|code-19|mathematical miracle|19[\s\-]?based|nineteen", re.I
        ),
    ),
    (
        "egyptian_standard",
        re.compile(r"egyptian[\s\-]?standard|king fuad|cairo edition", re.I),
    ),
    (
        "farthest_prostration",
        re.compile(
            r"farthest place of prostration|farthest masjid|farthest mosque", re.I
        ),
    ),
    ("translation_word", re.compile(r"khalifa's translation|in khalifa", re.I)),
    (
        "transforms_credits",
        re.compile(
            r"transforms? (their|the) sins into credits|sins into credits", re.I
        ),
    ),
    ("temporary_god", re.compile(r"temporary god", re.I)),
    (
        "graph_count",
        re.compile(
            r"\d+\s*verse-level mentions|in the graph|verse-level mentions", re.I
        ),
    ),
    (
        "messenger_no_distinction",
        re.compile(r"no distinction (among|between) (any of )?(his )?messengers", re.I),
    ),
    (
        "hedging_classical",
        re.compile(
            r"classical tafsir|classical exegesis|mainstream sunni|contested outside|contested both within|classical (and modern )?(sunni|shia|sunni\s*/\s*shia)|outside submitter|departs from classical|mainstream interpretation|classical islamic",
            re.I,
        ),
    ),
    (
        "hadith_caveat",
        re.compile(
            r"not hadith[\s\-]derived|hadith literature is read as|without recourse to hadith|hadith-centric|not from hadith|not via hadith|absent from the quran but appears in hadith|hadith material|extra-quranic|extra[\s\-]?quranic|hadith[\s\-]derived|hadith[\s\-]level|hadith tradition|later hadith|anti[\s\-]hadith|anti[\s\-]?Hadith proof[\s\-]text",
            re.I,
        ),
    ),
    (
        "khalifa_framework",
        re.compile(
            r"khalifa's (framework|exegesis|reading|community|tradition|footnote|interpretation|appendix|approach|view|position|theology|argument)|khalifa community|khalifa-aware",
            re.I,
        ),
    ),
    (
        "quran_alone",
        re.compile(
            r"quran[\s\-]alone|quran[\s\-]only|only the quran|sufficient religious source",
            re.I,
        ),
    ),
    (
        "kun_fa_yakun",
        re.compile(r"\bkun fa[\s\-]?yakun\b|be[\s\-]and[\s\-]it[\s\-]is", re.I),
    ),
    (
        "messenger_of_covenant",
        re.compile(r"messenger of the covenant|rashad khalifa", re.I),
    ),
]

# Hard flags — these are concerning if present in answer text.
HARD_FLAGS = [
    # Citing the Khalifa-excluded verses as scripture (with `[9:128]` or `[9:129]` form)
    ("cites_9_128", re.compile(r"\[\s*9\s*:\s*128\s*\]")),
    ("cites_9_129", re.compile(r"\[\s*9\s*:\s*129\s*\]")),
    # "Aqsa Mosque" as a building (we want "farthest place of prostration")
    ("aqsa_mosque_building", re.compile(r"(al[\s\-]?)?aqsa\s+(mosque|masjid)", re.I)),
    # "Sacred Mosque of Jerusalem" type back-projection (besides "Sacred Masjid (of Mecca)" which IS the Khalifa rendering for masjid al-haram)
    (
        "sacred_mosque_jerusalem",
        re.compile(r"sacred mosque of jerusalem|al-aqsa mosque in", re.I),
    ),
    # Hadith citations (Bukhari, Muslim, Tirmidhi, etc.) — only the canonical six
    ("cites_bukhari", re.compile(r"\b(sahih|imam)\s+(al[\s\-]?)?bukhari\b", re.I)),
    ("cites_sahih_muslim", re.compile(r"\bsahih\s+muslim\b", re.I)),
    ("cites_tirmidhi", re.compile(r"\b(jami\s+at[\s\-]?)?tirmidhi\b", re.I)),
    ("cites_abu_dawud", re.compile(r"\babu\s+dawu[dw]d?\b|\babu\s+da'?ud\b", re.I)),
    ("cites_nasai", re.compile(r"\b(sunan\s+an[\s\-]?)?nasa'?i\b", re.I)),
    ("cites_ibn_majah", re.compile(r"\b(sunan\s+)?ibn[\s\-]majah\b", re.I)),
    # Christian theological vocabulary
    ("jesus_christ", re.compile(r"\bjesus christ\b|jesus the christ\b", re.I)),
    ("son_of_god", re.compile(r"son of god\b", re.I)),
    ("virgin_mary_title", re.compile(r"\bvirgin mary\b", re.I)),
    # Post-Muhammad-prophets affirmed without rejection caveat
    (
        "ahmadiyya_positive",
        re.compile(
            r"ahmadiyya (movement |community |muslim )?(accept|affirm|recognise|recognize)",
            re.I,
        ),
    ),
    # Crucifixion as fact
    (
        "crucifixion_fact",
        re.compile(
            r"\bjesus was crucified\b|jesus' crucifixion\b|the crucifixion of (jesus|christ)\b",
            re.I,
        ),
    ),
    # Trinity as Christian mystery (without [4:171] caveat)
    # — handled in manual review (ambiguous)
    # Successor prophets affirmed
    (
        "after_muhammad_prophet",
        re.compile(r"prophet after muhammad\b|prophets came after muhammad", re.I),
    ),
    # Sufism / wali / saint cult vocabulary
    ("sufi_saint", re.compile(r"\bsufi\b|\bwali allah\b|\bsaints of god\b", re.I)),
]

# Partial-positive markers — these indicate engagement with topics that
# *require* Submitter hedging. Used to scope manual review.
RISK_TOPICS = [
    ("jesus_topic", re.compile(r"\b(jesus|isa|mary|maryam|son of mary|crucif)", re.I)),
    (
        "salat_topic",
        re.compile(
            r"\bsalat\b|\bcontact prayer\b|five[\s\-]times|\bdhuhr\b|\b`?asr\b|\bfajr\b|\bmaghrib\b|\b`?isha\b|prayer times",
            re.I,
        ),
    ),
    (
        "hadith_topic",
        re.compile(r"\bhadith\b|\bsunnah\b|\bsira\b|\bsiyar\b|\bdua\b\s+from", re.I),
    ),
    (
        "eschatology_topic",
        re.compile(
            r"\bdajjal\b|\bmahdi\b|\breturn of jesus\b|second coming|return of christ",
            re.I,
        ),
    ),
    (
        "aqsa_topic",
        re.compile(
            r"\baqsa\b|al[\s\-]?masjid al[\s\-]?aqsa|farthest masjid|night journey|isra|miraj",
            re.I,
        ),
    ),
    ("code19_topic", re.compile(r"code[\s\-]?19|nineteen|miracle of 19|74:30", re.I)),
    (
        "meccan_medinan_topic",
        re.compile(r"\bmeccan\b|\bmedinan\b|revelation order|hijrah", re.I),
    ),
    (
        "disputed_surahs",
        re.compile(
            r"\b(?:13|22|55|76|99)\b.*\b(meccan|medinan)\b|\b(meccan|medinan)\b.*\b(?:13|22|55|76|99)\b",
            re.I,
        ),
    ),
    (
        "prophet_after_muhammad",
        re.compile(
            r"khatam|final prophet|seal of the prophets|ahmadiyya|baha'i|mormon|joseph smith",
            re.I,
        ),
    ),
    ("trinity_topic", re.compile(r"\btrinity\b|\btriune\b|three-in-one", re.I)),
]


# Negation / contextual-rejection cues. If any of these appear within
# ~120 chars of the hard-flag match, the flag is "contextually negated" —
# the model is naming the term to reject it, which is the aligned move.
NEGATION_CUES = re.compile(
    r"\b(not|never|deny|denies|denying|denial|reject(?:s|ed|ing|ion)?|"
    r"refute(?:s|d|ing)?|excluded|excludes|excluding|exclusion|exclude|"
    r"allegedly|allegedly called|alleged|"
    r"khalifa[\s\-]excluded|khalifa[\s\-]omitted|"
    r"calling|claim(?:s|ed|ing)?|claims that|claimed by|"
    r"called by|forged|forgery|"
    r"was constructed|did not exist|after the quranic|"
    r"anachron|7th[\s\-]?(?:century|8th)|7th–8th centuries|"
    r"jews allegedly|christians? alleged|christian (claim|tradition|theology)|"
    r"\bin (?:any )?literal sense\b|absolutely not|"
    r"explicitly reject|opposes|opposed to|"
    r"used by|named by|"
    r"refer to|referring to|"
    r"\bagainst\b)",
    re.I,
)


def score_entry(rec):
    answer = rec.get("answer", "")
    question = rec.get("question", "")
    text = answer  # only scan the answer, not the question

    aligned_hits = []
    for name, rx in ALIGNED_MARKERS:
        if rx.search(text):
            aligned_hits.append(name)

    hard_flags = []
    for name, rx in HARD_FLAGS:
        for m in rx.finditer(text):
            # widen window for context check
            window_start = max(0, m.start() - 120)
            window_end = min(len(text), m.end() + 120)
            window = text[window_start:window_end]
            # if there's a negation cue *in the window*, this is contextually-negated
            negated = bool(NEGATION_CUES.search(window))
            ctx = text[max(0, m.start() - 40) : m.end() + 40]
            hard_flags.append((name, m.group(0), ctx.replace("\n", " "), negated))
            break  # one hit per pattern is enough for flagging

    risk_topics = []
    for name, rx in RISK_TOPICS:
        if rx.search(text) or rx.search(question):
            risk_topics.append(name)

    # Also check for `[9:128]` or `[9:129]` in citations list — these are
    # NOT contextually-negatable: citing in the cites list = treating as scripture.
    cites = rec.get("citations", [])
    if "9:128" in cites or "[9:128]" in cites:
        hard_flags.append(("cite_list_9_128", "9:128", "in citations[]", False))
    if "9:129" in cites or "[9:129]" in cites:
        hard_flags.append(("cite_list_9_129", "9:129", "in citations[]", False))

    return {
        "id": rec.get("id"),
        "bucket": rec.get("bucket"),
        "category": rec.get("category", ""),
        "question": question,
        "answer_len": len(answer),
        "cite_count": len(cites),
        "aligned_count": len(aligned_hits),
        "aligned_markers": aligned_hits,
        "hard_flags": hard_flags,
        "risk_topics": risk_topics,
        "model": rec.get("model", ""),
        "method": rec.get("method", ""),
        "answered_at": rec.get("answered_at", ""),
    }


def categorize(score):
    """Map a score dict to ALIGNED / PARTIAL / DRIFTED with rationale."""
    n_aligned = score["aligned_count"]
    flags = score["hard_flags"]
    risks = score["risk_topics"]

    # DRIFTED: hard flag present (any of: 9:128/9:129 cited as scripture, Aqsa-as-building, hadith canonical six cited, Christian theological vocabulary)
    drifted_flag_types = {
        "cites_9_128",
        "cites_9_129",
        "cite_list_9_128",
        "cite_list_9_129",
        "aqsa_mosque_building",
        "sacred_mosque_jerusalem",
        "cites_bukhari",
        "cites_sahih_muslim",
        "cites_tirmidhi",
        "cites_abu_dawud",
        "cites_nasai",
        "cites_ibn_majah",
        "jesus_christ",
        "son_of_god",
        "virgin_mary_title",
        "crucifixion_fact",
        "after_muhammad_prophet",
    }
    # Only count hard flags that are NOT contextually-negated.
    # Cite-list entries (cite_list_*) always count — citing means treating-as-scripture.
    # Non-cite-list flags in an entry with high marker density (5+) are most likely
    # quoted-context / named-and-rejected; treat as ALIGNED-with-noted-flag.
    effective_flags = [
        f
        for f in flags
        if f[0] in drifted_flag_types and (not f[3] or f[0].startswith("cite_list_"))
    ]
    cite_list_flags = [f for f in effective_flags if f[0].startswith("cite_list_")]
    if cite_list_flags:
        return "DRIFTED", "cite-list flag(s): " + ", ".join(
            set(f[0] for f in cite_list_flags)
        )

    non_cite_effective = [
        f for f in effective_flags if not f[0].startswith("cite_list_")
    ]
    if non_cite_effective:
        if n_aligned >= 5:
            # Highly-marked entry with an un-negated risky term — most likely a quoted
            # context the negation cue missed (e.g. Khalifa's own footnote referencing
            # "Jesus Christ" as a period-anchor). Flag for human spot-check.
            return (
                "ALIGNED",
                f"{n_aligned} markers + flagged-but-likely-quoted: "
                + ", ".join(set(f[0] for f in non_cite_effective)),
            )
        return "DRIFTED", "hard flag(s): " + ", ".join(
            set(f[0] for f in non_cite_effective)
        )

    # Note contextually-negated flags — entry name-and-rejects → ALIGNED
    negated = [f for f in flags if f[0] in drifted_flag_types and f[3]]
    if negated and n_aligned >= 3:
        return (
            "ALIGNED",
            f"{n_aligned} aligned markers + {len(negated)} contextually-rejected term(s)",
        )

    # PARTIAL: risk topic engaged but very few aligned markers
    high_risk_topics = {
        "jesus_topic",
        "salat_topic",
        "hadith_topic",
        "aqsa_topic",
        "code19_topic",
        "trinity_topic",
    }
    has_risk = any(t in high_risk_topics for t in risks)
    if has_risk and n_aligned < 2:
        return (
            "PARTIAL",
            f"risk topic ({','.join(t for t in risks if t in high_risk_topics)}) with low marker density ({n_aligned} aligned markers)",
        )

    # PARTIAL: zero markers anywhere → generic tone
    if n_aligned == 0:
        return "PARTIAL", "zero aligned markers — generic tone"

    return "ALIGNED", f"{n_aligned} aligned markers, no hard flags"


def main():
    paths = [Path(p) for p in sys.argv[1:]]
    all_scores = []
    for p in paths:
        src = p.name
        with p.open(encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                s = score_entry(rec)
                s["source_file"] = src
                tier, rationale = categorize(s)
                s["tier"] = tier
                s["rationale"] = rationale
                all_scores.append(s)

    # Output summary
    tiers = Counter(s["tier"] for s in all_scores)
    print(f"\nTotal entries audited: {len(all_scores)}")
    print(f"Distribution: {dict(tiers)}")
    print("By source:")
    for src in sorted(set(s["source_file"] for s in all_scores)):
        sub = [s for s in all_scores if s["source_file"] == src]
        sub_tiers = Counter(s["tier"] for s in sub)
        print(f"  {src}: {len(sub)} total — {dict(sub_tiers)}")

    # Hard-flag summary (raw vs. effective)
    print("\nHard-flag totals (raw match | contextually-rejected | effective):")
    flag_raw = Counter()
    flag_neg = Counter()
    for s in all_scores:
        for f in s["hard_flags"]:
            flag_raw[f[0]] += 1
            if f[3]:
                flag_neg[f[0]] += 1
    for name, n in flag_raw.most_common():
        neg = flag_neg.get(name, 0)
        eff = n - neg
        print(f"  {n:4d} | {neg:4d} | {eff:4d}  {name}")

    # Write detailed JSON
    out_json = Path("data/research/doctrinal_audit/audit_scan_2026-05-22.json")
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(all_scores, f, ensure_ascii=False, indent=2)
    print(f"\nWrote: {out_json}")

    return all_scores


if __name__ == "__main__":
    main()
