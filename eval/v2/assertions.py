"""Hard-assertion checker for eval v2.

Each question may carry six list-valued assertion fields (see
``data/eval/v2/SCHEMA.md``). Every assertion either passes or fails as
a unit; a single failure across the whole question zeroes its
dimension scores in the runner (most conservative interpretation;
Phase 4d may refine).

These are *contracts*, not aspirations — they catch the failure modes
the LLM-as-judge tends to miss (subtly wrong answers that read well).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .agent_caller import TrajectoryResult


ASSERTION_KEYS = (
    "cites_must_include",
    "cites_must_not_include",
    "tools_used_must_include",
    "tools_used_must_not_include",
    "answer_substring_required",
    "answer_substring_forbidden",
)


@dataclass
class AssertionOutcome:
    """Result of running every assertion against a single trajectory.

    Attributes:
        passed: list of human-readable assertion descriptors that
            passed (e.g. ``"cites_must_include:2:255"``).
        failed: list of descriptors that failed.
        all_passed: convenience boolean — ``True`` iff ``failed`` is empty.
    """

    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return not self.failed


def _normalise_citations(citations: list[str]) -> set[str]:
    return {c.strip() for c in citations if c}


def _normalise_tool_names(tool_calls: list[dict]) -> set[str]:
    return {tc.get("name") for tc in tool_calls if tc.get("name")}


def check_assertions(
    asserts: dict, trajectory: TrajectoryResult
) -> AssertionOutcome:
    """Run every assertion in the dict. Returns a structured outcome.

    Unknown assertion keys are ignored (forward compatibility — a
    newer question file should still run on an older runner; the
    runner is conservative and prefers an under-strict result over
    a crash).
    """
    outcome = AssertionOutcome()
    asserts = asserts or {}

    cite_set = _normalise_citations(trajectory.citations)
    tool_set = _normalise_tool_names(trajectory.tool_calls)
    answer_lower = (trajectory.answer_text or "").lower()

    # cites_must_include: every listed verse_id present in trajectory.citations.
    for vid in asserts.get("cites_must_include") or []:
        label = f"cites_must_include:{vid}"
        if vid in cite_set:
            outcome.passed.append(label)
        else:
            outcome.failed.append(label)

    # cites_must_not_include: none of the listed verse_ids present.
    for vid in asserts.get("cites_must_not_include") or []:
        label = f"cites_must_not_include:{vid}"
        if vid in cite_set:
            outcome.failed.append(label)
        else:
            outcome.passed.append(label)

    # tools_used_must_include: every listed tool called at least once.
    for tool in asserts.get("tools_used_must_include") or []:
        label = f"tools_used_must_include:{tool}"
        if tool in tool_set:
            outcome.passed.append(label)
        else:
            outcome.failed.append(label)

    # tools_used_must_not_include: none of the listed tools called.
    for tool in asserts.get("tools_used_must_not_include") or []:
        label = f"tools_used_must_not_include:{tool}"
        if tool in tool_set:
            outcome.failed.append(label)
        else:
            outcome.passed.append(label)

    # answer_substring_required: every listed substring in the answer
    # (case-insensitive).
    for needle in asserts.get("answer_substring_required") or []:
        label = f"answer_substring_required:{needle}"
        if needle.lower() in answer_lower:
            outcome.passed.append(label)
        else:
            outcome.failed.append(label)

    # answer_substring_forbidden: none of the listed substrings in the answer.
    for needle in asserts.get("answer_substring_forbidden") or []:
        label = f"answer_substring_forbidden:{needle}"
        if needle.lower() in answer_lower:
            outcome.failed.append(label)
        else:
            outcome.passed.append(label)

    return outcome
