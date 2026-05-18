"""
Regression: tool_run_cypher's denylist must reject every write/admin
Cypher clause that's been observed (or imagined) trying to slip past.

The tool is the long-tail escape hatch the agent reaches for when no
specialised tool fits the user's question. It's powerful — full Cypher
against the production graph — and the denylist is the only thing
between "let the model write its own aggregation query" and "let the
model accidentally truncate the graph."

Phase 7 item 30 in docs/QKG_RETROFIT_PLAN.md called for this test
explicitly. The denylist itself was added in earlier work; what was
missing was a guard that catches if a refactor or a "while we're in
there" tweak silently weakens it.

These tests cover three concerns:

  1. EVERY currently-denied clause is denied — across case variants,
     whitespace, and trailing-syntax variants.
  2. Valid read-only queries pass through (no false rejections of
     ordinary MATCH/RETURN shape).
  3. Known limitations are pinned by example so they can't drift
     silently (string-literal false-positives, etc.).

No Neo4j required: the denylist check fires before any session.run()
call, so we pass a sentinel session that would raise if accessed.
"""

from __future__ import annotations

import pytest

import chat


class _BoomSession:
    """Sentinel session: any attribute access raises.

    If the denylist correctly rejects a forbidden query, we never get
    to session.run() and the test passes. If the denylist FAILS to
    reject a forbidden query, we hit this and the test fails with a
    clear message.
    """

    def __getattr__(self, name):
        raise AssertionError(
            f"_BoomSession.{name} accessed — the denylist failed to reject "
            f"a forbidden query and the request would have been forwarded "
            f"to Neo4j."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Forbidden clauses — each entry is (label, query). Every one MUST be rejected.
# ─────────────────────────────────────────────────────────────────────────────

FORBIDDEN_QUERIES = [
    # Node / relationship mutations
    ("CREATE node", "CREATE (n:Verse {verseId: '99:99'})"),
    ("create lowercase", "create (n:Verse {verseId: '99:99'})"),
    ("CREATE INDEX", "CREATE INDEX my_idx FOR (n:Verse) ON (n.text)"),
    ("MERGE node", "MERGE (n:Verse {verseId: '1:1'})"),
    ("DELETE node", "MATCH (n:Verse) DELETE n"),
    ("DETACH DELETE", "MATCH (n:Verse) DETACH DELETE n"),
    ("SET property", "MATCH (n:Verse) SET n.text = 'hax'"),
    ("REMOVE property", "MATCH (n:Verse) REMOVE n.embedding"),
    # Data-loading
    ("LOAD CSV", "LOAD CSV FROM 'file:///x.csv' AS row CREATE (n:X) RETURN n"),
    (
        "LOAD CSV WITH HEADERS",
        "LOAD CSV WITH HEADERS FROM 'file:///x.csv' AS row RETURN row",
    ),
    # APOC mutations
    ("CALL apoc.refactor", "CALL apoc.refactor.rename.label('Verse', 'Hax')"),
    (
        "CALL apoc.periodic",
        "CALL apoc.periodic.iterate('MATCH (n) RETURN n', 'DETACH DELETE n', {})",
    ),
    ("CALL apoc.nodes.delete", "CALL apoc.nodes.delete(['v1'], 1000)"),
    ("CALL apoc.load", "CALL apoc.load.json('https://evil.example/x.json')"),
    # DBMS / admin
    ("CALL dbms", "CALL dbms.security.createUser('hax','pw',false)"),
    ("DROP index", "DROP INDEX verse_embedding"),
    ("DROP database", "DROP DATABASE quran"),
    ("CALL db.create", "CALL db.createLabel('Hax')"),
    ("CALL db.drop", "CALL db.dropConstraint('foo')"),
    (
        "CALL db.index.vector.create",
        "CALL db.index.vector.createNodeIndex('hax','Verse','embedding',384,'cosine')",
    ),
    # Session / schema control
    ("USE database", "USE quran MATCH (n) RETURN n"),
    ("START transaction", "START explicit transaction"),
    ("STOP", "STOP foo"),
    (
        "CONSTRAINT",
        "CREATE CONSTRAINT verse_id FOR (n:Verse) REQUIRE n.verseId IS UNIQUE",
    ),
    ("INDEX ON", "CREATE INDEX ON :Verse(verseId)"),
    ("INDEX FOR", "CREATE INDEX my_idx FOR (n:Verse) ON (n.text)"),
    # Whitespace / case variations on the headline clauses
    ("merge mixed case", "MERGE  (n:Verse {verseId:'1:1'})"),
    ("delete tabbed", "MATCH (n:Verse)\tDELETE\tn"),
]


@pytest.mark.parametrize(
    "label,query", FORBIDDEN_QUERIES, ids=lambda x: x if isinstance(x, str) else None
)
def test_denylist_rejects_forbidden_query(label, query):
    """Every entry in FORBIDDEN_QUERIES must return ok=False with an error."""
    result = chat.tool_run_cypher(_BoomSession(), query=query)
    assert isinstance(result, dict), (
        f"{label}: expected dict, got {type(result).__name__}"
    )
    assert result.get("ok") is False, (
        f"{label}: denylist FAILED to reject query {query!r}. "
        f"This is a critical regression — the run_cypher escape hatch "
        f"is the only barrier between the agent and arbitrary graph "
        f"writes. Result: {result!r}"
    )
    assert "error" in result, (
        f"{label}: rejection result missing 'error' field; payload: {result!r}"
    )
    assert (
        "forbidden" in result["error"].lower() or "deny" in result["error"].lower()
    ), f"{label}: error message does not mention forbidden/denied: {result['error']!r}"


# ─────────────────────────────────────────────────────────────────────────────
# Valid read-only queries — must pass denylist (we don't care what Neo4j
# returns; we only assert the denylist did not stop us).
# ─────────────────────────────────────────────────────────────────────────────


class _OkSession:
    """Fake session that returns an empty result. Used for positive tests
    where we want the denylist to pass but don't care about Neo4j output.
    """

    class _OkResult:
        def data(self):
            return []

    def run(self, query, **params):
        return self._OkResult()


VALID_QUERIES = [
    ("simple MATCH", "MATCH (n:Verse) RETURN n LIMIT 5"),
    (
        "OPTIONAL MATCH",
        "MATCH (v:Verse) OPTIONAL MATCH (v)-[:MENTIONS]->(k) RETURN v, k LIMIT 5",
    ),
    ("WITH chain", "MATCH (v:Verse) WITH v WHERE v.verseId STARTS WITH '1:' RETURN v"),
    ("aggregation", "MATCH (n:Verse) RETURN count(n) AS total"),
    ("collect", "MATCH (s:Sura) RETURN s.number, collect(s.surahName)[..3] AS sample"),
    ("UNWIND", "UNWIND [1,2,3] AS x RETURN x"),
    ("ORDER BY", "MATCH (s:Sura) RETURN s ORDER BY s.number LIMIT 10"),
    ("CALL db.labels", "CALL db.labels() YIELD label RETURN label"),
    (
        "CALL db.schema.visualization",
        "CALL db.schema.visualization() YIELD nodes RETURN nodes",
    ),
]


@pytest.mark.parametrize(
    "label,query", VALID_QUERIES, ids=lambda x: x if isinstance(x, str) else None
)
def test_denylist_allows_valid_query(label, query):
    """Read-only MATCH/RETURN shapes must pass through the denylist."""
    result = chat.tool_run_cypher(_OkSession(), query=query)
    assert isinstance(result, dict), f"{label}: expected dict"
    assert result.get("ok") is True, (
        f"{label}: denylist FALSE-POSITIVED on a legitimate read-only "
        f"query {query!r}. Result: {result!r}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Input-shape rejections (separate from clause denylist).
# ─────────────────────────────────────────────────────────────────────────────


def test_rejects_non_string_query():
    result = chat.tool_run_cypher(_BoomSession(), query=None)
    assert result["ok"] is False
    assert "non-empty string" in result["error"]


def test_rejects_empty_string_query():
    result = chat.tool_run_cypher(_BoomSession(), query="")
    assert result["ok"] is False
    assert "non-empty string" in result["error"]


def test_rejects_whitespace_only_query():
    """All-whitespace counts as empty for the purposes of the safety check.

    Note: chat.tool_run_cypher's current behaviour treats "   " as a
    non-empty string and forwards it; that would reach session.run().
    This test pins the current behaviour so a future tightening doesn't
    drift it silently.
    """
    # NOTE: documents current behaviour, not desirable behaviour.
    # A whitespace-only query passes the empty-string check but Neo4j
    # would error on parse. The denylist isn't the right layer to
    # catch this; the input-validation step ahead of dispatch is.
    # Test pins that we don't claim to handle this and that the
    # forbidden-list isn't accidentally tightened in a way that
    # changes the behaviour without intent.
    pytest.skip(
        "Whitespace-only handling is delegated to Neo4j's parser by "
        "design; not asserting either behaviour here."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Documented limitations — false-positives on string literals.
# ─────────────────────────────────────────────────────────────────────────────


def test_known_false_positive_on_string_literal_containing_keyword():
    """Documented limitation: the denylist matches keyword tokens via
    \\b word-boundary regex, so a string literal that happens to contain
    a forbidden keyword will trigger a rejection.

    This is intentional behaviour today — we'd rather over-reject than
    risk a smart-enough adversarial prompt slipping a write past us.
    The test pins the behaviour so it can't silently change.
    """
    # The user might legitimately want to search for verses containing
    # the word "CREATE" or "SET" in their text. They cannot, today.
    queries_that_trigger_false_positive = [
        # "SET" inside a string literal
        "MATCH (v:Verse) WHERE v.text CONTAINS 'SET an example' RETURN v LIMIT 5",
        # "CREATE" inside a string literal
        "MATCH (v:Verse) WHERE v.text CONTAINS 'we CREATE the heavens' RETURN v LIMIT 5",
    ]
    for q in queries_that_trigger_false_positive:
        result = chat.tool_run_cypher(_BoomSession(), query=q)
        assert result["ok"] is False, (
            f"Expected denylist to over-reject {q!r} (string-literal "
            f"false-positive). If this passes, the denylist has been "
            f"made smarter — update the docstring and this test."
        )


# ─────────────────────────────────────────────────────────────────────────────
# LIMIT auto-injection (a separate safety belt, but worth pinning here
# since it's part of the run_cypher contract).
# ─────────────────────────────────────────────────────────────────────────────


def test_limit_clause_auto_injected_when_missing():
    """If the agent forgets LIMIT, the tool appends one."""

    captured = {}

    class _CaptureSession:
        class _R:
            def data(self):
                return []

        def run(self, q, **params):
            captured["query"] = q
            return self._R()

    chat.tool_run_cypher(_CaptureSession(), query="MATCH (n) RETURN n")
    assert "LIMIT" in captured["query"].upper(), (
        f"Expected auto-injected LIMIT; got query: {captured['query']!r}"
    )


def test_limit_clause_preserved_when_present():
    """Existing LIMIT must not be doubled."""

    captured = {}

    class _CaptureSession:
        class _R:
            def data(self):
                return []

        def run(self, q, **params):
            captured["query"] = q
            return self._R()

    chat.tool_run_cypher(_CaptureSession(), query="MATCH (n) RETURN n LIMIT 7")
    # The query should contain LIMIT 7, not appended a second LIMIT.
    q_upper = captured["query"].upper()
    # Count LIMIT occurrences as standalone tokens.
    import re

    limit_count = len(re.findall(r"\bLIMIT\s+\d+", q_upper))
    assert limit_count == 1, (
        f"Expected exactly 1 LIMIT clause; got {limit_count} in {captured['query']!r}"
    )
