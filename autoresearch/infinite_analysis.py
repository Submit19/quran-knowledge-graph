#!/usr/bin/env python3
"""
Infinite Analysis Loop — AutoResearch on Deductions.

Runs continuously alongside the infinite deduction loop, performing
increasingly deeper analysis on the growing corpus of deductions.

Every 60 seconds:
  1. Read new deductions from all_deductions.jsonl (incremental)
  2. Categorize and quality-score new deductions
  3. Update meta-knowledge graph, synthesized insights, categorized deductions
  4. Run meta-deduction phase: find patterns across deductions
  5. Log findings and save meta-insights

Also runs an inner optimization loop that tunes categorization thresholds
and quality scoring weights to maximize insight quality.
"""

import argparse
import copy
import json
import math
import os
import random
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
AUTORESEARCH_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(AUTORESEARCH_DIR)
sys.path.insert(0, AUTORESEARCH_DIR)

from analyze_deductions import (
    categorize_deduction,
    score_quality,
    build_meta_graph,
    synthesize_insights,
    load_verses_text,
    THEOLOGICAL_CATEGORIES,
)

# ---------------------------------------------------------------------------
# Output paths
# ---------------------------------------------------------------------------
DEDUCTIONS_LOG = os.path.join(AUTORESEARCH_DIR, "all_deductions.jsonl")
META_GRAPH_PATH = os.path.join(AUTORESEARCH_DIR, "meta_knowledge_graph.json")
INSIGHTS_PATH = os.path.join(AUTORESEARCH_DIR, "synthesized_insights.json")
CATEGORIZED_PATH = os.path.join(AUTORESEARCH_DIR, "categorized_deductions.json")
ANALYSIS_ROUNDS_LOG = os.path.join(AUTORESEARCH_DIR, "analysis_rounds.tsv")
META_INSIGHTS_PATH = os.path.join(AUTORESEARCH_DIR, "meta_insights.json")

POLL_INTERVAL_SECONDS = 60


# ══════════════════════════════════════════════════════════════════════════════
# Adaptive quality scorer with tunable weights
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_QUALITY_WEIGHTS = {
    "specificity": 0.20,
    "surah_diversity": 0.15,
    "meaningfulness": 0.15,
    "coherence": 0.20,
    "relevance": 0.15,
    "rule_bonus": 0.15,
}

DEFAULT_THRESHOLDS = {
    "min_quality_for_graph": 50,
    "min_quality_for_insights": 55,
    "top_categorized_keep": 500,
}


def score_quality_weighted(deduction, verses_text, weights):
    """Score deduction quality using custom weights.

    Re-implements the factor computation from analyze_deductions.score_quality
    but applies the supplied weight dict instead of hardcoded weights.
    """
    import re

    COMMON_WORDS = {
        "the", "and", "of", "to", "in", "for", "is", "are", "was", "that",
        "this", "god", "lord", "shall", "will", "upon",
    }

    factors = {}

    # Factor 1: specificity
    bridges = deduction.get("bridge_keywords", [])
    specific_bridges = [b for b in bridges if b.lower() not in COMMON_WORDS and len(b) > 3]
    factors["specificity"] = min(100, len(specific_bridges) * 30)

    # Factor 2: surah diversity
    surahs = set()
    for vid in deduction.get("premise_verses", []):
        surahs.add(vid.split(":")[0])
    factors["surah_diversity"] = min(100, (len(surahs) - 1) * 40)

    # Factor 3: meaningfulness
    clen = len(deduction.get("conclusion", ""))
    if 50 < clen < 300:
        factors["meaningfulness"] = 80
    elif 30 < clen < 500:
        factors["meaningfulness"] = 50
    else:
        factors["meaningfulness"] = 20

    # Factor 4: coherence
    if len(bridges) >= 2:
        unique_ratio = len(set(bridges)) / len(bridges)
        factors["coherence"] = unique_ratio * 100
    else:
        factors["coherence"] = 30

    # Factor 5: relevance
    verse_ids = deduction.get("premise_verses", [])
    if len(verse_ids) >= 2:
        first_text = verses_text.get(verse_ids[0], "").lower()
        last_text = verses_text.get(verse_ids[-1], "").lower()
        first_words = set(re.findall(r'[a-z]{4,}', first_text))
        last_words = set(re.findall(r'[a-z]{4,}', last_text))
        shared = first_words & last_words - COMMON_WORDS
        factors["relevance"] = min(100, len(shared) * 20)
    else:
        factors["relevance"] = 50

    # Factor 6: rule bonus
    rule = deduction.get("rule", "")
    factors["rule_bonus"] = {
        "thematic_bridge_3hop": 70,
        "transitive_chain": 60,
        "shared_subject_synthesis": 40,
        "shared_subject_multi_predicate": 30,
    }.get(rule, 50)

    composite = sum(factors.get(k, 0) * weights.get(k, 0) for k in weights)
    return round(composite, 2), factors


