"""
Quran Graph Chat — conversational LLM agent with graph tools.

Claude drives the exploration. Instead of a fixed keyword→query→answer pipeline,
Claude decides which tools to call, how deep to traverse, and when it has enough
context to answer well.

Usage:
    py chat.py

Tools available to Claude:
    search_keyword(keyword)              → verses mentioning a keyword, by surah
    get_verse(verse_id)                  → verse text + connected verses + shared keywords
    traverse_topic(keywords, hops)       → multi-keyword search + graph traversal
    find_path(verse_id_1, verse_id_2)    → shortest thematic path between two verses
    explore_surah(surah_number)          → all verses in a surah + cross-surah connections
"""

import json
import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase
import anthropic

# ── env loading ────────────────────────────────────────────────────────────────

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
MODEL          = "claude-sonnet-4-5"

# ── reuse lemmatizer ───────────────────────────────────────────────────────────

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_graph import tokenize_and_lemmatize

# ── semantic model (loaded once, reused across requests) ───────────────────────

_sem_model = None

def _get_sem_model():
    global _sem_model
    if _sem_model is None:
        from sentence_transformers import SentenceTransformer
        _sem_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _sem_model

# ── graph tool implementations ─────────────────────────────────────────────────

def tool_search_keyword(session, keyword: str) -> dict:
    """Find ALL verses mentioning a keyword, grouped by surah."""
    lemmas = tokenize_and_lemmatize(keyword)
    if not lemmas:
        return {"error": f"'{keyword}' is a stopword or too short — try a different word"}
    kw = lemmas[0]

    exists = session.run("MATCH (k:Keyword {keyword: $kw}) RETURN k.keyword AS kw", kw=kw).single()
    if not exists:
        # Fuzzy fallback: suggest similar keywords
        similar = [r["kw"] for r in session.run(
            "MATCH (k:Keyword) WHERE k.keyword STARTS WITH $prefix RETURN k.keyword AS kw LIMIT 8",
            prefix=kw[:4]
        )]
        return {
            "error": f"Keyword '{kw}' not in graph",
            "suggestions": similar,
            "tip": "Try one of the suggested keywords above"
        }

    # No LIMIT — return every verse that mentions this keyword
    rows = list(session.run("""
        MATCH (k:Keyword {keyword: $kw})<-[r:MENTIONS]-(v:Verse)
        RETURN v.surah AS surah, v.surahName AS surahName,
               v.verseId AS verseId, v.text AS text, r.score AS score
        ORDER BY r.score DESC
    """, kw=kw))

    by_surah = {}
    for row in rows:
        sname = f"Surah {row['surah']}: {row['surahName']}"
        by_surah.setdefault(sname, []).append({
            "verse_id": row["verseId"],
            "score": round(row["score"], 4),
            "text": row["text"]
        })

    return {
        "keyword": kw,
        "total_verses": len(rows),
        "by_surah": by_surah
    }


def tool_get_verse(session, verse_id: str) -> dict:
    """Get a verse's full text, its keywords, and all directly connected verses."""
    verse_id = verse_id.strip().replace(" ", ":")
    row = session.run("MATCH (v:Verse {verseId: $id}) RETURN v", id=verse_id).single()
    if not row:
        return {"error": f"Verse [{verse_id}] not found. Format: surah:verse e.g. 2:255"}

    v = row["v"]
    keywords = [r["kw"] for r in session.run("""
        MATCH (v:Verse {verseId: $id})-[r:MENTIONS]->(k:Keyword)
        RETURN k.keyword AS kw ORDER BY r.score DESC LIMIT 15
    """, id=verse_id)]

    neighbours = list(session.run("""
        MATCH (v:Verse {verseId: $id})-[r:RELATED_TO]-(other:Verse)
        RETURN other.verseId AS otherId, other.surahName AS surahName,
               other.text AS text, r.score AS score
        ORDER BY r.score DESC LIMIT 12
    """, id=verse_id))

    # Batch: fetch shared keywords for ALL neighbours in one query
    neighbour_ids = [r["otherId"] for r in neighbours]
    shared_map = {}
    if neighbour_ids:
        shared_rows = session.run("""
            UNWIND $otherIds AS oid
            MATCH (v1:Verse {verseId: $v1})-[:MENTIONS]->(k:Keyword)<-[:MENTIONS]-(v2:Verse {verseId: oid})
            WITH oid, collect(k.keyword)[..5] AS kws
            RETURN oid, kws
        """, v1=verse_id, otherIds=neighbour_ids)
        for sr in shared_rows:
            shared_map[sr["oid"]] = sr["kws"]

    connected = [{
        "verse_id": r["otherId"],
        "surah_name": r["surahName"],
        "text": r["text"],
        "shared_keywords": shared_map.get(r["otherId"], []),
        "connection_score": round(r["score"], 4)
    } for r in neighbours]

    return {
        "verse_id": verse_id,
        "surah": v["surah"],
        "surah_name": v["surahName"],
        "text": v["text"],
        "keywords": keywords,
        "connected_verses": connected
    }


