"""
Regression: agent_stream must poll stop_event at mid-turn checkpoints, not
only at the top of each turn.

The Phase-3b "Bug D" fix added a stop_event poll at the TOP of each turn
in shared_agent.agent_stream's run() loop. That fix is necessary but not
sufficient: a single agent turn can spend 60-120s blocked in the LLM
syscall (qwen3:14b on a thematic question) and another several seconds
inside a Neo4j-backed tool dispatch. If the consumer disconnects during
those blocking windows, the top-of-turn poll only catches it on the NEXT
turn — by which point we've already done one wasted LLM call + N wasted
tool dispatches.

The 2026-05-19 server-degradation diagnosis ruled IN the resulting
daemon-thread leak as an amplifier of the cascade (see
data/research/server_degradation_diagnosis_2026-05-19/DIAGNOSIS.md).

This file pins two additional poll locations:

  1. After _call_backend() returns — closes the longest blocking
     syscall in the loop (the LLM call).
  2. Inside the tool_calls for-loop, before each dispatch — closes
     the secondary blocking window (Neo4j-backed tool dispatch).

Pure structural test: greps shared_agent.py for the expected poll lines.
This guards against accidental removal during refactors. The existing
behavioural test for the stop_event mechanism itself lives at
tests/regression/test_sse_worker_leak.py and is unchanged.
"""

from __future__ import annotations

import re
from pathlib import Path


SHARED_AGENT = Path(__file__).resolve().parent.parent.parent / "shared_agent.py"


def _read_run_loop_body() -> str:
    """Return the body of the inner ``run(q, stop_event)`` function.

    We slice from the ``def run(`` line to the matching ``return`` /
    function end so the assertions only look at the worker body and
    don't false-match on prose in the module docstring.
    """
    text = SHARED_AGENT.read_text(encoding="utf-8")
    assert "def run(q, stop_event):" in text, (
        "shared_agent.py no longer defines the inner run(q, stop_event) "
        "worker — the stop_event polling pattern has been refactored. "
        "Update this test to match the new shape."
    )
    start = text.index("def run(q, stop_event):")
    # The run body ends at the next top-level statement after the
    # nested function. Cheap heuristic: cut at the first occurrence of
    # the well-known sse_pump wrapper call.
    end = text.index("pump_worker_into_sse", start)
    return text[start:end]


def test_top_of_turn_stop_poll_present():
    """Phase-3b Bug D's poll lives at the top of each turn. Must remain."""
    body = _read_run_loop_body()
    # Find the while-turn loop header, then the stop_event poll on the
    # very next non-blank line(s).
    assert re.search(
        r"while turn < config\.max_tool_turns:\s*\n\s*if stop_event\.is_set\(\):",
        body,
    ), (
        "Top-of-turn stop_event poll is missing. This is Phase-3b Bug D's "
        "guarantee — the worker must check stop_event before starting a new "
        "turn so a disconnected consumer doesn't trigger another LLM call."
    )


def test_post_llm_stop_poll_present():
    """New checkpoint: stop_event must be polled after _call_backend returns."""
    body = _read_run_loop_body()
    # _call_backend assigns to `resp`. The post-LLM poll should appear
    # between the resp assignment / fallback dance and the
    # ``msg = resp.get(...)`` line that begins response parsing.
    match = re.search(
        r"resp = _call_backend\([^)]*\)"  # the call itself, or the fallback raise
        r".*?"  # any try/except/fallback handling
        r"if stop_event\.is_set\(\):\s*\n\s*return"
        r".*?"
        r"msg = resp\.get\(",
        body,
        flags=re.DOTALL,
    )
    assert match, (
        "Post-LLM stop_event poll is missing. After _call_backend() returns, "
        "but before parsing the response or dispatching any tools, the worker "
        "must check stop_event. Without this, a consumer disconnect during a "
        "long LLM call (qwen3:14b can spend 60-120s here) leaves the worker "
        "running through one more wasted dispatch cycle before noticing on "
        "the next top-of-turn poll."
    )


def test_per_tool_stop_poll_present():
    """New checkpoint: stop_event must be polled before each tool dispatch."""
    body = _read_run_loop_body()
    # Inside the `for tc in tool_calls:` loop, before any tool-call work,
    # there must be a stop_event check.
    match = re.search(
        r"for tc in tool_calls:\s*\n"
        r"(?:\s*#[^\n]*\n)*"  # optional comment lines
        r"\s*if stop_event\.is_set\(\):\s*\n\s*return",
        body,
    )
    assert match, (
        "Per-tool stop_event poll is missing. Inside the tool_calls for-loop, "
        "before each dispatch_tool() call, the worker must check stop_event. "
        "Without this, a consumer disconnect mid-turn would still let the "
        "remaining parallel tool calls in the same turn run to completion."
    )


def test_stop_polls_appear_before_their_blocking_callees():
    """Sanity: each poll must precede the blocking call it guards.

    Catches accidental reorderings that would make the polls useless
    (e.g., putting the post-LLM poll AFTER dispatch_tool rather than
    before it).
    """
    body = _read_run_loop_body()

    # Order of expected occurrences in the run body, top-to-bottom:
    #   1. while-turn header
    #   2. top-of-turn poll
    #   3. resp = _call_backend(...)
    #   4. post-LLM poll
    #   5. msg = resp.get(...)
    #   6. for tc in tool_calls:
    #   7. per-tool poll
    #   8. dispatch_tool(...)
    expected_in_order = [
        ("while-turn header", r"while turn < config\.max_tool_turns:"),
        (
            "top-of-turn poll",
            r"if stop_event\.is_set\(\):\s*\n\s*return  # consumer disconnect",
        ),
        ("_call_backend call", r"resp = _call_backend\("),
        ("post-LLM poll", r"# Mid-turn stop-poll: the LLM call"),
        ("response parsing", r"msg = resp\.get\(\"message\", \{\}\)"),
        ("tool_calls loop", r"for tc in tool_calls:"),
        ("per-tool poll", r"# Per-tool stop-poll: a tool dispatch"),
        ("dispatch_tool call", r"dispatch_tool\("),
    ]

    last_pos = -1
    for label, pattern in expected_in_order:
        m = re.search(pattern, body)
        assert m is not None, f"could not find: {label} (pattern {pattern!r})"
        assert m.start() > last_pos, (
            f"{label} appears out of order — pattern matched at offset "
            f"{m.start()} but previous landmark was at {last_pos}. "
            f"A stop-poll has been moved past the blocking call it should "
            f"guard, which silently defeats its purpose."
        )
        last_pos = m.start()
