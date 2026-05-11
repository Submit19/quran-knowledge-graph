"""
Backfill valid_from and model_version onto existing RETRIEVED edges.

Run ONCE after deploying the reasoning_memory.py update that writes these
properties on new edges.  Idempotent — edges that already have model_version
are skipped.

Usage:
    python backfill_retrieved_model_version.py

Environment:
    NEO4J_URI        defaults to neo4j://127.0.0.1:7687
    NEO4J_USER       defaults to neo4j
    NEO4J_PASSWORD   defaults to Bismillah19
    NEO4J_DATABASE   defaults to quran

Context:
    Task: from_neo4j_yt_memory_01_bitemporal_retrieved (p75, cleanup)
    Adds `valid_from` (ISO timestamp) and `model_version` string to RETRIEVED
    edges. Existing edges predate BGE-M3, so they get the sentinel 'pre-bge-m3'.
    Enables bitemporal queries such as:
        "Which verses ranked highly under MiniLM but not BGE-M3?"
    Schema-additive; no indexes dropped.
"""

import os
import sys

NEO4J_URI = os.environ.get("NEO4J_URI", "neo4j://127.0.0.1:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "Bismillah19")
NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE", "quran")

SENTINEL_MODEL = "pre-bge-m3"
# Approximate timestamp before BGE-M3 rollout — used as valid_from sentinel
SENTINEL_TS = "2026-04-27T00:00:00+00:00"

BATCH_SIZE = 2000


def run_backfill(driver):
    with driver.session(database=NEO4J_DATABASE) as s:
        # Count edges that need backfill
        total = s.run(
            "MATCH ()-[r:RETRIEVED]->() WHERE r.model_version IS NULL RETURN count(r) AS n"
        ).single()["n"]
        print(f"Edges to backfill: {total}")
        if total == 0:
            print("Nothing to do — all RETRIEVED edges already have model_version.")
            return

        batches = 0
        while True:
            result = s.run(
                """
                MATCH ()-[r:RETRIEVED]->()
                WHERE r.model_version IS NULL
                WITH r LIMIT $batch
                SET r.model_version = $mv,
                    r.valid_from    = $ts
                RETURN count(r) AS updated
                """,
                batch=BATCH_SIZE,
                mv=SENTINEL_MODEL,
                ts=SENTINEL_TS,
            )
            updated = result.single()["updated"]
            batches += 1
            print(f"  batch {batches}: set {updated} edges")
            if updated == 0:
                break

        # Final count
        remaining = s.run(
            "MATCH ()-[r:RETRIEVED]->() WHERE r.model_version IS NULL RETURN count(r) AS n"
        ).single()["n"]
        print(f"Backfill complete. Remaining without model_version: {remaining}")


def main():
    try:
        from neo4j import GraphDatabase
    except ImportError:
        print("ERROR: neo4j package not installed. Run: pip install neo4j")
        sys.exit(1)

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        run_backfill(driver)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
