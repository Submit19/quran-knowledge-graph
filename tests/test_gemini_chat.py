"""_gemini_chat + Gemini message/response translation.

HTTP is mocked (monkeypatch shared_agent.requests.post) so these run offline
and deterministically. _gemini_chat must return the same normalised
``{"message": {role, content, tool_calls}}`` shape the rest of the agent loop
consumes, with tool-call ``arguments`` as a JSON string (matching the
OpenRouter/Anthropic backends).
"""

import json

import pytest
import requests

import shared_agent

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class FakeResp:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)


def _text_response(text):
    return {
        "candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": "STOP"}]
    }


def _toolcall_response(name, args):
    return {
        "candidates": [
            {
                "content": {"parts": [{"functionCall": {"name": name, "args": args}}]},
                "finishReason": "STOP",
            }
        ]
    }


# ── _to_gemini_contents ───────────────────────────────────────────────────


def test_to_gemini_contents_multi_turn():
    msgs = [
        {"role": "system", "content": "You are an assistant."},
        {"role": "user", "content": "What is verse 2:255?"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "c1",
                    "type": "function",
                    "function": {
                        "name": "get_verse",
                        "arguments": '{"verse_id": "2:255"}',
                    },
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "c1",
            "name": "get_verse",
            "content": '{"verse_id": "2:255", "text": "God: there is no god but He."}',
        },
    ]
    contents = shared_agent._to_gemini_contents(msgs)
    # System message is stripped (it goes in systemInstruction).
    assert all(c["role"] in ("user", "model") for c in contents)
    assert contents[0] == {"role": "user", "parts": [{"text": "What is verse 2:255?"}]}
    # Assistant tool call → model/functionCall with args parsed back to a dict.
    model_turn = contents[1]
    assert model_turn["role"] == "model"
    fc = model_turn["parts"][-1]["functionCall"]
    assert fc["name"] == "get_verse"
    assert fc["args"] == {"verse_id": "2:255"}
    # Tool result → user/functionResponse with an object response.
    fr_turn = contents[2]
    assert fr_turn["role"] == "user"
    fr = fr_turn["parts"][0]["functionResponse"]
    assert fr["name"] == "get_verse"
    assert isinstance(fr["response"], dict)
    assert fr["response"]["text"].startswith("God")


# ── _gemini_chat: basic + tool call ───────────────────────────────────────


def test_simple_chat_no_tools(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["json"] = kwargs.get("json")
        captured["headers"] = kwargs.get("headers")
        return FakeResp(200, _text_response("Peace. [2:255]"))

    monkeypatch.setattr(shared_agent.requests, "post", fake_post)
    out = shared_agent._gemini_chat(
        api_key="k",
        url=GEMINI_BASE,
        model="gemini-2.5-flash",
        system="sys prompt",
        messages=[{"role": "user", "content": "hi"}],
    )
    assert out["message"]["content"] == "Peace. [2:255]"
    assert out["message"]["tool_calls"] == []
    # Endpoint + key header + systemInstruction wired correctly.
    assert captured["url"].endswith("/gemini-2.5-flash:generateContent")
    assert captured["headers"]["x-goog-api-key"] == "k"
    assert captured["json"]["systemInstruction"]["parts"][0]["text"] == "sys prompt"


def test_chat_with_tool_call(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured["json"] = kwargs.get("json")
        return FakeResp(200, _toolcall_response("get_verse", {"verse_id": "2:255"}))

    monkeypatch.setattr(shared_agent.requests, "post", fake_post)
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_verse",
                "description": "get a verse",
                "parameters": {
                    "type": "object",
                    "properties": {"verse_id": {"type": "string"}},
                    "required": ["verse_id"],
                },
            },
        }
    ]
    out = shared_agent._gemini_chat(
        api_key="k",
        url=GEMINI_BASE,
        model="gemini-2.5-flash",
        system="sys",
        messages=[{"role": "user", "content": "verse 2:255"}],
        tools=tools,
    )
    tcs = out["message"]["tool_calls"]
    assert len(tcs) == 1
    assert tcs[0]["function"]["name"] == "get_verse"
    # arguments must be a JSON string (loop re-parses it like OpenRouter).
    assert isinstance(tcs[0]["function"]["arguments"], str)
    assert json.loads(tcs[0]["function"]["arguments"]) == {"verse_id": "2:255"}
    assert tcs[0].get("id")  # an id is always present (synthesised if absent)
    # Tools were translated into the Gemini functionDeclarations envelope.
    assert "functionDeclarations" in captured["json"]["tools"][0]


