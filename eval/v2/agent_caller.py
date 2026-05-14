"""Default agent caller for the v2 eval runner.

Drives an app's `_agent_stream` end-to-end and returns a structured
`TrajectoryResult`. The drain logic mirrors
`scripts/capture_baseline_trajectory.py` so the v2 eval and the
phase-3a trajectory baseline parse SSE the same way — one source of
truth, no parser drift.

The runner consumes `TrajectoryResult`; the assertion checker and judge
both read from the same shape. Treat this as the contract between the
agent and the rest of the eval pipeline.
"""

from __future__ import annotations

import importlib
import json
import re
from dataclasses import dataclass, field
from typing import Any


CITATION_PATTERN = re.compile(r"\[(\d+):(\d+)\]")


@dataclass
class TrajectoryResult:
    """Structured snapshot of a single agent-stream run.

    Attributes:
        answer_text: concatenation of every ``text`` SSE delta.
        tool_calls: ordered list of ``{name, args_keys, args_str}``
            dicts, one per ``tool`` SSE event. ``args_keys`` is a
            sorted list of the tool-call arg names if the SSE payload
            carried full JSON; ``None`` if the args were truncated.
        citations: sorted unique ``surah:verse`` strings extracted from
            the answer text via the ``[S:V]`` bracket pattern the agent
            emits inline.
        sse_events: the raw event payloads, useful for debugging or
            assertion authors who want more granularity.
        elapsed_seconds: wall-clock duration of the run.
    """

    answer_text: str
    tool_calls: list[dict[str, Any]]
    citations: list[str]
    sse_events: list[dict[str, Any]]
    elapsed_seconds: float = 0.0
    error: str | None = field(default=None)


def _parse_sse_frame(frame: str) -> dict | None:
    """Pull the JSON payload out of a 'data: {...}\\n\\n' SSE line."""
    if not frame.startswith("data: "):
        return None
    body = frame[len("data: ") :].rstrip("\n").rstrip()
    if not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def _structure_tool_event(ev: dict) -> dict:
    raw_args = ev.get("args")
    args_keys: list[str] | None = None
    if isinstance(raw_args, str) and raw_args.startswith("{"):
        try:
            args_keys = sorted(json.loads(raw_args))
        except (json.JSONDecodeError, TypeError):
            args_keys = None
    return {
        "name": ev.get("name"),
        "args_keys": args_keys,
        "args_str": raw_args if isinstance(raw_args, str) else None,
    }


def build_trajectory(events: list[dict]) -> TrajectoryResult:
    """Convert a list of SSE event dicts to a TrajectoryResult."""
    text_chunks: list[str] = []
    tool_calls: list[dict] = []
    error: str | None = None

    for ev in events:
        t = ev.get("t")
        if t == "text":
            text_chunks.append(ev.get("d") or "")
        elif t == "tool":
            tool_calls.append(_structure_tool_event(ev))
        elif t == "error":
            error = ev.get("message") or ev.get("d") or "unknown error"

    answer_text = "".join(text_chunks)
    citation_pairs = CITATION_PATTERN.findall(answer_text)
    citations = sorted({f"{s}:{v}" for s, v in citation_pairs})

    return TrajectoryResult(
        answer_text=answer_text,
        tool_calls=tool_calls,
        citations=citations,
        sse_events=events,
        error=error,
    )


async def run_against_app(
    question: str, *, app_module_name: str = "app_free"
) -> TrajectoryResult:
    """Default agent_caller: drive an app's ``_agent_stream`` and structure the trace.

    The app module is imported lazily so importing this file does not pull
    in Neo4j, sentence-transformers, or any other heavyweight runtime.
    """
    import time

    app_module = importlib.import_module(app_module_name)

    started = time.monotonic()
    events: list[dict] = []
    async for raw_frame in app_module._agent_stream(question, history=[]):
        payload = _parse_sse_frame(raw_frame)
        if payload is None:
            continue
        events.append(payload)
    elapsed = time.monotonic() - started

    trajectory = build_trajectory(events)
    trajectory.elapsed_seconds = round(elapsed, 2)
    return trajectory


def make_app_agent_caller(app_module_name: str = "app_free"):
    """Return an ``agent_caller`` bound to a specific app module.

    Useful when the operator wants to run the same question set
    against app_lite vs app_free for an A/B comparison.
    """

    async def _caller(question: str) -> TrajectoryResult:
        return await run_against_app(question, app_module_name=app_module_name)

    return _caller
