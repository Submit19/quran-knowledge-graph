"""
Phase 5 design assertions 009 (§G of phase5_design_proposal_2026-05-22.md):

System integration: the tamed loop reads the v2 baseline as canonical,
exposes a real cache_op executor, declares reads_graph for graph-touching
tasks, and stays hands-off from the reasoning-memory subgraph writes.

xfail until §G implementation lands.

Cross-ref:
- data/research/phase5_design_proposal_2026-05-22.md §G
"""

from __future__ import annotations

import inspect

import pytest


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §G.1: execute_eval default compare_to is v2 baseline",
)
def test_execute_eval_default_compare_to_is_v2_baseline():
    import ralph_loop

    src = inspect.getsource(ralph_loop.execute_eval)
    assert "data/eval/v2/" in src, (
        "Expected execute_eval to reference data/eval/v2/ as the default "
        "baseline corpus (§G.1)"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §G.2: execute_cache_op exists",
)
def test_execute_cache_op_exists():
    import ralph_loop

    assert hasattr(ralph_loop, "execute_cache_op"), (
        "Expected ralph_loop.execute_cache_op real executor (§G.2)"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §G.2: cache_op is registered in EXECUTORS",
)
def test_cache_op_registered():
    import ralph_loop

    assert "cache_op" in ralph_loop.EXECUTORS, (
        "Expected `cache_op` registered in EXECUTORS dict (§G.2 / "
        "PHASE_5_LOOP_TAMING_PLAN item 18)"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Phase 5 §G.3: reads_graph spec field is honoured in dispatch",
)
def test_reads_graph_spec_field_is_recognised():
    """A task with spec.reads_graph: true must be checked for Neo4j
    reachability before the executor runs."""
    import ralph_loop

    src = inspect.getsource(ralph_loop.tick)
    assert "reads_graph" in src, (
        "Expected ralph_loop.tick() to honour the spec.reads_graph field (§G.3)"
    )
