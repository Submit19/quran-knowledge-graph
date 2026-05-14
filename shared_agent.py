"""Shared agent-loop module — Phase 3a target.

Public surface for the four ``app*.py`` files. Today the body of each app's
``_agent_stream`` is a near-duplicate of the others — this module is the
single home where that body now lives.

Step 2 (interface stub) and step 3 (implementation move from ``app_free.py``)
of ``docs/PHASE_3A_PLAN.md``. This module now contains the live agent loop;
the other three apps (``app.py``, ``app_full.py``, ``app_lite.py``) keep
their own ``_agent_stream`` for now and will be ported in later sessions.

Public surface:
    AgentConfig — frozen dataclass of per-app variant axes (configuration).
    AgentCollaborators — dataclass carrying live runtime resources
        (Neo4j driver, ReasoningMemory instance, OpenRouter key, DB name)
        each app instantiates and passes to every ``agent_stream`` call.
    agent_stream — async generator that yields SSE frames.

Wiring contract (preserved through the refactor):
    - Each call goes through ``sse_pump.pump_worker_into_sse`` so the
      Phase 3b daemon-thread leak fix remains active.
    - The agent loop body polls ``stop_event.is_set()`` at the top of
      every turn for cooperative cancellation on consumer disconnect.
"""

from __future__ import annotations

import json
import os
import re
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal

import requests

from answer_cache import build_cache_context, save_answer
from chat import classify_query, dispatch_tool
from sse_pump import pump_worker_into_sse
from tool_compressor import compress_tool_result


# ──────────────────────────────────────────────────────────────────────────
# Public configuration
# ──────────────────────────────────────────────────────────────────────────


BackendName = Literal["anthropic", "ollama", "openrouter"]
"""Allowed values for ``AgentConfig.backend``. Enforced at construction."""


@dataclass(frozen=True)
class FallbackBackend:
    """One entry in ``AgentConfig.fallback_chain``.

    When the active backend raises during a turn, ``agent_stream`` walks the
    chain in order: pops the next ``FallbackBackend``, switches the active
    backend + model to it, and retries the turn. Once the chain is empty,
    the original exception propagates.
    """

    backend: BackendName
    model: str


@dataclass(frozen=True)
class AgentConfig:
    """Per-app variant axes for ``agent_stream``.

    Each app instantiates one of these at import time and passes the same
    instance to every ``agent_stream(...)`` call. The fields cover the
    variant table in ``docs/PHASE_3A_PLAN.md`` §"What behaviour preservation
    means concretely".

    The dataclass is frozen so wrappers cannot drift its values mid-request.
    Per-request overrides (e.g. ``deep_dive``, ``model_override``) go through
    ``agent_stream`` kwargs, not by mutating the config.
    """

    # — Required —
    backend: BackendName
    default_model: str
    tools: list[dict]
    system_prompt: str

    # — Loop limits —
    max_tool_turns: int = 15
    max_tokens: int = 4096

    # — Feature flags (variant axes) —
    enable_citation_density_retry: bool = False
    min_citations_for_retry: int = 5
    enable_uncertainty_probe: bool = False
    enable_citation_verifier: bool = False
    enable_priming_graph_update: bool = False
    enable_reasoning_memory_playbook: bool = False
    enable_query_classification: bool = False
    enable_tool_result_compression: bool = False
    enable_answer_cache_lookup: bool = True
    enable_answer_cache_save: bool = True

    # — Backend-specific routing (mostly app_free) —
    openrouter_model: str | None = None
    deep_dive_model: str | None = None
    prefer_openrouter: bool = False
    ollama_url: str = "http://localhost:11434/api/chat"
    openrouter_url: str = "https://openrouter.ai/api/v1/chat/completions"

    # — Tooling identifiers (informational; surfaced to the UI) —
    tool_labels: dict[str, str] = field(default_factory=dict)

    # — Multi-tool discipline policy —
    # Maps a class label (e.g. "keyword retrieval") to the list of tool names
    # that satisfy that class. agent_stream nudges the model if it tries to
    # answer without exercising every class. Empty dict = discipline disabled
    # (anthropic apps default to this).
    required_tool_classes: dict[str, list[str]] = field(default_factory=dict)

    # — Fallback chain —
    # Walked in order on API error: pop the next entry, switch
    # active_backend/active_model to it, retry the turn. Empty tuple (default)
    # = no fallback; the exception propagates.
    fallback_chain: tuple[FallbackBackend, ...] = ()

    def __post_init__(self) -> None:
        if self.backend not in ("anthropic", "ollama", "openrouter"):
            raise ValueError(
                f"AgentConfig.backend must be one of "
                f"'anthropic'|'ollama'|'openrouter', got {self.backend!r}"
            )
        if self.max_tool_turns < 1:
            raise ValueError(
                f"AgentConfig.max_tool_turns must be >= 1, got {self.max_tool_turns}"
            )
        if not isinstance(self.tools, list):
            raise TypeError(
                f"AgentConfig.tools must be a list, got {type(self.tools).__name__}"
            )


@dataclass
class AgentCollaborators:
    """Live per-process resources passed to every ``agent_stream`` call.

    Each app constructs one of these from its own module-level globals
    and passes it in. ``shared_agent`` no longer reaches into any app's
    module to find live resources — this kills the lazy-import seam that
    coupled Phase 3a-1's first cut to ``app_free``.

    Fields:
        driver: neo4j Driver (one per process; threadsafe; long-lived).
        reasoning_memory: ReasoningMemory instance. May be None for apps
            that opt out of reasoning-memory recording.
        db_name: Neo4j database name (e.g. ``"quran"``).
        openrouter_api_key: OpenRouter Bearer token. May be empty when
            the app doesn't use OpenRouter; ``agent_stream``'s routing
            decision treats an empty key as "OpenRouter unavailable".
        anthropic_client: ``anthropic.Anthropic`` client instance (or
            test double). Required when ``config.backend == "anthropic"``;
            ignored for Ollama-only apps.
    """

    driver: Any
    reasoning_memory: Any = None
    db_name: str = "quran"
    openrouter_api_key: str = ""
    anthropic_client: Any = None


