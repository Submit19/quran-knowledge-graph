"""
Quran Graph — Browser Chat UI

Usage:
    py ui.py

Opens automatically at http://localhost:7860
"""

import json
import os
import re
import sys

from dotenv import load_dotenv
import gradio as gr
from neo4j import GraphDatabase
import anthropic

# ── env ────────────────────────────────────────────────────────────────────────

def _load_env():
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chat import TOOLS, SYSTEM_PROMPT, dispatch_tool

# ── clients ────────────────────────────────────────────────────────────────────

NEO4J_URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
ANTHROPIC_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL   = "claude-sonnet-4-5"

print("Connecting to Neo4j...")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
driver.verify_connectivity()
print("  Neo4j OK")

ai = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# ── verse tooltip helpers ───────────────────────────────────────────────────────

_VERSE_REF = re.compile(r'\[(\d+):(\d+)\]')


def _fetch_verse_texts(session, verse_ids: set) -> dict:
    if not verse_ids:
        return {}
    result = session.run(
        "UNWIND $ids AS vid "
        "MATCH (v:Verse {verseId: vid}) "
        "RETURN v.verseId AS id, v.text AS text",
        ids=list(verse_ids),
    )
    return {r["id"]: r["text"] for r in result}


def _add_tooltips(text: str, session) -> str:
    """Replace [N:N] verse refs with hoverable <span> elements."""
    refs = {f"{s}:{v}" for s, v in _VERSE_REF.findall(text)}
    if not refs:
        return text
    verse_texts = _fetch_verse_texts(session, refs)

    def replacer(m):
        vid = f"{m.group(1)}:{m.group(2)}"
        verse_text = verse_texts.get(vid, "")
        if not verse_text:
            return m.group(0)
        safe = verse_text.replace("&", "&amp;").replace('"', "&quot;")
        # Truncate long verses cleanly at a word boundary
        if len(safe) > 280:
            safe = safe[:280].rsplit(" ", 1)[0] + "..."
        return f'<span class="vref" data-v="{safe}">[{vid}]</span>'

    return _VERSE_REF.sub(replacer, text)


# ── agent ──────────────────────────────────────────────────────────────────────

TOOL_ICONS = {
    "search_keyword":  "Searching keywords",
    "get_verse":       "Looking up verse",
    "traverse_topic":  "Traversing topic",
    "find_path":       "Finding path",
    "explore_surah":   "Exploring surah",
}


def chat_fn(message: str, history: list):
    """
    Streaming generator for gr.ChatInterface.
    Yields partial response strings; applies verse tooltips on the final yield.
    """
    messages = []
    for msg in history:
        role    = msg.get("role")    if isinstance(msg, dict) else getattr(msg, "role", None)
        content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": str(content)})
    messages.append({"role": "user", "content": message})

    partial = ""

    with driver.session() as session:
        while True:
            response = ai.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            for block in response.content:
                if block.type == "text" and block.text.strip():
                    partial += block.text
                    yield partial

            if response.stop_reason != "tool_use":
                break   # exit loop → apply tooltips below

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                label       = TOOL_ICONS.get(block.name, block.name)
                args_preview = json.dumps(block.input)
                if len(args_preview) > 80:
                    args_preview = args_preview[:77] + "..."

                partial += f"\n\n<details><summary><em>{label}</em> — {args_preview}</summary>\n\n"
                yield partial

                result_str = dispatch_tool(session, block.name, block.input)

                try:
                    result = json.loads(result_str)
                    if "error" in result:
                        summary = f"**Error:** {result['error']}"
                    elif "total_verses" in result:
                        summary = f"Found **{result['total_verses']}** verses for keyword `{result.get('keyword','')}`"
                    elif "verse_id" in result:
                        summary = f"Verse **[{result['verse_id']}]** — {result.get('text','')[:120]}..."
                    elif "hops" in result:
                        summary = f"Path found in **{result['hops']}** hops"
                    elif "verse_count" in result:
                        summary = f"Surah **{result.get('surah_name','')}** — {result['verse_count']} verses"
                    elif "total_verses_found" in result:
                        summary = f"Found **{result['total_verses_found']}** verses"
                    else:
                        summary = "Result retrieved"
                except Exception:
                    summary = "Result retrieved"

                partial += f"{summary}\n\n</details>\n\n"
                yield partial

                tool_results.append({
                    "type":        "tool_result",
                    "tool_use_id": block.id,
                    "content":     result_str,
                })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user",      "content": tool_results})

        # ── final pass: inject verse tooltips ──────────────────────────────────
        final = _add_tooltips(partial, session)
        if final != partial:
            yield final


