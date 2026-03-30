#!/usr/bin/env python3
"""
Contradiction Detection Loop — AutoResearch for Quranic Verse Tensions.

Runs continuously, detecting apparent contradictions and tensions between
Quranic verses that share thematic connections in the knowledge graph.

Each round:
  1. Sample connected verse pairs (sharing keywords)
  2. Analyze texts for potential tensions (sentiment divergence, conditional
     vs absolute statements, universal vs particular claims)
  3. Score and classify each tension
  4. Save results to contradictions.json (continuously updated)
  5. Log rounds to contradiction_rounds.tsv

Tension types:
  - apparent_contradiction: Same topic, opposing claims
  - conditional_tension: One verse conditional, other absolute
  - scope_tension: One verse universal, other particular
  - mercy_justice_tension: Forgiveness vs punishment
  - abrogation_candidate: Possibly superseded ruling
"""

import argparse
import json
import os
import random
import re
import sys
import tempfile
import time
from collections import defaultdict
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTORESEARCH_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AUTORESEARCH_DIR)

from deduction_engine import load_graph

# ══════════════════════════════════════════════════════════════════════════════
# Output files
# ══════════════════════════════════════════════════════════════════════════════

CONTRADICTIONS_FILE = os.path.join(AUTORESEARCH_DIR, "contradictions.json")
ROUND_LOG = os.path.join(AUTORESEARCH_DIR, "contradiction_rounds.tsv")

# ══════════════════════════════════════════════════════════════════════════════
# Sentiment word sets
# ══════════════════════════════════════════════════════════════════════════════

POSITIVE = {
    "forgive", "mercy", "merciful", "reward", "paradise", "bless", "save",
    "guide", "love", "peace", "righteous", "grace", "compassion", "patient",
    "kind", "gentle", "permit", "allow", "accept", "redeem",
}

NEGATIVE = {
    "punish", "hell", "fire", "retribution", "curse", "wrath", "doom",
    "destroy", "forbid", "prohibit", "reject", "torment", "severe", "enemy",
    "wicked", "evil", "kill", "slay", "banish", "condemn",
}

# ══════════════════════════════════════════════════════════════════════════════
# Theological significance keywords — topics touching God's nature, judgment,
# law, salvation, and eschatology score higher.
# ══════════════════════════════════════════════════════════════════════════════

THEOLOGICAL_CORE = {
    "god", "allah", "lord", "judgment", "law", "decree", "salvation",
    "heaven", "hell", "paradise", "fire", "mercy", "justice", "forgive",
    "punish", "worship", "faith", "belief", "disbelief", "prayer",
    "righteous", "sin", "repent", "repentance", "prophet", "messenger",
    "scripture", "revelation", "command", "obey", "disobey",
}

# ══════════════════════════════════════════════════════════════════════════════
# Opposite-sentiment word pairs for direct tension detection
# ══════════════════════════════════════════════════════════════════════════════

OPPOSITE_PAIRS = [
    ("forgive", "punish"), ("mercy", "wrath"), ("reward", "retribution"),
    ("paradise", "hell"), ("permit", "prohibit"), ("allow", "forbid"),
    ("save", "destroy"), ("bless", "curse"), ("guide", "banish"),
    ("accept", "reject"), ("love", "enemy"), ("peace", "torment"),
    ("gentle", "severe"), ("kind", "wicked"), ("redeem", "condemn"),
    ("patient", "doom"), ("righteous", "evil"),
]

# ══════════════════════════════════════════════════════════════════════════════
# Patterns for conditional / unconditional / universal / particular detection
# ══════════════════════════════════════════════════════════════════════════════

CONDITIONAL_PATTERNS = [
    re.compile(r"\bif\b", re.IGNORECASE),
    re.compile(r"\bwhen\b", re.IGNORECASE),
    re.compile(r"\bwhoever\b", re.IGNORECASE),
    re.compile(r"\bthose who\b", re.IGNORECASE),
    re.compile(r"\bunless\b", re.IGNORECASE),
    re.compile(r"\bexcept\b", re.IGNORECASE),
    re.compile(r"\bprovided\b", re.IGNORECASE),
]

