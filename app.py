"""
Quran Graph — Web Chat App

Anthropic-backed paid variant. The agent loop body now lives in
``shared_agent.agent_stream``; this module is the thin wrapper that
builds an AgentConfig + the per-process AgentCollaborators (Neo4j
driver + Anthropic SDK client) and exposes the FastAPI surface.

Port: 8081 — model: ``cfg.llm_model()`` (claude-sonnet-4-5 today).

Usage:
    py app.py
"""

import os
import sys
import webbrowser
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
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
import config as cfg  # noqa: E402
from chat import SYSTEM_PROMPT, TOOLS  # noqa: E402
from shared_agent import (  # noqa: E402
    AgentCollaborators,
    AgentConfig,
    agent_stream as _shared_agent_stream,
)


# ── clients ────────────────────────────────────────────────────────────────────

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DB = os.getenv("NEO4J_DATABASE", "quran")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_TOKEN = os.getenv("ANTHROPIC_OAUTH_TOKEN", "")
CLAUDE_MODEL = cfg.llm_model()

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
# Flags reflect what app.py actually did pre-refactor — variant table in
# docs/PHASE_3A_PLAN.md lists citation_density_retry / uncertainty_probe /
# verification as "yes" for app.py but the actual code had all three commented
# out (see git history). The port preserves the *observable* current
# behaviour: all three off. Tool-result compression stays on (app.py did
# compress; the table's "no" was inaccurate).

AGENT_CONFIG = AgentConfig(
    backend="anthropic",
    default_model=CLAUDE_MODEL,
    tools=TOOLS,
    system_prompt=SYSTEM_PROMPT,
    max_tool_turns=15,
    max_tokens=cfg.llm_max_tokens(),
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
    reasoning_memory=None,
    db_name=NEO4J_DB,
    openrouter_api_key="",
    anthropic_client=ai,
)


# ── FastAPI ────────────────────────────────────────────────────────────────────

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    history: list  # [{"role": "user"|"assistant", "content": str}]


@app.get("/")
async def index():
    html = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@app.get("/stats")
async def stats():
    html = (Path(__file__).parent / "stats.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@app.get("/cache-stats")
async def get_cache_stats():
    from answer_cache import cache_stats
    return cache_stats()


@app.get("/model-info")
async def model_info():
    return {"model": CLAUDE_MODEL, "backend": "anthropic", "cost": "paid"}


@app.get("/verses")
async def all_verses():
    """Return all verse IDs and surah numbers for the initial 3D graph."""
    with driver.session(database=NEO4J_DB) as s:
        result = s.run(
            "MATCH (v:Verse) RETURN v.reference AS id, v.sura AS surah, v.number AS num "
            "ORDER BY v.sura, v.number"
        )
        verses = [{"id": r["id"], "surah": r["surah"]} for r in result if r["id"]]
    return {"verses": verses}


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
    can keep using app._agent_stream. New code should call
    shared_agent.agent_stream(..., AGENT_CONFIG, ...) directly.
    """
    async for frame in _shared_agent_stream(
        message, history, AGENT_CONFIG, AGENT_COLLABORATORS,
    ):
        yield frame


if __name__ == "__main__":
    import uvicorn
    print("\nQuran Graph Web UI: http://localhost:8081\n")
    webbrowser.open("http://localhost:8081")
    uvicorn.run(app, host="0.0.0.0", port=8081, log_level="info")
