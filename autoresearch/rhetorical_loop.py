"""
Rhetorical Pattern Analysis Loop for the Quran Knowledge Graph.

Detects ring compositions, repetition patterns, question-answer pairs,
and word frequency symmetries across surahs in an infinite analysis loop.
"""

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deduction_engine import load_graph

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

STOP_WORDS = {
    "the", "of", "and", "to", "in", "a", "is", "that", "for", "it", "with",
    "was", "on", "are", "be", "this", "have", "from", "or", "an", "they",
    "which", "you", "not", "but", "had", "his", "her", "has", "their", "all",
    "been", "if", "will", "who", "do", "shall", "them", "he", "she", "we",
    "no", "so", "by", "as", "at", "your", "what", "when", "upon", "did",
    "those", "then", "there", "may", "would", "its", "any", "into", "said",
}

def words(text):
    """Extract lowercase words from text, filtering stop words."""
    return [w for w in re.findall(r"[a-z']+", text.lower()) if w not in STOP_WORDS and len(w) > 2]


def group_by_surah(verses):
    """Group verses by surah number, sorted by verse number."""
    surahs = defaultdict(list)
    for vid, info in verses.items():
        surahs[info["surah"]].append((vid, info))
    for s in surahs:
        surahs[s].sort(key=lambda x: int(x[0].split(":")[1]))
    return surahs


def save_json(filename, data):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


# ══════════════════════════════════════════════════════════════════════════════
# Analysis 1: Ring Composition Detection
# ══════════════════════════════════════════════════════════════════════════════

def detect_ring_compositions(surahs, keyword_map):
    """Detect chiastic (A-B-C-B'-A') theme patterns within surahs."""
    results = []

    for surah_num, verse_list in surahs.items():
        if len(verse_list) < 5:
            continue

        # Build theme sequence per verse using top keywords
        themes = []
        for vid, info in verse_list:
            kws = keyword_map.get(vid, [])
            top_kw = tuple(sorted(kw for kw, _ in kws[:3]))
            themes.append((vid, top_kw))

        n = len(themes)
        # Check for mirror symmetry: compare first half with reversed second half
        half = n // 2
        matches = 0
        match_pairs = []
        for i in range(half):
            front = set(themes[i][1])
            back = set(themes[n - 1 - i][1])
            overlap = front & back
            if overlap and len(overlap) >= 1:
                matches += 1
                match_pairs.append({
                    "front_verse": themes[i][0],
                    "back_verse": themes[n - 1 - i][0],
                    "shared_themes": list(overlap),
                })

        if half > 0:
            symmetry_ratio = matches / half
        else:
            continue

        if symmetry_ratio >= 0.25 and matches >= 2:
            results.append({
                "surah": surah_num,
                "surah_name": verse_list[0][1]["surahName"],
                "total_verses": n,
                "mirror_matches": matches,
                "symmetry_ratio": round(symmetry_ratio, 3),
                "pairs": match_pairs[:10],
            })

    results.sort(key=lambda x: -x["symmetry_ratio"])
    return results


# ══════════════════════════════════════════════════════════════════════════════
# Analysis 2: Repetition Pattern Detection
# ══════════════════════════════════════════════════════════════════════════════

def find_repetition_patterns(verses, min_phrase_len=3, max_phrase_len=5, min_surahs=3):
    """Find phrases of 3-5 words that appear across 3+ surahs."""
    phrase_locations = defaultdict(set)  # phrase -> set of surah numbers

    for vid, info in verses.items():
        w = info["text"].lower().split()
        surah = info["surah"]
        for length in range(min_phrase_len, min(max_phrase_len + 1, len(w) + 1)):
            for i in range(len(w) - length + 1):
                phrase = " ".join(w[i:i + length])
                # Skip boring phrases
                phrase_words = set(re.findall(r"[a-z]+", phrase))
                if phrase_words <= STOP_WORDS:
                    continue
                phrase_locations[phrase].add(surah)

    # Filter to phrases in 3+ surahs
    patterns = []
    for phrase, surah_set in phrase_locations.items():
        if len(surah_set) >= min_surahs:
            patterns.append({
                "phrase": phrase,
                "surah_count": len(surah_set),
                "surahs": sorted(surah_set, key=lambda x: int(x))[:20],
            })

    patterns.sort(key=lambda x: -x["surah_count"])
    return patterns[:500]


# ══════════════════════════════════════════════════════════════════════════════
# Analysis 3: Question-Answer Detection
# ══════════════════════════════════════════════════════════════════════════════

def find_question_answer_pairs(surahs):
    """Find verses containing '?' and pair with following verse."""
    qa_pairs = []

    for surah_num, verse_list in surahs.items():
        for i, (vid, info) in enumerate(verse_list):
            if "?" in info["text"]:
                answer = None
                if i + 1 < len(verse_list):
                    answer = {
                        "verse_id": verse_list[i + 1][0],
                        "text": verse_list[i + 1][1]["text"][:200],
                    }
                qa_pairs.append({
                    "question_verse": vid,
                    "question_text": info["text"][:200],
                    "surah": surah_num,
                    "surah_name": info["surahName"],
                    "answer": answer,
                })

    return qa_pairs


# ══════════════════════════════════════════════════════════════════════════════
# Analysis 4: Word Frequency Symmetries
# ══════════════════════════════════════════════════════════════════════════════

