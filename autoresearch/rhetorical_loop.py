"""
Rhetorical Pattern Analyzer — infinite loop that discovers ring compositions,
repetition patterns, question-answer pairs, and word frequency symmetries.

Saves: ring_compositions.json, repetition_patterns.json, rhetorical_structures.json
"""

import argparse
import json
import os
import re
import time
from collections import Counter, defaultdict

from deduction_engine import load_graph
from analyze_deductions import THEOLOGICAL_CATEGORIES

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

STOPWORDS = {
    "the", "and", "of", "to", "in", "for", "is", "are", "was", "were", "a",
    "an", "that", "this", "it", "he", "she", "they", "we", "you", "his",
    "her", "their", "our", "your", "with", "from", "on", "at", "by", "or",
    "be", "has", "have", "had", "shall", "will", "do", "did", "not", "but",
    "who", "whom", "which", "what", "them", "those", "these", "its", "as",
    "if", "then", "than", "so", "no", "nor", "upon", "when", "into",
}

WORD_PAIRS = [
    ("life", "death"), ("heaven", "hell"), ("angel", "devil"),
    ("light", "darkness"), ("good", "evil"), ("reward", "punishment"),
    ("believer", "disbeliever"), ("day", "night"), ("man", "woman"),
    ("land", "sea"), ("rich", "poor"), ("mercy", "wrath"),
    ("paradise", "fire"), ("peace", "war"), ("truth", "falsehood"),
    ("love", "hate"), ("patience", "haste"), ("visible", "invisible"),
]


def tokenize(text):
    return re.findall(r'[a-z]+', text.lower())


def content_words(text):
    return [w for w in tokenize(text) if w not in STOPWORDS and len(w) > 2]


def get_surah_verses(graph):
    """Group verses by surah, ordered by verse number."""
    surahs = defaultdict(list)
    for vid, data in graph["verses"].items():
        parts = vid.split(":")
        surahs[data["surah"]].append({
            "id": vid,
            "num": int(parts[1]),
            "text": data["text"],
            "surahName": data["surahName"],
        })
    for s in surahs:
        surahs[s].sort(key=lambda v: v["num"])
    return surahs


# ══════════════════════════════════════════════════════════════════════════════
# Analysis 1: Ring Composition Detection (category-based LCS approach)
# ══════════════════════════════════════════════════════════════════════════════

def _verse_primary_category(text):
    """Assign a single primary theological category to a verse."""
    words = set(re.findall(r'[a-z]+', text.lower()))
    best_cat = "uncategorized"
    best_score = 0
    for cat_name, cat_info in THEOLOGICAL_CATEGORIES.items():
        overlap = len(words & cat_info["keywords"])
        if overlap > best_score:
            best_score = overlap
            best_cat = cat_name
    return best_cat


def _lcs_length(seq_a, seq_b):
    """Compute length of the longest common subsequence of two sequences."""
    m, n = len(seq_a), len(seq_b)
    if m == 0 or n == 0:
        return 0
    # Space-optimised DP (two rows)
    prev = [0] * (n + 1)
    curr = [0] * (n + 1)
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq_a[i - 1] == seq_b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev, curr = curr, [0] * (n + 1)
    return max(prev)


