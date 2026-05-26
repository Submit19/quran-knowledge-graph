"""
Phase 5 design assertion 002 (§A.2 of phase5_design_proposal_2026-05-22.md):

`ralph_loop.verify_acceptance` must HARD-FAIL when a task spec has no
`acceptance` block — not soft-pass as it does today (lines 296-300).

Today: a task with no acceptance returns
(True, [{"check": "none specified", "passed": True, ...}]) — i.e. the
gate passes. This is the second leg of the load-bearing-fiction
finding (the first being §A.1's DWC-in-TERMINAL_OK).

Post-Phase-5: missing acceptance is a hard failure with a clear detail.

xfail until §A.2 implementation lands.

Cross-ref:
- data/research/phase5_design_proposal_2026-05-22.md §A.2
- ralph_loop.py::verify_acceptance lines 296-300
"""

from __future__ import annotations

import pytest

from ralph_loop import TickResult, verify_acceptance


def _task(acceptance=None) -> dict:
    spec = {}
    if acceptance is not None:
        spec["acceptance"] = acceptance
    return {"id": "t", "type": "test", "spec": spec}


def _result() -> TickResult:
    return TickResult(task_id="t", type="test", started_at="2026-05-22T00:00:00Z")


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §A.2: missing acceptance block must hard-fail, not soft-pass",
)
def test_task_with_no_acceptance_block_fails():
    """A task whose spec has no `acceptance:` field must fail verification."""
    task = _task(acceptance=None)
    all_ok, checks = verify_acceptance(task, _result())
    assert all_ok is False, (
        "Expected verify_acceptance to FAIL when no acceptance is specified; "
        "got soft-pass. This is the §A.2 leak."
    )


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §A.2: empty acceptance list must also hard-fail",
)
def test_task_with_empty_acceptance_list_fails():
    """`acceptance: []` is equivalent to no acceptance and must hard-fail."""
    task = _task(acceptance=[])
    all_ok, _ = verify_acceptance(task, _result())
    assert all_ok is False, "Expected acceptance=[] to fail the same as acceptance=None"


def test_task_with_acceptance_still_evaluates():
    """Guardrail (not xfail): real acceptance checks must still run.

    A task with a working `file_exists: <existing-path>` must pass.
    Ensures §A.2 doesn't accidentally short-circuit the whole verify_acceptance.
    """
    # ralph_loop.py exists at repo root; safe to reference.
    task = {
        "id": "t",
        "type": "test",
        "spec": {"acceptance": [{"file_exists": "ralph_loop.py"}]},
    }
    all_ok, checks = verify_acceptance(task, _result())
    assert all_ok is True
    assert any(c["check"].startswith("file_exists") for c in checks)
