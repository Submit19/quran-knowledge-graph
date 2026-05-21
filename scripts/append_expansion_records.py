"""Append expansion answer records to the JSONL.

Usage:
    python scripts/append_expansion_records.py records.json

Where records.json contains a JSON array of records, each:
{
  id: 'expansion-NNN',
  question, answer, citations [str],
  category, priority_score, gap_addressed,
  tools_used: [...], tools_used_agent_equivalent: [...]
}
The script:
- Verifies every citation resolves in Neo4j; warns if not, but
  still appends (the writer is responsible — we just record the
  citation-validity rate).
- Adds `model`, `method`, `answered_at`, `bucket`, `verses` dict
- Appends to data/eval/v2/baseline_extra_overnight_2026-05-21.jsonl
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_JSONL = (
    REPO_ROOT / "data" / "eval" / "v2" / "baseline_extra_overnight_2026-05-21.jsonl"
)


def fetch_verses(driver, db, vids: list[str]) -> dict:
    if not vids:
        return {}
    with driver.session(database=db) as s:
        rows = s.run(
            """
            UNWIND $ids AS vid
            MATCH (v:Verse {verseId: vid})
            RETURN v.verseId AS id, v.text AS t, v.arabicPlain AS ar
            """,
            ids=vids,
        ).values()
    return {r[0]: {"text": r[1] or "", "arabic": r[2] or ""} for r in rows}


def main():
    records_path = Path(sys.argv[1])
    records = json.load(records_path.open(encoding="utf-8"))
    print(f"loaded {len(records)} records from {records_path.name}")

    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")),
    )
    db = os.getenv("NEO4J_DATABASE", "quran")

    total_cites = 0
    valid_cites = 0
    invalid_by_id: dict[str, list[str]] = {}

    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    appended = 0
    try:
        with OUT_JSONL.open("a", encoding="utf-8") as f:
            for rec in records:
                cites = rec.get("citations") or []
                verses = fetch_verses(driver, db, cites) if cites else {}
                missing = [c for c in cites if c not in verses]
                total_cites += len(cites)
                valid_cites += len(cites) - len(missing)
                if missing:
                    invalid_by_id[rec["id"]] = missing

                final = {
                    "id": rec["id"],
                    "bucket": "EXPANSION",
                    "category": rec.get("category", ""),
                    "question": rec["question"],
                    "answer": rec["answer"],
                    "citations": cites,
                    "verses": verses,
                    "tools_used": rec.get("tools_used") or ["run_cypher"],
                    "tools_used_agent_equivalent": rec.get(
                        "tools_used_agent_equivalent"
                    )
                    or [],
                    "model": "claude-opus-4-7[1m]",
                    "method": "advisor-overnight-bash-cypher",
                    "answered_at": datetime.now(timezone.utc).isoformat(),
                    "priority_score": rec.get("priority_score", 0),
                    "gap_addressed": rec.get("gap_addressed", ""),
                }
                f.write(json.dumps(final, ensure_ascii=False) + "\n")
                appended += 1
    finally:
        driver.close()

    rate = (valid_cites / total_cites * 100) if total_cites else 100.0
    print(f"appended {appended} records to {OUT_JSONL.name}")
    print(f"citation validity: {valid_cites}/{total_cites} = {rate:.1f}%")
    if invalid_by_id:
        print("invalid citations:")
        for k, v in invalid_by_id.items():
            print(f"  {k}: {v[:5]}{' …' if len(v) > 5 else ''}")


if __name__ == "__main__":
    main()
