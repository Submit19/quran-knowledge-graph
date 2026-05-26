"""
Phase 5 design assertions 006 (§D of phase5_design_proposal_2026-05-22.md):

Scope discipline: `EXECUTORS` shrinks; `agent_creative` removed from
cron dispatch; CRON_BRIEF.md MAINT/RESEARCH cycles stripped; the loop
cannot edit its own scaffolding.

Today:
- EXECUTORS = {eval, cypher_analysis, cleanup, agent_creative}
- CRON_BRIEF.md still contains the MAINT (memory_hygiene, ADR-drift)
  and RESEARCH steps.
- No scaffolding-edit lockdown.

Post-Phase-5:
- agent_creative NOT auto-dispatched from cron (D.1)
- regression and triangulation task types EXIST in EXECUTORS (D.1)
- CRON_BRIEF.md MAINT block stripped of memory_hygiene / ADR-drift /
  synthesis (D.2)
- ralph_loop has a scaffolding-edit check (D.4)

xfail until §D implementation lands.

Cross-ref:
- data/research/phase5_design_proposal_2026-05-22.md §D
- docs/PHASE_5_LOOP_TAMING_PLAN.md item 18
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §D.1: regression task type must be a registered executor",
)
def test_regression_executor_registered():
    import ralph_loop

    assert "regression" in ralph_loop.EXECUTORS, (
        "Expected `regression` in EXECUTORS (§D.1 / retrofit plan item 18)"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §D.1: triangulation task type must be a registered executor",
)
def test_triangulation_executor_registered():
    import ralph_loop

    assert "triangulation" in ralph_loop.EXECUTORS, (
        "Expected `triangulation` in EXECUTORS (§D.1)"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §D.1: agent_creative must NOT be in cron-dispatch EXECUTORS",
)
def test_agent_creative_not_in_executors():
    """agent_creative stays in code (callable manually) but is removed
    from the auto-dispatch dict the cron uses."""
    import ralph_loop

    assert "agent_creative" not in ralph_loop.EXECUTORS, (
        "Expected `agent_creative` to be REMOVED from EXECUTORS so the cron "
        "no longer auto-dispatches it (§D.1). It may still be callable via "
        "operator-only entry points."
    )


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §D.2: CRON_BRIEF.md MAINT block must be stripped",
)
def test_cron_brief_strips_maintenance_research():
    """Static check: CRON_BRIEF.md should no longer reference memory_hygiene.py
    or the RESEARCH-tick research-queue pop logic."""
    repo_root = Path(__file__).resolve().parents[1]
    brief = (repo_root / "scripts" / "CRON_BRIEF.md").read_text(encoding="utf-8")
    # Both phrases are signatures of the strip-targets.
    has_memory_hygiene = "memory_hygiene.py" in brief
    has_research_block = "RESEARCH tick procedure" in brief
    assert not has_memory_hygiene and not has_research_block, (
        f"CRON_BRIEF.md still references stripped scope: "
        f"memory_hygiene={has_memory_hygiene}, research_block={has_research_block}"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §D.4: scaffolding-edit lockdown must exist",
)
def test_scaffolding_edit_lockdown_helper_exists():
    """ralph_loop must expose a helper that checks if a diff touches
    forbidden scaffolding paths (ralph_loop.py, ralph_run.py, CRON_BRIEF.md,
    etc.)."""
    import ralph_loop

    candidates = [
        getattr(ralph_loop, name, None)
        for name in (
            "check_scaffolding_edit",
            "_check_scaffolding_edit",
            "detect_scaffolding_edit",
            "scaffolding_edit_lockdown",
        )
    ]
    assert any(callable(c) for c in candidates), (
        "Expected ralph_loop to expose a scaffolding-edit-detection helper "
        "(§D.4 of design proposal)"
    )