UNIVERSAL_PATTERNS = [
    re.compile(r"\ball\b", re.IGNORECASE),
    re.compile(r"\bevery\b", re.IGNORECASE),
    re.compile(r"\bnone\b", re.IGNORECASE),
    re.compile(r"\bno one\b", re.IGNORECASE),
    re.compile(r"\balways\b", re.IGNORECASE),
    re.compile(r"\bnever\b", re.IGNORECASE),
]

PARTICULAR_PATTERNS = [
    re.compile(r"\bsome\b", re.IGNORECASE),
    re.compile(r"\bamong them\b", re.IGNORECASE),
    re.compile(r"\ba group\b", re.IGNORECASE),
    re.compile(r"\bmany\b", re.IGNORECASE),
    re.compile(r"\bfew\b", re.IGNORECASE),
    re.compile(r"\bmost\b", re.IGNORECASE),
]

RULING_PATTERNS = [
    re.compile(r"\bprescribed\b", re.IGNORECASE),
    re.compile(r"\bdecreed?\b", re.IGNORECASE),
    re.compile(r"\bordained?\b", re.IGNORECASE),
    re.compile(r"\bpermitted?\b", re.IGNORECASE),
    re.compile(r"\bforbidden\b", re.IGNORECASE),
    re.compile(r"\bprohibited?\b", re.IGNORECASE),
    re.compile(r"\blawful\b", re.IGNORECASE),
    re.compile(r"\bunlawful\b", re.IGNORECASE),
]


# ══════════════════════════════════════════════════════════════════════════════
# Analysis helpers
# ══════════════════════════════════════════════════════════════════════════════

def _words(text):
    """Return lowercased word set from text."""
    return set(re.findall(r"[a-z]+", text.lower()))


def sentiment_score(text):
    """Return (positive_count, negative_count) for a verse text."""
    words = _words(text)
    pos = len(words & POSITIVE)
    neg = len(words & NEGATIVE)
    return pos, neg


def sentiment_divergence(text_a, text_b):
    """
    Score how much sentiment diverges between two texts.
    Returns 0.0-1.0 where 1.0 = maximally divergent.
    """
    pos_a, neg_a = sentiment_score(text_a)
    pos_b, neg_b = sentiment_score(text_b)

    # One text positive-leaning, other negative-leaning
    total_a = pos_a + neg_a
    total_b = pos_b + neg_b
    if total_a == 0 and total_b == 0:
        return 0.0

    # Compute sentiment polarity for each (-1 to +1)
    polarity_a = (pos_a - neg_a) / max(1, total_a)
    polarity_b = (pos_b - neg_b) / max(1, total_b)

    # Divergence is the absolute difference, normalized to 0-1
    return min(1.0, abs(polarity_a - polarity_b) / 2.0)


def find_opposite_pairs(text_a, text_b):
    """Find which opposite word pairs fire between two texts."""
    words_a = _words(text_a)
    words_b = _words(text_b)
    found = []
    for w1, w2 in OPPOSITE_PAIRS:
        if (w1 in words_a and w2 in words_b) or (w2 in words_a and w1 in words_b):
            found.append((w1, w2))
    return found


def is_conditional(text):
    """Check if text contains conditional language."""
    return any(p.search(text) for p in CONDITIONAL_PATTERNS)


def is_universal(text):
    """Check if text contains universal quantifiers."""
    return any(p.search(text) for p in UNIVERSAL_PATTERNS)


def is_particular(text):
    """Check if text contains particular quantifiers."""
    return any(p.search(text) for p in PARTICULAR_PATTERNS)


def is_ruling(text):
    """Check if text contains legal/ruling language."""
    return any(p.search(text) for p in RULING_PATTERNS)


