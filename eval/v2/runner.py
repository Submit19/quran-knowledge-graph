"""Eval v2 runner: behaviour-asserted, rubric-scored, bootstrap-aggregated.

Replaces `eval_v1.py`'s "did the agent emit citations" existence check
(see `docs/QKG_AUDIT.md` §1). Each question carries hard assertions
(failing any zeroes the score) plus a 4-dimensional LLM-as-judge rubric
(citation_accuracy, answer_completeness, tool_path_correctness,
framing_appropriateness).

Public entry: `run_eval(questions, agent_caller=..., judge_caller=...)`.

The runner is async because the agent stream is async. The judge calls
are synchronous (one HTTP request per dimension, no streaming needed).
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from .agent_caller import TrajectoryResult
from .aggregate import aggregate
from .assertions import AssertionOutcome, check_assertions
from .judge import score_dimension


AgentCaller = Callable[[str], Awaitable[TrajectoryResult]]
JudgeCaller = Callable[..., dict[str, Any]]

RUBRIC_DIMENSIONS = (
    "citation_accuracy",
    "answer_completeness",
    "tool_path_correctness",
    "framing_appropriateness",
)


class RubricWeightsError(ValueError):
    """Raised when a question's rubric_weights don't sum to ~1.0."""


def _validate_weights(question: dict) -> dict[str, float]:
    weights = question.get("rubric_weights") or {}
    missing = [d for d in RUBRIC_DIMENSIONS if d not in weights]
    if missing:
        raise RubricWeightsError(
            f"{question.get('id')}: rubric_weights missing dimensions: {missing}"
        )
    total = sum(float(weights[d]) for d in RUBRIC_DIMENSIONS)
    if not 0.99 <= total <= 1.01:
        raise RubricWeightsError(
            f"{question.get('id')}: rubric_weights sum to {total:.3f}, not 1.0"
        )
    return {d: float(weights[d]) for d in RUBRIC_DIMENSIONS}


def score_rubric(
    *,
    question: dict,
    trajectory: TrajectoryResult,
    judge_caller: JudgeCaller,
    asserts_outcome: AssertionOutcome,
) -> dict[str, dict[str, Any]]:
    """Score each rubric dimension. Returns ``{dim: {score, justification}}``.

    Hard-assert semantics: if any assertion failed, every dimension is
    forced to ``score=0`` regardless of the judge's verdict. Phase 4a
    treats this as the most conservative interpretation; Phase 4d may
    refine to dimension-specific zeroing.
    """
    if not asserts_outcome.all_passed:
        return {
            dim: {
                "score": 0,
                "justification": "zeroed by failed hard assertion: "
                + ", ".join(asserts_outcome.failed),
                "judge_skipped": True,
            }
            for dim in RUBRIC_DIMENSIONS
        }

    scored: dict[str, dict[str, Any]] = {}
    for dim in RUBRIC_DIMENSIONS:
        verdict = judge_caller(
            dimension=dim,
            question=question,
            trajectory=trajectory,
        )
        scored[dim] = verdict
    return scored


def weighted_score(
    rubric: dict[str, dict[str, Any]], weights: dict[str, float]
) -> float:
    """Weighted sum of dimension scores. Returns 0–5."""
    total = 0.0
    for dim, weight in weights.items():
        total += float(rubric[dim]["score"]) * weight
    return round(total, 3)


async def run_eval(
    questions: list[dict],
    *,
    agent_caller: AgentCaller,
    judge_caller: JudgeCaller,
    output_path: Path | None = None,
) -> dict:
    """Run the eval over a question list. Returns aggregated results.

    Args:
        questions: list of question dicts conforming to
            ``data/eval/v2/SCHEMA.md``.
        agent_caller: async callable ``(question_text) -> TrajectoryResult``.
        judge_caller: callable ``(dimension, question, trajectory) ->
            {score, justification}``.
        output_path: optional Path to write the per-question results
            plus aggregated summary as JSON.

    Returns:
        Aggregated dict from ``aggregate()``: ``overall``, ``by_bucket``,
        ``by_dimension``, ``hard_assert_pass_rate``.
    """
    results: list[dict] = []

    for q in questions:
        weights = _validate_weights(q)
        trajectory = await agent_caller(q["question"])
        asserts_outcome = check_assertions(q.get("asserts", {}), trajectory)
        rubric = score_rubric(
            question=q,
            trajectory=trajectory,
            judge_caller=judge_caller,
            asserts_outcome=asserts_outcome,
        )
        results.append(
            {
                "question_id": q["id"],
                "bucket": q["bucket"],
                "trajectory": _trajectory_to_dict(trajectory),
                "asserts": {
                    "passed": list(asserts_outcome.passed),
                    "failed": list(asserts_outcome.failed),
                    "all_passed": asserts_outcome.all_passed,
                },
                "rubric": rubric,
                "weighted_score": weighted_score(rubric, weights),
            }
        )

    aggregated = aggregate(results)

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(
                {"results": results, "aggregated": aggregated},
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    return aggregated


def _trajectory_to_dict(trajectory: TrajectoryResult) -> dict:
    """Serialise a TrajectoryResult for JSON output.

    SSE events are dropped from the output (large + redundant); kept
    only in-process so assertions and judges can read them.
    """
    return {
        "answer_text": trajectory.answer_text,
        "tool_calls": list(trajectory.tool_calls),
        "citations": list(trajectory.citations),
        "elapsed_seconds": trajectory.elapsed_seconds,
        "error": trajectory.error,
        "n_sse_events": len(trajectory.sse_events),
    }
