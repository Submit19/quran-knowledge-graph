"""
Phase 5 design assertions 008 (§F of phase5_design_proposal_2026-05-22.md):

Quality bar:
- execute_eval defaults to v2 hard_pass_rate, not avg_unique_cites_per_q (F.1)
- python_test_passes ALSO runs the full suite with --maxfail=1 (F.2)
- execute_regression handles the xfail-removal workflow (F.3)
- triangulation gate active (F.4)

xfail until §F implementation lands.

Cross-ref:
- data/research/phase5_design_proposal_2026-05-22.md §F
- docs/PHASE_5_LOOP_TAMING_PLAN.md item 21 (triangulation)
- operator's CLAUDE.md (xfail pattern)
"""

from __future__ import annotations

import inspect

import pytest


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §F.1: execute_eval default metric is v2 hard_pass_rate",
)
def test_execute_eval_default_metric_is_hard_pass():
    """The default metric in execute_eval must be `hard_pass_rate`."""
    import ralph_loop

    src = inspect.getsource(ralph_loop.execute_eval)
    # The default value is a string literal in spec.get(...) — search for it.
    assert '"hard_pass_rate"' in src or "'hard_pass_rate'" in src, (
        "Expected execute_eval to default metric='hard_pass_rate' (§F.1)"
    )
    # And the old default should NO LONGER be in the source as a default:
    assert '"avg_unique_cites_per_q"' not in src.split("metric = spec.get")[0:1][0], (
        "Sanity: the retired metric should not be the function-default anymore"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §F.2: python_test_passes must also run the full suite",
)
def test_python_test_passes_includes_full_suite_check():
    """Static check: verify_acceptance source mentions a full-suite (--maxfail=1) run."""
    import ralph_loop

    src = inspect.getsource(ralph_loop.verify_acceptance)
    # Heuristic — the design's pytest invocation includes --maxfail=1 over tests/
    has_maxfail = "--maxfail" in src
    has_tests_dir = '"tests/"' in src or "'tests/'" in src or '"tests"' in src
    assert has_maxfail and has_tests_dir, (
        f"Expected verify_acceptance to run a full-suite pytest in addition "
        f"to the targeted test path. has_maxfail={has_maxfail}, "
        f"has_tests_dir={has_tests_dir} (§F.2)"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §F.3: execute_regression task executor exists",
)
def test_execute_regression_exists():
    """A dedicated executor for the xfail-removal regression task type."""
    import ralph_loop

    assert hasattr(ralph_loop, "execute_regression"), (
        "Expected ralph_loop.execute_regression to exist (§F.3)"
    )
    fn = ralph_loop.execute_regression
    assert callable(fn), "execute_regression must be callable"


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §F.4: triangulation gate function exists",
)
def test_triangulation_gate_helper_exists():
    """ralph_loop must expose a gate function that detects classifier
    additions and refuses to pass without ≥2 new tests."""
    import ralph_loop

    candidates = [
        getattr(ralph_loop, name, None)
        for name in (
            "acceptance_classifier_or_routing_change",
            "triangulation_gate",
            "_triangulation_gate",
            "detect_classifier_additions",
        )
    ]
    assert any(callable(c) for c in candidates), (
        "Expected ralph_loop to expose a triangulation-gate helper "
        "(§F.4 / retrofit item 21)"
    )
