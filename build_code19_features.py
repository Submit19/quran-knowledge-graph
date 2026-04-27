"""
build_code19_features.py — compute Khalifa-style Code-19 features and stamp
them as Neo4j properties on Sura and Verse nodes.

These are pure arithmetic over the immutable Arabic text. Once stamped, they
can be cited by the agent without any chance of hallucination — they are not
interpretive, they are counts.

Per :Sura:
  - verses_count           total number of verses
  - mysterious_letters     the opening letters string (e.g. "Q", "N", "ALR")
                           or null for surahs without
  - ml_letter_counts       map<letter -> count> for the letters that initialize
                           this surah (computed over arabicPlain of all its verses)
  - ml_div_19              map<letter -> bool> indicating count % 19 == 0
  - mod19_verse_count      verses_count % 19
  - sura_number            for convenience

Per :Verse:
  - position_in_sura       1-based index within the sura
  - is_initial_verse       true iff verseNum == 1 in a mysterious-letter surah
  - char_count             length of arabicPlain
  - word_count             words in arabicPlain
  - letter_q / _n / _s / _m / _h / _ya / _alif / _lam / _ain / _sad / _sin / _kaf / _ta / _ra
                           per-verse counts of the 13 letters that appear in
                           any mysterious-letter combination

Globally written to data/code19_summary.json:
  - total_numbered_verses
  - khalifa_total (numbered + 112 unnumbered Basmalahs = 6346)
  - global_letter_counts (across all Arabic verses)
  - per-mysterious-letter-surah summary

Usage:
  python build_code19_features.py
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
USER     = os.getenv("NEO4J_USER",     "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "")
DB       = os.getenv("NEO4J_DATABASE", "quran")

# ── Letters relevant to mysterious-letter (huroof muqatta'at) calculations ──
LETTERS = {
    "alif": "\u0627",   # ا
    "lam":  "\u0644",   # ل
    "mim":  "\u0645",   # م
    "ra":   "\u0631",   # ر
    "sad":  "\u0635",   # ص
    "kaf":  "\u0643",   # ك
    "ha":   "\u0647",   # ه (the regular ha — used in "Ta Ha" + "Kaf Ha Ya Ain Sad")
    "ya":   "\u064A",   # ي
    "ain":  "\u0639",   # ع
    "ta":   "\u0637",   # ط (emphatic Ta — used in "Ta Ha" + "Ta Sin Mim" + "Ta Sin")
    "sin":  "\u0633",   # س
    "qaf":  "\u0642",   # ق
    "nun":  "\u0646",   # ن
    # Note: "Ha Mim" surahs (40-46) use \u062D (ح) "heavy ha", different from
    # \u0647 (ه) "regular ha". We track this separately:
    "ha_heavy": "\u062D",
}

# Map each mysterious-letter surah to the LIST of letters that open it.
# (We use letter NAMES, not the Arabic letters, because we'll look up each
# from LETTERS above to get the actual character for counting.)
MYSTERIOUS_LETTERS = {
    2:  ["alif", "lam", "mim"],            # Alif Lam Mim
    3:  ["alif", "lam", "mim"],
    7:  ["alif", "lam", "mim", "sad"],     # Alif Lam Mim Sad
    10: ["alif", "lam", "ra"],             # Alif Lam Ra
    11: ["alif", "lam", "ra"],
    12: ["alif", "lam", "ra"],
    13: ["alif", "lam", "mim", "ra"],      # Alif Lam Mim Ra
    14: ["alif", "lam", "ra"],
    15: ["alif", "lam", "ra"],
    19: ["kaf", "ha", "ya", "ain", "sad"], # Kaf Ha Ya Ain Sad
    20: ["ta", "ha"],                       # Ta Ha
    26: ["ta", "sin", "mim"],              # Ta Sin Mim
    27: ["ta", "sin"],                      # Ta Sin
    28: ["ta", "sin", "mim"],
    29: ["alif", "lam", "mim"],
    30: ["alif", "lam", "mim"],
    31: ["alif", "lam", "mim"],
    32: ["alif", "lam", "mim"],
    36: ["ya", "sin"],                      # Ya Sin
    38: ["sad"],                            # Sad
    40: ["ha_heavy", "mim"],               # Ha Mim
    41: ["ha_heavy", "mim"],
    42: ["ha_heavy", "mim", "ain", "sin", "qaf"],  # Ha Mim, Ain Sin Qaf
    43: ["ha_heavy", "mim"],
    44: ["ha_heavy", "mim"],
    45: ["ha_heavy", "mim"],
    46: ["ha_heavy", "mim"],
    50: ["qaf"],                            # Qaf
    68: ["nun"],                            # Nun
}

# Display string for the letters opening a surah, e.g. "Q" for Sura 50
LETTER_DISPLAY = {
    "alif": "A", "lam": "L", "mim": "M", "ra": "R", "sad": "S",
    "kaf": "K", "ha": "h", "ya": "Y", "ain": "Ain", "ta": "T",
    "sin": "Sin", "qaf": "Q", "nun": "N", "ha_heavy": "H",
}


def display_letters(names: list[str]) -> str:
    return "".join(LETTER_DISPLAY[n] for n in names)


def main():
    print(f"Connecting to Neo4j ({URI}, db={DB})...")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    driver.verify_connectivity()
    print("  OK")

    # ── Pull all verses with arabicPlain ─────────────────────────────────────
    print("\nLoading verses + arabic text...")
    with driver.session(database=DB) as s:
        rows = s.run("""
            MATCH (v:Verse) WHERE v.verseId IS NOT NULL
            RETURN v.verseId AS id, v.surah AS sura, v.verseNum AS vn,
                   v.arabicPlain AS ap, v.arabicText AS at, v.text AS en
            ORDER BY v.surah, v.verseNum
        """).data()
    print(f"  loaded {len(rows):,} verses")

    # group by sura
    by_sura: dict[int, list[dict]] = {}
    for r in rows:
        by_sura.setdefault(r["sura"], []).append(r)

    # ── Per-verse features ───────────────────────────────────────────────────
    print("\nComputing per-verse features...")
    verse_props = []
    for sura_num, verses in by_sura.items():
        verses.sort(key=lambda v: v["vn"])
        for idx, v in enumerate(verses, 1):
            ap = v["ap"] or ""
            features = {
                "id": v["id"],
                "position_in_sura": idx,
                "is_initial_verse": (idx == 1 and sura_num in MYSTERIOUS_LETTERS),
                "char_count": len(ap),
                "word_count": len(ap.split()) if ap else 0,
            }
            # Per-letter counts across ALL letters
            for name, ch in LETTERS.items():
                features[f"letter_{name}"] = ap.count(ch)
            verse_props.append(features)
    print(f"  computed for {len(verse_props):,} verses")

    # ── Per-sura aggregates ──────────────────────────────────────────────────
    print("\nComputing per-sura aggregates...")
    sura_props = []
    summary_per_sura = {}
    for sura_num, verses in by_sura.items():
        # Aggregate plain text for the whole sura
        full_plain = " ".join(v["ap"] or "" for v in verses)

        ml_letter_counts = {}
        ml_div_19 = {}
        if sura_num in MYSTERIOUS_LETTERS:
            for letter_name in MYSTERIOUS_LETTERS[sura_num]:
                ch = LETTERS[letter_name]
                cnt = full_plain.count(ch)
                ml_letter_counts[letter_name] = cnt
                ml_div_19[letter_name] = (cnt % 19 == 0)

        sura_props.append({
            "number": sura_num,
            "verses_count": len(verses),
            "mysterious_letters": (
                display_letters(MYSTERIOUS_LETTERS[sura_num])
                if sura_num in MYSTERIOUS_LETTERS else None
            ),
            "ml_letter_counts_json": json.dumps(ml_letter_counts) if ml_letter_counts else None,
            "ml_div_19_json": json.dumps(ml_div_19) if ml_div_19 else None,
            "mod19_verse_count": len(verses) % 19,
        })
        if sura_num in MYSTERIOUS_LETTERS:
            summary_per_sura[sura_num] = {
                "letters": display_letters(MYSTERIOUS_LETTERS[sura_num]),
                "verses": len(verses),
                "letter_counts": ml_letter_counts,
                "all_div_19": all(ml_div_19.values()) if ml_div_19 else None,
            }

    # ── Write to Neo4j ───────────────────────────────────────────────────────
    print("\nWriting per-verse properties...")
    BATCH = 200
    with driver.session(database=DB) as s:
        for i in range(0, len(verse_props), BATCH):
            batch = verse_props[i:i + BATCH]
            s.run("""
                UNWIND $rows AS row
                MATCH (v:Verse {verseId: row.id})
                SET v.position_in_sura = row.position_in_sura,
                    v.is_initial_verse = row.is_initial_verse,
                    v.ar_char_count = row.char_count,
                    v.ar_word_count = row.word_count,
                    v.letter_alif = row.letter_alif,
                    v.letter_lam  = row.letter_lam,
                    v.letter_mim  = row.letter_mim,
                    v.letter_ra   = row.letter_ra,
                    v.letter_sad  = row.letter_sad,
                    v.letter_kaf  = row.letter_kaf,
                    v.letter_ha   = row.letter_ha,
                    v.letter_ha_heavy = row.letter_ha_heavy,
                    v.letter_ya   = row.letter_ya,
                    v.letter_ain  = row.letter_ain,
                    v.letter_ta   = row.letter_ta,
                    v.letter_sin  = row.letter_sin,
                    v.letter_qaf  = row.letter_qaf,
                    v.letter_nun  = row.letter_nun
            """, rows=batch)
            done = min(i + BATCH, len(verse_props))
            print(f"  {done}/{len(verse_props)}", end="\r")
    print(f"  {len(verse_props)}/{len(verse_props)} OK              ")

    print("\nWriting per-sura properties...")
    with driver.session(database=DB) as s:
        s.run("""
            UNWIND $rows AS row
            MERGE (su:Sura {number: row.number})
            SET su.verses_count = row.verses_count,
                su.mysterious_letters = row.mysterious_letters,
                su.ml_letter_counts_json = row.ml_letter_counts_json,
                su.ml_div_19_json = row.ml_div_19_json,
                su.mod19_verse_count = row.mod19_verse_count
        """, rows=sura_props)
    print(f"  {len(sura_props)} suras updated")

    # ── Global summary ───────────────────────────────────────────────────────
    print("\nComputing global summary...")
    total_numbered_verses = sum(s["verses_count"] for s in sura_props)
    # Khalifa's full count = numbered verses + 112 unnumbered Basmalahs
    # (114 surahs minus Surah 9 which has no Basmalah, minus Al-Fatihah whose
    #  Basmalah is counted as 1:1 and thus already in numbered verses)
    unnumbered_basmalahs = 112
    khalifa_total = total_numbered_verses + unnumbered_basmalahs

    global_letter_counts = {}
    for letter_name, ch in LETTERS.items():
        global_letter_counts[letter_name] = sum(v[f"letter_{letter_name}"] for v in verse_props)

    summary = {
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "total_numbered_verses": total_numbered_verses,
        "unnumbered_basmalahs": unnumbered_basmalahs,
        "khalifa_total": khalifa_total,
        "khalifa_total_div_19": khalifa_total % 19 == 0,
        "khalifa_total_div_by_19_quotient": khalifa_total // 19,
        "num_surahs": len(sura_props),
        "num_surahs_div_19": len(sura_props) % 19 == 0,
        "num_mysterious_letter_surahs": len(MYSTERIOUS_LETTERS),
        "global_letter_counts": global_letter_counts,
        "per_mysterious_letter_surah": summary_per_sura,
    }

    out_path = Path(__file__).parent / "data" / "code19_summary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote {out_path}")

    print("\n=== Headline checks ===")
    print(f"  Numbered verses          : {total_numbered_verses}")
    print(f"  Khalifa total (+112 basm): {khalifa_total}  div 19: {khalifa_total % 19 == 0}  (= 19 * {khalifa_total // 19})")
    print(f"  Surahs                   : {len(sura_props)}")
    print(f"  Qaf in Surah 50          : {summary_per_sura.get(50, {}).get('letter_counts', {}).get('qaf')}")
    print(f"  Qaf in Surah 42          : {summary_per_sura.get(42, {}).get('letter_counts', {}).get('qaf')}")
    print(f"  Nun in Surah 68          : {summary_per_sura.get(68, {}).get('letter_counts', {}).get('nun')}")
    print(f"  Sad in Surah 38          : {summary_per_sura.get(38, {}).get('letter_counts', {}).get('sad')}")
    print(f"  Ya+Sin in Surah 36       : ya={summary_per_sura.get(36, {}).get('letter_counts', {}).get('ya')} "
          f"sin={summary_per_sura.get(36, {}).get('letter_counts', {}).get('sin')}")

    driver.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
