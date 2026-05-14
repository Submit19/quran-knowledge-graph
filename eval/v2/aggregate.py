"""Aggregator for eval v2 — per-bucket + overall + per-dimension means
with 95% bootstrap confidence intervals.

The audit (`docs/QKG_AUDIT.md` §1) called out that the existing QRCD
numbers were reported with no CIs, so a 0.028 → 0.139 lift looked
decisive without disclosing that the underlying n=22 could easily
move that much from sampling noise. v2 closes that gap by reporting
CIs on every aggregated number.

Bootstrap: resample question-level ``weighted_score`` values with
replacement N times, take the 2.5 and 97.5 percentiles. Default
N=1000 — enough for stable CI bounds without slowing the eval down.

Uses numpy when available (it ships with sentence-transformers, so
it's already a transitive dep), falls back to ``random.choices`` for
test environments where numpy isn't installed.
"""

from __future__ import annotations

import random
from typing import Any


try:
    import numpy as _np

    _HAS_NUMPY = True
except ImportError:
    _np = None  # type: ignore[assignment]
    _HAS_NUMPY = False


def _bootstrap_ci(
    values: list[float], *, n_bootstrap: int, rng_seed: int | None = None
) -> tuple[float, float, float]:
    """Return (mean, ci_lower, ci_upper) at 95% from a bootstrap resample.

    For an empty input, returns ``(0.0, 0.0, 0.0)``.

    Args:
        values: per-question scalar scores.
        n_bootstrap: number of resamples.
        rng_seed: optional seed for deterministic bounds (used in tests).
    """
    if not values:
        return 0.0, 0.0, 0.0

    if _HAS_NUMPY:
        rng = _np.random.default_rng(rng_seed)
        arr = _np.asarray(values, dtype=float)
        idx = rng.integers(0, len(arr), size=(n_bootstrap, len(arr)))
        sample_means = arr[idx].mean(axis=1)
        sample_means.sort()
        lower = float(_np.percentile(sample_means, 2.5))
        upper = float(_np.percentile(sample_means, 97.5))
        return float(arr.mean()), lower, upper

    # Pure-Python fallback. Slower but identical contract.
    rng = random.Random(rng_seed)
    means: list[float] = []
    n = len(values)
    for _ in range(n_bootstrap):
        sample = [rng.choice(values) for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lower_idx = int(0.025 * n_bootstrap)
    upper_idx = max(int(0.975 * n_bootstrap) - 1, lower_idx)
    return (
        sum(values) / n,
        means[lower_idx],
        means[upper_idx],
    )


def _summarise(values: list[float], *, n_bootstrap: int, rng_seed: int | None) -> dict:
    mean, lo, hi = _bootstrap_ci(values, n_bootstrap=n_bootstrap, rng_seed=rng_seed)
    return {
        "mean": round(mean, 3),
        "ci_lower": round(lo, 3),
        "ci_upper": round(hi, 3),
        "n": len(values),
    }


def aggregate(
    results: list[dict],
    *,
    n_bootstrap: int = 1000,
    rng_seed: int | None = None,
) -> dict[str, Any]:
    """Aggregate per-question results into bucket / overall / dimension summaries.

    Args:
        results: list of question-level result dicts produced by
            ``runner.run_eval``. Each must contain ``weighted_score``,
            ``bucket``, ``rubric``, and ``asserts``.
        n_bootstrap: number of bootstrap resamples (default 1000).
        rng_seed: optional seed for deterministic CI bounds — useful in
            tests; leave None for real runs.

    Returns:
        Dict shaped::

          {
            "overall": {"mean": ..., "ci_lower": ..., "ci_upper": ..., "n": ...},
            "by_bucket": {
              "STRUCTURED": {...}, "ABSTRACT": {...}, ...
            },
            "by_dimension": {
              "citation_accuracy": {...}, ...
            },
            "hard_assert_pass_rate": float,
          }
    """
    all_scores = [float(r["weighted_score"]) for r in results]
    overall = _summarise(all_scores, n_bootstrap=n_bootstrap, rng_seed=rng_seed)

    bucket_to_scores: dict[str, list[float]] = {}
    for r in results:
        bucket_to_scores.setdefault(r["bucket"], []).append(float(r["weighted_score"]))
    by_bucket = {
        bucket: _summarise(scores, n_bootstrap=n_bootstrap, rng_seed=rng_seed)
        for bucket, scores in sorted(bucket_to_scores.items())
    }

    dimension_to_scores: dict[str, list[float]] = {}
    for r in results:
        for dim, verdict in (r.get("rubric") or {}).items():
            dimension_to_scores.setdefault(dim, []).append(float(verdict.get("score", 0)))
    by_dimension = {
        dim: _summarise(scores, n_bootstrap=n_bootstrap, rng_seed=rng_seed)
        for dim, scores in sorted(dimension_to_scores.items())
    }

    hard_assert_pass_rate = (
        sum(1 for r in results if r["asserts"]["all_passed"]) / len(results)
        if results
        else 0.0
    )

    return {
        "overall": overall,
        "by_bucket": by_bucket,
        "by_dimension": by_dimension,
        "hard_assert_pass_rate": round(hard_assert_pass_rate, 3),
    }
