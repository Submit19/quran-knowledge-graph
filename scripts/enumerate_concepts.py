"""Enumerate graph concepts + score against existing cache for coverage gaps.

Phase 1 of cache-content-expansion 2026-05-21:
- Pulls Sura, ArabicRoot, Concept, SemanticDomain inventories from Neo4j.
- Reads data/answer_cache.json once, builds a coverage index keyed by:
  * surah number   (regex [N:M] over answer text)
  * prophet name   (substring match over answer text)
  * root form      (substring match, hyphenated like "ج-ن-ن")
  * concept text   (substring match against canonical Keyword.text)
- Emits data/research/concept_inventory_2026-05-21.{json,md}.
"""

import json
import os
import re
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE = REPO_ROOT / "data" / "answer_cache.json"
OUT_JSON = REPO_ROOT / "data" / "research" / "concept_inventory_2026-05-21.json"
OUT_MD = REPO_ROOT / "data" / "research" / "concept_inventory_2026-05-21.md"

VERSE_RE = re.compile(r"\[(\d{1,3}):(\d{1,3})\]")

PROPHETS = [
    ("Adam", ["adam"]),
    ("Idris", ["idris", "enoch"]),
    ("Nuh", ["noah", "nuh"]),
    ("Hud", ["hud"]),
    ("Salih", ["salih", "saleh"]),
    ("Ibrahim", ["abraham", "ibrahim"]),
    ("Lut", ["lot", "lut"]),
    ("Ismail", ["ismail", "ishmael"]),
    ("Ishaq", ["ishaq", "isaac"]),
    ("Yaqub", ["ya'qub", "yaqub", "ya`qub", "jacob", "israel"]),
    ("Yusuf", ["yusuf", "joseph"]),
    (
        "Shuaib",
        [
            "shu`aib",
            "shuaib",
            "shu'aib",
            "shu‘aib",
            "shu’aib",
            "shu`ayb",
            "shoaib",
            "jethro",
        ],
    ),
    ("Ayyub", ["ayyub", "job"]),
    ("Dhulkifl", ["dhul-kifl", "dhul kifl", "dhulkifl", "ezekiel"]),
    ("Musa", ["musa", "moses"]),
    ("Harun", ["harun", "aaron"]),
    ("Dawud", ["dawud", "david"]),
    ("Sulaiman", ["sulaiman", "solomon"]),
    ("Ilyas", ["ilyas", "ilyasin", "elijah", "elias"]),
    ("Alyasa", ["al-yasa", "al-yasa`", "alyasa", "elisha"]),
    ("Yunus", ["yunus", "jonah", "dhun-nun"]),
    ("Zakariya", ["zakariya", "zechariah", "zakariyya"]),
    ("Yahya", ["yahya", "john the baptist"]),
    ("Isa", ["jesus", "isa", "messiah", "christ"]),
    ("Muhammad", ["muhammad", "mohammed", "the prophet"]),
]


def load_cache_index() -> dict:
    """Read cache once; build surah/prophet/root/keyword coverage tallies."""
    data = json.load(CACHE.open(encoding="utf-8"))
    surah_hits = Counter()
    prophet_hits = Counter()
    answers = []
    for rec in data:
        ans = rec.get("answer", "") or ""
        ans_low = ans.lower()
        answers.append(ans_low)
        for m in VERSE_RE.finditer(ans):
            surah_hits[int(m.group(1))] += 1
        for canonical, aliases in PROPHETS:
            if any(a in ans_low for a in aliases):
                prophet_hits[canonical] += 1
    return {
        "total_entries": len(data),
        "surah_hits": dict(surah_hits),
        "prophet_hits": dict(prophet_hits),
        "answers_lower": answers,
    }


def fetch_surahs(driver, db):
    with driver.session(database=db) as s:
        rows = s.run(
            """
            MATCH (su:Sura)
            OPTIONAL MATCH (su)-[:CONTAINS]->(v:Verse)
            WITH su, collect(v.surahName)[0] AS sname, count(v) AS vc
            RETURN su.number AS num, sname AS name,
                   su.revelation_location AS rev_loc,
                   su.revelation_order AS rev_order,
                   su.mysterious_letters AS ml,
                   vc
            ORDER BY su.number
            """
        ).values()
    return [
        {
            "number": r[0],
            "name": r[1],
            "rev_loc": r[2],
            "rev_order": r[3],
            "mysterious_letters": r[4],
            "verses_count": r[5],
        }
        for r in rows
    ]


