"""
Phase 5 design assertions 004 (§B of phase5_design_proposal_2026-05-22.md):

Observability surface that lets the operator see the loop's live state.

Today: no live signal — `ralph_state.json::in_progress` is written at
tick start but no progress, no duration telemetry, no per-phase signal.

Post-Phase-5:
- `data/.ralph_heartbeat.json` is written by `tick()` while the executor
  runs (B.1)
- `state['tick_durations']['window']` 24h-rolling list of per-tick
  duration records (B.2)
- `status()` exposes additional fields including `review_pending`,
  `spec_broken_quarantine`, `tick_duration_p50_sec`, `halted_via_RALPH_STOP` (B.3)
- `scripts/ralph_digest.py` exists as a separate script the operator can
  run to dump the last 24h to `data/ralph_digest.md` (B.4)

xfail until §B implementation lands.

Cross-ref:
- data/research/phase5_design_proposal_2026-05-22.md §B
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §B.1: tick() must write a heartbeat file while executor runs",
)
def test_tick_function_references_heartbeat():
    """Static check: ralph_loop.tick() source mentions `.ralph_heartbeat`.

    A real runtime test would require Neo4j + a real task; this check
    catches the 80% case (someone implemented it) cheaply.
    """
    import ralph_loop

    src = inspect.getsource(ralph_loop.tick)
    assert "ralph_heartbeat" in src, (
        "Expected ralph_loop.tick() to write a heartbeat file at "
        "data/.ralph_heartbeat.json (§B.1)"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §B.2: state must accumulate per-tick durations",
)
def test_state_has_tick_durations_window():
    """A fresh state from load_state must include tick_durations."""
    import ralph_loop

    # load_state inlines the schema defaults — inspect its source for the
    # new tick_durations field directly.
    src = inspect.getsource(ralph_loop.load_state)
    assert "tick_durations" in src, (
        "Expected ralph_loop.load_state to seed a tick_durations field "
        "for the duration-telemetry window (§B.2)"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §B.3: status() must expose review_pending",
)
def test_status_exposes_review_pending():
    """status() output must include the review_pending key."""
    import ralph_loop

    s = ralph_loop.status()
    assert "review_pending" in s, (
        "Expected ralph_loop.status() output to include 'review_pending' "
        "(post-§A.1 + §B.3)"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §B.3: status() must report tick duration percentiles",
)
def test_status_exposes_duration_percentiles():
    import ralph_loop

    s = ralph_loop.status()
    assert "tick_duration_p50_sec" in s
    assert "tick_duration_p95_sec" in s


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §B.4: scripts/ralph_digest.py exists",
)
def test_ralph_digest_script_exists():
    """The standalone digest script lives at scripts/ralph_digest.py."""
    repo_root = Path(__file__).resolve().parents[1]
    assert (repo_root / "scripts" / "ralph_digest.py").exists(), (
        "Expected scripts/ralph_digest.py to exist (§B.4)"
    )
