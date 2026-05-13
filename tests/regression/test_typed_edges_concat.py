"""
Regression: chat.py tool_query_typed_edges builds Cypher by string concat.

Today the function does `"...-[r:" + edge_type + "]-..."`. It's safe because
an allowlist check `if edge_type not in valid_types: return error` runs
before the concat. But the pattern is a foot-gun — a future refactor that
loosens the allowlist would open a query-injection surface.

This is a characterization test, not a red-bar test: it pins the externally
visible behaviour so we can refactor the implementation (to parameter
binding or a fixed query map) without changing observable output.

Boundary cases:
- Each valid edge_type returns the expected by_type shape.
- An invalid edge_type is rejected upstream with a clear error.
- Verse-not-found path works regardless of edge_type filter.
"""

from __future__ import annotations

import pytest

import chat
from tests.fakes.neo4j_session import FakeNeo4jSession, graph_with_fatiha_opening


VALID_TYPES = ["SUPPORTS", "ELABORATES", "QUALIFIES", "CONTRASTS", "REPEATS"]


def _graph_with_typed_edges():
    """1:1 connected to a different verse via every valid edge type."""
    g = graph_with_fatiha_opening()
    g["verses"]["1:2"] = {
        "verseId": "1:2",
        "surah": 1,
        "surahName": "Al-Fatihah",
        "text": "Praise be to God, Lord of the universe.",
        "arabicText": "",
    }
    g["typed_edges"]["1:1"] = [
        ("1:2", "SUPPORTS", 0.91, 0.95),
        ("1:2", "ELABORATES", 0.80, 0.90),
        ("1:2", "QUALIFIES", 0.70, 0.85),
        ("1:2", "CONTRASTS", 0.60, 0.80),
        ("1:2", "REPEATS", 0.50, 0.75),
    ]
    return g


@pytest.mark.parametrize("edge_type", VALID_TYPES)
def test_query_typed_edges_each_valid_type_returns_expected_shape(edge_type):
    session = FakeNeo4jSession(_graph_with_typed_edges())
    result = chat.tool_query_typed_edges(session, "1:1", edge_type=edge_type)

    assert "error" not in result, f"unexpected error for {edge_type}: {result!r}"
    assert result["verse_id"] == "1:1"
    assert result["edge_type_filter"] == edge_type
    assert result["total_results"] >= 1
    assert edge_type in result["by_type"]
    hit = result["by_type"][edge_type][0]
    assert hit["verse_id"] == "1:2"


def test_query_typed_edges_no_filter_returns_all_types():
    session = FakeNeo4jSession(_graph_with_typed_edges())
    result = chat.tool_query_typed_edges(session, "1:1")

    assert "error" not in result, f"unexpected error: {result!r}"
    assert result["edge_type_filter"] is None
    # All five valid types are represented in the fake.
    assert set(result["by_type"].keys()) == set(VALID_TYPES)


@pytest.mark.parametrize(
    "bad_type",
    [
        "SUPPORTS]-(x) DETACH DELETE v //",  # injection-like
        "SUPPORTS OR true",  # logic-injection-like
        "NOT_A_TYPE",  # plain unknown
    ],
)
def test_query_typed_edges_rejects_non_allowlisted_types(bad_type):
    """Allowlist boundary holds: anything outside the 5 valid types is rejected."""
    session = FakeNeo4jSession(_graph_with_typed_edges())
    result = chat.tool_query_typed_edges(session, "1:1", edge_type=bad_type)
    assert "error" in result, f"expected rejection of {bad_type!r}, got {result!r}"
    assert "Unknown edge type" in result["error"]


def test_query_typed_edges_lowercase_is_uppercased_then_accepted():
    """'supports' uppercases to 'SUPPORTS' — an ergonomics affordance we pin."""
    session = FakeNeo4jSession(_graph_with_typed_edges())
    result = chat.tool_query_typed_edges(session, "1:1", edge_type="supports")
    assert "error" not in result
    assert result["edge_type_filter"] == "SUPPORTS"


def test_query_typed_edges_empty_string_filter_treated_as_no_filter():
    """Empty string is falsy → function returns the union of all types."""
    session = FakeNeo4jSession(_graph_with_typed_edges())
    result = chat.tool_query_typed_edges(session, "1:1", edge_type="")
    assert "error" not in result
    # Falsy filter triggers the no-filter branch; all 5 types present.
    assert set(result["by_type"].keys()) == set(VALID_TYPES)


def test_query_typed_edges_unknown_verse_returns_not_found():
    session = FakeNeo4jSession(_graph_with_typed_edges())
    result = chat.tool_query_typed_edges(session, "99:99", edge_type="SUPPORTS")
    assert "error" in result
    assert "not found" in result["error"].lower()