def tool_traverse_topic(session, keywords: list[str], hops: int = 1) -> dict:
    """Multi-keyword search + graph traversal to map a topic."""
    hops = max(1, min(hops, 2))
    lemmas = list(set(
        lemma
        for kw in keywords
        for lemma in tokenize_and_lemmatize(kw)
    ))
    if not lemmas:
        return {"error": "All keywords were stopwords. Use more specific terms."}

    # Direct matches — no limit, return ALL verses matching any of the keywords
    direct = list(session.run("""
        UNWIND $keywords AS kw
        MATCH (k:Keyword {keyword: kw})<-[r:MENTIONS]-(v:Verse)
        WITH v, sum(r.score) AS total, collect(kw) AS matched
        RETURN v.verseId AS verseId, v.surahName AS surahName,
               v.text AS text, total, matched
        ORDER BY total DESC
    """, keywords=lemmas))

    direct_ids = [r["verseId"] for r in direct]
    direct_results = [{
        "verse_id": r["verseId"],
        "surah_name": r["surahName"],
        "text": r["text"],
        "matched_keywords": r["matched"],
        "score": round(r["total"], 4)
    } for r in direct]

    # Use only top 30 direct matches as seeds for hop traversal (keeps query fast)
    seed_ids = direct_ids[:30]

    # 1-hop — top 60 thematically connected verses not already in direct matches
    hop1 = list(session.run("""
        UNWIND $seedIds AS sid
        MATCH (seed:Verse {verseId: sid})-[r:RELATED_TO]-(n:Verse)
        WHERE NOT n.verseId IN $allDirectIds
        WITH n, sum(r.score) AS score, collect(sid) AS via
        RETURN n.verseId AS verseId, n.surahName AS surahName,
               n.text AS text, score, via
        ORDER BY score DESC LIMIT 60
    """, seedIds=seed_ids, allDirectIds=direct_ids))

    hop1_ids = [r["verseId"] for r in hop1]
    hop1_results = [{
        "verse_id": r["verseId"],
        "surah_name": r["surahName"],
        "text": r["text"],
        "connected_via": r["via"],
        "score": round(r["score"], 4)
    } for r in hop1]

    hop2_results = []
    if hops >= 2:
        exclude = set(direct_ids + hop1_ids)
        hop2 = list(session.run("""
            UNWIND $h1Ids AS h1
            MATCH (h1v:Verse {verseId: h1})-[:RELATED_TO]-(h2:Verse)
            WHERE NOT h2.verseId IN $exclude
            WITH h2, count(*) AS connections
            RETURN h2.verseId AS verseId, h2.surahName AS surahName,
                   h2.text AS text, connections
            ORDER BY connections DESC LIMIT 40
        """, h1Ids=hop1_ids, exclude=list(exclude)))
        hop2_results = [{
            "verse_id": r["verseId"],
            "surah_name": r["surahName"],
            "text": r["text"]
        } for r in hop2]

    return {
        "keywords_used": lemmas,
        "direct_matches": direct_results,
        "hop_1_connections": hop1_results,
        "hop_2_connections": hop2_results,
        "total_verses_found": len(direct_results) + len(hop1_results) + len(hop2_results)
    }


