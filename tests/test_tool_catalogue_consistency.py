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
import re
from pathlib import Path

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


# Catalogue tool bullets are lowercase snake_case "- name:    description".
# Edge-type / typed-relationship bullets (- SUPPORTS:, - ELABORATES:) are
# uppercase and so excluded — this regex isolates tool names cleanly.
_BULLET_RE = re.compile(r"^-\s+([a-z][a-z0-9_]+):", re.MULTILINE)


def _catalogue_bullets(prompt: str) -> list[str]:
    return _BULLET_RE.findall(prompt)


def test_paid_prompt_documents_every_chat_tool() -> None:
    """(a) Paid prompt ↔ chat.TOOLS are consistent in BOTH directions.

    Forward: every exposed tool is documented. Reverse: every tool named in
    the catalogue is a real chat.TOOLS tool (no phantom names). The paid
    catalogue is clean in reverse today, so this guards against future drift."""
    import config

    prompt = config.system_prompt()
    exposed = _chat_tool_names()

    missing = [name for name in exposed if name not in prompt]
    assert not missing, (
        f"chat.TOOLS exposes {len(exposed)} tools but the paid system "
        f"prompt (config.system_prompt) never names: {missing}"
    )

    phantom = [name for name in _catalogue_bullets(prompt) if name not in exposed]
    assert not phantom, (
        f"Paid prompt catalogue names tools that don't exist in chat.TOOLS: {phantom}"
    )


def test_free_prompt_documents_every_ollama_tool() -> None:
    """(b) Free prompt ↔ OLLAMA_TOOLS are consistent in BOTH directions.

    Forward: every exposed tool is documented. Reverse: every tool named in
    the catalogue is actually exposed (catches a phantom like find_path, which
    was documented but never handed to the local model)."""
    prompt = (PROMPTS_DIR / "system_prompt_free.txt").read_text(encoding="utf-8")
    exposed = _ollama_tool_names()

    missing = [name for name in exposed if name not in prompt]
    assert not missing, (
        f"OLLAMA_TOOLS exposes tools the free prompt never names: {missing}"
    )

    phantom = [name for name in _catalogue_bullets(prompt) if name not in exposed]
    assert not phantom, (
        f"Free prompt catalogue names tools the local model can't call "
        f"(not in OLLAMA_TOOLS): {phantom}"
    )


def test_search_arabic_root_is_exposed_to_free_backend() -> None:
    """(c) search_arabic_root is in OLLAMA_TOOLS — the free prompt mandates it."""
    assert "search_arabic_root" in _ollama_tool_names(), (
        "system_prompt_free.txt mandates calling search_arabic_root, but it is "
        "not in app_free.OLLAMA_TOOLS — the free/Ollama backend can never call it."
    )
