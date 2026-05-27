"""Shape B: held-out cache-lift composition signal.

Held-out questions (data/eval/v2/_holdout.yaml) carry empty asserts (asserts: {}),
so there is no programmatic hard-pass signal. The full Shape-B intent — Opus
composes an answer from cache context then a judge scores it — is prohibitively
expensive in a tight iteration loop.

This script provides a programmatic *proxy* for cache-lift quality:
  For each of the 15 held-out questions, fetch build_cache_context's top-3 hits
  and measure:
    - top1_similarity, top1_rerank_score
    - top1 answer length, citation count
    - top3 mean similarity (signal: cluster vs single-hit)
    - any-hit rate (does build_cache_context return anything at threshold>=0.6?)

A hand-composed rubric pass over a small sample (5 worst by top1 score) is
written separately to data/research/cache_eval_loop/iter_NNN_shape_b_qualitative.md.

Output: data/research/cache_eval_loop/iter_NNN_shape_b.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from answer_cache import search_cache, _reset_memory_cache_for_tests  # noqa: E402


CITATION_PATTERN = re.compile(r"\[(\d+):(\d+)\]")
HOLDOUT_PATH = REPO_ROOT / "data" / "eval" / "v2" / "_holdout.yaml"


def load_holdout() -> list[dict]:
    with open(HOLDOUT_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def extract_citations(text: str) -> int:
    return len({f"{s}:{v}" for s, v in CITATION_PATTERN.findall(text or "")})


def evaluate(questions: list[dict]) -> dict:
    per_question: list[dict] = []
    for q in questions:
        qid = q["id"]
        bucket = q["bucket"]
        hits = search_cache(q["question"], top_k=3, threshold=0.6)
        if not hits:
            per_question.append(
                {
                    "id": qid,
                    "bucket": bucket,
                    "any_hit": False,
                    "top1_similarity": None,
                    "top1_rerank": None,
                    "top1_question": None,
                    "top1_answer_length": 0,
                    "top1_cite_count": 0,
                    "top3_mean_similarity": None,
                    "top3_questions": [],
                }
            )
            continue
        top = hits[0]
        ans = top.get("answer", "")
        sims = [h.get("similarity", 0.0) for h in hits]
        per_question.append(
            {
                "id": qid,
                "bucket": bucket,
                "any_hit": True,
                "top1_similarity": top.get("similarity"),
                "top1_rerank": top.get("rerank_score"),
                "top1_question": top.get("question"),
                "top1_answer_length": len(ans),
                "top1_cite_count": extract_citations(ans),
                "top3_mean_similarity": round(sum(sims) / len(sims), 3),
                "top3_questions": [h.get("question") for h in hits],
            }
        )

    return _aggregate(per_question)


def _aggregate(per_question: list[dict]) -> dict:
    total = len(per_question)
    any_hit = sum(1 for r in per_question if r["any_hit"])
    avg_top1_sim = (
        sum((r["top1_similarity"] or 0.0) for r in per_question) / total if total else 0
    )
    avg_top1_ans_len = (
        sum(r["top1_answer_length"] for r in per_question) / total if total else 0
    )
    avg_top1_cites = (
        sum(r["top1_cite_count"] for r in per_question) / total if total else 0
    )
    by_bucket: dict[str, dict] = {}
    for r in per_question:
        b = r["bucket"]
        d = by_bucket.setdefault(b, {"total": 0, "any_hit": 0})
        d["total"] += 1
        if r["any_hit"]:
            d["any_hit"] += 1

    # Sort questions by a composite cache-quality score so the iteration loop
    # can target the weakest end. Score = 0.5 * top1_sim + 0.3 * (cite_count/15) + 0.2 * (ans_len/4000)
    def cache_quality_score(r: dict) -> float:
        if not r["any_hit"]:
            return 0.0
        sim = r["top1_similarity"] or 0.0
        cite_norm = min((r["top1_cite_count"] or 0) / 15.0, 1.0)
        ans_norm = min((r["top1_answer_length"] or 0) / 4000.0, 1.0)
        return 0.5 * sim + 0.3 * cite_norm + 0.2 * ans_norm

    for r in per_question:
        r["cache_quality_score"] = round(cache_quality_score(r), 3)

    weakest = sorted(per_question, key=lambda r: r["cache_quality_score"])[:10]

    return {
        "total": total,
        "any_hit": any_hit,
        "any_hit_rate": round(any_hit / total, 4) if total else 0.0,
        "avg_top1_similarity": round(avg_top1_sim, 3),
        "avg_top1_answer_length": round(avg_top1_ans_len, 1),
        "avg_top1_cite_count": round(avg_top1_cites, 2),
        "by_bucket": by_bucket,
        "weakest": weakest,
        "per_question": per_question,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iter", required=True, help="iteration number, e.g. 0")
    ap.add_argument("--cache", default=None, help="optional cache file path override")
    ap.add_argument("--out", default=None, help="optional output path override")
    args = ap.parse_args()

    if args.cache:
        import answer_cache as ac

        ac.CACHE_FILE = Path(args.cache)
        _reset_memory_cache_for_tests()

    qs = load_holdout()
    print(f"[shape_b] loaded {len(qs)} held-out questions")
    print(
        f"[shape_b] cache file: {Path(args.cache).resolve() if args.cache else 'data/answer_cache.json'}"
    )

    result = evaluate(qs)
    print(
        f"[shape_b] any_hit {result['any_hit']}/{result['total']} ({result['any_hit_rate'] * 100:.1f}%)"
    )
    print(
        f"[shape_b] avg_top1_sim={result['avg_top1_similarity']} avg_top1_len={result['avg_top1_answer_length']} avg_top1_cites={result['avg_top1_cite_count']}"
    )
    print("[shape_b] weakest by composite score:")
    for r in result["weakest"][:5]:
        print(
            f"[shape_b]   {r['id']:30s} sim={r['top1_similarity']} cites={r['top1_cite_count']} len={r['top1_answer_length']} quality={r['cache_quality_score']}"
        )

    out_path = (
        Path(args.out)
        if args.out
        else (
            REPO_ROOT
            / "data"
            / "research"
            / "cache_eval_loop"
            / f"iter_{int(args.iter):03d}_shape_b.json"
        )
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[shape_b] wrote {out_path}")


if __name__ == "__main__":
    main()
