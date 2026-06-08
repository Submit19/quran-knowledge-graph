"""Surgical no-surface-rule fix for the lone remaining answer-cache surface.

History: the original (2026-05-28) version hardcoded idx 1513 and stripped a
bracketed form " (at [9:128] and [9:129])". The live cache has since drifted
(a background-write-race restore plus subsequent live-server writes), so that
index and that exact string no longer match anything. As of the 2026-06-08
re-run, after re-merging the cleaned baseline (which cleared the #1591/#1596
copies), exactly ONE surface remains: the "What does verse 2:255 say?" answer,
which says:

  "...he removed two verses (9:128-129 and renumbered others) that he
   concluded were not part of the original revelation."

The no-surface rule forbids naming those verses in ANY form. We strip just the
numeral reference from the parenthetical, preserving the sentence's meaning
("he removed two verses (and renumbered others) ..."). Everything else in the
entry — and every other cache entry — is left untouched.

This version locates the violation by scanning answers (robust to index drift)
rather than trusting a hardcoded position, asserts there is exactly one, and
verifies no residual reference survives.

Usage:
    python scripts/fix_cache_1514_surface.py [--cache PATH]
"""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CACHE = ROOT / "data" / "answer_cache.json"

SURFACE_RE = re.compile(r"9\s*[:.]\s*12[89]")
# The exact parenthetical numeral run to remove, leaving the rest intact.
STRIP = "9:128-129 and renumbered others"
REPLACEMENT = "and renumbered others"
EXPECTED_Q = "What does verse 2:255 say?"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(DEFAULT_CACHE))
    args = ap.parse_args()
    path = Path(args.cache)

    cache = json.loads(path.read_text(encoding="utf-8"))

    surfacing = [
        i for i, e in enumerate(cache) if SURFACE_RE.search(e.get("answer", ""))
    ]
    if not surfacing:
        print("nothing to fix: no 9:128/9:129 surface in any cache answer")
        return
    if len(surfacing) != 1:
        raise SystemExit(
            f"expected exactly one surfacing entry, found {len(surfacing)}: {surfacing}"
        )

    idx = surfacing[0]
    entry = cache[idx]
    assert entry["question"] == EXPECTED_Q, (
        f"idx {idx} question mismatch: {entry['question']!r}"
    )

    before = entry["answer"]
    if STRIP not in before:
        raise SystemExit(
            f"expected substring {STRIP!r} not present in idx {idx}; aborting"
        )
    after = before.replace(STRIP, REPLACEMENT)

    if SURFACE_RE.search(after):
        raise SystemExit(f"FAILED: 9:128/9:129 still present after fix in idx {idx}")

    entry["answer"] = after
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    print(
        f"fixed idx {idx}: removed {len(before) - len(after)} chars; no residual refs"
    )


if __name__ == "__main__":
    main()