# ──────────────────────────────────────────────────────────────────────────
# Module-level constants (moved from app_free.py)
# ──────────────────────────────────────────────────────────────────────────


TOOL_LABELS = {
    "search_keyword": "Searching keywords",
    "get_verse": "Looking up verse",
    "traverse_topic": "Traversing topic",
    "find_path": "Finding path",
    "explore_surah": "Exploring surah",
    "semantic_search": "Semantic search",
    "search_arabic_root": "Searching Arabic root",
    "compare_arabic_usage": "Comparing Arabic usage",
    "query_typed_edges": "Querying typed edges",
    "lookup_word": "Looking up word",
    "explore_root_family": "Exploring root family",
    "get_verse_words": "Analyzing verse words",
    "search_semantic_field": "Searching semantic field",
    "lookup_wujuh": "Looking up word meanings",
    "search_morphological_pattern": "Searching patterns",
}

_ETYMOLOGY_TOOLS = {
    "lookup_word",
    "explore_root_family",
    "get_verse_words",
    "search_semantic_field",
    "lookup_wujuh",
    "search_morphological_pattern",
}

_BRACKET_REF = re.compile(r"(\d+:\d+)")
_BRACKET_CONTEXT = re.compile(r"\[[\d:,\s]+\]")


# ──────────────────────────────────────────────────────────────────────────
# Pure helpers (moved from app_free.py)
# ──────────────────────────────────────────────────────────────────────────


def _extract_verse_refs(text: str) -> set:
    """Pull [surah:ayah] citations out of a text blob."""
    refs = set()
    for block in _BRACKET_CONTEXT.findall(text):
        refs.update(_BRACKET_REF.findall(block))
    return refs


def _fetch_verses(session, verse_ids: set) -> dict:
    """Batch-fetch verse text/arabic for a set of verse_ids."""
    if not verse_ids:
        return {}
    result = session.run(
        "UNWIND $ids AS vid "
        "MATCH (v:Verse {verseId: vid}) "
        "RETURN v.verseId AS id, v.text AS text, v.arabicText AS arabic",
        ids=list(verse_ids),
    )
    return {
        r["id"]: {"text": r["text"], "arabic": r["arabic"] or ""} for r in result
    }


def _extract_priming_keywords(message: str) -> list:
    """Pull 2-3 salient words from the user's message for a fast pre-flight lookup."""
    stop = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "to", "of", "in", "on", "at", "for", "with", "by", "and", "or", "but",
        "not", "no", "do", "does", "did", "have", "has", "had", "what", "who",
        "when", "where", "why", "how", "which", "that", "this", "these",
        "those", "it", "its", "about", "say", "says", "tell", "me", "i",
        "you", "your", "can", "could", "would", "should", "quran", "verse",
        "verses", "god", "allah",
    }
    words = re.findall(r"[a-zA-Z]{4,}", message.lower())
    uniq = []
    seen = set()
    for w in words:
        if w in stop or w in seen:
            continue
        seen.add(w)
        uniq.append(w)
    uniq.sort(key=len, reverse=True)
    return uniq[:3]


def _priming_graph_update(session, message: str) -> dict | None:
    """Fast (<200ms) lookup that returns a few seed verses to render before the LLM responds."""
    kws = _extract_priming_keywords(message)
    if not kws:
        return None
    try:
        seed_verses = session.run(
            """
            UNWIND $kws AS kw
            MATCH (k:Keyword) WHERE toLower(k.keyword) CONTAINS kw
            MATCH (k)<-[:MENTIONS]-(v:Verse)
            WITH v, count(DISTINCT k) AS matchCount
            ORDER BY matchCount DESC, v.verseId
            LIMIT 6
            RETURN v.verseId AS id, v.text AS text, v.surahName AS surahName,
                   v.arabicText AS arabicText
            """,
            kws=kws,
        ).data()
    except Exception:
        return None
    if not seed_verses:
        return None
    nodes = [
        {
            "id": v["id"],
            "type": "verse",
            "verseId": v["id"],
            "label": f"[{v['id']}]",
            "surahName": v["surahName"] or "",
            "text": (v["text"] or "")[:240],
            "arabicText": v["arabicText"] or "",
        }
        for v in seed_verses
    ]
    return {"nodes": nodes, "links": [], "active": [v["id"] for v in seed_verses[:3]]}


