"""Shared agent-loop module — Phase 3a target.

Public surface for the four `app*.py` files. Today the body of each app's
``_agent_stream`` is a near-duplicate of the others — this module is the
single home where that body will live.

This file is the **interface stub**, written first per Phase 3a step 2 of
``docs/PHASE_3A_PLAN.md``. Function bodies raise ``NotImplementedError``
so any accidental caller surfaces immediately. The implementation lands in
the next commit (step 3) by moving code out of ``app_free.py``.

Public surface:
    AgentConfig — frozen dataclass of per-app variant axes.
    agent_stream — async generator that yields SSE frames.

Wiring contract (preserved through the refactor):
    - Each turn is wrapped in ``sse_pump.pump_worker_into_sse`` so the
      Phase 3b daemon-thread leak fix remains active.
    - The agent loop body polls ``stop_event.is_set()`` at the top of
      every turn for cooperative cancellation on consumer disconnect.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Literal


# ──────────────────────────────────────────────────────────────────────────
# Public configuration
# ──────────────────────────────────────────────────────────────────────────


BackendName = Literal["anthropic", "ollama", "openrouter"]
"""Allowed values for ``AgentConfig.backend``. Enforced at construction."""


@dataclass(frozen=True)
class AgentConfig:
    """Per-app variant axes for ``agent_stream``.

    Each app instantiates one of these at import time and passes the same
    instance to every ``agent_stream(...)`` call. The fields cover the
    variant table in ``docs/PHASE_3A_PLAN.md`` §"What behaviour preservation
    means concretely".

    The dataclass is frozen so wrappers cannot drift its values mid-request.
    Per-request overrides (e.g. ``deep_dive``, ``model_override``) go through
    ``agent_stream`` kwargs, not by mutating the config.
    """

    # — Required —
    backend: BackendName
    default_model: str
    tools: list[dict]
    system_prompt: str

    # — Loop limits —
    max_tool_turns: int = 15
    max_tokens: int = 4096

    # — Feature flags (variant axes) —
    enable_citation_density_retry: bool = False
    min_citations_for_retry: int = 3
    enable_uncertainty_probe: bool = False
    enable_citation_verifier: bool = False
    enable_priming_graph_update: bool = False
    enable_reasoning_memory_playbook: bool = False
    enable_query_classification: bool = False
    enable_tool_result_compression: bool = False
    enable_answer_cache_lookup: bool = True
    enable_answer_cache_save: bool = True

    # — Backend-specific routing (mostly app_free) —
    openrouter_model: str | None = None
    deep_dive_model: str | None = None
    prefer_openrouter: bool = False

    # — Tooling identifiers (informational; surfaced to the UI) —
    tool_labels: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.backend not in ("anthropic", "ollama", "openrouter"):
            raise ValueError(
                f"AgentConfig.backend must be one of "
                f"'anthropic'|'ollama'|'openrouter', got {self.backend!r}"
            )
        if self.max_tool_turns < 1:
            raise ValueError(
                f"AgentConfig.max_tool_turns must be >= 1, got {self.max_tool_turns}"
            )
        if not isinstance(self.tools, list):
            raise TypeError(
                f"AgentConfig.tools must be a list, got {type(self.tools).__name__}"
            )


# ──────────────────────────────────────────────────────────────────────────
# Public entry-point
# ──────────────────────────────────────────────────────────────────────────


async def agent_stream(
    message: str,
    history: list,
    config: AgentConfig,
    *,
    deep_dive: bool = False,
    full_coverage: bool = False,
    model_override: str | None = None,
    local_only: bool = False,
) -> AsyncIterator[str]:
    """Run the agent loop and yield SSE-formatted ``data: …\\n\\n`` frames.

    Each app's ``@app.post("/chat")`` handler builds a `StreamingResponse`
    from this generator. The body delegates the daemon-thread + queue
    orchestration to ``sse_pump.pump_worker_into_sse``; the worker polls
    ``stop_event`` between turns so a client disconnect cleanly tears down
    the agent loop (Phase 3b Bug D contract).

    Per-request overrides:
        deep_dive: route through a larger backend for this request.
        full_coverage: extend max_tokens/context for synthesis-heavy queries.
        model_override: pin a specific backend model for this request.
        local_only: skip OpenRouter even if normally preferred (offline /
            quota-hit fallback).

    Backend-specific knobs (e.g. priming, playbook injection, OpenAI vs
    Anthropic tool-call shape) are dispatched off ``config``, not the
    per-request kwargs.

    Yields:
        str frames in ``data: <json>\\n\\n`` SSE format.
    """
    raise NotImplementedError(
        "shared_agent.agent_stream — Phase 3a stub; impl lands in step 3"
    )
    yield  # marker: this function is an async generator, not a coroutine
