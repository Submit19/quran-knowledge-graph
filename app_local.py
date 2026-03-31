"""
Quran Graph — Local Web App (NO Neo4j required)

Only requires: ANTHROPIC_API_KEY in .env file

Usage:
    python app_local.py
    # Opens at http://localhost:8081
"""

import asyncio
import json
import os
import re
import sys
import threading
import webbrowser
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import anthropic

# ── env ────────────────────────────────────────────────────────────────────────

load_dotenv()
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from chat_local import TOOLS, SYSTEM_PROMPT, dispatch_tool, VERSES

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-5"

if not ANTHROPIC_KEY:
    print("\n  ERROR: Set ANTHROPIC_API_KEY in your .env file")
    print("  Create .env with: ANTHROPIC_API_KEY=sk-ant-...\n")
    sys.exit(1)

ai = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# ── FastAPI ────────────────────────────────────────────────────────────────────

app = FastAPI()

_BRACKET_REF = re.compile(r'\[(\d+:\d+)\]')

TOOL_LABELS = {
    "search_keyword":  "Searching keywords",
    "get_verse":       "Looking up verse",
    "traverse_topic":  "Traversing topic",
    "find_path":       "Finding path",
    "explore_surah":   "Exploring surah",
    "semantic_search": "Semantic search",
}


# ── graph extraction for 3D visualiser ────────────────────────────────────────

def _graph_for_tool(name, inp, result):
    nodes = {}
    links = []
    active = []

    def vnode(vid, sname="", text=""):
        nid = f"v:{vid}"
        if nid not in nodes:
            try: surah = int(vid.split(":")[0])
            except: surah = 0
            nodes[nid] = {"id": nid, "type": "verse", "label": f"[{vid}]",
                          "verseId": vid, "surah": surah,
                          "surahName": sname, "text": (text or "")[:200]}
        return nid

    def knode(kw):
        nid = f"k:{kw}"
        if nid not in nodes:
            nodes[nid] = {"id": nid, "type": "keyword", "label": kw}
        return nid

    def link(src, tgt, ltype):
        links.append({"source": src, "target": tgt, "type": ltype})

    try:
        if name == "get_verse" and "verse_id" in result:
            vid = result["verse_id"]
            v = vnode(vid, result.get("surah_name", ""), result.get("text", ""))
            active.append(v)
            for kw in result.get("keywords", [])[:10]:
                k = knode(kw); link(v, k, "mentions")
            for cv in result.get("connected_verses", [])[:8]:
                cv_n = vnode(cv["verse_id"], cv.get("surah_name",""), cv.get("text",""))
                link(v, cv_n, "related")

        elif name == "search_keyword" and "keyword" in result:
            kw = result["keyword"]
            k = knode(kw); active.append(k)
            count = 0
            for surah_verses in result.get("by_surah", {}).values():
                for v_data in surah_verses[:3]:
                    if count >= 15: break
                    v = vnode(v_data["verse_id"], "", v_data.get("text",""))
                    link(v, k, "mentions"); count += 1
                if count >= 15: break

        elif name == "traverse_topic":
            for v_data in result.get("direct_matches", [])[:15]:
                v = vnode(v_data["verse_id"], v_data.get("surah_name",""), v_data.get("text",""))
                active.append(v)
                for kw in v_data.get("matched_keywords", []):
                    k = knode(kw); link(v, k, "mentions")

        elif name == "find_path" and "path" in result:
            path = result["path"]
            for i, step in enumerate(path):
                v = vnode(step["verse_id"], step.get("surah_name",""), step.get("text",""))
                if i == 0 or i == len(path) - 1: active.append(v)
                if i > 0: link(f"v:{path[i-1]['verse_id']}", v, "related")

        elif name == "explore_surah" and "verses" in result:
            sname = result.get("surah_name", "")
            for v_data in result.get("verses", [])[:30]:
                vnode(v_data["verse_id"], sname, v_data.get("text",""))
            active = list(nodes.keys())[:5]

    except Exception as e:
        return None

    return {"nodes": list(nodes.values()), "links": links, "active": active} if nodes else None