def _graph_for_tool(name: str, inp: dict, result: dict):
    """Extract graph nodes + links from a tool result for the 3D visualiser."""
    nodes: dict = {}
    links: list = []
    active: list = []

    def vnode(vid, sname="", text="", arabic=""):
        nid = f"v:{vid}"
        if nid not in nodes:
            try:
                surah = int(vid.split(":")[0])
            except Exception:
                surah = 0
            nodes[nid] = {
                "id": nid, "type": "verse", "label": f"[{vid}]",
                "verseId": vid, "surah": surah,
                "surahName": sname, "text": (text or "")[:200],
                "arabicText": (arabic or "")[:300],
            }
        return nid

    def knode(kw):
        nid = f"k:{kw}"
        if nid not in nodes:
            nodes[nid] = {"id": nid, "type": "keyword", "label": kw}
        return nid

    def lnk(src, tgt, ltype):
        links.append({"source": src, "target": tgt, "type": ltype})

    try:
        if name == "search_keyword" and "keyword" in result:
            kw = result["keyword"]
            k = knode(kw); active.append(k)
            count = 0
            for surah_verses in result.get("by_surah", {}).values():
                for v_data in surah_verses[:3]:
                    if count >= 15: break
                    v = vnode(v_data["verse_id"], "", v_data.get("text", ""))
                    lnk(v, k, "mentions"); count += 1
                if count >= 15: break

        elif name == "get_verse" and "verse_id" in result:
            vid = result["verse_id"]
            v = vnode(vid, result.get("surah_name", ""), result.get("text", ""))
            active.append(v)
            for kw in result.get("keywords", [])[:10]:
                k = knode(kw); lnk(v, k, "mentions")
            for cv in result.get("connected_verses", [])[:8]:
                cv_n = vnode(cv["verse_id"], cv.get("surah_name", ""), cv.get("text", ""))
                lnk(v, cv_n, "related")

        elif name == "semantic_search" and "results" in result:
            for v_data in result.get("results", [])[:10]:
                v = vnode(v_data["verse_id"], "", v_data.get("text", ""))
                active.append(v)

        elif name == "traverse_topic":
            for v_data in result.get("direct_matches", []):
                v = vnode(v_data["verse_id"], v_data.get("surah_name", ""), v_data.get("text", ""))
                active.append(v)
                for kw in v_data.get("matched_keywords", []):
                    k = knode(kw); lnk(v, k, "mentions")

        elif name == "search_arabic_root" and "root" in result:
            root = result["root"]
            rnid = f"r:{root}"
            nodes[rnid] = {"id": rnid, "type": "arabicRoot", "label": root}
            active.append(rnid)
            count = 0
            for surah_verses in result.get("by_surah", {}).values():
                for v_data in surah_verses[:3]:
                    if count >= 15: break
                    v = vnode(v_data["verse_id"], "", v_data.get("text", ""))
                    lnk(v, rnid, "mentions_root"); count += 1
                if count >= 15: break

        elif name == "find_path" and "path" in result:
            path = result["path"]
            for i, step in enumerate(path):
                v = vnode(step["verse_id"], step.get("surah_name", ""), step.get("text", ""))
                if i == 0 or i == len(path) - 1:
                    active.append(v)
                if i > 0:
                    lnk(f"v:{path[i - 1]['verse_id']}", v, "related")
                for kw in step.get("bridge_keywords", [])[:5]:
                    k = knode(kw); lnk(v, k, "mentions")

        elif name == "explore_surah" and "verses" in result:
            sname = result.get("surah_name", "")
            for v_data in result.get("verses", [])[:30]:
                vnode(v_data["verse_id"], sname, v_data.get("text", ""))
            active = list(nodes.keys())[:5]

        elif name == "query_typed_edges" and "by_type" in result:
            vid = result.get("verse_id", "")
            v_center = vnode(vid)
            active.append(v_center)
            for rtype, edges in result.get("by_type", {}).items():
                ltype = rtype.lower()
                for e in edges[:8]:
                    v = vnode(e["verse_id"], e.get("surah_name", ""),
                              e.get("text", ""), e.get("arabic_text", ""))
                    lnk(v_center, v, ltype)

        elif name == "compare_arabic_usage" and "root" in result:
            root = result["root"]
            rnid = f"r:{root}"
            nodes[rnid] = {"id": rnid, "type": "arabicRoot", "label": root,
                           "gloss": result.get("gloss", "")}
            active.append(rnid)
            for form_data in result.get("forms", [])[:8]:
                fnid = f"f:{form_data['form']}"
                nodes[fnid] = {"id": fnid, "type": "arabicForm",
                               "label": form_data["form"]}
                lnk(rnid, fnid, "derives")
                for v_data in form_data.get("sample_verses", [])[:3]:
                    v = vnode(v_data["verse_id"], v_data.get("surah_name", ""),
                              v_data.get("text", ""), v_data.get("arabic_text", ""))
                    lnk(fnid, v, "appears_in")

        elif name == "lookup_word" and result.get("found"):
            for lem_data in result.get("lemmas", [])[:5]:
                lnid = f"l:{lem_data['lemma']}"
                nodes[lnid] = {"id": lnid, "type": "lemma",
                               "label": lem_data["lemma"],
                               "gloss": lem_data.get("rootGloss", "")}
                active.append(lnid)
                if lem_data.get("root"):
                    rnid = f"r:{lem_data['root']}"
                    nodes[rnid] = {"id": rnid, "type": "arabicRoot",
                                   "label": lem_data["root"],
                                   "gloss": lem_data.get("rootGloss", "")}
                    lnk(lnid, rnid, "derives_from")
                for occ in lem_data.get("occurrences", [])[:8]:
                    v = vnode(occ["verse_id"]); lnk(lnid, v, "appears_in")

        elif name == "explore_root_family" and result.get("found"):
            root_info = result.get("root", {})
            rnid = f"r:{root_info.get('root', '')}"
            nodes[rnid] = {"id": rnid, "type": "arabicRoot",
                           "label": root_info.get("root", ""),
                           "gloss": root_info.get("gloss", "")}
            active.append(rnid)
            for dom_id, dom_name in result.get("semantic_domains", {}).items():
                dnid = f"d:{dom_id}"
                nodes[dnid] = {"id": dnid, "type": "semanticDomain", "label": dom_name}
                lnk(rnid, dnid, "in_domain")
            for lem_data in result.get("lemmas", [])[:15]:
                lnid = f"l:{lem_data['lemma']}"
                nodes[lnid] = {"id": lnid, "type": "lemma",
                               "label": lem_data["lemma"],
                               "gloss": lem_data.get("gloss", "")}
                lnk(rnid, lnid, "derives")
                if lem_data.get("pattern"):
                    pnid = f"p:{lem_data['pattern']}"
                    nodes[pnid] = {"id": pnid, "type": "morphPattern",
                                   "label": lem_data.get("pattern_label")
                                            or lem_data["pattern"]}
                    lnk(lnid, pnid, "follows_pattern")
                for sv in lem_data.get("sample_verses", [])[:2]:
                    v = vnode(sv["verse_id"]); lnk(lnid, v, "appears_in")

        elif name == "get_verse_words" and result.get("found"):
            vid = result["verse_id"]
            v = vnode(vid, result.get("surah_name", ""), result.get("translation", ""))
            active.append(v)
            for w in result.get("words", []):
                if w.get("root"):
                    rnid = f"r:{w['root']}"
                    nodes[rnid] = {"id": rnid, "type": "arabicRoot",
                                   "label": w["root"],
                                   "gloss": w.get("root_gloss", "")}
                    lnk(v, rnid, "mentions_root")

        elif name == "search_semantic_field" and result.get("found"):
            dom = result.get("domain", {})
            dnid = f"d:{dom.get('domainId', '')}"
            nodes[dnid] = {"id": dnid, "type": "semanticDomain",
                           "label": dom.get("nameEn", "")}
            active.append(dnid)
            for root_data in result.get("roots", [])[:15]:
                rnid = f"r:{root_data['root']}"
                nodes[rnid] = {"id": rnid, "type": "arabicRoot",
                               "label": root_data["root"],
                               "gloss": root_data.get("gloss", "")}
                lnk(dnid, rnid, "contains_root")
                for lem in root_data.get("lemmas", [])[:3]:
                    lnid = f"l:{lem['lemma']}"
                    nodes[lnid] = {"id": lnid, "type": "lemma",
                                   "label": lem["lemma"],
                                   "gloss": lem.get("gloss", "")}
                    lnk(rnid, lnid, "derives")

        elif name == "lookup_wujuh" and result.get("found"):
            root = result.get("root", "")
            rnid = f"r:{root}"
            nodes[rnid] = {"id": rnid, "type": "arabicRoot", "label": root}
            active.append(rnid)
            for sense in result.get("senses", []):
                snid = f"s:{sense['sense_id']}"
                nodes[snid] = {"id": snid, "type": "lemma",
                               "label": sense["meaning_en"][:30]}
                lnk(rnid, snid, "has_sense")
                for sv in sense.get("sample_verses", [])[:3]:
                    v = vnode(sv["verse_id"], "", sv.get("text", ""))
                    lnk(snid, v, "example_in")

        elif name == "search_morphological_pattern" and result.get("found"):
            pat = result.get("pattern", "")
            if pat:
                pnid = f"p:{pat}"
                nodes[pnid] = {"id": pnid, "type": "morphPattern", "label": pat}
                active.append(pnid)
            for root_data in result.get("by_root", [])[:10]:
                if root_data.get("root"):
                    rnid = f"r:{root_data['root']}"
                    nodes[rnid] = {"id": rnid, "type": "arabicRoot",
                                   "label": root_data["root"],
                                   "gloss": root_data.get("gloss", "")}
                    if pat:
                        lnk(pnid, rnid, "used_by")
                    for w in root_data.get("words", [])[:3]:
                        lnid = f"l:{w.get('lemma', w['arabic'])}"
                        nodes[lnid] = {"id": lnid, "type": "lemma",
                                       "label": w.get("lemma", w["arabic"])}
                        lnk(rnid, lnid, "derives")

    except Exception as e:
        print(f"  [graph] extract error ({name}): {e}")
        return None

    return {"nodes": list(nodes.values()), "links": links, "active": active} if nodes else None