def theological_significance(text_a, text_b):
    """Score 0.0-1.0 for how theologically significant the pair is."""
    words = _words(text_a) | _words(text_b)
    overlap = words & THEOLOGICAL_CORE
    # Normalize: 5+ core terms = max significance
    return min(1.0, len(overlap) / 5.0)


def keyword_overlap_score(keywords_a, keywords_b):
    """
    Score 0.0-1.0 for keyword overlap between two verses.
    Higher overlap = more related, making any tension more meaningful.
    """
    set_a = set(kw for kw, _ in keywords_a)
    set_b = set(kw for kw, _ in keywords_b)
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


# ══════════════════════════════════════════════════════════════════════════════
# Tension classification
# ══════════════════════════════════════════════════════════════════════════════

def classify_tension(text_a, text_b, opposite_pairs):
    """
    Classify the type of tension between two verse texts.
    Returns a list of (tension_type, confidence) tuples.
    """
    tensions = []

    # mercy_justice_tension: forgiveness vs punishment keywords
    mercy_justice_pairs = {
        ("forgive", "punish"), ("mercy", "wrath"), ("reward", "retribution"),
        ("paradise", "hell"), ("save", "destroy"), ("bless", "curse"),
        ("redeem", "condemn"),
    }
    mj_matches = [p for p in opposite_pairs if p in mercy_justice_pairs
                  or (p[1], p[0]) in mercy_justice_pairs]
    if mj_matches:
        conf = min(1.0, len(mj_matches) * 0.4)
        tensions.append(("mercy_justice_tension", conf))

    # conditional_tension: one conditional, other absolute
    cond_a = is_conditional(text_a)
    cond_b = is_conditional(text_b)
    if cond_a != cond_b:
        tensions.append(("conditional_tension", 0.6))

    # scope_tension: one universal, other particular
    univ_a = is_universal(text_a)
    univ_b = is_universal(text_b)
    part_a = is_particular(text_a)
    part_b = is_particular(text_b)
    if (univ_a and part_b) or (univ_b and part_a):
        tensions.append(("scope_tension", 0.7))

    # abrogation_candidate: both contain rulings but with opposite sentiment
    if is_ruling(text_a) and is_ruling(text_b) and opposite_pairs:
        tensions.append(("abrogation_candidate", 0.5))

    # apparent_contradiction: strong opposite pairs on same topic without
    # conditional or scope explanation
    if opposite_pairs and not tensions:
        conf = min(1.0, len(opposite_pairs) * 0.35)
        tensions.append(("apparent_contradiction", conf))
    elif opposite_pairs and len(opposite_pairs) >= 2:
        # Multiple opposing pairs even with other classifications = also flag
        tensions.append(("apparent_contradiction", min(1.0, len(opposite_pairs) * 0.3)))

    return tensions


# ══════════════════════════════════════════════════════════════════════════════
# Scoring
# ══════════════════════════════════════════════════════════════════════════════

def score_tension(kw_overlap, sent_div, theo_sig, opposite_pairs, tensions):
    """
    Compute a composite tension score (0-100).

    Weights:
      - keyword overlap:          20%  (more related = more meaningful)
      - sentiment divergence:     30%
      - theological significance: 25%
      - opposite pair count:      15%
      - classification confidence: 10%
    """
    pair_score = min(1.0, len(opposite_pairs) / 3.0)
    max_conf = max((conf for _, conf in tensions), default=0.0)

    composite = (
        kw_overlap * 20
        + sent_div * 30
        + theo_sig * 25
        + pair_score * 15
        + max_conf * 10
    )
    return round(composite, 2)


# ══════════════════════════════════════════════════════════════════════════════
# Pair sampling
# ══════════════════════════════════════════════════════════════════════════════

