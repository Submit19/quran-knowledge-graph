"""
Linguistic Statistics Analyzer — infinite loop that computes per-surah stats,
word pair symmetries, and keyword co-occurrence networks.

Saves: surah_linguistics.json, word_symmetries.json, cooccurrence_network.json
"""

import argparse
import json
import os
import re
import time
from collections import Counter, defaultdict
from itertools import combinations

from deduction_engine import load_graph

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

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
    ("man", "woman"), ("day", "night"), ("land", "sea"),
    ("good", "evil"), ("light", "darkness"), ("reward", "punishment"),
    ("believer", "disbeliever"), ("rich", "poor"), ("mercy", "wrath"),
    ("paradise", "fire"), ("peace", "war"), ("truth", "falsehood"),
    ("love", "hate"), ("visible", "invisible"), ("world", "hereafter"),
    ("obey", "disobey"), ("create", "destroy"), ("remember", "forget"),
    ("patient", "hasty"), ("grateful", "ungrateful"), ("east", "west"),
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
# Analysis 1: Per-Surah Linguistic Statistics
# ══════════════════════════════════════════════════════════════════════════════

def compute_surah_stats(surah_verses):
    """Compute word count, unique words, TTR, avg word/verse length per surah."""
    results = []

    for surah_id, verses in surah_verses.items():
        name = verses[0]["surahName"]
        all_words = []
        verse_lengths = []

        for v in verses:
            words = tokenize(v["text"])
            all_words.extend(words)
            verse_lengths.append(len(words))

        total_words = len(all_words)
        unique_words = len(set(all_words))
        ttr = unique_words / total_words if total_words > 0 else 0

        word_lengths = [len(w) for w in all_words]
        avg_word_len = sum(word_lengths) / len(word_lengths) if word_lengths else 0
        avg_verse_len = sum(verse_lengths) / len(verse_lengths) if verse_lengths else 0

        # Top content words
        cwords = content_words(" ".join(v["text"] for v in verses))
        top_words = Counter(cwords).most_common(20)

        # Hapax legomena (words appearing exactly once)
        word_freq = Counter(all_words)
        hapax = sum(1 for w, c in word_freq.items() if c == 1)

        results.append({
            "surah": surah_id,
            "surahName": name,
            "num_verses": len(verses),
            "total_words": total_words,
            "unique_words": unique_words,
            "type_token_ratio": round(ttr, 4),
            "avg_word_length": round(avg_word_len, 2),
            "avg_verse_length": round(avg_verse_len, 2),
            "max_verse_length": max(verse_lengths) if verse_lengths else 0,
            "min_verse_length": min(verse_lengths) if verse_lengths else 0,
            "hapax_legomena": hapax,
            "hapax_ratio": round(hapax / total_words, 4) if total_words else 0,
            "top_content_words": [{"word": w, "count": c} for w, c in top_words],
        })

    results.sort(key=lambda x: int(x["surah"]))
    return results


# ══════════════════════════════════════════════════════════════════════════════
# Analysis 2: Word Pair Symmetries (whole-Quran counts)
# ══════════════════════════════════════════════════════════════════════════════

def compute_word_symmetries(graph, extra_pairs=None):
    """Count occurrences of word pairs across all verses, with stem matching."""
    pairs_to_check = list(WORD_PAIRS)
    if extra_pairs:
        pairs_to_check.extend(extra_pairs)

    pair_data = {}
    for a, b in pairs_to_check:
        key = f"{a}/{b}"
        pair_data[key] = {
            "word_a": a, "word_b": b,
            "count_a": 0, "count_b": 0,
            "verses_a": [], "verses_b": [],
            "co_occur_verses": [],
        }

    for vid, data in graph["verses"].items():
        text_lower = data["text"].lower()
        for a, b in pairs_to_check:
            key = f"{a}/{b}"
            found_a = bool(re.search(r'\b' + a + r'\w*\b', text_lower))
            found_b = bool(re.search(r'\b' + b + r'\w*\b', text_lower))

            if found_a:
                pair_data[key]["count_a"] += 1
                if len(pair_data[key]["verses_a"]) < 5:
                    pair_data[key]["verses_a"].append(vid)
            if found_b:
                pair_data[key]["count_b"] += 1
                if len(pair_data[key]["verses_b"]) < 5:
                    pair_data[key]["verses_b"].append(vid)
            if found_a and found_b:
                if len(pair_data[key]["co_occur_verses"]) < 5:
                    pair_data[key]["co_occur_verses"].append(vid)

    results = []
    for key, d in pair_data.items():
        ca, cb = d["count_a"], d["count_b"]
        ratio = min(ca, cb) / max(ca, cb) if max(ca, cb) > 0 else 0
        results.append({
            "pair": key,
            "word_a": d["word_a"],
            "word_b": d["word_b"],
            "count_a": ca,
            "count_b": cb,
            "ratio": round(ratio, 4),
            "total": ca + cb,
            "sample_verses_a": d["verses_a"],
            "sample_verses_b": d["verses_b"],
            "co_occurrence_verses": d["co_occur_verses"],
        })

    results.sort(key=lambda x: -x["total"])
    return results


# ══════════════════════════════════════════════════════════════════════════════
# Analysis 3: Keyword Co-occurrence Network
# ══════════════════════════════════════════════════════════════════════════════