# ──────────────────────────────────────────────────────────────────────────
# HTTP-client helpers (moved from app_free.py)
# ──────────────────────────────────────────────────────────────────────────


def _openrouter_chat(
    *, api_key: str, url: str, model: str, messages: list,
    tools: list | None = None, temperature: float = 0.3,
    num_predict: int = 4096,
) -> dict:
    """Send a chat request to OpenRouter (OpenAI-compatible API).

    Normalises the OpenAI response into the same ``{"message": {...}}`` shape
    that ``_ollama_chat`` returns, so the agent loop can stay backend-agnostic
    once a turn's response is in hand.
    """
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": num_predict,
    }
    if tools:
        payload["tools"] = tools

    r = requests.post(
        url,
        json=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8085",
            "X-Title": "Quran Knowledge Graph",
        },
        timeout=900,
    )
    r.raise_for_status()
    data = r.json()
    choice = data.get("choices", [{}])[0]
    msg = choice.get("message", {}) or {}
    return {
        "message": {
            "role": "assistant",
            "content": msg.get("content", "") or "",
            "tool_calls": msg.get("tool_calls", []) or [],
        }
    }


def _ollama_chat(
    *, url: str, model: str, messages: list,
    tools: list | None = None, temperature: float = 0.3,
    num_ctx: int = 24576, num_predict: int = 4096, think: bool = False,
) -> dict:
    """Send a chat request to Ollama. Returns the full response dict."""
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
            "num_ctx": num_ctx,
        },
        "think": think,
    }
    if tools:
        payload["tools"] = tools
    resp = requests.post(url, json=payload, timeout=600)
    resp.raise_for_status()
    return resp.json()


# ──────────────────────────────────────────────────────────────────────────
# Anthropic SDK translation helpers
# ──────────────────────────────────────────────────────────────────────────
#
# The agent loop operates on the OpenAI-ish message shape returned by
# ``_ollama_chat`` and ``_openrouter_chat``. Anthropic's SDK speaks a
# different dialect: messages have block-list content (``text`` / ``tool_use``
# / ``tool_result``), tools are flat (``name`` + ``input_schema`` instead of
# nested ``function.parameters``), and responses come back as ``Message``
# objects with ``.content`` blocks + ``.stop_reason``.
#
# These three helpers form the boundary translation. Keeping them as
# module-level pure functions makes them unit-testable without spinning up
# the whole agent loop (see tests/test_shared_agent_anthropic.py).


