"""End-to-end tests for shared_agent.agent_stream (Phase 3a-2 step 5).

These tests drive ``agent_stream`` with a canned LLM response sequence and a
FakeNeo4jSession-backed driver — no real OpenRouter, no real Ollama, no real
Neo4j. They cover the per-request and config-knob paths added in 3a-2:
required_tool_classes (the discipline nudge), max_tool_turns (loop cap), and
the happy-path tool-call → text → done sequence.

The fake LLM matches the normalised dict shape ``_call_backend`` returns:
``{"message": {"role": "assistant", "content": str, "tool_calls": list}}``.
We monkey-patch ``shared_agent._ollama_chat`` rather than going through the
HTTP client.
"""

from __future__ import annotations

import asyncio
import json


import shared_agent
from tests.fakes.neo4j_session import FakeNeo4jSession, graph_with_fatiha_opening


# ── canned-response helpers ─────────────────────────────────────────────────


def _resp_tool_call(
    tool_name: str, tool_args: dict, tool_call_id: str = "tc_1"
) -> dict:
    """Normalised response with a single tool_call. Arguments JSON-encoded."""
    return {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": tool_call_id,
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": json.dumps(tool_args),
                    },
                }
            ],
        }
    }


def _resp_text(text: str) -> dict:
    """Normalised response with just text — ends the agent loop."""
    return {"message": {"role": "assistant", "content": text, "tool_calls": []}}


class _ScriptedLLM:
    """Returns the next canned response on each call; tracks calls for asserts."""

    def __init__(self, responses):
        self.queue = list(responses)
        self.calls = []

    def __call__(self, **kwargs):  # noqa: D401 — callable to mimic the HTTP helper
        self.calls.append(kwargs)
        if not self.queue:
            raise AssertionError(
                "ScriptedLLM ran out of canned responses on call "
                f"#{len(self.calls)}; messages-len={len(kwargs.get('messages', []))}"
            )
        return self.queue.pop(0)


# ── collaborator / driver fakes ─────────────────────────────────────────────


class _FakeNeo4jDriver:
    """Wraps a single FakeNeo4jSession in a Driver-shaped interface.

    ``shared_agent.agent_stream`` does ``with driver.session(database=name) as s:``
    so the returned object needs a context-manager protocol; FakeNeo4jSession
    already provides ``__enter__`` / ``__exit__``.
    """

    def __init__(self, session: FakeNeo4jSession):
        self._session = session

    def session(self, **_kw):
        return self._session


def _make_collaborators_with_fatiha() -> shared_agent.AgentCollaborators:
    session = FakeNeo4jSession(graph_with_fatiha_opening())
    return shared_agent.AgentCollaborators(
        driver=_FakeNeo4jDriver(session),
        reasoning_memory=None,  # agent_stream's try/except handles None
        db_name="test",
        openrouter_api_key="",
    )