def detect_ring_compositions(surah_verses, keyword_data):
    """
    Detect chiastic (A-B-C-D-C-B-A) ring compositions within surahs.

    Approach:
      1. Assign each verse a primary theological category.
      2. Build the category sequence for the surah.
      3. Split into first-half and reversed second-half.
      4. Compute LCS between them.
      5. symmetry_score = LCS_length / half_length * 100.
    """
    results = []

    for surah_id, verses in surah_verses.items():
        if len(verses) < 6:
            continue

        n = len(verses)
        name = verses[0]["surahName"]

        # Step 1-2: Build category sequence
        cat_sequence = [_verse_primary_category(v["text"]) for v in verses]

        # Step 3: Split around centre
        half = n // 2
        first_half = cat_sequence[:half]
        second_half = cat_sequence[n - half:]  # same length as first_half
        reversed_second = list(reversed(second_half))

        # Step 4: LCS
        lcs_len = _lcs_length(first_half, reversed_second)

        # Step 5: Score
        if half == 0:
            continue
        symmetry_score = round(lcs_len / half * 100, 2)

        # Build mirror-pair detail (block-level for readability)
        block_size = max(1, n // 7)
        mirror_pairs = []
        num_blocks = n // block_size
        num_pairs = num_blocks // 2
        for i in range(num_pairs):
            front_start = i * block_size
            front_end = min(front_start + block_size, n)
            back_end = n - i * block_size
            back_start = max(back_end - block_size, 0)
            front_cats = Counter(cat_sequence[front_start:front_end])
            back_cats = Counter(cat_sequence[back_start:back_end])
            shared_cats = set(front_cats.keys()) & set(back_cats.keys())
            total_cats = set(front_cats.keys()) | set(back_cats.keys())
            sim = len(shared_cats) / max(1, len(total_cats))
            mirror_pairs.append({
                "pair": (verses[front_start]["id"], verses[back_start]["id"]),
                "front_dominant": front_cats.most_common(1)[0][0],
                "back_dominant": back_cats.most_common(1)[0][0],
                "category_overlap": round(sim, 3),
            })

        # Centre element(s)
        if n % 2 == 1:
            center_cat = cat_sequence[n // 2]
        else:
            center_cat = Counter(cat_sequence[half - 1:half + 1]).most_common(1)[0][0]

        results.append({
            "surah": surah_id,
            "surahName": name,
            "num_verses": n,
            "symmetry_score": symmetry_score,
            "lcs_length": lcs_len,
            "half_length": half,
            "center_theme": center_cat,
            "category_sequence_summary": [
                f"{cat}({count})"
                for cat, count in Counter(cat_sequence).most_common()
            ],
            "num_mirror_pairs": len(mirror_pairs),
            "mirror_pairs": mirror_pairs,
        })

    results.sort(key=lambda x: -x["symmetry_score"])
    return results


# ══════════════════════════════════════════════════════════════════════════════
# Analysis 2: Repetition Patterns
# ══════════════════════════════════════════════════════════════════════════════

def find_repetition_patterns(graph, min_phrase_len=3, max_phrase_len=5, min_surahs=3):
    """Find repeated multi-word phrases across surahs."""
    phrase_locations = defaultdict(list)

    for vid, data in graph["verses"].items():
        words = tokenize(data["text"])
        surah = data["surah"]
        for plen in range(min_phrase_len, max_phrase_len + 1):
            for i in range(len(words) - plen + 1):
                phrase = " ".join(words[i:i + plen])
                non_stop = [w for w in words[i:i + plen] if w not in STOPWORDS]
                if len(non_stop) < 2:
                    continue
                phrase_locations[phrase].append((vid, surah))

    results = []
    for phrase, locations in phrase_locations.items():
        surah_set = set(s for _, s in locations)
        if len(surah_set) >= min_surahs:
            verse_ids = list(set(v for v, _ in locations))
            results.append({
                "phrase": phrase,
                "num_occurrences": len(locations),
                "num_surahs": len(surah_set),
                "surahs": sorted(surah_set, key=lambda x: int(x))[:20],
                "sample_verses": verse_ids[:10],
            })

    results.sort(key=lambda x: (-x["num_surahs"], -x["num_occurrences"]))
    return results[:500]


# ══════════════════════════════════════════════════════════════════════════════
# Analysis 3: Question-Answer Detection
# ══════════════════════════════════════════════════════════════════════════════

def find_question_answer_pairs(surah_verses):
    """Find verses containing '?' and pair with following verse(s)."""
    results = []

    for surah_id, verses in surah_verses.items():
        for i, v in enumerate(verses):
            if "?" in v["text"]:
                pair = {
                    "question_verse": v["id"],
                    "question_text": v["text"],
                    "surahName": v["surahName"],
                }
                answers = []
                for j in range(i + 1, min(i + 3, len(verses))):
                    answers.append({
                        "verse_id": verses[j]["id"],
                        "text": verses[j]["text"],
                    })
                pair["following_verses"] = answers
                results.append(pair)

    return results


# ══════════════════════════════════════════════════════════════════════════════
# Analysis 4: Word Pair Symmetries
# ══════════════════════════════════════════════════════════════════════════════

def count_word_symmetries(graph):
    """Count occurrences of thematic word pairs across all verses."""
    pair_counts = {f"{a}/{b}": {"a": a, "b": b, "count_a": 0, "count_b": 0,
                                 "verses_a": [], "verses_b": []}
                   for a, b in WORD_PAIRS}

    for vid, data in graph["verses"].items():
        text_lower = data["text"].lower()
        for a, b in WORD_PAIRS:
            key = f"{a}/{b}"
            if re.search(r'\b' + a + r'\w*\b', text_lower):
                pair_counts[key]["count_a"] += 1
                if len(pair_counts[key]["verses_a"]) < 5:
                    pair_counts[key]["verses_a"].append(vid)
            if re.search(r'\b' + b + r'\w*\b', text_lower):
                pair_counts[key]["count_b"] += 1
                if len(pair_counts[key]["verses_b"]) < 5:
                    pair_counts[key]["verses_b"].append(vid)

    results = []
    for key, data in pair_counts.items():
        ca, cb = data["count_a"], data["count_b"]
        ratio = min(ca, cb) / max(ca, cb) if max(ca, cb) > 0 else 0
        results.append({
            "pair": key,
            "word_a": data["a"],
            "word_b": data["b"],
            "count_a": ca,
            "count_b": cb,
            "ratio": round(ratio, 3),
            "sample_verses_a": data["verses_a"],
            "sample_verses_b": data["verses_b"],
        })

    results.sort(key=lambda x: -(x["count_a"] + x["count_b"]))
    return results


# ══════════════════════════════════════════════════════════════════════════════
# Save helper
# ══════════════════════════════════════════════════════════════════════════════

def save_json(data, filename):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


# ══════════════════════════════════════════════════════════════════════════════
# Main Loop
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Rhetorical pattern analysis loop")
    parser.add_argument("--max-hours", type=float, default=0,
                        help="Max hours to run (0=infinite)")
    args = parser.parse_args()

    print("Loading graph data...")
    graph = load_graph()
    print(f"  {len(graph['verses'])} verses loaded")

    surah_verses = get_surah_verses(graph)
    print(f"  {len(surah_verses)} surahs")

    start_time = time.time()
    deadline = start_time + args.max_hours * 3600 if args.max_hours > 0 else None

    ring_results = []
    rep_results = []
    qa_results = []
    sym_results = []
    rnd = 0

    while True:
        rnd += 1

        if deadline and time.time() > deadline:
            print(f"\nTime limit reached after {rnd - 1} rounds.")
            break

        # Ring compositions
        rings = detect_ring_compositions(surah_verses, graph["verse_keywords"])
        if rnd == 1 or len(rings) > len(ring_results):
            ring_results = rings

        # Repetition patterns (vary phrase length requirements)
        min_surahs = max(2, 3 + (rnd % 4))
        reps = find_repetition_patterns(graph, min_phrase_len=3,
                                         max_phrase_len=3 + (rnd % 3),
                                         min_surahs=min_surahs)
        seen_phrases = {r["phrase"] for r in rep_results}
        for r in reps:
            if r["phrase"] not in seen_phrases:
                rep_results.append(r)
                seen_phrases.add(r["phrase"])
        rep_results.sort(key=lambda x: (-x["num_surahs"], -x["num_occurrences"]))
        rep_results = rep_results[:1000]

        # QA pairs and symmetries (deterministic, run once)
        if rnd == 1:
            qa_results = find_question_answer_pairs(surah_verses)
            sym_results = count_word_symmetries(graph)

        # Progress every 5 rounds
        if rnd % 5 == 0 or rnd == 1:
            elapsed = time.time() - start_time
            print(f"\n[Round {rnd}] {elapsed/60:.1f} min elapsed")
            print(f"  Ring compositions: {len(ring_results)} surahs with mirror patterns")
            print(f"  Repetition patterns: {len(rep_results)} repeated phrases")
            print(f"  Question-answer pairs: {len(qa_results)}")
            print(f"  Word pair symmetries: {len(sym_results)} pairs tracked")

            if ring_results:
                top = ring_results[0]
                print(f"  Top ring: {top['surahName']} (symmetry={top['symmetry_score']:.1f}%)")
            if sym_results:
                for s in sym_results[:3]:
                    print(f"  Symmetry: {s['pair']} = {s['count_a']} vs {s['count_b']}")

        # Save every 10 rounds
        if rnd % 10 == 0 or rnd == 1:
            save_json(ring_results, "ring_compositions.json")
            save_json(rep_results, "repetition_patterns.json")

            rhetorical = {
                "question_answer_pairs": qa_results,
                "word_symmetries": sym_results,
                "meta": {
                    "rounds_completed": rnd,
                    "elapsed_minutes": round((time.time() - start_time) / 60, 1),
                },
            }
            save_json(rhetorical, "rhetorical_structures.json")
            print(f"  [Saved all 3 JSON files]")

        if rnd > 20:
            time.sleep(2)

    # Final save
    save_json(ring_results, "ring_compositions.json")
    save_json(rep_results, "repetition_patterns.json")
    rhetorical = {
        "question_answer_pairs": qa_results,
        "word_symmetries": sym_results,
        "meta": {
            "rounds_completed": rnd,
            "elapsed_minutes": round((time.time() - start_time) / 60, 1),
        },
    }
    save_json(rhetorical, "rhetorical_structures.json")
    print(f"\nDone. {rnd} rounds, final files saved.")


if __name__ == "__main__":
    main()
