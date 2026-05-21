"""Merge the expansion answers into data/answer_cache.json.

Reads data/eval/v2/baseline_extra_overnight_2026-05-21.jsonl, looks
up each citation against Neo4j to build the (verse_text, arabic)
dict the cache expects, then calls answer_cache.save_answer() for
each record.

The cache's 0.98 cosine dedupe means if a near-identical question
already exists, the entry is overwritten with the expansion
version — so this script is safe to re-run.

RUN FROM THE MAIN CHECKOUT (not from a worktree) — the live
data/answer_cache.json lives only in the main checkout.

Usage:
    python scripts/merge_expansion_to_cache.py
    python scripts/merge_expansion_to_cache.py --dry-run
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPANSION_JSONL = (
    REPO_ROOT / "data" / "eval" / "v2" / "baseline_extra_overnight_2026-05-21.jsonl"
)


def fetch_verses(driver, db, verse_ids: list[str]) -> dict:
    """Return {verse_id: {text, arabic}} for the given ids."""
    if not verse_ids:
        return {}
    with driver.session(database=db) as session:
        rows = session.run(
            "UNWIND $ids AS vid "
            "MATCH (v:Verse {verseId: vid}) "
            "RETURN v.verseId AS id, v.text AS t, v.arabicPlain AS ar",
            ids=verse_ids,
        ).values()
    return {row[0]: {"text": row[1] or "", "arabic": row[2] or ""} for row in rows}


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    sys.path.insert(0, str(REPO_ROOT))
    from answer_cache import save_answer, cache_stats

    if not EXPANSION_JSONL.exists():
        raise SystemExit(f"expansion file not found: {EXPANSION_JSONL}")

    records = []
    with EXPANSION_JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    print(f"loaded {len(records)} expansion records from {EXPANSION_JSONL.name}")

    if not dry_run:
        before = cache_stats()
        print(f"cache before: {before}")

    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")),
    )
    db = os.getenv("NEO4J_DATABASE", "quran")

    missing_cite_count = 0
    appended_or_updated = 0

    try:
        for rec in records:
            qid = rec["id"]
            question = rec["question"]
            answer = rec["answer"]
            citations = rec.get("citations", []) or []

            verses = fetch_verses(driver, db, citations)
            missing = [c for c in citations if c not in verses]
            if missing:
                missing_cite_count += len(missing)
                print(
                    f"  {qid}: WARN — {len(missing)} citations not found in graph: {missing[:5]}"
                )

            if dry_run:
                print(
                    f"  [dry] {qid}: would save question ({len(question)}c), "
                    f"answer ({len(answer)}c), verses dict has {len(verses)} entries"
                )
                continue

            save_answer(question, answer, verses=verses)
            appended_or_updated += 1

    finally:
        driver.close()

    if not dry_run:
        after = cache_stats()
        print(f"cache after:  {after}")
        delta = after["total_entries"] - before["total_entries"]
        print(
            f"net cache change: +{delta} entries (some may have been updates via 0.98 dedupe)"
        )
        print(f"records processed: {appended_or_updated}")
        print(f"total missing citations across all records: {missing_cite_count}")
    else:
        print(f"\n[dry-run] would have processed {len(records)} records")
        print(f"[dry-run] total missing citations: {missing_cite_count}")


if __name__ == "__main__":
    main()
