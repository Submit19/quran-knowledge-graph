"""
Regression-guard for the Shuaib alias matcher in
scripts/cache_coverage_report.py.

The coverage report walks PROPHETS_25 and checks whether each prophet's
alias list appears as a case-insensitive substring inside any cache
answer. On 2026-05-21 Shuaib was flagged as 0-coverage even though
the cache contains 8 entries mentioning "Shu`aib" (backtick ʿayn) and
10 entries mentioning "Shu‘aib" (curly apostrophe). The aliases shipped
were ["shu'aib", "shuaib", "shoaib"] — only straight apostrophe and
the de-diacritised "shuaib"/"shoaib" forms, neither of which matched
the canonical Shu`aib transliteration the capable-model baseline used.

This test loads PROPHETS_25 from the script and verifies that the
Shuaib alias list, run against a synthetic answer using the backtick
form, produces at least one match. The same is checked against a
representative slice of the real cache when present.

When the alias list omits the backtick variant, this test fails.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "cache_coverage_report.py"
CACHE = ROOT / "data" / "answer_cache.json"


def _load_prophets_25():
    """Import PROPHETS_25 from the coverage-report script by path."""
    spec = importlib.util.spec_from_file_location("cache_coverage_report", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("cache_coverage_report", mod)
    spec.loader.exec_module(mod)
    return mod.PROPHETS_25


def _shuaib_aliases():
    for canonical, aliases in _load_prophets_25():
        if canonical.lower().startswith("shu"):
            return aliases
    raise AssertionError("Shu`aib entry missing from PROPHETS_25")


def test_shuaib_alias_matches_backtick_form():
    """The alias list must match the backtick ʿayn form ("Shu`aib")."""
    aliases = _shuaib_aliases()
    sample = "Madyan and their brother Shu`aib. He said, 'O my people...'"
    txt = sample.lower()
    assert any(a in txt for a in aliases), (
        f"Shu`aib alias list does not match backtick-ʿayn form. Aliases={aliases!r}"
    )


@pytest.mark.skipif(
    not CACHE.exists(), reason="answer_cache.json absent (gitignored fixture)"
)
def test_shuaib_alias_finds_at_least_one_cache_hit():
    """Across the live cache, the Shuaib alias list must hit ≥1 entry."""
    aliases = _shuaib_aliases()
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    hits = sum(
        1 for r in cache if any(a in (r.get("answer") or "").lower() for a in aliases)
    )
    assert hits >= 1, (
        f"Shuaib alias list matched {hits} cache entries; expected ≥1. "
        f"Aliases={aliases!r}"
    )
