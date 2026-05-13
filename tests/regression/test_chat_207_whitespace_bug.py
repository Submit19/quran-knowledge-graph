"""
Regression: chat.py:207 turns "1 : 1" into "1:::1".

`tool_get_verse` does `verse_id.strip().replace(" ", ":")`. The intent was
to strip internal whitespace from a verse id so "1 : 1" normalises to
"1:1", but `replace(" ", ":")` substitutes each space character with a
colon, producing "1:::1" — which then fails `_validate_verse_id` and is
reported as "not found".

This test pins the intended behaviour. It currently FAILS (the buggy code
returns an error); the xfail-strict marker keeps the suite green while
documenting the bug. When chat.py:207 is fixed in Phase 3, this test will
start passing as XPASS, which strict=True turns into a hard failure —
forcing the operator to remove the marker and admit the regression test
into the regular suite.
"""

from __future__ import annotations

import pytest

import chat
from tests.fakes.neo4j_session import FakeNeo4jSession, graph_with_fatiha_opening


@pytest.mark.xfail(strict=True, reason="chat.py:207 replace(' ',':') bug; Phase 3 fix")
def test_get_verse_normalises_inner_whitespace():
    session = FakeNeo4jSession(graph_with_fatiha_opening())
    result = chat.tool_get_verse(session, "1 : 1")
    assert "error" not in result, f"normalisation failed: {result!r}"
    assert result["verse_id"] == "1:1"
