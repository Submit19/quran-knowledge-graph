"""
Regression test for the compress_tool_result(full_coverage=...) keyword.

Surfaced by an operator-reported error in app_free.py:
    Error: compress_tool_result() got an unexpected keyword argument 'full_coverage'

app_free.py:977 calls compress_tool_result(tool_name, result_str, full_coverage=...)
to disable verse truncation in deep-dive mode, but the function signature in
tool_compressor.py didn't accept the kwarg. This test pins the kwarg + its
intended behaviour: full_coverage=True returns result_str unchanged.
"""

from __future__ import annotations

import json

from tool_compressor import compress_tool_result


def _sample_result() -> str:
    """A tool result with a long text field that would normally get truncated."""
    return json.dumps({
        "verses": [
            {
                "verse_id": "1:1",
                "text": "In the name of God, Most Gracious, Most Merciful. " * 5,
                "arabic_text": "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
                "keywords": ["name", "god", "merciful"] * 5,
            },
        ],
    })


def test_compress_tool_result_accepts_full_coverage_kwarg():
    """The signature must accept full_coverage=... (regression for the
    'unexpected keyword argument' error from app_free.py:977)."""
    result = _sample_result()
    # Must not raise TypeError.
    out = compress_tool_result("search_keyword", result, full_coverage=False)
    assert isinstance(out, str)


def test_full_coverage_true_returns_input_unchanged():
    """When full_coverage=True, no compression happens — model sees the full
    tool result. Pins the documented intent of the kwarg."""
    result = _sample_result()
    out = compress_tool_result("search_keyword", result, full_coverage=True)
    assert out == result, "full_coverage=True must return the input unchanged"


def test_full_coverage_false_still_compresses():
    """Default behaviour preserved: full_coverage=False trims long text,
    drops arabic_text, caps keywords."""
    result = _sample_result()
    out = compress_tool_result("search_keyword", result, full_coverage=False)
    parsed = json.loads(out)
    verse = parsed["verses"][0]
    # Long text should be truncated to ~100 chars + "..."
    assert len(verse["text"]) <= 110
    assert verse["text"].endswith("...")
    # arabic_text should be dropped
    assert "arabic_text" not in verse
    # keywords should be capped at 8
    assert len(verse["keywords"]) <= 8


def test_full_coverage_default_is_false():
    """Existing callers (app.py, app_lite.py, app_full.py) pass only 2 args
    and rely on the default. Pins the default."""
    result = _sample_result()
    # 2-arg call (no full_coverage) — must still compress.
    out = compress_tool_result("search_keyword", result)
    parsed = json.loads(out)
    verse = parsed["verses"][0]
    assert "arabic_text" not in verse, "default must compress (full_coverage=False)"
