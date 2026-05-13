"""
A minimal in-memory fake of the neo4j.Session interface used by chat.py.

This is a Beck-style "Fake It" double — not a real Cypher engine. It pattern-
matches on substrings in the query text and looks up canned data from a
synthetic graph dict.

When a Cypher feature you need isn't supported here, add a new pattern or
swap in a real Neo4j via testcontainers. The fake is deliberately small so
the substitution is cheap when you outgrow it.

Synthetic graph shape (see SAMPLE_GRAPH below for an example):

    {
        "verses": {
            "1:1": {
                "verseId": "1:1",
                "surah": 1,
                "surahName": "Al-Fatihah",
                "text": "In the name of God, ...",
                "arabicText": "...",
            },
            ...
        },
        "mentions": {            # verse_id -> [(keyword, score)]
            "1:1": [("name", 0.9), ("god", 0.85)],
        },
        "related": {             # verse_id -> [(other_id, score)]
            "1:1": [("2:255", 0.7)],
        },
        "roots": {               # verse_id -> [(root, gloss, forms, count)]
            "1:1": [("ر-ح-م", "mercy", ["rahman", "rahim"], 2)],
        },
        "typed_edges": {         # verse_id -> [(other_id, rel_type, score, conf)]
            "1:1": [],
        },
    }
"""

from __future__ import annotations

from typing import Any


class FakeResult:
    """Stand-in for neo4j.Result; supports iteration, .single(), list()."""

    def __init__(self, rows: list[dict]):
        self._rows = rows

    def __iter__(self):
        return iter(self._rows)

    def single(self):
        return self._rows[0] if self._rows else None


class FakeNeo4jSession:
    """
    Pattern-matches Cypher query strings used by chat.py tool functions and
    returns rows from a synthetic graph dict.

    Supports the queries used by tool_get_verse today. Extend as more tools
    get tests. Each pattern is a substring check (cheap, intentional) — when
    a query stops matching, add the new substring or a tighter check.
    """

    def __init__(self, graph: dict):
        self.graph = graph
        self.calls: list[tuple[str, dict]] = []  # for test introspection

    # ── Session protocol ────────────────────────────────────────────────────

    def run(self, query: str, **params) -> FakeResult:
        self.calls.append((query, params))
        rows = self._dispatch(query, params)
        return FakeResult(rows)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    # ── Query dispatch ──────────────────────────────────────────────────────

    def _dispatch(self, query: str, params: dict) -> list[dict]:
        q = " ".join(query.split())  # collapse whitespace

        # MATCH (v:Verse {verseId: $id}) RETURN v
        if "Verse {verseId: $id}" in q and "RETURN v" in q and "MENTIONS" not in q \
                and "RELATED_TO" not in q and "MENTIONS_ROOT" not in q:
            v = self.graph.get("verses", {}).get(params.get("id"))
            return [{"v": v}] if v else []

        # MENTIONS keywords for a verse
        if "MENTIONS]->(k:Keyword)" in q:
            verse_id = params.get("id")
            limit = params.get("lim", 50)
            kws = self.graph.get("mentions", {}).get(verse_id, [])
            return [{"kw": k} for (k, _score) in kws[:limit]]

        # RELATED_TO neighbours for a verse
        if "RELATED_TO]-(other:Verse)" in q:
            verse_id = params.get("id")
            limit = params.get("lim", 12)
            rels = self.graph.get("related", {}).get(verse_id, [])
            return [
                {
                    "otherId": other_id,
                    "surahName": self.graph.get("verses", {}).get(other_id, {}).get("surahName", ""),
                    "text": self.graph.get("verses", {}).get(other_id, {}).get("text", ""),
                    "score": score,
                }
                for (other_id, score) in rels[:limit]
            ]

        # UNWIND $otherIds AS oid ... shared keywords
        if "UNWIND $otherIds" in q and "MENTIONS" in q:
            v1 = params.get("v1")
            other_ids = params.get("otherIds", [])
            sk_limit = params.get("skLim", 5)
            v1_kws = {k for (k, _) in self.graph.get("mentions", {}).get(v1, [])}
            out = []
            for oid in other_ids:
                other_kws = {k for (k, _) in self.graph.get("mentions", {}).get(oid, [])}
                shared = sorted(v1_kws & other_kws)[:sk_limit]
                out.append({"oid": oid, "kws": shared})
            return out

        # MENTIONS_ROOT for a verse
        if "MENTIONS_ROOT]->(r:ArabicRoot)" in q:
            verse_id = params.get("id")
            roots = self.graph.get("roots", {}).get(verse_id, [])
            return [
                {"root": r, "gloss": g, "forms": f}
                for (r, g, f, _count) in roots
            ]

        # Typed edges (SUPPORTS, ELABORATES, etc.)
        if "WHERE type(r) IN ['SUPPORTS','ELABORATES','QUALIFIES','CONTRASTS','REPEATS']" in q.replace(" ", "") \
                or "type(r) IN" in q and "SUPPORTS" in q:
            verse_id = params.get("id")
            edges = self.graph.get("typed_edges", {}).get(verse_id, [])
            return [
                {"otherId": oid, "relType": rt, "score": score, "confidence": conf}
                for (oid, rt, score, conf) in edges
            ]

        # Unrecognised pattern — return empty so callers see "no data" gracefully.
        # If a test depends on a specific query and gets empty results, this is
        # the place to add a new pattern.
        return []


# ── Sample fixture graphs ───────────────────────────────────────────────────


def empty_graph() -> dict:
    """Graph with no verses — useful for red-bar tests."""
    return {
        "verses": {},
        "mentions": {},
        "related": {},
        "roots": {},
        "typed_edges": {},
    }


def graph_with_fatiha_opening() -> dict:
    """Graph containing only 1:1 — useful for the first green-bar test."""
    return {
        "verses": {
            "1:1": {
                "verseId": "1:1",
                "surah": 1,
                "surahName": "Al-Fatihah",
                "text": "In the name of God, Most Gracious, Most Merciful.",
                "arabicText": "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
            },
        },
        "mentions": {"1:1": []},
        "related": {"1:1": []},
        "roots": {"1:1": []},
        "typed_edges": {"1:1": []},
    }
