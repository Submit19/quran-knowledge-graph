"""
Intertextuality Analyzer — finds parallel passages, thematic bookends,
and compelling cross-surah connections.
Saves: parallel_passages.json, compelling_connections.json
"""

import argparse
import json
import os
import re
import time
from collections import Counter, defaultdict

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

NAMED_ENTITIES = {
    "moses", "abraham", "jesus", "noah", "joseph", "david", "solomon",
    "pharaoh", "mary", "adam", "lot", "jonah", "isaac", "ishmael",
    "jacob", "aaron", "job", "satan", "gabriel",
}

RESONANCE_KEYWORDS = {
    "mercy": 3, "hope": 3, "perseverance": 3, "patience": 3,
    "forgive": 3, "compassion": 3, "love": 3, "peace": 2,
    "comfort": 3, "trust": 2, "grateful": 2, "grace": 3,
    "redeem": 3, "save": 2, "bless": 2, "light": 2,
    "guide": 2, "protect": 2, "sustain": 2, "heal": 3,
    "gentle": 2, "kindness": 3, "relief": 3, "strength": 2,
    "steadfast": 3, "endure": 2, "overcome": 2,
}


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
# Analysis 1: Parallel Passages (shared named entities + word overlap)
# ══════════════════════════════════════════════════════════════════════════════

