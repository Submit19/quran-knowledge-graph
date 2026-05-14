"""Tests for eval.v2.judge — 4-dimension prompts + parsing + factory.

Tests cover:
  * DIMENSION_PROMPTS contains all 4 dimensions
  * parse_judge_response handles clean JSON, prose-wrapped JSON, malformed
  * score_dimension calls the client with the right shape (mocked)
  * make_judge_caller produces stub caller when key is missing
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from eval.v2.agent_caller import TrajectoryResult  # noqa: E402
from eval.v2.judge import (  # noqa: E402
    DIMENSION_PROMPTS,
    VALID_DIMENSIONS,
    make_judge_caller,
    parse_judge_response,
    score_dimension,
)


# --- prompt inventory -------------------------------------------------------


def test_dimension_prompts_cover_all_four_dimensions():
    assert set(DIMENSION_PROMPTS.keys()) == set(VALID_DIMENSIONS)
    assert len(VALID_DIMENSIONS) == 4


def test_each_dimension_prompt_is_substantial():
    # ~300+ words minimum — anchors and examples need room.
    for dim, prompt in DIMENSION_PROMPTS.items():
        word_count = len(prompt.split())
        assert word_count >= 200, f"{dim} prompt is too short ({word_count} words)"


def test_each_prompt_contains_calibration_anchors():
    for dim, prompt in DIMENSION_PROMPTS.items():
        assert "Score 0" in prompt
        assert "Score 5" in prompt
        assert "CALIBRATION ANCHORS" in prompt
        assert "Example" in prompt, f"{dim} missing in-context examples"


# --- parse_judge_response --------------------------------------------------


def test_parse_judge_response_clean_json():
    raw = '{"score": 4, "justification": "good citation alignment"}'
    parsed = parse_judge_response(raw)
    assert parsed["score"] == 4
    assert parsed["justification"] == "good citation alignment"


def test_parse_judge_response_prose_wrapped_json():
    raw = 'Here is my verdict: {"score": 2, "justification": "mixed"} — done.'
    parsed = parse_judge_response(raw)
    assert parsed["score"] == 2
    assert parsed["justification"] == "mixed"


def test_parse_judge_response_clamps_score_to_int():
    raw = '{"score": 3.0, "justification": "x"}'
    parsed = parse_judge_response(raw)
    assert parsed["score"] == 3
    assert isinstance(parsed["score"], int)


def test_parse_judge_response_fallback_regex_extracts_digit():
    # Malformed JSON but a single 0–5 digit is present.
    raw = "I would give this a 3 because of the misalignment."
    parsed = parse_judge_response(raw)
    assert parsed["score"] == 3
    assert "regex" in parsed["justification"].lower()


def test_parse_judge_response_unparseable_defaults_to_zero():
    parsed = parse_judge_response("no relevant content here")
    assert parsed["score"] == 0
    assert "defaulted" in parsed["justification"].lower()


# --- score_dimension (mocked client) ---------------------------------------


def _make_fake_client(response_text: str):
    fake_block = MagicMock()
    fake_block.text = response_text
    fake_response = MagicMock()
    fake_response.content = [fake_block]
    client = MagicMock()
    client.messages.create.return_value = fake_response
    return client


def test_score_dimension_calls_client_with_dimension_prompt():
    client = _make_fake_client('{"score": 5, "justification": "spot on"}')
    trajectory = TrajectoryResult(
        answer_text="Verse [2:255] declares ...",
        tool_calls=[{"name": "get_verse", "args_keys": ["verse_id"], "args_str": None}],
        citations=["2:255"],
        sse_events=[],
    )
    result = score_dimension(
        dimension="citation_accuracy",
        question={"question": "What does verse 2:255 say?"},
        trajectory=trajectory,
        client=client,
        model="claude-opus-4-7",
    )
    assert result == {"score": 5, "justification": "spot on"}
    client.messages.create.assert_called_once()
    call_kwargs = client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-opus-4-7"
    user_message = call_kwargs["messages"][0]["content"]
    assert "citation accuracy" in user_message.lower()
    assert "2:255" in user_message
    assert "get_verse" not in user_message  # citation_accuracy doesn't include tools


def test_score_dimension_tool_path_prompt_includes_tool_calls():
    client = _make_fake_client('{"score": 4, "justification": "good path"}')
    trajectory = TrajectoryResult(
        answer_text="",
        tool_calls=[
            {"name": "search_keyword", "args_keys": ["keyword"], "args_str": None},
            {"name": "get_verse", "args_keys": ["verse_id"], "args_str": None},
        ],
        citations=[],
        sse_events=[],
    )
    score_dimension(
        dimension="tool_path_correctness",
        question={"question": "Where is Moses mentioned?"},
        trajectory=trajectory,
        client=client,
    )
    user_message = client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "search_keyword" in user_message
    assert "get_verse" in user_message


def test_score_dimension_rejects_unknown_dimension():
    client = _make_fake_client("{}")
    try:
        score_dimension(
            dimension="bogus",
            question={"question": "q"},
            trajectory=TrajectoryResult(
                answer_text="", tool_calls=[], citations=[], sse_events=[]
            ),
            client=client,
        )
    except ValueError as e:
        assert "bogus" in str(e)
    else:
        raise AssertionError("expected ValueError")


# --- make_judge_caller -----------------------------------------------------


def test_make_judge_caller_returns_stub_when_no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    caller = make_judge_caller(backend="anthropic", model="claude-opus-4-7")
    result = caller(
        dimension="citation_accuracy",
        question={"question": "q"},
        trajectory=TrajectoryResult(
            answer_text="", tool_calls=[], citations=[], sse_events=[]
        ),
    )
    assert result["score"] == 0
    assert result.get("judge_skipped") is True


def test_make_judge_caller_stub_backend_returns_stub_verdict():
    caller = make_judge_caller(backend="stub", model="claude-opus-4-7")
    result = caller(
        dimension="answer_completeness",
        question={"question": "q"},
        trajectory=TrajectoryResult(
            answer_text="x", tool_calls=[], citations=[], sse_events=[]
        ),
    )
    assert result["score"] == 0
    assert result.get("judge_skipped") is True


def test_make_judge_caller_rejects_unknown_backend():
    try:
        make_judge_caller(backend="openai", model="gpt-4")
    except ValueError as e:
        assert "openai" in str(e)
    else:
        raise AssertionError("expected ValueError")
