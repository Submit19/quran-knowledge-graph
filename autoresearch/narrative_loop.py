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

def _smooth_categories(raw_sequence, window=5):
    """Smooth a category sequence using a sliding-window majority vote.

    For each position, the most common category within a centred window of
    *window* verses is chosen.  Ties are broken by keeping the raw value.
    """
    if len(raw_sequence) <= window:
        # Too short to smooth — just return as-is
        return list(raw_sequence)

    half = window // 2
    smoothed = []
    for i in range(len(raw_sequence)):
        lo = max(0, i - half)
        hi = min(len(raw_sequence), i + half + 1)
        counts = Counter(raw_sequence[lo:hi])
        top_cat, top_count = counts.most_common(1)[0]
        # If the raw value ties with the winner, prefer the raw value
        # (avoids unnecessary flicker)
        if counts[raw_sequence[i]] == top_count:
            smoothed.append(raw_sequence[i])
        else:
            smoothed.append(top_cat)
    return smoothed


def _build_theme_blocks(smoothed_sequence, verse_ids, sustain=3):
    """Identify contiguous theme blocks from a smoothed sequence.

    A new block starts only when the smoothed theme changes AND the new
    theme sustains for at least *sustain* consecutive verses.  Short
    interruptions (< sustain verses) are absorbed into the surrounding block.

    Returns a list of dicts:
        {"theme": str, "start_verse": str, "end_verse": str, "length": int}
    """
    if not smoothed_sequence:
        return []

    # First pass: run-length encode the smoothed sequence
    runs = []  # [(category, start_index, length)]
    cur_cat = smoothed_sequence[0]
    cur_start = 0
    for i in range(1, len(smoothed_sequence)):
        if smoothed_sequence[i] != cur_cat:
            runs.append((cur_cat, cur_start, i - cur_start))
            cur_cat = smoothed_sequence[i]
            cur_start = i
    runs.append((cur_cat, cur_start, len(smoothed_sequence) - cur_start))

    # Second pass: merge short runs (< sustain) into the preceding block
    merged = [runs[0]]
    for cat, start, length in runs[1:]:
        if length < sustain:
            # Absorb into previous block
            prev_cat, prev_start, prev_len = merged[-1]
            merged[-1] = (prev_cat, prev_start, prev_len + length)
        else:
            merged.append((cat, start, length))

    # Convert to output format
    blocks = []
    for cat, start, length in merged:
        blocks.append({
            "theme": cat,
            "start_verse": verse_ids[start],
            "end_verse": verse_ids[min(start + length - 1, len(verse_ids) - 1)],
            "length": length,
        })
    return blocks


def analyze_intra_surah(surah_num, verse_ids, graph):
    """Analyze theme flow within a single surah.

    Returns a dict with:
      - verse_categories: [{verseId, keywords, primary_cat, all_cats}, ...]
      - transitions: [(from_cat, to_cat, verse_index), ...]  (sustained only)
      - theme_blocks: [{theme, start_verse, end_verse, length}, ...]
      - narrative_arc: {opening_block, development_blocks, closing_block}
      - thematic_center: category name
      - category_distribution: {cat: count}
      - narrative_complexity: number of theme blocks
    """
    verse_categories = []
    raw_sequence = []

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
        raw_sequence.append(p_cat)

    # Smooth with sliding window of 5 verses (majority vote)
    smoothed = _smooth_categories(raw_sequence, window=5)

    # Build theme blocks (only count sustained changes of 4+ verses)
    theme_blocks = _build_theme_blocks(smoothed, verse_ids, sustain=4)

    # Transitions: only between consecutive theme blocks
    transitions = []
    for i in range(1, len(theme_blocks)):
        if theme_blocks[i]["theme"] != theme_blocks[i - 1]["theme"]:
            # Find the verse index where this block starts
            block_start_vid = theme_blocks[i]["start_verse"]
            v_idx = verse_ids.index(block_start_vid) if block_start_vid in verse_ids else i
            transitions.append((
                theme_blocks[i - 1]["theme"],
                theme_blocks[i]["theme"],
                v_idx,
            ))

    # Category distribution (from smoothed sequence)
    cat_counts = Counter(smoothed)
    thematic_center = cat_counts.most_common(1)[0][0] if cat_counts else "uncategorized"

    # Narrative arc based on theme blocks
    if not theme_blocks:
        arc = {
            "opening_block": "uncategorized",
            "development_blocks": [],
            "closing_block": "uncategorized",
        }
    elif len(theme_blocks) == 1:
        arc = {
            "opening_block": theme_blocks[0]["theme"],
            "development_blocks": [],
            "closing_block": theme_blocks[0]["theme"],
        }
    else:
        arc = {
            "opening_block": theme_blocks[0]["theme"],
            "development_blocks": [b["theme"] for b in theme_blocks[1:-1]],
            "closing_block": theme_blocks[-1]["theme"],
        }

    # For backward compatibility, also expose the old-style arc keys
    arc["opening"] = arc["opening_block"]
    arc["development"] = arc["development_blocks"]
    arc["conclusion"] = arc["closing_block"]

    return {
        "surah": surah_num,
        "num_verses": len(verse_ids),
        "verse_categories": verse_categories,
        "transitions": transitions,
        "num_transitions": len(transitions),
        "theme_blocks": theme_blocks,
        "narrative_complexity": len(theme_blocks),
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
    narrative_complexity = arc_data.get("narrative_complexity", arc_data["num_transitions"])

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
                    "theme_blocks": arc_data.get("theme_blocks", []),
                    "narrative_complexity": arc_data.get("narrative_complexity", arc_data["num_transitions"]),
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
