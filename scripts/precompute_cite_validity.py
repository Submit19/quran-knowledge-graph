"""
Pass 3 — precompute `cite_validity` per cache entry.

After Pass 2 stripped every invalid `[surah:verse]` token, this pass
re-extracts the remaining citations and writes
    cite_validity = unique_valid / unique_total
per entry. With Pass 2 having run, every entry should land at 1.0
(no invalid cites left). The field exists so the runtime reranker
can filter or downweight low-validity entries without re-running a
Neo4j check at query time.

Entries with zero citations get cite_validity = 1.0 — an answer
without any citations has no invalid cites either; nothing to
penalize.

Verification step: count entries where cite_validity < 1.0 and
report (should be zero). If non-zero, Pass 2 missed something.

NO Anthropic API calls. Read-only Neo4j.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import answer_cache  # noqa: E402

CITE_RX = re.compile(r"\[(\d{1,3}):(\d{1,3})\]")


def extract_cites(text: str) -> set[tuple[int, int]]:
    return {(int(s), int(v)) for s, v in CITE_RX.findall(text or "")}


def fetch_valid_set(cites: set[tuple[int, int]]) -> set[tuple[int, int]]:
    load_dotenv(ROOT / ".env")
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    pw = os.getenv("NEO4J_PASSWORD")
    db = os.getenv("NEO4J_DATABASE", "quran")
    if not (uri and user and pw):
        print("Missing Neo4j env vars", file=sys.stderr)
        sys.exit(2)
    valid: set[tuple[int, int]] = set()
    driver = GraphDatabase.driver(uri, auth=(user, pw))
    try:
        with driver.session(database=db) as s:
            rows = s.run(
                """
                UNWIND $cites AS pair
                WITH pair[0] AS surah, pair[1] AS verse
                MATCH (v:Verse {surah: surah, verseNum: verse})
                RETURN surah, verse
                """,
                cites=[list(c) for c in cites],
            ).data()
    finally:
        driver.close()
    for row in rows:
        valid.add((row["surah"], row["verse"]))
    return valid


def main() -> int:
    answer_cache._reset_memory_cache_for_tests()
    entries = answer_cache._load_cache()
    print(f"Loaded {len(entries)} cache entries")

    all_cites: set[tuple[int, int]] = set()
    for e in entries:
        all_cites |= extract_cites(e.get("answer", "") or "")
    print(f"Unique cited verseIds across cache: {len(all_cites)}")

    valid = fetch_valid_set(all_cites)
    invalid_unique = all_cites - valid
    print(f"Valid:   {len(valid)}")
    print(f"Invalid: {len(invalid_unique)} (should be 0 after Pass 2)")

    counts = {"1.0": 0, "lt_1": 0, "no_cites": 0}
    bad_entries: list[tuple[int, str, float, int, int]] = []

    for i, e in enumerate(entries):
        cites = extract_cites(e.get("answer", "") or "")
        if not cites:
            validity = 1.0
            counts["no_cites"] += 1
        else:
            n_valid = sum(1 for c in cites if c in valid)
            validity = n_valid / len(cites)
            if validity < 1.0:
                counts["lt_1"] += 1
                bad_entries.append(
                    (i, e.get("question", "")[:120], validity, n_valid, len(cites))
                )
            else:
                counts["1.0"] += 1
        e["cite_validity"] = round(validity, 4)

    print("\nDistribution:")
    print(f"  cite_validity == 1.0:         {counts['1.0']}")
    print(f"  cite_validity <  1.0:         {counts['lt_1']}")
    print(f"  no citations (assigned 1.0):  {counts['no_cites']}")

    if bad_entries:
        print("\nEntries with cite_validity < 1.0 (Pass 2 missed these):")
        for idx, q, val, nv, nt in bad_entries[:20]:
            print(f"  [#{idx}] validity={val:.3f}  ({nv}/{nt})  Q={q!r}")

    pct_perfect = (
        100 * (counts["1.0"] + counts["no_cites"]) / len(entries) if entries else 0.0
    )
    print(f"\n100% perfect-validity entries: {pct_perfect:.2f}%")

    print("\nSaving cache via answer_cache._save_cache …")
    answer_cache._save_cache(entries)
    print("Saved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
