"""
eval_v1_bucketed.py — 50-question bucketed end-to-end eval for QKG.

Adds bucket-level breakdown to the eval_v1 framework:
  - avg_cites per bucket (STRUCTURED | ABSTRACT | CONCRETE | BROAD | ARABIC)
  - avg_tool_calls per bucket
  - avg_elapsed per bucket

Usage:
    python eval_v1_bucketed.py
    python eval_v1_bucketed.py --bucket STRUCTURED   # run one bucket only
    python eval_v1_bucketed.py --dry-run             # list questions, no API calls
    python eval_v1_bucketed.py --ids s01,a02,b03     # run specific question IDs

Environment:
    EVAL_PORT=8085            (default)
    EVAL_MODEL=openai/gpt-oss-120b:free  (default; ignored when EVAL_LOCAL_ONLY=1)
    EVAL_LOCAL_ONLY=0         (set to 1 for Ollama)

Output:
    data/eval_v1_bucketed_results.json
    data/eval_v1_bucketed_results.md
"""
import json
import os
import re
import sys
import time
import argparse
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import requests
import yaml

PORT = int(os.environ.get("EVAL_PORT", 8085))
BASE = f"http://localhost:{PORT}"
QUESTIONS_FILE = Path("data/eval_v1_50q_bucketed.yaml")
OUT_JSON = Path("data/eval_v1_bucketed_results.json")
OUT_MD = Path("data/eval_v1_bucketed_results.md")

EVAL_MODEL = os.environ.get("EVAL_MODEL", "openai/gpt-oss-120b:free")
EVAL_LOCAL_ONLY = os.environ.get("EVAL_LOCAL_ONLY", "0") == "1"


def ask(message: str, timeout: int = 900) -> dict:
    """Send a question to /chat and collect SSE events."""
    t0 = time.time()
    payload = {
        "message": message,
        "history": [],
        "deep_dive": False,
        "full_coverage": True,
        "local_only": EVAL_LOCAL_ONLY,
    }
    if not EVAL_LOCAL_ONLY:
        payload["model_override"] = EVAL_MODEL
    try:
        r = requests.post(f"{BASE}/chat", json=payload, stream=True, timeout=timeout)
        r.raise_for_status()
    except Exception as e:
        return {"ok": False, "error": str(e)[:300], "elapsed_sec": round(time.time() - t0, 1),
                "n_citations": 0, "n_unique_citations": 0, "n_tool_calls": 0,
                "tool_call_breakdown": {}, "char_count": 0, "answer": ""}

    full = ""
    tools_fired = []
    error = None
    for line in r.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        try:
            ev = json.loads(line[6:])
        except Exception:
            continue
        etype = ev.get("type")
        if etype == "text":
            full += ev.get("text", "")
        elif etype == "tool":
            tname = ev.get("name", "")
            targs = ev.get("args", {})
            tools_fired.append((tname, str(targs)[:60]))
        elif etype == "error":
            error = ev.get("text", "")

    tool_counter = Counter(t[0] for t in tools_fired)
    cites = re.findall(r"\[\d{1,3}:\d{1,3}\]", full)
    unique_cites = set(cites)
    elapsed = time.time() - t0

    return {
        "ok": True,
        "elapsed_sec": round(elapsed, 1),
        "n_tool_calls": len(tools_fired),
        "tool_call_breakdown": dict(tool_counter),
        "n_citations": len(cites),
        "n_unique_citations": len(unique_cites),
        "char_count": len(full),
        "answer": full[:4000],
        "error": error,
    }


def bucket_stats(results_for_bucket: list) -> dict:
    ok = [r for r in results_for_bucket if r.get("ok")]
    if not ok:
        return {"n": len(results_for_bucket), "ok": 0,
                "avg_cites": 0.0, "avg_unique_cites": 0.0,
                "avg_tools": 0.0, "avg_elapsed_sec": 0.0}
    n = len(ok)
    return {
        "n": len(results_for_bucket),
        "ok": n,
        "avg_cites": round(sum(r["n_citations"] for r in ok) / n, 1),
        "avg_unique_cites": round(sum(r["n_unique_citations"] for r in ok) / n, 1),
        "avg_tools": round(sum(r["n_tool_calls"] for r in ok) / n, 1),
        "avg_elapsed_sec": round(sum(r["elapsed_sec"] for r in ok) / n, 1),
    }


