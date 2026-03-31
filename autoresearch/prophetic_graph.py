"""
Prophetic Story Graph Builder for the Quran Knowledge Graph.

Builds comprehensive "story graphs" for each named prophet/entity in the Quran,
identifying verse inventories, surah distributions, story events, parallel
tellings across surahs, progressive detail analysis, and narrative statistics.

One-shot script: run once, saves results to prophetic_stories.json and
prophetic_summary.md.
"""

import json
import os
import re
import sys
from collections import defaultdict, Counter

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
AUTO_DIR = os.path.join(BASE_DIR, "autoresearch")

VERSES_JSON = os.path.join(DATA_DIR, "verses.json")
PARALLEL_JSON = os.path.join(AUTO_DIR, "parallel_passages.json")
OUTPUT_JSON = os.path.join(AUTO_DIR, "prophetic_stories.json")
OUTPUT_MD = os.path.join(AUTO_DIR, "prophetic_summary.md")

# ---------------------------------------------------------------------------
# Entity definitions: canonical key -> list of name variants to search for
# ---------------------------------------------------------------------------

ENTITIES = {
    "moses":    ["Moses"],
    "abraham":  ["Abraham"],
    "noah":     ["Noah"],
    "jesus":    ["Jesus"],
    "joseph":   ["Joseph"],
    "david":    ["David"],
    "solomon":  ["Solomon"],
    "lot":      ["Lot"],
    "adam":      ["Adam"],
    "jonah":    ["Jonah"],
    "job":      ["Job"],
    "elijah":   ["Elias", "Elijah"],
    "elisha":   ["Elisha"],
    "ishmael":  ["Ishmael", "Ismail"],
    "isaac":    ["Isaac"],
    "jacob":    ["Jacob"],
    "aaron":    ["Aaron"],
    "mary":     ["Mary"],
    "pharaoh":  ["Pharaoh"],
}

# Stopwords for keyword extraction
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "not",
    "no", "nor", "so", "if", "then", "than", "that", "this", "these",
    "those", "it", "its", "he", "his", "him", "she", "her", "they",
    "them", "their", "we", "us", "our", "you", "your", "who", "whom",
    "which", "what", "when", "where", "how", "why", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such",
    "only", "own", "same", "too", "very", "just", "about", "above",
    "after", "before", "between", "into", "through", "during", "out",
    "up", "down", "over", "under", "again", "further", "once", "here",
    "there", "also", "even", "still", "upon", "said", "say", "says",
    "saying", "unto", "let", "made", "make", "go", "went", "came",
    "come", "one", "two", "among", "against",
}


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_verses():
    """Load verses from verses.json."""
    with open(VERSES_JSON, encoding="utf-8") as f:
        return json.load(f)


