"""
eval_qrcd.py — evaluate QKG against the QRCD benchmark (Quran-QA 2022/2023).

Dataset: tarteel-ai/quranqa on HuggingFace.
  Train: 710 q-p pairs (861 triplets)
  Dev:   109 q-p pairs (128 triplets)
  Test:  274 q-p pairs (348 triplets)

Each example has:
  pq_id     "38:41-44_105"        (surah:verseRange_questionId)
  passage   Arabic text
  surah     int
  verses    "41-44" or "12"       (range or single)
  question  Arabic text
  answers   [{text, start_char}, ...]

We treat the gold "passage" as the set of correct verseIds (e.g. surah=38,
verses="41-44" -> {38:41, 38:42, 38:43, 38:44}). For each question we
ask the agent (via /chat at localhost:8085), parse its [X:Y] citations,
and compute:

  - hit@k    : did any of the agent's top-k citations overlap with gold?
  - recall@k : |cited & gold| / |gold|
  - mrr      : 1/rank of first correct citation (0 if none)

Run:
  python eval_qrcd.py --n 30          # pilot run on first 30 test items
  python eval_qrcd.py --split test    # full test set (274 items)
  python eval_qrcd.py --port 8085 --out data/qrcd_results.json
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import requests

from eval_common import hit_at_k, recall_at_k, first_hit_rank

# Lazy import datasets only if not using a cached local copy
LOCAL_QRCD = Path(__file__).parent / "data" / "qrcd_test.jsonl"


def load_qrcd(split: str = "test", n: int = None):
    """Load QRCD; cache locally so we don't re-fetch."""
    cache = Path(__file__).parent / "data" / f"qrcd_{split}.jsonl"
    if cache.exists():
        items = [json.loads(line) for line in cache.read_text(encoding="utf-8").splitlines() if line.strip()]
        return items[:n] if n else items

    print(f"  fetching tarteel-ai/quranqa[{split}] from HuggingFace...")
    from datasets import load_dataset
    ds = load_dataset("tarteel-ai/quranqa", split=split)
    items = [dict(row) for row in ds]
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text("\n".join(json.dumps(it, ensure_ascii=False) for it in items),
                     encoding="utf-8")
    return items[:n] if n else items


def gold_verse_ids(item: dict) -> set[str]:
    """Convert (surah, verses) into a set of verseId strings."""
    sura = item["surah"]
    vrange = str(item["verses"])
    out = set()
    if "-" in vrange:
        a, b = vrange.split("-", 1)
        try:
            for v in range(int(a), int(b) + 1):
                out.add(f"{sura}:{v}")
        except ValueError:
            pass
    else:
        out.add(f"{sura}:{vrange}")
    return out


_CITE = re.compile(r"\[(\d+):(\d+)\]")
def extract_citations(answer_text: str) -> list[str]:
    """Return citations in order they appear (deduped, preserving first-seen rank)."""
    seen = []
    seen_set = set()
    for m in _CITE.finditer(answer_text):
        ref = f"{m.group(1)}:{m.group(2)}"
        if ref not in seen_set:
            seen.append(ref)
            seen_set.add(ref)
    return seen


