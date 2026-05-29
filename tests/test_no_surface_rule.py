"""
Regression guards for the no-surface rule on 9:128 / 9:129.

Doctrine (memory: khalifa-only-source-rule-project-foundational): the app must
NEVER surface or reference 9:128 / 9:129 in any user-facing output — not in
brackets, not in prose, not as "the excluded verses". Khalifa flagged both as
forged additions on Code-19 grounds.

The constraint binds the OUTPUT, not the source corpus. Khalifa's own writings
(Appendix 24) discuss these verses, so the corpus may name them — but anything
the app shows a user (composed answers in eval JSONLs, cache entries) must be
clean.

These tests therefore scan ONLY the user-facing `answer` field of each entry.
They deliberately do NOT inspect `question`, `notes_meta`, or any other metadata
— a question that asks about verse counts, or a meta-note recording provenance,
is not app output and is out of scope for the rule.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_V2_DIR = REPO_ROOT / "data" / "eval" / "v2"
CACHE_PATH = REPO_ROOT / "data" / "answer_cache.json"

# Bracket citation form: [9:128] / [9:129].
BRACKET_FORMS = ("[9:128]", "[9:129]")

# Plain prose form: 9:128 / 9:129 as a standalone reference. The word boundaries
# keep 19:128, 29:128, 9:1280 etc. from matching.
PROSE_RE = re.compile(r"\b9:12[89]\b")


def _iter_jsonl_answers(path: Path):
    """Yield (entry_id, answer) for each entry in a JSONL output file."""
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            yield entry.get("id", "<no-id>"), entry.get("answer", "")


def _scan_jsonl(path: Path, *, mode: str) -> list[str]:
    """Return human-readable violation strings for one JSONL file.

    mode="bracket" → literal [9:128]/[9:129]; mode="prose" → \\b9:12[89]\\b.
    """
    violations: list[str] = []
    for entry_id, answer in _iter_jsonl_answers(path):
        if mode == "bracket":
            hit = next((b for b in BRACKET_FORMS if b in answer), None)
            if hit:
                violations.append(f"{path.name}:{entry_id}: surfaces {hit}")
        else:
            m = PROSE_RE.search(answer)
            if m:
                violations.append(f"{path.name}:{entry_id}: surfaces {m.group(0)!r}")
    return violations


@pytest.mark.xfail(
    strict=True, reason="baseline answers not yet cleaned of bracketed 9:128/9:129"
)
def test_jsonl_outputs_no_9_128_129_brackets():
    """No eval/v2 answer may cite [9:128] or [9:129] in bracket form."""
    jsonls = sorted(EVAL_V2_DIR.glob("*.jsonl"))
    assert jsonls, f"no JSONL outputs found under {EVAL_V2_DIR}"
    violations = [v for path in jsonls for v in _scan_jsonl(path, mode="bracket")]
    assert not violations, "bracketed 9:128/9:129 in answers:\n" + "\n".join(violations)


@pytest.mark.xfail(
    strict=True, reason="baseline answers not yet cleaned of prose 9:128/9:129"
)
def test_jsonl_outputs_no_9_128_129_prose():
    """No eval/v2 answer may reference 9:128 or 9:129 in prose."""
    jsonls = sorted(EVAL_V2_DIR.glob("*.jsonl"))
    assert jsonls, f"no JSONL outputs found under {EVAL_V2_DIR}"
    violations = [v for path in jsonls for v in _scan_jsonl(path, mode="prose")]
    assert not violations, "prose 9:128/9:129 in answers:\n" + "\n".join(violations)


@pytest.mark.xfail(strict=True, reason="cache answers not yet cleaned of 9:128/9:129")
def test_cache_outputs_no_9_128_129():
    """No answer_cache.json entry may surface 9:128/9:129 (bracket or prose)."""
    if not CACHE_PATH.exists():
        pytest.skip(f"{CACHE_PATH} not present locally (gitignored cache)")
    entries = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    violations: list[str] = []
    for i, entry in enumerate(entries):
        answer = entry.get("answer", "")
        hit = next((b for b in BRACKET_FORMS if b in answer), None)
        if hit:
            violations.append(f"cache[{i}]: surfaces {hit}")
        m = PROSE_RE.search(answer)
        if m:
            violations.append(f"cache[{i}]: surfaces {m.group(0)!r}")
    assert not violations, "9:128/9:129 in cache answers:\n" + "\n".join(violations)