def sample_connected_pairs(graph, n_pairs=200):
    """
    Sample verse pairs that share at least one keyword.
    Uses keyword_verses to find co-occurring verses.
    """
    pairs = set()
    keywords = list(graph["keyword_verses"].keys())
    if not keywords:
        return []

    random.shuffle(keywords)
    for kw in keywords:
        verse_list = graph["keyword_verses"][kw]
        if len(verse_list) < 2:
            continue
        # Sample pairs from verses sharing this keyword
        sample_size = min(len(verse_list), 20)
        sampled = random.sample(verse_list, sample_size)
        for i in range(len(sampled)):
            for j in range(i + 1, len(sampled)):
                vid_a = sampled[i][0]
                vid_b = sampled[j][0]
                if vid_a < vid_b:
                    pairs.add((vid_a, vid_b))
                else:
                    pairs.add((vid_b, vid_a))
                if len(pairs) >= n_pairs * 3:
                    break
            if len(pairs) >= n_pairs * 3:
                break
        if len(pairs) >= n_pairs * 3:
            break

    # Return a random subset
    pairs_list = list(pairs)
    if len(pairs_list) > n_pairs:
        pairs_list = random.sample(pairs_list, n_pairs)
    return pairs_list


# ══════════════════════════════════════════════════════════════════════════════
# One round of analysis
# ══════════════════════════════════════════════════════════════════════════════

def analyze_pair(graph, vid_a, vid_b):
    """
    Analyze a single verse pair for tension.
    Returns a tension dict or None if no meaningful tension found.
    """
    verse_a = graph["verses"].get(vid_a)
    verse_b = graph["verses"].get(vid_b)
    if not verse_a or not verse_b:
        return None

    text_a = verse_a["text"]
    text_b = verse_b["text"]

    # Quick filter: need at least one opposite pair or sentiment divergence
    opposite_pairs = find_opposite_pairs(text_a, text_b)
    sent_div = sentiment_divergence(text_a, text_b)

    if not opposite_pairs and sent_div < 0.3:
        return None

    # Detailed analysis
    kw_a = graph["verse_keywords"].get(vid_a, [])
    kw_b = graph["verse_keywords"].get(vid_b, [])
    kw_overlap = keyword_overlap_score(kw_a, kw_b)

    theo_sig = theological_significance(text_a, text_b)
    tensions = classify_tension(text_a, text_b, opposite_pairs)

    if not tensions:
        return None

    score = score_tension(kw_overlap, sent_div, theo_sig, opposite_pairs, tensions)

    # Minimum score threshold
    if score < 15.0:
        return None

    shared_keywords = sorted(
        set(kw for kw, _ in kw_a) & set(kw for kw, _ in kw_b)
    )

    return {
        "verse_a": vid_a,
        "verse_b": vid_b,
        "surah_a": verse_a.get("surahName", verse_a.get("surah", "")),
        "surah_b": verse_b.get("surahName", verse_b.get("surah", "")),
        "text_a": text_a[:300],
        "text_b": text_b[:300],
        "tension_types": [(t, round(c, 3)) for t, c in tensions],
        "primary_type": tensions[0][0],
        "opposite_pairs": opposite_pairs,
        "shared_keywords": shared_keywords[:10],
        "keyword_overlap": round(kw_overlap, 4),
        "sentiment_divergence": round(sent_div, 4),
        "theological_significance": round(theo_sig, 4),
        "score": score,
    }


def run_one_round(graph, seen_pairs, round_num, pairs_per_round=200):
    """Run one round of contradiction detection. Returns list of new tensions."""
    t0 = time.time()

    candidates = sample_connected_pairs(graph, n_pairs=pairs_per_round)

    new_tensions = []
    pairs_analyzed = 0

    for vid_a, vid_b in candidates:
        pair_key = (vid_a, vid_b)
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)
        pairs_analyzed += 1

        result = analyze_pair(graph, vid_a, vid_b)
        if result:
            result["round"] = round_num
            result["timestamp"] = datetime.now().isoformat()
            new_tensions.append(result)

    elapsed = time.time() - t0
    return new_tensions, pairs_analyzed, elapsed


# ══════════════════════════════════════════════════════════════════════════════
# File I/O with atomic writes
# ══════════════════════════════════════════════════════════════════════════════