def write_markdown(stats: dict, all_results: list) -> None:
    lines = [
        "# Bucketed Eval Results\n\n",
        f"_Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}_\n\n",
        "## Per-bucket summary\n\n",
        "| Bucket | N | OK | avg_cites | avg_unique | avg_tools | avg_elapsed |\n",
        "|--------|---:|---:|-----------:|-----------:|----------:|------------:|\n",
    ]
    for bucket in ["STRUCTURED", "ABSTRACT", "CONCRETE", "BROAD", "ARABIC", "OVERALL"]:
        s = stats.get(bucket, {})
        sep = "| **" if bucket == "OVERALL" else "| "
        end = "** |" if bucket == "OVERALL" else " |"
        lines.append(
            f"{sep}{bucket}{end} {s.get('n',0)} | {s.get('ok',0)} "
            f"| {s.get('avg_cites',0)} | {s.get('avg_unique_cites',0)} "
            f"| {s.get('avg_tools',0)} | {s.get('avg_elapsed_sec',0)}s |\n"
        )
    lines.append("\n## Per-question detail\n\n")
    for r in all_results:
        status = "OK" if r.get("ok") else f"FAIL"
        lines.append(
            f"- **[{r['bucket']}] {r['id']}** {status}: "
            f"cites={r.get('n_citations',0)} tools={r.get('n_tool_calls',0)} "
            f"elapsed={r.get('elapsed_sec',0)}s\n"
            f"  > {r['question']}\n"
        )
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"Saved: {OUT_MD}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", help="Run only this bucket (STRUCTURED|ABSTRACT|CONCRETE|BROAD|ARABIC)")
    parser.add_argument("--ids", help="Comma-separated question IDs to run (e.g. s01,a02,b03)")
    parser.add_argument("--dry-run", action="store_true", help="List questions without calling API")
    args = parser.parse_args()

    with open(QUESTIONS_FILE, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    questions = data.get("questions", [])

    if args.bucket:
        questions = [q for q in questions if q.get("bucket") == args.bucket.upper()]
        print(f"Filtered to bucket {args.bucket.upper()}: {len(questions)} questions")

    if args.ids:
        id_set = {i.strip() for i in args.ids.split(",")}
        questions = [q for q in questions if q.get("id") in id_set]
        print(f"Filtered to IDs {id_set}: {len(questions)} questions")

    if args.dry_run:
        for q in questions:
            print(f"[{q['bucket']}] {q['id']}: {q['question'][:80]}")
        print(f"\nTotal: {len(questions)} questions")
        return

    # Verify server is up
    try:
        requests.get(f"{BASE}/health", timeout=5)
    except Exception:
        print(f"WARNING: server at {BASE} may not be up — proceeding anyway.")

    all_results = []
    by_bucket: dict = defaultdict(list)

    for i, q_spec in enumerate(questions):
        qid = q_spec["id"]
        bucket = q_spec["bucket"]
        question = q_spec["question"]
        print(f"[{i+1}/{len(questions)}] [{bucket}] {qid}: {question[:65]}", flush=True)
        result = ask(question)
        result["id"] = qid
        result["bucket"] = bucket
        result["question"] = question
        all_results.append(result)
        by_bucket[bucket].append(result)
        status = "OK" if result.get("ok") else f"FAIL({result.get('error','?')[:40]})"
        print(
            f"  -> {status}  cites={result.get('n_citations',0)}"
            f"  tools={result.get('n_tool_calls',0)}"
            f"  elapsed={result.get('elapsed_sec',0)}s"
        )

    # Compute stats
    stats = {b: bucket_stats(rs) for b, rs in by_bucket.items()}
    overall_ok = [r for r in all_results if r.get("ok")]
    n_ok = max(len(overall_ok), 1)
    stats["OVERALL"] = {
        "n": len(all_results),
        "ok": len(overall_ok),
        "avg_cites": round(sum(r["n_citations"] for r in overall_ok) / n_ok, 1),
        "avg_unique_cites": round(sum(r["n_unique_citations"] for r in overall_ok) / n_ok, 1),
        "avg_tools": round(sum(r["n_tool_calls"] for r in overall_ok) / n_ok, 1),
        "avg_elapsed_sec": round(sum(r["elapsed_sec"] for r in overall_ok) / n_ok, 1),
    }

    output = {"stats": stats, "questions": all_results}
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Saved: {OUT_JSON}")

    write_markdown(stats, all_results)

    # Console summary
    print("\n=== BUCKET SUMMARY ===")
    for b in ["STRUCTURED", "ABSTRACT", "CONCRETE", "BROAD", "ARABIC", "OVERALL"]:
        s = stats.get(b, {})
        print(
            f"  {b:12s}: avg_cites={s.get('avg_cites',0):6.1f}"
            f"  avg_tools={s.get('avg_tools',0):4.1f}"
            f"  ok={s.get('ok',0)}/{s.get('n',0)}"
        )


if __name__ == "__main__":
    main()
