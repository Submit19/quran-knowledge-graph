"""Regression guard: each system prompt must describe exactly the tool registry
its app actually exposes to the model.

Two registries, two prompts (see data/research/system_prompt_toolcount_2026-05-28.md):
  - chat.TOOLS          -> prompts/system_prompt.txt       (app.py, server.py, ui.py, ...)
  - app_free.OLLAMA_TOOLS -> prompts/system_prompt_free.txt (app_free.py only)

These tests fail if a prompt under-describes its registry (a tool the model can
call but was never told about -> silent under-use) or over-describes it (the
prompt mandates a tool the model cannot see). They are robust to rephrasing:
they assert on tool-name presence and a count derived from len(registry), never
on fixed prose.
"""

import re
from pathlib import Path

import pytest

from chat import TOOLS as CHAT_TOOLS
from app_free import OLLAMA_TOOLS

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"
PAID_PROMPT = (PROMPTS / "system_prompt.txt").read_text(encoding="utf-8")
FREE_PROMPT = (PROMPTS / "system_prompt_free.txt").read_text(encoding="utf-8")


def _chat_names():
    return [t["name"] for t in CHAT_TOOLS]


def _ollama_names():
    return [t["function"]["name"] for t in OLLAMA_TOOLS]


def _mentions(text, name):
    """Whole-token match so 'get_verse' does not match inside 'get_verse_words'."""
    return re.search(r"(?<![\w]){}(?![\w])".format(re.escape(name)), text) is not None


# universe of all real tool names, used for the over-description (vice-versa) check
ALL_TOOL_NAMES = {t["name"] for t in CHAT_TOOLS}


@pytest.mark.xfail(
    strict=True, reason="system_prompt.txt omits 5 exposed tools (fix pending)"
)
def test_paid_prompt_describes_every_chat_tool():
    """Every tool exposed via chat.TOOLS must appear in system_prompt.txt."""
    missing = [n for n in _chat_names() if not _mentions(PAID_PROMPT, n)]
    assert not missing, f"system_prompt.txt omits exposed tools: {missing}"


@pytest.mark.xfail(
    strict=True, reason="system_prompt.txt says '15 tools' not '20' (fix pending)"
)
def test_paid_prompt_tool_count_matches_registry():
    """The hardcoded count must equal len(chat.TOOLS); no stale wrong count."""
    n = len(CHAT_TOOLS)
    assert f"{n} tools" in PAID_PROMPT, f"expected '{n} tools' in system_prompt.txt"
    # no other integer-tool-count claim may contradict the real count
    wrong = [m for m in re.findall(r"(\d+) tools\b", PAID_PROMPT) if int(m) != n]
    assert not wrong, f"system_prompt.txt claims wrong tool count(s): {wrong}"


@pytest.mark.xfail(
    strict=True, reason="free prompt omits recall_similar_query (fix pending)"
)
def test_free_prompt_describes_every_ollama_tool():
    """Every tool exposed via OLLAMA_TOOLS must appear in system_prompt_free.txt."""
    missing = [n for n in _ollama_names() if not _mentions(FREE_PROMPT, n)]
    assert not missing, f"system_prompt_free.txt omits exposed tools: {missing}"


@pytest.mark.xfail(
    strict=True,
    reason="free prompt references find_path/search_arabic_root absent from OLLAMA_TOOLS (fix pending)",
)
def test_free_prompt_references_no_unavailable_tool():
    """Vice-versa: any real tool name the free prompt references must be exposed
    in OLLAMA_TOOLS — the prompt must not mandate a tool the model cannot call."""
    ollama = set(_ollama_names())
    referenced_but_unavailable = [
        n for n in ALL_TOOL_NAMES if _mentions(FREE_PROMPT, n) and n not in ollama
    ]
    assert not referenced_but_unavailable, (
        "system_prompt_free.txt references tools absent from OLLAMA_TOOLS: "
        f"{referenced_but_unavailable}"
    )


def test_free_prompt_tool_count_matches_registry():
    """The hardcoded count must equal len(OLLAMA_TOOLS); no stale wrong count."""
    n = len(OLLAMA_TOOLS)
    assert f"{n} retrieval/exploration tools" in FREE_PROMPT, (
        f"expected '{n} retrieval/exploration tools' in system_prompt_free.txt"
    )
    wrong = [
        m
        for m in re.findall(r"(\d+) retrieval/exploration tools\b", FREE_PROMPT)
        if int(m) != n
    ]
    assert not wrong, f"system_prompt_free.txt claims wrong tool count(s): {wrong}"


@pytest.mark.xfail(
    strict=True,
    reason="search_arabic_root not yet added to OLLAMA_TOOLS (Q2=ADD, fix pending)",
)
def test_search_arabic_root_available_in_free_surface():
    """Q2 path taken = ADD: search_arabic_root is mandated by the free prompt's
    Arabic-root augmentation block, so it must be exposed in OLLAMA_TOOLS and
    named in the catalogue. Pins the decision against silent reversion."""
    assert "search_arabic_root" in set(_ollama_names()), (
        "search_arabic_root must be in OLLAMA_TOOLS (free prompt mandates it)"
    )
    assert _mentions(FREE_PROMPT, "search_arabic_root")
