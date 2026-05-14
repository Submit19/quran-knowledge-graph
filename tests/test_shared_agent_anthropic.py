"""Anthropic backend path e2e tests for shared_agent (Phase 3a-3).

Three coverage points:
  1. The translation helpers (``_to_anthropic_messages``,
     ``_to_anthropic_tools``, ``_from_anthropic_response``) round-trip
     correctly between the OpenAI-ish dict shape the loop speaks and the
     Anthropic SDK shape ``_anthropic_step`` speaks.
  2. ``agent_stream`` drives a full single-tool-call-then-answer turn
     through the Anthropic branch (``config.backend="anthropic"``,
     ``collaborators.anthropic_client = FakeAnthropicClient(...)``) with
     no real API key.

The fake SDK lives in ``tests/fakes/anthropic_client.py`` and is
intentionally separate from ``FakeLLMClient`` — the two operate at
different layers of the system (3a-2 lesson).
"""

from __future__ import annotations

import asyncio
import json

import shared_agent
from tests.fakes.anthropic_client import (
    FakeAnthropicClient,
    fake_message,
    text_block,
    tool_use_block,
)
from tests.fakes.neo4j_session import FakeNeo4jSession, graph_with_fatiha_opening


# ── 1. Pure translation helpers ─────────────────────────────────────────────


