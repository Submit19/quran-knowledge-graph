"""
eval_common.py — shared helpers for all QKG eval scripts.

Canonical home for:
  - expand_verse_range   : parse QRCD verse range strings to set of "surah:verse" ids
  - load_qrcd_grouped    : group QRCD test-set items by question, gold = union of passages
  - hit_at_k             : bool — any retrieved id in gold within top-k?
  - recall_at_k          : fraction of gold verses retrieved within top-k
  - first_hit_rank       : 1-based rank of first hit (None if miss)
  - average_precision_at_k : AP@k for MAP computation

Import pattern (drop-in replacement for inline copies):

    from eval_common import (
        expand_verse_range, load_qrcd_grouped,
        hit_at_k, recall_at_k, first_hit_rank, average_precision_at_k,
    )
"""

import json
from collections import defaultdict
from pathlib import Path

# ------------------------------------------------------------------
# Default QRCD path — can be overridden by callers
# ------------------------------------------------------------------
QRCD_PATH = Path(__file__).parent / "data" / "qrcd_test.jsonl"


# ------------------------------------------------------------------
# Core helpers
# ------------------------------------------------------------------

def expand_verse_range(surah, vrange) -> set:
    """Parse a QRCD verse-range string like '3,7-9' into a set of 'surah:verse' ids."""
    out = set()
    for chunk in str(vrange).split(","):
        chunk = chunk.strip()
        if "-" in chunk:
            a, b = chunk.split("-", 1)
            try:
                for v in range(int(a), int(b) + 1):
                    out.add(f"{surah}:{v}")
            except ValueError:
                pass
        else:
            try:
                int(chunk)
                out.add(f"{surah}:{chunk}")
            except ValueError:
                pass
    return out


def load_qrcd_grouped(qrcd_path=None) -> list:
    """
    Load QRCD test-set and group by question.

    Returns list of dicts:
        {
          'question': str,
          'gold': list[str],          # sorted list of 'surah:verse' ids (union across passages)
          'n_gold_verses': int,
          'n_passages': int,
        }
    Sorted by n_gold_verses descending (largest gold set first).
    """
    path = Path(qrcd_path) if qrcd_path else QRCD_PATH
    items = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_q = defaultdict(lambda: {"gold": set(), "n_passages": 0})
    for it in items:
        gold = expand_verse_range(it["surah"], it["verses"])
        by_q[it["question"]]["gold"] |= gold
        by_q[it["question"]]["n_passages"] += 1
    grouped = [
        {
            "question": q,
            "gold": sorted(d["gold"]),
            "n_gold_verses": len(d["gold"]),
            "n_passages": d["n_passages"],
        }
        for q, d in by_q.items()
    ]
    grouped.sort(key=lambda x: -x["n_gold_verses"])
    return grouped


# ------------------------------------------------------------------
# Metrics
# ------------------------------------------------------------------

def hit_at_k(retrieved_ids, gold, k) -> bool:
    """Return True if any of the top-k retrieved ids appears in gold."""
    gold_set = gold if isinstance(gold, (set, frozenset)) else set(gold)
    return any(r in gold_set for r in retrieved_ids[:k])


def recall_at_k(retrieved_ids, gold, k) -> float:
    """Return |retrieved[:k] ∩ gold| / |gold|. Returns 0.0 for empty gold."""
    gold_set = gold if isinstance(gold, (set, frozenset)) else set(gold)
    if not gold_set:
        return 0.0
    return sum(1 for r in retrieved_ids[:k] if r in gold_set) / len(gold_set)


def first_hit_rank(retrieved_ids, gold) -> "int | None":
    """Return 1-based rank of first hit, or None if no hit."""
    gold_set = gold if isinstance(gold, (set, frozenset)) else set(gold)
    for i, r in enumerate(retrieved_ids, 1):
        if r in gold_set:
            return i
    return None


def average_precision_at_k(retrieved_ids, gold, k) -> float:
    """AP@k = sum(precision@i * relevant(i)) / min(|gold|, k). Returns 0.0 for empty gold."""
    gold_set = gold if isinstance(gold, (set, frozenset)) else set(gold)
    if not gold_set:
        return 0.0
    correct = 0
    sum_p = 0.0
    for i, r in enumerate(retrieved_ids[:k], 1):
        if r in gold_set:
            correct += 1
            sum_p += correct / i
    return sum_p / min(len(gold_set), k)