def test_multi_turn_tool_loop(monkeypatch):
    """tool call → tool result → final answer, driven through _gemini_chat twice."""
    responses = [
        _toolcall_response("get_verse", {"verse_id": "2:255"}),
        _text_response("The Throne verse. [2:255]"),
    ]

    def fake_post(url, **kwargs):
        return FakeResp(200, responses.pop(0))

    monkeypatch.setattr(shared_agent.requests, "post", fake_post)

    msgs = [{"role": "user", "content": "verse 2:255"}]
    first = shared_agent._gemini_chat(
        api_key="k",
        url=GEMINI_BASE,
        model="gemini-2.5-flash",
        system="s",
        messages=msgs,
    )
    assert first["message"]["tool_calls"][0]["function"]["name"] == "get_verse"
    # Append the model turn + a tool result, then re-call.
    msgs.append(first["message"])
    msgs.append(
        {
            "role": "tool",
            "tool_call_id": first["message"]["tool_calls"][0]["id"],
            "name": "get_verse",
            "content": '{"text": "the Throne verse"}',
        }
    )
    second = shared_agent._gemini_chat(
        api_key="k",
        url=GEMINI_BASE,
        model="gemini-2.5-flash",
        system="s",
        messages=msgs,
    )
    assert second["message"]["content"] == "The Throne verse. [2:255]"
    assert second["message"]["tool_calls"] == []


def test_handles_rate_limit(monkeypatch):
    """429 twice then 200 → _gemini_chat retries with backoff and succeeds."""
    calls = {"n": 0}

    def fake_post(url, **kwargs):
        calls["n"] += 1
        if calls["n"] < 3:
            return FakeResp(429, {"error": {"message": "rate limited"}})
        return FakeResp(200, _text_response("done"))

    monkeypatch.setattr(shared_agent.requests, "post", fake_post)
    monkeypatch.setattr(shared_agent.time, "sleep", lambda *a, **k: None)
    out = shared_agent._gemini_chat(
        api_key="k",
        url=GEMINI_BASE,
        model="gemini-2.5-flash",
        system="s",
        messages=[{"role": "user", "content": "hi"}],
        max_retries=3,
    )
    assert calls["n"] == 3
    assert out["message"]["content"] == "done"


def test_rate_limit_exhausted_raises(monkeypatch):
    """Persistent 429 past max_retries propagates (so the fallback chain fires)."""

    def fake_post(url, **kwargs):
        return FakeResp(429, {"error": {"message": "rate limited"}})

    monkeypatch.setattr(shared_agent.requests, "post", fake_post)
    monkeypatch.setattr(shared_agent.time, "sleep", lambda *a, **k: None)
    with pytest.raises(requests.HTTPError):
        shared_agent._gemini_chat(
            api_key="k",
            url=GEMINI_BASE,
            model="gemini-2.5-flash",
            system="s",
            messages=[{"role": "user", "content": "hi"}],
            max_retries=2,
        )


def test_non_transient_error_raises_immediately(monkeypatch):
    """A 400 does not retry — it raises on the first call."""
    calls = {"n": 0}

    def fake_post(url, **kwargs):
        calls["n"] += 1
        return FakeResp(400, {"error": {"message": "bad request"}})

    monkeypatch.setattr(shared_agent.requests, "post", fake_post)
    monkeypatch.setattr(shared_agent.time, "sleep", lambda *a, **k: None)
    with pytest.raises(requests.HTTPError):
        shared_agent._gemini_chat(
            api_key="k",
            url=GEMINI_BASE,
            model="gemini-2.5-flash",
            system="s",
            messages=[{"role": "user", "content": "hi"}],
            max_retries=3,
        )
    assert calls["n"] == 1  # no retry on a non-transient error


def test_safety_blocked_translates_to_error(monkeypatch):
    """A SAFETY-blocked candidate with no parts becomes a clean RuntimeError."""
    blocked = {"candidates": [{"content": {"parts": []}, "finishReason": "SAFETY"}]}

    def fake_post(url, **kwargs):
        return FakeResp(200, blocked)

    monkeypatch.setattr(shared_agent.requests, "post", fake_post)
    with pytest.raises(RuntimeError, match="(?i)gemini.*block|safety"):
        shared_agent._gemini_chat(
            api_key="k",
            url=GEMINI_BASE,
            model="gemini-2.5-flash",
            system="s",
            messages=[{"role": "user", "content": "hi"}],
        )