# ── UI ─────────────────────────────────────────────────────────────────────────

CSS = """
.gradio-container { max-width: 900px !important; margin: auto; }

details {
    background: #f8f8f0;
    border: 1px solid #e0ddd0;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 6px 0;
    font-size: 0.88em;
}
summary { cursor: pointer; color: #555; font-style: italic; }
summary:hover { color: #222; }

.vref {
    color: #059669;
    font-weight: 600;
    cursor: help;
    border-bottom: 1px dotted #059669;
}

#vref-tooltip {
    position: fixed;
    background: #1e293b;
    color: #f1f5f9;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 0.84em;
    font-style: italic;
    line-height: 1.5;
    max-width: 340px;
    white-space: normal;
    z-index: 99999;
    pointer-events: none;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
    display: none;
}
"""

# JavaScript: floating tooltip driven by mouseover on .vref spans.
# Uses a MutationObserver so it works even when new messages stream in.
TOOLTIP_JS = """
() => {
    const tip = document.createElement('div');
    tip.id = 'vref-tooltip';
    document.body.appendChild(tip);

    function attach(el) {
        el.addEventListener('mouseenter', function(e) {
            const text = this.getAttribute('data-v') || this.title;
            if (!text) return;
            tip.textContent = text;
            tip.style.display = 'block';
            const r = this.getBoundingClientRect();
            const tipW = 340;
            let left = r.left + r.width / 2 - tipW / 2;
            left = Math.max(8, Math.min(left, window.innerWidth - tipW - 8));
            const top = r.top - tip.offsetHeight - 8;
            tip.style.left = left + 'px';
            tip.style.top  = (top < 8 ? r.bottom + 8 : top) + 'px';
        });
        el.addEventListener('mouseleave', function() {
            tip.style.display = 'none';
        });
    }

    // Attach to existing refs
    document.querySelectorAll('.vref').forEach(attach);

    // Watch for new refs added during streaming
    new MutationObserver(function(mutations) {
        mutations.forEach(function(m) {
            m.addedNodes.forEach(function(node) {
                if (node.nodeType !== 1) return;
                if (node.classList && node.classList.contains('vref')) attach(node);
                node.querySelectorAll && node.querySelectorAll('.vref').forEach(attach);
            });
        });
    }).observe(document.body, { childList: true, subtree: true });
}
"""

with gr.Blocks(title="Quran Knowledge Graph") as demo:
    gr.Markdown(
        "## Quran Knowledge Graph\n"
        "Ask questions about the Quran. "
        "Claude explores the knowledge graph and cites verses inline. "
        "Hover over any **[N:N]** reference to read the full verse."
    )
    gr.ChatInterface(
        fn=chat_fn,
        examples=[
            "What does the Quran say about the covenant with Abraham?",
            "What is the significance of the number 19?",
            "How are prayer and remembrance connected?",
            "What does the Quran say about the role of Jesus?",
            "Show me the thematic path between verse 2:255 and 112:1",
            "Explore Surah 36 (Ya-Sin) and its connections",
        ],
    )
    demo.load(fn=None, js=TOOLTIP_JS)

if __name__ == "__main__":
    print("\nQuran Graph UI starting...")
    demo.launch(
        server_name="0.0.0.0",
        inbrowser=True,
        share=False,
        css=CSS,
    )
