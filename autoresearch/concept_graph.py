"""
Concept Dependency Graph Builder for the Quran Knowledge Graph.

Builds a directed graph of abstract Quranic concepts and their prerequisite
relationships, answering: "What must you understand before understanding X?"

Pipeline:
  1. Define ~40 core concepts with keyword signatures
  2. Match verses to concepts (threshold: 2+ keyword hits)
  3. Compute dependency edges via co-occurrence + sequential ordering bias
  4. Identify foundation concepts, advanced concepts, and learning paths
  5. Save to autoresearch/concept_graph.json
"""

import csv
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from itertools import combinations

csv.field_size_limit(sys.maxsize)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
AUTORESEARCH_DIR = os.path.dirname(os.path.abspath(__file__))


# ══════════════════════════════════════════════════════════════════════════════
# Core Quranic Concepts (~40 with keyword signatures)
# ══════════════════════════════════════════════════════════════════════════════

CONCEPTS = {
    # Foundational theology
    "monotheism": {
        "keywords": {"god", "one", "lord", "creator", "eternal", "sovereign", "almighty"},
        "description": "The oneness and supremacy of God (Tawhid)",
    },
    "prayer": {
        "keywords": {"salat", "contact", "prayer", "prostrate", "bow", "worship", "mosque"},
        "description": "Ritual prayer and worship (Salat)",
    },
    "charity": {
        "keywords": {"zakat", "charity", "give", "poor", "needy", "alms", "spend"},
        "description": "Obligatory and voluntary charity (Zakat/Sadaqah)",
    },
    "fasting": {
        "keywords": {"fast", "ramadan", "abstain", "dawn", "month"},
        "description": "Fasting during Ramadan and beyond (Sawm)",
    },
    "pilgrimage": {
        "keywords": {"hajj", "pilgrimage", "kaaba", "shrine", "mecca", "sacred"},
        "description": "Pilgrimage to Mecca (Hajj)",
    },
    "judgment_day": {
        "keywords": {"resurrection", "judgment", "day", "reckoning", "scale", "trumpet", "account"},
        "description": "The Day of Judgment and final reckoning",
    },
    "paradise": {
        "keywords": {"paradise", "garden", "river", "reward", "eternal", "heaven", "bliss"},
        "description": "Paradise and eternal reward (Jannah)",
    },
    "hell": {
        "keywords": {"hell", "fire", "punishment", "torment", "doom", "retribution"},
        "description": "Hellfire and divine punishment (Jahannam)",
    },
    "prophets": {
        "keywords": {"messenger", "prophet", "sent", "revelation", "mission"},
        "description": "The role and mission of prophets and messengers",
    },
    "scripture": {
        "keywords": {"quran", "book", "scripture", "torah", "gospel", "psalm", "recite"},
        "description": "Divine scriptures and revealed books",
    },
    "angels": {
        "keywords": {"angel", "gabriel", "guardian", "wing", "descend"},
        "description": "Angels and their roles in creation",
    },
    "satan": {
        "keywords": {"devil", "satan", "jinn", "evil", "whisper", "mislead"},
        "description": "Satan, jinn, and forces of evil",
    },
    "creation": {
        "keywords": {"create", "heavens", "earth", "universe", "fashion", "originate"},
        "description": "God's creation of the universe and all things",
    },
    "covenant": {
        "keywords": {"covenant", "promise", "pledge", "oath", "fulfill"},
        "description": "Divine covenants and sacred pledges",
    },
    "patience": {
        "keywords": {"patience", "perseverance", "steadfast", "endure", "forbear"},
        "description": "Patience and perseverance in faith (Sabr)",
    },
    "gratitude": {
        "keywords": {"grateful", "thankful", "appreciate", "praise", "glorify"},
        "description": "Gratitude toward God and appreciation of blessings",
    },
    "repentance": {
        "keywords": {"repent", "return", "forgive", "mercy", "pardon", "atone"},
        "description": "Repentance and seeking God's forgiveness (Tawbah)",
    },
    "justice": {
        "keywords": {"justice", "fair", "equity", "balance", "judge", "oppression"},
        "description": "Divine and social justice",
    },
    "truth": {
        "keywords": {"truth", "honest", "sincere", "upright", "falsehood", "lie"},
        "description": "Truth, honesty, and sincerity",
    },
    "free_will": {
        "keywords": {"choose", "will", "freedom", "test", "trial", "accountable"},
        "description": "Human free will, divine testing, and accountability",
    },
    # Additional 20 concepts
    "faith": {
        "keywords": {"believe", "faith", "trust", "conviction", "submit"},
        "description": "Belief and faith in God (Iman)",
    },
    "disbelief": {
        "keywords": {"disbelieve", "reject", "deny", "idol", "polytheist", "hypocrite"},
        "description": "Disbelief, idolatry, and hypocrisy (Kufr/Shirk)",
    },
    "moses_narrative": {
        "keywords": {"moses", "pharaoh", "egypt", "plague", "staff", "israelite"},
        "description": "The story of Moses and Pharaoh",
    },
    "abraham_narrative": {
        "keywords": {"abraham", "idol", "sacrifice", "ishmael", "isaac", "star"},
        "description": "The story of Abraham, father of monotheism",
    },
    "jesus_narrative": {
        "keywords": {"jesus", "mary", "miracle", "gospel", "disciple", "virgin"},
        "description": "The story of Jesus and Mary",
    },
    "noah_narrative": {
        "keywords": {"noah", "flood", "ark", "drown", "generation"},
        "description": "The story of Noah and the great flood",
    },
    "family_law": {
        "keywords": {"marry", "divorce", "wife", "husband", "dowry", "inherit"},
        "description": "Marriage, divorce, and family relations",
    },
    "economic_ethics": {
        "keywords": {"trade", "usury", "debt", "contract", "wealth", "property"},
        "description": "Economic principles and prohibition of usury",
    },
    "warfare": {
        "keywords": {"fight", "war", "strive", "battle", "defend", "persecute"},
        "description": "Rules of warfare and struggle (Jihad)",
    },
    "knowledge": {
        "keywords": {"knowledge", "wisdom", "learn", "teach", "understand", "reflect"},
        "description": "Knowledge, wisdom, and intellectual pursuit",
    },
    "human_nature": {
        "keywords": {"soul", "human", "clay", "spirit", "nafs", "desire"},
        "description": "Human nature, the soul, and inner struggle",
    },
    "community": {
        "keywords": {"nation", "community", "people", "tribe", "unity", "congregation"},
        "description": "The Muslim community and social cohesion (Ummah)",
    },
    "dietary_law": {
        "keywords": {"food", "eat", "drink", "lawful", "forbidden", "meat", "intoxicant"},
        "description": "Dietary laws and permissible food (Halal/Haram)",
    },
    "death": {
        "keywords": {"death", "die", "grave", "soul", "life", "mortal"},
        "description": "Death, mortality, and the transition to the hereafter",
    },
    "divine_attributes": {
        "keywords": {"merciful", "gracious", "wise", "omniscient", "hearing", "seeing", "living"},
        "description": "The names and attributes of God (Asma ul-Husna)",
    },
    "obedience": {
        "keywords": {"obey", "follow", "command", "submit", "devote", "stray"},
        "description": "Obedience to God and His messengers",
    },
    "nature_signs": {
        "keywords": {"rain", "mountain", "sea", "star", "moon", "sun", "night", "wind"},
        "description": "Natural phenomena as signs of God's existence",
    },
    "resurrection": {
        "keywords": {"resurrect", "raise", "bone", "body", "restore", "gather"},
        "description": "Physical resurrection and bodily restoration",
    },
    "predestination": {
        "keywords": {"decree", "ordain", "fate", "predetermine", "plan", "knowledge"},
        "description": "Divine decree and predestination (Qadr)",
    },
    "remembrance": {
        "keywords": {"remember", "commemorate", "invoke", "glorify", "mention", "dhikr"},
        "description": "Remembrance and mindfulness of God (Dhikr)",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# Graph Loader (reuses pattern from deduction_engine.py)
# ══════════════════════════════════════════════════════════════════════════════

def load_graph():
    """Load graph data from CSVs."""
    verses = {}
    with open(os.path.join(DATA_DIR, "verse_nodes.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            verses[row["verseId"]] = {
                "text": row["text"],
                "surah": row["surah"],
                "surahName": row["surahName"],
            }

    keyword_verses = defaultdict(list)
    verse_keywords = defaultdict(list)
    with open(os.path.join(DATA_DIR, "verse_keyword_rels.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            vid, kw, score = row["verseId"], row["keyword"], float(row["score"])
            keyword_verses[kw].append((vid, score))
            verse_keywords[vid].append((kw, score))

    return {
        "verses": verses,
        "keyword_verses": keyword_verses,
        "verse_keywords": verse_keywords,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Step 2: Match verses to concepts
# ══════════════════════════════════════════════════════════════════════════════

def match_verses_to_concepts(graph, min_keyword_hits=2):
    """
    For each concept, find all verses that match its keyword signature.
    A verse matches if at least `min_keyword_hits` of the concept's keywords
    appear in the verse text (case-insensitive word boundary match).
    """
    verses = graph["verses"]
    concept_verses = defaultdict(list)   # concept_id -> [(verse_id, hit_count)]
    verse_concepts = defaultdict(list)   # verse_id -> [(concept_id, hit_count)]

    # Precompute lowercased word sets per verse for speed
    verse_word_sets = {}
    for vid, vdata in verses.items():
        words = set(re.findall(r"[a-z]+", vdata["text"].lower()))
        verse_word_sets[vid] = words

    for concept_id, concept_info in CONCEPTS.items():
        kw_set = concept_info["keywords"]
        for vid, words in verse_word_sets.items():
            hits = words & kw_set
            if len(hits) >= min_keyword_hits:
                concept_verses[concept_id].append((vid, len(hits)))
                verse_concepts[vid].append((concept_id, len(hits)))

    return concept_verses, verse_concepts, verse_word_sets


# ══════════════════════════════════════════════════════════════════════════════
# Step 3: Build dependency edges
# ══════════════════════════════════════════════════════════════════════════════

def parse_verse_id(vid):
    """Parse '2:255' into (surah_int, verse_int)."""
    parts = vid.split(":")
    if len(parts) == 2:
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            pass
    return None, None


def compute_dependencies(concept_verses, verse_word_sets):
    """
    Build directed dependency edges between concepts.

    Concept A depends on concept B if:
      1. Co-occurrence: verses about A frequently also contain B's keywords.
      2. Ordering bias: in sequential verse pairs, B tends to appear before A.

    Weight = co_occurrence_score * ordering_bias
    """
    concept_ids = list(CONCEPTS.keys())
    concept_verse_sets = {c: set(vid for vid, _ in vlist) for c, vlist in concept_verses.items()}

    # Precompute verse ordering index: (surah, verse_num) for each verse
    verse_order = {}
    for c, vlist in concept_verses.items():
        for vid, _ in vlist:
            if vid not in verse_order:
                s, v = parse_verse_id(vid)
                if s is not None:
                    verse_order[vid] = (s, v)

    dependencies = []

    for i, concept_a in enumerate(concept_ids):
        if concept_a not in concept_verses or not concept_verses[concept_a]:
            continue
        verses_a = concept_verse_sets.get(concept_a, set())
        if not verses_a:
            continue

        kw_a = CONCEPTS[concept_a]["keywords"]

        for j, concept_b in enumerate(concept_ids):
            if i == j:
                continue
            if concept_b not in concept_verses or not concept_verses[concept_b]:
                continue

            verses_b = concept_verse_sets.get(concept_b, set())
            if not verses_b:
                continue

            kw_b = CONCEPTS[concept_b]["keywords"]

            # --- Co-occurrence score ---
            # How often do verses about A also mention B's keywords?
            a_mentions_b = 0
            for vid in verses_a:
                words = verse_word_sets.get(vid, set())
                b_hits = words & kw_b
                if len(b_hits) >= 1:
                    a_mentions_b += 1

            if a_mentions_b == 0:
                continue

            co_occurrence = a_mentions_b / len(verses_a)

            # --- Ordering bias ---
            # In same-surah sequential pairs where both appear, does B come first?
            # B before A suggests B is a prerequisite for understanding A.
            b_before_a = 0
            a_before_b = 0

            # Group verses by surah for efficient ordering check
            a_by_surah = defaultdict(list)
            b_by_surah = defaultdict(list)
            for vid in verses_a:
                order = verse_order.get(vid)
                if order:
                    a_by_surah[order[0]].append(order[1])
            for vid in verses_b:
                order = verse_order.get(vid)
                if order:
                    b_by_surah[order[0]].append(order[1])

            for surah in set(a_by_surah.keys()) & set(b_by_surah.keys()):
                a_verses_sorted = sorted(a_by_surah[surah])
                b_verses_sorted = sorted(b_by_surah[surah])

                # For each A-verse, find how many B-verses come before it
                b_idx = 0
                for av in a_verses_sorted:
                    while b_idx < len(b_verses_sorted) and b_verses_sorted[b_idx] < av:
                        b_idx += 1
                    b_before_a += b_idx

                # For each B-verse, find how many A-verses come before it
                a_idx = 0
                for bv in b_verses_sorted:
                    while a_idx < len(a_verses_sorted) and a_verses_sorted[a_idx] < bv:
                        a_idx += 1
                    a_before_b += a_idx

            total_order = b_before_a + a_before_b
            if total_order > 0:
                ordering_bias = b_before_a / total_order  # >0.5 means B tends to precede A
            else:
                ordering_bias = 0.5  # neutral

            # --- Final weight ---
            weight = co_occurrence * ordering_bias

            if weight < 0.05:
                continue

            # Collect evidence verses (shared overlap, limited set)
            overlap = verses_a & verses_b
            evidence = sorted(list(overlap))[:10]

            dependencies.append({
                "from": concept_a,
                "to": concept_b,
                "weight": round(weight, 4),
                "co_occurrence": round(co_occurrence, 4),
                "ordering_bias": round(ordering_bias, 4),
                "evidence_verses": evidence,
            })

    # Sort by weight descending
    dependencies.sort(key=lambda x: -x["weight"])
    return dependencies


# ══════════════════════════════════════════════════════════════════════════════
# Step 4: Analyze graph structure
# ══════════════════════════════════════════════════════════════════════════════

def analyze_graph_structure(concepts_data, dependencies):
    """
    Identify foundation concepts, advanced concepts, and learning paths.
    """
    concept_ids = [c["id"] for c in concepts_data]

    # Build adjacency structures
    # Edge: from A to B means "A depends on B" (B is prerequisite)
    in_deps = defaultdict(list)   # concept -> list of concepts it depends ON
    out_deps = defaultdict(list)  # concept -> list of concepts that depend on IT

    # Use only the stronger dependencies (top edges per concept)
    deps_by_source = defaultdict(list)
    for d in dependencies:
        deps_by_source[d["from"]].append(d)

    strong_deps = []
    for src, dep_list in deps_by_source.items():
        # Keep top 5 dependencies per concept
        top = sorted(dep_list, key=lambda x: -x["weight"])[:5]
        strong_deps.extend(top)

    for d in strong_deps:
        src = d["from"]   # the concept that has the dependency
        tgt = d["to"]     # the prerequisite
        in_deps[src].append((tgt, d["weight"]))
        out_deps[tgt].append((src, d["weight"]))

    # Foundation concepts: most depended upon (high out_deps), fewest own deps (low in_deps)
    foundation_scores = {}
    for cid in concept_ids:
        depended_on = len(out_deps.get(cid, []))
        own_deps = len(in_deps.get(cid, []))
        # High score = many dependents, few prerequisites
        if depended_on + own_deps > 0:
            foundation_scores[cid] = depended_on / (1 + own_deps)
        else:
            foundation_scores[cid] = 0

    foundations = sorted(foundation_scores, key=lambda x: -foundation_scores[x])
    foundations = [c for c in foundations if foundation_scores[c] > 0][:10]

    # Advanced concepts: many prerequisites (high in_deps)
    advanced_scores = {}
    for cid in concept_ids:
        own_deps = len(in_deps.get(cid, []))
        depended_on = len(out_deps.get(cid, []))
        # High score = many prerequisites, few dependents
        if own_deps + depended_on > 0:
            advanced_scores[cid] = own_deps / (1 + depended_on)
        else:
            advanced_scores[cid] = 0

    advanced = sorted(advanced_scores, key=lambda x: -advanced_scores[x])
    advanced = [c for c in advanced if advanced_scores[c] > 0][:10]

    # Learning paths: find longest chains via DFS from foundation concepts
    # Build adjacency: prerequisite -> dependent (reverse of "from" -> "to")
    # "from A to B" means A needs B, so B -> A in teaching order
    teach_graph = defaultdict(list)
    for d in strong_deps:
        # B is prerequisite for A, so teach B before A
        teach_graph[d["to"]].append((d["from"], d["weight"]))

    learning_paths = []

    def dfs_paths(start, visited, path, max_depth=8):
        """Find all paths from a foundation concept outward."""
        if len(path) >= max_depth:
            return path[:]
        best_sub = path[:]
        # Sort neighbors by weight (strongest first) and limit branching
        neighbors = sorted(teach_graph.get(start, []), key=lambda x: -x[1])[:5]
        for neighbor, w in neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                path.append(neighbor)
                candidate = dfs_paths(neighbor, visited, path, max_depth)
                if len(candidate) > len(best_sub):
                    best_sub = candidate[:]
                path.pop()
                visited.discard(neighbor)
        return best_sub

    for foundation in foundations[:5]:
        visited = {foundation}
        longest = dfs_paths(foundation, visited, [foundation])
        if len(longest) >= 3:
            learning_paths.append(longest)

    # Deduplicate paths that share the same start/end
    seen_paths = set()
    unique_paths = []
    for p in sorted(learning_paths, key=len, reverse=True):
        key = (p[0], p[-1])
        if key not in seen_paths:
            seen_paths.add(key)
            unique_paths.append(p)

    return foundations, advanced, unique_paths[:10]


# ══════════════════════════════════════════════════════════════════════════════
# Main Pipeline
# ══════════════════════════════════════════════════════════════════════════════

def build_concept_graph():
    """Run the full concept dependency graph pipeline."""
    print("=" * 70)
    print("  CONCEPT DEPENDENCY GRAPH BUILDER")
    print("=" * 70)

    # Load data
    print("\nStep 1: Loading graph data...")
    graph = load_graph()
    print(f"  {len(graph['verses'])} verses loaded")
    print(f"  {len(graph['keyword_verses'])} keywords loaded")

    # Match verses to concepts
    print("\nStep 2: Matching verses to concepts (threshold: 2+ keyword hits)...")
    concept_verses, verse_concepts, verse_word_sets = match_verses_to_concepts(graph)

    concepts_data = []
    for cid, cinfo in CONCEPTS.items():
        vlist = concept_verses.get(cid, [])
        concepts_data.append({
            "id": cid,
            "verse_count": len(vlist),
            "keywords": sorted(cinfo["keywords"]),
            "description": cinfo["description"],
        })

    concepts_data.sort(key=lambda x: -x["verse_count"])

    print(f"\n  Concept verse counts:")
    for c in concepts_data:
        if c["verse_count"] > 0:
            print(f"    {c['id']:25s} {c['verse_count']:5d} verses")

    matched_count = sum(1 for c in concepts_data if c["verse_count"] > 0)
    print(f"\n  {matched_count}/{len(CONCEPTS)} concepts matched to at least one verse")

    # Build dependencies
    print("\nStep 3: Computing dependency edges (co-occurrence + ordering)...")
    dependencies = compute_dependencies(concept_verses, verse_word_sets)
    print(f"  {len(dependencies)} raw dependency edges")

    # Show top dependencies
    print(f"\n  Top 15 dependency edges:")
    for d in dependencies[:15]:
        print(f"    {d['from']:25s} needs {d['to']:25s} "
              f"(w={d['weight']:.3f}, co={d['co_occurrence']:.3f}, "
              f"ord={d['ordering_bias']:.3f}, evidence={len(d['evidence_verses'])})")

    # Analyze structure
    print("\nStep 4: Analyzing graph structure...")
    foundations, advanced, learning_paths = analyze_graph_structure(
        concepts_data, dependencies
    )

    print(f"\n  Foundation concepts (most depended upon, fewest dependencies):")
    for i, c in enumerate(foundations, 1):
        print(f"    {i}. {c}")

    print(f"\n  Advanced concepts (many prerequisites):")
    for i, c in enumerate(advanced, 1):
        print(f"    {i}. {c}")

    print(f"\n  Learning paths ({len(learning_paths)} found):")
    for i, path in enumerate(learning_paths, 1):
        print(f"    {i}. {' -> '.join(path)}")

    # Build output
    output = {
        "concepts": concepts_data,
        "dependencies": dependencies,
        "foundations": foundations,
        "advanced": advanced,
        "learning_paths": learning_paths,
        "stats": {
            "total_concepts": len(CONCEPTS),
            "matched_concepts": matched_count,
            "total_dependency_edges": len(dependencies),
            "total_verses_analyzed": len(graph["verses"]),
        },
    }

    # Save
    output_path = os.path.join(AUTORESEARCH_DIR, "concept_graph.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nSaved concept graph to {output_path}")

    return output


if __name__ == "__main__":
    build_concept_graph()
