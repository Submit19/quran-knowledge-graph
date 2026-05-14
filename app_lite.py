"""
Quran Graph — LITE (Cheapest) Version

Model: claude-haiku-4-5 (~10-20x cheaper than Sonnet)
No hallucination reduction:
  - No uncertainty probes
  - No citation retry
  - No NLI verification
  - Lower max_tokens (1536 vs 3072)

Port: 8084

Usage:
    py app_lite.py

Phase 3a-3: the agent loop body lives in ``shared_agent.agent_stream``.
This module is the thin wrapper that builds an AgentConfig + the per-
process AgentCollaborators (including the Anthropic SDK client) and
exposes the FastAPI surface.
"""

import os
import sys
import webbrowser
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from neo4j import GraphDatabase
from pydantic import BaseModel


# ── env ────────────────────────────────────────────────────────────────────────


def _load_env():
    path = Path(__file__).parent / ".env"
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                if v.strip():
                    os.environ[k.strip()] = v.strip()


load_dotenv()
_load_env()

sys.path.insert(0, str(Path(__file__).parent))
from chat import SYSTEM_PROMPT, TOOLS  # noqa: E402
from shared_agent import (  # noqa: E402
    AgentCollaborators,
    AgentConfig,
    agent_stream as _shared_agent_stream,
)

# ── Lite config overrides ─────────────────────────────────────────────────────

HAIKU_MODEL = "claude-haiku-4-5-20251001"
LITE_MAX_TOKENS = 1536  # half of full version — keeps responses concise + cheap
LITE_MAX_TOOL_TURNS = 8  # safety cap on the agentic loop

# ── clients ────────────────────────────────────────────────────────────────────

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DB = os.getenv("NEO4J_DATABASE", "quran")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_TOKEN = os.getenv("ANTHROPIC_OAUTH_TOKEN", "")

print(f"[LITE] Model: {HAIKU_MODEL}")
print(f"[LITE] Max tokens: {LITE_MAX_TOKENS}")
print("[LITE] Hallucination reduction: NONE (cheapest mode)")

print("Connecting to Neo4j...")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
try:
    driver.verify_connectivity()
    print(f"  Neo4j OK  (database: {NEO4J_DB})")
except Exception as e:
    print(f"  Neo4j unavailable: {e}\n  Graph tools will return errors until Neo4j is started.")

if ANTHROPIC_TOKEN:
    ai = anthropic.Anthropic(auth_token=ANTHROPIC_TOKEN)
    print("  Auth: OAuth token")
else:
    ai = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    print("  Auth: API key")


# ── AgentConfig + AgentCollaborators ──────────────────────────────────────────
# Built once at import time and passed into every shared_agent.agent_stream()
# call. Flags follow docs/PHASE_3A_PLAN.md §"variant axes" — app_lite is the
# bare-bones Anthropic variant: no uncertainty probe, no citation density
# retry, no NLI verifier, no priming graph, no reasoning-memory playbook, no
# query classification, no required-tool-classes discipline, no fallback.
# Tool-result compression stays on (Haiku's input window is tight) and the
# answer cache stays on (shared across all four apps).

AGENT_CONFIG = AgentConfig(
    backend="anthropic",
    default_model=HAIKU_MODEL,
    tools=TOOLS,
    system_prompt=SYSTEM_PROMPT,
    max_tool_turns=LITE_MAX_TOOL_TURNS,
    max_tokens=LITE_MAX_TOKENS,
    enable_citation_density_retry=False,
    enable_uncertainty_probe=False,
    enable_citation_verifier=False,
    enable_priming_graph_update=False,
    enable_reasoning_memory_playbook=False,
    enable_query_classification=False,
    enable_tool_result_compression=True,
    enable_answer_cache_lookup=True,
    enable_answer_cache_save=True,
    required_tool_classes={},
    fallback_chain=(),
)

AGENT_COLLABORATORS = AgentCollaborators(
    driver=driver,
    reasoning_memory=None,  # app_lite opts out of reasoning-memory recording
    db_name=NEO4J_DB,
    openrouter_api_key="",
    anthropic_client=ai,
)