def ask_agent(base_url: str, question: str, timeout: int = 600) -> dict:
    """POST to /chat and stream-parse the SSE response."""
    t0 = time.time()
    payload = {
        "message": question,
        "history": [],
        "deep_dive": False,
        "full_coverage": True,
    }
    r = requests.post(f"{base_url}/chat", json=payload, stream=True, timeout=timeout)
    r.raise_for_status()

    full = ""
    tool_calls = 0
    for line in r.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        try:
            ev = json.loads(line[6:])
        except Exception:
            continue
        t = ev.get("t")
        if t == "tool":
            tool_calls += 1
        if t == "text":
            full += ev.get("d", "")
        if t == "done":
            break
        if t == "error":
            return {"ok": False, "error": ev.get("d", "")[:300],
                    "elapsed": time.time() - t0}
    return {"ok": True, "answer": full, "tool_calls": tool_calls,
            "elapsed": round(time.time() - t0, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8085)
    ap.add_argument("--split", default="test", help="train|validation|test")
    ap.add_argument("--n", type=int, default=30, help="how many items (default 30 for pilot)")
    ap.add_argument("--out", default="data/qrcd_results.json")
    ap.add_argument("--start", type=int, default=0, help="skip the first N (resume support)")
    args = ap.parse_args()

    base = f"http://localhost:{args.port}"
    print(f"Loading QRCD[{args.split}]...")
    items = load_qrcd(args.split, n=None)  # load all, then slice
    print(f"  loaded {len(items)} total items")

    items = items[args.start:args.start + args.n]
    print(f"  evaluating {len(items)} items (start={args.start}, n={args.n})")

    # Verify server
    try:
        requests.get(base, timeout=5).raise_for_status()
    except Exception as e:
        print(f"FATAL: server at {base} not reachable: {e}")
        sys.exit(1)

    results = []
    summary = {"n": 0,
               "hit@1": 0, "hit@3": 0, "hit@5": 0, "hit@10": 0,
               "sum_recall@5": 0.0, "sum_recall@10": 0.0,
               "sum_reciprocal_rank": 0.0,
               "sum_elapsed": 0.0,
               "errors": 0,
               "skipped_no_arabic": 0}

    for i, item in enumerate(items, 1):
        q = item.get("question", "")
        gold = gold_verse_ids(item)
        if not q or not gold:
            summary["skipped_no_arabic"] += 1
            continue

        print(f"\n[{i}/{len(items)}] pq_id={item.get('pq_id')} | gold={sorted(gold)}")
        print(f"  Q: {q[:90]}{'...' if len(q) > 90 else ''}")

        try:
            r = ask_agent(base, q)
        except Exception as e:
            print(f"  ERROR: {e}")
            summary["errors"] += 1
            results.append({"pq_id": item.get("pq_id"), "question": q,
                            "gold": sorted(gold), "ok": False, "error": str(e)[:300]})
            continue

        if not r["ok"]:
            print(f"  FAIL: {r.get('error')}")
            summary["errors"] += 1
            results.append({"pq_id": item.get("pq_id"), "question": q,
                            "gold": sorted(gold), "ok": False,
                            "error": r.get("error", "unknown")})
            continue

        cites = extract_citations(r["answer"])
        rank = first_hit_rank(cites, gold)
        rec5 = recall_at_k(cites, gold, 5)
        rec10 = recall_at_k(cites, gold, 10)
        h1 = hit_at_k(cites, gold, 1)
        h3 = hit_at_k(cites, gold, 3)
        h5 = hit_at_k(cites, gold, 5)
        h10 = hit_at_k(cites, gold, 10)

        summary["n"] += 1
        summary["hit@1"] += int(h1)
        summary["hit@3"] += int(h3)
        summary["hit@5"] += int(h5)
        summary["hit@10"] += int(h10)
        summary["sum_recall@5"] += rec5
        summary["sum_recall@10"] += rec10
        summary["sum_reciprocal_rank"] += (1.0 / rank) if rank else 0.0
        summary["sum_elapsed"] += r["elapsed"]

        print(f"  -> {r['elapsed']}s, {r['tool_calls']} tools, {len(cites)} cites")
        print(f"     hit@5={h5} recall@10={rec10:.2f} rr={1/rank if rank else 0:.2f} "
              f"top10={cites[:10]}")

        results.append({
            "pq_id": item.get("pq_id"),
            "question": q,
            "gold": sorted(gold),
            "ok": True,
            "elapsed": r["elapsed"],
            "tool_calls": r["tool_calls"],
            "cites": cites[:30],
            "first_hit_rank": rank,
            "hit@1": h1, "hit@3": h3, "hit@5": h5, "hit@10": h10,
            "recall@5": round(rec5, 4),
            "recall@10": round(rec10, 4),
            "answer_chars": len(r["answer"]),
        })

        # Persist progressively (every 5 items) so we don't lose work
        if i % 5 == 0:
            Path(args.out).write_text(json.dumps({
                "summary": summary, "results": results
            }, indent=2, ensure_ascii=False), encoding="utf-8")

    # Final stats
    n = summary["n"] or 1
    final = {
        "computed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "split": args.split,
        "n_evaluated": summary["n"],
        "n_errors": summary["errors"],
        "hit@1": round(summary["hit@1"] / n, 4),
        "hit@3": round(summary["hit@3"] / n, 4),
        "hit@5": round(summary["hit@5"] / n, 4),
        "hit@10": round(summary["hit@10"] / n, 4),
        "recall@5": round(summary["sum_recall@5"] / n, 4),
        "recall@10": round(summary["sum_recall@10"] / n, 4),
        "mrr": round(summary["sum_reciprocal_rank"] / n, 4),
        "avg_elapsed_sec": round(summary["sum_elapsed"] / n, 1),
    }

    Path(args.out).write_text(json.dumps({
        "summary": final, "results": results
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n=== QRCD eval summary ===")
    for k, v in final.items():
        print(f"  {k}: {v}")
    print(f"\n  Output: {args.out}")


if __name__ == "__main__":
    main()