def load_parallel_passages():
    """Load parallel passages if available."""
    if not os.path.exists(PARALLEL_JSON):
        return []
    with open(PARALLEL_JSON, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------

def extract_keywords(text, min_len=3):
    """Extract meaningful words from text."""
    words = re.findall(r"[a-zA-Z']+", text.lower())
    return [w for w in words if len(w) >= min_len and w not in STOPWORDS]


def jaccard(set_a, set_b):
    """Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


# ---------------------------------------------------------------------------
# Step 1: Verse inventory per entity
# ---------------------------------------------------------------------------

def build_verse_inventories(verses):
    """Find all verses mentioning each entity."""
    inventories = {key: [] for key in ENTITIES}

    for v in verses:
        text = v["text"]
        vid = v["verse_id"]
        surah = v["surah"]
        for entity_key, name_variants in ENTITIES.items():
            for name in name_variants:
                # Word-boundary match to avoid partial matches
                # (e.g., "Job" shouldn't match "job" as in employment
                #  but Quran text capitalises proper names so exact match works)
                pattern = r'\b' + re.escape(name) + r'\b'
                if re.search(pattern, text):
                    inventories[entity_key].append({
                        "verse_id": vid,
                        "surah": surah,
                        "surah_name": v.get("surah_name", ""),
                        "text": text,
                    })
                    break  # don't double-count if multiple variants match

    return inventories


# ---------------------------------------------------------------------------
# Step 2: Surah distribution
# ---------------------------------------------------------------------------

def compute_surah_distribution(entity_verses):
    """Count verses per surah for an entity."""
    dist = Counter()
    for v in entity_verses:
        dist[str(v["surah"])] += 1
    return dict(dist.most_common())


# ---------------------------------------------------------------------------
# Step 3: Story event clustering
# ---------------------------------------------------------------------------

def cluster_events(entity_verses, entity_name, min_cluster=2, similarity_threshold=0.25):
    """
    Cluster verses about an entity into story events using keyword overlap.
    Uses a simple greedy agglomerative approach.
    """
    if len(entity_verses) < min_cluster:
        return []

    # Extract keywords for each verse
    verse_kws = []
    for v in entity_verses:
        kws = set(extract_keywords(v["text"]))
        # Remove the entity's own name variants from keywords
        for name in ENTITIES.get(entity_name, []):
            kws.discard(name.lower())
        verse_kws.append(kws)

    # Greedy clustering: assign each verse to the best existing cluster
    # or create a new one
    clusters = []  # list of {"verse_indices": [], "keywords": set()}

    for i, kws in enumerate(verse_kws):
        best_cluster = None
        best_sim = similarity_threshold

        for ci, cluster in enumerate(clusters):
            sim = jaccard(kws, cluster["keywords"])
            if sim > best_sim:
                best_sim = sim
                best_cluster = ci

        if best_cluster is not None:
            clusters[best_cluster]["verse_indices"].append(i)
            clusters[best_cluster]["keywords"] |= kws
        else:
            clusters.append({
                "verse_indices": [i],
                "keywords": set(kws),
            })

    # Filter tiny clusters and name them
    events = []
    for cluster in clusters:
        if len(cluster["verse_indices"]) < min_cluster:
            continue

        # Pick the top keywords as the event name
        # Count keyword frequency within the cluster
        kw_freq = Counter()
        for idx in cluster["verse_indices"]:
            for kw in verse_kws[idx]:
                kw_freq[kw] += 1

        top_kws = [kw for kw, _ in kw_freq.most_common(5)]
        event_name = "_".join(top_kws[:3])

        event_verses = [entity_verses[i]["verse_id"] for i in cluster["verse_indices"]]

        events.append({
            "name": event_name,
            "verses": event_verses,
            "keywords": top_kws,
            "verse_count": len(event_verses),
        })

    # Sort by verse count descending
    events.sort(key=lambda e: e["verse_count"], reverse=True)
    return events


# ---------------------------------------------------------------------------
# Step 4: Parallel tellings
# ---------------------------------------------------------------------------

def find_parallel_tellings(events, entity_verses, parallel_data, entity_name):
    """
    Group events that appear across multiple surahs. Use parallel_passages.json
    data where available, otherwise compute Jaccard similarity.
    """
    # Build a lookup of known parallels for this entity
    known_parallels = defaultdict(list)
    for entry in parallel_data:
        if entry.get("entity", "").lower() == entity_name:
            known_parallels[entry["verse_a"]].append(entry["verse_b"])
            known_parallels[entry["verse_b"]].append(entry["verse_a"])

    # Build verse_id -> verse data lookup
    verse_lookup = {v["verse_id"]: v for v in entity_verses}

    parallels = []
    for event in events:
        # Group event verses by surah
        surah_groups = defaultdict(list)
        for vid in event["verses"]:
            v = verse_lookup.get(vid)
            if v:
                surah_groups[str(v["surah"])].append(vid)

        if len(surah_groups) < 2:
            continue

        tellings = []
        for surah_id, vids in sorted(surah_groups.items(), key=lambda x: len(x[1]), reverse=True):
            tellings.append({
                "surah": int(surah_id),
                "verses": sorted(vids, key=lambda x: (int(x.split(":")[0]), int(x.split(":")[1]))),
                "verse_count": len(vids),
            })

        parallels.append({
            "event": event["name"],
            "keywords": event["keywords"],
            "tellings": tellings,
            "num_surahs": len(tellings),
        })

    # Sort by number of parallel surahs
    parallels.sort(key=lambda p: p["num_surahs"], reverse=True)
    return parallels


# ---------------------------------------------------------------------------
# Step 5: Progressive detail analysis
# ---------------------------------------------------------------------------

def analyze_progressive_detail(parallels, entity_verses):
    """
    For each parallel event told in multiple surahs, identify what each
    version adds or omits compared to others.
    """
    verse_lookup = {v["verse_id"]: v for v in entity_verses}

    for parallel in parallels:
        # Collect all words used across all tellings
        telling_words = []
        all_words = set()
        for telling in parallel["tellings"]:
            words = set()
            for vid in telling["verses"]:
                v = verse_lookup.get(vid)
                if v:
                    words |= set(extract_keywords(v["text"]))
            telling_words.append(words)
            all_words |= words

        # For each telling, find unique content (words not in any other telling)
        for i, telling in enumerate(parallel["tellings"]):
            other_words = set()
            for j, tw in enumerate(telling_words):
                if j != i:
                    other_words |= tw
            unique = telling_words[i] - other_words
            shared = telling_words[i] & other_words
            telling["unique_words"] = sorted(unique)[:15]
            telling["unique_word_count"] = len(unique)
            telling["shared_word_count"] = len(shared)

    return parallels


# ---------------------------------------------------------------------------
# Step 6: Story statistics and cross-prophet connections
# ---------------------------------------------------------------------------

def compute_connections(inventories):
    """Compute how many verses are shared between entity pairs."""
    connections = {}
    entity_keys = list(inventories.keys())

    for i, key_a in enumerate(entity_keys):
        verse_ids_a = set(v["verse_id"] for v in inventories[key_a])
        conn = {}
        for j, key_b in enumerate(entity_keys):
            if key_a == key_b:
                continue
            verse_ids_b = set(v["verse_id"] for v in inventories[key_b])
            shared = len(verse_ids_a & verse_ids_b)
            if shared > 0:
                conn[key_b] = shared
        # Sort by count descending
        connections[key_a] = dict(sorted(conn.items(), key=lambda x: x[1], reverse=True))

    return connections


def compute_stats(entity_key, entity_verses, events, parallels, connections):
    """Compute summary statistics for one entity."""
    surah_dist = compute_surah_distribution(entity_verses)

    most_detailed_surah = None
    if surah_dist:
        most_detailed_surah = int(max(surah_dist, key=surah_dist.get))

    # Most unique details: which telling across all parallels adds the most
    most_unique_telling = None
    max_unique = 0
    for par in parallels:
        for telling in par["tellings"]:
            uc = telling.get("unique_word_count", 0)
            if uc > max_unique:
                max_unique = uc
                most_unique_telling = {
                    "surah": telling["surah"],
                    "event": par["event"],
                    "unique_word_count": uc,
                }

    # Narrative centrality: total connections to other entities
    entity_conn = connections.get(entity_key, {})
    centrality = sum(entity_conn.values())

    return {
        "total_verses": len(entity_verses),
        "num_surahs": len(surah_dist),
        "most_detailed_surah": most_detailed_surah,
        "most_unique_telling": most_unique_telling,
        "narrative_centrality": centrality,
    }


# ---------------------------------------------------------------------------
# Build full prophetic graph
# ---------------------------------------------------------------------------

def build_prophetic_graph():
    """Main pipeline: build story graphs for all entities."""
    print("Loading verses...")
    verses = load_verses()
    print(f"  {len(verses)} verses loaded")

    print("Loading parallel passages...")
    parallel_data = load_parallel_passages()
    print(f"  {len(parallel_data)} parallel passage entries loaded")

    print("\nBuilding verse inventories...")
    inventories = build_verse_inventories(verses)
    for key in sorted(inventories, key=lambda k: len(inventories[k]), reverse=True):
        print(f"  {key:12s}: {len(inventories[key]):4d} verses")

    print("\nComputing cross-entity connections...")
    connections = compute_connections(inventories)

    print("\nBuilding story graphs...")
    results = {}

    for entity_key in ENTITIES:
        entity_verses = inventories[entity_key]
        if not entity_verses:
            results[entity_key] = {
                "total_verses": 0,
                "surahs": {},
                "events": [],
                "parallels": [],
                "most_detailed_surah": None,
                "connections_to": {},
            }
            continue

        # Surah distribution
        surah_dist = compute_surah_distribution(entity_verses)

        # Cluster into events
        events = cluster_events(entity_verses, entity_key)

        # Find parallel tellings
        parallels = find_parallel_tellings(events, entity_verses, parallel_data, entity_key)

        # Analyze progressive detail
        parallels = analyze_progressive_detail(parallels, entity_verses)

        # Stats
        stats = compute_stats(entity_key, entity_verses, events, parallels, connections)

        results[entity_key] = {
            "total_verses": stats["total_verses"],
            "surahs": surah_dist,
            "events": events,
            "parallels": parallels,
            "most_detailed_surah": stats["most_detailed_surah"],
            "most_unique_telling": stats["most_unique_telling"],
            "narrative_centrality": stats["narrative_centrality"],
            "num_surahs": stats["num_surahs"],
            "connections_to": connections.get(entity_key, {}),
        }

        n_events = len(events)
        n_par = len(parallels)
        print(f"  {entity_key:12s}: {n_events} events, {n_par} parallel tellings")

    return results


# ---------------------------------------------------------------------------
# Generate human-readable summary
# ---------------------------------------------------------------------------

def generate_summary(results):
    """Generate prophetic_summary.md."""
    lines = []
    lines.append("# Prophetic Story Graphs: Summary")
    lines.append("")
    lines.append("Auto-generated analysis of prophetic narratives in the Quran.")
    lines.append("")

    # -- Top 10 by verse count --
    lines.append("## Top 10 Prophets/Entities by Verse Count")
    lines.append("")
    ranked = sorted(results.items(), key=lambda x: x[1]["total_verses"], reverse=True)
    lines.append("| Rank | Entity | Verses | Surahs | Centrality |")
    lines.append("|------|--------|--------|--------|------------|")
    for i, (key, data) in enumerate(ranked[:10]):
        lines.append(
            f"| {i+1} | {key.title()} | {data['total_verses']} "
            f"| {data.get('num_surahs', len(data['surahs']))} "
            f"| {data.get('narrative_centrality', 0)} |"
        )
    lines.append("")

    # -- Most retold events --
    lines.append("## Most Retold Events (Appearing in Most Surahs)")
    lines.append("")
    all_parallels = []
    for key, data in results.items():
        for par in data.get("parallels", []):
            all_parallels.append({
                "entity": key,
                "event": par["event"],
                "num_surahs": par["num_surahs"],
                "keywords": par.get("keywords", []),
            })
    all_parallels.sort(key=lambda x: x["num_surahs"], reverse=True)

    lines.append("| Entity | Event | Surahs |")
    lines.append("|--------|-------|--------|")
    for par in all_parallels[:15]:
        kw_str = ", ".join(par["keywords"][:4])
        lines.append(f"| {par['entity'].title()} | {kw_str} | {par['num_surahs']} |")
    lines.append("")

    # -- Most variation across tellings --
    lines.append("## Most Variation Across Tellings")
    lines.append("")
    lines.append("Which entity has the most unique content across its parallel tellings?")
    lines.append("")

    variation_scores = []
    for key, data in results.items():
        total_unique = 0
        for par in data.get("parallels", []):
            for telling in par.get("tellings", []):
                total_unique += telling.get("unique_word_count", 0)
        if total_unique > 0:
            variation_scores.append((key, total_unique))
    variation_scores.sort(key=lambda x: x[1], reverse=True)

    lines.append("| Entity | Unique Words Across Tellings |")
    lines.append("|--------|------------------------------|")
    for key, score in variation_scores[:10]:
        lines.append(f"| {key.title()} | {score} |")
    lines.append("")

    # -- Cross-prophet connections --
    lines.append("## Interesting Cross-Prophet Connections")
    lines.append("")
    lines.append("Entity pairs that appear together in the most verses:")
    lines.append("")

    pairs_seen = set()
    all_pairs = []
    for key, data in results.items():
        for other, count in data.get("connections_to", {}).items():
            pair = tuple(sorted([key, other]))
            if pair not in pairs_seen:
                pairs_seen.add(pair)
                all_pairs.append((pair[0], pair[1], count))
    all_pairs.sort(key=lambda x: x[2], reverse=True)

    lines.append("| Entity A | Entity B | Shared Verses |")
    lines.append("|----------|----------|---------------|")
    for a, b, count in all_pairs[:15]:
        lines.append(f"| {a.title()} | {b.title()} | {count} |")
    lines.append("")

    # -- Per-entity highlights --
    lines.append("## Per-Entity Highlights")
    lines.append("")
    for key, data in ranked:
        if data["total_verses"] == 0:
            continue
        lines.append(f"### {key.title()}")
        lines.append("")
        lines.append(f"- **Total verses**: {data['total_verses']}")
        lines.append(f"- **Surahs**: {data.get('num_surahs', len(data['surahs']))}")
        lines.append(f"- **Most detailed surah**: {data['most_detailed_surah']}")

        top_conn = list(data.get("connections_to", {}).items())[:3]
        if top_conn:
            conn_str = ", ".join(f"{c.title()} ({n})" for c, n in top_conn)
            lines.append(f"- **Strongest connections**: {conn_str}")

        events = data.get("events", [])
        if events:
            event_names = [f"{e['name']} ({e['verse_count']}v)" for e in events[:5]]
            lines.append(f"- **Top events**: {', '.join(event_names)}")

        mu = data.get("most_unique_telling")
        if mu:
            lines.append(
                f"- **Most unique telling**: Surah {mu['surah']} "
                f"for event '{mu['event']}' ({mu['unique_word_count']} unique words)"
            )

        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    results = build_prophetic_graph()

    # Save JSON
    print(f"\nSaving results to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Generate and save markdown summary
    print(f"Generating summary at {OUTPUT_MD}...")
    summary = generate_summary(results)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(summary)

    print("\nDone.")
    print(f"  JSON: {OUTPUT_JSON}")
    print(f"  Summary: {OUTPUT_MD}")


if __name__ == "__main__":
    main()