def tool_find_path(session, verse_id_1: str, verse_id_2: str) -> dict:
    """Find the shortest thematic path between two verses through the graph."""
    v1 = verse_id_1.strip().replace(" ", ":")
    v2 = verse_id_2.strip().replace(" ", ":")

    for vid in [v1, v2]:
        if not session.run("MATCH (v:Verse {verseId: $id}) RETURN v", id=vid).single():
            return {"error": f"Verse [{vid}] not found"}

    result = session.run("""
        MATCH (v1:Verse {verseId: $v1}), (v2:Verse {verseId: $v2}),
              path = shortestPath((v1)-[:RELATED_TO*..6]-(v2))
        RETURN path, length(path) AS hops LIMIT 1
    """, v1=v1, v2=v2).single()

    if not result:
        return {"error": f"No path found between [{v1}] and [{v2}] within 6 hops"}

    nodes = result["path"].nodes

    # Batch: fetch bridge keywords for ALL consecutive pairs in one query
    pairs = [{"a": nodes[i]["verseId"], "b": nodes[i + 1]["verseId"]}
             for i in range(len(nodes) - 1)]
    bridge_map = {}
    if pairs:
        bridge_rows = session.run("""
            UNWIND $pairs AS pair
            MATCH (a:Verse {verseId: pair.a})-[:MENTIONS]->(k:Keyword)<-[:MENTIONS]-(b:Verse {verseId: pair.b})
            WITH pair.a AS fromId, pair.b AS toId, collect(k.keyword)[..5] AS kws
            RETURN fromId, toId, kws
        """, pairs=pairs)
        for br in bridge_rows:
            bridge_map[(br["fromId"], br["toId"])] = br["kws"]

    steps = []
    for i, node in enumerate(nodes):
        step = {
            "step": i + 1,
            "verse_id": node["verseId"],
            "surah_name": node["surahName"],
            "text": node["text"]
        }
        if i < len(nodes) - 1:
            step["bridge_keywords"] = bridge_map.get(
                (node["verseId"], nodes[i + 1]["verseId"]), [])
        steps.append(step)

    return {
        "from": v1,
        "to": v2,
        "hops": result["hops"],
        "path": steps
    }


def tool_explore_surah(session, surah_number: int) -> dict:
    """Get all verses in a surah and its top cross-surah thematic connections."""
    verses = list(session.run("""
        MATCH (v:Verse {surah: $s})
        RETURN v.verseId AS verseId, v.text AS text, v.verseNum AS verseNum
        ORDER BY v.verseNum
    """, s=surah_number))

    if not verses:
        return {"error": f"Surah {surah_number} not found (valid range: 1-114)"}

    surah_name = session.run(
        "MATCH (v:Verse {surah: $s}) RETURN v.surahName AS name LIMIT 1", s=surah_number
    ).single()["name"]

    verse_ids = [v["verseId"] for v in verses]
    cross = list(session.run("""
        UNWIND $vids AS vid
        MATCH (v:Verse {verseId: vid})-[:RELATED_TO]-(other:Verse)
        WHERE other.surah <> $s
        WITH other.surah AS otherSurah, other.surahName AS otherName, count(*) AS connections
        RETURN otherSurah, otherName, connections
        ORDER BY connections DESC LIMIT 10
    """, vids=verse_ids, s=surah_number))

    return {
        "surah": surah_number,
        "surah_name": surah_name,
        "verse_count": len(verses),
        "verses": [{"verse_id": v["verseId"], "text": v["text"]} for v in verses],
        "top_cross_surah_connections": [{
            "surah": r["otherSurah"],
            "surah_name": r["otherName"],
            "connections": r["connections"]
        } for r in cross]
    }


def tool_semantic_search(session, query: str, top_k: int = 40) -> dict:
    """Find verses conceptually similar to a query using vector embeddings."""
    model = _get_sem_model()
    vec = model.encode([query], normalize_embeddings=True, convert_to_numpy=True)[0].tolist()

    results = session.run("""
        CALL db.index.vector.queryNodes('verse_embedding', $k, $vec)
        YIELD node, score
        WHERE node.verseId IS NOT NULL
        RETURN node.verseId AS verseId, node.surahName AS surahName,
               node.surah AS surah, node.text AS text, score
    """, k=top_k, vec=vec).data()

    by_surah = {}
    for r in results:
        sname = f"Surah {r['surah']}: {r['surahName']}"
        by_surah.setdefault(sname, []).append({
            "verse_id": r["verseId"],
            "similarity": round(r["score"], 4),
            "text": r["text"],
        })

    return {
        "query": query,
        "total_verses": len(results),
        "note": "Results ranked by conceptual similarity, not keyword presence",
        "by_surah": by_surah,
    }


# ── tool schema (Anthropic tool_use format) ────────────────────────────────────

