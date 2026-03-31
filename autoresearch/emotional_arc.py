"""
Emotional Arc Analyzer for the Quran Knowledge Graph.

Scores each verse for emotional valence and maps the emotional arc
of each surah.  Identifies emotional climaxes, arc shapes, and
intensity profiles.

One-shot script: run directly to produce autoresearch/emotional_arcs.json.
"""

import json
import os
import re
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ══════════════════════════════════════════════════════════════════════════════
# Emotion keyword lexicons
# ══════════════════════════════════════════════════════════════════════════════

EMOTION_KEYWORDS = {
    "comfort": [
        "mercy", "merciful", "forgive", "paradise", "garden", "reward",
        "bless", "peace", "love", "grace", "compassion", "gentle", "kind",
        "patient", "glad", "joy", "happy", "hope", "save", "redeem",
        "protect",
    ],
    "warning": [
        "hell", "fire", "punish", "retribution", "wrath", "doom",
        "destroy", "torment", "severe", "curse", "disaster", "affliction",
        "calamity", "grief", "regret", "fear",
    ],
    "command": [
        "shall", "must", "observe", "worship", "pray", "fast", "give",
        "strive", "fight", "obey", "follow", "avoid", "believe", "devote",
        "submit", "remember",
    ],
    "narrative": [
        "said", "told", "came", "went", "people", "sent", "when", "then",
        "before", "after", "story", "remember", "recall",
    ],
    "wonder": [
        "glory", "praise", "exalted", "magnificent", "supreme", "heavens",
        "earth", "created", "stars", "moon", "sun", "mountains", "seas",
    ],
}

# Pre-compile a single regex per category for fast matching
_EMOTION_PATTERNS = {}
for cat, words in EMOTION_KEYWORDS.items():
    # Build pattern that matches each keyword as a substring of any word
    _EMOTION_PATTERNS[cat] = re.compile(
        r"\b(?:" + "|".join(re.escape(w) for w in words) + r")",
        re.IGNORECASE,
    )

# Tiebreak order (highest priority first): narrative > command > comfort > warning > wonder
TIEBREAK_ORDER = ["narrative", "command", "comfort", "warning", "wonder"]


# ══════════════════════════════════════════════════════════════════════════════
# Verse-level scoring
# ══════════════════════════════════════════════════════════════════════════════