def fetch_top_roots(driver, db, limit=200):
    with driver.session(database=db) as s:
        rows = s.run(
            """
            MATCH (r:ArabicRoot)
            RETURN r.root AS root, r.rootBW AS bw, r.gloss AS gloss, r.verseCount AS mentions
            ORDER BY r.verseCount DESC
            LIMIT $lim
            """,
            lim=limit,
        ).values()
    return [
        {"root": r[0], "bw": r[1], "gloss": r[2] or "", "mentions": r[3] or 0}
        for r in rows
    ]


def fetch_concepts(driver, db, limit=400):
    with driver.session(database=db) as s:
        rows = s.run(
            """
            MATCH (c:Concept)
            RETURN c.name AS canonical, c.n_verses AS verse_count, c.n_keywords AS kw_count
            ORDER BY c.n_verses DESC
            LIMIT $lim
            """,
            lim=limit,
        ).values()
    return [{"canonical": r[0], "verse_count": r[1], "kw_count": r[2]} for r in rows]


def fetch_semantic_domains(driver, db):
    with driver.session(database=db) as s:
        rows = s.run(
            """
            MATCH (d:SemanticDomain)
            OPTIONAL MATCH (d)<-[:IN_DOMAIN]-(k)
            WITH d, count(k) AS member_count
            RETURN d.nameEn AS name, d.description AS desc, member_count
            ORDER BY member_count DESC
            """
        ).values()
    return [{"name": r[0], "description": r[1], "member_count": r[2]} for r in rows]


def fetch_prophet_anchors(driver, db):
    """For each prophet, get verses whose text mentions them most distinctively."""
    anchors = {}
    for canonical, aliases in PROPHETS:
        with driver.session(database=db) as s:
            primary = aliases[0]
            rows = s.run(
                """
                MATCH (v:Verse)
                WHERE toLower(v.text) CONTAINS $name
                RETURN v.verseId AS vid
                LIMIT 25
                """,
                name=primary.lower(),
            ).values()
        anchors[canonical] = [r[0] for r in rows]
    return anchors


def fetch_iconic_verses(driver, db, limit=80):
    """Verses with highest RELATED_TO degree as a proxy for thematic centrality."""
    with driver.session(database=db) as s:
        rows = s.run(
            """
            MATCH (v:Verse)-[r:RELATED_TO]-()
            WITH v, count(r) AS deg
            RETURN v.verseId AS vid, v.text AS text, deg
            ORDER BY deg DESC
            LIMIT $lim
            """,
            lim=limit,
        ).values()
    return [{"verseId": r[0], "text": r[1][:160], "degree": r[2]} for r in rows]


def score_concept_coverage(canonical: str, answers_lower: list[str]) -> int:
    needle = canonical.lower()
    return sum(1 for a in answers_lower if needle in a)


def score_root_coverage(root: str, answers_lower: list[str]) -> int:
    """Match either bare form (جنن) or hyphenated form (ج-ن-ن)."""
    if not root or len(root) < 2:
        return 0
    hyphenated = "-".join(list(root))
    return sum(1 for a in answers_lower if root in a or hyphenated in a)