def _to_anthropic_messages(messages: list) -> list:
    """OpenAI-ish messages → Anthropic ``messages`` param.

    System messages are stripped (Anthropic takes ``system`` separately).
    Tool results and assistant tool_calls are rewritten into Anthropic's
    block-list shape.
    """
    out: list = []
    for m in messages:
        role = m.get("role")
        if role == "system":
            continue  # passed separately as the `system` param
        if role == "tool":
            out.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": m.get("tool_call_id", ""),
                    "content": m.get("content", ""),
                }],
            })
            continue
        if role == "assistant" and m.get("tool_calls"):
            blocks: list = []
            if m.get("content"):
                blocks.append({"type": "text", "text": m["content"]})
            for tc in m["tool_calls"]:
                fn = tc.get("function", {})
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                blocks.append({
                    "type": "tool_use",
                    "id": tc.get("id", ""),
                    "name": fn.get("name", ""),
                    "input": args,
                })
            out.append({"role": "assistant", "content": blocks})
            continue
        out.append({"role": role, "content": m.get("content", "")})
    return out


def _to_anthropic_tools(tools: list) -> list:
    """OpenAI-style tool schema → Anthropic tool schema.

    Anthropic expects ``{name, description, input_schema}`` (flat); OpenAI
    nests them inside ``function``. Passes through anything already in
    Anthropic shape (no ``function`` key).
    """
    out: list = []
    for t in tools:
        if "function" in t:
            fn = t["function"]
            out.append({
                "name": fn.get("name", ""),
                "description": fn.get("description", ""),
                "input_schema": fn.get("parameters", {"type": "object"}),
            })
        else:
            out.append(t)
    return out


def _from_anthropic_response(response) -> dict:
    """Anthropic ``Message`` → OpenAI-ish ``{"message": {...}}`` dict.

    Concatenates all text blocks; converts tool_use blocks into
    ``tool_calls`` entries with JSON-stringified ``arguments``.
    """
    text_parts: list = []
    tool_calls: list = []
    for block in response.content:
        btype = getattr(block, "type", None)
        if btype == "text":
            text_parts.append(getattr(block, "text", "") or "")
        elif btype == "tool_use":
            tool_calls.append({
                "id": getattr(block, "id", ""),
                "type": "function",
                "function": {
                    "name": getattr(block, "name", ""),
                    "arguments": json.dumps(getattr(block, "input", {}) or {}),
                },
            })
    return {
        "message": {
            "role": "assistant",
            "content": "".join(text_parts),
            "tool_calls": tool_calls,
        },
        "stop_reason": getattr(response, "stop_reason", None),
    }


def _anthropic_step(
    *, client, model: str, system: str, tools: list,
    messages: list, max_tokens: int = 4096, temperature: float = 0.3,
) -> dict:
    """Call Anthropic and return the OpenAI-ish shape the agent loop expects.

    ``messages`` arrives in the OpenAI-ish shape used throughout the loop;
    translation in both directions happens here so the rest of the loop is
    backend-agnostic.
    """
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        tools=_to_anthropic_tools(tools),
        messages=_to_anthropic_messages(messages),
        temperature=temperature,
    )
    return _from_anthropic_response(response)


# ──────────────────────────────────────────────────────────────────────────
# Public entry-point — agent_stream
# ──────────────────────────────────────────────────────────────────────────