# ── FastAPI ────────────────────────────────────────────────────────────────────

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    history: list


@app.get("/")
async def index():
    html = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@app.get("/stats")
async def stats():
    html = (Path(__file__).parent / "stats.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@app.get("/verses")
async def all_verses():
    with driver.session(database=NEO4J_DB) as s:
        result = s.run(
            "MATCH (v:Verse) RETURN v.reference AS id, v.sura AS surah, v.number AS num "
            "ORDER BY v.sura, v.number"
        )
        verses = [{"id": r["id"], "surah": r["surah"]} for r in result if r["id"]]
    return {"verses": verses}


@app.get("/model-info")
async def model_info():
    return {"model": HAIKU_MODEL, "backend": "anthropic", "cost": "paid"}


@app.get("/cache-stats")
async def get_cache_stats():
    from answer_cache import cache_stats

    return cache_stats()


# ── Sefaria-inspired ref resolver / linker API ────────────────────────────────


class ResolveRefsRequest(BaseModel):
    text: str


@app.post("/api/resolve_refs")
async def api_resolve_refs(req: ResolveRefsRequest):
    """Find Quranic citations in the given text, return resolved verseIds."""
    from ref_resolver import resolve_refs

    matches = resolve_refs(req.text)
    return {
        "input_length": len(req.text),
        "match_count": len(matches),
        "matches": [
            {
                "start": m.start,
                "end": m.end,
                "raw": m.raw,
                "verse_id": m.canonical,
                "kind": m.kind,
                "confidence": m.confidence,
            }
            for m in matches
        ],
    }


@app.get("/api/verse/{verse_id}")
async def api_get_verse(verse_id: str):
    """Return one verse by reference (e.g. '2:255')."""
    if ":" not in verse_id:
        return {"error": "verseId must be in format 'surah:verseNum'"}
    with driver.session(database=NEO4J_DB) as s:
        row = s.run(
            """
            MATCH (v:Verse)
            WHERE v.reference = $vid OR v.verseId = $vid
            RETURN v.reference AS id, v.text AS text,
                   v.arabicText AS arabic, v.surahName AS surahName,
                   v.surah AS surah, v.verseNum AS verseNum
            LIMIT 1
            """,
            vid=verse_id,
        ).single()
    if not row or not row.get("id"):
        return {"error": f"verse {verse_id} not found"}
    return {
        "verse_id": row["id"],
        "surah": row["surah"],
        "surah_name": row["surahName"],
        "verse_num": row["verseNum"],
        "text": row["text"],
        "arabic": row["arabic"],
    }


@app.get("/quran_linker.js")
async def quran_linker_js():
    """Single-file JS widget — drops into any page to auto-link Quranic refs."""
    js_path = Path(__file__).parent / "static" / "quran_linker.js"
    if not js_path.exists():
        return Response(content="// quran_linker.js not built yet",
                        media_type="application/javascript")
    return Response(content=js_path.read_text(encoding="utf-8"),
                    media_type="application/javascript")


@app.post("/chat")
async def chat(req: ChatRequest):
    return StreamingResponse(
        _agent_stream(req.message, req.history),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _agent_stream(message: str, history: list):
    """Back-compat shim — the loop body now lives in shared_agent.agent_stream.

    Kept so scripts/capture_baseline_trajectory.py (and any external callers)
    can keep using app_lite._agent_stream. New code should call
    shared_agent.agent_stream(..., AGENT_CONFIG, ...) directly.
    """
    async for frame in _shared_agent_stream(
        message, history, AGENT_CONFIG, AGENT_COLLABORATORS,
    ):
        yield frame


if __name__ == "__main__":
    import uvicorn

    print("\n[LITE] Quran Graph — Haiku Cheap Mode: http://localhost:8084\n")
    webbrowser.open("http://localhost:8084")
    uvicorn.run(app, host="0.0.0.0", port=8084, log_level="info")
