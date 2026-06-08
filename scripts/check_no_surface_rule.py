#!/usr/bin/env python
"""
Enforce the no-surface rule on 9:128 / 9:129 across app output.

Doctrine (memory: khalifa-only-source-rule-project-foundational): anything the
app shows a user must NEVER surface or reference 9:128 / 9:129 — not in brackets
([9:128]), not in prose (9:128), not as "the excluded verses". Khalifa flagged
both as forged additions on Code-19 grounds.

The rule binds OUTPUT, not the source corpus. Khalifa's own writings discuss
these verses, so the Khalifa-primary corpus may name them. This scanner is for
the things users see: composed answers in eval/v2 JSONLs and answer_cache.json.
It therefore inspects ONLY the `answer` field of each entry — never `question`,
`notes_meta`, or other metadata.

Usage:
    python scripts/check_no_surface_rule.py [JSONL ...] [--cache PATH]

With no positional args it scans data/eval/v2/*.jsonl. Exit code is 0 when
clean, 1 when any violation is found. Intended to be wired into a pre-commit
hook so a future composer rewrite cannot silently reintroduce the references.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVAL_DIR = REPO_ROOT / "data" / "eval" / "v2"

BRACKET_FORMS = ("[9:128]", "[9:129]")
PROSE_RE = re.compile(r"\b9:12[89]\b")
_CONTEXT = 70


@dataclass
class Violation:
    source: str
    entry: str
    location: str  # "bracket" | "prose"
    match: str
    context: str

    def render(self) -> str:
        return (
            f"  {self.source} :: {self.entry} :: {self.location} :: {self.match}\n"
            f"      …{self.context}…"
        )


def _context_around(text: str, start: int, end: int) -> str:
    lo = max(0, start - _CONTEXT)
    hi = min(len(text), end + _CONTEXT)
    return text[lo:hi].replace("\n", " ")


def scan_answer(text: str) -> list[tuple[str, str, str]]:
    """Return (location, match, context) for each surface in one answer string."""
    out: list[tuple[str, str, str]] = []
    for form in BRACKET_FORMS:
        idx = text.find(form)
        while idx != -1:
            out.append(("bracket", form, _context_around(text, idx, idx + len(form))))
            idx = text.find(form, idx + 1)
    for m in PROSE_RE.finditer(text):
        # Skip prose hits that are the inner part of a bracket form already caught.
        if text[max(0, m.start() - 1) : m.start()] == "[":
            continue
        out.append(("prose", m.group(0), _context_around(text, m.start(), m.end())))
    return out


def scan_jsonl(path: Path) -> list[Violation]:
    violations: list[Violation] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            entry_id = entry.get("id", "<no-id>")
            for location, match, context in scan_answer(entry.get("answer", "")):
                violations.append(
                    Violation(path.name, entry_id, location, match, context)
                )
    return violations


def scan_cache(path: Path) -> list[Violation]:
    violations: list[Violation] = []
    entries = json.loads(path.read_text(encoding="utf-8"))
    for i, entry in enumerate(entries):
        label = entry.get("question", f"[{i}]")[:60]
        for location, match, context in scan_answer(entry.get("answer", "")):
            violations.append(
                Violation(path.name, f"#{i} {label}", location, match, context)
            )
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Enforce the 9:128/9:129 no-surface rule."
    )
    parser.add_argument(
        "jsonl", nargs="*", type=Path, help="JSONL output files to scan"
    )
    parser.add_argument("--cache", type=Path, help="answer_cache.json to scan")
    args = parser.parse_args(argv)

    jsonls = args.jsonl or sorted(DEFAULT_EVAL_DIR.glob("*.jsonl"))

    violations: list[Violation] = []
    for path in jsonls:
        if not path.exists():
            print(f"warning: {path} not found, skipping", file=sys.stderr)
            continue
        violations.extend(scan_jsonl(path))
    if args.cache:
        if args.cache.exists():
            violations.extend(scan_cache(args.cache))
        else:
            print(f"warning: {args.cache} not found, skipping", file=sys.stderr)

    scanned = ", ".join(p.name for p in jsonls) or "(none)"
    if not violations:
        print(f"OK — no 9:128/9:129 surfaces. Scanned: {scanned}")
        return 0

    print(f"VIOLATIONS ({len(violations)}):")
    for v in violations:
        print(v.render())
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
