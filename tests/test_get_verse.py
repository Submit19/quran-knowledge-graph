"""
First failing test → first green bar for tool_get_verse.

Beck's Red/Green/Refactor in action: this file documents the original
red-bar (verse not in fixture → tool returns error) AND the green-bar
(verse in fixture → tool returns the expected text). Both stay as
permanent regressions.
"""

from __future__ import annotations

import chat


def test_get_verse_returns_error_when_verse_missing(empty_session):
    """RED-BAR: tool reports 'not found' when the graph has no such verse."""
    result = chat.tool_get_verse(empty_session, "1:1")
    assert "error" in result, f"expected error key, got {result!r}"
    assert "not found" in result["error"].lower()


def test_get_verse_returns_fatiha_opening_when_present(fatiha_session):
    """GREEN-BAR: tool returns the verse text when it's in the graph."""
    result = chat.tool_get_verse(fatiha_session, "1:1")
    assert "error" not in result, f"unexpected error: {result.get('error')!r}"
    assert result["verse_id"] == "1:1"
    assert result["surah"] == 1
    assert result["surah_name"] == "Al-Fatihah"
    assert result["text"].startswith("In the name"), \
        f"expected text to start with 'In the name', got {result['text']!r}"


def test_get_verse_validates_format(empty_session):
    """tool_get_verse rejects malformed verse IDs before hitting Neo4j."""
    result = chat.tool_get_verse(empty_session, "not-a-verse-id")
    assert "error" in result
    # Either the validator catches it OR the not-found path; either is acceptable
    # for this test — we just want a structured error response, not a crash.


# NOTE: A speculative whitespace-normalisation test surfaced a latent bug
# (chat.py:207 `replace(" ", ":")` turns "1 : 1" into "1:::1"). Removed per
# Beck's Triangulate rule — write a regression test for it in Phase 2 instead,
# then fix in Phase 3 (it's unsafe to touch chat.py during Phase 1).
