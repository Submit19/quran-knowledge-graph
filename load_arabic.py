"""
Load Arabic Quran text (Hafs ʿan ʿĀṣim, Uthmani script) into Neo4j.

Reads data/quran-arabic-raw.json (6,236 verses), skips 9:128-129 to align
with Rashad Khalifa's translation (6,234 verses), then batch-updates every
Verse node with arabicText (full diacritics) and arabicPlain (stripped).

Usage:
    py load_arabic.py
"""

import json
import os
import re
import sys
import unicodedata
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
ARABIC_JSON = PROJECT_ROOT / "data" / "quran-arabic-raw.json"

NEO4J_URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DB       = os.getenv("NEO4J_DATABASE", "quran")

# Verses excluded from Khalifa's translation
SKIP = {(9, 128), (9, 129)}

# ── diacritics stripping ─────────────────────────────────────────────────────

# Arabic diacritical marks (tashkeel) Unicode range + additional marks
_TASHKEEL = re.compile(
    '['
    '\u0610-\u061A'   # Arabic sign ranges
    '\u064B-\u065F'   # Fathatan through Waslah
    '\u0670'           # Superscript Alef
    '\u06D6-\u06DC'   # Small high ligatures
    '\u06DF-\u06E4'   # Small high marks
    '\u06E7-\u06E8'   # Small high marks
    '\u06EA-\u06ED'   # Small low marks
    '\u08D3-\u08E1'   # Extended Arabic marks
    '\u08E3-\u08FF'   # Extended Arabic marks
    '\uFE70-\uFE7F'   # Arabic presentation forms
    ']'
)

# Uthmani-specific characters to normalise
_UTHMANI_MAP = str.maketrans({
    '\u0671': '\u0627',  # Alef Wasla → plain Alef
    '\u06E5': '',         # Small Waw
    '\u06E6': '',         # Small Yaa
    '\u06DF': '',         # Small High Rounded Zero
})


def strip_tashkeel(text: str) -> str:
    """Remove Arabic diacritics and normalise Uthmani-specific characters."""
    text = text.translate(_UTHMANI_MAP)
    text = _TASHKEEL.sub('', text)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ── main ─────────────────────────────────────────────────────────────────────

def load_arabic():
    # 1. Read Arabic JSON
    print(f"Reading {ARABIC_JSON}...")
    with open(ARABIC_JSON, encoding="utf-8") as f:
        raw = json.load(f)

    # Build verse map: "surah:verse" -> arabic text
    arabic_map = {}
    skipped = 0
    for surah_num_str, verses in raw.items():
        for v in verses:
            ch, vn = int(v["chapter"]), int(v["verse"])
            if (ch, vn) in SKIP:
                skipped += 1
                continue
            vid = f"{ch}:{vn}"
            arabic_map[vid] = v["text"]

    print(f"  Parsed {len(arabic_map)} verses (skipped {skipped}: 9:128-129)")

    # 2. Generate plain (stripped) versions
    plain_map = {vid: strip_tashkeel(text) for vid, text in arabic_map.items()}

    # 3. Connect to Neo4j and batch update
    print(f"Connecting to Neo4j at {NEO4J_URI} (database: {NEO4J_DB})...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()

    batch_size = 500
    items = list(arabic_map.items())
    updated = 0

    with driver.session(database=NEO4J_DB) as session:
        # Check current verse count
        count = session.run("MATCH (v:Verse) RETURN count(v) AS c").single()["c"]
        print(f"  Found {count} Verse nodes in Neo4j")

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            params = [
                {"vid": vid, "ar": text, "arPlain": plain_map[vid]}
                for vid, text in batch
            ]
            result = session.run("""
                UNWIND $batch AS row
                MATCH (v:Verse {verseId: row.vid})
                SET v.arabicText = row.ar,
                    v.arabicPlain = row.arPlain
                RETURN count(v) AS updated
            """, batch=params).single()
            updated += result["updated"]
            print(f"  Batch {i // batch_size + 1}: updated {result['updated']} verses (total: {updated})")

        # 4. Verify
        missing = session.run(
            "MATCH (v:Verse) WHERE v.arabicText IS NULL RETURN count(v) AS c"
        ).single()["c"]

        # Sample check
        sample = session.run(
            "MATCH (v:Verse {verseId: '2:255'}) RETURN v.arabicText AS ar, v.arabicPlain AS plain"
        ).single()

    driver.close()

    print(f"\nDone. Updated {updated} verses.")
    if missing:
        print(f"  WARNING: {missing} verses still missing Arabic text!")
    else:
        print("  All verses have Arabic text.")

    if sample:
        ar = sample["ar"]
        pl = sample["plain"]
        # Safe print for Windows console
        try:
            print(f"\n  Sample [2:255] arabicText: {ar[:80]}...")
            print(f"  Sample [2:255] arabicPlain: {pl[:80]}...")
        except UnicodeEncodeError:
            print("  Sample verified (console can't display Arabic)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    load_arabic()
