"""Shape A: direct cache-scoring eval.

For each phase-4b main-set question:
  1. Search the cache via answer_cache.search_cache (top-1).
  2. If no cache hit (similarity < 0.6) -> CACHE_MISS, hard_pass=False.
  3. Otherwise extract cited verseIds from the cached answer and run the
     question's programmatic asserts on it.

Tools assertions: tools_used_must_include / _must_not_include are SKIPPED
because cache-direct scoring doesn't have access to a live agent trajectory.
The cached entry's stored tools_used field reflects what tools were called
when the entry was generated, not what an agent would invoke now. We note
this in the report.

Output: data/research/cache_eval_loop/iter_NNN_shape_a.json with per-question
results plus aggregate stats.

Usage:
  python scripts/eval_shape_a.py --iter 0 [--cache data/answer_cache.json]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from answer_cache import search_cache, _reset_memory_cache_for_tests  # noqa: E402


CITATION_PATTERN = re.compile(r"\[(\d+):(\d+)\]")
EVAL_DIR = REPO_ROOT / "data" / "eval" / "v2"
MAIN_BUCKETS = ("abstract", "broad", "concrete", "structured")


def load_main_questions() -> list[dict]:
    qs: list[dict] = []
    for bucket in MAIN_BUCKETS:
        with open(EVAL_DIR / f"{bucket}.yaml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or []
        qs.extend(data)
    return qs


def extract_citations(text: str) -> set[str]:
    return {f"{s}:{v}" for s, v in CITATION_PATTERN.findall(text or "")}


def check_asserts_on_cached(
    asserts: dict, answer_text: str, citations: set[str]
) -> dict:
    """Return {passed: [...], failed: [...], skipped: [...]}.

    tools_used_* are skipped (cache-direct has no live trajectory).
    """
    passed: list[str] = []
    failed: list[str] = []
    skipped: list[str] = []
    asserts = asserts or {}
    answer_lower = (answer_text or "").lower()

    for vid in asserts.get("cites_must_include") or []:
        label = f"cites_must_include:{vid}"
        (passed if vid in citations else failed).append(label)

    for vid in asserts.get("cites_must_not_include") or []:
        label = f"cites_must_not_include:{vid}"
        (failed if vid in citations else passed).append(label)

    for needle in asserts.get("answer_substring_required") or []:
        label = f"answer_substring_required:{needle}"
        (passed if needle.lower() in answer_lower else failed).append(label)

    for needle in asserts.get("answer_substring_forbidden") or []:
        label = f"answer_substring_forbidden:{needle}"
        (failed if needle.lower() in answer_lower else passed).append(label)

    for tool in asserts.get("tools_used_must_include") or []:
        skipped.append(f"tools_used_must_include:{tool}")
    for tool in asserts.get("tools_used_must_not_include") or []:
        skipped.append(f"tools_used_must_not_include:{tool}")

    return {"passed": passed, "failed": failed, "skipped": skipped}


def evaluate(questions: list[dict]) -> dict:
    per_question: list[dict] = []
    for q in questions:
        qid = q["id"]
        bucket = q["bucket"]
        hits = search_cache(q["question"], top_k=1, threshold=0.6)
        if not hits:
            per_question.append(
                {
                    "id": qid,
                    "bucket": bucket,
                    "cache_hit": False,
                    "similarity": None,
                    "retrieved_question": None,
                    "answer_length": 0,
                    "cite_count": 0,
                    "asserts": {"passed": [], "failed": ["CACHE_MISS"], "skipped": []},
                    "hard_pass": False,
                    "applicable_asserts": _count_applicable(q.get("asserts", {})),
                }
            )
            continue
        top = hits[0]
        ans = top.get("answer", "")
        cites = extract_citations(ans)
        outcome = check_asserts_on_cached(q.get("asserts", {}), ans, cites)
        per_question.append(
            {
                "id": qid,
                "bucket": bucket,
                "cache_hit": True,
                "similarity": top.get("similarity"),
                "rerank_score": top.get("rerank_score"),
                "retrieved_question": top.get("question"),
                "answer_length": len(ans),
                "cite_count": len(cites),
                "asserts": outcome,
                "hard_pass": (not outcome["failed"]),
                "applicable_asserts": _count_applicable(q.get("asserts", {})),
            }
        )

    return _aggregate(per_question)


def _count_applicable(asserts: dict) -> int:
    """How many programmatic asserts (excl. tools_used_*) does this Q have?"""
    if not asserts:
        return 0
    keys = (
        "cites_must_include",
        "cites_must_not_include",
        "answer_substring_required",
        "answer_substring_forbidden",
    )
    return sum(len(asserts.get(k) or []) for k in keys)


def _aggregate(per_question: list[dict]) -> dict:
    total = len(per_question)
    hard_pass = sum(1 for r in per_question if r["hard_pass"])
    cache_hits = sum(1 for r in per_question if r["cache_hit"])
    by_bucket: dict[str, dict] = {}
    for r in per_question:
        b = r["bucket"]
        d = by_bucket.setdefault(b, {"total": 0, "hard_pass": 0, "cache_hits": 0})
        d["total"] += 1
        if r["hard_pass"]:
            d["hard_pass"] += 1
        if r["cache_hit"]:
            d["cache_hits"] += 1

    failures = sorted(
        [r for r in per_question if not r["hard_pass"]],
        key=lambda r: (
            len(r["asserts"]["failed"]),
            -(r.get("similarity") or 0.0),
        ),
        reverse=True,
    )

    return {
        "total": total,
        "hard_pass": hard_pass,
        "hard_pass_rate": round(hard_pass / total, 4) if total else 0.0,
        "cache_hits": cache_hits,
        "cache_hit_rate": round(cache_hits / total, 4) if total else 0.0,
        "by_bucket": by_bucket,
        "worst_failures": failures[:15],
        "per_question": per_question,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iter", required=True, help="iteration number, e.g. 0")
    ap.add_argument("--cache", default=None, help="optional cache file path override")
    ap.add_argument("--out", default=None, help="optional output path override")
    args = ap.parse_args()

    if args.cache:
        os.environ["__SHAPE_A_CACHE_OVERRIDE__"] = args.cache
        import answer_cache as ac

        ac.CACHE_FILE = Path(args.cache)
        _reset_memory_cache_for_tests()

    questions = load_main_questions()
    print(
        f"[shape_a] loaded {len(questions)} questions across {len(MAIN_BUCKETS)} buckets"
    )
    print(
        f"[shape_a] cache file: {Path(args.cache).resolve() if args.cache else 'data/answer_cache.json'}"
    )

    result = evaluate(questions)
    print(
        f"[shape_a] hard_pass {result['hard_pass']}/{result['total']} ({result['hard_pass_rate'] * 100:.1f}%)"
    )
    print(
        f"[shape_a] cache_hits {result['cache_hits']}/{result['total']} ({result['cache_hit_rate'] * 100:.1f}%)"
    )
    for b, d in sorted(result["by_bucket"].items()):
        print(
            f"[shape_a]   {b}: {d['hard_pass']}/{d['total']} ({d['hard_pass'] / d['total'] * 100:.1f}%)"
        )

    out_path = (
        Path(args.out)
        if args.out
        else (
            REPO_ROOT
            / "data"
            / "research"
            / "cache_eval_loop"
            / f"iter_{int(args.iter):03d}_shape_a.json"
        )
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[shape_a] wrote {out_path}")


if __name__ == "__main__":
    main()