def build_cooccurrence_network(graph, min_cooccur=5, top_keywords=200):
    """
    Build a co-occurrence network: which keywords appear together most
    often in the same verse?
    """
    # Find top keywords by frequency
    kw_freq = Counter()
    for kw, verse_list in graph["keyword_verses"].items():
        kw_freq[kw] = len(verse_list)

    top_kws = set(kw for kw, _ in kw_freq.most_common(top_keywords))

    # Build co-occurrence counts
    cooccur = Counter()
    verse_kw_sets = {}

    for vid, kw_list in graph["verse_keywords"].items():
        kws_in_verse = set(kw for kw, score in kw_list if kw in top_kws)
        verse_kw_sets[vid] = kws_in_verse
        for pair in combinations(sorted(kws_in_verse), 2):
            cooccur[pair] += 1

    # Build network
    nodes = []
    for kw in top_kws:
        nodes.append({
            "id": kw,
            "frequency": kw_freq[kw],
        })

    edges = []
    for (kw1, kw2), count in cooccur.most_common(2000):
        if count < min_cooccur:
            break
        edges.append({
            "source": kw1,
            "target": kw2,
            "weight": count,
        })

    # Compute per-keyword stats
    kw_partners = defaultdict(list)
    for (kw1, kw2), count in cooccur.items():
        if count >= min_cooccur:
            kw_partners[kw1].append({"keyword": kw2, "count": count})
            kw_partners[kw2].append({"keyword": kw1, "count": count})

    for kw in kw_partners:
        kw_partners[kw].sort(key=lambda x: -x["count"])
        kw_partners[kw] = kw_partners[kw][:10]

    top_hubs = sorted(kw_partners.items(), key=lambda x: -len(x[1]))[:30]
    hub_stats = [{"keyword": kw, "num_connections": len(partners),
                   "top_partners": partners[:5]}
                  for kw, partners in top_hubs]

    return {
        "nodes": nodes,
        "edges": edges,
        "hub_keywords": hub_stats,
        "num_nodes": len(nodes),
        "num_edges": len(edges),
    }


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
    parser = argparse.ArgumentParser(description="Linguistic statistics analysis loop")
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

    surah_stats = []
    symmetry_results = []
    cooccur_network = {}
    rnd = 0

    # Additional word pairs discovered across rounds
    discovered_pairs = []

    while True:
        rnd += 1

        if deadline and time.time() > deadline:
            print(f"\nTime limit reached after {rnd - 1} rounds.")
            break

        # Per-surah stats (deterministic, run once)
        if rnd == 1:
            surah_stats = compute_surah_stats(surah_verses)

        # Word symmetries: expand pair list each round
        extra = discovered_pairs[:rnd * 2] if discovered_pairs else None
        symmetry_results = compute_word_symmetries(graph, extra_pairs=extra)

        # Co-occurrence network: vary parameters
        min_co = max(2, 5 - (rnd % 3))
        top_kw = min(500, 150 + rnd * 20)
        cooccur_network = build_cooccurrence_network(graph, min_cooccur=min_co,
                                                      top_keywords=top_kw)

        # Discover new word pairs from co-occurrence data
        if cooccur_network.get("edges"):
            for edge in cooccur_network["edges"][:50]:
                pair = (edge["source"], edge["target"])
                if pair not in WORD_PAIRS and pair not in discovered_pairs:
                    discovered_pairs.append(pair)

        # Progress every 5 rounds
        if rnd % 5 == 0 or rnd == 1:
            elapsed = time.time() - start_time
            print(f"\n[Round {rnd}] {elapsed/60:.1f} min elapsed")
            print(f"  Surah stats: {len(surah_stats)} surahs analyzed")
            print(f"  Word symmetries: {len(symmetry_results)} pairs tracked")
            print(f"  Co-occurrence: {cooccur_network.get('num_nodes', 0)} nodes, "
                  f"{cooccur_network.get('num_edges', 0)} edges")
            print(f"  Discovered pairs: {len(discovered_pairs)}")

            # Print interesting stats
            if surah_stats:
                longest = max(surah_stats, key=lambda x: x["total_words"])
                highest_ttr = max(surah_stats, key=lambda x: x["type_token_ratio"])
                print(f"  Longest surah: {longest['surahName']} ({longest['total_words']} words)")
                print(f"  Highest TTR: {highest_ttr['surahName']} ({highest_ttr['type_token_ratio']:.3f})")

            if symmetry_results:
                for s in symmetry_results[:3]:
                    print(f"  Symmetry: {s['pair']} = {s['count_a']} vs {s['count_b']} "
                          f"(ratio={s['ratio']:.3f})")

            if cooccur_network.get("hub_keywords"):
                top_hub = cooccur_network["hub_keywords"][0]
                print(f"  Top hub keyword: '{top_hub['keyword']}' "
                      f"({top_hub['num_connections']} connections)")

        # Save every 10 rounds
        if rnd % 10 == 0 or rnd == 1:
            save_json(surah_stats, "surah_linguistics.json")
            save_json({
                "standard_pairs": symmetry_results,
                "discovered_pairs_count": len(discovered_pairs),
                "meta": {
                    "rounds_completed": rnd,
                    "elapsed_minutes": round((time.time() - start_time) / 60, 1),
                },
            }, "word_symmetries.json")
            save_json(cooccur_network, "cooccurrence_network.json")
            print(f"  [Saved all 3 JSON files]")

        if rnd > 20:
            time.sleep(2)

    # Final save
    save_json(surah_stats, "surah_linguistics.json")
    save_json({
        "standard_pairs": symmetry_results,
        "discovered_pairs_count": len(discovered_pairs),
        "meta": {
            "rounds_completed": rnd,
            "elapsed_minutes": round((time.time() - start_time) / 60, 1),
        },
    }, "word_symmetries.json")
    save_json(cooccur_network, "cooccurrence_network.json")
    print(f"\nDone. {rnd} rounds, final files saved.")


if __name__ == "__main__":
    main()