TOOLS = [
    {
        "name": "search_keyword",
        "description": (
            "Search for all Quran verses that mention a specific keyword. "
            "Results are grouped by surah and ranked by relevance (TF-IDF score). "
            "Use this to find where a concept appears across the Quran."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "A single word to search for (e.g. 'covenant', 'prayer', 'abraham')"
                }
            },
            "required": ["keyword"]
        }
    },
    {
        "name": "get_verse",
        "description": (
            "Get a specific verse by its ID, along with its keywords and all directly "
            "connected verses in the knowledge graph. Shows what the verse is thematically "
            "linked to and which keywords they share. Use this to deeply explore a single verse."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "verse_id": {
                    "type": "string",
                    "description": "Verse ID in surah:verse format, e.g. '2:255' or '36:1'"
                }
            },
            "required": ["verse_id"]
        }
    },
    {
        "name": "traverse_topic",
        "description": (
            "Explore a topic using multiple keywords + graph traversal. "
            "Finds direct keyword matches first, then expands outward through "
            "thematic connections (1-2 hops) to find related verses that wouldn't "
            "show up in a keyword search. Best for broad topic exploration."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of keywords describing the topic (e.g. ['covenant', 'abraham', 'prophet'])"
                },
                "hops": {
                    "type": "integer",
                    "description": "How many graph hops to traverse: 1 (faster, tighter focus) or 2 (broader, more connections). Default: 1",
                    "default": 1
                }
            },
            "required": ["keywords"]
        }
    },
    {
        "name": "find_path",
        "description": (
            "Find the shortest thematic path between two verses through the knowledge graph. "
            "Shows the chain of connected verses and the keywords that bridge each step. "
            "Useful for discovering unexpected connections between concepts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "verse_id_1": {
                    "type": "string",
                    "description": "Starting verse ID, e.g. '2:255'"
                },
                "verse_id_2": {
                    "type": "string",
                    "description": "Ending verse ID, e.g. '112:1'"
                }
            },
            "required": ["verse_id_1", "verse_id_2"]
        }
    },
    {
        "name": "explore_surah",
        "description": (
            "Get all verses in a specific surah (chapter) and a map of its strongest "
            "thematic connections to other surahs. Use this to understand a surah's "
            "content and how it relates to the rest of the Quran."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "surah_number": {
                    "type": "integer",
                    "description": "Surah number between 1 and 114"
                }
            },
            "required": ["surah_number"]
        }
    },
    {
        "name": "semantic_search",
        "description": (
            "Find verses that are CONCEPTUALLY similar to a query using vector embeddings. "
            "Unlike search_keyword which requires exact word matches, this finds verses that "
            "express the same idea even with completely different vocabulary. "
            "Use this to catch verses about redemption, divine mercy, being freed from sin, "
            "etc. when searching for 'forgiveness' — or any concept where the idea matters "
            "more than the exact words. Always use this alongside keyword search for full coverage."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A phrase or sentence describing the concept to search for, e.g. 'God forgiving and accepting repentance' or 'patience in hardship'"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of most similar verses to return (default 40, max 80)",
                    "default": 40
                }
            },
            "required": ["query"]
        }
    }
]

SYSTEM_PROMPT = """You are a knowledgeable Quran scholar and graph analyst with access to a \
knowledge graph of all 6,234 verses from Rashad Khalifa's translation of the Quran \
(The Final Testament). The graph connects verses through shared rare keywords using TF-IDF \
weighting, revealing thematic relationships across surahs.

You have 6 tools to explore the graph:
- search_keyword:  find ALL verses that explicitly mention a keyword (exact lemma match, no limit)
- semantic_search: find verses CONCEPTUALLY related to a query using vector similarity — catches verses that express the same idea with different words (e.g. redemption, divine acceptance, wiping away sins — all conceptually "forgiveness" without using the word)
- get_verse:       deep-dive into a specific verse and its graph connections
- traverse_topic:  multi-keyword search + graph traversal (all direct matches + connected verses)
- find_path:       shortest thematic path between two verses
- explore_surah:   map a surah's content and cross-surah connections

EXHAUSTIVE SEARCH MANDATE — for every topical question:
1. Identify ALL relevant keyword variants and call search_keyword for each
2. ALWAYS also call semantic_search with a descriptive phrase — this catches conceptually related verses that use completely different vocabulary (e.g. a verse about God "redeeming" or "absolving" someone won't show up in a keyword search for "forgiveness" but will rank highly in semantic search)
3. Also call traverse_topic with all keywords combined
4. Deduplicate across all three methods and report the TOTAL unique verse count upfront
5. Organise your answer by theme — synthesise what the Quran says as a whole
6. When semantic_search surfaces a verse that doesn't use the keyword but is clearly conceptually related, explicitly note WHY it belongs — this is a key insight for the user

CITATION RULES — these are MANDATORY, no exceptions:
- EVERY claim, point, or statement you make MUST be grounded in specific verses from the graph tools. Do NOT make any theological statement without a verse citation.
- Always cite verse references inline using bracket notation like [2:255] or [36:1]. The UI renders these as hoverable tooltips showing the full verse text — so cite generously.
- When listing or discussing verses, ALWAYS include the reference even if you've mentioned it before. The user relies on these references to verify and explore further.
- If you cannot find a verse to support a point, do NOT make the point. You are a graph-backed research tool, not a general-purpose Islamic scholar. Stay grounded in what the data shows.
- Prefer quoting or paraphrasing the actual verse text alongside the reference where it strengthens the answer.
- NEVER give a thematic summary without verse references. Every paragraph should contain at least one [surah:verse] citation.

The user expects the FULL picture: explicit mentions AND conceptual parallels.
This is Khalifa's translation — note where topics relate to his unique interpretations
(e.g. the mathematical miracle of 19, the Messenger of the Covenant)."""