def score_verse(text: str) -> dict:
    """
    Score a single verse for emotional valence.

    Returns dict with:
      counts   - {emotion: int}
      primary  - the dominant emotion category
      intensity - 0-10 based on keyword density
    """
    text_lower = text.lower()
    word_count = max(len(text_lower.split()), 1)

    counts = {}
    total_hits = 0
    for cat, pat in _EMOTION_PATTERNS.items():
        hits = len(pat.findall(text_lower))
        counts[cat] = hits
        total_hits += hits

    # Primary emotion: highest count, tiebreak by TIEBREAK_ORDER
    max_count = max(counts.values())
    if max_count == 0:
        primary = "neutral"
    else:
        candidates = [c for c in TIEBREAK_ORDER if counts.get(c, 0) == max_count]
        primary = candidates[0] if candidates else max(counts, key=counts.get)

    # Intensity: keyword density scaled to 0-10
    # density = total_hits / word_count; scale so that ~0.3 density => 10
    density = total_hits / word_count
    intensity = min(10, round(density * 33.3))

    return {
        "counts": counts,
        "primary": primary,
        "intensity": intensity,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Surah-level analysis
# ══════════════════════════════════════════════════════════════════════════════

def classify_arc_shape(emotions: list) -> str:
    """
    Determine the emotional arc shape of a surah based on the first
    and last thirds of its verses.

    Returns a string like "comfort_to_warning", "warning_to_comfort", etc.
    """
    if not emotions:
        return "unknown"

    n = len(emotions)
    if n < 3:
        # Too short to have a meaningful arc; just use first and last
        first_third = emotions[:1]
        last_third = emotions[-1:]
    else:
        split = max(1, n // 3)
        first_third = emotions[:split]
        last_third = emotions[-split:]

    def dominant(segment):
        counts = defaultdict(int)
        for e in segment:
            if e["primary"] != "neutral":
                counts[e["primary"]] += 1
        if not counts:
            return "neutral"
        max_c = max(counts.values())
        for cat in TIEBREAK_ORDER:
            if counts.get(cat, 0) == max_c:
                return cat
        return max(counts, key=counts.get)

    start_emotion = dominant(first_third)
    end_emotion = dominant(last_third)

    if start_emotion == end_emotion:
        return f"sustained_{start_emotion}"
    return f"{start_emotion}_to_{end_emotion}"


def analyze_surah(surah_num: int, name: str, verses: list) -> dict:
    """
    Analyze a complete surah.

    Parameters:
      surah_num - integer surah number
      name      - surah name string
      verses    - list of dicts with keys: verse_id, text (ordered by verse)

    Returns the full surah analysis dict.
    """
    emotions = []
    for v in verses:
        result = score_verse(v["text"])
        emotions.append({
            "verse": v["verse_id"],
            "primary": result["primary"],
            "intensity": result["intensity"],
        })

    # Profile: percentage of verses in each category
    total = max(len(emotions), 1)
    profile = {}
    for cat in EMOTION_KEYWORDS:
        count = sum(1 for e in emotions if e["primary"] == cat)
        profile[cat] = round(count / total, 4)

    # Emotional range
    intensities = [e["intensity"] for e in emotions]
    max_intensity = max(intensities) if intensities else 0
    min_intensity = min(intensities) if intensities else 0
    emotional_range = max_intensity - min_intensity

    # Climax verse (highest intensity; on tie, pick the last one for dramatic effect)
    climax_verse = None
    climax_intensity = -1
    for e in emotions:
        if e["intensity"] >= climax_intensity:
            climax_intensity = e["intensity"]
            climax_verse = e["verse"]

    # Arc shape
    arc_shape = classify_arc_shape(emotions)

    return {
        "surah": surah_num,
        "name": name,
        "emotions": emotions,
        "profile": profile,
        "climax_verse": climax_verse,
        "climax_intensity": climax_intensity,
        "emotional_range": emotional_range,
        "arc_shape": arc_shape,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Main pipeline
# ══════════════════════════════════════════════════════════════════════════════

def load_verses() -> list:
    """Load verses from data/verses.json."""
    path = os.path.join(DATA_DIR, "verses.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run():
    """Run the full emotional arc analysis and save results."""
    print("Loading verses...")
    all_verses = load_verses()
    print(f"  {len(all_verses)} verses loaded")

    # Group by surah
    surahs = defaultdict(list)
    surah_names = {}
    for v in all_verses:
        s = v["surah"]
        surahs[s].append(v)
        surah_names[s] = v.get("surah_name", f"Surah {s}")

    print(f"  {len(surahs)} surahs found")
    print("\nAnalyzing emotional arcs...")

    results = {}
    for surah_num in sorted(surahs.keys()):
        verses = sorted(surahs[surah_num], key=lambda v: v["verse"])
        analysis = analyze_surah(surah_num, surah_names[surah_num], verses)
        results[str(surah_num)] = analysis

        if surah_num % 20 == 0:
            print(f"  Processed surah {surah_num}/114")

    # Summary statistics
    print(f"\n{'='*60}")
    print("  EMOTIONAL ARC SUMMARY")
    print(f"{'='*60}")

    # Most common arc shapes
    arc_counts = defaultdict(int)
    for r in results.values():
        arc_counts[r["arc_shape"]] += 1
    print("\n  Arc shapes:")
    for shape, count in sorted(arc_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"    {shape:40s} {count:3d} surahs")

    # Highest intensity surahs
    by_climax = sorted(results.values(), key=lambda r: r["climax_intensity"], reverse=True)
    print("\n  Top 10 highest-intensity surahs:")
    for r in by_climax[:10]:
        print(f"    Surah {r['surah']:3d} ({r['name']:25s})  "
              f"climax={r['climax_intensity']:2d} at {r['climax_verse']}  "
              f"arc={r['arc_shape']}")

    # Widest emotional range
    by_range = sorted(results.values(), key=lambda r: r["emotional_range"], reverse=True)
    print("\n  Top 10 widest emotional range:")
    for r in by_range[:10]:
        print(f"    Surah {r['surah']:3d} ({r['name']:25s})  range={r['emotional_range']}")

    # Save
    output_path = os.path.join(OUTPUT_DIR, "emotional_arcs.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    run()
