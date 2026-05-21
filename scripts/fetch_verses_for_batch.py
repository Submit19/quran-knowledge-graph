"""Fetch verses for a batch of question IDs (Phase 3 helper).

Usage:
    python scripts/fetch_verses_for_batch.py 1 25       # ids 1..25
    python scripts/fetch_verses_for_batch.py 1 25 +     # also pull root mentions + neighbors

Reads data/eval/v2/expansion_questions_2026-05-21.json,
selects expansion-NNN by ID range, collects target_verses,
adds context-bearing neighbors (next 2 verses + previous 1), and
queries Neo4j once for {verseId: {text, arabicPlain}} plus a
target_themes-derived MENTIONS lookup. Writes a single
data/eval/v2/_batch_NNN_MMM.json file the answer-composition step
can read.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
REPO_ROOT = Path(__file__).resolve().parent.parent
QFILE = REPO_ROOT / "data" / "eval" / "v2" / "expansion_questions_2026-05-21.json"


def expand_neighbors(vids: list[str]) -> list[str]:
    """For each verseId N:M, add N:M-1, N:M+1, N:M+2 if positive."""
    out = set(vids)
    for v in vids:
        try:
            s, n = v.split(":")
            n = int(n)
            for d in (-1, 1, 2):
                if n + d > 0:
                    out.add(f"{s}:{n + d}")
        except Exception:
            continue
    return sorted(out, key=lambda x: (int(x.split(":")[0]), int(x.split(":")[1])))


def fetch_verses(driver, db, vids: list[str]) -> dict:
    if not vids:
        return {}
    with driver.session(database=db) as s:
        rows = s.run(
            """
            UNWIND $ids AS vid
            MATCH (v:Verse {verseId: vid})
            RETURN v.verseId AS id, v.text AS t, v.arabicPlain AS ar, v.surahName AS sn
            """,
            ids=vids,
        ).values()
    return {
        r[0]: {"text": r[1] or "", "arabic": r[2] or "", "surahName": r[3] or ""}
        for r in rows
    }


def search_themes(driver, db, themes: list[str], limit_per_theme: int = 8) -> dict:
    """For each theme, find verses whose text contains the theme keyword."""
    out: dict[str, list[dict]] = {}
    for theme in themes:
        if not theme or len(theme) < 3:
            continue
        with driver.session(database=db) as s:
            rows = s.run(
                """
                MATCH (v:Verse)
                WHERE toLower(v.text) CONTAINS $needle
                RETURN v.verseId AS id, v.text AS t
                LIMIT $lim
                """,
                needle=theme.lower(),
                lim=limit_per_theme,
            ).values()
        out[theme] = [{"verseId": r[0], "text": r[1]} for r in rows]
    return out


def find_root(driver, db, root: str) -> dict | None:
    """If theme looks like a 3-letter Arabic root (with or without hyphens),
    look it up and return basic info + top 6 mention verses."""
    if not root:
        return None
    bare = root.replace("-", "").replace(" ", "")
    if not (2 <= len(bare) <= 6) or not any(ord(c) > 127 for c in bare):
        return None
    with driver.session(database=db) as s:
        rows = s.run(
            """
            MATCH (r:ArabicRoot {root: $r})
            OPTIONAL MATCH (r)<-[m:MENTIONS_ROOT]-(v:Verse)
            WITH r, v
            ORDER BY v.verseId
            WITH r, collect(v.verseId)[..8] AS sample_verses
            RETURN r.root AS root, r.rootBW AS bw, r.gloss AS gloss, r.verseCount AS verseCount, sample_verses
            """,
            r=bare,
        ).single()
    if not rows:
        return None
    return {
        "root": rows[0],
        "rootBW": rows[1],
        "gloss": rows[2] or "",
        "verseCount": rows[3] or 0,
        "sample_verses": rows[4] or [],
    }


def main():
    start = int(sys.argv[1])
    end = int(sys.argv[2])
    expand = "+" in sys.argv

    data = json.load(QFILE.open(encoding="utf-8"))
    questions = data["primary"]
    selected = [q for q in questions if start <= int(q["id"].split("-")[1]) <= end]
    print(f"selected {len(selected)} questions in range {start}-{end}")

    target_vids = set()
    target_themes: set[str] = set()
    for q in selected:
        for v in q.get("target_verses") or []:
            target_vids.add(v)
        for t in q.get("target_themes") or []:
            target_themes.add(t)

    expanded_vids = (
        expand_neighbors(list(target_vids)) if expand else sorted(target_vids)
    )

    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")),
    )
    db = os.getenv("NEO4J_DATABASE", "quran")
    try:
        verses = fetch_verses(driver, db, expanded_vids)
        theme_verses = search_themes(driver, db, sorted(target_themes), 6)
        roots = {}
        for t in target_themes:
            r = find_root(driver, db, t)
            if r:
                roots[t] = r
    finally:
        driver.close()

    out = {
        "questions": selected,
        "verses": verses,
        "theme_verses": theme_verses,
        "roots": roots,
    }
    out_path = REPO_ROOT / "data" / "eval" / "v2" / f"_batch_{start:03d}_{end:03d}.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"wrote {out_path}  ({len(verses)} verses, {len(theme_verses)} themes, {len(roots)} roots)"
    )


if __name__ == "__main__":
    main()
