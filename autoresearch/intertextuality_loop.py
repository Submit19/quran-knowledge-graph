"""
Intertextuality Analysis Loop for the Quran Knowledge Graph.

Finds cross-references and echoes within the Quran: parallel passages,
thematic bookends, and compelling cross-surah connections.
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

STOP_WORDS = {
    "the", "of", "and", "to", "in", "a", "is", "that", "for", "it", "with",
    "was", "on", "are", "be", "this", "have", "from", "or", "an", "they",
    "which", "you", "not", "but", "had", "his", "her", "has", "their", "all",
    "been", "if", "will", "who", "do", "shall", "them", "he", "she", "we",
    "no", "so", "by", "as", "at", "your", "what", "when", "upon", "did",
    "those", "then", "there", "may", "would", "its", "any", "into", "said",
}

NAMED_ENTITIES = {
    "moses", "abraham", "jesus", "noah", "joseph", "david", "solomon",
    "pharaoh", "mary", "adam", "lot", "jonah", "isaac", "ishmael",
    "jacob", "aaron", "job", "satan", "gabriel", "michael",
}

COMPELLING_KEYWORDS = {
    "mercy": {"mercy", "merciful", "compassion", "compassionate", "grace", "gracious"},
    "hope": {"hope", "glad", "tidings", "promise", "reward", "paradise", "garden"},
    "perseverance": {"patience", "patient", "steadfast", "endure", "persevere", "strive"},
    "redemption": {"forgive", "forgiveness", "repent", "repentance", "redeem", "pardon"},
    "justice": {"justice", "just", "fair", "equitable", "oppression", "oppress"},
    "love": {"love", "beloved", "devotion", "devote", "affection"},
    "gratitude": {"grateful", "gratitude", "thankful", "appreciate", "praise"},
}


def content_words(text):
    return [w for w in re.findall(r"[a-z']+", text.lower())
            if w not in STOP_WORDS and len(w) > 2]


def group_by_surah(verses):
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
# Analysis 1: Parallel Passages (shared named entities + word overlap)
# ══════════════════════════════════════════════════════════════════════════════

def find_parallel_passages(verses, batch_start=0, batch_size=2000):
    """Find verse pairs sharing named entities and high content word overlap."""
    # Index verses by named entity
    entity_index = defaultdict(list)
    for vid, info in verses.items():
        text_lower = info["text"].lower()
        for entity in NAMED_ENTITIES:
            if entity in text_lower:
                entity_index[entity].append(vid)

    results = []
    seen_pairs = set()

    entities = sorted(entity_index.keys())
    for entity in entities:
        vids = entity_index[entity]
        # Sample pairs within this entity group
        subset = vids[batch_start:batch_start + batch_size]
        for i in range(len(subset)):
            for j in range(i + 1, min(i + 50, len(subset))):
                v1, v2 = subset[i], subset[j]
                # Skip same surah
                if verses[v1]["surah"] == verses[v2]["surah"]:
                    continue
                pair_key = tuple(sorted([v1, v2]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                w1 = set(content_words(verses[v1]["text"]))
                w2 = set(content_words(verses[v2]["text"]))
                overlap = w1 & w2
                if len(overlap) < 3:
                    continue

                jaccard = len(overlap) / len(w1 | w2) if (w1 | w2) else 0
                results.append({
                    "verse1": v1,
                    "verse2": v2,
                    "shared_entity": entity,
                    "surah1": verses[v1]["surahName"],
                    "surah2": verses[v2]["surahName"],
                    "overlap_words": sorted(overlap),
                    "overlap_count": len(overlap),
                    "jaccard": round(jaccard, 3),
                    "text1": verses[v1]["text"][:150],
                    "text2": verses[v2]["text"][:150],
                })

    results.sort(key=lambda x: -x["overlap_count"])
    return results


# ══════════════════════════════════════════════════════════════════════════════
# Analysis 2: Thematic Bookends
# ══════════════════════════════════════════════════════════════════════════════

def find_thematic_bookends(surahs, n_verses=3):
    """Find surahs where first N and last N verses share keywords."""
    results = []

    for surah_num, verse_list in surahs.items():
        if len(verse_list) < n_verses * 2 + 1:
            continue

        first_n = verse_list[:n_verses]
        last_n = verse_list[-n_verses:]

        first_words = set()
        for vid, info in first_n:
            first_words.update(content_words(info["text"]))

        last_words = set()
        for vid, info in last_n:
            last_words.update(content_words(info["text"]))

        shared = first_words & last_words
        if len(shared) < 2:
            continue

        total_unique = len(first_words | last_words)
        overlap_ratio = len(shared) / total_unique if total_unique > 0 else 0

        results.append({
            "surah": surah_num,
            "surah_name": verse_list[0][1]["surahName"],
            "total_verses": len(verse_list),
            "bookend_size": n_verses,
            "shared_keywords": sorted(shared)[:20],
            "shared_count": len(shared),
            "overlap_ratio": round(overlap_ratio, 3),
            "first_verses": [vid for vid, _ in first_n],
            "last_verses": [vid for vid, _ in last_n],
        })

    results.sort(key=lambda x: -x["shared_count"])
    return results


# ══════════════════════════════════════════════════════════════════════════════
# Analysis 3: Compelling Cross-Surah Connections
# ══════════════════════════════════════════════════════════════════════════════

def find_compelling_connections(verses, related, verse_keywords, batch_offset=0, batch_size=500):
    """Find emotionally resonant cross-surah links through mercy/hope/perseverance."""
    # Build per-verse theme tags
    verse_themes = {}
    for vid, info in verses.items():
        text_lower = info["text"].lower()
        themes = []
        for theme, kw_set in COMPELLING_KEYWORDS.items():
            if any(kw in text_lower for kw in kw_set):
                themes.append(theme)
        if themes:
            verse_themes[vid] = themes

    results = []
    themed_vids = list(verse_themes.keys())
    subset = themed_vids[batch_offset:batch_offset + batch_size]

    for vid in subset:
        v_themes = set(verse_themes[vid])
        v_surah = verses[vid]["surah"]

        # Check related verses for shared compelling themes
        neighbors = related.get(vid, [])
        for neighbor_id, score in neighbors[:20]:
            if neighbor_id not in verse_themes:
                continue
            n_surah = verses.get(neighbor_id, {}).get("surah", "")
            if n_surah == v_surah:
                continue

            n_themes = set(verse_themes[neighbor_id])
            shared_themes = v_themes & n_themes
            if not shared_themes:
                continue

            # Compute word overlap for substance
            w1 = set(content_words(verses[vid]["text"]))
            w2 = set(content_words(verses[neighbor_id]["text"]))
            overlap = w1 & w2

            # Get shared graph keywords
            kw1 = set(kw for kw, _ in verse_keywords.get(vid, []))
            kw2 = set(kw for kw, _ in verse_keywords.get(neighbor_id, []))
            shared_kw = kw1 & kw2

            results.append({
                "verse1": vid,
                "verse2": neighbor_id,
                "surah1": verses[vid]["surahName"],
                "surah2": verses[neighbor_id]["surahName"],
                "shared_themes": sorted(shared_themes),
                "graph_score": round(score, 3),
                "word_overlap": sorted(overlap)[:10],
                "shared_keywords": sorted(shared_kw)[:10],
                "text1": verses[vid]["text"][:150],
                "text2": verses[neighbor_id]["text"][:150],
                "resonance_score": round(score * len(shared_themes) * (1 + len(overlap) * 0.1), 2),
            })

    results.sort(key=lambda x: -x["resonance_score"])
    return results


# ══════════════════════════════════════════════════════════════════════════════
# Main Loop
# ══════════════════════════════════════════════════════════════════════════════

def run_loop(max_hours=0):
    print("=" * 70)
    print("  INTERTEXTUALITY ANALYSIS LOOP")
    print("=" * 70)

    print("\nLoading graph data...")
    graph = load_graph()
    verses = graph["verses"]
    related = graph["related"]
    verse_keywords = graph["verse_keywords"]
    surahs = group_by_surah(verses)
    print(f"  {len(verses)} verses in {len(surahs)} surahs")

    start_time = time.time()
    rnd = 0

    parallel_results = []
    bookend_results = []
    compelling_results = []

    parallel_seen = set()
    compelling_seen = set()

    while True:
        rnd += 1
        elapsed_h = (time.time() - start_time) / 3600
        if max_hours > 0 and elapsed_h >= max_hours:
            print(f"\nTime limit reached ({max_hours}h). Stopping.")
            break

        if rnd % 3 == 1:
            # Parallel passages with shifting batch window
            batch_start = ((rnd - 1) // 3) * 200
            parallels = find_parallel_passages(verses, batch_start=batch_start, batch_size=2000)
            for p in parallels:
                key = (p["verse1"], p["verse2"])
                if key not in parallel_seen:
                    parallel_seen.add(key)
                    parallel_results.append(p)

        elif rnd % 3 == 2:
            # Bookends with varying window size
            n = 3 + (rnd // 6) % 4  # 3, 4, 5, 6 verses
            bookends = find_thematic_bookends(surahs, n_verses=n)
            # Merge: keep best per surah
            existing = {b["surah"]: b for b in bookend_results}
            for b in bookends:
                if b["surah"] not in existing or b["shared_count"] > existing[b["surah"]]["shared_count"]:
                    existing[b["surah"]] = b
            bookend_results = sorted(existing.values(), key=lambda x: -x["shared_count"])

        else:
            # Compelling connections with shifting offset
            offset = ((rnd - 1) // 3) * 300
            comps = find_compelling_connections(verses, related, verse_keywords,
                                               batch_offset=offset, batch_size=500)
            for c in comps:
                key = tuple(sorted([c["verse1"], c["verse2"]]))
                if key not in compelling_seen:
                    compelling_seen.add(key)
                    compelling_results.append(c)

        # Progress report every 6 rounds
        if rnd % 6 == 0:
            print(f"\n  [Round {rnd}] {elapsed_h:.2f}h elapsed")
            print(f"    Parallel passages: {len(parallel_results)}")
            print(f"    Thematic bookends: {len(bookend_results)}")
            print(f"    Compelling connections: {len(compelling_results)}")

        # Save every 9 rounds
        if rnd % 9 == 0 or rnd == 3:
            parallel_results.sort(key=lambda x: -x["overlap_count"])
            save_json("parallel_passages.json", parallel_results[:1000])

            compelling_results.sort(key=lambda x: -x["resonance_score"])
            save_json("compelling_connections.json", {
                "bookends": bookend_results[:200],
                "compelling_links": compelling_results[:1000],
                "rounds_completed": rnd,
                "elapsed_hours": round(elapsed_h, 2),
            })
            if rnd == 3:
                print(f"\n  [Round {rnd}] Initial save complete.")
            else:
                print(f"    -> Saved results to JSON files")

    # Final save
    parallel_results.sort(key=lambda x: -x["overlap_count"])
    p1 = save_json("parallel_passages.json", parallel_results[:1000])

    compelling_results.sort(key=lambda x: -x["resonance_score"])
    p2 = save_json("compelling_connections.json", {
        "bookends": bookend_results[:200],
        "compelling_links": compelling_results[:1000],
        "rounds_completed": rnd,
        "elapsed_hours": round((time.time() - start_time) / 3600, 2),
    })
    print(f"\nFinal results saved:")
    print(f"  {p1}")
    print(f"  {p2}")
    print(f"  Total rounds: {rnd}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Intertextuality analysis loop")
    parser.add_argument("--max-hours", type=float, default=0,
                        help="Maximum hours to run (0=infinite)")
    args = parser.parse_args()
    run_loop(max_hours=args.max_hours)
