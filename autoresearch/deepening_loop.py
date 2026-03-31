#!/usr/bin/env python3
"""
Deepening Loop — Extends the best deduction chains to 4-5 hops for deeper insights.

Takes the highest-scoring deduction chains from previous runs and attempts to
extend them by traversing 1-2 additional hops from their endpoints. The result
is longer, more profound chains that cross more surahs and theological themes.

The "metric" being optimized: chain length, cross-surah diversity, keyword
coherence, and thematic breadth — combined into a single depth score.
"""

import argparse
import copy
import json
import math
import os
import random
import sys
import time
from collections import defaultdict
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTORESEARCH_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AUTORESEARCH_DIR)

from deduction_engine import (
    PropositionExtractor, NoveltyScorer,
    load_graph, Deduction,
)

# ══════════════════════════════════════════════════════════════════════════════
# Output paths
# ══════════════════════════════════════════════════════════════════════════════

BEST_DEDUCTIONS_PATH = os.path.join(AUTORESEARCH_DIR, "best_deductions.json")
SYNTHESIZED_PATH = os.path.join(AUTORESEARCH_DIR, "synthesized_insights.json")
DEEP_CHAINS_PATH = os.path.join(AUTORESEARCH_DIR, "deep_chains.json")
ROUND_LOG_PATH = os.path.join(AUTORESEARCH_DIR, "deepening_rounds.tsv")

# ══════════════════════════════════════════════════════════════════════════════
# Theological theme categories (for theme diversity scoring)
# ══════════════════════════════════════════════════════════════════════════════

THEME_KEYWORDS = {
    "monotheism": {"god", "lord", "worship", "idols", "one", "partner", "associate",
                   "sovereign", "almighty", "creator", "omnipotent"},
    "eschatology": {"day", "judgment", "resurrection", "heaven", "hell", "fire",
                    "paradise", "garden", "hereafter", "death", "grave", "reckoning",
                    "hour", "doom"},
    "ethics": {"righteous", "justice", "good", "evil", "sin", "charity", "honest",
               "patience", "humble", "arrogant", "oppress", "kind", "forgive",
               "mercy", "fair"},
    "law": {"pray", "prayer", "fast", "fasting", "zakat", "pilgrimage", "hajj",
            "forbidden", "lawful", "halal", "haram", "decree", "command",
            "prohibit", "obligate"},
    "prophethood": {"messenger", "prophet", "moses", "abraham", "jesus", "noah",
                    "joseph", "david", "solomon", "muhammad", "scripture", "book",
                    "revelation", "sign", "miracle"},
    "creation": {"create", "heaven", "earth", "water", "mountain", "star", "moon",
                 "sun", "animal", "livestock", "human", "clay", "seed", "plant",
                 "night", "day"},
    "community": {"believer", "disbeliever", "hypocrite", "people", "nation",
                  "tribe", "family", "children", "orphan", "poor", "society",
                  "covenant", "treaty"},
    "spiritual": {"soul", "heart", "faith", "guidance", "light", "darkness",
                  "knowledge", "wisdom", "remember", "reflect", "ponder",
                  "grateful", "thankful", "trust"},
}


def detect_themes(keywords):
    """Return the set of theological theme categories matched by keywords."""
    kw_lower = {k.lower() for k in keywords}
    matched = set()
    for theme, theme_kws in THEME_KEYWORDS.items():
        if kw_lower & theme_kws:
            matched.add(theme)
    return matched


# ══════════════════════════════════════════════════════════════════════════════
# Load seed chains from previous runs
# ══════════════════════════════════════════════════════════════════════════════

