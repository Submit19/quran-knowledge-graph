"""
Phase 5 design assertion 003 (§A.3 of phase5_design_proposal_2026-05-22.md):

The `attempts` counter in ralph_state must split `needs_context` (broken
spec) from `failed_or_blocked` (broken work) so the quarantine reason
is legible.

Today: `state['attempts'][task_id]` is a single int. The 3-strikes
rule fires on the combined count, and the console can't tell the
operator whether to fix the YAML or fix the code.

Post-Phase-5: `state['attempts'][task_id] = {'needs_context': N1,
'failed_or_blocked': N2}` and a migration shim handles the old shape.

xfail until §A.3 implementation lands.

Cross-ref:
- data/research/phase5_design_proposal_2026-05-22.md §A.3
- ralph_loop.py::tick attempts handling
"""

from __future__ import annotations

import pytest


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §A.3: attempts counter must be a dict with split sub-counters",
)
def test_attempts_shape_is_split_dict():
    """A migrate_state helper must convert int attempts to {needs_context, failed_or_blocked}."""
    import ralph_loop

    # The helper isn't required to be named exactly _migrate_state; allow either name.
    candidates = [
        getattr(ralph_loop, name, None)
        for name in ("_migrate_state", "migrate_state", "_normalize_attempts")
    ]
    migrator = next((c for c in candidates if callable(c)), None)
    assert migrator is not None, (
        "Expected ralph_loop to expose a state-migration helper for the "
        "split attempts shape (e.g. _migrate_state)."
    )

    legacy_state = {
        "version": 1,
        "attempts": {"task_a": 2, "task_b": 1},
    }
    migrated = migrator(dict(legacy_state))  # don't mutate the input
    assert isinstance(migrated["attempts"]["task_a"], dict)
    assert set(migrated["attempts"]["task_a"].keys()) >= {
        "needs_context",
        "failed_or_blocked",
    }
    # Conservative migration: legacy int -> failed_or_blocked (i.e. assume
    # the worst, so the 3-strikes rule continues to fire on resume).
    assert migrated["attempts"]["task_a"]["failed_or_blocked"] == 2, (
        "Legacy int attempts should migrate into failed_or_blocked"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §A.3: quarantine reason should be distinguishable",
)
def test_quarantine_reason_distinguishable():
    """state should expose which counter tripped the quarantine."""
    import ralph_loop

    # The split quarantine sets named in §A.3 of the design proposal.
    has_spec_broken = hasattr(ralph_loop, "SPEC_BROKEN_QUARANTINE") or False
    has_work_failed = hasattr(ralph_loop, "WORK_FAILED_QUARANTINE") or False
    # Either both module-level constants or a single helper that returns
    # which reason — design proposal leaves naming open.
    assert has_spec_broken or has_work_failed, (
        "Expected ralph_loop to expose distinct quarantine-reason constants "
        "or a helper returning one."
    )
