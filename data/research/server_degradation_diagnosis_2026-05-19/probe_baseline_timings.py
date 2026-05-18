"""Replay-analyzer for the 2026-05-17 baseline run_log.jsonl.

Reads ``captures/baseline_run_log.jsonl`` and prints structured evidence of
server degradation over the 50-question sequential run: rolling-median elapsed
times, failure phases, and per-question outcome buckets.

Pure-Python, no network or Neo4j. Safe to re-run any time.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = HERE / "captures" / "baseline_run_log.jsonl"


def _rolling_median(vals: list[float], window: int) -> list[float | None]:
    out: list[float | None] = []
    for i in range(len(vals)):
        lo = max(0, i - window + 1)
        chunk = [v for v in vals[lo : i + 1] if v is not None]
        out.append(statistics.median(chunk) if chunk else None)
    return out


def main() -> None:
    rows = [json.loads(l) for l in LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(rows) == 50, len(rows)

    elapsed = [r["elapsed_sec"] for r in rows]
    status = [r["status"] for r in rows]

    # Phase 1 = Q1-Q23 (pre-degradation), Phase 2 = Q24-Q50.
    p1_ok = [e for e, s in zip(elapsed[:23], status[:23]) if s == "ok"]
    p2_ok = [e for e, s in zip(elapsed[23:], status[23:]) if s == "ok"]
    p1_fail = [s for s in status[:23] if s != "ok"]
    p2_fail = [s for s in status[23:] if s != "ok"]

    print("=" * 72)
    print("Phase comparison")
    print("=" * 72)
    print(f"  Phase 1 (Q1-Q23):  ok={len(p1_ok):2d}  fail={len(p1_fail):2d}  "
          f"median={statistics.median(p1_ok):.1f}s  max={max(p1_ok):.1f}s")
    print(f"  Phase 2 (Q24-Q50): ok={len(p2_ok):2d}  fail={len(p2_fail):2d}  "
          f"median={statistics.median(p2_ok):.1f}s  max={max(p2_ok):.1f}s")

    print()
    print("=" * 72)
    print("Rolling median (window=5) — does elapsed grow over the run?")
    print("=" * 72)
    rm = _rolling_median(elapsed, 5)
    for i, (e, s, m) in enumerate(zip(elapsed, status, rm), start=1):
        marker = "  " if s == "ok" else ("** " if s == "error" else "?? ")
        print(f"  {marker}Q{i:2d}  status={s:8s}  elapsed={e:6.1f}s  rolling_med5={m:6.1f}s")

    print()
    print("=" * 72)
    print("Failure clustering (status != ok)")
    print("=" * 72)
    streak = 0
    failures: list[tuple[int, str, float]] = []
    for i, (s, e) in enumerate(zip(status, elapsed), start=1):
        if s != "ok":
            failures.append((i, s, e))
            streak += 1
        else:
            streak = 0
    print(f"  Total failures: {len(failures)}")
    print(f"  First failure: Q{failures[0][0]}" if failures else "")
    print(f"  Last failure: Q{failures[-1][0]}" if failures else "")
    # Longest consecutive run of failures.
    longest = cur = 0
    for s in status:
        if s != "ok":
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0
    print(f"  Longest consecutive-failure streak: {longest}")

    print()
    print("=" * 72)
    print("Elapsed distribution for 'error' status (no SSE bytes for 300s)")
    print("=" * 72)
    err_elapsed = [e for s, e in zip(status, elapsed) if s == "error"]
    print(f"  count={len(err_elapsed)}  "
          f"min={min(err_elapsed):.1f}s  "
          f"median={statistics.median(err_elapsed):.1f}s  "
          f"max={max(err_elapsed):.1f}s")
    print("  (Runner read-timeout = 300s; an 'error' verdict means the server")
    print("   stopped emitting SSE frames for >=300s straight.)")

    print()
    print("=" * 72)
    print("Elapsed distribution for 'timeout' status (received some bytes, total >300s)")
    print("=" * 72)
    to_elapsed = [e for s, e in zip(status, elapsed) if s == "timeout"]
    print(f"  count={len(to_elapsed)}  "
          f"min={min(to_elapsed):.1f}s  "
          f"median={statistics.median(to_elapsed):.1f}s  "
          f"max={max(to_elapsed):.1f}s")


if __name__ == "__main__":
    main()
