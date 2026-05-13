"""
End-to-end agent loop tests using the Self Shunt LLM client.

Drives chat.run_agent_turn with a fake LLM that returns canned tool_use +
text blocks. Asserts that:

  - the right tool was dispatched with the right input
  - the agent loop terminates and returns the final text
  - the conversation was extended correctly with assistant + tool_result blocks
  - the LLM client was called with the expected shape (model, tools, messages)
"""

from __future__ import annotations

import json

import chat
from tests.fakes.llm_client import FakeLLMClient, FakeResponse, text_block, tool_use_block


def test_single_tool_call_returns_final_text(fatiha_session):
    """
    Two-turn agent loop:
      turn 1: model emits tool_use(get_verse, "1:1") → chat dispatches → fixture returns 1:1
      turn 2: model sees tool result, emits text → loop returns the text
    """
    client = FakeLLMClient([
        FakeResponse(
            stop_reason="tool_use",
            content=[tool_use_block(id="tu_1", name="get_verse", input={"verse_id": "1:1"})],
        ),
        FakeResponse(
            stop_reason="end_turn",
            content=[text_block("In the name of God, Most Gracious, Most Merciful.")],
        ),
    ])

    conversation: list = []
    final_text = chat.run_agent_turn(
        user_message="show me 1:1",
        conversation=conversation,
        session=fatiha_session,
        client=client,
    )

    # Final text bubbles up from the second turn
    assert "In the name of God" in final_text

    # The fake was called exactly twice (one tool turn + one final turn)
    assert len(client.calls) == 2, f"expected 2 LLM calls, got {len(client.calls)}"

    # The first call had the user message
    first_call = client.calls[0]
    assert first_call["messages"][0]["role"] == "user"
    assert first_call["messages"][0]["content"] == "show me 1:1"

    # Conversation now contains: user, assistant (tool_use), user (tool_result), assistant (text)
    assert len(conversation) == 4, f"expected 4 conversation entries, got {len(conversation)}"
    assert conversation[0]["role"] == "user"
    assert conversation[1]["role"] == "assistant"  # tool_use turn
    assert conversation[2]["role"] == "user"       # tool_result
    assert conversation[3]["role"] == "assistant"  # final text

    # tool_get_verse was actually called against the fake session
    queries_run = [q for (q, _params) in fatiha_session.calls]
    assert any("Verse {verseId: $id}" in q for q in queries_run), \
        "expected tool_get_verse to issue a Verse lookup query"


def test_zero_tool_calls_returns_text_immediately(empty_session):
    """If the model replies with text on turn 1 (no tool_use), loop returns immediately."""
    client = FakeLLMClient([
        FakeResponse(
            stop_reason="end_turn",
            content=[text_block("I don't need to look anything up to answer that.")],
        ),
    ])

    final_text = chat.run_agent_turn(
        user_message="what is 2+2?",
        conversation=[],
        session=empty_session,
        client=client,
    )

    assert "don't need to look anything up" in final_text
    assert len(client.calls) == 1
    # Empty session was never queried (the model didn't dispatch any tools)
    assert empty_session.calls == []


def test_tool_result_payload_is_json(fatiha_session):
    """
    The tool_result content passed back to the LLM must be a JSON string
    (not a dict). Regression guard for the dispatch_tool contract.
    """
    client = FakeLLMClient([
        FakeResponse(
            stop_reason="tool_use",
            content=[tool_use_block(id="tu_1", name="get_verse", input={"verse_id": "1:1"})],
        ),
        FakeResponse(
            stop_reason="end_turn",
            content=[text_block("done")],
        ),
    ])

    conversation: list = []
    chat.run_agent_turn("show me 1:1", conversation, fatiha_session, client)

    # The tool_result entry is conversation[2] (user role), with a list of blocks.
    tool_result_msg = conversation[2]
    assert tool_result_msg["role"] == "user"
    blocks = tool_result_msg["content"]
    assert len(blocks) == 1
    assert blocks[0]["type"] == "tool_result"
    payload = blocks[0]["content"]
    assert isinstance(payload, str), f"expected str payload, got {type(payload).__name__}"
    parsed = json.loads(payload)
    assert parsed["verse_id"] == "1:1"
    assert parsed["text"].startswith("In the name")