def load_seed_chains():
    """Load the best deduction chains from best_deductions.json or synthesized_insights.json."""
    seeds = []

    if os.path.exists(BEST_DEDUCTIONS_PATH):
        with open(BEST_DEDUCTIONS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        for entry in data:
            seeds.append({
                "premise_verses": entry["premise_verses"],
                "bridge_keywords": entry.get("bridge_keywords", []),
                "conclusion": entry.get("conclusion", ""),
                "novelty_score": entry.get("novelty_score", 0),
                "rule": entry.get("rule", "unknown"),
                "graph_distance": entry.get("graph_distance", 0),
                "source": "best_deductions",
            })

    if os.path.exists(SYNTHESIZED_PATH):
        with open(SYNTHESIZED_PATH, encoding="utf-8") as f:
            data = json.load(f)
        for entry in data:
            seeds.append({
                "premise_verses": entry.get("verse_pair", []),
                "bridge_keywords": entry.get("bridge_keywords", []),
                "conclusion": entry.get("best_conclusion", ""),
                "novelty_score": entry.get("avg_quality", 0),
                "rule": "synthesized_insight",
                "graph_distance": len(entry.get("verse_pair", [])),
                "source": "synthesized_insights",
            })

    # Sort by score descending
    seeds.sort(key=lambda x: -x["novelty_score"])
    return seeds


# ══════════════════════════════════════════════════════════════════════════════
# Chain extension logic
# ══════════════════════════════════════════════════════════════════════════════

def get_chain_keywords(graph, verse_ids):
    """Collect all keywords for a list of verse IDs."""
    all_kw = []
    for vid in verse_ids:
        kws = graph["verse_keywords"].get(vid, [])
        all_kw.extend(kw for kw, _ in kws)
    return all_kw


def get_chain_surahs(graph, verse_ids):
    """Return the set of surah numbers touched by a chain."""
    surahs = set()
    for vid in verse_ids:
        v = graph["verses"].get(vid, {})
        surahs.add(v.get("surah", ""))
    return surahs


def extend_chain(graph, chain_verses, extractor, props_cache, max_extensions=8):
    """
    Try to extend a chain by 1-2 hops from both endpoints.
    Returns a list of extended chain tuples: (verse_list, bridge_keywords_per_hop).
    """
    if not chain_verses:
        return []

    chain_set = set(chain_verses)
    start_id = chain_verses[0]
    end_id = chain_verses[-1]
    extensions = []

    # Extend from the END by 1 hop
    for neighbor_id, score in graph["related"].get(end_id, [])[:max_extensions]:
        if neighbor_id in chain_set:
            continue
        new_chain = list(chain_verses) + [neighbor_id]
        extensions.append(new_chain)

        # Extend from that neighbor by 1 more hop (total +2 from end)
        for hop2_id, score2 in graph["related"].get(neighbor_id, [])[:max_extensions // 2]:
            if hop2_id in chain_set or hop2_id == neighbor_id:
                continue
            new_chain2 = list(chain_verses) + [neighbor_id, hop2_id]
            extensions.append(new_chain2)

    # Extend from the START by 1 hop (prepend)
    for neighbor_id, score in graph["related"].get(start_id, [])[:max_extensions]:
        if neighbor_id in chain_set:
            continue
        new_chain = [neighbor_id] + list(chain_verses)
        extensions.append(new_chain)

        # Extend from that neighbor by 1 more hop (total +2 from start)
        for hop2_id, score2 in graph["related"].get(neighbor_id, [])[:max_extensions // 2]:
            if hop2_id in chain_set or hop2_id == neighbor_id:
                continue
            new_chain2 = [hop2_id, neighbor_id] + list(chain_verses)
            extensions.append(new_chain2)

    # Filter: keep only chains of length 4 or 5
    extensions = [c for c in extensions if 4 <= len(c) <= 6]

    # For each extension, extract propositions for new verses (cached)
    for chain in extensions:
        for vid in chain:
            if vid not in props_cache and vid in graph["verses"]:
                text = graph["verses"][vid]["text"]
                props = extractor.extract(vid, text)
                props_cache[vid] = props

    return extensions


# ══════════════════════════════════════════════════════════════════════════════
# Scoring extended chains
# ══════════════════════════════════════════════════════════════════════════════

def score_deep_chain(graph, chain_verses, props_cache):
    """
    Score an extended chain on four axes, returning a composite depth score (0-100).

    Axes:
      1. Chain length (longer = potentially more novel)
      2. Cross-surah diversity (how many surahs does it touch?)
      3. Bridge keyword chain coherence (do consecutive hops share keywords?)
      4. Theme diversity (how many theological categories does the chain span?)
    """
    scores = {}

    # --- 1. Chain length score ---
    length = len(chain_verses)
    # 4-hop = 60, 5-hop = 80, 6-hop = 100
    scores["length"] = min(100, (length - 3) * 20 + 40)

    # --- 2. Cross-surah diversity ---
    surahs = get_chain_surahs(graph, chain_verses)
    surahs.discard("")
    n_surahs = len(surahs)
    # 1 surah = 10, 2 = 40, 3 = 65, 4 = 85, 5+ = 100
    if n_surahs <= 1:
        scores["surah_diversity"] = 10
    elif n_surahs == 2:
        scores["surah_diversity"] = 40
    elif n_surahs == 3:
        scores["surah_diversity"] = 65
    elif n_surahs == 4:
        scores["surah_diversity"] = 85
    else:
        scores["surah_diversity"] = 100

    # --- 3. Bridge keyword coherence ---
    # For each consecutive pair (i, i+1), compute keyword overlap
    coherence_hits = 0
    coherence_pairs = 0
    bridge_chain = []  # ordered keywords forming the bridge progression
    for i in range(len(chain_verses) - 1):
        v1, v2 = chain_verses[i], chain_verses[i + 1]
        kw1 = set(kw for kw, _ in graph["verse_keywords"].get(v1, []))
        kw2 = set(kw for kw, _ in graph["verse_keywords"].get(v2, []))
        overlap = kw1 & kw2
        coherence_pairs += 1
        if overlap:
            coherence_hits += 1
            bridge_chain.append(sorted(overlap)[0])  # pick one representative
        else:
            bridge_chain.append("---")  # gap

    if coherence_pairs > 0:
        scores["keyword_coherence"] = round(coherence_hits / coherence_pairs * 100)
    else:
        scores["keyword_coherence"] = 0

    # --- 4. Theme diversity ---
    all_kw = get_chain_keywords(graph, chain_verses)
    themes = detect_themes(all_kw)
    n_themes = len(themes)
    # 0 themes = 0, 1 = 20, 2 = 45, 3 = 70, 4+ = 100
    if n_themes == 0:
        scores["theme_diversity"] = 0
    elif n_themes == 1:
        scores["theme_diversity"] = 20
    elif n_themes == 2:
        scores["theme_diversity"] = 45
    elif n_themes == 3:
        scores["theme_diversity"] = 70
    else:
        scores["theme_diversity"] = 100

    # Composite: weighted average
    weights = {
        "length": 0.15,
        "surah_diversity": 0.25,
        "keyword_coherence": 0.35,
        "theme_diversity": 0.25,
    }
    composite = sum(scores[k] * weights[k] for k in weights)

    return round(composite, 2), scores, bridge_chain, list(themes)


# ══════════════════════════════════════════════════════════════════════════════
# Chain narrative construction
# ══════════════════════════════════════════════════════════════════════════════

def build_narrative(graph, chain_verses, bridge_chain, themes, props_cache):
    """
    Build a natural language description of what a deep chain reveals.

    Format:
    "Starting from [verse] about [topic], through [bridge keywords],
     we reach [verse] about [different topic], revealing that [connection]."
    """
    if not chain_verses or len(chain_verses) < 2:
        return ""

    start_id = chain_verses[0]
    end_id = chain_verses[-1]

    # Get surah names for context
    start_info = graph["verses"].get(start_id, {})
    end_info = graph["verses"].get(end_id, {})
    start_surah = start_info.get("surahName", "Unknown")
    end_surah = end_info.get("surahName", "Unknown")

    # Get propositions for start and end
    start_props = props_cache.get(start_id, [])
    end_props = props_cache.get(end_id, [])

    start_topic = ""
    if start_props:
        p = start_props[0]
        start_topic = f"{p.subject} {p.relation} {p.object}"
    else:
        # Fall back to first few keywords
        kws = [kw for kw, _ in graph["verse_keywords"].get(start_id, [])[:3]]
        start_topic = ", ".join(kws) if kws else "its theme"

    end_topic = ""
    if end_props:
        p = end_props[0]
        end_topic = f"{p.subject} {p.relation} {p.object}"
    else:
        kws = [kw for kw, _ in graph["verse_keywords"].get(end_id, [])[:3]]
        end_topic = ", ".join(kws) if kws else "its theme"

    # Build bridge keyword string (filter gaps)
    bridge_words = [b for b in bridge_chain if b != "---"]
    bridge_str = " -> ".join(bridge_words) if bridge_words else "thematic proximity"

    # Build the intermediate path description
    mid_ids = chain_verses[1:-1]
    path_str = " -> ".join(f"[{v}]" for v in chain_verses)

    # Theme string
    theme_str = ", ".join(sorted(themes)) if themes else "interconnected themes"

    # Construct the narrative
    narrative = (
        f"Starting from [{start_id}] (Surah {start_surah}) about '{start_topic}', "
        f"through bridge keywords [{bridge_str}], "
        f"we reach [{end_id}] (Surah {end_surah}) about '{end_topic}', "
        f"revealing that {theme_str} are linked across {len(chain_verses)} verses. "
        f"Full path: {path_str}."
    )
    return narrative


# ══════════════════════════════════════════════════════════════════════════════
# Persistence helpers
# ══════════════════════════════════════════════════════════════════════════════

def load_existing_deep_chains():
    """Load previously saved deep chains."""
    if os.path.exists(DEEP_CHAINS_PATH):
        with open(DEEP_CHAINS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_deep_chains(chains):
    """Save top 100 deep chains to disk."""
    chains.sort(key=lambda x: -x["depth_score"])
    chains = chains[:100]
    with open(DEEP_CHAINS_PATH, "w", encoding="utf-8") as f:
        json.dump(chains, f, indent=2, ensure_ascii=False)
    return chains


def init_round_log():
    """Initialize the round log TSV if it does not exist."""
    if not os.path.exists(ROUND_LOG_PATH):
        with open(ROUND_LOG_PATH, "w", encoding="utf-8") as f:
            f.write(
                "round\ttimestamp\tseeds_tried\textensions_found\t"
                "kept_above_threshold\ttotal_deep_chains\telapsed_s\n"
            )


def append_round_log(round_num, seeds_tried, extensions_found, kept, total, elapsed):
    """Append a row to the round log."""
    with open(ROUND_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(
            f"{round_num}\t{datetime.now().isoformat()}\t{seeds_tried}\t"
            f"{extensions_found}\t{kept}\t{total}\t{elapsed:.1f}\n"
        )


# ══════════════════════════════════════════════════════════════════════════════
# One deepening round
# ══════════════════════════════════════════════════════════════════════════════

def run_one_deepening_round(graph, extractor, seeds, props_cache, existing_chains,
                            seen_chain_keys, threshold=40.0, top_n=20):
    """
    Pick the top-N seed chains, extend each, score, and keep the best.

    Returns (new_chains, stats_dict).
    """
    t0 = time.time()

    # Pick top_n seeds; shuffle within the top tier to get variety across rounds
    pool = seeds[:max(top_n * 2, len(seeds))]
    random.shuffle(pool)
    selected = pool[:top_n]

    extensions_found = 0
    new_chains = []

    for seed in selected:
        chain_verses = seed["premise_verses"]
        if not chain_verses:
            continue

        extended_chains = extend_chain(
            graph, chain_verses, extractor, props_cache, max_extensions=8
        )
        extensions_found += len(extended_chains)

        for ext_chain in extended_chains:
            # Dedup: use sorted tuple of verse IDs as key
            chain_key = tuple(ext_chain)
            if chain_key in seen_chain_keys:
                continue
            seen_chain_keys.add(chain_key)

            # Score
            depth_score, sub_scores, bridge_chain, themes = score_deep_chain(
                graph, ext_chain, props_cache
            )

            if depth_score < threshold:
                continue

            # Build narrative
            narrative = build_narrative(graph, ext_chain, bridge_chain, themes, props_cache)

            # Collect propositions for the full chain
            chain_props = []
            for vid in ext_chain:
                for p in props_cache.get(vid, []):
                    chain_props.append(str(p))

            # Surah info
            surahs_touched = []
            for vid in ext_chain:
                v_info = graph["verses"].get(vid, {})
                s_name = v_info.get("surahName", "")
                s_num = v_info.get("surah", "")
                label = f"{s_num}:{s_name}" if s_name else s_num
                if label not in surahs_touched:
                    surahs_touched.append(label)

            entry = {
                "chain_verses": ext_chain,
                "chain_length": len(ext_chain),
                "depth_score": depth_score,
                "sub_scores": sub_scores,
                "bridge_keywords": bridge_chain,
                "themes": themes,
                "surahs_touched": surahs_touched,
                "propositions": chain_props[:10],  # keep it compact
                "narrative": narrative,
                "seed_rule": seed.get("rule", "unknown"),
                "seed_source": seed.get("source", "unknown"),
                "timestamp": datetime.now().isoformat(),
            }
            new_chains.append(entry)

    elapsed = time.time() - t0
    stats = {
        "seeds_tried": len(selected),
        "extensions_found": extensions_found,
        "kept": len(new_chains),
        "elapsed": elapsed,
    }
    return new_chains, stats


# ══════════════════════════════════════════════════════════════════════════════
# Main loop
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Deepening Loop: extend best deduction chains to 4-5 hops."
    )
    parser.add_argument(
        "--max-hours", type=float, default=0,
        help="Maximum hours to run (0 = infinite)."
    )
    parser.add_argument(
        "--threshold", type=float, default=40.0,
        help="Minimum depth score to keep a chain (0-100)."
    )
    parser.add_argument(
        "--top-n", type=int, default=20,
        help="Number of top seed chains to try extending each round."
    )
    args = parser.parse_args()

    max_seconds = args.max_hours * 3600 if args.max_hours > 0 else float("inf")

    print("=" * 70)
    print("  DEEPENING LOOP — Extended Chain Discovery")
    print("=" * 70)
    print(f"  Time limit:  {'infinite' if max_seconds == float('inf') else f'{args.max_hours}h'}")
    print(f"  Threshold:   {args.threshold}")
    print(f"  Seeds/round: {args.top_n}")

    # Load graph
    print("\nLoading knowledge graph...")
    graph = load_graph()
    print(f"  {len(graph['verses'])} verses, "
          f"{len(graph['keyword_verses'])} keywords, "
          f"{sum(len(v) for v in graph['related'].values()) // 2} related edges")

    # Load proposition extractor
    print("Loading spaCy model for proposition extraction...")
    extractor = PropositionExtractor()
    print("  Ready.")

    # Load seed chains
    print("\nLoading seed chains from previous deduction runs...")
    seeds = load_seed_chains()
    if not seeds:
        print("  ERROR: No seed chains found. Run infinite_deduction.py first to generate")
        print(f"         {BEST_DEDUCTIONS_PATH}")
        print(f"         or {SYNTHESIZED_PATH}")
        sys.exit(1)
    print(f"  Loaded {len(seeds)} seed chains.")

    # Load existing deep chains
    deep_chains = load_existing_deep_chains()
    seen_chain_keys = set()
    for dc in deep_chains:
        seen_chain_keys.add(tuple(dc["chain_verses"]))
    print(f"  {len(deep_chains)} existing deep chains loaded.")

    # Proposition cache (verse_id -> [Proposition, ...])
    props_cache = {}

    # Initialize round log
    init_round_log()

    print(f"\n{'=' * 70}")
    print(f"  Starting deepening loop...")
    print(f"{'=' * 70}\n")

    start_time = time.time()
    round_num = 0
    total_kept = 0

    while True:
        round_num += 1
        elapsed_total = time.time() - start_time

        if elapsed_total > max_seconds:
            print(f"\n  Time limit reached ({args.max_hours}h)")
            break

        # Run one deepening round
        new_chains, stats = run_one_deepening_round(
            graph, extractor, seeds, props_cache, deep_chains,
            seen_chain_keys, threshold=args.threshold, top_n=args.top_n,
        )
        total_kept += stats["kept"]

        # Merge and save
        if new_chains:
            deep_chains.extend(new_chains)
            deep_chains = save_deep_chains(deep_chains)

            # Also feed the new deep chains back as seeds for the next round
            for nc in new_chains:
                seeds.append({
                    "premise_verses": nc["chain_verses"],
                    "bridge_keywords": nc["bridge_keywords"],
                    "conclusion": nc["narrative"],
                    "novelty_score": nc["depth_score"],
                    "rule": "deep_chain",
                    "graph_distance": nc["chain_length"],
                    "source": "deepening_loop",
                })
            seeds.sort(key=lambda x: -x["novelty_score"])

        # Log
        append_round_log(
            round_num,
            stats["seeds_tried"],
            stats["extensions_found"],
            stats["kept"],
            len(deep_chains),
            stats["elapsed"],
        )

        # Print progress every 5 rounds or when new chains are found
        if new_chains:
            best = max(new_chains, key=lambda c: c["depth_score"])
            print(f"[round {round_num:4d}] +{stats['kept']:3d} deep chains "
                  f"(total: {len(deep_chains)}, cumulative kept: {total_kept}) "
                  f"[{stats['elapsed']:.1f}s]")
            print(f"  BEST: score={best['depth_score']:.1f} "
                  f"len={best['chain_length']} "
                  f"surahs={len(best['surahs_touched'])} "
                  f"themes={best['themes']}")
            print(f"  {best['narrative'][:200]}")
        elif round_num % 5 == 0:
            hours = elapsed_total / 3600
            rate = total_kept / max(1, elapsed_total) * 3600
            print(f"[round {round_num:4d}] 0 new chains "
                  f"(total: {len(deep_chains)}) "
                  f"[{stats['elapsed']:.1f}s] "
                  f"| {hours:.2f}h elapsed, {rate:.0f} chains/hr")

        # Periodic summary every 25 rounds
        if round_num % 25 == 0:
            hours = elapsed_total / 3600
            rate = total_kept / max(1, elapsed_total) * 3600
            print(f"\n  === DEEPENING PROGRESS: {round_num} rounds, "
                  f"{len(deep_chains)} deep chains, "
                  f"{total_kept} total kept, "
                  f"{hours:.2f}h elapsed, "
                  f"{rate:.0f} chains/hr ===")
            # Print theme distribution
            theme_counts = defaultdict(int)
            for dc in deep_chains:
                for t in dc.get("themes", []):
                    theme_counts[t] += 1
            if theme_counts:
                dist = ", ".join(f"{t}:{c}" for t, c in
                                sorted(theme_counts.items(), key=lambda x: -x[1]))
                print(f"  Theme distribution: {dist}")
            print()

    # ── Final summary ────────────────────────────────────────────────────────
    total_time = time.time() - start_time
    print(f"\n{'=' * 70}")
    print(f"  DEEPENING LOOP COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Rounds:          {round_num}")
    print(f"  Deep chains:     {len(deep_chains)}")
    print(f"  Total kept:      {total_kept}")
    print(f"  Time:            {total_time / 60:.1f} minutes")
    print(f"  Rate:            {total_kept / max(1, total_time) * 3600:.0f} chains/hr")
    print(f"  Props cached:    {len(props_cache)} verses")
    print(f"  Output:          {DEEP_CHAINS_PATH}")
    print(f"  Round log:       {ROUND_LOG_PATH}")
    print(f"{'=' * 70}")

    # Print top 10 deep chains
    if deep_chains:
        print(f"\n  TOP 10 DEEPEST CHAINS:")
        for i, dc in enumerate(deep_chains[:10]):
            print(f"\n  #{i + 1} [depth: {dc['depth_score']:.1f}] "
                  f"len={dc['chain_length']} "
                  f"surahs={dc['surahs_touched']}")
            print(f"  Themes: {dc['themes']}")
            print(f"  Bridge: {' -> '.join(dc['bridge_keywords'])}")
            print(f"  {dc['narrative'][:250]}")


if __name__ == "__main__":
    main()