def main():
    print("loading cache index...")
    cache_idx = load_cache_index()
    print(f"  cache entries: {cache_idx['total_entries']}")

    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")),
    )
    db = os.getenv("NEO4J_DATABASE", "quran")

    try:
        print("fetching surahs...")
        surahs = fetch_surahs(driver, db)
        print(f"  {len(surahs)} surahs")
        print("fetching top-200 roots...")
        roots = fetch_top_roots(driver, db, 200)
        print(f"  {len(roots)} roots")
        print("fetching top concepts...")
        concepts = fetch_concepts(driver, db, 400)
        print(f"  {len(concepts)} concepts")
        print("fetching semantic domains...")
        domains = fetch_semantic_domains(driver, db)
        print(f"  {len(domains)} domains")
        print("fetching prophet anchors...")
        prophet_anchors = fetch_prophet_anchors(driver, db)
        print(f"  {len(prophet_anchors)} prophets with anchors")
        print("fetching iconic verses...")
        iconic = fetch_iconic_verses(driver, db, 80)
        print(f"  {len(iconic)} iconic verses")
    finally:
        driver.close()

    answers_lower = cache_idx["answers_lower"]

    # Coverage scoring
    for s in surahs:
        s["cache_hits"] = cache_idx["surah_hits"].get(s["number"], 0)
    for r in roots:
        r["cache_hits"] = score_root_coverage(r["root"], answers_lower)
    concepts = [c for c in concepts if c.get("canonical")]
    for c in concepts:
        c["cache_hits"] = score_concept_coverage(c["canonical"], answers_lower)
    for d in domains:
        d["cache_hits"] = (
            score_concept_coverage(d["name"], answers_lower) if d.get("name") else 0
        )
    prophets_info = []
    for canonical, aliases in PROPHETS:
        prophets_info.append(
            {
                "canonical": canonical,
                "aliases": aliases,
                "cache_hits": cache_idx["prophet_hits"].get(canonical, 0),
                "anchor_verses": prophet_anchors.get(canonical, [])[:8],
            }
        )

    # Gap-severity sort: lowest cache_hits = highest priority
    surahs_sorted = sorted(surahs, key=lambda x: x["cache_hits"])
    roots_sorted = sorted(roots, key=lambda x: x["cache_hits"])
    concepts_sorted = sorted(concepts, key=lambda x: x["cache_hits"])
    prophets_sorted = sorted(prophets_info, key=lambda x: x["cache_hits"])

    inventory = {
        "generated_at": "2026-05-21",
        "cache_total_entries": cache_idx["total_entries"],
        "surahs": surahs,
        "surahs_by_gap": surahs_sorted[:30],
        "roots_top200": roots,
        "roots_by_gap": roots_sorted[:50],
        "concepts": concepts,
        "concepts_by_gap": concepts_sorted[:80],
        "semantic_domains": domains,
        "prophets": prophets_info,
        "prophets_by_gap": prophets_sorted,
        "iconic_verses": iconic,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"wrote {OUT_JSON}")

    # MD report
    md = []
    md.append("# Concept Inventory & Coverage Gap Report — 2026-05-21\n")
    md.append(
        f"Source: Neo4j `quran` db + `data/answer_cache.json` ({cache_idx['total_entries']} entries).\n"
    )

    md.append("## Surah coverage — thinnest 30 (by cache verse-citations)\n")
    md.append("| # | Surah | Verses | Loc | Hits |")
    md.append("|---:|---|---:|---|---:|")
    for s in surahs_sorted[:30]:
        md.append(
            f"| {s['number']} | {s.get('name', '')} | {s.get('verses_count', 0)} | {s.get('rev_loc', '?')} | {s['cache_hits']} |"
        )

    md.append("\n## Top-200 Arabic roots — thinnest 50 (by cache substring match)\n")
    md.append("| Root | Gloss | Mentions | Hits |")
    md.append("|---|---|---:|---:|")
    for r in roots_sorted[:50]:
        md.append(
            f"| {r['root']} | {r.get('gloss', '') or ''} | {r['mentions']} | {r['cache_hits']} |"
        )

    md.append("\n## Top concepts — thinnest 80 (canonical Concept names)\n")
    md.append("| Canonical | Verse count | Hits |")
    md.append("|---|---:|---:|")
    for c in concepts_sorted[:80]:
        md.append(f"| {c['canonical']} | {c['verse_count']} | {c['cache_hits']} |")

    md.append("\n## Prophets — by cache-mention gap\n")
    md.append("| Prophet | Aliases | Hits | Anchors |")
    md.append("|---|---|---:|---|")
    for p in prophets_sorted:
        md.append(
            f"| {p['canonical']} | {', '.join(p['aliases'][:3])} | {p['cache_hits']} | {', '.join(p['anchor_verses'][:5])} |"
        )

    md.append("\n## Semantic domains\n")
    md.append("| Domain | Members | Hits |")
    md.append("|---|---:|---:|")
    for d in domains:
        md.append(f"| {d['name']} | {d['member_count']} | {d['cache_hits']} |")

    md.append("\n## Iconic verses (top RELATED_TO degree)\n")
    for v in iconic[:30]:
        md.append(f"- {v['verseId']} (deg {v['degree']}): {v['text']}")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