# ══════════════════════════════════════════════════════════════════════════════
# Incremental deduction reader (safe for concurrent writes)
# ══════════════════════════════════════════════════════════════════════════════

class IncrementalDeductionReader:
    """Reads new lines from all_deductions.jsonl since last read.

    Handles the case where the deduction generator is writing simultaneously
    by tracking byte offset and discarding incomplete trailing lines.
    """

    def __init__(self, path):
        self.path = path
        self.byte_offset = 0

    def read_new(self):
        """Return a list of new deduction dicts since last call."""
        if not os.path.exists(self.path):
            return []

        new_deductions = []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                f.seek(self.byte_offset)
                raw = f.read()
                if not raw:
                    return []

                # Only process complete lines (the last line may be partial
                # if the deduction generator is mid-write).
                if not raw.endswith("\n"):
                    last_nl = raw.rfind("\n")
                    if last_nl == -1:
                        # Entire chunk is a partial line; wait for next poll.
                        return []
                    raw = raw[: last_nl + 1]

                for line in raw.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        new_deductions.append(json.loads(line))
                    except json.JSONDecodeError:
                        # Skip corrupted / partial lines.
                        continue

                self.byte_offset += len(raw.encode("utf-8"))
        except OSError:
            return []

        return new_deductions


# ══════════════════════════════════════════════════════════════════════════════
# Meta-deduction engine: patterns across deductions
# ══════════════════════════════════════════════════════════════════════════════

