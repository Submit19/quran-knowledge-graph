"""Guard against system-prompt / tool-catalogue drift.

The model only uses a tool well if the prompt documents it. Two prompts had
drifted from the tool lists actually handed to the model:

  - the paid prompt (prompts/system_prompt.txt, surfaced by config.system_prompt)
    named 15 tools while chat.TOOLS exposes 20;
  - the free prompt (prompts/system_prompt_free.txt) mandated search_arabic_root,
    which was missing from app_free.OLLAMA_TOOLS, and omitted recall_similar_query,
    which IS exposed.

These are pure-text / static-structure assertions — no Neo4j, no LLM call.
OLLAMA_TOOLS is read by ast (app_free connects to Neo4j at import time).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import chat

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"


def _ollama_tool_names() -> list[str]:
    """Extract the OLLAMA_TOOLS literal from app_free.py without importing it
    (the module opens a Neo4j connection at import time)."""
    source = (PROJECT_ROOT / "app_free.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "OLLAMA_TOOLS" for t in node.targets
        ):
            tools = ast.literal_eval(node.value)
            return [t["function"]["name"] for t in tools]
    raise AssertionError("OLLAMA_TOOLS assignment not found in app_free.py")


def _chat_tool_names() -> list[str]:
    return [t["name"] for t in chat.TOOLS]


@pytest.mark.xfail(
    strict=True, reason="paid prompt names 15 tools; chat.TOOLS exposes 20"
)
def test_paid_prompt_documents_every_chat_tool() -> None:
    """(a) Every name in chat.TOOLS appears in config.system_prompt()."""
    import config

    prompt = config.system_prompt()
    missing = [name for name in _chat_tool_names() if name not in prompt]
    assert not missing, (
        f"chat.TOOLS exposes {len(_chat_tool_names())} tools but the paid system "
        f"prompt (config.system_prompt) never names: {missing}"
    )


@pytest.mark.xfail(strict=True, reason="free prompt omits recall_similar_query")
def test_free_prompt_documents_every_ollama_tool() -> None:
    """(b) Every name in app_free.OLLAMA_TOOLS appears in the free prompt text."""
    prompt = (PROMPTS_DIR / "system_prompt_free.txt").read_text(encoding="utf-8")
    missing = [name for name in _ollama_tool_names() if name not in prompt]
    assert not missing, (
        f"OLLAMA_TOOLS exposes tools the free prompt never names: {missing}"
    )


@pytest.mark.xfail(strict=True, reason="search_arabic_root missing from OLLAMA_TOOLS")
def test_search_arabic_root_is_exposed_to_free_backend() -> None:
    """(c) search_arabic_root is in OLLAMA_TOOLS — the free prompt mandates it."""
    assert "search_arabic_root" in _ollama_tool_names(), (
        "system_prompt_free.txt mandates calling search_arabic_root, but it is "
        "not in app_free.OLLAMA_TOOLS — the free/Ollama backend can never call it."
    )