WORD_PAIRS = [
    ("life", "death"), ("angel", "devil"), ("heaven", "hell"),
    ("man", "woman"), ("good", "evil"), ("day", "night"),
    ("reward", "punishment"), ("believe", "disbelieve"),
    ("mercy", "wrath"), ("love", "hate"), ("peace", "war"),
    ("light", "darkness"), ("earth", "sky"), ("rich", "poor"),
    ("patient", "impatient"), ("truth", "falsehood"),
    ("obey", "disobey"), ("paradise", "fire"),
    ("gratitude", "ingratitude"), ("visible", "invisible"),
]


def count_word_pair_symmetries(verses):
    """Count occurrences of paired concepts across all verses."""
    results = []
    all_text = " ".join(v["text"].lower() for v in verses.values())

    for w1, w2 in WORD_PAIRS:
        c1 = len(re.findall(r"\b" + w1 + r"\w*\b", all_text))
        c2 = len(re.findall(r"\b" + w2 + r"\w*\b", all_text))
        if c1 > 0 or c2 > 0:
            ratio = min(c1, c2) / max(c1, c2) if max(c1, c2) > 0 else 0
            results.append({
                "word1": w1, "count1": c1,
                "word2": w2, "count2": c2,
                "ratio": round(ratio, 3),
                "total": c1 + c2,
                "nearly_symmetric": ratio > 0.8,
            })

    results.sort(key=lambda x: -x["total"])
    return results


# ══════════════════════════════════════════════════════════════════════════════
# Main Loop
# ══════════════════════════════════════════════════════════════════════════════

def run_loop(max_hours=0):
    print("=" * 70)
    print("  RHETORICAL PATTERN ANALYSIS LOOP")
    print("=" * 70)

    print("\nLoading graph data...")
    graph = load_graph()
    verses = graph["verses"]
    verse_keywords = graph["verse_keywords"]
    surahs = group_by_surah(verses)
    print(f"  {len(verses)} verses in {len(surahs)} surahs")

    start_time = time.time()
    rnd = 0

    ring_results = []
    repetition_results = []
    qa_pairs = []
    symmetry_results = []

    while True:
        rnd += 1
        elapsed_h = (time.time() - start_time) / 3600
        if max_hours > 0 and elapsed_h >= max_hours:
            print(f"\nTime limit reached ({max_hours}h). Stopping.")
            break

        # Round-robin through analyses with varying parameters
        if rnd % 4 == 1:
            ring = detect_ring_compositions(surahs, verse_keywords)
            # Merge new findings
            seen = {r["surah"] for r in ring_results}
            for r in ring:
                if r["surah"] not in seen:
                    ring_results.append(r)
                    seen.add(r["surah"])

        elif rnd % 4 == 2:
            min_len = 3 + (rnd // 8) % 3  # vary phrase length
            min_s = 3 + (rnd // 12) % 3   # vary min surahs
            reps = find_repetition_patterns(verses, min_phrase_len=min_len,
                                            max_phrase_len=min_len + 2,
                                            min_surahs=min_s)
            seen = {r["phrase"] for r in repetition_results}
            for r in reps:
                if r["phrase"] not in seen:
                    repetition_results.append(r)
                    seen.add(r["phrase"])

        elif rnd % 4 == 3:
            if not qa_pairs:
                qa_pairs = find_question_answer_pairs(surahs)

        else:
            symmetry_results = count_word_pair_symmetries(verses)

        # Progress report every 5 rounds
        if rnd % 5 == 0:
            print(f"\n  [Round {rnd}] {elapsed_h:.2f}h elapsed")
            print(f"    Ring compositions: {len(ring_results)}")
            print(f"    Repetition patterns: {len(repetition_results)}")
            print(f"    Question-answer pairs: {len(qa_pairs)}")
            print(f"    Word symmetries: {len(symmetry_results)}")

        # Save every 10 rounds
        if rnd % 10 == 0:
            ring_results.sort(key=lambda x: -x["symmetry_ratio"])
            save_json("ring_compositions.json", ring_results[:300])

            repetition_results.sort(key=lambda x: -x["surah_count"])
            save_json("repetition_patterns.json", repetition_results[:500])

            save_json("rhetorical_structures.json", {
                "question_answer_pairs": qa_pairs[:500],
                "word_pair_symmetries": symmetry_results,
                "rounds_completed": rnd,
                "elapsed_hours": round(elapsed_h, 2),
            })
            print(f"    -> Saved results to JSON files")

        # For the first pass, do a quick save after round 4
        if rnd == 4:
            save_json("ring_compositions.json", ring_results[:300])
            save_json("repetition_patterns.json", repetition_results[:500])
            save_json("rhetorical_structures.json", {
                "question_answer_pairs": qa_pairs[:500],
                "word_pair_symmetries": symmetry_results,
                "rounds_completed": rnd,
                "elapsed_hours": round(elapsed_h, 2),
            })
            print(f"\n  [Round {rnd}] Initial save complete.")

    # Final save
    ring_results.sort(key=lambda x: -x["symmetry_ratio"])
    p1 = save_json("ring_compositions.json", ring_results[:300])
    repetition_results.sort(key=lambda x: -x["surah_count"])
    p2 = save_json("repetition_patterns.json", repetition_results[:500])
    p3 = save_json("rhetorical_structures.json", {
        "question_answer_pairs": qa_pairs[:500],
        "word_pair_symmetries": symmetry_results,
        "rounds_completed": rnd,
        "elapsed_hours": round((time.time() - start_time) / 3600, 2),
    })
    print(f"\nFinal results saved:")
    print(f"  {p1}")
    print(f"  {p2}")
    print(f"  {p3}")
    print(f"  Total rounds: {rnd}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rhetorical pattern analysis loop")
    parser.add_argument("--max-hours", type=float, default=0,
                        help="Maximum hours to run (0=infinite)")
    args = parser.parse_args()
    run_loop(max_hours=args.max_hours)
