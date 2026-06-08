"""Tiny SSE client for the Phase 6 Gemini e2e smoke. Sends one /chat query,
prints the tool calls dispatched, the final answer, and the [s:v] citations."""

import json
import re
import sys

import requests

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PORT = sys.argv[2] if len(sys.argv) > 2 else "8090"
query = sys.argv[1]

r = requests.post(
    f"http://localhost:{PORT}/chat",
    json={"message": query, "history": []},
    stream=True,
    timeout=600,
)

text = []
tools = []
backend = None
err = None
for raw in r.iter_lines(decode_unicode=True):
    if not raw or not raw.startswith("data:"):
        continue
    try:
        ev = json.loads(raw[5:].strip())
    except json.JSONDecodeError:
        continue
    t = ev.get("t")
    if t == "text":
        text.append(ev.get("d", ""))
    elif t == "retry":
        # citation-density retry replaces the whole answer
        text = [ev.get("d", "")]
    elif t == "tool":
        name = ev.get("name", "")
        if name == "Model":
            backend = f"{ev.get('args')} :: {ev.get('summary')}"
        tools.append(f"{name}({ev.get('args', '')}) -> {ev.get('summary', '')}")
    elif t == "error":
        err = ev.get("d")
    elif t == "done":
        break

answer = "".join(text)
cites = sorted(set(re.findall(r"\[(\d+:\d+)\]", answer)))
print("BACKEND:", backend)
print("TOOLS DISPATCHED:")
for x in tools:
    print("   ", x[:160])
print("ERROR:", err)
print("CITATIONS:", cites)
print("ANSWER (first 700 chars):")
print(answer[:700])
