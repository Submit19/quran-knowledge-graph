"""
Narrative Arc Loop — infinite analysis of thematic flow within and across surahs.

Analyzes:
  1. Intra-surah flow: verse-by-verse theme transitions, narrative arcs, thematic centers
  2. Inter-surah connections: bridge keywords, ending-to-opening theme continuity
  3. Surah profiles: primary/secondary themes, diversity, complexity, connections

Outputs:
  - surah_profiles.json     — profile for all 114 surahs
  - narrative_arcs.json     — intra-surah thematic flow data
  - surah_bridges.json      — inter-surah connection analysis
  - narrative_rounds.tsv    — round-by-round log
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict

csv.field_size_limit(sys.maxsize)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTORESEARCH_DIR = os.path.dirname(os.path.abspath(__file__))

from deduction_engine import load_graph
from analyze_deductions import THEOLOGICAL_CATEGORIES


# ══════════════════════════════════════════════════════════════════════════════
# Theological categorization helpers
# ══════════════════════════════════════════════════════════════════════════════

def categorize_text(text):
    """Map a text string to theological categories with scores.

    Returns a list of (category_name, overlap_count) sorted descending,
    including only categories with at least one keyword match.
    """
    words = set(re.findall(r"[a-z]+", text.lower()))
    scores = {}
    for cat_name, cat_info in THEOLOGICAL_CATEGORIES.items():
        overlap = words & cat_info["keywords"]
        if overlap:
            scores[cat_name] = len(overlap)
    if not scores:
        return [("uncategorized", 0)]
    return sorted(scores.items(), key=lambda x: -x[1])


def primary_category(text):
    """Return the single best-matching category name for *text*."""
    return categorize_text(text)[0][0]


# ══════════════════════════════════════════════════════════════════════════════
# Index helpers
# ══════════════════════════════════════════════════════════════════════════════

def build_surah_index(graph):
    """Return {surah_number: [verseId, ...]} sorted by verse order."""
    surah_verses = defaultdict(list)
    for vid, info in graph["verses"].items():
        surah_num = int(info["surah"])
        surah_verses[surah_num].append(vid)

    # Sort verses within each surah by their verse number
    for s in surah_verses:
        surah_verses[s].sort(key=lambda v: int(v.split(":")[1]))
    return surah_verses


def surah_name(graph, surah_num):
    """Look up the surahName for a given surah number."""
    for info in graph["verses"].values():
        if int(info["surah"]) == surah_num:
            return info.get("surahName", f"Surah {surah_num}")
    return f"Surah {surah_num}"


# ══════════════════════════════════════════════════════════════════════════════
# Intra-surah analysis
# ══════════════════════════════════════════════════════════════════════════════

def analyze_intra_surah(surah_num, verse_ids, graph):
    """Analyze theme flow within a single surah.

    Returns a dict with:
      - verse_categories: [{verseId, keywords, primary_cat, all_cats}, ...]
      - transitions: [(from_cat, to_cat, verse_index), ...]
      - narrative_arc: {opening, development, conclusion}
      - thematic_center: category name
      - category_distribution: {cat: count}
    """
    verse_categories = []
    category_sequence = []

    for vid in verse_ids:
        text = graph["verses"][vid]["text"]
        kw_list = graph["verse_keywords"].get(vid, [])
        keywords = [kw for kw, _ in sorted(kw_list, key=lambda x: -x[1])[:10]]

        # Combine verse text and keywords for richer categorization
        combined = text + " " + " ".join(keywords)
        cats = categorize_text(combined)
        p_cat = cats[0][0]

        verse_categories.append({
            "verseId": vid,
            "keywords": keywords[:6],
            "primary_category": p_cat,
            "all_categories": [(c, s) for c, s in cats[:3]],
        })
        category_sequence.append(p_cat)

    # Detect theme transitions
    transitions = []
    for i in range(1, len(category_sequence)):
        if category_sequence[i] != category_sequence[i - 1]:
            transitions.append((category_sequence[i - 1], category_sequence[i], i))

    # Category distribution
    cat_counts = Counter(category_sequence)
    thematic_center = cat_counts.most_common(1)[0][0] if cat_counts else "uncategorized"

    # Narrative arc: opening (first ~10%), development (middle ~80%), conclusion (last ~10%)
    n = len(category_sequence)
    if n == 0:
        arc = {"opening": "uncategorized", "development": [], "conclusion": "uncategorized"}
    else:
        boundary_open = max(1, n // 10)
        boundary_close = max(boundary_open + 1, n - max(1, n // 10))

        opening_cats = Counter(category_sequence[:boundary_open])
        conclusion_cats = Counter(category_sequence[boundary_close:])
        dev_cats = Counter(category_sequence[boundary_open:boundary_close])

        arc = {
            "opening": opening_cats.most_common(1)[0][0] if opening_cats else "uncategorized",
            "development": [c for c, _ in dev_cats.most_common(3)],
            "conclusion": conclusion_cats.most_common(1)[0][0] if conclusion_cats else "uncategorized",
        }

    return {
        "surah": surah_num,
        "num_verses": len(verse_ids),
        "verse_categories": verse_categories,
        "transitions": transitions,
        "num_transitions": len(transitions),
        "narrative_arc": arc,
        "thematic_center": thematic_center,
        "category_distribution": dict(cat_counts),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Inter-surah analysis
# ══════════════════════════════════════════════════════════════════════════════

def analyze_inter_surah(surah_a_num, surah_b_num, arc_a, arc_b, graph, surah_index):
    """Analyze thematic bridge between two sequential surahs.

    Returns a dict describing the connection between surah_a and surah_b.
    """
    # 1. Ending theme of A vs opening theme of B
    ending_theme = arc_a["narrative_arc"]["conclusion"]
    opening_theme = arc_b["narrative_arc"]["opening"]
    theme_continues = ending_theme == opening_theme

    # 2. Bridge keywords: keywords shared between last verses of A and first verses of B
    verses_a = surah_index[surah_a_num]
    verses_b = surah_index[surah_b_num]

    tail_count = max(1, min(5, len(verses_a) // 10 or 1))
    head_count = max(1, min(5, len(verses_b) // 10 or 1))

    tail_kws = set()
    for vid in verses_a[-tail_count:]:
        for kw, _ in graph["verse_keywords"].get(vid, []):
            tail_kws.add(kw)

    head_kws = set()
    for vid in verses_b[:head_count]:
        for kw, _ in graph["verse_keywords"].get(vid, []):
            head_kws.add(kw)

    bridge_keywords = sorted(tail_kws & head_kws)

    # 3. Graph-edge bridges: count related-verse edges crossing from A to B
    set_a = set(verses_a)
    set_b = set(verses_b)
    cross_edges = 0
    cross_edge_pairs = []
    for vid in verses_a:
        for neighbor, score in graph["related"].get(vid, []):
            if neighbor in set_b:
                cross_edges += 1
                if len(cross_edge_pairs) < 5:
                    cross_edge_pairs.append((vid, neighbor, score))

    return {
        "surah_a": surah_a_num,
        "surah_b": surah_b_num,
        "ending_theme_a": ending_theme,
        "opening_theme_b": opening_theme,
        "theme_continues": theme_continues,
        "bridge_keywords": bridge_keywords[:15],
        "num_bridge_keywords": len(bridge_keywords),
        "cross_edges": cross_edges,
        "cross_edge_examples": [
            {"from": p[0], "to": p[1], "score": p[2]} for p in cross_edge_pairs
        ],
        "narrative_bridge": theme_continues or len(bridge_keywords) >= 3 or cross_edges >= 3,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Surah profile builder
# ══════════════════════════════════════════════════════════════════════════════

def build_surah_profile(surah_num, arc_data, bridges_in, bridges_out, graph, surah_index):
    """Build a comprehensive profile for a single surah.

    *bridges_in*: bridge data where this surah is surah_b (incoming).
    *bridges_out*: bridge data where this surah is surah_a (outgoing).
    """
    cat_dist = arc_data["category_distribution"]
    sorted_cats = sorted(cat_dist.items(), key=lambda x: -x[1])

    primary_theme = sorted_cats[0][0] if sorted_cats else "uncategorized"
    secondary_themes = [c for c, _ in sorted_cats[1:3]]
    theme_diversity = len(cat_dist)
    narrative_complexity = arc_data["num_transitions"]

    # Key bridge keywords across both directions
    all_bridge_kws = set()
    for b in bridges_in + bridges_out:
        all_bridge_kws.update(b.get("bridge_keywords", []))

    # Most connected surahs via graph edges
    verses = surah_index.get(surah_num, [])
    connected_surah_counts = Counter()
    for vid in verses:
        for neighbor, _ in graph["related"].get(vid, []):
            n_info = graph["verses"].get(neighbor, {})
            n_surah = int(n_info.get("surah", 0))
            if n_surah != surah_num and n_surah > 0:
                connected_surah_counts[n_surah] += 1

    return {
        "surah": surah_num,
        "name": surah_name(graph, surah_num),
        "num_verses": arc_data["num_verses"],
        "primary_theme": primary_theme,
        "secondary_themes": secondary_themes,
        "theme_diversity": theme_diversity,
        "narrative_complexity": narrative_complexity,
        "thematic_center": arc_data["thematic_center"],
        "narrative_arc": arc_data["narrative_arc"],
        "category_distribution": cat_dist,
        "bridge_keywords": sorted(all_bridge_kws)[:20],
        "most_connected_surahs": [
            {"surah": s, "edge_count": c}
            for s, c in connected_surah_counts.most_common(10)
        ],
    }


# ══════════════════════════════════════════════════════════════════════════════
# Persistence helpers
# ══════════════════════════════════════════════════════════════════════════════

def _load_json(path, default=None):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}


def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _append_tsv(path, row_dict):
    exists = os.path.exists(path)
    fieldnames = ["round", "timestamp", "surahs_processed", "total_profiles",
                  "total_arcs", "total_bridges", "elapsed_sec"]
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        if not exists:
            writer.writeheader()
        writer.writerow(row_dict)


# ══════════════════════════════════════════════════════════════════════════════
# Main loop
# ══════════════════════════════════════════════════════════════════════════════

PROFILES_PATH = os.path.join(AUTORESEARCH_DIR, "surah_profiles.json")
ARCS_PATH = os.path.join(AUTORESEARCH_DIR, "narrative_arcs.json")
BRIDGES_PATH = os.path.join(AUTORESEARCH_DIR, "surah_bridges.json")
ROUNDS_PATH = os.path.join(AUTORESEARCH_DIR, "narrative_rounds.tsv")


def run_loop(max_hours=0):
    """Run the narrative arc analysis loop.

    Args:
        max_hours: Maximum runtime in hours. 0 means infinite.
    """
    print("=" * 72)
    print("  NARRATIVE ARC LOOP")
    print("  Analyzing thematic flow within and across surahs")
    print("=" * 72)

    # Load graph
    print("\nLoading knowledge graph...")
    graph = load_graph()
    print(f"  {len(graph['verses']):,} verses")
    print(f"  {len(graph['keyword_verses']):,} keywords")
    print(f"  {sum(len(v) for v in graph['related'].values()) // 2:,} related-verse edges")

    surah_index = build_surah_index(graph)
    all_surahs = sorted(surah_index.keys())
    print(f"  {len(all_surahs)} surahs indexed")

    # Load any previously saved state
    profiles = _load_json(PROFILES_PATH, {})
    arcs = _load_json(ARCS_PATH, {})
    bridges = _load_json(BRIDGES_PATH, {})

    start_time = time.time()
    deadline = start_time + max_hours * 3600 if max_hours > 0 else None
    round_num = 0
    surah_cursor = 0  # cycles through all_surahs

    batch_size_min = 5
    batch_size_max = 10

    print(f"\nStarting loop (max_hours={max_hours}, batch={batch_size_min}-{batch_size_max} surahs/round)")
    print(f"  Resuming with {len(profiles)} existing profiles, "
          f"{len(arcs)} arcs, {len(bridges)} bridges\n")

    try:
        while True:
            round_num += 1
            round_start = time.time()

            # Check deadline
            if deadline and time.time() >= deadline:
                print(f"\nTime limit reached ({max_hours}h). Stopping.")
                break

            # Pick batch of surahs for this round
            batch_size = min(batch_size_max, max(batch_size_min,
                             batch_size_max - round_num % 6))
            batch = []
            for _ in range(batch_size):
                batch.append(all_surahs[surah_cursor % len(all_surahs)])
                surah_cursor += 1
            batch = sorted(set(batch))

            # ── Intra-surah analysis ─────────────────────────────────────
            for s in batch:
                verse_ids = surah_index[s]
                arc_data = analyze_intra_surah(s, verse_ids, graph)
                arcs[str(s)] = {
                    "surah": s,
                    "name": surah_name(graph, s),
                    "num_verses": arc_data["num_verses"],
                    "transitions": [
                        {"from": t[0], "to": t[1], "verse_index": t[2]}
                        for t in arc_data["transitions"]
                    ],
                    "num_transitions": arc_data["num_transitions"],
                    "narrative_arc": arc_data["narrative_arc"],
                    "thematic_center": arc_data["thematic_center"],
                    "category_distribution": arc_data["category_distribution"],
                }

                # Store arc_data for profile building (keep in memory)
                # We tag it on the arcs dict entry temporarily
                arcs[str(s)]["_arc_data"] = arc_data

            # ── Inter-surah analysis ─────────────────────────────────────
            for s in batch:
                s_next = s + 1
                if s_next in surah_index and str(s) in arcs and str(s_next) in arcs:
                    arc_a = arcs[str(s)].get("_arc_data") or arcs[str(s)]
                    arc_b = arcs[str(s_next)].get("_arc_data") or arcs[str(s_next)]
                    # Ensure arc_data-like dicts have the right keys
                    if "narrative_arc" not in arc_a:
                        continue
                    bridge = analyze_inter_surah(s, s_next, arc_a, arc_b, graph, surah_index)
                    bridges[f"{s}-{s_next}"] = bridge

                # Also check previous surah
                s_prev = s - 1
                if s_prev in surah_index and str(s_prev) in arcs and str(s) in arcs:
                    arc_prev = arcs[str(s_prev)].get("_arc_data") or arcs[str(s_prev)]
                    arc_curr = arcs[str(s)].get("_arc_data") or arcs[str(s)]
                    if "narrative_arc" in arc_prev:
                        bridge = analyze_inter_surah(s_prev, s, arc_prev, arc_curr,
                                                     graph, surah_index)
                        bridges[f"{s_prev}-{s}"] = bridge

            # ── Build / update surah profiles ────────────────────────────
            for s in batch:
                arc_data = arcs[str(s)].get("_arc_data")
                if arc_data is None:
                    continue
                b_in = [v for k, v in bridges.items() if v.get("surah_b") == s]
                b_out = [v for k, v in bridges.items() if v.get("surah_a") == s]
                profile = build_surah_profile(s, arc_data, b_in, b_out, graph, surah_index)
                profiles[str(s)] = profile

            # ── Clean temporary _arc_data before saving ──────────────────
            for s in batch:
                arcs[str(s)].pop("_arc_data", None)

            # ── Persist ──────────────────────────────────────────────────
            _save_json(PROFILES_PATH, profiles)
            _save_json(ARCS_PATH, arcs)
            _save_json(BRIDGES_PATH, bridges)

            elapsed = time.time() - round_start
            _append_tsv(ROUNDS_PATH, {
                "round": round_num,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "surahs_processed": ",".join(str(s) for s in batch),
                "total_profiles": len(profiles),
                "total_arcs": len(arcs),
                "total_bridges": len(bridges),
                "elapsed_sec": f"{elapsed:.1f}",
            })

            # ── Progress reporting ───────────────────────────────────────
            if round_num % 5 == 0 or round_num == 1:
                total_elapsed = time.time() - start_time
                pct = len(profiles) / len(all_surahs) * 100
                print(f"[Round {round_num}] "
                      f"Surahs {','.join(str(s) for s in batch)} | "
                      f"Profiles: {len(profiles)}/{len(all_surahs)} ({pct:.0f}%) | "
                      f"Arcs: {len(arcs)} | Bridges: {len(bridges)} | "
                      f"Round: {elapsed:.1f}s | Total: {total_elapsed:.0f}s")

            # If we have completed all surahs at least once, pause briefly
            # before starting the refinement pass
            if surah_cursor >= len(all_surahs) and surah_cursor % len(all_surahs) < batch_size:
                print(f"\n  --- Full pass complete ({len(profiles)} profiles). "
                      f"Starting refinement pass ---\n")

    except KeyboardInterrupt:
        print("\nInterrupted by user. Saving final state...")
        _save_json(PROFILES_PATH, profiles)
        _save_json(ARCS_PATH, arcs)
        _save_json(BRIDGES_PATH, bridges)

    # Final summary
    total_elapsed = time.time() - start_time
    print(f"\n{'=' * 72}")
    print(f"  NARRATIVE ARC LOOP — COMPLETE")
    print(f"  Rounds: {round_num}")
    print(f"  Surah profiles: {len(profiles)}")
    print(f"  Narrative arcs:  {len(arcs)}")
    print(f"  Surah bridges:   {len(bridges)}")
    print(f"  Total time:      {total_elapsed:.0f}s ({total_elapsed / 3600:.2f}h)")
    print(f"{'=' * 72}")
    print(f"\nOutput files:")
    print(f"  {PROFILES_PATH}")
    print(f"  {ARCS_PATH}")
    print(f"  {BRIDGES_PATH}")
    print(f"  {ROUNDS_PATH}")


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Narrative Arc Loop — analyze thematic flow within and across Quran surahs"
    )
    parser.add_argument(
        "--max-hours", type=float, default=0,
        help="Maximum runtime in hours (0 = infinite, default: 0)"
    )
    args = parser.parse_args()
    run_loop(max_hours=args.max_hours)
