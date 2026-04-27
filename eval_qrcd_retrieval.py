"""
eval_qrcd_retrieval.py — pure retrieval evaluation against QRCD test set.

Bypasses the agent loop. Runs each unique QRCD question directly through
the vector index, computes coverage of gold passages.

Compares two retrieval modes:
  - MiniLM   (verse_embedding,    384-dim, English-only)
  - BGE-M3   (verse_embedding_m3, 1024-dim, multilingual)
  - BGE-M3-AR (verse_embedding_m3_ar, 1024-dim, Arabic over Arabic verses)

QRCD test set has 238 items but only 22 unique questions. Each question has
1-142 gold passages (median 4). We group by question and evaluate union.

Metrics:
  hit@k    : did any retrieved verse fall in any gold passage?
  recall@k : |retrieved & gold_verses| / |gold_verses|
  mrr      : 1/rank of first hit (0 if none)
  map@k    : mean average precision @k

Run: python eval_qrcd_retrieval.py
"""

import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
USER     = os.getenv("NEO4J_USER",     "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "")
DB       = os.getenv("NEO4J_DATABASE", "quran")

QRCD_PATH = Path(__file__).parent / "data" / "qrcd_test.jsonl"


def expand_verse_range(surah, vrange) -> set[str]:
    out = set()
    for chunk in str(vrange).split(","):
        chunk = chunk.strip()
        if "-" in chunk:
            a, b = chunk.split("-", 1)
            try:
                for v in range(int(a), int(b) + 1):
                    out.add(f"{surah}:{v}")
            except ValueError:
                pass
        else:
            try:
                int(chunk)
                out.add(f"{surah}:{chunk}")
            except ValueError:
                pass
    return out


def load_qrcd_grouped() -> list[dict]:
    """Group QRCD items by question; gold = union of all passages per question."""
    items = [json.loads(l) for l in QRCD_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_q = defaultdict(lambda: {"gold": set(), "n_passages": 0})
    for it in items:
        gold = expand_verse_range(it["surah"], it["verses"])
        by_q[it["question"]]["gold"] |= gold
        by_q[it["question"]]["n_passages"] += 1
    grouped = [
        {"question": q, "gold": sorted(d["gold"]),
         "n_gold_verses": len(d["gold"]), "n_passages": d["n_passages"]}
        for q, d in by_q.items()
    ]
    grouped.sort(key=lambda x: -x["n_gold_verses"])
    return grouped


def retrieve_verses(driver, vec: list, index_name: str, top_k: int = 100) -> list[tuple[str, float]]:
    """Run vector search and return [(verseId, score), ...]"""
    with driver.session(database=DB) as s:
        rows = s.run("""
            CALL db.index.vector.queryNodes($idx, $k, $vec)
            YIELD node, score
            WHERE node.verseId IS NOT NULL
            RETURN node.verseId AS id, score
            ORDER BY score DESC
        """, idx=index_name, k=top_k, vec=vec).data()
    return [(r["id"], r["score"]) for r in rows]


def hit_at_k(retrieved_ids, gold, k):
    return any(r in gold for r in retrieved_ids[:k])

def recall_at_k(retrieved_ids, gold, k):
    if not gold:
        return 0.0
    return sum(1 for r in retrieved_ids[:k] if r in gold) / len(gold)

def first_hit_rank(retrieved_ids, gold):
    for i, r in enumerate(retrieved_ids, 1):
        if r in gold:
            return i
    return None

def average_precision_at_k(retrieved_ids, gold, k):
    """AP@k = sum(precision@i * relevant(i)) / min(|gold|, k)"""
    if not gold:
        return 0.0
    correct = 0
    sum_p = 0.0
    for i, r in enumerate(retrieved_ids[:k], 1):
        if r in gold:
            correct += 1
            sum_p += correct / i
    return sum_p / min(len(gold), k)


def main():
    print(f"Connecting to Neo4j ({URI}, db={DB})...")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    driver.verify_connectivity()
    print("  OK")

    print("\nLoading QRCD grouped...")
    questions = load_qrcd_grouped()
    print(f"  {len(questions)} unique questions, total gold verses: "
          f"{sum(q['n_gold_verses'] for q in questions)}")

    print("\nLoading embedding models...")
    from sentence_transformers import SentenceTransformer
    minilm = SentenceTransformer("all-MiniLM-L6-v2")
    bge_m3 = SentenceTransformer("BAAI/bge-m3")
    bge_m3.max_seq_length = 512
    print("  models loaded")

    backends = [
        ("MiniLM",       "verse_embedding",        minilm),
        ("BGE-M3-EN",    "verse_embedding_m3",     bge_m3),
        ("BGE-M3-AR",    "verse_embedding_m3_ar",  bge_m3),
    ]

    K_VALUES = [5, 10, 20, 50, 100]
    summaries = {}
    per_q = {b[0]: [] for b in backends}

    for backend_name, index_name, model in backends:
        print(f"\n=== {backend_name} (index: {index_name}) ===")
        agg = {f"hit@{k}": 0 for k in K_VALUES}
        agg.update({f"recall@{k}": 0.0 for k in K_VALUES})
        agg.update({f"map@{k}": 0.0 for k in K_VALUES})
        agg["sum_rr"] = 0.0
        agg["n"] = 0
        agg["sum_n_gold"] = 0

        t0 = time.time()
        for i, q in enumerate(questions, 1):
            qtext = q["question"]
            gold = set(q["gold"])
            vec = model.encode([qtext], normalize_embeddings=True, convert_to_numpy=True)[0].tolist()
            retrieved = retrieve_verses(driver, vec, index_name, top_k=max(K_VALUES))
            ids = [r[0] for r in retrieved]
            rank = first_hit_rank(ids, gold)
            rr = (1.0 / rank) if rank else 0.0

            row = {
                "question": qtext,
                "n_gold_verses": len(gold),
                "first_hit_rank": rank,
                "rr": rr,
            }
            for k in K_VALUES:
                row[f"hit@{k}"]    = hit_at_k(ids, gold, k)
                row[f"recall@{k}"] = recall_at_k(ids, gold, k)
                row[f"map@{k}"]    = average_precision_at_k(ids, gold, k)

                agg[f"hit@{k}"]    += int(row[f"hit@{k}"])
                agg[f"recall@{k}"] += row[f"recall@{k}"]
                agg[f"map@{k}"]    += row[f"map@{k}"]

            agg["sum_rr"] += rr
            agg["n"] += 1
            agg["sum_n_gold"] += len(gold)
            per_q[backend_name].append(row)

        elapsed = time.time() - t0
        n = max(agg["n"], 1)
        smry = {
            "backend": backend_name,
            "index": index_name,
            "n_questions": agg["n"],
            "elapsed_sec": round(elapsed, 1),
            "avg_n_gold_verses": round(agg["sum_n_gold"] / n, 1),
            "mrr": round(agg["sum_rr"] / n, 4),
        }
        for k in K_VALUES:
            smry[f"hit@{k}"]    = round(agg[f"hit@{k}"] / n, 4)
            smry[f"recall@{k}"] = round(agg[f"recall@{k}"] / n, 4)
            smry[f"map@{k}"]    = round(agg[f"map@{k}"] / n, 4)
        summaries[backend_name] = smry
        print(f"  hit@10  = {smry['hit@10']}")
        print(f"  recall@10 = {smry['recall@10']}")
        print(f"  map@10  = {smry['map@10']}")
        print(f"  mrr     = {smry['mrr']}")
        print(f"  elapsed = {elapsed:.1f}s")

    # Comparison table
    print("\n\n=== SIDE-BY-SIDE ===")
    metrics = ["hit@5", "hit@10", "recall@10", "map@10", "mrr"]
    header = "| metric | " + " | ".join(b[0] for b in backends) + " |"
    sep = "|---|" + "|".join(["---"] * len(backends)) + "|"
    print(header); print(sep)
    for m in metrics:
        row = "| " + m + " | " + " | ".join(f"{summaries[b[0]][m]:.4f}" for b in backends) + " |"
        print(row)

    # Save
    out = Path("data") / "qrcd_retrieval_results.json"
    out.write_text(json.dumps({
        "computed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_questions": len(questions),
        "summary": summaries,
        "per_question": per_q,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {out}")

    driver.close()


if __name__ == "__main__":
    main()
