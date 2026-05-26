"""
Phase 5 design assertions 007 (§E of phase5_design_proposal_2026-05-22.md):

Explicit, mechanical resumability after a pause.

Today:
- Restart is "delete data/RALPH_STOP and run the cron". No audit, no
  backlog-shape verification, no on-resume self-check.

Post-Phase-5:
- scripts/ralph_restart_audit.py exists; emits per-task fitness for
  restart and writes data/.ralph_restart_audit_OK with the backlog SHA
  if all-green (E.1, E.2).
- ralph_tick.py --resume-all rejects unless audit-OK SHA matches the
  current ralph_backlog.yaml (E.2).
- ralph_loop.tick() runs a self-check before its first post-resume
  pick: quality_gate + pytest --maxfail=1 + v2-eval-default-metric
  confirmed (E.4).

xfail until §E implementation lands.

Cross-ref:
- data/research/phase5_design_proposal_2026-05-22.md §E
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §E.1: scripts/ralph_restart_audit.py must exist",
)
def test_restart_audit_script_exists():
    repo_root = Path(__file__).resolve().parents[1]
    p = repo_root / "scripts" / "ralph_restart_audit.py"
    assert p.exists(), f"Expected {p} to exist (§E.1)"


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §E.1: restart audit runs without error on the live backlog",
)
def test_restart_audit_runs_clean():
    """The audit must execute on the current ralph_backlog.yaml without crashing.

    It may emit warnings (review_pending, blocked tasks) but should exit 0
    in audit-only mode (the SHA pin is a separate concern from successful
    execution).
    """
    repo_root = Path(__file__).resolve().parents[1]
    p = repo_root / "scripts" / "ralph_restart_audit.py"
    proc = subprocess.run(
        [sys.executable, str(p)],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(repo_root),
    )
    assert proc.returncode == 0, (
        f"ralph_restart_audit.py exited {proc.returncode}\n"
        f"stdout: {proc.stdout[:400]}\n"
        f"stderr: {proc.stderr[:400]}"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §E.4: post-resume self-check exists",
)
def test_on_resume_self_check_helper_exists():
    """ralph_loop must expose an on-resume self-check helper."""
    import ralph_loop

    candidates = [
        getattr(ralph_loop, name, None)
        for name in (
            "post_resume_self_check",
            "_post_resume_self_check",
            "on_resume_self_check",
            "verify_resume_preconditions",
        )
    ]
    assert any(callable(c) for c in candidates), (
        "Expected ralph_loop to expose an on-resume self-check helper (§E.4)"
    )
