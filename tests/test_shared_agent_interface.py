"""Interface contract for shared_agent (Phase 3a step 2).

These tests pin the public surface — what callers depend on — before any
implementation lands. They run on the stub (step 2) and must continue to
pass after the code move from app_free.py (step 3).
"""

from __future__ import annotations

import asyncio
import inspect

import pytest

import shared_agent


# ── AgentConfig construction ────────────────────────────────────────────────


def _make_minimal_config(**overrides):
    base = dict(
        backend="anthropic",
        default_model="claude-sonnet-4-5",
        tools=[],
        system_prompt="You are a helpful assistant.",
    )
    base.update(overrides)
    return shared_agent.AgentConfig(**base)


@pytest.mark.parametrize("backend", ["anthropic", "ollama", "openrouter"])
def test_agent_config_accepts_each_valid_backend(backend):
    cfg = _make_minimal_config(backend=backend)
    assert cfg.backend == backend


def test_agent_config_rejects_unknown_backend():
    with pytest.raises(ValueError, match="backend must be one of"):
        _make_minimal_config(backend="gpt-4-via-curl")


def test_agent_config_rejects_zero_max_tool_turns():
    with pytest.raises(ValueError, match="max_tool_turns"):
        _make_minimal_config(max_tool_turns=0)


def test_agent_config_rejects_non_list_tools():
    with pytest.raises(TypeError, match="tools"):
        _make_minimal_config(tools="not-a-list")


def test_agent_config_is_frozen():
    cfg = _make_minimal_config()
    with pytest.raises((AttributeError, Exception)):  # FrozenInstanceError
        cfg.backend = "ollama"  # type: ignore[misc]


def test_agent_config_required_tool_classes_defaults_empty():
    """Discipline is opt-in. The default is no policy = no nudge."""
    cfg = _make_minimal_config()
    assert cfg.required_tool_classes == {}


def test_agent_config_fallback_chain_defaults_empty():
    """No fallback by default — Anthropic apps inherit this when they port."""
    cfg = _make_minimal_config()
    assert cfg.fallback_chain == ()


def test_agent_config_accepts_single_fallback_entry():
    """app_free's preserved behaviour: one entry, ollama deep-dive."""
    fb = shared_agent.FallbackBackend(backend="ollama", model="qwen3:14b")
    cfg = _make_minimal_config(fallback_chain=(fb,))
    assert len(cfg.fallback_chain) == 1
    assert cfg.fallback_chain[0].backend == "ollama"
    assert cfg.fallback_chain[0].model == "qwen3:14b"


def test_agent_config_accepts_multi_step_fallback_chain():
    """Multi-step chain: try backend A, then B, then C; raise after C."""
    chain = (
        shared_agent.FallbackBackend(
            backend="openrouter", model="qwen/qwen3-coder:free"
        ),
        shared_agent.FallbackBackend(backend="ollama", model="qwen3:14b"),
        shared_agent.FallbackBackend(backend="ollama", model="qwen3:8b"),
    )
    cfg = _make_minimal_config(fallback_chain=chain)
    assert len(cfg.fallback_chain) == 3
    assert [fb.model for fb in cfg.fallback_chain] == [
        "qwen/qwen3-coder:free",
        "qwen3:14b",
        "qwen3:8b",
    ]


def test_fallback_backend_is_frozen():
    """FallbackBackend is a frozen dataclass — chains are hashable/immutable."""
    fb = shared_agent.FallbackBackend(backend="ollama", model="x")
    with pytest.raises((AttributeError, Exception)):
        fb.model = "y"  # type: ignore[misc]


def test_agent_config_accepts_required_tool_classes_dict():
    """Two-class policy mirroring app_free's preserved behaviour."""
    cfg = _make_minimal_config(
        required_tool_classes={
            "keyword retrieval": ["search_keyword", "traverse_topic"],
            "semantic retrieval": ["semantic_search"],
        }
    )
    assert set(cfg.required_tool_classes) == {"keyword retrieval", "semantic retrieval"}
    assert cfg.required_tool_classes["semantic retrieval"] == ["semantic_search"]