def test_anthropic_message_translation_roundtrip():
    """All four message shapes survive the OpenAI-ish → Anthropic conversion."""
    msgs = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "What is verse 1:1?"},
        {"role": "assistant", "content": "Looking it up."},
        {
            "role": "assistant",
            "content": "calling tool",
            "tool_calls": [
                {
                    "id": "tu_1",
                    "type": "function",
                    "function": {
                        "name": "get_verse",
                        "arguments": json.dumps({"verse_id": "1:1"}),
                    },
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "tu_1",
            "name": "get_verse",
            "content": '{"verse_id":"1:1","text":"..."}',
        },
    ]

    out = shared_agent._to_anthropic_messages(msgs)

    # System message stripped (Anthropic takes `system` separately).
    assert all(m["role"] != "system" for m in out), (
        f"system role should be stripped; got {[m['role'] for m in out]!r}"
    )

    # Plain user / assistant messages pass through.
    assert out[0] == {"role": "user", "content": "What is verse 1:1?"}
    assert out[1] == {"role": "assistant", "content": "Looking it up."}

    # Assistant tool-call → blocks: text + tool_use.
    assistant_with_tools = out[2]
    assert assistant_with_tools["role"] == "assistant"
    blocks = assistant_with_tools["content"]
    assert any(b["type"] == "text" and b["text"] == "calling tool" for b in blocks)
    tool_use_blocks = [b for b in blocks if b["type"] == "tool_use"]
    assert len(tool_use_blocks) == 1
    assert tool_use_blocks[0]["id"] == "tu_1"
    assert tool_use_blocks[0]["name"] == "get_verse"
    assert tool_use_blocks[0]["input"] == {"verse_id": "1:1"}

    # Tool result → user message with tool_result block.
    tool_result = out[3]
    assert tool_result["role"] == "user"
    assert tool_result["content"][0]["type"] == "tool_result"
    assert tool_result["content"][0]["tool_use_id"] == "tu_1"
    assert tool_result["content"][0]["content"] == '{"verse_id":"1:1","text":"..."}'


def test_anthropic_tools_translation_flattens_openai_shape():
    """OpenAI-style nested tool schemas become flat Anthropic shape."""
    openai_tools = [
        {
            "type": "function",
            "function": {
                "name": "get_verse",
                "description": "Get a verse by id.",
                "parameters": {
                    "type": "object",
                    "properties": {"verse_id": {"type": "string"}},
                    "required": ["verse_id"],
                },
            },
        }
    ]
    already_anthropic = [
        {
            "name": "ping",
            "description": "ping the server",
            "input_schema": {"type": "object", "properties": {}},
        }
    ]

    out_openai = shared_agent._to_anthropic_tools(openai_tools)
    assert out_openai == [
        {
            "name": "get_verse",
            "description": "Get a verse by id.",
            "input_schema": {
                "type": "object",
                "properties": {"verse_id": {"type": "string"}},
                "required": ["verse_id"],
            },
        }
    ]

    # Tools already in Anthropic shape pass through untouched.
    out_native = shared_agent._to_anthropic_tools(already_anthropic)
    assert out_native == already_anthropic


def test_anthropic_response_translation():
    """A mixed text + tool_use Message → OpenAI-ish dict."""
    resp = fake_message(
        content=[
            text_block("Here is the verse."),
            tool_use_block(id="tu_42", name="get_verse", input={"verse_id": "1:1"}),
            text_block(" Citing it now."),
        ],
        stop_reason="tool_use",
    )

    out = shared_agent._from_anthropic_response(resp)

    assert out["stop_reason"] == "tool_use"
    msg = out["message"]
    assert msg["role"] == "assistant"
    # Multiple text blocks are concatenated.
    assert msg["content"] == "Here is the verse. Citing it now."
    # Tool-use becomes a single tool_call with JSON-stringified arguments.
    assert len(msg["tool_calls"]) == 1
    tc = msg["tool_calls"][0]
    assert tc["id"] == "tu_42"
    assert tc["type"] == "function"
    assert tc["function"]["name"] == "get_verse"
    assert tc["function"]["arguments"] == '{"verse_id": "1:1"}'


# ── 2. Full agent_stream loop through the Anthropic branch ──────────────────


class _FakeNeo4jDriver:
    """Single-session driver shaped like neo4j.Driver."""

    def __init__(self, session):
        self._session = session

    def session(self, **_kw):
        return self._session


def _drain(gen) -> list[dict]:
    """Collect SSE event payloads from the async generator."""
    events: list[dict] = []

    async def run():
        async for raw in gen:
            assert raw.startswith("data: "), f"non-SSE frame: {raw!r}"
            body = raw[len("data: ") :].rstrip()
            if body:
                events.append(json.loads(body))

    asyncio.run(run())
    return events


def test_anthropic_single_tool_then_answer():
    """Drive agent_stream with config.backend='anthropic' end-to-end.

    Two SDK calls:
      1. tool_use(get_verse, "1:1")
      2. text("...verse 1:1...")

    Asserts the Model badge SSE fires, the tool dispatches against the fake
    Neo4j fixture, and a done frame closes the stream cleanly.
    """
    fake_client = FakeAnthropicClient(
        [
            fake_message(
                content=[
                    tool_use_block(
                        id="tu_1", name="get_verse", input={"verse_id": "1:1"}
                    )
                ],
                stop_reason="tool_use",
            ),
            fake_message(
                content=[
                    text_block(
                        "Verse [1:1]: In the name of God, Most Gracious, Most Merciful."
                    )
                ],
                stop_reason="end_turn",
            ),
        ]
    )

    config = shared_agent.AgentConfig(
        backend="anthropic",
        default_model="claude-haiku-4-5",
        tools=[],  # _anthropic_step translates the empty list trivially
        system_prompt="test system prompt",
        max_tool_turns=3,
        max_tokens=256,
        enable_priming_graph_update=False,
        enable_reasoning_memory_playbook=False,
        enable_query_classification=False,
        enable_tool_result_compression=False,
        enable_citation_density_retry=False,
        enable_citation_verifier=False,
        enable_answer_cache_lookup=False,
        enable_answer_cache_save=False,
    )
    session = FakeNeo4jSession(graph_with_fatiha_opening())
    collaborators = shared_agent.AgentCollaborators(
        driver=_FakeNeo4jDriver(session),
        reasoning_memory=None,
        db_name="test",
        openrouter_api_key="",
        anthropic_client=fake_client,
    )

    events = _drain(
        shared_agent.agent_stream("What does verse 1:1 say?", [], config, collaborators)
    )

    types = [e.get("t") for e in events]
    # Model badge always fires first.
    assert events[0]["t"] == "tool" and events[0]["name"] == "Model"
    assert events[0]["summary"] == "claude-haiku-4-5"

    # Tool dispatch surfaced as a UI event (TOOL_LABELS rename).
    tool_events = [
        e for e in events if e.get("t") == "tool" and e.get("name") != "Model"
    ]
    assert any(e["name"] == "Looking up verse" for e in tool_events), (
        f"expected 'Looking up verse' tool frame; got {[e['name'] for e in tool_events]!r}"
    )

    # Text frame from the second SDK call.
    text_events = [e for e in events if e.get("t") == "text"]
    full_text = "".join(e["d"] for e in text_events)
    assert "In the name of God" in full_text

    # Loop closes cleanly.
    assert "done" in types, f"missing 'done' event in {types!r}"
    assert "error" not in types

    # The fake recorded two calls; the first had no prior assistant turn,
    # the second saw the tool_result + assistant tool_use turn.
    assert len(fake_client.calls) == 2
    first_call = fake_client.calls[0]
    # _anthropic_step strips the system message and passes it as the system kwarg.
    assert first_call["system"] == "test system prompt"
    # System role does NOT appear in the Anthropic messages payload.
    assert all(m.get("role") != "system" for m in first_call["messages"]), (
        f"system role leaked into Anthropic messages payload: {first_call['messages']!r}"
    )