async def agent_stream(
    message: str,
    history: list,
    config: AgentConfig,
    collaborators: AgentCollaborators,
    *,
    deep_dive: bool = False,
    full_coverage: bool = False,
    model_override: str | None = None,
    local_only: bool = False,
) -> AsyncIterator[str]:
    """Run the agent loop and yield SSE-formatted ``data: …\\n\\n`` frames.

    Each app's ``@app.post("/chat")`` handler builds a `StreamingResponse`
    from this generator. The body delegates the daemon-thread + queue
    orchestration to ``sse_pump.pump_worker_into_sse``; the worker polls
    ``stop_event`` between turns so a client disconnect cleanly tears down
    the agent loop (Phase 3b Bug D contract).
    """
    # Live runtime resources arrive via ``collaborators`` (Phase 3a-2). No
    # lazy ``import app_free`` here — the module is now uncoupled from any
    # particular app.
    driver = collaborators.driver
    reasoning_memory = collaborators.reasoning_memory
    db_name = collaborators.db_name
    openrouter_api_key = collaborators.openrouter_api_key
    anthropic_client = collaborators.anthropic_client

    # Routing decision.
    # For Anthropic-backed apps (app_lite, app.py, app_full.py) the default
    # is just config.backend with no fallback — the OpenRouter/Ollama branches
    # below only fire when an Ollama-default app gets `deep_dive` /
    # `model_override` / etc. from the request layer.
    if config.backend == "anthropic":
        if anthropic_client is None:
            raise RuntimeError(
                "AgentConfig.backend == 'anthropic' but "
                "AgentCollaborators.anthropic_client is None — apps using the "
                "Anthropic backend must construct an anthropic.Anthropic "
                "client and pass it in via AgentCollaborators."
            )
        active_model = model_override or config.default_model
        active_backend = "anthropic"
    else:
        # Routing decision (variant: app_free).
        use_openrouter = (
            not local_only
            and bool(openrouter_api_key)
            and (config.prefer_openrouter or deep_dive or model_override)
        )
        if use_openrouter:
            active_model = model_override or (
                config.openrouter_model or config.default_model
            )
            active_backend = "openrouter"
        elif deep_dive or local_only:
            active_model = config.deep_dive_model or config.default_model
            active_backend = "ollama"
        else:
            active_model = config.default_model
            active_backend = "ollama"

    print(f"  [chat] {active_backend} :: {active_model}")

    def run(q, stop_event):
        nonlocal active_model, active_backend

        # Surface the routing decision to the UI as the first event.
        try:
            q.put({
                "t": "tool", "name": "Model",
                "args": active_backend, "summary": active_model,
            })
        except Exception:
            pass

        # Start a reasoning-memory recording for this query.
        try:
            rec = reasoning_memory.start_query(
                text=message,
                backend=f"{active_backend}:{active_model}",
                deep_dive=deep_dive,
            )
        except Exception as _e:
            print(f"  [reasoning_memory] start failed: {_e}")
            rec = None

        try:
            # Build messages.
            msgs: list = [{"role": "system", "content": config.system_prompt}]
            for m in history:
                r = m.get("role") if isinstance(m, dict) else m["role"]
                c = m.get("content") if isinstance(m, dict) else m["content"]
                if r in ("user", "assistant") and c:
                    msgs.append({"role": r, "content": str(c)})

            # Answer-cache lookup.
            system_content = config.system_prompt
            if config.enable_answer_cache_lookup:
                try:
                    cache_ctx = build_cache_context(message, top_k=3, threshold=0.6)
                    if cache_ctx:
                        system_content = config.system_prompt + "\n\n" + cache_ctx
                        msgs[0] = {"role": "system", "content": system_content}
                        q.put({
                            "t": "tool", "name": "Answer cache",
                            "args": message[:60],
                            "summary": "Found relevant cached answers",
                        })
                except Exception as ce:
                    print(f"  [cache] lookup error: {ce}")

            # Reasoning-memory playbook injection.
            if config.enable_reasoning_memory_playbook:
                try:
                    similar = reasoning_memory.find_similar_queries(
                        message, top_k=3, min_sim=0.7
                    )
                    useful = [
                        s for s in similar
                        if s.get("status") == "completed" and (s.get("tool_steps") or [])
                    ]
                    if useful:
                        playbook_lines = [
                            "\n=== Past reasoning playbooks (similar queries you've answered) ===\n"
                        ]
                        for s in useful[:2]:
                            playbook_lines.append(
                                f"\nPrevious question (sim={s['score']:.2f}, "
                                f"{s['turns']} turns, {s['citation_count']} citations):"
                            )
                            playbook_lines.append(f"  Q: {s['text']}")
                            playbook_lines.append("  Tool sequence:")
                            for step in (s["tool_steps"] or [])[:8]:
                                playbook_lines.append(
                                    f"    - {step['tool_name']}({step['args'][:80]}) "
                                    f"-> {step['summary'][:80]}"
                                )
                        playbook_lines.append(
                            "\nConsider this playbook when choosing tools. You may reuse "
                            "the same keywords/queries that worked before, or diverge if "
                            "the new question needs different angles.\n"
                            "=== end playbooks ==="
                        )
                        system_content = system_content + "\n".join(playbook_lines)
                        msgs[0] = {"role": "system", "content": system_content}
                        q.put({
                            "t": "tool", "name": "Reasoning memory",
                            "args": f"{len(useful)} playbook(s)",
                            "summary": f"Found {len(useful)} similar past traces",
                        })
                except Exception as rme:
                    print(f"  [reasoning_memory] playbook lookup failed: {rme}")

            msgs.append({"role": "user", "content": message})

            # Query classification (gates rerank).
            _query_profile: str | None = None
            if config.enable_query_classification:
                try:
                    _query_profile = classify_query(message)
                    print(f"  [routing] classify_query -> profile={_query_profile!r}")
                    q.put({
                        "t": "tool", "name": "Query profile",
                        "args": message[:60],
                        "summary": f"profile={_query_profile}",
                    })
                except Exception as _qpe:
                    _query_profile = None
                    print(f"  [routing] classify_query failed: {_qpe}")

            full_text = ""
            turn = 0
            labels = config.tool_labels or TOOL_LABELS

            with driver.session(database=db_name) as session:
                # Priming graph update.
                if config.enable_priming_graph_update:
                    try:
                        prime = _priming_graph_update(session, message)
                        if prime:
                            q.put({
                                "t": "graph_update",
                                "nodes": prime["nodes"],
                                "links": prime["links"],
                                "active": prime["active"],
                            })
                            q.put({
                                "t": "tool", "name": "Priming search",
                                "args": ", ".join(_extract_priming_keywords(message)),
                                "summary": f"Found {len(prime['nodes'])} candidate verses",
                            })
                    except Exception as _e:
                        print(f"  [priming] {_e}")

                # Multi-tool discipline for topical questions.
                total_tool_calls = 0
                tools_used_so_far: set = set()
                _is_simple_lookup = bool(
                    re.search(r"\bverse\s*\d+[:.]\d+", message.lower())
                ) or len(message.split()) < 4

                discipline_classes = config.required_tool_classes

                def _needs_more_tools() -> bool:
                    if not discipline_classes:
                        return False  # discipline disabled
                    if _is_simple_lookup:
                        return False
                    if total_tool_calls < 2:
                        return True
                    for satisfying_tools in discipline_classes.values():
                        if not (tools_used_so_far & set(satisfying_tools)):
                            return True  # this class is unmet
                    return False

                num_predict_default = 8192 if full_coverage else config.max_tokens
                num_ctx_default = 40960 if full_coverage else 24576

                # Fallback chain (Phase 3a-2): on API error pop the next
                # entry, switch active backend/model, retry. Empty = no
                # fallback (current Anthropic-app behaviour when they port).
                pending_fallbacks = list(config.fallback_chain)

                def _call_backend(backend: str, model: str) -> dict:
                    """Dispatch one LLM call to the right backend.

                    Returns the normalised ``{"message": {content, tool_calls}}``
                    shape every helper produces.
                    """
                    if backend == "openrouter":
                        return _openrouter_chat(
                            api_key=openrouter_api_key,
                            url=config.openrouter_url,
                            model=model,
                            messages=msgs,
                            tools=config.tools,
                            temperature=0.3,
                            num_predict=num_predict_default,
                        )
                    if backend == "ollama":
                        return _ollama_chat(
                            url=config.ollama_url,
                            model=model,
                            messages=msgs,
                            tools=config.tools,
                            temperature=0.3,
                            num_ctx=num_ctx_default,
                            num_predict=num_predict_default,
                            think=full_coverage,
                        )
                    if backend == "anthropic":
                        if anthropic_client is None:
                            raise RuntimeError(
                                "anthropic backend requested but "
                                "collaborators.anthropic_client is None"
                            )
                        system_text = (
                            msgs[0]["content"]
                            if msgs and msgs[0].get("role") == "system"
                            else config.system_prompt
                        )
                        return _anthropic_step(
                            client=anthropic_client,
                            model=model,
                            system=system_text,
                            tools=config.tools,
                            messages=msgs,
                            max_tokens=num_predict_default,
                            temperature=0.3,
                        )
                    raise NotImplementedError(
                        f"_call_backend: backend {backend!r} not yet wired "
                        "in shared_agent — port the corresponding step "
                        "function before adding it to fallback_chain."
                    )

                def _sanitise_messages_for_backend_switch(from_b: str, to_b: str) -> None:
                    """OpenAI/OpenRouter returns tool_call arguments as JSON strings;
                    Ollama expects parsed dicts. Convert in-place when switching."""
                    if not (from_b == "openrouter" and to_b == "ollama"):
                        return
                    for m in msgs:
                        if m.get("role") == "assistant" and isinstance(
                            m.get("tool_calls"), list
                        ):
                            for tc in m["tool_calls"]:
                                args = tc.get("function", {}).get("arguments")
                                if isinstance(args, str):
                                    try:
                                        tc["function"]["arguments"] = json.loads(args)
                                    except Exception:
                                        pass

                while turn < config.max_tool_turns:
                    if stop_event.is_set():
                        return  # consumer disconnect — Phase 3b Bug D contract
                    turn += 1
                    print(
                        f"  [turn {turn}] backend={active_backend} "
                        f"model={active_model} msgs={len(msgs)}"
                    )
                    try:
                        resp = _call_backend(active_backend, active_model)
                    except Exception as e:
                        err_body = ""
                        if hasattr(e, "response") and e.response is not None:
                            try:
                                err_body = e.response.text[:500]
                            except Exception:
                                pass
                        print(f"  [api error] {active_backend}: {e}  body={err_body!r}")
                        # Walk the configured fallback chain (Phase 3a-2).
                        if pending_fallbacks:
                            fb = pending_fallbacks.pop(0)
                            print(
                                f"  [fallback] {active_backend} -> "
                                f"{fb.backend}:{fb.model}"
                            )
                            _sanitise_messages_for_backend_switch(
                                active_backend, fb.backend
                            )
                            active_backend = fb.backend
                            active_model = fb.model
                            q.put({
                                "t": "tool", "name": "Fallback",
                                "args": f"{e.__class__.__name__}",
                                "summary": f"Switching to {active_model}",
                            })
                            resp = _call_backend(active_backend, active_model)
                        else:
                            raise

                    msg = resp.get("message", {})
                    content = msg.get("content", "")
                    tool_calls = msg.get("tool_calls", [])

                    # Discipline-nudge if the model tries to skip retrieval.
                    if not tool_calls and _needs_more_tools():
                        missing = []
                        for class_name, satisfying_tools in discipline_classes.items():
                            if not (tools_used_so_far & set(satisfying_tools)):
                                missing.append(
                                    f"{class_name} ({' or '.join(satisfying_tools)})"
                                )
                        nudge = (
                            "You have not done enough retrieval yet. Before writing "
                            f"any answer, you MUST call one of: {'; '.join(missing)}. "
                            "Call them now."
                        )
                        msgs.append({"role": "user", "content": nudge})
                        continue

                    if content and content.strip():
                        full_text += content
                        q.put({"t": "text", "d": content})

                    if not tool_calls:
                        break

                    msgs.append(msg)

                    for tc in tool_calls:
                        func = tc.get("function", {})
                        tool_name = func.get("name", "")
                        tool_args = func.get("arguments", {})
                        tool_call_id = tc.get("id", "")

                        total_tool_calls += 1
                        tools_used_so_far.add(tool_name)

                        if isinstance(tool_args, str):
                            try:
                                tool_args = json.loads(tool_args)
                            except json.JSONDecodeError:
                                tool_args = {}

                        label = labels.get(tool_name, tool_name)
                        args_s = json.dumps(tool_args)
                        if len(args_s) > 80:
                            args_s = args_s[:77] + "..."

                        _t0 = time.time()
                        result_str = dispatch_tool(
                            session, tool_name, tool_args,
                            user_query=message, query_profile=_query_profile,
                        )
                        tool_duration_ms = int((time.time() - _t0) * 1000)

                        # Summary for UI.
                        tool_ok = True
                        result_cite_count = 0
                        try:
                            res = json.loads(result_str)
                            if "error" in res:
                                summary = f"Error: {res['error']}"
                                tool_ok = False
                            elif "total_verses" in res:
                                summary = f"Found {res['total_verses']} verses"
                                result_cite_count = int(res.get("total_verses") or 0)
                            elif "verse_id" in res:
                                summary = f"[{res['verse_id']}]"
                                result_cite_count = 1
                            elif "hops" in res:
                                summary = f"Path in {res['hops']} hops"
                            elif "verse_count" in res:
                                summary = (
                                    f"{res.get('surah_name','')} — {res['verse_count']} verses"
                                )
                                result_cite_count = int(res.get("verse_count") or 0)
                            else:
                                summary = "Done"
                        except Exception:
                            summary = "Done"
                            tool_ok = False

                        if rec is not None:
                            try:
                                rec.log_tool_call(
                                    turn=turn, order=total_tool_calls,
                                    tool_name=tool_name, args=tool_args,
                                    summary=summary, ok=tool_ok,
                                    duration_ms=tool_duration_ms,
                                    result_citation_count=result_cite_count,
                                    result_payload=result_str,
                                )
                            except Exception as _e:
                                print(f"  [reasoning_memory] log_tool_call failed: {_e}")

                        q.put({
                            "t": "tool", "name": label,
                            "args": args_s, "summary": summary,
                        })

                        # Graph update for the 3D visualiser.
                        try:
                            res_dict = json.loads(result_str)
                            gu = _graph_for_tool(tool_name, tool_args, res_dict)
                            if gu:
                                q.put({
                                    "t": "graph_update",
                                    "nodes": gu["nodes"], "links": gu["links"],
                                    "active": gu["active"],
                                })
                        except Exception:
                            pass

                        # Etymology side panel for relevant tools.
                        if tool_name in _ETYMOLOGY_TOOLS:
                            try:
                                ep = json.loads(result_str)
                                if ep.get("found") or ep.get("words") or ep.get("lemmas"):
                                    q.put({
                                        "t": "etymology_panel",
                                        "tool": tool_name, "result": ep,
                                    })
                            except Exception:
                                pass

                        # Feed the (compressed) tool result back to the model.
                        if config.enable_tool_result_compression:
                            compressed = compress_tool_result(
                                tool_name, result_str, full_coverage=full_coverage
                            )
                        else:
                            compressed = result_str
                        tool_msg = {"role": "tool", "content": compressed}
                        if tool_call_id:
                            tool_msg["tool_call_id"] = tool_call_id
                            tool_msg["name"] = tool_name
                        msgs.append(tool_msg)

                # Post-loop wrap-up.
                refs = _extract_verse_refs(full_text)

                # Citation-density retry.
                if (
                    config.enable_citation_density_retry
                    and not _is_simple_lookup
                    and len(refs) < config.min_citations_for_retry
                    and turn < config.max_tool_turns
                ):
                    q.put({
                        "t": "tool", "name": "Citation check",
                        "args": f"{len(refs)} citations",
                        "summary": (
                            f"Below threshold ({config.min_citations_for_retry}) — expanding"
                        ),
                    })
                    expand = (
                        f"Your answer so far has only {len(refs)} verse citations. "
                        f"A thorough answer needs at least {config.min_citations_for_retry}-10 citations. "
                        "Review the tool results you have, add more thematic sections with additional "
                        "verse references that you may have missed, and rewrite the answer. "
                        "Every paragraph must contain at least one [surah:verse] citation."
                    )
                    msgs.append({"role": "user", "content": expand})
                    retry_resp = _call_backend(active_backend, active_model)
                    retry_msg = retry_resp.get("message", {})
                    retry_content = retry_msg.get("content", "")
                    if retry_content and retry_content.strip():
                        full_text = retry_content
                        q.put({"t": "retry", "d": retry_content})
                    refs = _extract_verse_refs(full_text)

                verses = _fetch_verses(session, refs)

                # Save to answer cache.
                if config.enable_answer_cache_save:
                    try:
                        save_answer(message, full_text, verses)
                    except Exception as ce:
                        print(f"  [cache] save error: {ce}")

                # Optional citation verification — env-gated.
                if (
                    config.enable_citation_verifier
                    and os.getenv("ENABLE_CITATION_VERIFY", "0") == "1"
                    and verses
                    and full_text
                ):
                    try:
                        from citation_verifier import verify_response
                        v_result = verify_response(full_text, verses)
                        q.put({"t": "verification", "d": v_result})
                        if rec is not None:
                            try:
                                rec.log_citation_checks(v_result)
                            except Exception as _le:
                                print(f"  [reasoning_memory] citation log failed: {_le}")
                        print(
                            f"  [verify] precision={v_result.get('citation_precision')} "
                            f"checked={v_result.get('total_citations_checked')} "
                            f"flagged={v_result.get('flagged_count')}"
                        )
                    except Exception as ve:
                        print(f"  [verify] error: {ve}")

                if rec is not None:
                    try:
                        rec.finish(
                            answer_text=full_text,
                            citation_count=len(refs),
                            status=(
                                "retry_used" if turn > config.max_tool_turns else "completed"
                            ),
                        )
                    except Exception as _e:
                        print(f"  [reasoning_memory] finish failed: {_e}")

                q.put({"t": "done", "verses": verses})

        except requests.ConnectionError:
            if rec is not None:
                try:
                    rec.mark_failed("ollama connection")
                except Exception:
                    pass
            q.put({
                "t": "error",
                "d": "Cannot connect to Ollama. Make sure it's running: ollama serve",
            })
        except requests.Timeout:
            if rec is not None:
                try:
                    rec.mark_failed("ollama timeout")
                except Exception:
                    pass
            q.put({
                "t": "error",
                "d": "Ollama request timed out (600s). Try a smaller model or shorter question.",
            })
        except Exception as e:
            if rec is not None:
                try:
                    rec.mark_failed(str(e)[:300])
                except Exception:
                    pass
            q.put({"t": "error", "d": str(e)})
        finally:
            q.put(None)

    async for sse_frame in pump_worker_into_sse(run):
        yield sse_frame
