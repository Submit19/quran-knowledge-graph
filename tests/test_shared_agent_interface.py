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
    assert {"message", "history", "config"}.issubset(params)
    # Per-request overrides the free app currently passes through.
    assert {"deep_dive", "full_coverage", "model_override", "local_only"}.issubset(
        params
    )


def test_agent_stream_is_callable_with_minimal_config():
    """After step 3, agent_stream is implemented; invoking it returns a live
    async generator (we don't drain it here — that would require a running
    Neo4j + Ollama. The structural baseline harness covers end-to-end).
    """
    cfg = _make_minimal_config(backend="ollama", default_model="dummy")
    gen = shared_agent.agent_stream("hi", [], cfg)
    assert inspect.isasyncgen(gen), (
        f"agent_stream(...) should return an async generator, got {type(gen).__name__}"
    )
    # Close immediately so we don't actually start the worker thread.
    asyncio.run(gen.aclose())
