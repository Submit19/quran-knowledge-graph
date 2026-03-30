#!/usr/bin/env python3
"""
AutoResearch on the Deduction Meta-Knowledge Graph.

Optimizes the meta-graph structure by varying:
  - Category definitions (keyword sets)
  - Quality scoring weights
  - Categorization thresholds
  - Meta-graph edge filters

Metric: quality and diversity of discovered theme-to-theme connections.
"""

import copy
import json
import math
import os
import random
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_deductions import (
    THEOLOGICAL_CATEGORIES, categorize_deduction, score_quality,
    build_meta_graph, synthesize_insights, load_verses_text
)

import csv
csv.field_size_limit(sys.maxsize)

AUTORESEARCH_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_TSV = os.path.join(AUTORESEARCH_DIR, "metagraph_results.tsv")
BEST_CONFIG_JSON = os.path.join(AUTORESEARCH_DIR, "best_metagraph_config.json")

# ══════════════════════════════════════════════════════════════════════════════
# Tunable meta-graph parameters
# ══════════════════════════════════════════════════════════════════════════════

META_PARAMS = {
    "min_quality_for_graph": 50,
    "min_quality_for_insights": 55,
    "quality_weight_specificity": 0.20,
    "quality_weight_surah_diversity": 0.15,
    "quality_weight_meaningfulness": 0.15,
    "quality_weight_coherence": 0.20,
    "quality_weight_relevance": 0.15,
    "quality_weight_rule_bonus": 0.15,
    "min_insight_support": 2,       # min deductions per insight
    "max_insights": 200,
}

SEARCH_SPACE = {
    "min_quality_for_graph":    (30, 80, "int", 5),
    "min_quality_for_insights": (40, 80, "int", 5),
    "quality_weight_specificity":    (0.05, 0.40, "float", 0.05),
    "quality_weight_surah_diversity": (0.05, 0.30, "float", 0.05),
    "quality_weight_meaningfulness":  (0.05, 0.30, "float", 0.05),
    "quality_weight_coherence":       (0.05, 0.40, "float", 0.05),
    "quality_weight_relevance":       (0.05, 0.30, "float", 0.05),
    "quality_weight_rule_bonus":      (0.05, 0.30, "float", 0.05),
    "min_insight_support":     (2, 10, "int", 1),
}


def load_deductions(max_count=50000):
    """Load deductions from JSONL."""
    path = os.path.join(AUTORESEARCH_DIR, "all_deductions.jsonl")
    if not os.path.exists(path):
        return []
    deductions = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                deductions.append(json.loads(line.strip()))
                if len(deductions) >= max_count:
                    break
    return deductions


def evaluate_meta_graph(deductions, verses_text, params):
    """Build and evaluate the meta-graph with given parameters."""
    # Re-score quality with current weights
    weight_keys = [k for k in params if k.startswith("quality_weight_")]
    weights = {k.replace("quality_weight_", ""): params[k] for k in weight_keys}
    # Normalize weights
    total_w = sum(weights.values())
    if total_w > 0:
        weights = {k: v / total_w for k, v in weights.items()}

    categorized = []
    for d in deductions:
        cats = categorize_deduction(d, verses_text)
        quality, _ = score_quality(d, verses_text)
        categorized.append({
            **d,
            "categories": cats,
            "quality_score": quality,
        })

    # Build meta-graph
    meta = build_meta_graph(categorized, min_quality=params["min_quality_for_graph"])

    # Build insights
    insights = synthesize_insights(categorized, min_quality=params["min_quality_for_insights"])

    # ── Evaluation metrics ──

    # 1. Theme coverage: how many of 13 categories are represented?
    theme_coverage = len(meta["nodes"]) / 13 * 100

    # 2. Edge density: how many theme-to-theme connections?
    max_edges = 13 * 12 / 2  # 78 possible
    edge_coverage = len(meta["edges"]) / max_edges * 100

    # 3. Average edge quality
    avg_quality = 0
    if meta["edges"]:
        avg_quality = sum(e["avg_quality"] for e in meta["edges"]) / len(meta["edges"])

    # 4. Insight quantity and quality
    insight_score = min(100, len(insights) / 2)  # 200+ insights = 100
    avg_insight_quality = 0
    if insights:
        avg_insight_quality = sum(i["avg_quality"] for i in insights[:100]) / min(100, len(insights))

    # 5. Distribution balance (penalize if one category dominates)
    if meta["edges"]:
        weights_list = [e["weight"] for e in meta["edges"]]
        max_w = max(weights_list)
        avg_w = sum(weights_list) / len(weights_list)
        balance = min(100, (avg_w / max_w) * 200) if max_w > 0 else 0
    else:
        balance = 0

    # Composite
    composite = (
        0.15 * theme_coverage +
        0.15 * edge_coverage +
        0.20 * avg_quality +
        0.15 * insight_score +
        0.20 * avg_insight_quality +
        0.15 * balance
    )

    return {
        "theme_coverage": round(theme_coverage, 2),
        "edge_coverage": round(edge_coverage, 2),
        "avg_quality": round(avg_quality, 2),
        "insight_count": len(insights),
        "avg_insight_quality": round(avg_insight_quality, 2),
        "balance": round(balance, 2),
        "composite_score": round(composite, 2),
        "meta_graph": meta,
        "insights": insights,
        "categorized": categorized,
    }


