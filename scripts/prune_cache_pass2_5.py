"""
Pass 2.5 — looser prune over LOW-tier survivors of Pass 2.

The Pass 2 triple-AND criterion (score<0.15 AND len<200 AND cites==0) only
caught one canonical "test" stub. The cache-quality audit (Pass 1) flagged
~80 LOW-tier entries that combine bogus citations (verseIds out of range
like [110:9]), repetition, and a low overall quality score — those survive
Pass 2 because they DO contain citations and long text.

Pass 2.5 criterion (looser, three-AND):

    quality_score   < 0.20
    cite_validity   < 0.5
    has_repetition  == True

Cite validity is recomputed inline against Neo4j (same batched lookup as
audit_cache_quality.py) so this script is self-contained and doesn't depend
on the gitignored Pass-1 sidecar.

Safety:
  - Stops if the prune set exceeds 150 entries (brief's overshoot ceiling).
  - Paper trail: data/research/cache_pruned_pass2_5_2026-05-21.jsonl
  - Cache rewritten via answer_cache._save_cache() for format consistency.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import answer_cache  # noqa: E402

CACHE_FILE = ROOT / "data" / "answer_cache.json"
TRAIL_FILE = ROOT / "data" / "research" / "cache_pruned_pass2_5_2026-05-21.jsonl"

MAX_PRUNE = 150  # brief's overshoot ceiling

CITE_RX = re.compile(r"\[(\d{1,3}):(\d{1,3})\]")
SENT_RX = re.compile(r"(?<=[.!?])\s+")
ARABIC_RX = re.compile(r"[؀-ۿ]")


def extract_cites(text: str) -> list[tuple[int, int]]:
    out = []
    for surah, verse in CITE_RX.findall(text or ""):
        s, v = int(surah), int(verse)
        if 1 <= s <= 114 and 1 <= v <= 286:
            out.append((s, v))
    return out


def has_repetition(text: str) -> bool:
    if not text:
        return False
    sents = [s.strip() for s in SENT_RX.split(text) if len(s.strip()) >= 40]
    if not sents:
        return False
    c = Counter(sents)
    return any(v >= 2 for v in c.values())


def score_entry(rec: dict, valid_cites: set[tuple[int, int]]) -> dict:
    """Mirror of audit_cache_quality.score_entry — kept inline so Pass 2.5
    doesn't depend on the gitignored audit sidecar."""
    answer = rec.get("answer", "") or ""
    cites = extract_cites(answer)
    cite_set = set(cites)
    cite_count = len(cites)
    validity = (
        sum(1 for c in cite_set if c in valid_cites) / len(cite_set)
        if cite_set
        else 0.0
    )
    answer_len = len(answer)
    rep = has_repetition(answer)
    arabic = bool(ARABIC_RX.search(answer))

    quality = (
        0.3 * min(cite_count / 5.0, 1.0)
        + 0.3 * validity
        + 0.2 * (1.0 if answer_len >= 300 else 0.0)
        + 0.1 * (1.0 if arabic else 0.0)
        - 0.4 * (1.0 if rep else 0.0)
    )
    quality = max(0.0, min(1.0, quality))

    return {
        "quality_score": round(quality, 3),
        "cite_validity": round(validity, 3),
        "has_repetition": rep,
        "cite_count": cite_count,
        "answer_len": answer_len,
    }


def main() -> int:
    load_dotenv(ROOT / ".env")
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    pw = os.getenv("NEO4J_PASSWORD")
    db = os.getenv("NEO4J_DATABASE", "quran")
    if not (uri and user and pw):
        print("Missing Neo4j env vars", file=sys.stderr)
        return 2

    cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    print(f"Cache before: {len(cache)}")

    all_cites: set[tuple[int, int]] = set()
    for r in cache:
        for c in extract_cites(r.get("answer", "") or ""):
            all_cites.add(c)
    print(f"Unique cited verseIds across cache: {len(all_cites)}")

    valid: set[tuple[int, int]] = set()
    driver = GraphDatabase.driver(uri, auth=(user, pw))
    with driver.session(database=db) as s:
        rows = s.run(
            """
            UNWIND $cites AS pair
            WITH pair[0] AS surah, pair[1] AS verse
            MATCH (v:Verse {surah: surah, verseNum: verse})
            RETURN surah, verse
            """,
            cites=[list(c) for c in all_cites],
        ).data()
    driver.close()
    for row in rows:
        valid.add((row["surah"], row["verse"]))
    print(f"Valid in Neo4j:                       {len(valid)}")

    to_prune: list[tuple[dict, dict]] = []  # (cache_rec, signals)
    kept: list[dict] = []
    for rec in cache:
        sig = score_entry(rec, valid)
        if (
            sig["quality_score"] < 0.20
            and sig["cite_validity"] < 0.5
            and sig["has_repetition"]
        ):
            to_prune.append((rec, sig))
        else:
            kept.append(rec)

    n_prune = len(to_prune)
    print(f"Matched Pass 2.5 criteria: {n_prune}")

    if n_prune > MAX_PRUNE:
        print(
            f"!!! STOP: prune set ({n_prune}) exceeds overshoot ceiling "
            f"({MAX_PRUNE}). Criteria likely too loose — manual review required.",
            file=sys.stderr,
        )
        return 3

    if n_prune == 0:
        print("No entries matched. Nothing to do.")
        return 0

    pruned_records = []
    for rec, sig in to_prune:
        pruned_records.append(
            {
                "question": rec.get("question", ""),
                "answer_preview": (rec.get("answer", "") or "")[:300],
                "quality_score": sig["quality_score"],
                "cite_validity": sig["cite_validity"],
                "has_repetition": sig["has_repetition"],
                "cite_count": sig["cite_count"],
                "answer_len": sig["answer_len"],
                "timestamp": rec.get("timestamp"),
            }
        )

    TRAIL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with TRAIL_FILE.open("w", encoding="utf-8") as f:
        for p in pruned_records:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    answer_cache._save_cache(kept)

    after = len(kept)
    print(f"Cache after:  {after}  (-{len(cache) - after})")
    print(f"Paper trail:  {TRAIL_FILE.relative_to(ROOT)}")
    print()
    print("Sample pruned entries (up to 10):")
    for p in pruned_records[:10]:
        print(
            f"  - q={p['question'][:80]!r}  "
            f"score={p['quality_score']}  validity={p['cite_validity']}  "
            f"cites={p['cite_count']}  len={p['answer_len']}"
        )
    if len(pruned_records) > 10:
        print(f"  ... +{len(pruned_records) - 10} more in the paper trail")

    return 0


if __name__ == "__main__":
    sys.exit(main())