def test_agent_config_default_flags_are_conservative():
    """Most feature flags default off — wrappers opt-in per the variant table."""
    cfg = _make_minimal_config()
    assert cfg.enable_citation_density_retry is False
    assert cfg.enable_uncertainty_probe is False
    assert cfg.enable_priming_graph_update is False
    assert cfg.enable_reasoning_memory_playbook is False
    assert cfg.enable_query_classification is False
    assert cfg.enable_tool_result_compression is False
    assert cfg.enable_citation_verifier is False
    # The two cache flags default ON — every app today uses the answer cache.
    assert cfg.enable_answer_cache_lookup is True
    assert cfg.enable_answer_cache_save is True


# ── agent_stream surface ────────────────────────────────────────────────────


def test_agent_stream_is_async_generator_function():
    """Per the SSE contract, agent_stream must be an async generator."""
    assert inspect.isasyncgenfunction(shared_agent.agent_stream)


def test_agent_stream_signature_accepts_per_request_overrides():
    sig = inspect.signature(shared_agent.agent_stream)
    params = set(sig.parameters)
    assert {"message", "history", "config", "collaborators"}.issubset(params)
    # Per-request overrides the free app currently passes through.
    assert {"deep_dive", "full_coverage", "model_override", "local_only"}.issubset(
        params
    )


def _make_minimal_collaborators(**overrides):
    """A lightweight stand-in suitable for surface tests; no real Neo4j."""

    class _MockDriver:
        def session(self, **_kw):  # not actually opened in surface tests
            raise NotImplementedError("MockDriver.session — surface test only")

    base = dict(
        driver=_MockDriver(),
        reasoning_memory=None,
        db_name="test",
        openrouter_api_key="",
    )
    base.update(overrides)
    return shared_agent.AgentCollaborators(**base)


def test_agent_collaborators_construction():
    """AgentCollaborators is a plain mutable dataclass for live runtime resources."""
    co = _make_minimal_collaborators()
    assert co.db_name == "test"
    assert co.openrouter_api_key == ""
    assert co.reasoning_memory is None
    # New in Phase 3a-3: Anthropic backend uses an injected client. Defaults
    # to None for Ollama-only apps.
    assert co.anthropic_client is None


def test_agent_collaborators_accepts_anthropic_client():
    """Anthropic-backed apps inject an SDK client via collaborators."""
    sentinel = object()
    co = _make_minimal_collaborators(anthropic_client=sentinel)
    assert co.anthropic_client is sentinel


def test_agent_stream_raises_when_anthropic_backend_lacks_client():
    """Contract: config.backend='anthropic' demands a non-None anthropic_client."""
    cfg = _make_minimal_config(backend="anthropic", default_model="claude-haiku-4-5")
    co = _make_minimal_collaborators()  # anthropic_client defaults to None
    with pytest.raises(RuntimeError, match="anthropic_client"):
        gen = shared_agent.agent_stream("hi", [], cfg, co)
        # Touch the generator to trigger the eager routing check.
        asyncio.run(gen.__anext__())


def test_agent_stream_is_callable_with_minimal_config():
    """After step 3, agent_stream is implemented; invoking it returns a live
    async generator (we don't drain it here — that would require a running
    Neo4j + Ollama. The structural baseline harness covers end-to-end).
    """
    cfg = _make_minimal_config(backend="ollama", default_model="dummy")
    co = _make_minimal_collaborators()
    gen = shared_agent.agent_stream("hi", [], cfg, co)
    assert inspect.isasyncgen(gen), (
        f"agent_stream(...) should return an async generator, got {type(gen).__name__}"
    )
    # Close immediately so we don't actually start the worker thread.
    asyncio.run(gen.aclose())