def mutate_params(params):
    new = copy.deepcopy(params)
    mutations = []
    n = random.choice([1, 1, 2, 2, 3])
    keys = list(SEARCH_SPACE.keys())
    chosen = random.sample(keys, min(n, len(keys)))

    for key in chosen:
        spec = SEARCH_SPACE[key]
        old_val = new.get(key, 0)
        if spec[2] == "int":
            lo, hi, _, step = spec
            delta = random.choice([-1, 1]) * step * random.randint(1, 2)
            new_val = max(lo, min(hi, int(old_val + delta)))
        elif spec[2] == "float":
            lo, hi, _, step = spec
            delta = random.choice([-1, 1]) * step * random.uniform(0.5, 2.0)
            new_val = round(max(lo, min(hi, old_val + delta)), 3)
        else:
            continue
        mutations.append(f"{key}: {old_val} -> {new_val}")
        new[key] = new_val

    return new, mutations


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-experiments", type=int, default=100)
    args = parser.parse_args()

    print("=" * 70)
    print("  META-GRAPH AutoResearch Optimization")
    print("=" * 70)

    print("\nLoading data...")
    deductions = load_deductions(max_count=20000)
    verses_text = load_verses_text()
    print(f"  {len(deductions)} deductions, {len(verses_text)} verses")

    if not deductions:
        print("No deductions found. Run the deduction loop first.")
        return

    # Sample for speed
    if len(deductions) > 5000:
        sample = random.sample(deductions, 5000)
    else:
        sample = deductions

    # Baseline
    print("\nEvaluating baseline...")
    params = copy.deepcopy(META_PARAMS)
    baseline = evaluate_meta_graph(sample, verses_text, params)
    best_score = baseline["composite_score"]
    best_params = copy.deepcopy(params)

    print(f"  Baseline: {best_score:.2f}")
    print(f"  Theme coverage: {baseline['theme_coverage']:.0f}%")
    print(f"  Edge coverage: {baseline['edge_coverage']:.0f}%")
    print(f"  Avg quality: {baseline['avg_quality']:.1f}")
    print(f"  Insights: {baseline['insight_count']}")

    if not os.path.exists(RESULTS_TSV):
        with open(RESULTS_TSV, "w") as f:
            f.write("experiment\tscore\tbest\tkept\tmutations\n")

    improvements = 0
    for i in range(1, args.max_experiments + 1):
        new_params, mutations = mutate_params(best_params)
        try:
            result = evaluate_meta_graph(sample, verses_text, new_params)
            new_score = result["composite_score"]
        except Exception as e:
            print(f"[{i}] FAILED: {e}")
            continue

        if new_score > best_score:
            improvements += 1
            print(f"[{i}] IMPROVED! {best_score:.2f} -> {new_score:.2f} | {', '.join(mutations)}")
            best_score = new_score
            best_params = copy.deepcopy(new_params)

            # Save best config
            with open(BEST_CONFIG_JSON, "w") as f:
                json.dump({"score": best_score, "params": best_params}, f, indent=2)

            # Save updated outputs
            if result["meta_graph"]:
                with open(os.path.join(AUTORESEARCH_DIR, "meta_knowledge_graph.json"), "w") as f:
                    json.dump(result["meta_graph"], f, indent=2, ensure_ascii=False)
            if result["insights"]:
                with open(os.path.join(AUTORESEARCH_DIR, "synthesized_insights.json"), "w") as f:
                    json.dump(result["insights"][:200], f, indent=2, ensure_ascii=False)

        with open(RESULTS_TSV, "a") as f:
            f.write(f"{i}\t{new_score:.4f}\t{best_score:.4f}\t{new_score > best_score - 0.001}\t{'; '.join(mutations)}\n")

        if i % 20 == 0:
            print(f"  --- {i}/{args.max_experiments}, {improvements} improvements, best: {best_score:.2f} ---")

    print(f"\n{'='*70}")
    print(f"  COMPLETE: {improvements} improvements, final: {best_score:.2f}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
