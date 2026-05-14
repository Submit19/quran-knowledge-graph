"""Tests for eval.v2.runner — end-to-end orchestration with mocked agent + judge.

Covers:
  * Single question produces a question-level result with weighted_score
  * Hard assert failure forces every dimension to 0
  * Bucket aggregation: 3 questions in 2 buckets returns the right per-bucket means
  * Bootstrap CI bounds are deterministic with rng_seed
  * Runner writes JSON output to disk when output_path is provided
  * Rubric weights validation raises on malformed weights
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from eval.v2.agent_caller import TrajectoryResult  # noqa: E402
from eval.v2.aggregate import aggregate  # noqa: E402
from eval.v2.runner import RubricWeightsError, run_eval, weighted_score  # noqa: E402


# --- fakes ------------------------------------------------------------------


def make_fake_agent_caller(traj_by_question: dict[str, TrajectoryResult]):
    """Returns the canned trajectory for the given question text, else default."""

    async def _caller(question: str) -> TrajectoryResult:
        if question in traj_by_question:
            return traj_by_question[question]
        return TrajectoryResult(
            answer_text="",
            tool_calls=[],
            citations=[],
            sse_events=[],
        )

    return _caller


def make_fake_judge(scores_by_question_and_dim: dict):
    """Judge that returns canned (question_id, dimension) -> score."""

    def _caller(*, dimension: str, question: dict, trajectory: TrajectoryResult, **_):
        score = scores_by_question_and_dim.get((question["id"], dimension), 0)
        return {"score": score, "justification": f"fake-{dimension}-{score}"}

    return _caller


def _example_q(
    qid: str, bucket: str, *, question_text: str = "q", asserts: dict | None = None
):
    return {
        "id": qid,
        "bucket": bucket,
        "question": question_text,
        "asserts": asserts or {},
        "rubric_weights": {
            "citation_accuracy": 0.4,
            "answer_completeness": 0.3,
            "tool_path_correctness": 0.2,
            "framing_appropriateness": 0.1,
        },
    }


# --- weighted_score --------------------------------------------------------


def test_weighted_score_simple():
    rubric = {
        "citation_accuracy": {"score": 5, "justification": ""},
        "answer_completeness": {"score": 4, "justification": ""},
        "tool_path_correctness": {"score": 3, "justification": ""},
        "framing_appropriateness": {"score": 2, "justification": ""},
    }
    weights = {
        "citation_accuracy": 0.4,
        "answer_completeness": 0.3,
        "tool_path_correctness": 0.2,
        "framing_appropriateness": 0.1,
    }
    assert weighted_score(rubric, weights) == pytest.approx(
        5 * 0.4 + 4 * 0.3 + 3 * 0.2 + 2 * 0.1
    )


# --- single question end-to-end -------------------------------------------


def test_single_question_passes_asserts_and_records_weighted_score():
    question = _example_q(
        "structured-001",
        "STRUCTURED",
        question_text="What does 2:255 say?",
        asserts={
            "cites_must_include": ["2:255"],
            "tools_used_must_include": ["get_verse"],
        },
    )
    traj = TrajectoryResult(
        answer_text="Verse [2:255] declares ...",
        tool_calls=[{"name": "get_verse", "args_keys": ["verse_id"], "args_str": None}],
        citations=["2:255"],
        sse_events=[],
    )
    agent = make_fake_agent_caller({"What does 2:255 say?": traj})
    judge = make_fake_judge(
        {
            ("structured-001", "citation_accuracy"): 5,
            ("structured-001", "answer_completeness"): 4,
            ("structured-001", "tool_path_correctness"): 5,
            ("structured-001", "framing_appropriateness"): 5,
        }
    )

    aggregated = asyncio.run(
        run_eval([question], agent_caller=agent, judge_caller=judge)
    )

    assert aggregated["hard_assert_pass_rate"] == 1.0
    assert aggregated["overall"]["n"] == 1
    # Weighted: 5*0.4 + 4*0.3 + 5*0.2 + 5*0.1 = 2.0 + 1.2 + 1.0 + 0.5 = 4.7
    assert aggregated["overall"]["mean"] == pytest.approx(4.7)


def test_failed_hard_assert_zeroes_every_dimension():
    question = _example_q(
        "structured-002",
        "STRUCTURED",
        asserts={"cites_must_include": ["2:255"]},
    )
    # Trajectory cites the WRONG verse — hard assert fails.
    traj = TrajectoryResult(
        answer_text="Verse [99:1] declares ...",
        tool_calls=[{"name": "get_verse", "args_keys": ["verse_id"], "args_str": None}],
        citations=["99:1"],
        sse_events=[],
    )
    agent = make_fake_agent_caller({"q": traj})
    # Judge would have given 5s on every dimension — but assert failure pre-empts.
    judge = make_fake_judge(
        {
            ("structured-002", dim): 5
            for dim in [
                "citation_accuracy",
                "answer_completeness",
                "tool_path_correctness",
                "framing_appropriateness",
            ]
        }
    )

    aggregated = asyncio.run(
        run_eval([question], agent_caller=agent, judge_caller=judge)
    )

    assert aggregated["hard_assert_pass_rate"] == 0.0
    assert aggregated["overall"]["mean"] == 0.0
    # by_dimension means should also be zero (all dims forced to 0)
    for dim_name, summary in aggregated["by_dimension"].items():
        assert summary["mean"] == 0.0, f"{dim_name} should be zero"


# --- bucket aggregation ----------------------------------------------------


def test_bucket_aggregation_three_questions_two_buckets():
    q_struct = _example_q("structured-001", "STRUCTURED", question_text="s1")
    q_abstract_a = _example_q("abstract-001", "ABSTRACT", question_text="a1")
    q_abstract_b = _example_q("abstract-002", "ABSTRACT", question_text="a2")

    def _good_traj():
        return TrajectoryResult(
            answer_text="x", tool_calls=[], citations=[], sse_events=[]
        )

    agent = make_fake_agent_caller(
        {"s1": _good_traj(), "a1": _good_traj(), "a2": _good_traj()}
    )
    judge = make_fake_judge(
        {
            # structured-001 → uniform 4
            ("structured-001", "citation_accuracy"): 4,
            ("structured-001", "answer_completeness"): 4,
            ("structured-001", "tool_path_correctness"): 4,
            ("structured-001", "framing_appropriateness"): 4,
            # abstract-001 → uniform 2
            ("abstract-001", "citation_accuracy"): 2,
            ("abstract-001", "answer_completeness"): 2,
            ("abstract-001", "tool_path_correctness"): 2,
            ("abstract-001", "framing_appropriateness"): 2,
            # abstract-002 → uniform 4
            ("abstract-002", "citation_accuracy"): 4,
            ("abstract-002", "answer_completeness"): 4,
            ("abstract-002", "tool_path_correctness"): 4,
            ("abstract-002", "framing_appropriateness"): 4,
        }
    )

    aggregated = asyncio.run(
        run_eval(
            [q_struct, q_abstract_a, q_abstract_b],
            agent_caller=agent,
            judge_caller=judge,
        )
    )

    # STRUCTURED bucket has one q with weighted 4.0.
    assert aggregated["by_bucket"]["STRUCTURED"]["n"] == 1
    assert aggregated["by_bucket"]["STRUCTURED"]["mean"] == pytest.approx(4.0)
    # ABSTRACT bucket has two qs with weighted 2.0 and 4.0; mean = 3.0.
    assert aggregated["by_bucket"]["ABSTRACT"]["n"] == 2
    assert aggregated["by_bucket"]["ABSTRACT"]["mean"] == pytest.approx(3.0)


# --- bootstrap determinism -------------------------------------------------


def test_bootstrap_ci_bounds_deterministic_with_seed():
    results = [
        {
            "weighted_score": 4.0,
            "bucket": "X",
            "rubric": {},
            "asserts": {"all_passed": True},
        },
        {
            "weighted_score": 3.0,
            "bucket": "X",
            "rubric": {},
            "asserts": {"all_passed": True},
        },
        {
            "weighted_score": 5.0,
            "bucket": "X",
            "rubric": {},
            "asserts": {"all_passed": True},
        },
        {
            "weighted_score": 2.0,
            "bucket": "X",
            "rubric": {},
            "asserts": {"all_passed": True},
        },
        {
            "weighted_score": 4.5,
            "bucket": "X",
            "rubric": {},
            "asserts": {"all_passed": True},
        },
    ]
    a = aggregate(results, n_bootstrap=200, rng_seed=42)
    b = aggregate(results, n_bootstrap=200, rng_seed=42)
    assert a["overall"]["ci_lower"] == b["overall"]["ci_lower"]
    assert a["overall"]["ci_upper"] == b["overall"]["ci_upper"]
    assert a["overall"]["mean"] == pytest.approx(
        sum(r["weighted_score"] for r in results) / 5
    )


def test_bootstrap_ci_widens_with_smaller_n():
    # Single question: CI bounds collapse to the mean (every resample
    # is the same value).
    results_single = [
        {
            "weighted_score": 3.5,
            "bucket": "X",
            "rubric": {},
            "asserts": {"all_passed": True},
        }
    ]
    summary = aggregate(results_single, n_bootstrap=50, rng_seed=0)
    assert summary["overall"]["mean"] == 3.5
    assert summary["overall"]["ci_lower"] == 3.5
    assert summary["overall"]["ci_upper"] == 3.5


# --- output JSON -----------------------------------------------------------


def test_runner_writes_output_json(tmp_path: Path):
    q = _example_q("structured-001", "STRUCTURED", question_text="s1")
    traj = TrajectoryResult(answer_text="x", tool_calls=[], citations=[], sse_events=[])
    agent = make_fake_agent_caller({"s1": traj})
    judge = make_fake_judge(
        {
            ("structured-001", dim): 3
            for dim in [
                "citation_accuracy",
                "answer_completeness",
                "tool_path_correctness",
                "framing_appropriateness",
            ]
        }
    )

    out = tmp_path / "run.json"
    asyncio.run(run_eval([q], agent_caller=agent, judge_caller=judge, output_path=out))
    assert out.exists()
    data = json.loads(out.read_text())
    assert "results" in data
    assert "aggregated" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["question_id"] == "structured-001"
    assert data["results"][0]["weighted_score"] == pytest.approx(3.0)


# --- weights validation ----------------------------------------------------


def test_rubric_weights_must_sum_to_one():
    q = _example_q("structured-001", "STRUCTURED")
    q["rubric_weights"]["citation_accuracy"] = 0.9  # now sums > 1.0
    agent = make_fake_agent_caller({})
    judge = make_fake_judge({})
    with pytest.raises(RubricWeightsError):
        asyncio.run(run_eval([q], agent_caller=agent, judge_caller=judge))


def test_rubric_weights_missing_dimension_raises():
    q = _example_q("structured-001", "STRUCTURED")
    del q["rubric_weights"]["framing_appropriateness"]
    agent = make_fake_agent_caller({})
    judge = make_fake_judge({})
    with pytest.raises(RubricWeightsError):
        asyncio.run(run_eval([q], agent_caller=agent, judge_caller=judge))
