"""
Phase 5 design assertions 005 (§C of phase5_design_proposal_2026-05-22.md):

Stop discipline beyond the existing CRON_BRIEF.md RALPH_STOP check.

Today:
- CRON_BRIEF.md step 1 checks RALPH_STOP — only fires if the cron
  subagent is the entry point. ralph_run.py / ralph_tick.py do not
  check it directly.
- No auto-halt on consecutive failures.
- No metric-trend halt.

Post-Phase-5:
- ralph_loop.tick() checks `data/RALPH_STOP` at the top and returns
  None if present (C.1) — belt-and-braces.
- After 5 consecutive failures, tick() writes `data/RALPH_STOP_AUTO`
  with a reason file (C.2).
- After 5 eval ticks with ≥5% cumulative regression, tick() writes
  RALPH_STOP_AUTO (C.3).
- ralph_tick.py supports --pause / --resume / --resume-all flags
  (C.4).

xfail until §C implementation lands.

Cross-ref:
- data/research/phase5_design_proposal_2026-05-22.md §C
"""

from __future__ import annotations

import inspect
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §C.1: tick() must short-circuit when data/RALPH_STOP exists",
)
def test_tick_returns_none_when_ralph_stop_exists(tmp_path, monkeypatch):
    """Construct a fake repo root with RALPH_STOP and check tick exits cleanly."""
    import ralph_loop

    fake_data = tmp_path / "data"
    fake_data.mkdir()
    (fake_data / "RALPH_STOP").write_text("test halt\n")

    # Re-point ROOT/DATA_DIR for this test.
    monkeypatch.setattr(ralph_loop, "ROOT", tmp_path)
    monkeypatch.setattr(ralph_loop, "DATA_DIR", fake_data)
    monkeypatch.setattr(
        ralph_loop,
        "BACKLOG_PATH",
        tmp_path / "ralph_backlog.yaml",
    )
    monkeypatch.setattr(ralph_loop, "STATE_PATH", tmp_path / "ralph_state.json")

    # tick() must exit early without loading backlog (so missing backlog is OK).
    result = ralph_loop.tick()
    assert result is None, (
        "Expected tick() to return None when data/RALPH_STOP is present"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §C.2: 5 consecutive failures must write RALPH_STOP_AUTO",
)
def test_consecutive_failure_auto_halt_source_marker():
    """Static check: tick source references RALPH_STOP_AUTO and 5-consecutive logic."""
    import ralph_loop

    src = inspect.getsource(ralph_loop.tick)
    assert "RALPH_STOP_AUTO" in src, (
        "Expected ralph_loop.tick() to write data/RALPH_STOP_AUTO on "
        "consecutive failures (§C.2)"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §C.4: ralph_tick.py exposes --pause and --resume-all flags",
)
def test_ralph_tick_cli_supports_pause_resume():
    """Run `python ralph_tick.py --help` and look for the new flags."""
    repo_root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(repo_root / "ralph_tick.py"), "--help"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(repo_root),
    )
    help_text = proc.stdout + proc.stderr
    assert "--pause" in help_text, "Expected --pause flag (§C.4)"
    assert "--resume-all" in help_text, "Expected --resume-all flag (§C.4)"
