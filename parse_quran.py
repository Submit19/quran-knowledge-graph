"""
Step 1 — Parse the Quran PDF into structured verse data.

Extracts all verses from Rashad Khalifa's Final Testament PDF.
Produces a list of dicts: {surah, verse, surah_name, text}
Expected output: ~6,234 verses across 114 surahs.
"""

import re
import json
from pdfminer.high_level import extract_text
from dotenv import load_dotenv
import os

load_dotenv()

PDF_PATH = os.getenv("PDF_PATH", r"C:\Users\alika\OneDrive\Documents\Dr.RashadKhalifa-Quran-TheFinalTestament-AuthorizedEnglishVersion.pdf")

# Regex patterns
VERSE_PATTERN = re.compile(r'^\[(\d+):(\d+)\]\s*(.*)')
FOOTNOTE_PATTERN = re.compile(r'^\*\d+:\d+')
SURA_HEADER_PATTERN = re.compile(r'^Sura\s+(\d+):\s+(.+?)\s+\((.+?)\)', re.IGNORECASE)
SURA_HEADER_SIMPLE = re.compile(r'^Sura\s+(\d+):\s+(.+)', re.IGNORECASE)
PAGE_NUMBER_PATTERN = re.compile(r'^\d+$')
CHAPTER_PATTERN = re.compile(r'^Chapter\s+\d+', re.IGNORECASE)

# Section header patterns to skip (lines between verses that aren't verses or footnotes)
SKIP_PATTERNS = [
    FOOTNOTE_PATTERN,
    PAGE_NUMBER_PATTERN,
    CHAPTER_PATTERN,
    re.compile(r'^Part\s+\d+', re.IGNORECASE),
    re.compile(r'^Number of verses', re.IGNORECASE),
    re.compile(r'^Order of revelation', re.IGNORECASE),
]


# ── Post-processing: clean individual verse text ──────────────────────────────

# Matches trailing section-header phrases after sentence-ending punctuation.
# e.g. "...the losers. Two Deaths and Two Lives for the Disbelievers*"
#       "...that you know. Mathematical Challenge"
#       "...the righteous. The Heifer*"
# Rules: phrase starts with Capital, 2-9 words, optional trailing *, at string end.
_SECTION_HEADER = re.compile(
    r'(?<=[.!?"\u201d])\s+'                           # after sentence-ending punctuation
    r'('
      r'[A-Z][A-Za-z\u2019\']*'                       # first word capitalised
      r'(?:\s+(?:[A-Z][A-Za-z\u2019\']*|of|the|and|for|in|to|a|an|its|their|your|our|my))*'
    r')'
    r'\*{0,2}\s*$',                                   # optional * or ** at end
    re.UNICODE,
)

# Matches a surah header that bled onto the end of the previous verse.
# e.g. "...the strayers. Sura 2: The Heifer (Al-Baqarah)"
_SURA_BLEED = re.compile(r'\s+Sura\s+\d+\s*:.*$', re.IGNORECASE)

# Matches PDF hyphenation artefacts: "abso- lutely" → "absolutely"
_HYPHEN_BREAK = re.compile(r'([a-z])- ([a-z])')


def clean_verse_text(text: str) -> str:
    """
    Clean a verse's raw text by removing:
      1. PDF hyphenation artefacts          (abso- lutely  →  absolutely)
      2. Footnote reference markers         (He*  →  He,   our**  →  our)
      3. Trailing surah-header bleed-ins    (... Sura 2: The Heifer)
      4. Trailing section-header bleed-ins  (... Kill Your Ego)
    """
    # 1. Fix hyphenated line-breaks from the PDF renderer
    text = _HYPHEN_BREAK.sub(r'\1\2', text)

    # 2. Strip footnote reference markers (* and **) — these are inline callout
    #    symbols, not footnote text. They appear as  word*  or  word**  or  ,*
    text = re.sub(r'\*{1,2}', '', text)

    # 3. Remove surah headers that bled onto the end of the last verse of a surah
    text = _SURA_BLEED.sub('', text)

    # 4. Remove trailing section headers (title phrases after the verse ends)
    #    Apply repeatedly in case two headers stacked (rare but possible)
    for _ in range(3):
        cleaned = _SECTION_HEADER.sub('', text).rstrip()
        if cleaned == text:
            break
        text = cleaned

    return text.strip()


def extract_raw_text(pdf_path: str) -> str:
    print(f"Extracting text from PDF: {pdf_path}")
    text = extract_text(pdf_path)
    print(f"  Extracted {len(text):,} characters")
    return text


