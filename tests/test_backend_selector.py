"""Backend routing decision, including the Gemini opt-in.

The routing logic that picks (active_backend, active_model) is extracted from
agent_stream into the pure helper _decide_backend so it can be tested without a
Neo4j driver or a live agent loop. Gemini is opt-in only: it never activates
unless config.prefer_gemini is set AND a key is present, and local_only always
forces local Ollama.
"""

import shared_agent
from shared_agent import AgentConfig


def _cfg(**over):
    base = dict(
        backend="ollama",
        default_model="qwen3:8b",
        tools=[],
        system_prompt="sys",
        openrouter_model="qwen/qwen3-coder:free",
        deep_dive_model="qwen3:14b",
        gemini_model="gemini-2.5-flash",
    )
    base.update(over)
    return AgentConfig(**base)


def test_default_is_ollama():
    b, m = shared_agent._decide_backend(_cfg())
    assert (b, m) == ("ollama", "qwen3:8b")


def test_prefer_gemini_routes_to_gemini():
    b, m = shared_agent._decide_backend(_cfg(prefer_gemini=True), gemini_api_key="gk")
    assert (b, m) == ("gemini", "gemini-2.5-flash")


def test_no_gemini_key_falls_back_cleanly():
    # prefer_gemini set but no key → must not route to gemini.
    b, m = shared_agent._decide_backend(_cfg(prefer_gemini=True), gemini_api_key="")
    assert (b, m) == ("ollama", "qwen3:8b")


def test_gemini_precedence_over_openrouter():
    # Both opt-ins set + both keys present → Gemini wins (rewire-test relevant).
    b, m = shared_agent._decide_backend(
        _cfg(prefer_gemini=True, prefer_openrouter=True),
        gemini_api_key="gk",
        openrouter_api_key="ok",
    )
    assert b == "gemini"


def test_local_only_overrides_gemini():
    b, m = shared_agent._decide_backend(
        _cfg(prefer_gemini=True), gemini_api_key="gk", local_only=True
    )
    assert b == "ollama"


def test_deep_dive_does_not_trigger_gemini():
    # deep_dive is an OpenRouter/Ollama concept; with no openrouter key and
    # gemini NOT preferred, it stays on the local deep-dive model.
    b, m = shared_agent._decide_backend(_cfg(), gemini_api_key="gk", deep_dive=True)
    assert (b, m) == ("ollama", "qwen3:14b")


def test_prefer_openrouter_still_works():
    # Regression: the existing OpenRouter path is unchanged when gemini is off.
    b, m = shared_agent._decide_backend(
        _cfg(prefer_openrouter=True), openrouter_api_key="ok"
    )
    assert (b, m) == ("openrouter", "qwen/qwen3-coder:free")


def test_gemini_is_valid_backend_name():
    # An app may set backend='gemini' directly; __post_init__ must accept it.
    cfg = _cfg(backend="gemini")
    assert cfg.backend == "gemini"
