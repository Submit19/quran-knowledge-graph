"""
Phase 5 design assertion 001 (§A.1 of phase5_design_proposal_2026-05-22.md):

DONE_WITH_CONCERNS must no longer be in ralph_loop.TERMINAL_OK.

This is the central failure-mode fix: today, agent_creative ticks
default to DWC; the picker treats DWC as "task complete" via TERMINAL_OK
membership; the work piles up in data/ralph_*.md unreviewed.

Post-Phase-5: DWC tasks are routed to a review_pending queue and stay
out of done_task_ids until the operator explicitly promotes them.

xfail until §A.1 implementation lands. When the implementation lands,
remove the xfail marker in the SAME commit (Beck red→green→commit).

Cross-ref:
- data/research/phase5_design_proposal_2026-05-22.md §A.1
- ralph_loop.py::TERMINAL_OK
- docs/QKG_AUDIT.md §7 ("62% DWC is a load-bearing fiction")
"""

from __future__ import annotations

import pytest

import ralph_loop


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §A.1: DONE_WITH_CONCERNS must leave TERMINAL_OK",
)
def test_dwc_not_in_terminal_ok():
    """The picker must not treat DWC as a terminal-success state."""
    assert ralph_loop.DONE_WITH_CONCERNS not in ralph_loop.TERMINAL_OK


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §A.1: a review_pending set should exist alongside TERMINAL_OK",
)
def test_review_pending_set_exists():
    """There must be a named set for the DWC route post-Phase-5."""
    # Either TERMINAL_NEEDS_REVIEW or REVIEW_PENDING — name TBD at impl time.
    has_review_set = any(
        hasattr(ralph_loop, name)
        for name in ("TERMINAL_NEEDS_REVIEW", "REVIEW_PENDING")
    )
    assert has_review_set, (
        "Expected ralph_loop to expose a TERMINAL_NEEDS_REVIEW or "
        "REVIEW_PENDING set covering {DONE_WITH_CONCERNS}"
    )


def test_done_stays_in_terminal_ok():
    """Guardrail (not xfail): A.1 must not accidentally also drop DONE/SKIPPED.

    Today this test passes (DONE and SKIPPED are in TERMINAL_OK). The Phase 5
    §A.1 implementation must keep it passing — only DWC leaves the set.
    """
    assert ralph_loop.DONE in ralph_loop.TERMINAL_OK
    assert ralph_loop.SKIPPED in ralph_loop.TERMINAL_OK
