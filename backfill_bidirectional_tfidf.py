"""
backfill_bidirectional_tfidf.py — Sefaria-inspired RefTopicLink pattern
applied to Verse-Keyword (`MENTIONS`) edges.

Enriches existing :MENTIONS edges with:
  - from_tfidf : original `score` field (salience of keyword in verse vocab)
  - to_tfidf   : score / sum_of_scores_across_keyword (verse's share of
                 the keyword's total weight)
  - data_source: "build_graph.py-tfidf"
  - generated_by: "tfidf-keywords"

Why this matters (Sefaria pattern):
  - "Verses about keyword X" should ORDER BY to_tfidf DESC
    (verses where X is most strongly anchored)
  - "Keywords describing verse Y" should ORDER BY from_tfidf DESC
    (the verse's own salience profile)

Run:  python backfill_bidirectional_tfidf.py
"""

import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
URI = os.getenv("NEO4J_URI"); USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD"); DB = os.getenv("NEO4J_DATABASE", "quran")


def main():
    print(f"Connecting to Neo4j ({URI}, db={DB})...")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    driver.verify_connectivity()
    print("  OK")

    # 1. Compute per-keyword sum_of_scores
    print("\nComputing per-keyword score sums...")
    with driver.session(database=DB) as s:
        rows = s.run("""
            MATCH (v:Verse)-[m:MENTIONS]->(k:Keyword)
            WHERE m.score IS NOT NULL
            RETURN k.keyword AS keyword, sum(m.score) AS total, count(*) AS n_verses
        """).data()
    keyword_totals = {r["keyword"]: r["total"] for r in rows}
    print(f"  {len(keyword_totals):,} keywords with scored mentions")
    print(f"  total mentions: {sum(r['n_verses'] for r in rows):,}")

    # 2. Update each MENTIONS edge with from_tfidf, to_tfidf, provenance
    #    from_tfidf = m.score (verse's salience toward this keyword)
    #    to_tfidf   = m.score / sum(scores for this keyword)
    #
    # Done in one Cypher pass per keyword for efficiency.
    print("\nWriting bidirectional TF-IDF + provenance...")
    BATCH = 100
    updated = 0
    with driver.session(database=DB) as s:
        # Build keyword -> total map for parameter passing
        kw_items = list(keyword_totals.items())
        for i in range(0, len(kw_items), BATCH):
            chunk = kw_items[i:i + BATCH]
            params = [{"kw": k, "total": float(t)} for k, t in chunk]
            r = s.run("""
                UNWIND $rows AS row
                MATCH (v:Verse)-[m:MENTIONS]->(k:Keyword {keyword: row.kw})
                WHERE m.score IS NOT NULL
                SET m.from_tfidf = m.score,
                    m.to_tfidf   = CASE WHEN row.total > 0
                                         THEN m.score / row.total
                                         ELSE 0.0 END,
                    m.data_source = 'build_graph.py-tfidf',
                    m.generated_by = 'tfidf-keywords'
                RETURN count(m) AS n
            """, rows=params).single()
            updated += r["n"] or 0
            done = min(i + BATCH, len(kw_items))
            print(f"  {done}/{len(kw_items)} keywords processed, {updated} edges updated", end="\r")
    print(f"\n  total edges updated: {updated:,}")

    # 3. Verify
    print("\nVerifying with sample queries...")
    with driver.session(database=DB) as s:
        sample = s.run("""
            MATCH (v:Verse)-[m:MENTIONS]->(k:Keyword {text: 'patience'})
            RETURN v.verseId AS v, m.score AS score,
                   m.from_tfidf AS ft, m.to_tfidf AS tt,
                   m.data_source AS ds
            ORDER BY m.to_tfidf DESC LIMIT 5
        """).data()
    print("\n  Top 5 verses for 'patience' (by to_tfidf — verses most anchoring this keyword):")
    for r in sample:
        score = r['score'] or 0
        ft = r['ft'] or 0
        tt = r['tt'] or 0
        print(f"    [{r['v']}]  score={score:.3f}  from_tfidf={ft:.3f}  to_tfidf={tt:.4f}  ds={r['ds']}")

    with driver.session(database=DB) as s:
        sample2 = s.run("""
            MATCH (v:Verse {verseId: '2:255'})-[m:MENTIONS]->(k:Keyword)
            WHERE m.from_tfidf IS NOT NULL
            RETURN k.keyword AS keyword, m.from_tfidf AS ft, m.to_tfidf AS tt
            ORDER BY m.from_tfidf DESC LIMIT 5
        """).data()
    print("\n  Top 5 keywords for 2:255 (by from_tfidf — keywords most central to this verse):")
    for r in sample2:
        ft = r['ft'] or 0
        tt = r['tt'] or 0
        print(f"    {r['keyword']}  from_tfidf={ft:.3f}  to_tfidf={tt:.4f}")

    driver.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
