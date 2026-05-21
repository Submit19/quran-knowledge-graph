"""Append a regen record to baseline_worst30_regen_2026-05-21.jsonl.

Reads a single-record JSON from stdin (or --file) and appends as a JSONL
line to the output file. Used by the Phase-2 regen workflow: each answer
is composed by the advisor session, written to a temp JSON, then this
script appends it durably so progress survives crashes between commits.

Usage:
  python scripts/_regen_append.py --file /tmp/record.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "eval" / "v2" / "baseline_worst30_regen_2026-05-21.jsonl"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    args = ap.parse_args()

    rec = json.loads(Path(args.file).read_text(encoding="utf-8"))
    # quick sanity — every regen record must carry these fields
    required = {
        "id",
        "bucket",
        "question",
        "answer",
        "citations",
        "model",
        "method",
        "answered_at",
        "original_quality_score",
    }
    missing = required - set(rec.keys())
    if missing:
        print(f"ERROR: record missing fields: {missing}", file=sys.stderr)
        return 2

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(
        f"appended id={rec['id']} (answer {len(rec['answer'])} chars, "
        f"{len(rec['citations'])} cites) -> {OUT.name}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