def parse_verses(raw_text: str) -> list[dict]:
    """
    Parse raw PDF text into structured verse records.
    Returns list of {surah, verse, surah_name, text, verse_id}
    """
    lines = raw_text.split('\n')

    # Pass 1: build surah name map
    surah_names = {}
    for line in lines:
        line = line.strip()
        m = SURA_HEADER_PATTERN.match(line)
        if m:
            surah_num = int(m.group(1))
            english_name = m.group(2).strip()
            surah_names[surah_num] = english_name
            continue
        m2 = SURA_HEADER_SIMPLE.match(line)
        if m2:
            surah_num = int(m2.group(1))
            name_part = m2.group(2).strip()
            # Remove trailing parenthetical if present
            name_part = re.sub(r'\s*\(.*?\)\s*$', '', name_part).strip()
            if surah_num not in surah_names:
                surah_names[surah_num] = name_part

    print(f"  Found {len(surah_names)} surah names")

    # Pass 2: extract verses
    verses = []
    current_surah = None
    current_verse_num = None
    current_text_parts = []
    in_footnote = False

    def flush_verse():
        """Save the current accumulated verse."""
        if current_surah is None or current_verse_num is None:
            return
        if current_verse_num == 0:
            return  # Skip Bismillah verse 0
        text = ' '.join(current_text_parts).strip()
        text = re.sub(r'\s+', ' ', text)
        text = clean_verse_text(text)
        if text:
            surah_name = surah_names.get(current_surah, f"Surah {current_surah}")
            verses.append({
                "surah": current_surah,
                "verse": current_verse_num,
                "surah_name": surah_name,
                "verse_id": f"{current_surah}:{current_verse_num}",
                "text": text,
            })

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            # Blank lines do NOT exit footnote mode — footnotes can be multi-paragraph.
            # Only a new [N:N] verse tag exits footnote mode.
            continue

        # Check if this line starts a footnote
        if FOOTNOTE_PATTERN.match(line):
            in_footnote = True
            continue

        # If we're in a footnote, skip everything until a new [N:N] verse tag
        if in_footnote:
            if VERSE_PATTERN.match(line):
                in_footnote = False
                # Fall through to verse handling below
            else:
                continue

        # Check for other skip patterns
        skip = False
        for pat in SKIP_PATTERNS:
            if pat.match(line):
                skip = True
                break
        if skip:
            continue

        # Check for a new verse
        verse_match = VERSE_PATTERN.match(line)
        if verse_match:
            # Save previous verse
            flush_verse()
            # Start new verse
            current_surah = int(verse_match.group(1))
            current_verse_num = int(verse_match.group(2))
            current_text_parts = [verse_match.group(3)] if verse_match.group(3).strip() else []
            in_footnote = False
            continue

        # If we have an active verse, accumulate continuation lines
        if current_surah is not None and current_verse_num is not None and current_verse_num != 0:
            # Skip lines that look like section headings mixed into text
            # (short ALL-CAPS or Title Case standalone lines between verses)
            # We keep them if they're clearly part of verse text (not too short, no bracket patterns)
            current_text_parts.append(line)

    # Flush last verse
    flush_verse()

    # Deduplicate: keep first occurrence of each verse_id (later ones are appendix refs)
    seen_ids = set()
    deduped = []
    for v in verses:
        if v['verse_id'] not in seen_ids:
            seen_ids.add(v['verse_id'])
            deduped.append(v)
    if len(deduped) < len(verses):
        print(f"  Deduplicated: removed {len(verses) - len(deduped)} duplicate verse IDs")

    return deduped


def validate_verses(verses: list[dict]) -> None:
    surah_counts = {}
    for v in verses:
        surah_counts[v['surah']] = surah_counts.get(v['surah'], 0) + 1

    print(f"\n{'='*50}")
    print(f"PARSING RESULTS")
    print(f"{'='*50}")
    print(f"Total verses parsed:  {len(verses):,}")
    print(f"Total surahs found:   {len(surah_counts)}")
    print(f"Expected verses:      ~6,234")
    print(f"Expected surahs:      114")

    # Show cleaning worked on known problem verses
    print(f"\nCleaning verification (known problem verses):")
    checks = [
        (1,   1,  "should have no trailing *"),
        (2,   3,  "should have no inline * markers"),
        (2,  19,  "should not end with 'The Light of Faith'"),
        (2,  22,  "should not end with 'Mathematical Challenge'"),
        (2,  27,  "should not end with section header"),
        (2,  53,  "should not end with 'Kill Your Ego'"),
        (1,   7,  "should not end with Sura 2 header"),
        (2,   4,  "abso-lutely should be fixed"),
    ]
    for s, v, note in checks:
        verse = next((x for x in verses if x['surah'] == s and x['verse'] == v), None)
        if verse:
            print(f"  [{s}:{v}] ({note})")
            print(f"         {verse['text'][:100]}")

    print(f"\nSample verses:")
    samples = [(1, 1), (2, 255), (36, 1), (112, 1), (114, 6)]
    for s, v in samples:
        verse = next((x for x in verses if x['surah'] == s and x['verse'] == v), None)
        if verse:
            print(f"  [{s}:{v}] {verse['text'][:80]}...")
        else:
            print(f"  [{s}:{v}] NOT FOUND")

    # Warn if surahs have unexpected verse counts
    KNOWN_COUNTS = {1: 7, 2: 286, 3: 200, 36: 83, 112: 4, 113: 5, 114: 6}
    print(f"\nSurah verse count check:")
    for s, expected in KNOWN_COUNTS.items():
        actual = surah_counts.get(s, 0)
        status = "OK" if actual == expected else f"MISMATCH (expected {expected})"
        print(f"  Surah {s:3d}: {actual} verses {status}")


def save_verses(verses: list[dict], output_path: str = "data/verses.json") -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(verses, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(verses):,} verses to {output_path}")


if __name__ == "__main__":
    raw = extract_raw_text(PDF_PATH)
    verses = parse_verses(raw)
    validate_verses(verses)
    save_verses(verses, "data/verses.json")
