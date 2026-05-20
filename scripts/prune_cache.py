"""
Pass 2 — prune obvious junk from data/answer_cache.json.

Conservative triple-AND criterion (from the overnight brief):
  quality_score < 0.15  AND  answer_length < 200  AND  cite_count == 0

Per-entry scores are sourced from the Pass-1 audit sidecar
(data/research/cache_quality_audit_2026-05-21.json). The entries are
matched back to the cache by question text (questions are unique within
the cache by construction — dedup in answer_cache.save_answer enforces
this via 0.98 cosine threshold).

Pruned entries are appended to data/research/cache_pruned_2026-05-21.jsonl
as a paper trail. The cache is rewritten via answer_cache._save_cache()
to keep its on-disk format consistent (indent=1, ensure_ascii=False).

Safety:
  - Refuses to run if Pass 1 audit sidecar is stale (mtime older than cache).
  - Stops if the prune set is >20% of the cache (the brief's hard guardrail).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import answer_cache  # noqa: E402

CACHE_FILE = ROOT / "data" / "answer_cache.json"
AUDIT_FILE = ROOT / "data" / "research" / "cache_quality_audit_2026-05-21.json"
TRAIL_FILE = ROOT / "data" / "research" / "cache_pruned_2026-05-21.jsonl"


def main() -> int:
    if not AUDIT_FILE.exists():
        print(
            "Pass 1 sidecar missing — run scripts/audit_cache_quality.py first.",
            file=sys.stderr,
        )
        return 2
    if AUDIT_FILE.stat().st_mtime < CACHE_FILE.stat().st_mtime:
        print(
            "Audit sidecar is older than the cache — re-run audit first to "
            "ensure scores reflect current entries.",
            file=sys.stderr,
        )
        return 2

    cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_FILE.read_text(encoding="utf-8"))["scored"]

    # Index audit by question text (canonical key). One audit row per entry.
    score_by_q: dict[str, dict] = {a["question"]: a for a in audit}

    to_prune_questions: set[str] = set()
    for s in audit:
        if s["quality_score"] < 0.15 and s["answer_len"] < 200 and s["cite_count"] == 0:
            to_prune_questions.add(s["question"])

    before = len(cache)
    print(f"Cache before: {before}")
    print(f"Audit-flagged for prune: {len(to_prune_questions)}")

    if before and len(to_prune_questions) / before > 0.20:
        print(
            f"!!! STOP: prune set ({len(to_prune_questions)}) exceeds 20% of cache "
            f"({before}). Threshold likely wrong — manual review required.",
            file=sys.stderr,
        )
        return 3

    pruned_records = []
    kept = []
    for rec in cache:
        if rec.get("question") in to_prune_questions:
            audit_row = score_by_q.get(rec["question"], {})
            pruned_records.append(
                {
                    "question": rec.get("question", ""),
                    "answer_preview": (rec.get("answer", "") or "")[:300],
                    "answer_len": audit_row.get("answer_len"),
                    "cite_count": audit_row.get("cite_count"),
                    "quality_score": audit_row.get("quality_score"),
                    "timestamp": rec.get("timestamp"),
                }
            )
        else:
            kept.append(rec)

    if not pruned_records:
        print("No entries matched the prune criteria. Nothing to do.")
        return 0

    TRAIL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with TRAIL_FILE.open("w", encoding="utf-8") as f:
        for p in pruned_records:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    answer_cache._save_cache(kept)

    after = len(kept)
    print(f"Cache after:  {after}  (-{before - after})")
    print(f"Paper trail:  {TRAIL_FILE.relative_to(ROOT)}")
    print()
    print("Pruned entries:")
    for p in pruned_records[:10]:
        print(
            f"  - q={p['question'][:80]!r}  len={p['answer_len']}  "
            f"cites={p['cite_count']}  score={p['quality_score']}"
        )
    if len(pruned_records) > 10:
        print(f"  ... +{len(pruned_records) - 10} more in the paper trail")

    return 0


if __name__ == "__main__":
    sys.exit(main())
