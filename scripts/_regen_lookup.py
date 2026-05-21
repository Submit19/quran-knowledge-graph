"""Helper for Phase-2 regen: batch-fetch verse text/Arabic and roots.

Used interactively from the advisor session: pass space-separated verseIds
as `--verses`, or a root in --root, and it dumps a compact human-readable
snapshot we can compose from. NOT a production script — sits in scripts/
so it can use the project's env loading and import path consistently.

Usage:
  python scripts/_regen_lookup.py --verses 2:255 12:87 39:53
  python scripts/_regen_lookup.py --root "ا-ي-ة"     # by Arabic chars
  python scripts/_regen_lookup.py --keyword sura     # text-contains scan
  python scripts/_regen_lookup.py --root-gloss "verse,sign"  # gloss filter
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def driver():
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")),
    )


def lookup_verses(verse_ids: list[str]) -> list[dict]:
    d = driver()
    db = os.getenv("NEO4J_DATABASE", "quran")
    with d.session(database=db) as s:
        rows = s.run(
            """
            UNWIND $ids AS vid
            MATCH (v:Verse {verseId: vid})
            RETURN v.verseId AS id,
                   v.surahName AS surahName,
                   v.text AS text,
                   v.arabicPlain AS arabic
            """,
            ids=verse_ids,
        ).data()
    d.close()
    by_id = {r["id"]: r for r in rows}
    return [by_id.get(vid, {"id": vid, "MISSING": True}) for vid in verse_ids]


def lookup_root(root_chars: str, limit: int = 20) -> list[dict]:
    d = driver()
    db = os.getenv("NEO4J_DATABASE", "quran")
    with d.session(database=db) as s:
        rows = s.run(
            """
            MATCH (r:ArabicRoot {root: $root})
            OPTIONAL MATCH (r)<-[m:MENTIONS_ROOT]-(v:Verse)
            WITH r, count(DISTINCT v) AS verse_count
            RETURN r.root AS root, r.gloss AS gloss, verse_count
            """,
            root=root_chars,
        ).data()
        verses = s.run(
            """
            MATCH (r:ArabicRoot {root: $root})<-[:MENTIONS_ROOT]-(v:Verse)
            RETURN v.verseId AS id, v.surahName AS surahName,
                   v.text AS text, v.arabicPlain AS arabic
            LIMIT $limit
            """,
            root=root_chars,
            limit=limit,
        ).data()
    d.close()
    return [{"root_info": rows, "sample_verses": verses}]


def lookup_root_by_gloss(needle: str, limit: int = 10) -> list[dict]:
    d = driver()
    db = os.getenv("NEO4J_DATABASE", "quran")
    with d.session(database=db) as s:
        rows = s.run(
            """
            MATCH (r:ArabicRoot)
            WHERE toLower(r.gloss) CONTAINS toLower($needle)
            OPTIONAL MATCH (r)<-[:MENTIONS_ROOT]-(v:Verse)
            WITH r, count(DISTINCT v) AS verse_count
            RETURN r.root AS root, r.gloss AS gloss, verse_count
            ORDER BY verse_count DESC
            LIMIT $limit
            """,
            needle=needle,
            limit=limit,
        ).data()
    d.close()
    return rows


def text_search(needle: str, limit: int = 20) -> list[dict]:
    d = driver()
    db = os.getenv("NEO4J_DATABASE", "quran")
    with d.session(database=db) as s:
        rows = s.run(
            """
            MATCH (v:Verse)
            WHERE toLower(v.text) CONTAINS toLower($needle)
            RETURN v.verseId AS id, v.surahName AS surahName,
                   v.text AS text
            LIMIT $limit
            """,
            needle=needle,
            limit=limit,
        ).data()
    d.close()
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verses", nargs="+")
    ap.add_argument("--root")
    ap.add_argument("--root-gloss")
    ap.add_argument("--keyword")
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()

    out = {}
    if args.verses:
        out["verses"] = lookup_verses(args.verses)
    if args.root:
        out["root"] = lookup_root(args.root, args.limit)
    if args.root_gloss:
        out["root_gloss"] = lookup_root_by_gloss(args.root_gloss, args.limit)
    if args.keyword:
        out["keyword"] = text_search(args.keyword, args.limit)

    sys.stdout.write(json.dumps(out, indent=2, ensure_ascii=False))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
