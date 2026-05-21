"""Phase 1 — select the 30 worst cache entries for regeneration.

Loads `data/answer_cache.json` (1,612 entries, of which 1,607 carry the
`quality_score` field added during the 2026-05-21 overnight audit/enrichment
pass). Filters out junk-tier short stubs (`answer_length < 200` chars) so we
only spend regeneration budget on entries large enough to plausibly be a
real attempted answer that just turned out poor, then sorts ascending by
`quality_score` and writes the lowest-30 to a research file the regen pass
will read.

Output: `data/research/worst30_to_regen_2026-05-21.json`
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = ROOT / "data" / "answer_cache.json"
OUT = ROOT / "data" / "research" / "worst30_to_regen_2026-05-21.json"


def main() -> int:
    recs = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    print(f"loaded {len(recs)} cache entries from {CACHE_FILE}")

    # Keep an index so we can map back to the original cache position
    # (and for the `id_in_cache` field the regen pass logs in its jsonl).
    with_score = [
        (i, r) for i, r in enumerate(recs) if r.get("quality_score") is not None
    ]
    print(f"with quality_score: {len(with_score)}")

    # Filter to regen-worthy length. Sub-200-char entries are junk stubs
    # that should be pruned rather than regenerated (and most were caught
    # by Pass 2 / 2.5). This is the brief's explicit rule.
    regen_worthy = [(i, r) for i, r in with_score if len(r.get("answer", "")) >= 200]
    print(f"with answer_length >= 200: {len(regen_worthy)}")

    # Sort ASCENDING by quality_score, then by length ASCENDING as a tiebreak
    # (shorter low-score answers are weaker per-char).
    regen_worthy.sort(
        key=lambda t: (t[1]["quality_score"], len(t[1].get("answer", "")))
    )

    worst30 = regen_worthy[:30]
    print(
        f"selected {len(worst30)} entries (q in [{worst30[0][1]['quality_score']}, {worst30[-1][1]['quality_score']}])"
    )

    out = []
    for cache_idx, r in worst30:
        answer = r.get("answer", "") or ""
        out.append(
            {
                "id_in_cache": cache_idx,
                "question": r.get("question", ""),
                "original_answer_first_300_chars": answer[:300],
                "original_answer_length": len(answer),
                "quality_score": r.get("quality_score"),
                "cite_count": r.get("cite_count"),
                "model_estimated": r.get("model_estimated"),
                "model_confidence": r.get("model_confidence"),
                "has_arabic": r.get("has_arabic"),
                "timestamp": r.get("timestamp"),
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"worst30": out}, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"wrote {OUT}")

    # Quick stdout summary for sanity (the regen pass will operate from JSON,
    # but this gives a one-glance read of what was picked).
    # Encode questions to ASCII for cp1252 Windows consoles — punctuation like
    # non-breaking hyphens occasionally appears and crashes the default codec.
    print("\nworst-30 (q | len | cites | model | question[:80]):")
    for row in out:
        q = row["question"][:80].encode("ascii", errors="replace").decode("ascii")
        print(
            f"  {row['quality_score']:.3f} | "
            f"{row['original_answer_length']:>5} | "
            f"{(row['cite_count'] or 0):>3} | "
            f"{(row.get('model_estimated') or 'unknown'):>12} | "
            f"{q}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
