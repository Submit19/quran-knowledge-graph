"""
Regression: chat.py whitespace-bug cluster (Phase 3b followup).

Phase 3b Bug A fixed one site of `verse_id.strip().replace(" ", ":")` —
the call that turned "1 : 1" into "1:::1" and broke tool_get_verse. The
same anti-pattern exists at four sibling sites, each normalising a
verse-id-shaped input:

  chat.py:133  _validate_verse_id      (helper called by many tools)
  chat.py:366  tool_find_path           (first verse ref `v1`)
  chat.py:367  tool_find_path           (second verse ref `v2`)
  chat.py:584  tool_query_typed_edges   (single verse ref)

Each test below pins the post-fix behaviour for one site (or pair, for
find_path's two refs). They are marked xfail-strict on the red bar and
flipped when the fix lands.
"""

from __future__ import annotations

import pytest

import chat


# ── _validate_verse_id (chat.py:133) ────────────────────────────────────────


@pytest.mark.parametrize(
    "raw",
    [
        "1 : 1",  # canonical inner whitespace
        "1: 1",  # asymmetric space after colon
        "1 :1",  # asymmetric space before colon
        "1  :  1",  # multiple inner spaces
    ],
)
def test_validate_verse_id_accepts_inner_whitespace(raw):
    """The validator normalises whitespace cleanly instead of inserting colons.

    Outer-only whitespace (" 1:1", "1:1 ") is already handled today by the
    leading `.strip()` — those cases pass pre-fix, so they aren't in this
    parametrize. Only inner-whitespace cases exercise the bug.
    """
    err = chat._validate_verse_id(raw)
    assert err is None, f"validator rejected normalised {raw!r}: {err!r}"


# ── tool_find_path (chat.py:366, 367) ──────────────────────────────────────


@pytest.mark.parametrize(
    "raw1,raw2",
    [
        ("1 : 1", "1:1"),  # only v1 has inner whitespace
        ("1:1", "1 : 1"),  # only v2 has inner whitespace
        ("1 :1", "1: 1"),  # both have asymmetric inner whitespace
        ("1  :  1", "1:1"),  # multiple inner spaces in v1
    ],
)
def test_tool_find_path_normalises_both_verse_refs(raw1, raw2, fatiha_session):
    """Both verse_id_1 and verse_id_2 must normalise past _validate_verse_id.

    Path-not-found in fatiha_session is fine (no edges in the fixture); a
    *validation* error is not — that signals the normalisation bug.
    """
    result = chat.tool_find_path(fatiha_session, raw1, raw2)
    err = (result.get("error") or "") if isinstance(result, dict) else ""
    assert "Invalid verse ID format" not in err, (
        f"validation rejected after normalisation for ({raw1!r}, {raw2!r}): {result!r}"
    )


# ── tool_query_typed_edges (chat.py:584) ───────────────────────────────────


@pytest.mark.parametrize(
    "raw_input",
    [
        "1 : 1",
        "1: 1",
        "1 :1",
        "1  :  1",
    ],
)
def test_tool_query_typed_edges_normalises_whitespace(raw_input, fatiha_session):
    result = chat.tool_query_typed_edges(fatiha_session, raw_input)
    assert "error" not in result, f"normalisation failed for {raw_input!r}: {result!r}"
    assert result["verse_id"] == "1:1"
