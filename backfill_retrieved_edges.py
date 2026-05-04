"""
backfill_retrieved_edges.py — backfill (:ReasoningTrace)-[:RETRIEVED]->(:Verse)
edges from the 1,500-entry answer cache.

We don't have the full tool-call payload history (those traces only exist
for queries that ran via the live agent loop — newer than the cache). What
we DO have is, per cached answer:
  - the question text -> we can synthesize a Query node + ReasoningTrace
  - cited_verses -> we treat each as RETRIEVED (proxy: a verse the system
                    found relevant enough to cite)
  - tool sequence is unknown, so we use tool="cache_seed" as the source

This is a proxy: it conflates "retrieved" with "cited", which is good
enough to bootstrap the data layer. Future live queries will produce
proper per-tool RETRIEVED edges via reasoning_memory.

Run:  python backfill_retrieved_edges.py [--dry-run]
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
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

CACHE_PATH = Path("data/answer_cache.json")
TOOL_TAG = "cache_seed"   # provenance for the synthetic edges


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Compute counts, don't write anything")
    args = ap.parse_args()

    print(f"Connecting to Neo4j ({URI}, db={DB})...")
    d = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    d.verify_connectivity()
    print("  OK")

    print("\nLoading answer cache...")
    cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    print(f"  {len(cache):,} cached entries")

    # We need to import re for verse extraction
    import re

    # Each cache entry has {question, answer, verses, embedding, timestamp}
    # `verses` is a dict {verseId: {text, arabic}} — those are what we
    # treat as "retrieved".
    rows = []
    for e in cache:
        q = (e.get("question") or "").strip()
        if not q:
            continue
        # Verses come as keys of `verses` dict; fall back to regex over answer
        verse_ids = []
        if isinstance(e.get("verses"), dict):
            verse_ids = sorted(e["verses"].keys())
        if not verse_ids:
            verse_ids = sorted({m.group(1) for m in
                                re.finditer(r"\[(\d+:\d+)\]", e.get("answer", ""))})
        if not verse_ids:
            continue
        rows.append({"question": q[:1000],
                     "verse_ids": verse_ids[:100],
                     "ts": float(e.get("timestamp") or 0)})

    print(f"  {len(rows):,} entries with verses to back-fill")
    print(f"  total edges to write: {sum(len(r['verse_ids']) for r in rows):,}")

    if args.dry_run:
        print("\n  --dry-run: no writes performed")
        d.close()
        return

    # For each cache entry, MERGE a synthetic Query + ReasoningTrace that
    # carries the question text. If a Query with the same text already
    # exists (from live runs), reuse it. Then write RETRIEVED edges.
    print("\nWriting synthetic Query/ReasoningTrace + RETRIEVED edges...")
    BATCH = 50
    written = 0
    skipped = 0
    with d.session(database=DB) as s:
        for i in range(0, len(rows), BATCH):
            chunk = rows[i:i + BATCH]
            params = [
                {
                    "qid": str(uuid.uuid4()),
                    "tid": str(uuid.uuid4()),
                    "qtext": r["question"],
                    "verse_ids": r["verse_ids"],
                    "ts": r["ts"] or datetime.now(timezone.utc).timestamp(),
                }
                for r in chunk
            ]
            res = s.run("""
                UNWIND $rows AS row
                // Reuse existing Query if same text already lives in the graph
                MERGE (q:Query {text: row.qtext})
                ON CREATE SET q.queryId   = row.qid,
                              q.timestamp = datetime({epochSeconds: toInteger(row.ts)}),
                              q.backend   = 'cache_seed_backfill',
                              q.deep_dive = false
                MERGE (q)-[:TRIGGERED]->(t:ReasoningTrace {traceId: q.queryId + '__seed'})
                ON CREATE SET t.status = 'cache_seed',
                              t.total_duration_ms = 0,
                              t.tool_call_count = 0,
                              t.turn_count = 0
                WITH q, t, row
                UNWIND row.verse_ids AS vref
                MATCH (v:Verse {verseId: vref})
                MERGE (t)-[r:RETRIEVED {tool: $tool, call_id: 'cache_seed'}]->(v)
                ON CREATE SET r.rank = 1,
                              r.turn = 0,
                              r.ts   = datetime({epochSeconds: toInteger(row.ts)})
                RETURN count(r) AS n
            """, rows=params, tool=TOOL_TAG).single()
            written += res["n"] or 0
            done = min(i + BATCH, len(rows))
            print(f"  {done}/{len(rows)} entries, {written} edges so far", end="\r")
    print(f"  {len(rows)}/{len(rows)} entries, {written} edges total OK             ")

    # Verification
    print("\nVerifying...")
    with d.session(database=DB) as s:
        n_total = s.run(
            "MATCH ()-[r:RETRIEVED]->() RETURN count(r) AS n"
        ).single()["n"]
        n_cache = s.run(
            "MATCH ()-[r:RETRIEVED {tool: $tool}]->() RETURN count(r) AS n",
            tool=TOOL_TAG,
        ).single()["n"]
        # Top 10 most-retrieved verses
        top = s.run("""
            MATCH ()-[r:RETRIEVED]->(v:Verse)
            RETURN v.verseId AS id, count(r) AS n
            ORDER BY n DESC LIMIT 10
        """).data()
    print(f"  total :RETRIEVED edges in graph: {n_total:,}")
    print(f"  of which cache_seed-tagged:      {n_cache:,}")
    print(f"\n  top-10 most-retrieved verses (across all tools):")
    for r in top:
        print(f"    [{r['id']}]  {r['n']} retrievals")

    d.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