def _make_minimal_test_config(**overrides) -> shared_agent.AgentConfig:
    """A config with every external-state knob OFF.

    Keeps tests deterministic: no answer_cache lookup, no priming, no
    reasoning-memory playbook, no classify_query, no compression, no
    citation-density retry. Each test opts back in to what it asserts on.
    """
    base = dict(
        backend="ollama",
        default_model="test-model",
        tools=[],
        system_prompt="test prompt",
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
    base.update(overrides)
    return shared_agent.AgentConfig(**base)


def _drain(gen) -> list[dict]:
    """Run the async generator and collect parsed event payloads."""
    events: list[dict] = []

    async def run():
        async for raw in gen:
            assert raw.startswith("data: "), f"non-SSE frame: {raw!r}"
            body = raw[len("data: ") :].rstrip()
            if body:
                events.append(json.loads(body))

    asyncio.run(run())
    return events


# ── tests ───────────────────────────────────────────────────────────────────


def test_agent_stream_single_tool_call_then_answer(monkeypatch):
    """Happy path: one tool call → text response → done."""
    llm = _ScriptedLLM(
        [
            _resp_tool_call("get_verse", {"verse_id": "1:1"}),
            _resp_text(
                "Verse 1:1 reads: In the name of God, Most Gracious, Most Merciful."
            ),
        ]
    )
    monkeypatch.setattr(shared_agent, "_ollama_chat", llm)

    config = _make_minimal_test_config()
    collaborators = _make_collaborators_with_fatiha()

    events = _drain(
        shared_agent.agent_stream("What does verse 1:1 say?", [], config, collaborators)
    )

    types = [e.get("t") for e in events]
    assert types[0] == "tool"  # Model badge
    assert events[0]["name"] == "Model"

    # The dispatched tool fires a "Looking up verse" UI event (TOOL_LABELS).
    tool_events = [
        e for e in events if e.get("t") == "tool" and e.get("name") != "Model"
    ]
    assert any(e["name"] == "Looking up verse" for e in tool_events), (
        f"expected a 'Looking up verse' tool event; got {[e['name'] for e in tool_events]!r}"
    )

    # Text frame from the second turn.
    text_events = [e for e in events if e.get("t") == "text"]
    assert text_events, "agent_stream did not emit any text frame"
    full_text = "".join(e["d"] for e in text_events)
    assert "In the name of God" in full_text

    # done is the final event and reports no error.
    assert "done" in types, f"missing 'done' event in {types!r}"
    assert "error" not in types
    assert llm.calls, "LLM was never called"


def test_agent_stream_respects_max_tool_turns(monkeypatch):
    """Cap: if the model keeps requesting tools, the loop stops at max_tool_turns."""
    # Three turns, all tool_use. agent_stream should stop after the 3rd, never
    # making a 4th LLM call.
    llm = _ScriptedLLM(
        [
            _resp_tool_call("get_verse", {"verse_id": "1:1"}, tool_call_id="tc_a"),
            _resp_tool_call("get_verse", {"verse_id": "1:1"}, tool_call_id="tc_b"),
            _resp_tool_call("get_verse", {"verse_id": "1:1"}, tool_call_id="tc_c"),
        ]
    )
    monkeypatch.setattr(shared_agent, "_ollama_chat", llm)

    config = _make_minimal_test_config(max_tool_turns=3)
    collaborators = _make_collaborators_with_fatiha()

    events = _drain(
        shared_agent.agent_stream("tell me about mercy", [], config, collaborators)
    )

    types = [e.get("t") for e in events]
    assert "done" in types, f"missing 'done' event in {types!r}"
    assert "error" not in types
    assert len(llm.calls) == 3, (
        f"expected exactly max_tool_turns=3 LLM calls, got {len(llm.calls)}"
    )


def _resp_parallel_tool_calls(calls: list[tuple[str, dict]]) -> dict:
    """Normalised response with N parallel tool_calls in one assistant turn."""
    return {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": f"tc_{i}",
                    "type": "function",
                    "function": {"name": name, "arguments": json.dumps(args)},
                }
                for i, (name, args) in enumerate(calls)
            ],
        }
    }


def test_agent_stream_discipline_nudge_fires_when_class_unmet(monkeypatch):
    """If the model tries to answer without exercising a required tool class,
    agent_stream pushes a nudge user-message and re-prompts."""
    # Turn 1: text only -> discipline gate fires (total_tool_calls == 0 < 2).
    # Turn 2: TWO parallel tool_calls in one response -> total_tool_calls = 2,
    #         class "verse retrieval" satisfied by get_verse.
    # Turn 3: text -> loop exits cleanly.
    llm = _ScriptedLLM(
        [
            _resp_text("Answering directly without retrieval."),
            _resp_parallel_tool_calls(
                [
                    ("get_verse", {"verse_id": "1:1"}),
                    ("get_verse", {"verse_id": "1:1"}),
                ]
            ),
            _resp_text("Verse-grounded answer."),
        ]
    )
    monkeypatch.setattr(shared_agent, "_ollama_chat", llm)

    # required_tool_classes maps a class name to its satisfying tools. We use
    # the actual get_verse tool so dispatch_tool can run end-to-end on the
    # fatiha fixture.
    config = _make_minimal_test_config(
        max_tool_turns=5,
        required_tool_classes={"verse retrieval": ["get_verse"]},
    )
    # _is_simple_lookup must be False — message > 4 words AND no "verse N:N".
    message = "tell me everything you know about mercy and forgiveness"
    collaborators = _make_collaborators_with_fatiha()

    events = _drain(shared_agent.agent_stream(message, [], config, collaborators))

    types = [e.get("t") for e in events]
    assert "done" in types
    assert "error" not in types
    # Verify the LLM was called at least twice — once for the text-only turn,
    # at least once more after the nudge.
    assert len(llm.calls) >= 2, (
        f"expected the nudge to trigger a re-prompt; LLM call count = {len(llm.calls)}"
    )
    # Inspect the second call's messages to confirm the nudge user-message
    # was injected after the first text-only response.
    nudge_call = llm.calls[1]
    nudge_msgs = nudge_call.get("messages", [])
    last_user_msg = next(
        (m for m in reversed(nudge_msgs) if m.get("role") == "user"),
        None,
    )
    assert last_user_msg is not None
    assert "MUST call one of" in last_user_msg["content"], (
        f"expected nudge phrase in last user-message, got {last_user_msg['content']!r}"
    )
    assert "verse retrieval" in last_user_msg["content"]
