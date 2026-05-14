"""Tests for eval.v2.assertions — hard-assertion checker.

Every assertion type gets a pass case and a fail case. Empty asserts
dict is the no-op case (all_passed=True with no entries).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from eval.v2.agent_caller import TrajectoryResult  # noqa: E402
from eval.v2.assertions import check_assertions  # noqa: E402


def _trajectory(
    *,
    citations: list[str] | None = None,
    tool_names: list[str] | None = None,
    answer_text: str = "",
) -> TrajectoryResult:
    return TrajectoryResult(
        answer_text=answer_text,
        tool_calls=[
            {"name": n, "args_keys": None, "args_str": None} for n in (tool_names or [])
        ],
        citations=citations or [],
        sse_events=[],
    )


# --- cites_must_include -----------------------------------------------------


def test_cites_must_include_passes_when_all_present():
    outcome = check_assertions(
        {"cites_must_include": ["2:255", "3:1"]},
        _trajectory(citations=["2:255", "3:1", "7:1"]),
    )
    assert outcome.all_passed
    assert "cites_must_include:2:255" in outcome.passed
    assert "cites_must_include:3:1" in outcome.passed


def test_cites_must_include_fails_when_any_missing():
    outcome = check_assertions(
        {"cites_must_include": ["2:255", "3:1"]},
        _trajectory(citations=["2:255"]),
    )
    assert not outcome.all_passed
    assert "cites_must_include:3:1" in outcome.failed
    assert "cites_must_include:2:255" in outcome.passed


# --- cites_must_not_include -------------------------------------------------


def test_cites_must_not_include_passes_when_none_present():
    outcome = check_assertions(
        {"cites_must_not_include": ["9:128", "9:129"]},
        _trajectory(citations=["2:255"]),
    )
    assert outcome.all_passed


def test_cites_must_not_include_fails_when_forbidden_present():
    outcome = check_assertions(
        {"cites_must_not_include": ["9:128"]},
        _trajectory(citations=["9:128"]),
    )
    assert not outcome.all_passed
    assert "cites_must_not_include:9:128" in outcome.failed


# --- tools_used_must_include ------------------------------------------------


def test_tools_used_must_include_passes_when_called():
    outcome = check_assertions(
        {"tools_used_must_include": ["get_verse"]},
        _trajectory(tool_names=["get_verse"]),
    )
    assert outcome.all_passed


def test_tools_used_must_include_fails_when_not_called():
    outcome = check_assertions(
        {"tools_used_must_include": ["get_verse"]},
        _trajectory(tool_names=["semantic_search"]),
    )
    assert not outcome.all_passed
    assert "tools_used_must_include:get_verse" in outcome.failed


# --- tools_used_must_not_include --------------------------------------------


def test_tools_used_must_not_include_passes_when_absent():
    outcome = check_assertions(
        {"tools_used_must_not_include": ["run_cypher"]},
        _trajectory(tool_names=["get_verse", "semantic_search"]),
    )
    assert outcome.all_passed


def test_tools_used_must_not_include_fails_when_called():
    outcome = check_assertions(
        {"tools_used_must_not_include": ["run_cypher"]},
        _trajectory(tool_names=["run_cypher"]),
    )
    assert not outcome.all_passed
    assert "tools_used_must_not_include:run_cypher" in outcome.failed


# --- answer_substring_required ----------------------------------------------


def test_answer_substring_required_case_insensitive_pass():
    outcome = check_assertions(
        {"answer_substring_required": ["Moses"]},
        _trajectory(answer_text="moses appears 136 times in the Quran"),
    )
    assert outcome.all_passed


def test_answer_substring_required_fails_when_missing():
    outcome = check_assertions(
        {"answer_substring_required": ["Moses"]},
        _trajectory(answer_text="The Quran has 6234 verses."),
    )
    assert not outcome.all_passed


# --- answer_substring_forbidden ---------------------------------------------


def test_answer_substring_forbidden_passes_when_absent():
    outcome = check_assertions(
        {"answer_substring_forbidden": ["hadith"]},
        _trajectory(answer_text="The Quran directly says..."),
    )
    assert outcome.all_passed


def test_answer_substring_forbidden_fails_when_present():
    outcome = check_assertions(
        {"answer_substring_forbidden": ["hadith"]},
        _trajectory(answer_text="As reported in hadith, ..."),
    )
    assert not outcome.all_passed


# --- empty / unknown handling ----------------------------------------------


def test_empty_asserts_dict_all_passed_true():
    outcome = check_assertions({}, _trajectory(citations=[]))
    assert outcome.all_passed
    assert outcome.passed == []
    assert outcome.failed == []


def test_none_asserts_arg_does_not_crash():
    outcome = check_assertions(None, _trajectory(citations=[]))  # type: ignore[arg-type]
    assert outcome.all_passed


def test_unknown_assertion_keys_are_ignored_for_forward_compat():
    outcome = check_assertions(
        {"future_assert_type": ["something"], "cites_must_include": ["2:255"]},
        _trajectory(citations=["2:255"]),
    )
    assert outcome.all_passed


# --- multiple failures aggregated ------------------------------------------


def test_multiple_failures_all_reported():
    outcome = check_assertions(
        {
            "cites_must_include": ["2:255"],
            "tools_used_must_include": ["get_verse"],
            "answer_substring_required": ["Throne"],
        },
        _trajectory(citations=[], tool_names=[], answer_text=""),
    )
    assert not outcome.all_passed
    assert len(outcome.failed) == 3
