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

        # Brief pause between ticks (avoids hammering OpenRouter / Neo4j).
        # User can pass --sleep 0 to disable.
        if i < args.max and args.sleep > 0:
            time.sleep(args.sleep)

    # ── Post-loop reporting ─────────────────────────────────────────────
    print("\n" + "=" * 62)
    s = ralph_loop.status()
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