# ── agentic tool-use loop ──────────────────────────────────────────────────────

def dispatch_tool(session, tool_name: str, tool_input: dict) -> str:
    """Call the appropriate graph function and return JSON string result."""
    try:
        if tool_name == "search_keyword":
            result = tool_search_keyword(session, **tool_input)
        elif tool_name == "get_verse":
            result = tool_get_verse(session, **tool_input)
        elif tool_name == "traverse_topic":
            result = tool_traverse_topic(session, **tool_input)
        elif tool_name == "find_path":
            result = tool_find_path(session, **tool_input)
        elif tool_name == "explore_surah":
            result = tool_explore_surah(session, **tool_input)
        elif tool_name == "semantic_search":
            result = tool_semantic_search(session, **tool_input)
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        result = {"error": str(e)}
    return json.dumps(result, ensure_ascii=False)


def run_agent_turn(
    user_message: str,
    conversation: list,
    session,
    client: anthropic.Anthropic,
) -> str:
    """
    Run one full agent turn: may involve multiple tool calls before final response.
    Returns the final text response.
    """
    conversation.append({"role": "user", "content": user_message})

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=conversation,
        )

        # Collect any text blocks for display
        text_parts = [b.text for b in response.content if b.type == "text" and b.text.strip()]

        # If no tool calls, we're done
        if response.stop_reason != "tool_use":
            final_text = "\n".join(text_parts) if text_parts else "(no response)"
            conversation.append({"role": "assistant", "content": response.content})
            return final_text

        # Process tool calls
        tool_results = []
        tool_names = []
        for block in response.content:
            if block.type == "tool_use":
                tool_names.append(f"{block.name}({json.dumps(block.input)})")
                print(f"  [tool] {block.name}({json.dumps(block.input)[:80]}{'...' if len(json.dumps(block.input)) > 80 else ''})")
                result_str = dispatch_tool(session, block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str,
                })

        # Add assistant turn + tool results to conversation
        conversation.append({"role": "assistant", "content": response.content})
        conversation.append({"role": "user", "content": tool_results})
        # Loop back for Claude to process tool results


# ── main loop ──────────────────────────────────────────────────────────────────

def main():
    print("Quran Knowledge Graph — Conversational Agent")
    print("=" * 60)
    print(f"Model: {MODEL}")
    print("Claude can freely explore the graph using tools.")
    print()

    if not ANTHROPIC_KEY:
        print("Set ANTHROPIC_API_KEY in your .env file first.")
        sys.exit(1)

    print(f"Connecting to Neo4j at {NEO4J_URI}...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        print("  Connected OK")
    except Exception as e:
        print(f"  Connection failed: {e}")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    conversation = []

    print("\nType your question (or 'quit' / 'clear'):\n")

    with driver.session() as session:
        while True:
            try:
                question = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                break

            if not question:
                continue
            if question.lower() in ("quit", "exit", "q"):
                print("Goodbye.")
                break
            if question.lower() == "clear":
                conversation.clear()
                print("  Conversation cleared.\n")
                continue

            print()
            answer = run_agent_turn(question, conversation, session, client)
            print(f"\nClaude:\n{answer}\n")
            print("-" * 60)

    driver.close()


if __name__ == "__main__":
    main()
