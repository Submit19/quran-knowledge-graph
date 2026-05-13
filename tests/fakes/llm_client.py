"""
Self-Shunt fake of the anthropic.Anthropic client used by chat.run_agent_turn.

Beck calls this pattern Self Shunt — the test itself implements the
collaborator interface, so the system-under-test can be exercised with
no external API calls.

Usage:

    from tests.fakes.llm_client import FakeLLMClient, text_block, tool_use_block

    client = FakeLLMClient([
        # Turn 1: model decides to call get_verse(1:1)
        FakeResponse(
            stop_reason="tool_use",
            content=[tool_use_block(id="tu_1", name="get_verse", input={"verse_id": "1:1"})],
        ),
        # Turn 2: model has tool result, replies with text
        FakeResponse(
            stop_reason="end_turn",
            content=[text_block("In the name of God, Most Gracious, Most Merciful.")],
        ),
    ])

    # Drive the agent loop:
    final_text = chat.run_agent_turn("show me 1:1", [], session, client)

The fake records every messages.create() call so tests can assert on the
prompt, model, tool list, conversation state — anything chat.py passed in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ── response/block dataclasses (match the anthropic SDK's duck-typed shape) ──

@dataclass
class FakeTextBlock:
    text: str
    type: str = "text"


@dataclass
class FakeToolUseBlock:
    id: str
    name: str
    input: dict
    type: str = "tool_use"


@dataclass
class FakeResponse:
    """Mirrors the anthropic.types.Message shape used by chat.py."""
    stop_reason: str           # "tool_use" | "end_turn" | "max_tokens" | etc.
    content: list              # list of FakeTextBlock | FakeToolUseBlock
    id: str = "msg_fake"
    role: str = "assistant"
    model: str = "fake-model"
    usage: Any = None


# ── factory helpers (more readable than direct dataclass calls in tests) ──

def text_block(text: str) -> FakeTextBlock:
    return FakeTextBlock(text=text)


def tool_use_block(id: str, name: str, input: dict) -> FakeToolUseBlock:
    return FakeToolUseBlock(id=id, name=name, input=input)


# ── fake client ────────────────────────────────────────────────────────────


class FakeMessages:
    """Stand-in for anthropic.Anthropic().messages."""

    def __init__(self, parent: "FakeLLMClient"):
        self._parent = parent

    def create(self, **kwargs) -> FakeResponse:
        self._parent.calls.append(kwargs)
        if not self._parent._queue:
            raise AssertionError(
                f"FakeLLMClient ran out of canned responses on call #{len(self._parent.calls)}. "
                f"Provide more responses or end the conversation. "
                f"Last call args keys: {list(kwargs.keys())}"
            )
        return self._parent._queue.pop(0)


class FakeLLMClient:
    """
    Anthropic SDK shape: client.messages.create(...) returns a Message.

    Construct with an ordered list of FakeResponse objects; each call to
    messages.create() consumes the next one. After construction, every call
    is recorded in `client.calls` so tests can assert on what chat.py passed.
    """

    def __init__(self, responses: list[FakeResponse]):
        self._queue: list[FakeResponse] = list(responses)
        self.calls: list[dict] = []
        self.messages = FakeMessages(self)

    @property
    def remaining(self) -> int:
        return len(self._queue)