class ChatRequest(BaseModel):
    message: str
    history: list


@app.get("/")
async def index():
    return HTMLResponse((ROOT / "index.html").read_text(encoding="utf-8"))


@app.get("/stats")
async def stats():
    return HTMLResponse((ROOT / "stats.html").read_text(encoding="utf-8"))


@app.get("/verses")
async def all_verses():
    verses = [{"id": vid, "surah": v["surah"]}
              for vid, v in sorted(VERSES.items(),
                                    key=lambda x: (x[1]["surah"], x[1]["verseNum"]))]
    return {"verses": verses}


@app.post("/chat")
async def chat(req: ChatRequest):
    return StreamingResponse(
        _agent_stream(req.message, req.history),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _agent_stream(message, history):
    import queue as tqueue
    q = tqueue.SimpleQueue()

    def run():
        try:
            msgs = []
            for m in history:
                r = m.get("role") if isinstance(m, dict) else m["role"]
                c = m.get("content") if isinstance(m, dict) else m["content"]
                if r in ("user", "assistant") and c:
                    msgs.append({"role": r, "content": str(c)})
            msgs.append({"role": "user", "content": message})

            full_text = ""

            while True:
                resp = ai.messages.create(
                    model=CLAUDE_MODEL, max_tokens=4096,
                    system=SYSTEM_PROMPT, tools=TOOLS, messages=msgs,
                )

                for block in resp.content:
                    if block.type == "text" and block.text.strip():
                        full_text += block.text
                        q.put({"t": "text", "d": block.text})

                if resp.stop_reason != "tool_use":
                    break

                tool_results = []
                for block in resp.content:
                    if block.type != "tool_use":
                        continue

                    label = TOOL_LABELS.get(block.name, block.name)
                    args_s = json.dumps(block.input)
                    if len(args_s) > 80: args_s = args_s[:77] + "..."

                    result_str = dispatch_tool(block.name, block.input)

                    try:
                        res = json.loads(result_str)
                        if "error" in res:
                            summary = f"Error: {res['error']}"
                        elif "total_verses" in res:
                            summary = f"Found {res['total_verses']} verses"
                        elif "verse_id" in res:
                            summary = f"[{res['verse_id']}]: {res.get('text','')[:90]}..."
                        elif "hops" in res:
                            summary = f"Path in {res['hops']} hops"
                        elif "verse_count" in res:
                            summary = f"{res.get('surah_name','')} — {res['verse_count']} verses"
                        elif "total_verses_found" in res:
                            summary = f"Found {res['total_verses_found']} verses"
                        else:
                            summary = "Done"
                    except:
                        summary = "Done"

                    q.put({"t": "tool", "name": label, "args": args_s, "summary": summary})

                    try:
                        res_dict = json.loads(result_str)
                        gu = _graph_for_tool(block.name, block.input, res_dict)
                        if gu:
                            q.put({"t": "graph_update", "nodes": gu["nodes"],
                                   "links": gu["links"], "active": gu["active"]})
                    except:
                        pass

                    tool_results.append({
                        "type": "tool_result", "tool_use_id": block.id,
                        "content": result_str,
                    })

                msgs.append({"role": "assistant", "content": resp.content})
                msgs.append({"role": "user", "content": tool_results})

            # Fetch verse texts for refs
            refs = set(_BRACKET_REF.findall(full_text))
            verse_texts = {vid: VERSES[vid]["text"] for vid in refs if vid in VERSES}
            q.put({"t": "done", "verses": verse_texts})

        except Exception as e:
            q.put({"t": "error", "d": str(e)})
        finally:
            q.put(None)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    while True:
        try:
            event = q.get_nowait()
        except:
            await asyncio.sleep(0.05)
            continue
        if event is None:
            break
        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 50)
    print("  Quran Knowledge Graph — Local Mode")
    print("  (No Neo4j required)")
    print("=" * 50)
    print(f"\n  http://localhost:8081\n")
    webbrowser.open("http://localhost:8081")
    uvicorn.run(app, host="0.0.0.0", port=8081, log_level="info")