def compute_meta_deductions(all_categorized):
    """Analyze patterns across the full corpus of categorized deductions.

    Returns a dict with:
      - hub_verses: verse IDs that appear in the most deductions
      - structural_patterns: recurring bridge keyword chains
      - category_pair_quality: category pairs ranked by avg quality
      - deduction_clusters: groups of 5+ deductions connecting same two surahs
    """
    if not all_categorized:
        return {
            "hub_verses": [],
            "structural_patterns": [],
            "category_pair_quality": [],
            "deduction_clusters": [],
        }

    # 1. Hub verses — which verse IDs appear in the MOST deductions
    verse_counter = Counter()
    for d in all_categorized:
        for vid in d.get("premise_verses", []):
            verse_counter[vid] += 1

    hub_verses = [
        {"verse_id": vid, "deduction_count": cnt}
        for vid, cnt in verse_counter.most_common(50)
    ]

    # 2. Structural patterns — recurring bridge keyword chains
    chain_counter = Counter()
    for d in all_categorized:
        bk = d.get("bridge_keywords", [])
        if len(bk) >= 2:
            # Normalize: sort pairs so (a,b) == (b,a)
            for i in range(len(bk)):
                for j in range(i + 1, len(bk)):
                    pair = tuple(sorted([bk[i].lower(), bk[j].lower()]))
                    chain_counter[pair] += 1

    structural_patterns = [
        {"keyword_pair": list(pair), "count": cnt}
        for pair, cnt in chain_counter.most_common(50)
    ]

    # 3. Category pair quality — which category pairs have highest avg quality
    pair_quality = defaultdict(lambda: {"total": 0.0, "count": 0})
    for d in all_categorized:
        cats = d.get("categories", [])
        q = d.get("quality_score", 0)
        if len(cats) >= 2:
            for i in range(len(cats)):
                for j in range(i + 1, len(cats)):
                    c1 = min(cats[i][0], cats[j][0])
                    c2 = max(cats[i][0], cats[j][0])
                    key = (c1, c2)
                    pair_quality[key]["total"] += q
                    pair_quality[key]["count"] += 1

    category_pair_quality = []
    for (c1, c2), data in pair_quality.items():
        if data["count"] >= 2:
            category_pair_quality.append({
                "categories": [c1, c2],
                "avg_quality": round(data["total"] / data["count"], 2),
                "count": data["count"],
            })
    category_pair_quality.sort(key=lambda x: -x["avg_quality"])
    category_pair_quality = category_pair_quality[:30]

    # 4. Deduction clusters — groups of 5+ deductions linking same two surahs
    surah_pair_counter = defaultdict(list)
    for idx, d in enumerate(all_categorized):
        vs = d.get("premise_verses", [])
        surahs = sorted(set(vid.split(":")[0] for vid in vs))
        if len(surahs) >= 2:
            key = (surahs[0], surahs[-1])
            surah_pair_counter[key].append(idx)

    deduction_clusters = []
    for (s1, s2), indices in surah_pair_counter.items():
        if len(indices) >= 5:
            cluster_qualities = [
                all_categorized[i].get("quality_score", 0) for i in indices
            ]
            deduction_clusters.append({
                "surah_pair": [s1, s2],
                "num_deductions": len(indices),
                "avg_quality": round(sum(cluster_qualities) / len(cluster_qualities), 2),
                "best_conclusion": max(
                    (all_categorized[i] for i in indices),
                    key=lambda d: d.get("quality_score", 0),
                ).get("conclusion", "")[:200],
            })
    deduction_clusters.sort(key=lambda x: -x["num_deductions"])
    deduction_clusters = deduction_clusters[:30]

    return {
        "hub_verses": hub_verses,
        "structural_patterns": structural_patterns,
        "category_pair_quality": category_pair_quality,
        "deduction_clusters": deduction_clusters,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Self-optimizing weight tuner
# ══════════════════════════════════════════════════════════════════════════════

def evaluate_insight_quality(insights):
    """Compute a scalar quality metric for a set of synthesized insights.

    Higher is better.  Rewards:
      - Number of insights
      - Average supporting deductions per insight
      - Average quality of those deductions
      - Diversity of categories covered
    """
    if not insights:
        return 0.0

    n = len(insights)
    avg_support = sum(i.get("num_supporting_deductions", 0) for i in insights) / n
    avg_q = sum(i.get("avg_quality", 0) for i in insights) / n
    categories = set(i.get("category", "") for i in insights)
    diversity = len(categories)

    # Composite (all terms are positive)
    return round(math.log1p(n) * avg_support * avg_q * math.log1p(diversity), 2)


def mutate_weights(weights):
    """Return a mutated copy of quality scoring weights."""
    new = copy.deepcopy(weights)
    key = random.choice(list(new.keys()))
    delta = random.uniform(-0.05, 0.05)
    new[key] = max(0.01, min(0.50, new[key] + delta))
    # Re-normalize so weights sum to 1.0
    total = sum(new.values())
    for k in new:
        new[k] = round(new[k] / total, 4)
    return new


def mutate_thresholds(thresholds):
    """Return a mutated copy of thresholds."""
    new = copy.deepcopy(thresholds)
    key = random.choice(list(new.keys()))
    if key == "top_categorized_keep":
        new[key] = random.choice([200, 300, 500, 750, 1000])
    else:
        new[key] = max(20, min(90, new[key] + random.choice([-5, -3, 0, 3, 5])))
    return new


# ══════════════════════════════════════════════════════════════════════════════
# Persistence helpers
# ══════════════════════════════════════════════════════════════════════════════

def save_json_atomic(path, data):
    """Write JSON atomically via tmp file + rename."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def init_analysis_log():
    """Ensure the TSV round log exists with a header."""
    if not os.path.exists(ANALYSIS_ROUNDS_LOG):
        with open(ANALYSIS_ROUNDS_LOG, "w", encoding="utf-8") as f:
            f.write(
                "round\ttimestamp\tnew_deductions\ttotal_deductions"
                "\thub_verses_top3\tstructural_patterns_top3"
                "\tclusters_found\tinsight_quality_score"
                "\tweights_mutated\tthresholds_mutated\n"
            )


def append_analysis_log(row_dict):
    """Append one row to the analysis rounds TSV."""
    with open(ANALYSIS_ROUNDS_LOG, "a", encoding="utf-8") as f:
        cols = [
            str(row_dict.get("round", "")),
            row_dict.get("timestamp", ""),
            str(row_dict.get("new_deductions", 0)),
            str(row_dict.get("total_deductions", 0)),
            row_dict.get("hub_verses_top3", ""),
            row_dict.get("structural_patterns_top3", ""),
            str(row_dict.get("clusters_found", 0)),
            str(row_dict.get("insight_quality_score", 0)),
            row_dict.get("weights_mutated", "no"),
            row_dict.get("thresholds_mutated", "no"),
        ]
        f.write("\t".join(cols) + "\n")


# ══════════════════════════════════════════════════════════════════════════════
# Main infinite analysis loop
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Infinite Analysis Loop — continuously analyzes deductions"
    )
    parser.add_argument(
        "--max-hours", type=float, default=0,
        help="Maximum hours to run (0 = infinite)",
    )
    args = parser.parse_args()

    max_seconds = args.max_hours * 3600 if args.max_hours > 0 else float("inf")

    print("=" * 70)
    print("  INFINITE ANALYSIS LOOP — AutoResearch on Deductions")
    print("=" * 70)
    print(f"  Time limit: {'none' if max_seconds == float('inf') else f'{args.max_hours}h'}")
    print(f"  Poll interval: {POLL_INTERVAL_SECONDS}s")

    # Load verse texts once (used by categorizer and scorer)
    print("\nLoading verse texts...")
    verses_text = load_verses_text()
    print(f"  {len(verses_text)} verses loaded")

    # Initialize reader
    reader = IncrementalDeductionReader(DEDUCTIONS_LOG)

    # Cumulative state
    all_categorized = []        # full list of categorized deductions
    best_weights = copy.deepcopy(DEFAULT_QUALITY_WEIGHTS)
    best_thresholds = copy.deepcopy(DEFAULT_THRESHOLDS)
    best_insight_score = 0.0

    # Load any previously categorized deductions to bootstrap
    if os.path.exists(CATEGORIZED_PATH):
        try:
            with open(CATEGORIZED_PATH, "r", encoding="utf-8") as f:
                all_categorized = json.load(f)
            print(f"  Bootstrapped {len(all_categorized)} previously categorized deductions")
            # Advance reader past already-analyzed deductions
            file_size = os.path.getsize(DEDUCTIONS_LOG) if os.path.exists(DEDUCTIONS_LOG) else 0
            reader.byte_offset = file_size
        except (json.JSONDecodeError, OSError):
            pass

    init_analysis_log()

    start_time = time.time()
    round_num = 0

    print(f"\n{'=' * 70}")
    print("  Starting infinite analysis loop...")
    print(f"{'=' * 70}\n")

    try:
        while True:
            round_num += 1
            round_start = time.time()
            elapsed_total = round_start - start_time

            if elapsed_total > max_seconds:
                print(f"\n  Time limit reached ({args.max_hours}h)")
                break

            # ------------------------------------------------------------------
            # Step 1: Read new deductions incrementally
            # ------------------------------------------------------------------
            new_deductions = reader.read_new()

            if not new_deductions and round_num > 1:
                # Nothing new — sleep and retry
                if round_num % 5 == 0:
                    print(f"[round {round_num:5d}] No new deductions. "
                          f"Total analyzed: {len(all_categorized)}. Waiting...")
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            # ------------------------------------------------------------------
            # Step 2: Categorize and quality-score new deductions
            # ------------------------------------------------------------------
            newly_categorized = []
            for d in new_deductions:
                cats = categorize_deduction(d, verses_text)
                quality, factors = score_quality_weighted(d, verses_text, best_weights)
                newly_categorized.append({
                    **d,
                    "categories": cats,
                    "quality_score": quality,
                    "quality_breakdown": factors,
                })

            all_categorized.extend(newly_categorized)

            # ------------------------------------------------------------------
            # Step 3: Update meta-knowledge graph
            # ------------------------------------------------------------------
            meta_graph = build_meta_graph(all_categorized, min_quality=best_thresholds["min_quality_for_graph"])
            save_json_atomic(META_GRAPH_PATH, meta_graph)

            # ------------------------------------------------------------------
            # Step 4: Update synthesized insights
            # ------------------------------------------------------------------
            insights = synthesize_insights(all_categorized, min_quality=best_thresholds["min_quality_for_insights"])
            save_json_atomic(INSIGHTS_PATH, insights[:200])

            # ------------------------------------------------------------------
            # Step 5: Update categorized deductions (top N by quality)
            # ------------------------------------------------------------------
            top_n = best_thresholds["top_categorized_keep"]
            top_categorized = sorted(all_categorized, key=lambda x: -x["quality_score"])[:top_n]
            save_json_atomic(CATEGORIZED_PATH, top_categorized)

            # ------------------------------------------------------------------
            # Step 6: Meta-deduction phase — patterns across deductions
            # ------------------------------------------------------------------
            meta = compute_meta_deductions(all_categorized)
            meta["analysis_round"] = round_num
            meta["timestamp"] = datetime.now().isoformat()
            meta["total_deductions_analyzed"] = len(all_categorized)
            meta["current_weights"] = best_weights
            meta["current_thresholds"] = best_thresholds
            meta["insight_quality_score"] = evaluate_insight_quality(insights)
            save_json_atomic(META_INSIGHTS_PATH, meta)

            # ------------------------------------------------------------------
            # Step 7: Self-optimization — tune weights and thresholds
            # ------------------------------------------------------------------
            current_insight_score = evaluate_insight_quality(insights)
            weights_mutated = "no"
            thresholds_mutated = "no"

            # Try mutated weights every round
            candidate_weights = mutate_weights(best_weights)
            trial_categorized = []
            # Re-score a sample (up to 500) with candidate weights
            sample = all_categorized[-500:] if len(all_categorized) > 500 else all_categorized
            for d_orig in sample:
                q, _ = score_quality_weighted(d_orig, verses_text, candidate_weights)
                trial_categorized.append({**d_orig, "quality_score": q})

            trial_insights = synthesize_insights(trial_categorized, min_quality=best_thresholds["min_quality_for_insights"])
            trial_score = evaluate_insight_quality(trial_insights)

            if trial_score > current_insight_score:
                best_weights = candidate_weights
                best_insight_score = trial_score
                weights_mutated = "yes (improved)"

            # Try mutated thresholds every 3 rounds
            if round_num % 3 == 0:
                candidate_thresholds = mutate_thresholds(best_thresholds)
                trial_insights_t = synthesize_insights(
                    all_categorized,
                    min_quality=candidate_thresholds["min_quality_for_insights"],
                )
                trial_score_t = evaluate_insight_quality(trial_insights_t)
                if trial_score_t > current_insight_score:
                    best_thresholds = candidate_thresholds
                    thresholds_mutated = "yes (improved)"

            # ------------------------------------------------------------------
            # Step 8: Log the round
            # ------------------------------------------------------------------
            hub_top3 = ", ".join(
                h["verse_id"] for h in meta.get("hub_verses", [])[:3]
            )
            pat_top3 = "; ".join(
                "+".join(p["keyword_pair"]) for p in meta.get("structural_patterns", [])[:3]
            )
            clusters_found = len(meta.get("deduction_clusters", []))

            append_analysis_log({
                "round": round_num,
                "timestamp": datetime.now().isoformat(),
                "new_deductions": len(new_deductions),
                "total_deductions": len(all_categorized),
                "hub_verses_top3": hub_top3,
                "structural_patterns_top3": pat_top3,
                "clusters_found": clusters_found,
                "insight_quality_score": current_insight_score,
                "weights_mutated": weights_mutated,
                "thresholds_mutated": thresholds_mutated,
            })

            # ------------------------------------------------------------------
            # Print progress every 5 rounds
            # ------------------------------------------------------------------
            elapsed_round = time.time() - round_start
            if round_num % 5 == 0 or round_num == 1:
                hours = elapsed_total / 3600
                print(
                    f"[round {round_num:5d}] "
                    f"+{len(new_deductions):4d} new, "
                    f"{len(all_categorized):6d} total | "
                    f"insights: {len(insights):4d} (score {current_insight_score:.1f}) | "
                    f"clusters: {clusters_found:3d} | "
                    f"hubs: {hub_top3 or 'none'} | "
                    f"{elapsed_round:.1f}s | "
                    f"{hours:.2f}h elapsed"
                )
                if weights_mutated.startswith("yes"):
                    print(f"  >> Weights improved! New best score: {best_insight_score:.1f}")
                if thresholds_mutated.startswith("yes"):
                    print(f"  >> Thresholds improved! {best_thresholds}")

            # Sleep until next poll
            sleep_remaining = max(0, POLL_INTERVAL_SECONDS - (time.time() - round_start))
            if sleep_remaining > 0:
                time.sleep(sleep_remaining)

    except KeyboardInterrupt:
        print("\n\n  Interrupted by user.")

    # -----------------------------------------------------------------------
    # Final summary
    # -----------------------------------------------------------------------
    total_time = time.time() - start_time
    print(f"\n{'=' * 70}")
    print("  ANALYSIS LOOP COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Rounds:                {round_num}")
    print(f"  Total analyzed:        {len(all_categorized)}")
    print(f"  Time:                  {total_time / 60:.1f} minutes")
    print(f"  Best insight score:    {best_insight_score:.1f}")
    print(f"  Optimized weights:     {best_weights}")
    print(f"  Optimized thresholds:  {best_thresholds}")
    print(f"\n  Output files:")
    print(f"    {META_GRAPH_PATH}")
    print(f"    {INSIGHTS_PATH}")
    print(f"    {CATEGORIZED_PATH}")
    print(f"    {META_INSIGHTS_PATH}")
    print(f"    {ANALYSIS_ROUNDS_LOG}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
