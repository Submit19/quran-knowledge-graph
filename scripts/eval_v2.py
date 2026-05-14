"""CLI entry for eval v2.

Run the v2 eval against a question YAML file. Drives the agent
end-to-end against real Neo4j, scores each answer via the 4-dim
LLM-as-judge, aggregates with bootstrap CIs.

This is the operator-facing surface. Pytest never calls it; the CI
workflow (informational, Phase 4a) does.

Usage:
  python scripts/eval_v2.py \\
      --questions data/eval/v2/examples.yaml \\
      --app app_free \\
      --output data/eval/v2/runs/local.json

  # Skip the judge (no ANTHROPIC_API_KEY available): scores will be 0.
  python scripts/eval_v2.py --questions ... --judge-model none --output ...
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from eval.v2.agent_caller import make_app_agent_caller  # noqa: E402
from eval.v2.judge import make_judge_caller  # noqa: E402
from eval.v2.runner import run_eval  # noqa: E402


def _load_questions(path: Path) -> list[dict]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{path}: expected a YAML list of questions, got {type(raw)}")
    return raw


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--questions",
        type=Path,
        required=True,
        help="Path to a YAML question file (e.g. data/eval/v2/examples.yaml).",
    )
    parser.add_argument(
        "--app",
        default="app_free",
        help="App module to drive. Must expose _agent_stream(message, history).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Where to write per-question results + aggregated summary as JSON.",
    )
    parser.add_argument(
        "--judge-model",
        default=os.environ.get("EVAL_V2_JUDGE_MODEL", "claude-opus-4-7"),
        help="Judge LLM model id. Pass 'none' to skip judging (every score → 0).",
    )
    parser.add_argument(
        "--judge-backend",
        default=os.environ.get("EVAL_V2_JUDGE_BACKEND", "anthropic"),
        choices=("anthropic", "stub"),
        help="Backend for the judge. 'stub' is for smoke tests; 'anthropic' is real.",
    )
    args = parser.parse_args()

    if not args.questions.exists():
        print(f"[eval_v2] questions file not found: {args.questions}", file=sys.stderr)
        return 2

    questions = _load_questions(args.questions)
    print(f"[eval_v2] loaded {len(questions)} questions from {args.questions}")

    agent_caller = make_app_agent_caller(args.app)
    judge_caller = make_judge_caller(
        backend=args.judge_backend,
        model=args.judge_model,
    )

    output_path = args.output
    if output_path is None:
        ts = time.strftime("%Y%m%dT%H%M%S")
        output_path = ROOT / "data" / "eval" / "v2" / "runs" / f"run_{ts}.json"

    started = time.monotonic()
    aggregated = asyncio.run(
        run_eval(
            questions,
            agent_caller=agent_caller,
            judge_caller=judge_caller,
            output_path=output_path,
        )
    )
    elapsed = time.monotonic() - started

    print(f"[eval_v2] wrote {output_path}")
    print(f"[eval_v2] elapsed: {elapsed:.1f}s")
    print("[eval_v2] aggregated summary:")
    print(json.dumps(aggregated, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