def atomic_json_write(filepath, data):
    """Write JSON atomically using a temp file + rename."""
    dir_name = os.path.dirname(filepath)
    try:
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, filepath)
    except OSError as e:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise e


def load_existing_contradictions():
    """Load previously found contradictions, if any."""
    if not os.path.exists(CONTRADICTIONS_FILE):
        return []
    try:
        with open(CONTRADICTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def rebuild_seen_pairs(all_tensions):
    """Rebuild the set of already-analyzed pairs from saved tensions."""
    seen = set()
    for t in all_tensions:
        va = t.get("verse_a", "")
        vb = t.get("verse_b", "")
        if va < vb:
            seen.add((va, vb))
        else:
            seen.add((vb, va))
    return seen


# ══════════════════════════════════════════════════════════════════════════════
# Main loop
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Contradiction Detection Loop for Quran Knowledge Graph"
    )
    parser.add_argument(
        "--max-hours", type=float, default=0,
        help="Maximum hours to run (0 = infinite)"
    )
    parser.add_argument(
        "--max-rounds", type=int, default=0,
        help="Maximum rounds to run (0 = infinite)"
    )
    parser.add_argument(
        "--pairs-per-round", type=int, default=200,
        help="Verse pairs to sample each round"
    )
    args = parser.parse_args()

    max_rounds = args.max_rounds if args.max_rounds > 0 else float("inf")
    max_seconds = args.max_hours * 3600 if args.max_hours > 0 else float("inf")

    print("=" * 70)
    print("  CONTRADICTION DETECTION LOOP — Quranic Verse Tension Analysis")
    print("=" * 70)
    print(f"  Time limit:    {'none' if max_seconds == float('inf') else f'{args.max_hours}h'}")
    print(f"  Round limit:   {'infinite' if max_rounds == float('inf') else max_rounds}")
    print(f"  Pairs/round:   {args.pairs_per_round}")

    # Load graph
    print("\nLoading graph...")
    try:
        graph = load_graph()
    except FileNotFoundError as e:
        print(f"  ERROR: Could not load graph data: {e}")
        print("  Make sure data/ directory contains verse_nodes.csv, "
              "verse_keyword_rels.csv, verse_related_rels.csv")
        sys.exit(1)

    print(f"  {len(graph['verses'])} verses, "
          f"{len(graph['keyword_verses'])} keywords, "
          f"{sum(len(v) for v in graph['related'].values()) // 2} edges")

    # Load existing results
    all_tensions = load_existing_contradictions()
    seen_pairs = rebuild_seen_pairs(all_tensions)
    print(f"  Loaded {len(all_tensions)} previous tensions, "
          f"{len(seen_pairs)} pairs already analyzed")

    # Initialize round log
    if not os.path.exists(ROUND_LOG):
        with open(ROUND_LOG, "w", encoding="utf-8") as f:
            f.write("round\ttimestamp\tnew_tensions\ttotal_tensions\t"
                    "pairs_analyzed\telapsed_s\ttop_type\ttop_score\n")

    print(f"\n{'=' * 70}")
    print("  Starting contradiction detection loop...")
    print(f"{'=' * 70}\n")

    start_time = time.time()
    round_num = 0
    total_new = 0

    while round_num < max_rounds:
        round_num += 1
        elapsed_total = time.time() - start_time

        if elapsed_total > max_seconds:
            print(f"\n  Time limit reached ({args.max_hours}h)")
            break

        # Run one round
        new_tensions, pairs_analyzed, elapsed = run_one_round(
            graph, seen_pairs, round_num,
            pairs_per_round=args.pairs_per_round,
        )

        total_new += len(new_tensions)

        if new_tensions:
            # Merge and sort all tensions by score
            all_tensions.extend(new_tensions)
            all_tensions.sort(key=lambda t: -t["score"])

            # Save atomically
            try:
                atomic_json_write(CONTRADICTIONS_FILE, all_tensions)
            except OSError as e:
                print(f"  WARNING: Could not write {CONTRADICTIONS_FILE}: {e}")

        # Determine top result for logging
        top_type = ""
        top_score = 0.0
        if new_tensions:
            best = max(new_tensions, key=lambda t: t["score"])
            top_type = best["primary_type"]
            top_score = best["score"]

        # Log round
        try:
            with open(ROUND_LOG, "a", encoding="utf-8") as f:
                f.write(f"{round_num}\t{datetime.now().isoformat()}\t"
                        f"{len(new_tensions)}\t{len(all_tensions)}\t"
                        f"{pairs_analyzed}\t{elapsed:.1f}\t"
                        f"{top_type}\t{top_score}\n")
        except OSError:
            pass

        # Print progress
        if new_tensions:
            best = max(new_tensions, key=lambda t: t["score"])
            print(f"[round {round_num:4d}] {len(new_tensions):3d} tensions found "
                  f"(total: {len(all_tensions)}) [{elapsed:.1f}s] "
                  f"pairs={pairs_analyzed}")
            print(f"  TOP: {best['primary_type']} score={best['score']:.1f} "
                  f"| {best['verse_a']} vs {best['verse_b']}")
            if best["opposite_pairs"]:
                pairs_str = ", ".join(
                    f"{a}<->{b}" for a, b in best["opposite_pairs"][:3]
                )
                print(f"       opposites: {pairs_str}")
        elif round_num % 10 == 0:
            print(f"[round {round_num:4d}]   0 tensions "
                  f"(total: {len(all_tensions)}) [{elapsed:.1f}s] "
                  f"pairs={pairs_analyzed}")

        # Periodic summary every 10 rounds
        if round_num % 10 == 0:
            hours = elapsed_total / 3600
            rate = total_new / max(1, elapsed_total) * 3600
            type_counts = defaultdict(int)
            for t in all_tensions:
                type_counts[t["primary_type"]] += 1
            type_summary = ", ".join(
                f"{k}={v}" for k, v in sorted(
                    type_counts.items(), key=lambda x: -x[1]
                )
            )
            print(f"\n  === PROGRESS: {round_num} rounds | "
                  f"{len(all_tensions)} tensions | "
                  f"{hours:.2f}h elapsed | "
                  f"{rate:.0f}/hr ===")
            print(f"  === Types: {type_summary} ===")
            if all_tensions:
                print(f"  === Top score: {all_tensions[0]['score']:.1f} | "
                      f"Avg: {sum(t['score'] for t in all_tensions) / len(all_tensions):.1f} ===\n")
            else:
                print()

    # Final summary
    total_time = time.time() - start_time
    print(f"\n{'=' * 70}")
    print("  CONTRADICTION DETECTION COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Rounds:           {round_num}")
    print(f"  Tensions found:   {len(all_tensions)}")
    print(f"  Pairs analyzed:   {len(seen_pairs)}")
    print(f"  Time:             {total_time / 60:.1f} minutes")
    print(f"  Rate:             {total_new / max(1, total_time) * 3600:.0f} tensions/hr")
    print(f"  Output:           {CONTRADICTIONS_FILE}")
    print(f"  Round log:        {ROUND_LOG}")
    print(f"{'=' * 70}")

    # Print top 10
    if all_tensions:
        print(f"\n  TOP 10 TENSIONS:")
        for i, t in enumerate(all_tensions[:10]):
            types = ", ".join(f"{tt}({c:.2f})" for tt, c in t["tension_types"])
            print(f"\n  #{i + 1} [score: {t['score']:.1f}] {types}")
            print(f"     {t['verse_a']} ({t['surah_a']}) vs "
                  f"{t['verse_b']} ({t['surah_b']})")
            if t["opposite_pairs"]:
                print(f"     Opposites: {t['opposite_pairs']}")
            if t["shared_keywords"]:
                print(f"     Shared:    {t['shared_keywords'][:5]}")
            print(f"     A: {t['text_a'][:120]}...")
            print(f"     B: {t['text_b'][:120]}...")


if __name__ == "__main__":
    main()