def find_parallel_passages(graph, surah_verses, entity_subset=None):
    """
    Find verse pairs that share a named entity AND have high word overlap,
    but come from different surahs.
    """
    entity_index = defaultdict(list)
    entities_to_check = entity_subset if entity_subset else NAMED_ENTITIES

    for vid, data in graph["verses"].items():
        text_lower = data["text"].lower()
        words = set(content_words(data["text"]))
        for entity in entities_to_check:
            if entity in text_lower:
                entity_index[entity].append({
                    "id": vid,
                    "surah": data["surah"],
                    "surahName": data["surahName"],
                    "words": words,
                    "text": data["text"],
                })

    results = []
    seen_pairs = set()

    for entity, verse_list in entity_index.items():
        for i in range(len(verse_list)):
            for j in range(i + 1, len(verse_list)):
                va, vb = verse_list[i], verse_list[j]
                if va["surah"] == vb["surah"]:
                    continue

                pair_key = tuple(sorted([va["id"], vb["id"]]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                shared = va["words"] & vb["words"]
                union = va["words"] | vb["words"]
                if not union:
                    continue
                overlap = len(shared) / len(union)

                if overlap > 0.1 and len(shared) >= 3:
                    results.append({
                        "entity": entity,
                        "verse_a": va["id"],
                        "verse_b": vb["id"],
                        "surah_a": f"{va['surah']} ({va['surahName']})",
                        "surah_b": f"{vb['surah']} ({vb['surahName']})",
                        "shared_words": sorted(shared)[:15],
                        "overlap_score": round(overlap, 3),
                        "text_a": va["text"][:200],
                        "text_b": vb["text"][:200],
                    })

                if len(results) > 2000:
                    break
            if len(results) > 2000:
                break

    results.sort(key=lambda x: -x["overlap_score"])
    return results[:500]


# ══════════════════════════════════════════════════════════════════════════════
# Analysis 2: Thematic Bookends
# ══════════════════════════════════════════════════════════════════════════════

def find_thematic_bookends(surah_verses, n_verses=3):
    """
    Find surahs where the first N and last N verses share significant keywords,
    creating a thematic 'bookend' or inclusio structure.
    """
    results = []

    for surah_id, verses in surah_verses.items():
        if len(verses) < n_verses * 2 + 2:
            continue

        name = verses[0]["surahName"]

        first_words = set()
        for v in verses[:n_verses]:
            first_words.update(content_words(v["text"]))

        last_words = set()
        for v in verses[-n_verses:]:
            last_words.update(content_words(v["text"]))

        shared = first_words & last_words
        union = first_words | last_words
        if not union or not shared:
            continue

        jaccard = len(shared) / len(union)

        if len(shared) >= 2:
            results.append({
                "surah": surah_id,
                "surahName": name,
                "num_verses": len(verses),
                "first_verses": [v["id"] for v in verses[:n_verses]],
                "last_verses": [v["id"] for v in verses[-n_verses:]],
                "shared_keywords": sorted(shared)[:15],
                "num_shared": len(shared),
                "similarity": round(jaccard, 4),
                "first_text": " ".join(v["text"] for v in verses[:n_verses])[:300],
                "last_text": " ".join(v["text"] for v in verses[-n_verses:])[:300],
            })

    results.sort(key=lambda x: -x["similarity"])
    return results


# ══════════════════════════════════════════════════════════════════════════════
# Analysis 3: Compelling Connections
# ══════════════════════════════════════════════════════════════════════════════

def find_compelling_connections(graph, surah_verses, round_num=0):
    """
    Find surprising cross-surah links that are emotionally resonant.
    Uses the relatedness graph + resonance keyword scoring.
    """
    results = []

    # Score each verse for emotional resonance
    verse_resonance = {}
    for vid, data in graph["verses"].items():
        text_lower = data["text"].lower()
        score = 0
        matched_kw = []
        for kw, weight in RESONANCE_KEYWORDS.items():
            if kw in text_lower:
                score += weight
                matched_kw.append(kw)
        if score > 0:
            verse_resonance[vid] = {
                "score": score,
                "keywords": matched_kw,
                "text": data["text"],
                "surah": data["surah"],
                "surahName": data["surahName"],
            }

    # Find cross-surah related pairs where BOTH verses are resonant
    seen = set()
    verse_list = sorted(verse_resonance.keys())
    start_offset = (round_num * 100) % max(1, len(verse_list))
    ordered = verse_list[start_offset:] + verse_list[:start_offset]

    for vid in ordered:
        vr = verse_resonance[vid]
        related = graph["related"].get(vid, [])

        for related_id, rel_score in related[:15]:
            if related_id not in verse_resonance:
                continue
            rr = verse_resonance[related_id]

            if vr["surah"] == rr["surah"]:
                continue

            pair_key = tuple(sorted([vid, related_id]))
            if pair_key in seen:
                continue
            seen.add(pair_key)

            combined_resonance = vr["score"] + rr["score"]
            shared_kw = set(vr["keywords"]) & set(rr["keywords"])

            kw_a = set(kw for kw, _ in graph["verse_keywords"].get(vid, []))
            kw_b = set(kw for kw, _ in graph["verse_keywords"].get(related_id, []))
            bridge_kw = kw_a & kw_b

            results.append({
                "verse_a": vid,
                "verse_b": related_id,
                "surah_a": f"{vr['surah']} ({vr['surahName']})",
                "surah_b": f"{rr['surah']} ({rr['surahName']})",
                "text_a": vr["text"][:250],
                "text_b": rr["text"][:250],
                "resonance_score": combined_resonance,
                "relatedness_score": round(rel_score, 3),
                "resonance_keywords_a": vr["keywords"],
                "resonance_keywords_b": rr["keywords"],
                "shared_resonance": sorted(shared_kw),
                "bridge_keywords": sorted(bridge_kw)[:10],
                "combined_score": round(combined_resonance * rel_score, 2),
            })

        if len(results) > 3000:
            break

    results.sort(key=lambda x: -x["combined_score"])
    return results[:500]


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
    parser = argparse.ArgumentParser(description="Intertextuality analysis loop")
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

    parallel_results = []
    bookend_results = []
    compelling_results = []
    rnd = 0

    entity_list = sorted(NAMED_ENTITIES)

    while True:
        rnd += 1

        if deadline and time.time() > deadline:
            print(f"\nTime limit reached after {rnd - 1} rounds.")
            break

        # Parallel passages: rotate entity subsets
        batch_size = max(3, len(entity_list) // 4)
        offset = ((rnd - 1) * batch_size) % len(entity_list)
        entity_batch = entity_list[offset:offset + batch_size]
        if not entity_batch:
            entity_batch = entity_list[:batch_size]

        new_parallels = find_parallel_passages(graph, surah_verses,
                                                entity_subset=entity_batch)
        seen_keys = {(p["verse_a"], p["verse_b"]) for p in parallel_results}
        for p in new_parallels:
            key = (p["verse_a"], p["verse_b"])
            if key not in seen_keys:
                parallel_results.append(p)
                seen_keys.add(key)
        parallel_results.sort(key=lambda x: -x["overlap_score"])
        parallel_results = parallel_results[:1000]

        # Bookends: vary N each round
        n_v = 2 + (rnd % 4)
        new_bookends = find_thematic_bookends(surah_verses, n_verses=n_v)
        if rnd == 1 or len(new_bookends) > len(bookend_results):
            bookend_results = new_bookends

        # Compelling connections: rotated start point each round
        new_compelling = find_compelling_connections(graph, surah_verses,
                                                     round_num=rnd)
        seen_comp = {(c["verse_a"], c["verse_b"]) for c in compelling_results}
        for c in new_compelling:
            key = (c["verse_a"], c["verse_b"])
            if key not in seen_comp:
                compelling_results.append(c)
                seen_comp.add(key)
        compelling_results.sort(key=lambda x: -x["combined_score"])
        compelling_results = compelling_results[:1000]

        # Progress every 5 rounds
        if rnd % 5 == 0 or rnd == 1:
            elapsed = time.time() - start_time
            print(f"\n[Round {rnd}] {elapsed/60:.1f} min elapsed")
            print(f"  Parallel passages: {len(parallel_results)}")
            print(f"  Thematic bookends: {len(bookend_results)} surahs")
            print(f"  Compelling connections: {len(compelling_results)}")

            if parallel_results:
                top = parallel_results[0]
                print(f"  Top parallel: {top['verse_a']} <-> {top['verse_b']} "
                      f"({top['entity']}, overlap={top['overlap_score']:.3f})")
            if compelling_results:
                top = compelling_results[0]
                print(f"  Top compelling: {top['verse_a']} <-> {top['verse_b']} "
                      f"(score={top['combined_score']:.1f})")

        # Save every 10 rounds
        if rnd % 10 == 0 or rnd == 1:
            save_json(parallel_results, "parallel_passages.json")

            compelling_output = {
                "bookends": bookend_results,
                "connections": compelling_results,
                "meta": {
                    "rounds_completed": rnd,
                    "elapsed_minutes": round((time.time() - start_time) / 60, 1),
                },
            }
            save_json(compelling_output, "compelling_connections.json")
            print(f"  [Saved JSON files]")

        if rnd > 20:
            time.sleep(2)

    # Final save
    save_json(parallel_results, "parallel_passages.json")
    compelling_output = {
        "bookends": bookend_results,
        "connections": compelling_results,
        "meta": {
            "rounds_completed": rnd,
            "elapsed_minutes": round((time.time() - start_time) / 60, 1),
        },
    }
    save_json(compelling_output, "compelling_connections.json")
    print(f"\nDone. {rnd} rounds, final files saved.")


if __name__ == "__main__":
    main()
