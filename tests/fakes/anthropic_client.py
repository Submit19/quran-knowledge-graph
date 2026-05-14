"""Fake of the anthropic.Anthropic SDK client used by shared_agent's
Anthropic backend path (Phase 3a-3).

This is intentionally separate from ``tests/fakes/llm_client.py``'s
``FakeLLMClient``: the latter targets the OpenAI-ish dict shape that
``shared_agent``'s loop speaks internally, this one targets the SDK
boundary where ``_anthropic_step`` does ``client.messages.create(...)``.
Reusing one fake for both shapes was the 3a-2 lesson — the confusion
isn't worth the LOC saved.

Usage:

    from tests.fakes.anthropic_client import (
        FakeAnthropicClient, fake_message, text_block, tool_use_block,
    )

    client = FakeAnthropicClient([
        # Turn 1: model decides to call get_verse(1:1)
        fake_message(
            stop_reason="tool_use",
            content=[tool_use_block(id="tu_1", name="get_verse",
                                    input={"verse_id": "1:1"})],
        ),
        # Turn 2: model has tool result, replies with text
        fake_message(
            stop_reason="end_turn",
            content=[text_block("In the name of God, Most Gracious, Most Merciful.")],
        ),
    ])

The fake records every messages.create() call in ``client.calls`` so
tests can assert on the kwargs ``shared_agent._anthropic_step`` sent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ── content blocks (duck-typed to the anthropic SDK shape) ─────────────────


@dataclass
class _FakeTextBlock:
    text: str
    type: str = "text"


@dataclass
class _FakeToolUseBlock:
    id: str
    name: str
    input: dict
    type: str = "tool_use"


@dataclass
class _FakeMessage:
    """Mirrors anthropic.types.Message's duck-typed shape used by
    ``_from_anthropic_response``."""

    content: list
    stop_reason: str
    id: str = "msg_fake"
    role: str = "assistant"
    model: str = "fake-haiku"
    usage: Any = None


# ── factory helpers (more readable than direct dataclass calls in tests) ──


def text_block(text: str) -> _FakeTextBlock:
    return _FakeTextBlock(text=text)


def tool_use_block(id: str, name: str, input: dict) -> _FakeToolUseBlock:
    return _FakeToolUseBlock(id=id, name=name, input=input)


def fake_message(content: list, stop_reason: str) -> _FakeMessage:
    return _FakeMessage(content=content, stop_reason=stop_reason)


# ── fake client ────────────────────────────────────────────────────────────


class _FakeMessages:
    """Stand-in for ``anthropic.Anthropic().messages``."""

    def __init__(self, parent: "FakeAnthropicClient"):
        self._parent = parent

    def create(self, **kwargs) -> _FakeMessage:
        self._parent.calls.append(kwargs)
        if not self._parent._queue:
            raise AssertionError(
                f"FakeAnthropicClient ran out of canned responses on call "
                f"#{len(self._parent.calls)}. Provide more responses or end "
                f"the conversation. Last call kwargs keys: {list(kwargs.keys())}"
            )
        return self._parent._queue.pop(0)


class FakeAnthropicClient:
    """SDK shape: ``client.messages.create(...)`` returns a Message.

    Construct with an ordered list of fake messages; each ``messages.create()``
    call consumes the next one. ``client.calls`` records every kwargs dict so
    tests can assert on the model, system, tools, messages payload.
    """

    def __init__(self, responses: list):
        self._queue = list(responses)
        self.calls: list[dict] = []
        self.messages = _FakeMessages(self)

    @property
    def remaining(self) -> int:
        return len(self._queue)
