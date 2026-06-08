"""Ollama/OpenAI tool schema -> Gemini functionDeclarations translation.

The translator lives in shared_agent (alongside the existing
_to_anthropic_tools). app_free.OLLAMA_TOOLS cannot be imported here because
app_free connects to Neo4j at module load, so the OpenAI-nested cases use
inline fixtures that mirror the real OLLAMA_TOOLS shapes. The "every tool is
expressible" guard round-trips chat.TOOLS (the full Anthropic-flat set).
"""

import pytest

import shared_agent
from chat import TOOLS as CHAT_TOOLS


# — OpenAI-nested fixtures mirroring app_free.OLLAMA_TOOLS shapes —

GET_VERSE = {
    "type": "function",
    "function": {
        "name": "get_verse",
        "description": "Get a specific verse, its text, connections, and context",
        "parameters": {
            "type": "object",
            "properties": {"verse_id": {"type": "string", "description": "e.g. 2:255"}},
            "required": ["verse_id"],
        },
    },
}

SEMANTIC_SEARCH = {
    "type": "function",
    "function": {
        "name": "semantic_search",
        "description": "Find verses conceptually related to a query via embeddings",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "natural language query"},
                "top_k": {"type": "integer", "description": "max results (default 20)"},
            },
            "required": ["query"],
        },
    },
}

GET_CODE19 = {
    "type": "function",
    "function": {
        "name": "get_code19_features",
        "description": "Khalifa Code-19 arithmetic features",
        "parameters": {
            "type": "object",
            "properties": {
                "scope": {"type": "string", "enum": ["global", "sura", "verse"]},
                "target": {"type": "string", "description": "sura number or verseId"},
            },
            "required": ["scope"],
        },
    },
}

TRAVERSE_TOPIC = {
    "type": "function",
    "function": {
        "name": "traverse_topic",
        "description": "Multi-keyword search + graph traversal",
        "parameters": {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "2-5 related keywords",
                },
                "hops": {
                    "type": "integer",
                    "description": "traversal depth (default 1)",
                },
            },
            "required": ["keywords"],
        },
    },
}

CONCEPT_SEARCH_WITH_DEFAULT = {
    "type": "function",
    "function": {
        "name": "concept_search",
        "description": "Search by canonical CONCEPT",
        "parameters": {
            "type": "object",
            "properties": {
                "concept": {"type": "string"},
                "top_k": {"type": "integer", "default": 30},
            },
            "required": ["concept"],
        },
    },
}


def _decls(result):
    """Pull the functionDeclarations list out of the Gemini tools envelope."""
    assert isinstance(result, list)
    assert len(result) == 1
    assert "functionDeclarations" in result[0]
    return result[0]["functionDeclarations"]


@pytest.mark.xfail(strict=True, reason="_to_gemini_tools not implemented yet")
def test_translates_simple_tool():
    decls = _decls(shared_agent._to_gemini_tools([GET_VERSE]))
    assert len(decls) == 1
    d = decls[0]
    assert d["name"] == "get_verse"
    assert d["description"].startswith("Get a specific verse")
    assert d["parameters"]["type"] == "object"
    assert d["parameters"]["properties"]["verse_id"]["type"] == "string"
    assert d["parameters"]["required"] == ["verse_id"]
    # The OpenAI "function" envelope must be unwrapped.
    assert "function" not in d
    assert "type" not in d or d.get("type") != "function"


@pytest.mark.xfail(strict=True, reason="_to_gemini_tools not implemented yet")
def test_translates_tool_with_required_optional_mix():
    d = _decls(shared_agent._to_gemini_tools([SEMANTIC_SEARCH]))[0]
    props = d["parameters"]["properties"]
    assert set(props) == {"query", "top_k"}
    assert d["parameters"]["required"] == ["query"]  # top_k stays optional (absent)
    assert props["top_k"]["type"] == "integer"


@pytest.mark.xfail(strict=True, reason="_to_gemini_tools not implemented yet")
def test_translates_tool_with_enum():
    d = _decls(shared_agent._to_gemini_tools([GET_CODE19]))[0]
    assert d["parameters"]["properties"]["scope"]["enum"] == ["global", "sura", "verse"]
    assert d["parameters"]["properties"]["scope"]["type"] == "string"


@pytest.mark.xfail(strict=True, reason="_to_gemini_tools not implemented yet")
def test_translates_tool_with_array_param():
    d = _decls(shared_agent._to_gemini_tools([TRAVERSE_TOPIC]))[0]
    kw = d["parameters"]["properties"]["keywords"]
    assert kw["type"] == "array"
    assert kw["items"]["type"] == "string"


@pytest.mark.xfail(strict=True, reason="_to_gemini_tools not implemented yet")
def test_strips_unsupported_default_field():
    d = _decls(shared_agent._to_gemini_tools([CONCEPT_SEARCH_WITH_DEFAULT]))[0]
    top_k = d["parameters"]["properties"]["top_k"]
    assert "default" not in top_k  # Gemini Schema rejects `default`
    assert top_k["type"] == "integer"


@pytest.mark.xfail(strict=True, reason="_to_gemini_tools not implemented yet")
def test_translates_multiple_openai_tools_in_one_envelope():
    decls = _decls(
        shared_agent._to_gemini_tools([GET_VERSE, SEMANTIC_SEARCH, TRAVERSE_TOPIC])
    )
    assert [d["name"] for d in decls] == [
        "get_verse",
        "semantic_search",
        "traverse_topic",
    ]


@pytest.mark.xfail(strict=True, reason="_to_gemini_tools not implemented yet")
def test_empty_tools_returns_empty_list():
    # Gemini rejects an empty functionDeclarations array, so emit no envelope.
    assert shared_agent._to_gemini_tools([]) == []


@pytest.mark.xfail(strict=True, reason="_to_gemini_tools not implemented yet")
def test_translates_all_chat_tools_without_error():
    """Every real tool (Anthropic-flat shape) must be expressible in Gemini.

    This is the stop-condition guard: if any of the 20 tool schemas cannot be
    translated, the round-trip raises and this test fails.
    """
    decls = _decls(shared_agent._to_gemini_tools(CHAT_TOOLS))
    assert len(decls) == len(CHAT_TOOLS)
    for d in decls:
        assert d["name"]  # non-empty name
        assert "function" not in d  # unwrapped
        assert d["parameters"]["type"] == "object"
        # No banned keys survive anywhere in the schema tree.
        assert "default" not in _flatten_keys(d["parameters"])
        assert "additionalProperties" not in _flatten_keys(d["parameters"])


def _flatten_keys(schema, acc=None):
    acc = acc if acc is not None else set()
    if isinstance(schema, dict):
        for k, v in schema.items():
            acc.add(k)
            _flatten_keys(v, acc)
    elif isinstance(schema, list):
        for item in schema:
            _flatten_keys(item, acc)
    return acc
