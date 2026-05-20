"""
Regression-guard for the cross-encoder rerank inside answer_cache.search_cache.

Mirrors what retrieval_gate already does for verse retrieval: a wider
cosine pre-filter pool, followed by a cross-encoder rerank to surface
matches that vector similarity misses.

Three properties under test:

  1. Rerank actually reorders results when the reranker disagrees with
     cosine. (test_rerank_changes_order)
  2. CACHE_RERANK_DISABLED=1 short-circuits before any reranker call.
     (test_rerank_disabled_by_env)
  3. Empty cache is handled without error. (test_rerank_handles_empty_cache)

No real cross-encoder is loaded; tests inject a fake via monkeypatch.

These tests are added with @pytest.mark.xfail(strict=True) and the xfail
markers are removed in the SAME commit that wires up the implementation —
xfail-then-flip pattern per CLAUDE.md's TDD discipline.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

import answer_cache


class _FakeReranker:
    """Minimal stand-in for a SentenceTransformers CrossEncoder.

    `score_map` maps cached question text -> rerank score. Higher score
    wins. Tests can inject specific maps to force a particular ordering.
    """

    def __init__(self, score_map: dict[str, float]):
        self.score_map = score_map
        self.calls: list[list[tuple[str, str]]] = []

    def predict(self, pairs):
        self.calls.append(list(pairs))
        return np.array([self.score_map.get(p[1], 0.0) for p in pairs])


class _FakeEncoder:
    """Stub that returns hard-coded embeddings keyed by exact input text."""

    def __init__(self, lookup: dict[str, list[float]]):
        self.lookup = lookup

    def encode(self, text, normalize_embeddings=True):
        if text not in self.lookup:
            raise KeyError(f"FakeEncoder has no embedding for {text!r}")
        return np.array(self.lookup[text])


@pytest.fixture
def tmp_cache(tmp_path: Path, monkeypatch):
    tmp_file = tmp_path / "answer_cache.json"
    monkeypatch.setattr(answer_cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(answer_cache, "CACHE_FILE", tmp_file)
    answer_cache._reset_memory_cache_for_tests()
    return tmp_file


def _make_entries() -> list[dict]:
    # Four entries with hand-crafted 4-d embeddings.
    # Cosine sim to query [1, 0, 0, 0]:
    #   alpha -> 0.95   (top by cosine)
    #   beta  -> 0.85
    #   gamma -> 0.75
    #   delta -> 0.70   (bottom by cosine)
    return [
        {
            "question": "alpha",
            "answer": "x",
            "verses": {},
            "embedding": [0.95, 0.31, 0.0, 0.0],
            "timestamp": 1.0,
        },
        {
            "question": "beta",
            "answer": "x",
            "verses": {},
            "embedding": [0.85, 0.52, 0.0, 0.0],
            "timestamp": 1.0,
        },
        {
            "question": "gamma",
            "answer": "x",
            "verses": {},
            "embedding": [0.75, 0.66, 0.0, 0.0],
            "timestamp": 1.0,
        },
        {
            "question": "delta",
            "answer": "x",
            "verses": {},
            "embedding": [0.70, 0.71, 0.0, 0.0],
            "timestamp": 1.0,
        },
    ]


def test_rerank_changes_order(tmp_cache, monkeypatch):
    """When the reranker disagrees with cosine, rerank wins."""
    answer_cache._save_cache(_make_entries())

    fake_encoder = _FakeEncoder({"my query": [1.0, 0.0, 0.0, 0.0]})
    monkeypatch.setattr(answer_cache, "_get_model", lambda: fake_encoder)

    # Reranker prefers the inverse cosine order.
    fake_reranker = _FakeReranker(
        {"alpha": 0.1, "beta": 0.4, "gamma": 0.7, "delta": 0.9}
    )
    monkeypatch.setattr(answer_cache, "_get_reranker", lambda: fake_reranker)

    out = answer_cache.search_cache("my query", top_k=1, threshold=0.0)

    assert len(out) == 1
    assert out[0]["question"] == "delta", (
        f"Expected rerank to surface 'delta'; got: {[r['question'] for r in out]}"
    )
    assert fake_reranker.calls, "Reranker was not consulted"
    # The pool fed to the reranker should be at least the top_k pool
    # widened — i.e. 10 entries asked for, only 4 available, so 4 fed.
    assert len(fake_reranker.calls[0]) == 4


def test_rerank_disabled_by_env(tmp_cache, monkeypatch):
    """CACHE_RERANK_DISABLED=1 must short-circuit before the reranker runs."""
    answer_cache._save_cache(_make_entries())
    fake_encoder = _FakeEncoder({"my query": [1.0, 0.0, 0.0, 0.0]})
    monkeypatch.setattr(answer_cache, "_get_model", lambda: fake_encoder)

    fake_reranker = _FakeReranker({"alpha": 0.1, "delta": 0.9})
    monkeypatch.setattr(answer_cache, "_get_reranker", lambda: fake_reranker)
    monkeypatch.setenv("CACHE_RERANK_DISABLED", "1")

    out = answer_cache.search_cache("my query", top_k=1, threshold=0.0)

    assert out[0]["question"] == "alpha", (
        "With rerank disabled, cosine top-1 ('alpha') should win"
    )
    assert not fake_reranker.calls, (
        "Reranker must NOT be invoked when CACHE_RERANK_DISABLED=1"
    )


def test_rerank_handles_empty_cache(tmp_cache, monkeypatch):
    """Empty cache returns []; no encoder or reranker calls."""
    fake_encoder = _FakeEncoder({})  # would KeyError if called
    monkeypatch.setattr(answer_cache, "_get_model", lambda: fake_encoder)
    fake_reranker = _FakeReranker({})
    monkeypatch.setattr(answer_cache, "_get_reranker", lambda: fake_reranker)

    out = answer_cache.search_cache("anything", top_k=3, threshold=0.0)

    assert out == []
    assert not fake_reranker.calls
