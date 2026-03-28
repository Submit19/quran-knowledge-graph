"""
Quran Graph — OpenAI-compatible API server.

Exposes the graph-powered Claude agent as an OpenAI-compatible endpoint
so Open WebUI (or any OpenAI client) can connect to it directly.

Usage:
    py server.py

Then in Open WebUI:
    Settings -> Connections -> Add OpenAI connection
    URL:    http://localhost:8100/v1
    Key:    quran (any value works)

The "quran-graph" model will appear in Open WebUI's model selector.
"""

import asyncio
import json
import os
import sys
import time
import uuid
from typing import AsyncIterator

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from neo4j import GraphDatabase
from pydantic import BaseModel

# ── env ────────────────────────────────────────────────────────────────────────

def _load_env(path=None):
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
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

NEO4J_URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
ANTHROPIC_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
PORT           = int(os.getenv("QURAN_SERVER_PORT", "8100"))
MODEL_ID       = "quran-graph"
CLAUDE_MODEL   = "claude-sonnet-4-5"

# ── import graph tools from chat.py ───────────────────────────────────────────

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chat import (
    TOOLS, SYSTEM_PROMPT, dispatch_tool,
    tool_search_keyword, tool_get_verse,
    tool_traverse_topic, tool_find_path, tool_explore_surah,
)

# ── Neo4j + Anthropic clients ─────────────────────────────────────────────────

print(f"Connecting to Neo4j at {NEO4J_URI}...")
_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
_driver.verify_connectivity()
print("  Neo4j connected OK")

_anthropic = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# ── FastAPI app ────────────────────────────────────────────────────────────────

app = FastAPI(title="Quran Graph API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request/Response models ───────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str | list

class ChatRequest(BaseModel):
    model: str = MODEL_ID
    messages: list[ChatMessage]
    stream: bool = False
    temperature: float = 1.0
    max_tokens: int = 4096

# ── SSE helpers ────────────────────────────────────────────────────────────────

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"

def _sse_done() -> str:
    return "data: [DONE]\n\n"

def _chunk(content: str, finish_reason=None, cid: str = "") -> dict:
    return {
        "id": cid or f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": MODEL_ID,
        "choices": [{
            "index": 0,
            "delta": {"content": content} if content else {},
            "finish_reason": finish_reason,
        }]
    }

# ── Agent logic ────────────────────────────────────────────────────────────────

def _convert_messages(messages: list[ChatMessage]) -> list[dict]:
    """Convert OpenAI-format messages to Anthropic format."""
    result = []
    for m in messages:
        if m.role == "system":
            continue  # handled via system param
        content = m.content if isinstance(m.content, str) else str(m.content)
        result.append({"role": m.role, "content": content})
    return result


async def _run_agent_streaming(
    messages: list[dict],
    cid: str,
) -> AsyncIterator[str]:
    """
    Run the agentic tool loop and stream output back as SSE chunks.
    Tool calls are shown as formatted text so the user can see graph exploration.
    """
    with _driver.session() as session:
        conversation = list(messages)

        while True:
            response = _anthropic.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=conversation,
            )

            # Stream any text blocks first
            for block in response.content:
                if block.type == "text" and block.text.strip():
                    # Stream word by word for a typing effect
                    words = block.text.split(" ")
                    for i, word in enumerate(words):
                        chunk_text = word + (" " if i < len(words) - 1 else "")
                        yield _sse(_chunk(chunk_text, cid=cid))
                        await asyncio.sleep(0.01)

            # If done, finish
            if response.stop_reason != "tool_use":
                yield _sse(_chunk("", finish_reason="stop", cid=cid))
                yield _sse_done()
                return

            # Process tool calls — show them as formatted text
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                # Format tool call announcement
                tool_display = _format_tool_call(block.name, block.input)
                yield _sse(_chunk(tool_display, cid=cid))
                await asyncio.sleep(0.05)

                # Execute tool
                result_str = dispatch_tool(session, block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str,
                })

            conversation.append({"role": "assistant", "content": response.content})
            conversation.append({"role": "user", "content": tool_results})


def _format_tool_call(name: str, inputs: dict) -> str:
    """Format a tool call as readable markdown for display in chat."""
    icons = {
        "search_keyword": "🔍",
        "get_verse": "📖",
        "traverse_topic": "🕸️",
        "find_path": "🛤️",
        "explore_surah": "📜",
    }
    icon = icons.get(name, "🔧")

    if name == "search_keyword":
        return f"\n\n{icon} *Searching keyword: **{inputs.get('keyword')}***\n\n"
    elif name == "get_verse":
        return f"\n\n{icon} *Reading verse **[{inputs.get('verse_id')}]***\n\n"
    elif name == "traverse_topic":
        kws = ", ".join(inputs.get("keywords", []))
        hops = inputs.get("hops", 1)
        return f"\n\n{icon} *Traversing topic: **{kws}** ({hops}-hop)*\n\n"
    elif name == "find_path":
        return f"\n\n{icon} *Finding path: **[{inputs.get('verse_id_1')}]** → **[{inputs.get('verse_id_2')}]***\n\n"
    elif name == "explore_surah":
        return f"\n\n{icon} *Exploring Surah **{inputs.get('surah_number')}***\n\n"
    return f"\n\n{icon} *{name}({json.dumps(inputs)[:60]})*\n\n"


async def _run_agent_sync(messages: list[dict]) -> str:
    """Non-streaming version — returns complete response."""
    with _driver.session() as session:
        conversation = list(messages)
        tool_log = []

        while True:
            response = _anthropic.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=conversation,
            )

            text_parts = [b.text for b in response.content if b.type == "text"]

            if response.stop_reason != "tool_use":
                prefix = ""
                if tool_log:
                    prefix = "\n".join(tool_log) + "\n\n---\n\n"
                return prefix + "\n".join(text_parts)

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                tool_log.append(_format_tool_call(block.name, block.input).strip())
                result_str = dispatch_tool(session, block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str,
                })

            conversation.append({"role": "assistant", "content": response.content})
            conversation.append({"role": "user", "content": tool_results})


# ── API routes ─────────────────────────────────────────────────────────────────

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [{
            "id": MODEL_ID,
            "object": "model",
            "created": 1700000000,
            "owned_by": "quran-graph",
            "description": "Quran knowledge graph agent — 6,234 verses, TF-IDF connections, Claude-powered",
        }]
    }

@app.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    return {
        "id": MODEL_ID,
        "object": "model",
        "created": 1700000000,
        "owned_by": "quran-graph",
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    cid = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    messages = _convert_messages(request.messages)

    if not messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    if request.stream:
        return StreamingResponse(
            _run_agent_streaming(messages, cid),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    else:
        content = await asyncio.get_event_loop().run_in_executor(
            None, lambda: asyncio.run(_run_agent_sync(messages))
        )
        return {
            "id": cid,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": MODEL_ID,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }

@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL_ID, "neo4j": NEO4J_URI}

# ── startup ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print(f"\nQuran Graph API server starting on http://localhost:{PORT}")
    print(f"\nTo connect Open WebUI:")
    print(f"  Settings -> Connections -> OpenAI API")
    print(f"  URL: http://localhost:{PORT}/v1")
    print(f"  Key: quran  (any value)")
    print(f"\nThe '{MODEL_ID}' model will appear in the model selector.\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
