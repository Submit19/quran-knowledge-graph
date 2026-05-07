"""
ralph_tick.py — single-tick CLI for the Ralph loop.

Usage:
    python ralph_tick.py                    # run one tick (auto-pick task)
    python ralph_tick.py --task <id>        # force a specific task
    python ralph_tick.py --dry              # preview what would run
    python ralph_tick.py --status           # print loop state
    python ralph_tick.py --types eval,cypher_analysis  # restrict task types

Wake-up integration: schedule a recurring tick by calling this from
your Claude Code wake-up prompt with --task <id> for deterministic
cycles, or with no args for greedy "highest priority unblocked".
"""

import argparse
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import ralph_loop


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", help="Force a specific task id")
    ap.add_argument("--dry", action="store_true", help="Preview, don't execute")
    ap.add_argument("--status", action="store_true", help="Print loop state and exit")
    ap.add_argument("--types", help="Comma-separated allowed task types "
                                     "(default: skip manual + external_run)")
    args = ap.parse_args()

    if args.status:
        s = ralph_loop.status()
        print(json.dumps(s, indent=2, ensure_ascii=False))
        return

    allow_types = None
    if args.types:
        allow_types = set(t.strip() for t in args.types.split(","))

    result = ralph_loop.tick(
        force_task_id=args.task,
        dry_run=args.dry,
        allow_types=allow_types,
    )
    if result is None:
        sys.exit(0)
    if result.status in ("failed", "regression"):
        sys.exit(2)


if __name__ == "__main__":
    main()
