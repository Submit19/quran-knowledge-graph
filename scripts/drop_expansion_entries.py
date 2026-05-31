"""Drop no-surface-rule-violating entries from the cache-expansion JSONL.

Five entries generated during the cache-content-expansion run (before the
no-surface rule was formalized) are essays built around the forged verses
9:128 / 9:129 — they are not editable, the forged verses ARE the subject
matter, so they are dropped wholesale. See
data/research/no_surface_rule_violations_2026-05-27.md.

The cleaned JSONL is the intended new content of the
cache-content-expansion-2026-05-21 branch (operator cherry-picks / rebases).

Usage:
    python scripts/drop_expansion_entries.py            # rewrite in place
    python scripts/drop_expansion_entries.py --check    # report only, no write
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JSONL = ROOT / "data" / "cache_expansion_2026-05-21.jsonl"

# id -> rationale (from the violations report)
DROP = {
    "expansion-307": "essay structured around quoting 9:128/9:129 as 'removed verses'",
    "expansion-308": "answer quotes both 9:128 and 9:129 in full",
    "expansion-311": "essay quoting 9:128/9:129 as the example of 'different verses'",
    "expansion-312": "answer entirely about the two removed verses, quoted",
    "expansion-313": "question itself surfaces the refs; answer quotes them",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only, do not write")
    args = ap.parse_args()

    kept, dropped = [], []
    for line in JSONL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        entry = json.loads(line)
        if entry.get("id") in DROP:
            dropped.append(entry["id"])
        else:
            kept.append(entry)

    print(
        f"total in: {len(kept) + len(dropped)} | keeping: {len(kept)} | dropping: {len(dropped)}"
    )
    for eid in DROP:
        status = "DROPPED" if eid in dropped else "NOT FOUND (already absent?)"
        print(f"  {eid}: {status} — {DROP[eid]}")

    missing = [e for e in DROP if e not in dropped]
    if missing:
        print(f"WARNING: expected-to-drop ids not present: {missing}")

    if args.check:
        print("--check: no write")
        return

    with JSONL.open("w", encoding="utf-8", newline="\n") as f:
        for entry in kept:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"wrote {JSONL} ({len(kept)} entries)")


if __name__ == "__main__":
    main()
