"""
ralph_run.py — loop wrapper around ralph_tick.

Snarktank/ralph (Geoffrey Huntley pattern, Ryan Carson's implementation)
loops until <promise>COMPLETE</promise> or max iterations. Our equivalent
loops `ralph_loop.tick()` until:
  - the project is complete (project_completion criteria met), or
  - the picker returns no eligible task (everything done / blocked / quarantined), or
  - max iterations reached.

Usage:
  python ralph_run.py                        # auto-loop, default 10 iterations
  python ralph_run.py --max 20               # up to 20 iterations
  python ralph_run.py --types eval,cypher_analysis,cleanup  # restrict types
  python ralph_run.py --sleep 30             # sleep 30s between ticks (default 5)
  python ralph_run.py --git-commit           # auto-commit+push after every tick
  python ralph_run.py --dry                  # preview each iteration's pick

Exit codes:
  0  project complete OR queue exhausted (graceful)
  1  hit max iterations without completion
  2  fatal error (Neo4j unreachable, etc.)
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import ralph_loop


def git_commit_push(tick_n: int):
    """Commit any tick artefacts + state, push to origin.

    Note: subprocess does NOT shell-expand globs. We expand them here with
    Path.glob so artefact files are actually staged (the previous version
    was passing literal "data/ralph_analysis_*.md" to git add and silently
    no-op'ing).
    """
    root = ralph_loop.ROOT
    try:
        explicit_paths = [
            "ralph_state.json", "ralph_log.md", "ralph_backlog.yaml",
            "data/eval_v1_results.json", "data/eval_v1_results.md",
        ]
        glob_patterns = [
            "data/ralph_analysis_*.md",
            "data/ralph_agent_*.md",
            "data/eval_*.json",
        ]
        files_to_add = [p for p in explicit_paths if (root / p).exists()]
        for pat in glob_patterns:
            files_to_add.extend(str(p.relative_to(root)) for p in root.glob(pat))
        if not files_to_add:
            return False
        subprocess.run(["git", "add", *files_to_add],
                       cwd=str(root), capture_output=True)
        proc = subprocess.run(
            ["git", "commit", "-m", f"ralph tick {tick_n}", "--allow-empty"],
            cwd=str(root), capture_output=True, text=True,
        )
        if proc.returncode == 0:
            subprocess.run(["git", "push"], cwd=str(root),
                           capture_output=True, timeout=60)
            return True
    except Exception as e:
        print(f"  [run] git commit/push failed: {e}")
    return False


def _usage_window_24h(state: dict) -> dict:
    """Sum the 24h rolling window of API usage from state."""
    win = (state.get("api_usage") or {}).get("window") or []
    return {
        "calls": sum(int(r[1]) for r in win),
        "tokens_in": sum(int(r[2]) for r in win),
        "tokens_out": sum(int(r[3]) for r in win),
        "n_window": len(win),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=10,
                    help="Max iterations (default 10, snarktank-style cap)")
    ap.add_argument("--sleep", type=int, default=5,
                    help="Seconds between ticks (default 5)")
    ap.add_argument("--types", help="Comma-separated allowed task types")
    ap.add_argument("--dry", action="store_true",
                    help="Print what each iteration would do, don't execute")
    ap.add_argument("--git-commit", action="store_true",
                    help="Auto-commit and push after every tick")
    # ── token / rate-limit pacing ────────────────────────────────────────
    # OpenRouter free tier: 20 req/min, 50 req/day (no credits) or
    # 1000 req/day with $10+ credits. Defaults below are conservative —
    # set --max-calls-per-day 950 if you have credits, --max-calls-per-day 45
    # if you don't. The pacer:
    #   1. enforces a minimum gap between API-calling ticks (default 4s -> ≤15/min)
    #   2. stops the loop early if the 24h call window crosses --max-calls-per-day
    ap.add_argument("--max-calls-per-day", type=int, default=0,
                    help="Stop loop when 24h API-call window hits this. 0=disabled.")
    ap.add_argument("--max-tokens-per-day", type=int, default=0,
                    help="Stop loop when 24h tokens (in+out) hit this. 0=disabled.")
    ap.add_argument("--min-api-gap-sec", type=float, default=4.0,
                    help="Minimum seconds between ticks that hit the API "
                         "(rate-limit safety; default 4 -> ≤15 req/min).")
    args = ap.parse_args()

    allow_types = None
    if args.types:
        allow_types = set(t.strip() for t in args.types.split(","))

    print("==============================================================")
    print(f"  Ralph Run — max iterations: {args.max} · types: {args.types or 'all'}")
    print("==============================================================")

    completed_at = None
    queue_empty_at = None

    for i in range(1, args.max + 1):
        print(f"\n=== iteration {i} of {args.max} ===")

        # Check project completion BEFORE picking — if everything's already
        # done, we should exit immediately (the snarktank "<promise>COMPLETE"
        # signal).
        done, checks = ralph_loop.is_project_complete()
        if done:
            print("[run] PROJECT COMPLETE — all criteria met:")
            for c in checks:
                print(f"  ✓ {c['check']}: {c['detail']}")
            completed_at = i
            break

        result = ralph_loop.tick(dry_run=args.dry, allow_types=allow_types)
        if result is None:
            # No eligible task — queue empty (or all blocked).
            print("[run] No eligible task — queue exhausted.")
            queue_empty_at = i
            break

        if args.git_commit and not args.dry:
            git_commit_push(i)

        # ── Pacing: enforce daily caps + minimum API gap ────────────────
        # We pull state fresh because tick() just persisted it.
        if not args.dry:
            cur_state = ralph_loop.load_state()
            usage_24h = _usage_window_24h(cur_state)
            print(f"  [run] 24h usage: {usage_24h['calls']} calls · "
                  f"{usage_24h['tokens_in']}+{usage_24h['tokens_out']} tokens "
                  f"({usage_24h['n_window']} entries)")
            if args.max_calls_per_day and usage_24h["calls"] >= args.max_calls_per_day:
                print(f"[run] HALT — 24h call budget reached "
                      f"({usage_24h['calls']} ≥ {args.max_calls_per_day}). "
                      f"Loop will resume on next wake-up.")
                sys.exit(0)
            if args.max_tokens_per_day:
                tot_tok = usage_24h["tokens_in"] + usage_24h["tokens_out"]
                if tot_tok >= args.max_tokens_per_day:
                    print(f"[run] HALT — 24h token budget reached "
                          f"({tot_tok} ≥ {args.max_tokens_per_day}).")
                    sys.exit(0)

        # Brief pause between ticks (avoids hammering OpenRouter / Neo4j).
        # If the tick made an API call, ensure we wait at least
        # --min-api-gap-sec to stay under per-minute rate limits. Otherwise
        # the regular --sleep applies.
        if i < args.max:
            base_sleep = args.sleep if args.sleep > 0 else 0
            api_gap = args.min_api_gap_sec if (result and result.api_calls) else 0
            wait = max(base_sleep, api_gap)
            if wait > 0:
                time.sleep(wait)

    # ── Post-loop reporting ─────────────────────────────────────────────
    print("\n" + "=" * 62)
    s = ralph_loop.status()
    final_state = ralph_loop.load_state()
    api = final_state.get("api_usage") or {}
    if api:
        u24 = _usage_window_24h(final_state)
        print(f"[run] API usage — 24h: {u24['calls']} calls, "
              f"{u24['tokens_in']}+{u24['tokens_out']} tokens · "
              f"all-time: {api.get('calls_total', 0)} calls, "
              f"{api.get('tokens_in_total', 0)}+{api.get('tokens_out_total', 0)} tokens")
    if completed_at:
        print(f"[run] PROJECT COMPLETE at iteration {completed_at}")
        sys.exit(0)
    if queue_empty_at:
        print(f"[run] queue exhausted at iteration {queue_empty_at}")
        # Still check project completion — maybe we're done even if some
        # tasks remain (e.g. they're skipped/quarantined and ignored)
        done, checks = ralph_loop.is_project_complete()
        if done:
            print(f"[run] project completion criteria ALSO met")
            sys.exit(0)
        print(f"[run] but project NOT complete — outstanding criteria:")
        for c in checks:
            mark = "✓" if c["passed"] else "✗"
            print(f"  {mark} {c['check']}: {c['detail']}")
        sys.exit(1)

    print(f"[run] hit max iterations ({args.max}) without completion")
    print(f"  done={s['done']}  skipped={s['skipped']}  "
          f"quarantined={s['quarantined']}  pending={s['pending']}")
    sys.exit(1)


if __name__ == "__main__":
    main()
