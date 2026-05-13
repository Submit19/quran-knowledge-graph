"""
Shared pytest fixtures for QKG tests.

Two flavours of mock Neo4j session:

  - `empty_session` — a FakeNeo4jSession backed by an empty graph. Tools
    that look up a verse will report "not found"; useful for red-bar tests.

  - `fatiha_session` — a FakeNeo4jSession with 1:1 (Al-Fatihah opening verse)
    in it. Useful for green-bar tests against tool_get_verse.

When you need a richer graph, build it inline in your test (or add a new
named fixture here). When you need real Cypher semantics, swap in
testcontainers-python with a Neo4j container — same `session` object shape.
"""

from __future__ import annotations

import pytest

from tests.fakes.neo4j_session import (
    FakeNeo4jSession,
    empty_graph,
    graph_with_fatiha_opening,
)


@pytest.fixture
def empty_session() -> FakeNeo4jSession:
    """A FakeNeo4jSession with no verses. tool_get_verse('X:Y') returns error."""
    return FakeNeo4jSession(empty_graph())


@pytest.fixture
def fatiha_session() -> FakeNeo4jSession:
    """A FakeNeo4jSession containing only verse 1:1 (Al-Fatihah opening)."""
    return FakeNeo4jSession(graph_with_fatiha_opening())
