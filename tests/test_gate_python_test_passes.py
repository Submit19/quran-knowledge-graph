"""
Unit tests for the `python_test_passes` acceptance gate added in Phase 2,
item 8 of docs/QKG_RETROFIT_PLAN.md.

The gate function is `ralph_loop.verify_acceptance(task, result)`. It returns
`(all_ok: bool, checks: list[dict])`. Each check dict has shape
`{check, passed, detail}`. We exercise the new branch in isolation by
constructing minimal task dicts that only carry a `spec.acceptance` block.
"""

from __future__ import annotations

import textwrap
from pathlib import Path


from ralph_loop import TickResult, verify_acceptance


def _result() -> TickResult:
    return TickResult(task_id="t", type="test", started_at="2026-05-13T00:00:00Z")


def _task(acceptance: list[dict]) -> dict:
    return {"id": "t", "type": "test", "spec": {"acceptance": acceptance}}


def _write_passing_test(dir_: Path, name: str = "test_pass.py") -> Path:
    p = dir_ / name
    p.write_text(
        textwrap.dedent("""
        def test_ok():
            assert 1 + 1 == 2
    """).lstrip(),
        encoding="utf-8",
    )
    return p


def _write_failing_test(dir_: Path, name: str = "test_fail.py") -> Path:
    p = dir_ / name
    p.write_text(
        textwrap.dedent("""
        def test_intentional_red_bar():
            assert 1 + 1 == 3, "intentional red bar for gate test"
    """).lstrip(),
        encoding="utf-8",
    )
    return p


def test_passing_path_makes_gate_pass(tmp_path):
    target = _write_passing_test(tmp_path)
    # Gate runs pytest with cwd=ROOT, so pass an absolute path.
    all_ok, checks = verify_acceptance(
        _task([{"python_test_passes": str(target)}]), _result()
    )
    assert all_ok is True
    assert len(checks) == 1
    assert checks[0]["passed"] is True
    assert checks[0]["check"].startswith("python_test_passes")


def test_failing_path_makes_gate_fail_and_captures_output(tmp_path):
    target = _write_failing_test(tmp_path)
    all_ok, checks = verify_acceptance(
        _task([{"python_test_passes": str(target)}]), _result()
    )
    assert all_ok is False
    assert len(checks) == 1
    assert checks[0]["passed"] is False
    # The pytest output should be in the detail field — at minimum the
    # AssertionError message should appear.
    assert (
        "intentional red bar" in checks[0]["detail"]
        or "failed" in checks[0]["detail"].lower()
    )


def test_list_of_paths_requires_all_to_pass(tmp_path):
    ok_test = _write_passing_test(tmp_path, "test_ok.py")
    bad_test = _write_failing_test(tmp_path, "test_bad.py")

    # Both pass.
    all_ok, checks = verify_acceptance(
        _task([{"python_test_passes": [str(ok_test), str(ok_test)]}]),
        _result(),
    )
    assert all_ok is True
    assert len(checks) == 2
    assert all(c["passed"] for c in checks)

    # One fails → gate fails, but both check rows are surfaced.
    all_ok, checks = verify_acceptance(
        _task([{"python_test_passes": [str(ok_test), str(bad_test)]}]),
        _result(),
    )
    assert all_ok is False
    assert len(checks) == 2
    assert checks[0]["passed"] is True
    assert checks[1]["passed"] is False


def test_missing_path_is_reported_as_failure_not_crash(tmp_path):
    missing = tmp_path / "does_not_exist.py"
    # The path is absolute so pytest will run, find no file, and exit non-zero.
    all_ok, checks = verify_acceptance(
        _task([{"python_test_passes": str(missing)}]), _result()
    )
    assert all_ok is False
    assert len(checks) == 1
    assert checks[0]["passed"] is False
    # Detail should be non-empty pytest output rather than a Python traceback
    # from our own code.
    assert checks[0]["detail"]
    assert (
        "Traceback" not in checks[0]["detail"]
        or "pytest" in checks[0]["detail"].lower()
    )
