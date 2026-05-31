"""Surgical no-surface-rule fix for answer-cache entry #1514 (idx 1513).

The answer named the two forged verses with bracketed refs:
  "...two late insertions in the ninth surah (at [9:128] and [9:129]) which
   he removed as non-divine; this is documented in his Appendix 24."

The no-surface rule forbids surfacing those refs in ANY form (brackets or
prose numerals). The parenthetical is removed; the sentence keeps its meaning
("two late insertions in the ninth surah ... documented in his Appendix 24")
without naming the verses. Everything else in the entry is preserved.

Usage:
    python scripts/fix_cache_1514_surface.py [--cache PATH]
"""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CACHE = ROOT / "data" / "answer_cache.json"
IDX = 1513
EXPECTED_Q = "What does the Quran say about the the integrity of scripture?"
SURFACE = " (at [9:128] and [9:129])"
_RESIDUAL = re.compile(r"9\s*[:.]\s*12[89]")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(DEFAULT_CACHE))
    args = ap.parse_args()
    path = Path(args.cache)

    cache = json.loads(path.read_text(encoding="utf-8"))
    entry = cache[IDX]
    assert entry["question"] == EXPECTED_Q, (
        f"idx {IDX} question mismatch: {entry['question']!r}"
    )

    before = entry["answer"]
    after = before.replace(SURFACE, "")
    if after == before:
        # exact substring not found — fall back to a tolerant parenthetical strip
        after = re.sub(
            r"\s*\(at \[?9[:.]128\]?(?:\s+and\s+\[?9[:.]129\]?)?\)", "", before
        )

    if _RESIDUAL.search(after):
        raise SystemExit(f"FAILED: 9:128/9:129 still present after fix in idx {IDX}")

    entry["answer"] = after
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    print(
        f"fixed idx {IDX}: removed {len(before) - len(after)} chars; no residual refs"
    )


if __name__ == "__main__":
    main()
